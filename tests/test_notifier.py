from __future__ import annotations

from datetime import datetime, timezone

from config import Config
from core.logger_db import SignalDB
from core.models import SignalResult
from core.notifier import Notifier


def _signal(ts: datetime, score: float) -> SignalResult:
    return SignalResult(
        symbol="BTCUSD",
        normalized_symbol="BTCUSDm",
        direction="BUY",
        score=score,
        category="alert",
        price=100000.0,
        timestamp=ts,
        timeframe_summary={"H4": "bullish", "H1": "bullish", "M15": "bullish", "M5": "bullish"},
        reason_summary="test",
        indicator_snapshot={"rsi14": 52.0, "macd": 1.0, "macd_signal": 0.8, "adx14": 24.0},
        hard_filters_passed=True,
    )


def test_should_alert_anti_duplicate(tmp_path) -> None:
    cfg = Config(db_path=str(tmp_path / "t.db"), dry_run=True, min_alert_category="alert", signal_profile="custom")
    db = SignalDB(cfg.db_path)
    notifier = Notifier(cfg, db)

    t1 = datetime.now(timezone.utc)
    s1 = _signal(t1, 86)
    assert notifier.should_alert(s1)
    notifier.send_alert(s1)

    s_same_candle = _signal(t1, 90)
    assert not notifier.should_alert(s_same_candle)

    s_improved = _signal(datetime.now(timezone.utc), 92)
    assert notifier.should_alert(s_improved)
