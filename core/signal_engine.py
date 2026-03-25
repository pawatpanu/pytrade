from __future__ import annotations

from dataclasses import asdict
import logging
from datetime import datetime
from typing import Any

import pandas as pd

from config import Config
from core.indicators import detect_price_structure, detect_support_resistance, detect_trend
from core.models import SignalResult
from core.risk_engine import build_trade_plan
from core.scorer import calculate_confidence
from core.utils import classify_score

logger = logging.getLogger(__name__)


def _row(df: pd.DataFrame, idx: int = -2) -> dict[str, float]:
    series = df.iloc[idx]
    return {k: float(series[k]) for k in series.index if k != "time"}


def _time(df: pd.DataFrame, idx: int = -2) -> datetime:
    return pd.Timestamp(df.iloc[idx]["time"]).to_pydatetime()


def _momentum_candle(direction: str, m5: pd.DataFrame) -> bool:
    row = m5.iloc[-2]
    prev = m5.iloc[-3]
    candle_range = max(float(row["high"] - row["low"]), 1e-8)
    body = abs(float(row["close"] - row["open"]))

    if direction == "BUY":
        return bool(
            row["close"] > row["open"]
            and body / candle_range >= 0.5
            and (row["close"] > prev["high"] or row["close"] > prev["close"])
        )
    return bool(
        row["close"] < row["open"]
        and body / candle_range >= 0.5
        and (row["close"] < prev["low"] or row["close"] < prev["close"])
    )


def _macd_cross(direction: str, df: pd.DataFrame) -> bool:
    prev = df.iloc[-3]
    row = df.iloc[-2]
    if direction == "BUY":
        cross = prev["macd"] <= prev["macd_signal"] and row["macd"] > row["macd_signal"]
        continuation = row["macd"] > row["macd_signal"] and row["macd_hist"] > prev["macd_hist"]
        return bool(cross or continuation)
    cross = prev["macd"] >= prev["macd_signal"] and row["macd"] < row["macd_signal"]
    continuation = row["macd"] < row["macd_signal"] and row["macd_hist"] < prev["macd_hist"]
    return bool(cross or continuation)


def _stoch_cross(direction: str, df: pd.DataFrame) -> bool:
    prev = df.iloc[-3]
    row = df.iloc[-2]
    if direction == "BUY":
        cross = prev["stoch_k"] <= prev["stoch_d"] and row["stoch_k"] > row["stoch_d"]
        continuation = row["stoch_k"] > row["stoch_d"] and row["stoch_k"] > prev["stoch_k"]
        return bool(cross or continuation)
    cross = prev["stoch_k"] >= prev["stoch_d"] and row["stoch_k"] < row["stoch_d"]
    continuation = row["stoch_k"] < row["stoch_d"] and row["stoch_k"] < prev["stoch_k"]
    return bool(cross or continuation)


def _volume_spike(df: pd.DataFrame, volume_spike_ratio: float) -> bool:
    row = df.iloc[-2]
    return bool(row["volume"] >= volume_spike_ratio * row["volume_sma20"])



def _find_order_block_zone(direction: str, m15: pd.DataFrame, profile: dict[str, Any]) -> tuple[float, float] | None:
    lookback = max(6, int(profile.get("order_block_lookback", 24) or 24))
    impulse_atr = max(0.1, float(profile.get("order_block_impulse_atr", 0.8) or 0.8))
    start = max(1, len(m15) - lookback - 3)
    end = max(start, len(m15) - 2)

    zone: tuple[float, float] | None = None
    for idx in range(start, end):
        base = m15.iloc[idx]
        impulse = m15.iloc[idx + 1]
        base_open = float(base["open"])
        base_close = float(base["close"])
        atr = max(float(base.get("atr14", 0.0) or 0.0), 1e-8)
        impulse_body = abs(float(impulse["close"] - impulse["open"]))

        if direction == "BUY":
            valid_base = base_close < base_open
            displacement = float(impulse["close"]) > float(base["high"])
        else:
            valid_base = base_close > base_open
            displacement = float(impulse["close"]) < float(base["low"])

        if not valid_base or not displacement:
            continue
        if impulse_body < (impulse_atr * atr):
            continue

        lo = min(base_open, base_close)
        hi = max(base_open, base_close)
        zone = (lo, hi)

    return zone


def _order_block_touch(direction: str, m15: pd.DataFrame, zone: tuple[float, float] | None, profile: dict[str, Any]) -> bool:
    if zone is None:
        return False
    row = m15.iloc[-2]
    low = float(row["low"])
    high = float(row["high"])
    close = float(row["close"])
    atr = max(float(row.get("atr14", 0.0) or 0.0), 1e-8)
    buffer = atr * max(0.0, float(profile.get("order_block_buffer_atr", 0.2) or 0.2))
    zone_low, zone_high = zone

    if direction == "BUY":
        touched = low <= (zone_high + buffer)
        accepted = close >= (zone_low - buffer)
        return bool(touched and accepted)

    touched = high >= (zone_low - buffer)
    accepted = close <= (zone_high + buffer)
    return bool(touched and accepted)


def _wick_rejection_trigger(direction: str, m5: pd.DataFrame, profile: dict[str, Any]) -> bool:
    row = m5.iloc[-2]
    high = float(row["high"])
    low = float(row["low"])
    open_ = float(row["open"])
    close = float(row["close"])
    candle_range = max(high - low, 1e-8)
    body = abs(close - open_)
    body_ratio = body / candle_range

    wick_min_ratio = max(0.1, float(profile.get("wick_entry_min_ratio", 0.45) or 0.45))
    body_max_ratio = min(0.9, max(0.05, float(profile.get("wick_entry_body_max_ratio", 0.45) or 0.45)))

    if body_ratio > body_max_ratio:
        return False

    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low

    if direction == "BUY":
        return bool(lower_wick / candle_range >= wick_min_ratio and close >= open_)

    return bool(upper_wick / candle_range >= wick_min_ratio and close <= open_)

def _safe_volume_ratio(df: pd.DataFrame) -> float:
    row = df.iloc[-2]
    baseline = max(float(row.get("volume_sma20", 0.0) or 0.0), 1e-8)
    return float(row.get("volume", 0.0) or 0.0) / baseline


def _di_bias(direction: str, row: pd.Series) -> float:
    plus_di = float(row.get("plus_di14", row.get("adx14", 0.0)))
    minus_di = float(row.get("minus_di14", row.get("adx14", 0.0)))
    if direction == "BUY":
        return plus_di - minus_di
    return minus_di - plus_di


def _metal_adaptive_reversal_ok(direction: str, h4_trend: str, m15: pd.DataFrame, m5: pd.DataFrame, profile: dict[str, Any]) -> bool:
    """Allow gold signals in strict mode during H4 sideway only when reversal confluence is strong."""
    if h4_trend != "sideway":
        return False

    m15_row = m15.iloc[-2]
    m15_prev = m15.iloc[-3]
    m5_row = m5.iloc[-2]
    m5_prev = m5.iloc[-3]

    close = float(m15_row["close"])
    bb_upper = float(m15_row["bb_upper"])
    bb_lower = float(m15_row["bb_lower"])
    band = max(bb_upper - bb_lower, 1e-8)
    rsi = float(m15_row["rsi14"])
    stoch = float(m5_row["stoch_k"])
    prev_stoch = float(m5_prev["stoch_k"])
    macd_hist = float(m15_row["macd_hist"])
    prev_macd_hist = float(m15_prev["macd_hist"])
    m15_di_bias = _di_bias(direction, m15_row)
    m5_di_bias = _di_bias(direction, m5_row)

    if direction == "BUY":
        near_extreme = close <= (bb_lower + 0.35 * band)
        rsi_extreme = rsi <= float(profile["rsi_buy_low"]) + 3.0
        trigger_turn = (stoch <= float(profile["stoch_buy_max"]) + 10.0 and stoch > prev_stoch) or macd_hist >= prev_macd_hist
        di_turn = m15_di_bias >= -3.0 and m5_di_bias >= -4.0
        return bool(near_extreme and rsi_extreme and trigger_turn and di_turn)

    near_extreme = close >= (bb_upper - 0.35 * band)
    rsi_extreme = rsi >= float(profile["rsi_sell_high"]) - 3.0
    trigger_turn = (stoch >= float(profile["stoch_sell_min"]) - 10.0 and stoch < prev_stoch) or macd_hist <= prev_macd_hist
    di_turn = m15_di_bias >= -3.0 and m5_di_bias >= -4.0
    return bool(near_extreme and rsi_extreme and trigger_turn and di_turn)


def _hard_filters(
    symbol: str,
    direction: str,
    mtf_data: dict[str, pd.DataFrame],
    cfg: Config,
    market_context: dict[str, Any] | None = None,
) -> tuple[bool, list[str], dict[str, str], dict[str, Any]]:
    asset_profile = cfg.asset_profile_for_symbol(symbol)
    h4 = mtf_data[cfg.timeframe_primary]
    h1 = mtf_data[cfg.timeframe_confirm]
    m15 = mtf_data[cfg.timeframe_setup]
    m5 = mtf_data[cfg.timeframe_trigger]

    h4_trend = detect_trend(h4)
    h1_trend = detect_trend(h1)
    m15_trend = detect_trend(m15)
    m5_trend = detect_trend(m5)

    summary = {
        "H4": h4_trend,
        "H1": h1_trend,
        "M15": m15_trend,
        "M5": m5_trend,
    }

    reasons: list[str] = []
    strict_mode = cfg.hard_filter_mode != "soft"
    adx_value = max(float(h1.iloc[-2]["adx14"]), float(m15.iloc[-2]["adx14"]))
    adx_minimum = float(asset_profile["adx_minimum"])
    if adx_value < adx_minimum:
        reasons.append(f"ADX too low ({adx_value:.2f} < {adx_minimum:.2f})")

    is_metal = str(asset_profile.get("asset_profile", "")) == "metal"
    metal_adaptive_reversal = is_metal and strict_mode and _metal_adaptive_reversal_ok(direction, h4_trend, m15, m5, asset_profile)
    metal_sideway_bias = False
    if is_metal and strict_mode and h4_trend == "sideway":
        if direction == "BUY":
            metal_sideway_bias = h1_trend == "bullish" or m15_trend == "bullish"
        else:
            metal_sideway_bias = h1_trend == "bearish" or m15_trend == "bearish"
    metal_override = metal_adaptive_reversal or metal_sideway_bias

    m15_row = m15.iloc[-2]
    entry_distance_atr = abs(float(m15_row["close"] - m15_row["ema20"])) / max(float(m15_row["atr14"]), 1e-8)
    base_entry_zone = float(asset_profile["entry_zone_max_atr"])
    allowed_entry_zone = base_entry_zone if strict_mode else base_entry_zone * 1.5
    # Gold can swing wider around EMA before reversal; keep strict mode but allow modestly wider zone.
    if is_metal and strict_mode:
        allowed_entry_zone = max(allowed_entry_zone, base_entry_zone * 1.35)
    if entry_distance_atr > allowed_entry_zone:
        reasons.append(f"Price too far from entry zone ({entry_distance_atr:.2f} ATR)")

    if direction == "BUY":
        if h4_trend == "bearish":
            reasons.append("H4 bearish conflict")
        elif h4_trend != "bullish":
            if strict_mode and not metal_override:
                reasons.append("H4 not bullish")
            elif not strict_mode and h1_trend != "bullish" and m15_trend != "bullish":
                reasons.append("H4 sideway without bullish bias")

        if h1_trend == "bearish" and (strict_mode or m15_trend != "bullish") and not metal_override:
            reasons.append("H1 bearish conflict")
        if strict_mode and m15_trend == "bearish" and m5_trend == "bearish" and not metal_override:
            reasons.append("Severe lower TF conflict")
    else:
        if h4_trend == "bullish":
            reasons.append("H4 bullish conflict")
        elif h4_trend != "bearish":
            if strict_mode and not metal_override:
                reasons.append("H4 not bearish")
            elif not strict_mode and h1_trend != "bearish" and m15_trend != "bearish":
                reasons.append("H4 sideway without bearish bias")

        if h1_trend == "bullish" and (strict_mode or m15_trend != "bearish") and not metal_override:
            reasons.append("H1 bullish conflict")
        if strict_mode and m15_trend == "bullish" and m5_trend == "bullish" and not metal_override:
            reasons.append("Severe lower TF conflict")

    if cfg.enable_volume_regime_filter:
        ratios = {
            "M5": _safe_volume_ratio(m5),
            "M15": _safe_volume_ratio(m15),
            "H1": _safe_volume_ratio(h1),
        }
        volume_checks = {
            "M5": ratios["M5"] >= float(cfg.volume_ratio_m5_min),
            "M15": ratios["M15"] >= float(cfg.volume_ratio_m15_min),
            "H1": ratios["H1"] >= float(cfg.volume_ratio_h1_min),
        }
        passes = sum(bool(v) for v in volume_checks.values())
        summary["VOL"] = ", ".join(f"{k}:{ratios[k]:.2f}" for k in ("M5", "M15", "H1"))
        if passes < int(cfg.volume_min_confirmations):
            reasons.append(
                f"Volume regime weak ({passes}/3 < {int(cfg.volume_min_confirmations)}): "
                f"M5={ratios['M5']:.2f}, M15={ratios['M15']:.2f}, H1={ratios['H1']:.2f}"
            )

    if cfg.enable_news_filter and market_context:
        if bool(market_context.get("blocked", False)):
            reason = str(market_context.get("reason", "news_blocked"))
            reasons.append(f"News risk block ({reason})")

    return len(reasons) == 0, reasons, summary, asset_profile



def _build_indicator_snapshot(m15: pd.DataFrame) -> dict[str, float]:
    row = m15.iloc[-2]
    return {
        "rsi14": float(row["rsi14"]),
        "macd": float(row["macd"]),
        "macd_signal": float(row["macd_signal"]),
        "macd_hist": float(row["macd_hist"]),
        "adx14": float(row["adx14"]),
        "atr14": float(row["atr14"]),
    }


def _evaluate_direction(
    symbol: str,
    normalized_symbol: str,
    direction: str,
    mtf_data: dict[str, pd.DataFrame],
    cfg: Config,
    market_context: dict[str, Any] | None = None,
) -> SignalResult:
    hard_ok, hard_reasons, tf_summary, asset_profile = _hard_filters(symbol, direction, mtf_data, cfg, market_context=market_context)

    m15 = mtf_data[cfg.timeframe_setup]
    m5 = mtf_data[cfg.timeframe_trigger]
    h4 = mtf_data[cfg.timeframe_primary]
    h1 = mtf_data[cfg.timeframe_confirm]

    price = float(m5.iloc[-2]["close"])
    timestamp = _time(m5, -2)

    structure = detect_price_structure(m15)
    support, resistance = detect_support_resistance(m15)

    m15_row = _row(m15, -2)
    m15_prev = _row(m15, -3)
    m5_row = _row(m5, -2)
    m5_prev = _row(m5, -3)

    adx_value = max(float(h1.iloc[-2]["adx14"]), float(m15.iloc[-2]["adx14"]))
    atr_baseline = float(m15["atr14"].tail(100).median()) if len(m15) >= 100 else float(m15["atr14"].median())

    context: dict[str, Any] = {
        "symbol": symbol,
        "direction": direction,
        "asset_profile": asset_profile,
        "h4_trend": detect_trend(h4),
        "h1_trend": detect_trend(h1),
        "m15": m15_row,
        "m15_prev": m15_prev,
        "m5": m5_row,
        "m5_prev": m5_prev,
        "structure": structure,
        "adx_value": adx_value,
        "atr_baseline": atr_baseline,
    }
    score, component_scores, reasons = calculate_confidence(context, cfg)

    if not hard_ok:
        trade_plan = build_trade_plan(
            direction=direction,
            entry_price=price,
            atr=float(m15.iloc[-2]["atr14"]),
            account_balance=cfg.account_balance,
            risk_per_trade_pct=float(cfg.risk_per_trade_pct) * float(asset_profile.get("risk_pct_multiplier", 1.0)),
            sl_atr_multiplier=float(asset_profile["sl_atr_multiplier"]),
            target_rr=float(asset_profile["target_rr"]),
        )
        return SignalResult(
            symbol=symbol,
            normalized_symbol=normalized_symbol,
            direction=direction,
            score=score,
            category="ignore",
            price=price,
            timestamp=timestamp,
            timeframe_summary=tf_summary,
            reason_summary="; ".join(reasons + [f"hard_fail[{asset_profile['asset_profile']}]"]),
            indicator_snapshot=_build_indicator_snapshot(m15),
            hard_filters_passed=False,
            hard_filter_reasons=hard_reasons,
            component_scores=component_scores,
            trade_plan=asdict(trade_plan),
        )

    support, resistance = detect_support_resistance(m15)

    m15_row = _row(m15, -2)
    m15_prev = _row(m15, -3)
    m5_row = _row(m5, -2)
    m5_prev = _row(m5, -3)

    adx_value = max(float(h1.iloc[-2]["adx14"]), float(m15.iloc[-2]["adx14"]))
    atr_baseline = float(m15["atr14"].tail(100).median()) if len(m15) >= 100 else float(m15["atr14"].median())

    context: dict[str, Any] = {
        "symbol": symbol,
        "direction": direction,
        "asset_profile": asset_profile,
        "h4_trend": detect_trend(h4),
        "h1_trend": detect_trend(h1),
        "m15": m15_row,
        "m15_prev": m15_prev,
        "m5": m5_row,
        "m5_prev": m5_prev,
        "structure": structure,
        "adx_value": adx_value,
        "atr_baseline": atr_baseline,
    }
    score, component_scores, reasons = calculate_confidence(context, cfg)

    enable_order_block = bool(asset_profile.get("enable_order_block", True))
    enable_wick_entry = bool(asset_profile.get("enable_wick_entry", True))

    order_block_zone = _find_order_block_zone(direction, m15, asset_profile) if enable_order_block else None
    order_block_touch = _order_block_touch(direction, m15, order_block_zone, asset_profile) if enable_order_block else False
    wick_entry = _wick_rejection_trigger(direction, m5, asset_profile) if enable_wick_entry else False

    trigger_checks: list[tuple[str, bool]] = [
        ("momentum", _momentum_candle(direction, m5)),
        ("macd", _macd_cross(direction, m5)),
        ("stoch", _stoch_cross(direction, m5)),
        ("volume", _volume_spike(m5, float(asset_profile["volume_spike_ratio"]))),
        ("order_block", order_block_touch),
        ("wick_entry", wick_entry),
    ]
    trigger_count = sum(1 for _, passed in trigger_checks if passed)
    trigger_total = len(trigger_checks)

    min_triggers = max(1, min(trigger_total, int(asset_profile["m5_min_triggers"])))
    if cfg.hard_filter_mode == "soft":
        min_triggers = 1
    risk_pct = float(cfg.risk_per_trade_pct) * float(asset_profile.get("risk_pct_multiplier", 1.0))
    sl_atr_multiplier = float(asset_profile["sl_atr_multiplier"])
    target_rr = float(asset_profile["target_rr"])

    if trigger_count < min_triggers:
        reasons.append(f"trigger={trigger_count}/{trigger_total}")
        trade_plan = build_trade_plan(
            direction=direction,
            entry_price=price,
            atr=float(m15.iloc[-2]["atr14"]),
            account_balance=cfg.account_balance,
            risk_per_trade_pct=risk_pct,
            sl_atr_multiplier=sl_atr_multiplier,
            target_rr=target_rr,
        )
        return SignalResult(
            symbol=symbol,
            normalized_symbol=normalized_symbol,
            direction=direction,
            score=score,
            category="candidate" if score >= cfg.watchlist_threshold else "ignore",
            price=price,
            timestamp=timestamp,
            timeframe_summary=tf_summary,
            reason_summary="; ".join(reasons),
            indicator_snapshot=_build_indicator_snapshot(m15),
            hard_filters_passed=True,
            hard_filter_reasons=[f"M5 trigger < {min_triggers}/{trigger_total}"],
            component_scores=component_scores,
            trade_plan=asdict(trade_plan),
        )

    if support is not None:
        reasons.append(f"support={support:.2f}")
    if resistance is not None:
        reasons.append(f"resistance={resistance:.2f}")
    if order_block_zone is not None:
        reasons.append(f"ob_zone={order_block_zone[0]:.2f}-{order_block_zone[1]:.2f}")
    if order_block_touch:
        reasons.append("ob_touch")
    if wick_entry:
        reasons.append("wick_entry")

    category = classify_score(
        score=score,
        watchlist_threshold=cfg.watchlist_threshold,
        alert_threshold=cfg.alert_threshold,
        strong_alert_threshold=cfg.strong_alert_threshold,
        premium_alert_threshold=cfg.premium_alert_threshold,
    )
    trade_plan = build_trade_plan(
        direction=direction,
        entry_price=price,
        atr=float(m15.iloc[-2]["atr14"]),
        account_balance=cfg.account_balance,
        risk_per_trade_pct=risk_pct,
        sl_atr_multiplier=sl_atr_multiplier,
        target_rr=target_rr,
    )

    return SignalResult(
        symbol=symbol,
        normalized_symbol=normalized_symbol,
        direction=direction,
        score=score,
        category=category,
        price=price,
        timestamp=timestamp,
        timeframe_summary=tf_summary,
        reason_summary="; ".join(reasons),
        indicator_snapshot=_build_indicator_snapshot(m15),
        hard_filters_passed=True,
        hard_filter_reasons=[],
        component_scores=component_scores,
        trade_plan=asdict(trade_plan),
    )


def evaluate_buy_signal(
    symbol: str,
    normalized_symbol: str,
    mtf_data: dict[str, pd.DataFrame],
    cfg: Config,
    market_context: dict[str, Any] | None = None,
) -> SignalResult:
    """Evaluate BUY signal using MTF logic + hard filters + scoring."""
    return _evaluate_direction(symbol, normalized_symbol, "BUY", mtf_data, cfg, market_context=market_context)


def evaluate_sell_signal(
    symbol: str,
    normalized_symbol: str,
    mtf_data: dict[str, pd.DataFrame],
    cfg: Config,
    market_context: dict[str, Any] | None = None,
) -> SignalResult:
    """Evaluate SELL signal using MTF logic + hard filters + scoring."""
    return _evaluate_direction(symbol, normalized_symbol, "SELL", mtf_data, cfg, market_context=market_context)
