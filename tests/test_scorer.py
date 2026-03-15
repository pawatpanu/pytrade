from __future__ import annotations

from config import Config
from core.scorer import calculate_confidence


def _build_context(direction: str = "BUY", symbol: str = "BTCUSDm") -> dict:
    return {
        "symbol": symbol,
        "direction": direction,
        "h4_trend": "bullish" if direction == "BUY" else "bearish",
        "h1_trend": "bullish" if direction == "BUY" else "bearish",
        "structure": "bullish" if direction == "BUY" else "bearish",
        "adx_value": 28.0,
        "atr_baseline": 100.0,
        "m15": {
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0 if direction == "BUY" else 99.0,
            "ema20": 100.0,
            "ema50": 98.0 if direction == "BUY" else 100.0,
            "ema200": 95.0 if direction == "BUY" else 105.0,
            "atr14": 95.0,
            "rsi14": 52.0 if direction == "BUY" else 48.0,
            "macd": 1.2 if direction == "BUY" else -1.2,
            "macd_signal": 1.0 if direction == "BUY" else -1.0,
            "macd_hist": 0.2 if direction == "BUY" else -0.2,
            "bb_upper": 110.0,
            "bb_middle": 100.0,
            "bb_lower": 90.0,
        },
        "m15_prev": {
            "open": 99.8,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0 if direction == "BUY" else 100.0,
            "ema20": 99.5,
            "ema50": 98.0 if direction == "BUY" else 100.0,
            "ema200": 95.0 if direction == "BUY" else 105.0,
            "atr14": 94.0,
            "rsi14": 49.0 if direction == "BUY" else 50.0,
            "macd": 0.8 if direction == "BUY" else -0.8,
            "macd_signal": 0.9 if direction == "BUY" else -0.9,
            "macd_hist": 0.1 if direction == "BUY" else -0.1,
            "bb_upper": 109.0,
            "bb_middle": 99.0,
            "bb_lower": 89.0,
        },
        "m5": {
            "volume": 150.0,
            "volume_sma20": 100.0,
            "stoch_k": 25.0 if direction == "BUY" else 75.0,
            "stoch_d": 20.0 if direction == "BUY" else 80.0,
        },
        "m5_prev": {
            "volume": 100.0,
            "volume_sma20": 95.0,
            "stoch_k": 15.0 if direction == "BUY" else 85.0,
            "stoch_d": 18.0 if direction == "BUY" else 82.0,
        },
    }


def test_confidence_score_is_in_range() -> None:
    cfg = Config()
    score, components, reasons = calculate_confidence(_build_context("BUY"), cfg)

    assert 0 <= score <= 100
    assert len(components) == 11
    assert reasons
    assert reasons[0].startswith("asset_profile=")


def test_confidence_score_degrades_with_conflict() -> None:
    cfg = Config()
    good_context = _build_context("BUY")
    bad_context = _build_context("BUY")
    bad_context["h1_trend"] = "bearish"
    bad_context["structure"] = "bearish"

    good_score, _, _ = calculate_confidence(good_context, cfg)
    bad_score, _, _ = calculate_confidence(bad_context, cfg)

    assert bad_score < good_score


def test_asset_profile_detection() -> None:
    cfg = Config()
    assert cfg.asset_profile_name("BTCUSDm") == "crypto_major"
    assert cfg.asset_profile_name("XAUUSDm") == "metal"
    assert cfg.asset_profile_name("EURUSDm") == "fx_major"


def test_asset_profile_changes_scoring_behavior() -> None:
    cfg = Config()
    crypto_context = _build_context("BUY", symbol="BTCUSDm")
    fx_context = _build_context("BUY", symbol="EURUSDm")
    crypto_context["m5"]["volume"] = 112.0
    crypto_context["m5"]["volume_sma20"] = 100.0
    fx_context["m5"]["volume"] = 112.0
    fx_context["m5"]["volume_sma20"] = 100.0

    _, crypto_components, crypto_reasons = calculate_confidence(crypto_context, cfg)
    _, fx_components, fx_reasons = calculate_confidence(fx_context, cfg)

    assert crypto_components["volume_confirmation"] < fx_components["volume_confirmation"]
    assert crypto_reasons[0] == "asset_profile=crypto_major"
    assert fx_reasons[0] == "asset_profile=fx_major"


def test_crypto_breakout_setup_scores_higher_than_fx_pullback_on_same_candle() -> None:
    cfg = Config()
    crypto_context = _build_context("BUY", symbol="BTCUSDm")
    fx_context = _build_context("BUY", symbol="EURUSDm")

    crypto_context["m15"].update({"open": 101.0, "low": 100.8, "high": 106.0, "close": 105.6, "ema20": 100.0, "ema50": 98.0})
    crypto_context["m15_prev"].update({"high": 101.0, "close": 100.5})
    fx_context["m15"].update({"open": 101.0, "low": 100.8, "high": 106.0, "close": 105.6, "ema20": 100.0, "ema50": 98.0})
    fx_context["m15_prev"].update({"high": 101.0, "close": 100.5})

    _, crypto_components, _ = calculate_confidence(crypto_context, cfg)
    _, fx_components, _ = calculate_confidence(fx_context, cfg)

    assert crypto_components["setup_quality"] > fx_components["setup_quality"]


def test_metal_mean_reversion_bollinger_scores_higher_than_crypto_on_band_rejection() -> None:
    cfg = Config()
    metal_context = _build_context("BUY", symbol="XAUUSDm")
    crypto_context = _build_context("BUY", symbol="BTCUSDm")

    metal_context["m15"].update({"close": 95.0, "bb_lower": 94.0, "bb_middle": 100.0, "bb_upper": 110.0})
    crypto_context["m15"].update({"close": 95.0, "bb_lower": 94.0, "bb_middle": 100.0, "bb_upper": 110.0})

    _, metal_components, _ = calculate_confidence(metal_context, cfg)
    _, crypto_components, _ = calculate_confidence(crypto_context, cfg)

    assert metal_components["bollinger_context"] > crypto_components["bollinger_context"]
