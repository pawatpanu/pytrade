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


def _volume_spike(df: pd.DataFrame) -> bool:
    row = df.iloc[-2]
    return bool(row["volume"] >= 1.2 * row["volume_sma20"])


def _hard_filters(direction: str, mtf_data: dict[str, pd.DataFrame], cfg: Config) -> tuple[bool, list[str], dict[str, str]]:
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
    if adx_value < cfg.adx_minimum:
        reasons.append(f"ADX too low ({adx_value:.2f} < {cfg.adx_minimum})")

    m15_row = m15.iloc[-2]
    entry_distance_atr = abs(float(m15_row["close"] - m15_row["ema20"])) / max(float(m15_row["atr14"]), 1e-8)
    allowed_entry_zone = cfg.entry_zone_max_atr if strict_mode else cfg.entry_zone_max_atr * 1.5
    if entry_distance_atr > allowed_entry_zone:
        reasons.append(f"Price too far from entry zone ({entry_distance_atr:.2f} ATR)")

    if direction == "BUY":
        if h4_trend == "bearish":
            reasons.append("H4 bearish conflict")
        elif h4_trend != "bullish":
            if strict_mode:
                reasons.append("H4 not bullish")
            elif h1_trend != "bullish" and m15_trend != "bullish":
                reasons.append("H4 sideway without bullish bias")

        if h1_trend == "bearish" and (strict_mode or m15_trend != "bullish"):
            reasons.append("H1 bearish conflict")
        if m15_trend == "bearish" and m5_trend == "bearish":
            reasons.append("Severe lower TF conflict")
    else:
        if h4_trend == "bullish":
            reasons.append("H4 bullish conflict")
        elif h4_trend != "bearish":
            if strict_mode:
                reasons.append("H4 not bearish")
            elif h1_trend != "bearish" and m15_trend != "bearish":
                reasons.append("H4 sideway without bearish bias")

        if h1_trend == "bullish" and (strict_mode or m15_trend != "bearish"):
            reasons.append("H1 bullish conflict")
        if m15_trend == "bullish" and m5_trend == "bullish":
            reasons.append("Severe lower TF conflict")

    return len(reasons) == 0, reasons, summary


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
) -> SignalResult:
    hard_ok, hard_reasons, tf_summary = _hard_filters(direction, mtf_data, cfg)

    m15 = mtf_data[cfg.timeframe_setup]
    m5 = mtf_data[cfg.timeframe_trigger]
    h4 = mtf_data[cfg.timeframe_primary]
    h1 = mtf_data[cfg.timeframe_confirm]

    price = float(m5.iloc[-2]["close"])
    timestamp = _time(m5, -2)

    if not hard_ok:
        return SignalResult(
            symbol=symbol,
            normalized_symbol=normalized_symbol,
            direction=direction,
            score=0.0,
            category="ignore",
            price=price,
            timestamp=timestamp,
            timeframe_summary=tf_summary,
            reason_summary="Hard filters failed",
            indicator_snapshot=_build_indicator_snapshot(m15),
            hard_filters_passed=False,
            hard_filter_reasons=hard_reasons,
            component_scores={},
        )

    structure = detect_price_structure(m15)
    support, resistance = detect_support_resistance(m15)

    m15_row = _row(m15, -2)
    m15_prev = _row(m15, -3)
    m5_row = _row(m5, -2)
    m5_prev = _row(m5, -3)

    adx_value = max(float(h1.iloc[-2]["adx14"]), float(m15.iloc[-2]["adx14"]))
    atr_baseline = float(m15["atr14"].tail(100).median()) if len(m15) >= 100 else float(m15["atr14"].median())

    context: dict[str, Any] = {
        "direction": direction,
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

    trigger_conditions = [
        _momentum_candle(direction, m5),
        _macd_cross(direction, m5),
        _stoch_cross(direction, m5),
        _volume_spike(m5),
    ]
    trigger_count = sum(bool(x) for x in trigger_conditions)

    min_triggers = max(1, min(4, cfg.m5_min_triggers))
    if trigger_count < min_triggers:
        reasons.append(f"trigger={trigger_count}/4")
        trade_plan = build_trade_plan(
            direction=direction,
            entry_price=price,
            atr=float(m15.iloc[-2]["atr14"]),
            account_balance=cfg.account_balance,
            risk_per_trade_pct=cfg.risk_per_trade_pct,
            sl_atr_multiplier=cfg.sl_atr_multiplier,
            target_rr=cfg.target_rr,
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
            hard_filter_reasons=[f"M5 trigger < {min_triggers}/4"],
            component_scores=component_scores,
            trade_plan=asdict(trade_plan),
        )

    if support is not None:
        reasons.append(f"support={support:.2f}")
    if resistance is not None:
        reasons.append(f"resistance={resistance:.2f}")

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
        risk_per_trade_pct=cfg.risk_per_trade_pct,
        sl_atr_multiplier=cfg.sl_atr_multiplier,
        target_rr=cfg.target_rr,
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


def evaluate_buy_signal(symbol: str, normalized_symbol: str, mtf_data: dict[str, pd.DataFrame], cfg: Config) -> SignalResult:
    """Evaluate BUY signal using MTF logic + hard filters + scoring."""
    return _evaluate_direction(symbol, normalized_symbol, "BUY", mtf_data, cfg)


def evaluate_sell_signal(symbol: str, normalized_symbol: str, mtf_data: dict[str, pd.DataFrame], cfg: Config) -> SignalResult:
    """Evaluate SELL signal using MTF logic + hard filters + scoring."""
    return _evaluate_direction(symbol, normalized_symbol, "SELL", mtf_data, cfg)
