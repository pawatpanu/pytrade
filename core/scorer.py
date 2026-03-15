from __future__ import annotations

from typing import Any

from config import Config


def _score_higher_tf(direction: str, h4_trend: str, h1_trend: str, profile: dict[str, Any]) -> float:
    sideway_score = float(profile.get("higher_tf_sideway_score", 10.0))
    if direction == "BUY":
        if h4_trend != "bullish":
            return 0.0
        if h1_trend == "bullish":
            return 20.0
        if h1_trend == "sideway":
            return sideway_score
        return 0.0

    if h4_trend != "bearish":
        return 0.0
    if h1_trend == "bearish":
        return 20.0
    if h1_trend == "sideway":
        return sideway_score
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


def _score_adx(adx: float, profile: dict[str, Any]) -> float:
    minimum = float(profile["adx_minimum"])
    if adx >= minimum + 14:
        return 10.0
    if adx >= minimum + 10:
        return 8.0
    if adx >= minimum + 6:
        return 6.0
    if adx >= minimum + 2:
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


def _score_structure_profile(direction: str, structure: str, profile: dict[str, Any]) -> float:
    mixed_score = float(profile.get("structure_mixed_score", 5.0))
    if direction == "BUY":
        if structure == "bullish":
            return 10.0
        if structure == "mixed":
            return mixed_score
        return 0.0

    if structure == "bearish":
        return 10.0
    if structure == "mixed":
        return mixed_score
    return 0.0


def _score_setup_quality(direction: str, row: dict[str, float], prev_row: dict[str, float], profile: dict[str, Any]) -> float:
    close = row["close"]
    open_ = row["open"]
    low = row["low"]
    high = row["high"]
    ema20 = row["ema20"]
    ema50 = row["ema50"]
    atr = max(row["atr14"], 1e-8)
    pullback_atr = float(profile["setup_pullback_atr"])
    style = str(profile.get("setup_style", "pullback"))
    body = abs(close - open_)
    candle_range = max(high - low, 1e-8)
    body_ratio = body / candle_range
    breakout_body_min = float(profile.get("breakout_body_min_ratio", 0.45))
    reversal_wick_ratio = float(profile.get("reversal_wick_ratio", 0.45))

    near_pullback_zone = min(abs(close - ema20), abs(close - ema50)) <= pullback_atr * atr
    breakout_up = close > max(prev_row["high"], prev_row["close"]) and body_ratio >= breakout_body_min
    breakout_down = close < min(prev_row["low"], prev_row["close"]) and body_ratio >= breakout_body_min
    lower_wick = min(open_, close) - low
    upper_wick = high - max(open_, close)
    bullish_reversal = lower_wick / candle_range >= reversal_wick_ratio and close > open_ and close >= ema20
    bearish_reversal = upper_wick / candle_range >= reversal_wick_ratio and close < open_ and close <= ema20

    if style == "breakout":
        if direction == "BUY":
            if breakout_up:
                return 10.0
            if near_pullback_zone and close >= ema20:
                return 6.0
            return 2.0
        if breakout_down:
            return 10.0
        if near_pullback_zone and close <= ema20:
            return 6.0
        return 2.0

    if style == "reversal":
        if direction == "BUY":
            if bullish_reversal:
                return 10.0
            if near_pullback_zone and close > open_:
                return 7.0
            return 2.0
        if bearish_reversal:
            return 10.0
        if near_pullback_zone and close < open_:
            return 7.0
        return 2.0

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


def _score_rsi(direction: str, rsi: float, prev_rsi: float, profile: dict[str, Any], cfg: Config) -> float:
    rising = rsi > prev_rsi
    falling = rsi < prev_rsi
    buy_low = float(profile.get("rsi_buy_low", cfg.rsi_buy_low))
    buy_high = float(profile.get("rsi_buy_high", cfg.rsi_buy_high))
    sell_low = float(profile.get("rsi_sell_low", cfg.rsi_sell_low))
    sell_high = float(profile.get("rsi_sell_high", cfg.rsi_sell_high))

    if direction == "BUY":
        if buy_low <= rsi <= buy_high and rising:
            return 8.0
        if rsi < buy_low - 10 and rising:
            return 8.0
        if rsi > buy_high + 10:
            return 1.0
        if buy_high < rsi <= buy_high + 8:
            return 4.0
        return 3.0

    if sell_low <= rsi <= sell_high and falling:
        return 8.0
    if rsi > sell_high + 10 and falling:
        return 8.0
    if rsi < max(10.0, sell_low - 15):
        return 1.0
    if max(10.0, sell_low - 10) <= rsi < sell_low:
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


def _score_macd_profile(direction: str, row: dict[str, float], prev_row: dict[str, float], profile: dict[str, Any]) -> float:
    mode = str(profile.get("macd_mode", "cross"))
    base_score = _score_macd(direction, row, prev_row)
    if mode == "momentum":
        if direction == "BUY":
            if row["macd"] > row["macd_signal"] and row["macd_hist"] > prev_row["macd_hist"]:
                return max(base_score, 8.0)
            if row["macd_hist"] > prev_row["macd_hist"]:
                return max(base_score, 6.0)
        else:
            if row["macd"] < row["macd_signal"] and row["macd_hist"] < prev_row["macd_hist"]:
                return max(base_score, 8.0)
            if row["macd_hist"] < prev_row["macd_hist"]:
                return max(base_score, 6.0)
    return base_score


def _score_stoch(direction: str, row: dict[str, float], prev_row: dict[str, float], profile: dict[str, Any]) -> float:
    cross_up = prev_row["stoch_k"] <= prev_row["stoch_d"] and row["stoch_k"] > row["stoch_d"]
    cross_down = prev_row["stoch_k"] >= prev_row["stoch_d"] and row["stoch_k"] < row["stoch_d"]
    stoch_buy_max = float(profile["stoch_buy_max"])
    stoch_sell_min = float(profile["stoch_sell_min"])

    if direction == "BUY":
        if cross_up and row["stoch_k"] < stoch_buy_max:
            return 5.0
        if cross_up:
            return 3.0
        return 0.0

    if cross_down and row["stoch_k"] > stoch_sell_min:
        return 5.0
    if cross_down:
        return 3.0
    return 0.0


def _score_stoch_profile(direction: str, row: dict[str, float], prev_row: dict[str, float], profile: dict[str, Any]) -> float:
    mode = str(profile.get("stoch_mode", "cross"))
    base_score = _score_stoch(direction, row, prev_row, profile)
    if mode == "extreme":
        if direction == "BUY":
            if row["stoch_k"] < float(profile["stoch_buy_max"]):
                if row["stoch_k"] > prev_row["stoch_k"]:
                    return max(base_score, 5.0)
                return max(base_score, 3.0)
        else:
            if row["stoch_k"] > float(profile["stoch_sell_min"]):
                if row["stoch_k"] < prev_row["stoch_k"]:
                    return max(base_score, 5.0)
                return max(base_score, 3.0)
    return base_score


def _score_volume(row: dict[str, float], profile: dict[str, Any]) -> float:
    volume = float(row["volume"])
    baseline = max(float(row["volume_sma20"]), 1e-8)
    ratio = volume / baseline
    spike_ratio = float(profile["volume_spike_ratio"])
    if ratio >= spike_ratio:
        return 5.0
    if ratio >= max(1.0, spike_ratio - 0.15):
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


def _score_bollinger_profile(direction: str, row: dict[str, float], profile: dict[str, Any]) -> float:
    mode = str(profile.get("bollinger_mode", "balanced"))
    close = row["close"]
    upper = row["bb_upper"]
    lower = row["bb_lower"]
    middle = row["bb_middle"]
    if mode == "trend":
        if direction == "BUY":
            if close >= upper:
                return 4.0
            if close >= middle:
                return 3.0
            return 1.0
        if close <= lower:
            return 4.0
        if close <= middle:
            return 3.0
        return 1.0
    if mode == "mean_revert":
        if direction == "BUY":
            if lower <= close <= middle:
                return 4.0
            if close < lower:
                return 3.0
            return 1.0
        if middle <= close <= upper:
            return 4.0
        if close > upper:
            return 3.0
        return 1.0
    return _score_bollinger(direction, row)


def _score_atr(row: dict[str, float], atr_baseline: float, profile: dict[str, Any]) -> float:
    atr = max(row["atr14"], 1e-8)
    ratio = atr / max(atr_baseline, 1e-8)
    pref_low = float(profile["atr_ratio_pref_low"])
    pref_high = float(profile["atr_ratio_pref_high"])
    ok_low = float(profile["atr_ratio_ok_low"])
    ok_high = float(profile["atr_ratio_ok_high"])
    if pref_low <= ratio <= pref_high:
        return 5.0
    if ok_low <= ratio <= ok_high:
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
    symbol = str(signal_context.get("symbol", ""))
    asset_profile = signal_context.get("asset_profile") or config.asset_profile_for_symbol(symbol)

    scores = {
        "higher_tf": _score_higher_tf(direction, h4_trend, h1_trend, asset_profile),
        "ema_alignment": _score_ema(direction, m15),
        "adx_strength": _score_adx(adx_value, asset_profile),
        "market_structure": _score_structure_profile(direction, structure, asset_profile),
        "setup_quality": _score_setup_quality(direction, m15, m15_prev, asset_profile),
        "rsi_context": _score_rsi(direction, m15["rsi14"], m15_prev["rsi14"], asset_profile, config),
        "macd_confirmation": _score_macd_profile(direction, m15, m15_prev, asset_profile),
        "stoch_trigger": _score_stoch_profile(direction, m5, m5_prev, asset_profile),
        "volume_confirmation": _score_volume(m5, asset_profile),
        "bollinger_context": _score_bollinger_profile(direction, m15, asset_profile),
        "atr_suitability": _score_atr(m15, atr_baseline, asset_profile),
    }

    total = 0.0
    reasons: list[str] = [f"asset_profile={asset_profile.get('asset_profile', 'default')}"]
    for key, raw_score in scores.items():
        max_weight = float(config.weights.get(key, 0))
        if max_weight <= 0:
            continue
        clamped = max(0.0, min(raw_score, max_weight))
        scores[key] = round(clamped, 2)
        total += clamped
        reasons.append(f"{key}={clamped:.1f}/{max_weight:.0f}")

    return round(min(total, 100.0), 2), scores, reasons
