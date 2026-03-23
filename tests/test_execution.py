from types import SimpleNamespace

from config import Config
from core.execution import ExecutionEngine
from core.logger_db import SignalDB


def test_calc_volume_positive(tmp_path) -> None:
    cfg = Config(db_path=str(tmp_path / "t.db"), signal_profile="custom")
    db = SignalDB(cfg.db_path)
    engine = ExecutionEngine(cfg, db)

    symbol_info = SimpleNamespace(volume_step=0.01, volume_min=0.01, volume_max=10.0, trade_contract_size=1.0)
    volume = engine._calc_volume(symbol_info, entry=100.0, stop_loss=99.0, risk_amount=100.0)

    assert volume > 0
    assert 0.01 <= volume <= 10.0


def test_proposed_stop_loss_break_even_buy(tmp_path) -> None:
    cfg = Config(
        db_path=str(tmp_path / "t.db"),
        signal_profile="custom",
        break_even_trigger_r=1.0,
        break_even_lock_r=0.2,
        trailing_start_r=99.0,
        enable_trailing_stop=False,
    )
    db = SignalDB(cfg.db_path)
    engine = ExecutionEngine(cfg, db)

    # risk = 10, profit = 12 => 1.2R, should move SL to entry + 0.2R = 102
    new_sl = engine._proposed_stop_loss(
        direction="BUY",
        entry_price=100.0,
        initial_stop_loss=90.0,
        current_price=112.0,
    )
    assert new_sl == 102.0


def test_proposed_stop_loss_trailing_buy(tmp_path) -> None:
    cfg = Config(
        db_path=str(tmp_path / "t.db"),
        signal_profile="custom",
        break_even_trigger_r=1.0,
        break_even_lock_r=0.1,
        trailing_start_r=1.5,
        trailing_distance_r=1.0,
        enable_trailing_stop=True,
    )
    db = SignalDB(cfg.db_path)
    engine = ExecutionEngine(cfg, db)

    # risk = 10, profit = 25 => 2.5R
    # BE = 101, trailing = 115, choose tighter (higher for BUY) => 115
    new_sl = engine._proposed_stop_loss(
        direction="BUY",
        entry_price=100.0,
        initial_stop_loss=90.0,
        current_price=125.0,
    )
    assert new_sl == 115.0


def test_calculate_partial_close_volume_keeps_min_lot() -> None:
    symbol_info = SimpleNamespace(volume_step=0.01, volume_min=0.01)
    close_volume = ExecutionEngine._calculate_partial_close_volume(
        symbol_info=symbol_info,
        position_volume=0.02,
        initial_volume=0.02,
        ratio=0.9,
    )
    # Must leave at least 0.01 open, so close only 0.01
    assert close_volume == 0.01


def test_is_symbol_trade_enabled() -> None:
    disabled = SimpleNamespace(trade_mode=0)
    enabled = SimpleNamespace(trade_mode=4)
    assert ExecutionEngine._is_symbol_trade_enabled(disabled) is False
    assert ExecutionEngine._is_symbol_trade_enabled(enabled) is True


def test_max_open_positions_for_premium_and_ultra(tmp_path) -> None:
    cfg = Config(
        db_path=str(tmp_path / "t.db"),
        signal_profile="custom",
        max_open_positions=1,
        enable_premium_stack=True,
        premium_stack_extra_slots=1,
        enable_ultra_stack=True,
        ultra_stack_score=93.0,
        ultra_stack_extra_slots=2,
    )
    db = SignalDB(cfg.db_path)
    engine = ExecutionEngine(cfg, db)

    premium_signal = SimpleNamespace(category="premium", score=90.0)
    ultra_signal = SimpleNamespace(category="premium", score=95.0)

    assert engine._max_open_positions_for_signal(premium_signal) == 2
    assert engine._max_open_positions_for_signal(ultra_signal) == 4


def test_resolve_risk_amount_uses_mt5_equity(tmp_path, monkeypatch) -> None:
    cfg = Config(
        db_path=str(tmp_path / "t.db"),
        signal_profile="custom",
        risk_per_trade_pct=1.0,
        use_mt5_balance_for_sizing=True,
        risk_balance_source="equity",
    )
    db = SignalDB(cfg.db_path)
    engine = ExecutionEngine(cfg, db)

    monkeypatch.setattr("core.execution.mt5.account_info", lambda: SimpleNamespace(equity=5000.0, balance=4000.0))
    risk_amount = engine._resolve_risk_amount({"risk_amount": 25.0})
    assert risk_amount == 50.0


def test_resolve_risk_amount_fallback_to_plan_when_mt5_unavailable(tmp_path, monkeypatch) -> None:
    cfg = Config(
        db_path=str(tmp_path / "t.db"),
        signal_profile="custom",
        risk_per_trade_pct=1.0,
        use_mt5_balance_for_sizing=True,
    )
    db = SignalDB(cfg.db_path)
    engine = ExecutionEngine(cfg, db)

    monkeypatch.setattr("core.execution.mt5.account_info", lambda: None)
    risk_amount = engine._resolve_risk_amount({"risk_amount": 25.0})
    assert risk_amount == 25.0

def test_is_btc_symbol_variants() -> None:
    assert ExecutionEngine._is_btc_symbol("BTCUSD") is True
    assert ExecutionEngine._is_btc_symbol("BTCUSDm") is True
    assert ExecutionEngine._is_btc_symbol("BTCUSD.a") is True
    assert ExecutionEngine._is_btc_symbol("ETHUSD") is False


def test_btc_pullback_ready_requires_retrace_buy(tmp_path) -> None:
    cfg = Config(
        db_path=str(tmp_path / "t.db"),
        signal_profile="custom",
        btc_pullback_entry_enabled=True,
        btc_pullback_min_retrace_r=0.2,
    )
    db = SignalDB(cfg.db_path)
    engine = ExecutionEngine(cfg, db)

    signal = SimpleNamespace(
        symbol="BTCUSD",
        normalized_symbol="BTCUSDm",
        direction="BUY",
        price=100.0,
        trade_plan={"entry": 100.0, "stop_loss": 90.0},
    )

    allowed, reason = engine._btc_pullback_ready(signal, current_price=99.0)
    assert allowed is False
    assert reason == "btc_wait_pullback"

    allowed, reason = engine._btc_pullback_ready(signal, current_price=98.0)
    assert allowed is True
    assert reason == ""
