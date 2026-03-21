from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from config import Config
from core.signal_engine import evaluate_buy_signal, evaluate_sell_signal


def _df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _base_row(ts: datetime) -> dict:
    return {
        "time": ts,
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.0,
        "ema20": 100.0,
        "ema50": 100.0,
        "ema200": 100.0,
        "rsi14": 50.0,
        "macd": 0.0,
        "macd_signal": 0.0,
        "macd_hist": 0.0,
        "bb_upper": 104.0,
        "bb_middle": 100.0,
        "bb_lower": 96.0,
        "adx14": 20.0,
        "plus_di14": 18.0,
        "minus_di14": 18.0,
        "atr14": 1.2,
        "stoch_k": 50.0,
        "stoch_d": 50.0,
        "volume": 120.0,
        "volume_sma20": 100.0,
    }


def _build_mtf_data() -> dict[str, pd.DataFrame]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    t0 = now - timedelta(minutes=15)
    t1 = now - timedelta(minutes=10)
    t2 = now - timedelta(minutes=5)

    # H4 sideway (no clear EMA alignment)
    h4 = _df([
        _base_row(t0),
        _base_row(t1),
        _base_row(t2),
    ])

    # H1 bearish alignment
    h1_rows = []
    for t in (t0, t1, t2):
        r = _base_row(t)
        r.update({"ema20": 98.0, "ema50": 100.0, "ema200": 102.0, "adx14": 21.0, "plus_di14": 15.0, "minus_di14": 22.0})
        h1_rows.append(r)
    h1 = _df(h1_rows)

    # M15 bearish alignment + reversal confluence for BUY on latest closed candle (-2)
    m15_prev = _base_row(t0)
    m15_prev.update({
        "open": 98.5,
        "high": 99.5,
        "low": 96.6,
        "close": 97.1,
        "ema20": 100.0,
        "ema50": 101.0,
        "ema200": 102.0,
        "rsi14": 43.0,
        "macd": -0.5,
        "macd_signal": -0.3,
        "macd_hist": -0.4,
        "bb_upper": 104.0,
        "bb_middle": 100.0,
        "bb_lower": 96.0,
        "adx14": 22.0,
        "plus_di14": 14.0,
        "minus_di14": 18.0,
        "atr14": 1.2,
    })
    m15_sig = _base_row(t1)
    m15_sig.update({
        "open": 97.0,
        "high": 98.4,
        "low": 96.7,
        "close": 97.0,
        "ema20": 100.0,
        "ema50": 101.0,
        "ema200": 102.0,
        "rsi14": 44.0,
        "macd": -0.4,
        "macd_signal": -0.3,
        "macd_hist": -0.2,
        "bb_upper": 104.0,
        "bb_middle": 100.0,
        "bb_lower": 96.0,
        "adx14": 22.0,
        "plus_di14": 15.0,
        "minus_di14": 17.0,
        "atr14": 1.2,
        # entry distance = |97 - 100| / 1.2 = 2.5 ATR
    })
    m15_tail = _base_row(t2)
    m15 = _df([m15_prev, m15_sig, m15_tail])

    # M5 bearish alignment but stochastic turning up to support reversal
    m5_prev = _base_row(t0)
    m5_prev.update({
        "open": 97.6,
        "high": 98.0,
        "low": 96.8,
        "close": 97.1,
        "ema20": 99.0,
        "ema50": 100.0,
        "ema200": 101.0,
        "stoch_k": 20.0,
        "stoch_d": 24.0,
        "macd": -0.3,
        "macd_signal": -0.2,
        "macd_hist": -0.3,
        "plus_di14": 15.0,
        "minus_di14": 18.0,
    })
    m5_sig = _base_row(t1)
    m5_sig.update({
        "open": 97.1,
        "high": 97.8,
        "low": 96.9,
        "close": 97.0,
        "ema20": 99.0,
        "ema50": 100.0,
        "ema200": 101.0,
        "stoch_k": 25.0,
        "stoch_d": 24.0,
        "macd": -0.2,
        "macd_signal": -0.2,
        "macd_hist": -0.2,
        "plus_di14": 16.0,
        "minus_di14": 17.0,
        "volume": 120.0,
        "volume_sma20": 100.0,
    })
    m5_tail = _base_row(t2)
    m5 = _df([m5_prev, m5_sig, m5_tail])

    return {
        "H4": h4,
        "H1": h1,
        "M15": m15,
        "M5": m5,
    }


def test_metal_adaptive_filter_allows_buy_in_h4_sideway_reversal() -> None:
    cfg = Config(signal_profile="custom", hard_filter_mode="strict")
    mtf = _build_mtf_data()
    sig = evaluate_buy_signal("XAUUSD", "XAUUSDm", mtf, cfg)

    assert sig.hard_filters_passed is True
    assert sig.score > 0


def test_non_metal_strict_still_blocks_same_sideway_setup() -> None:
    cfg = Config(signal_profile="custom", hard_filter_mode="strict")
    mtf = _build_mtf_data()
    sig = evaluate_buy_signal("EURUSD", "EURUSDm", mtf, cfg)

    assert sig.hard_filters_passed is False
    assert sig.score >= 0


def test_metal_sideway_with_bearish_lower_tf_can_generate_sell_signal() -> None:
    cfg = Config(signal_profile="custom", hard_filter_mode="strict")
    mtf = _build_mtf_data()
    sig = evaluate_sell_signal("XAUUSD", "XAUUSDm", mtf, cfg)

    assert sig.hard_filters_passed is True
    assert sig.score > 0


def test_news_block_context_rejects_signal() -> None:
    cfg = Config(signal_profile="custom", hard_filter_mode="strict", enable_news_filter=True)
    mtf = _build_mtf_data()
    news_ctx = {"blocked": True, "reason": "fed_event_window"}
    sig = evaluate_buy_signal("XAUUSD", "XAUUSDm", mtf, cfg, market_context=news_ctx)

    assert sig.hard_filters_passed is False
    assert any("News risk block" in r for r in sig.hard_filter_reasons)


def test_volume_regime_filter_rejects_weak_volume() -> None:
    cfg = Config(
        signal_profile="custom",
        hard_filter_mode="strict",
        enable_volume_regime_filter=True,
        volume_ratio_m5_min=2.0,
        volume_ratio_m15_min=2.0,
        volume_ratio_h1_min=2.0,
        volume_min_confirmations=2,
    )
    mtf = _build_mtf_data()
    sig = evaluate_buy_signal("XAUUSD", "XAUUSDm", mtf, cfg)

    assert sig.hard_filters_passed is False
    assert any("Volume regime weak" in r for r in sig.hard_filter_reasons)
