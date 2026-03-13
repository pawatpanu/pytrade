from datetime import datetime, timezone

from core.logger_db import SignalDB


def test_order_lifecycle_db(tmp_path) -> None:
    db = SignalDB(str(tmp_path / "t.db"))
    ts = datetime.now(timezone.utc).isoformat()

    db.log_order(
        timestamp=ts,
        symbol="BTCUSD",
        normalized_symbol="BTCUSDm",
        direction="BUY",
        category="strong",
        score=60.0,
        entry_price=100.0,
        stop_loss=99.0,
        take_profit=102.0,
        volume=0.1,
        risk_amount=10.0,
        status="sent",
        mt5_order=123,
        mt5_position=123,
    )

    assert db.count_open_orders() == 1
    sent = db.get_sent_orders()
    assert sent

    db.update_order_close(order_id=int(sent[0]["id"]), pnl=-5.0, closed_at=ts)
    assert db.count_open_orders() == 0
    assert db.today_realized_loss() <= -5.0


def test_daily_loss_guard_reset_checkpoint(tmp_path) -> None:
    db = SignalDB(str(tmp_path / "t2.db"))
    ts = datetime.now(timezone.utc).isoformat()

    db.log_order(
        timestamp=ts,
        symbol="ETHUSD",
        normalized_symbol="ETHUSDm",
        direction="BUY",
        category="alert",
        score=50.0,
        entry_price=100.0,
        stop_loss=99.0,
        take_profit=102.0,
        volume=0.1,
        risk_amount=10.0,
        status="closed",
        mt5_order=999,
        mt5_position=999,
        pnl=-7.0,
        closed_at=ts,
    )
    assert db.today_realized_loss() <= -7.0

    reset_at = db.reset_daily_loss_guard()
    assert isinstance(reset_at, str) and reset_at
    assert db.today_realized_loss() == 0.0
