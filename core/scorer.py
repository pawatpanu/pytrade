from __future__ import annotations

from typing import Any

from config import Config


def _score_higher_tf(direction: str, h4_trend: str, h1_trend: str) -> float:
    if direction == "BUY":
        if h4_trend != "bullish":
            return 0.0
        if h1_trend == "bullish":
            return 20.0
        if h1_trend == "sideway":
            return 10.0
        return 0.0

    if h4_trend != "bearish":
        return 0.0
    if h1_trend == "bearish":
        return 20.0
    if h1_trend == "sideway":
        return 10.0
    return 0.0


def _score_ema(direction: str, row: dict[str, float]) -> float:
    close = row["close"]
    ema20 = row["ema20"]
    ema50 = row["ema50"]
    ema200 = row["ema200"]

    if direction == "BUY":
        if ema20 > ema50 > ema200:
            if close >= ema20:
                return 15.0
            if ema50 <= close < ema20:
                return 13.0
            return 8.0
        return 4.0

    if ema20 < ema50 < ema200:
        if close <= ema20:
            return 15.0
        if ema20 < close <= ema50:
            return 13.0
        return 8.0
    return 4.0


def _score_adx(adx: float) -> float:
    if adx >= 30:
        return 10.0
    if adx >= 25:
        return 8.0
    if adx >= 20:
        return 6.0
    if adx >= 18:
        return 4.0
    return 0.0


def _score_structure(direction: str, structure: str) -> float:
    if direction == "BUY":
        if structure == "bullish":
            return 10.0
        if structure == "mixed":
            return 5.0
        return 0.0

    if structure == "bearish":
        return 10.0
    if structure == "mixed":
        return 5.0
    return 0.0


def _score_setup_quality(direction: str, row: dict[str, float], prev_row: dict[str, float]) -> float:
    close = row["close"]
    open_ = row["open"]
    low = row["low"]
    high = row["high"]
    ema20 = row["ema20"]
    ema50 = row["ema50"]
    atr = max(row["atr14"], 1e-8)

    near_pullback_zone = min(abs(close - ema20), abs(close - ema50)) <= 0.8 * atr

    if direction == "BUY":
        bounced = close > open_ and low <= ema20 and close > prev_row["close"]
        if near_pullback_zone and bounced:
            return 10.0
        if near_pullback_zone:
            return 7.0
        return 2.0

    rejected = close < open_ and high >= ema20 and close < prev_row["close"]
    if near_pullback_zone and rejected:
        return 10.0
    if near_pullback_zone:
        return 7.0
    return 2.0


def _score_rsi(direction: str, rsi: float, prev_rsi: float, cfg: Config) -> float:
    rising = rsi > prev_rsi
    falling = rsi < prev_rsi

    if direction == "BUY":
        if cfg.rsi_buy_low <= rsi <= cfg.rsi_buy_high and rising:
            return 8.0
        if rsi < 35 and rising:
            return 8.0
        if rsi > 75:
            return 1.0
        if 60 < rsi <= 70:
            return 4.0
        return 3.0

    if cfg.rsi_sell_low <= rsi <= cfg.rsi_sell_high and falling:
        return 8.0
    if rsi > 65 and falling:
        return 8.0
    if rsi < 25:
        return 1.0
    if 30 <= rsi < 40:
        return 4.0
    return 3.0


def _score_macd(direction: str, row: dict[str, float], prev_row: dict[str, float]) -> float:
    cross_up = prev_row["macd"] <= prev_row["macd_signal"] and row["macd"] > row["macd_signal"]
    cross_down = prev_row["macd"] >= prev_row["macd_signal"] and row["macd"] < row["macd_signal"]

    if direction == "BUY":
        if cross_up and row["macd_hist"] > 0:
            return 8.0
        if row["macd_hist"] > prev_row["macd_hist"]:
            return 5.0
        return 1.0

    if cross_down and row["macd_hist"] < 0:
        return 8.0
    if row["macd_hist"] < prev_row["macd_hist"]:
        return 5.0
    return 1.0


def _score_stoch(direction: str, row: dict[str, float], prev_row: dict[str, float]) -> float:
    cross_up = prev_row["stoch_k"] <= prev_row["stoch_d"] and row["stoch_k"] > row["stoch_d"]
    cross_down = prev_row["stoch_k"] >= prev_row["stoch_d"] and row["stoch_k"] < row["stoch_d"]

    if direction == "BUY":
        if cross_up and row["stoch_k"] < 30:
            return 5.0
        if cross_up:
            return 3.0
        return 0.0

    if cross_down and row["stoch_k"] > 70:
        return 5.0
    if cross_down:
        return 3.0
    return 0.0


def _score_volume(row: dict[str, float]) -> float:
    if row["volume"] >= 1.2 * row["volume_sma20"]:
        return 5.0
    if row["volume"] >= row["volume_sma20"]:
        return 3.0
    return 1.0


def _score_bollinger(direction: str, row: dict[str, float]) -> float:
    close = row["close"]
    upper = row["bb_upper"]
    lower = row["bb_lower"]
    middle = row["bb_middle"]

    if direction == "BUY":
        if close > upper:
            return 1.0
        if middle <= close <= upper:
            return 4.0
        if lower <= close < middle:
            return 3.0
        return 2.0

    if close < lower:
        return 1.0
    if lower <= close <= middle:
        return 4.0
    if middle < close <= upper:
        return 3.0
    return 2.0


def _score_atr(row: dict[str, float], atr_baseline: float) -> float:
    atr = max(row["atr14"], 1e-8)
    ratio = atr / max(atr_baseline, 1e-8)
    if 0.7 <= ratio <= 1.8:
        return 5.0
    if 0.5 <= ratio <= 2.2:
        return 3.0
    return 1.0


def calculate_confidence(signal_context: dict[str, Any], config: Config) -> tuple[float, dict[str, float], list[str]]:
    """Calculate weighted rule-based confidence score (not a win rate)."""
    direction = signal_context["direction"]
    h4_trend = signal_context["h4_trend"]
    h1_trend = signal_context["h1_trend"]
    m15 = signal_context["m15"]
    m15_prev = signal_context["m15_prev"]
    m5 = signal_context["m5"]
    m5_prev = signal_context["m5_prev"]
    structure = signal_context["structure"]
    adx_value = signal_context["adx_value"]
    atr_baseline = signal_context["atr_baseline"]

    scores = {
        "higher_tf": _score_higher_tf(direction, h4_trend, h1_trend),
        "ema_alignment": _score_ema(direction, m15),
        "adx_strength": _score_adx(adx_value),
        "market_structure": _score_structure(direction, structure),
        "setup_quality": _score_setup_quality(direction, m15, m15_prev),
        "rsi_context": _score_rsi(direction, m15["rsi14"], m15_prev["rsi14"], config),
        "macd_confirmation": _score_macd(direction, m15, m15_prev),
        "stoch_trigger": _score_stoch(direction, m5, m5_prev),
        "volume_confirmation": _score_volume(m5),
        "bollinger_context": _score_bollinger(direction, m15),
        "atr_suitability": _score_atr(m15, atr_baseline),
    }

    total = 0.0
    reasons: list[str] = []
    for key, raw_score in scores.items():
        max_weight = float(config.weights.get(key, 0))
        if max_weight <= 0:
            continue
        # Raw scorers already aligned with requested max points; clamp for safety.
        clamped = max(0.0, min(raw_score, max_weight))
        scores[key] = round(clamped, 2)
        total += clamped
        reasons.append(f"{key}={clamped:.1f}/{max_weight:.0f}")

    return round(min(total, 100.0), 2), scores, reasons
