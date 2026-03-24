from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from core.signal_engine import _find_order_block_zone, _order_block_touch, _wick_rejection_trigger


def _m15_rows_for_buy_ob() -> pd.DataFrame:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    rows = []
    for i in range(8):
        t = now - timedelta(minutes=(8 - i) * 15)
        rows.append(
            {
                "time": t,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.2,
                "atr14": 1.0,
            }
        )

    # base bearish candle (candidate OB)
    rows[4].update({"open": 100.8, "high": 101.0, "low": 99.6, "close": 100.0, "atr14": 1.0})
    # impulse up confirms displacement
    rows[5].update({"open": 100.1, "high": 102.4, "low": 100.0, "close": 102.0, "atr14": 1.0})
    # signal candle (-2) touches OB zone and closes above zone low
    rows[6].update({"open": 101.5, "high": 101.7, "low": 100.7, "close": 101.2, "atr14": 1.0})

    return pd.DataFrame(rows)


def _m5_wick_rows() -> pd.DataFrame:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    prev = {
        "time": now - timedelta(minutes=10),
        "open": 100.0,
        "high": 100.4,
        "low": 99.8,
        "close": 100.1,
    }
    sig = {
        "time": now - timedelta(minutes=5),
        "open": 100.0,
        "high": 100.2,
        "low": 99.0,
        "close": 100.1,
    }
    tail = {
        "time": now,
        "open": 100.1,
        "high": 100.3,
        "low": 99.9,
        "close": 100.2,
    }
    return pd.DataFrame([prev, sig, tail])


def test_order_block_buy_touch_detected() -> None:
    m15 = _m15_rows_for_buy_ob()
    profile = {
        "order_block_lookback": 24,
        "order_block_impulse_atr": 0.8,
        "order_block_buffer_atr": 0.2,
    }

    zone = _find_order_block_zone("BUY", m15, profile)
    assert zone is not None
    assert _order_block_touch("BUY", m15, zone, profile) is True


def test_wick_entry_buy_detected() -> None:
    m5 = _m5_wick_rows()
    profile = {
        "wick_entry_min_ratio": 0.45,
        "wick_entry_body_max_ratio": 0.45,
    }
    assert _wick_rejection_trigger("BUY", m5, profile) is True


def test_wick_entry_sell_detected() -> None:
    m5 = _m5_wick_rows()
    # flip signal candle to upper-wick rejection
    m5.iloc[-2, m5.columns.get_loc("open")] = 100.8
    m5.iloc[-2, m5.columns.get_loc("high")] = 101.6
    m5.iloc[-2, m5.columns.get_loc("low")] = 100.1
    m5.iloc[-2, m5.columns.get_loc("close")] = 100.4

    profile = {
        "wick_entry_min_ratio": 0.45,
        "wick_entry_body_max_ratio": 0.45,
    }
    assert _wick_rejection_trigger("SELL", m5, profile) is True

