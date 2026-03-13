from __future__ import annotations

from core.models import TradePlan


def build_trade_plan(
    direction: str,
    entry_price: float,
    atr: float,
    account_balance: float,
    risk_per_trade_pct: float,
    sl_atr_multiplier: float,
    target_rr: float,
) -> TradePlan:
    """Build an ATR-based plan for risk sizing (analysis-only, no order placement)."""
    atr = max(float(atr), 1e-8)
    risk_amount = max(account_balance * (risk_per_trade_pct / 100.0), 0.0)
    sl_distance = atr * max(sl_atr_multiplier, 0.1)
    rr = max(target_rr, 1.0)

    if direction == "BUY":
        stop_loss = entry_price - sl_distance
        take_profit = entry_price + (sl_distance * rr)
    else:
        stop_loss = entry_price + sl_distance
        take_profit = entry_price - (sl_distance * rr)

    # Generic unit sizing; exact contract size can be mapped later per symbol spec.
    position_size = risk_amount / sl_distance if sl_distance > 0 else 0.0

    return TradePlan(
        entry=round(entry_price, 8),
        stop_loss=round(stop_loss, 8),
        take_profit=round(take_profit, 8),
        risk_reward=round(rr, 2),
        risk_amount=round(risk_amount, 2),
        position_size=round(position_size, 6),
        atr=round(atr, 8),
    )
