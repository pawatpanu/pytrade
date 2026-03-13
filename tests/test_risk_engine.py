from core.risk_engine import build_trade_plan


def test_build_trade_plan_buy() -> None:
    plan = build_trade_plan(
        direction="BUY",
        entry_price=100.0,
        atr=2.0,
        account_balance=10000.0,
        risk_per_trade_pct=1.0,
        sl_atr_multiplier=1.5,
        target_rr=2.0,
    )

    assert plan.stop_loss == 97.0
    assert plan.take_profit == 106.0
    assert plan.risk_amount == 100.0
    assert plan.position_size > 0


def test_build_trade_plan_sell() -> None:
    plan = build_trade_plan(
        direction="SELL",
        entry_price=200.0,
        atr=4.0,
        account_balance=5000.0,
        risk_per_trade_pct=2.0,
        sl_atr_multiplier=1.0,
        target_rr=1.5,
    )

    assert plan.stop_loss == 204.0
    assert plan.take_profit == 194.0
    assert plan.risk_amount == 100.0
    assert plan.position_size == 25.0
