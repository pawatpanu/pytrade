from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _parse_float(value: str | None, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


def _parse_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [x.strip() for x in value.split(",") if x.strip()]


def _parse_weights(value: str | None) -> dict[str, int]:
    default = {
        "higher_tf": 20,
        "ema_alignment": 15,
        "adx_strength": 10,
        "market_structure": 10,
        "setup_quality": 10,
        "rsi_context": 8,
        "macd_confirmation": 8,
        "stoch_trigger": 5,
        "volume_confirmation": 5,
        "bollinger_context": 4,
        "atr_suitability": 5,
    }
    if not value:
        return default

    parsed = default.copy()
    for item in value.split(","):
        if ":" not in item:
            continue
        key, raw = item.split(":", 1)
        key = key.strip()
        if key in parsed:
            try:
                parsed[key] = int(raw.strip())
            except ValueError:
                continue
    return parsed


PROFILE_PRESETS: dict[str, dict[str, Any]] = {
    "aggressive": {
        "hard_filter_mode": "soft",
        "adx_minimum": 12.0,
        "entry_zone_max_atr": 3.5,
        "m5_min_triggers": 1,
        "watchlist_threshold": 35,
        "alert_threshold": 45,
        "strong_alert_threshold": 55,
        "premium_alert_threshold": 65,
    },
    "normal": {
        "hard_filter_mode": "soft",
        "adx_minimum": 14.0,
        "entry_zone_max_atr": 3.0,
        "m5_min_triggers": 2,
        "watchlist_threshold": 50,
        "alert_threshold": 60,
        "strong_alert_threshold": 70,
        "premium_alert_threshold": 80,
    },
    "strict": {
        "hard_filter_mode": "strict",
        "adx_minimum": 18.0,
        "entry_zone_max_atr": 1.8,
        "m5_min_triggers": 2,
        "watchlist_threshold": 75,
        "alert_threshold": 85,
        "strong_alert_threshold": 90,
        "premium_alert_threshold": 93,
    },
}


@dataclass(slots=True)
class Config:
    mt5_login: int | None = field(default_factory=lambda: _parse_int(os.getenv("MT5_LOGIN"), 0) or None)
    mt5_password: str | None = field(default_factory=lambda: os.getenv("MT5_PASSWORD") or None)
    mt5_server: str | None = field(default_factory=lambda: os.getenv("MT5_SERVER") or None)
    mt5_path: str | None = field(default_factory=lambda: os.getenv("MT5_PATH") or None)

    symbols: list[str] = field(
        default_factory=lambda: _parse_csv(
            os.getenv("SYMBOLS"), ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "BNBUSD", "DOGEUSD"]
        )
    )

    timeframe_primary: str = field(default_factory=lambda: os.getenv("TIMEFRAME_PRIMARY", "H4"))
    timeframe_confirm: str = field(default_factory=lambda: os.getenv("TIMEFRAME_CONFIRM", "H1"))
    timeframe_setup: str = field(default_factory=lambda: os.getenv("TIMEFRAME_SETUP", "M15"))
    timeframe_trigger: str = field(default_factory=lambda: os.getenv("TIMEFRAME_TRIGGER", "M5"))

    bars_to_fetch: int = field(default_factory=lambda: _parse_int(os.getenv("BARS_TO_FETCH"), 600))
    scan_interval_seconds: int = field(default_factory=lambda: _parse_int(os.getenv("SCAN_INTERVAL_SECONDS"), 60))
    sync_interval_seconds: int = field(default_factory=lambda: _parse_int(os.getenv("SYNC_INTERVAL_SECONDS"), 30))
    summary_interval_seconds: int = field(default_factory=lambda: _parse_int(os.getenv("SUMMARY_INTERVAL_SECONDS"), 300))
    signal_profile: str = field(default_factory=lambda: os.getenv("SIGNAL_PROFILE", "custom").strip().lower())

    watchlist_threshold: int = field(default_factory=lambda: _parse_int(os.getenv("WATCHLIST_THRESHOLD"), 75))
    alert_threshold: int = field(default_factory=lambda: _parse_int(os.getenv("ALERT_THRESHOLD"), 85))
    strong_alert_threshold: int = field(default_factory=lambda: _parse_int(os.getenv("STRONG_ALERT_THRESHOLD"), 90))
    premium_alert_threshold: int = field(default_factory=lambda: _parse_int(os.getenv("PREMIUM_ALERT_THRESHOLD"), 93))

    adx_minimum: float = field(default_factory=lambda: _parse_float(os.getenv("ADX_MINIMUM"), 18.0))
    entry_zone_max_atr: float = field(default_factory=lambda: _parse_float(os.getenv("ENTRY_ZONE_MAX_ATR"), 1.8))
    hard_filter_mode: str = field(default_factory=lambda: os.getenv("HARD_FILTER_MODE", "strict").lower())
    m5_min_triggers: int = field(default_factory=lambda: _parse_int(os.getenv("M5_MIN_TRIGGERS"), 2))
    anti_dup_score_delta: float = field(default_factory=lambda: _parse_float(os.getenv("ANTI_DUP_SCORE_DELTA"), 5.0))

    rsi_buy_low: float = field(default_factory=lambda: _parse_float(os.getenv("RSI_BUY_LOW"), 45.0))
    rsi_buy_high: float = field(default_factory=lambda: _parse_float(os.getenv("RSI_BUY_HIGH"), 60.0))
    rsi_sell_low: float = field(default_factory=lambda: _parse_float(os.getenv("RSI_SELL_LOW"), 40.0))
    rsi_sell_high: float = field(default_factory=lambda: _parse_float(os.getenv("RSI_SELL_HIGH"), 55.0))

    use_ema: bool = field(default_factory=lambda: _parse_bool(os.getenv("USE_EMA"), True))
    use_rsi: bool = field(default_factory=lambda: _parse_bool(os.getenv("USE_RSI"), True))
    use_macd: bool = field(default_factory=lambda: _parse_bool(os.getenv("USE_MACD"), True))
    use_bbands: bool = field(default_factory=lambda: _parse_bool(os.getenv("USE_BBANDS"), True))
    use_adx: bool = field(default_factory=lambda: _parse_bool(os.getenv("USE_ADX"), True))
    use_atr: bool = field(default_factory=lambda: _parse_bool(os.getenv("USE_ATR"), True))
    use_stoch: bool = field(default_factory=lambda: _parse_bool(os.getenv("USE_STOCH"), True))
    use_vwap: bool = field(default_factory=lambda: _parse_bool(os.getenv("USE_VWAP"), False))
    use_supertrend: bool = field(default_factory=lambda: _parse_bool(os.getenv("USE_SUPERTREND"), False))

    telegram_enabled: bool = field(default_factory=lambda: _parse_bool(os.getenv("TELEGRAM_ENABLED"), False))
    telegram_token: str | None = field(default_factory=lambda: os.getenv("TELEGRAM_TOKEN") or None)
    telegram_chat_id: str | None = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID") or None)

    line_enabled: bool = field(default_factory=lambda: _parse_bool(os.getenv("LINE_ENABLED"), False))
    line_token: str | None = field(default_factory=lambda: os.getenv("LINE_TOKEN") or None)

    dry_run: bool = field(default_factory=lambda: _parse_bool(os.getenv("DRY_RUN"), True))
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "signals.db"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    min_alert_category: str = field(default_factory=lambda: os.getenv("MIN_ALERT_CATEGORY", "alert").strip().lower())
    account_balance: float = field(default_factory=lambda: _parse_float(os.getenv("ACCOUNT_BALANCE"), 10000.0))
    risk_per_trade_pct: float = field(default_factory=lambda: _parse_float(os.getenv("RISK_PER_TRADE_PCT"), 1.0))
    sl_atr_multiplier: float = field(default_factory=lambda: _parse_float(os.getenv("SL_ATR_MULTIPLIER"), 1.5))
    target_rr: float = field(default_factory=lambda: _parse_float(os.getenv("TARGET_RR"), 1.8))

    backtest_bars: int = field(default_factory=lambda: _parse_int(os.getenv("BACKTEST_BARS"), 2500))
    backtest_forward_bars: int = field(default_factory=lambda: _parse_int(os.getenv("BACKTEST_FORWARD_BARS"), 12))
    enable_execution: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_EXECUTION"), False))
    execution_mode: str = field(default_factory=lambda: os.getenv("EXECUTION_MODE", "demo").strip().lower())
    min_execute_category: str = field(default_factory=lambda: os.getenv("MIN_EXECUTE_CATEGORY", "strong").strip().lower())
    max_open_positions: int = field(default_factory=lambda: _parse_int(os.getenv("MAX_OPEN_POSITIONS"), 2))
    enable_premium_stack: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_PREMIUM_STACK"), True))
    premium_stack_extra_slots: int = field(default_factory=lambda: _parse_int(os.getenv("PREMIUM_STACK_EXTRA_SLOTS"), 1))
    enable_ultra_stack: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_ULTRA_STACK"), True))
    ultra_stack_score: float = field(default_factory=lambda: _parse_float(os.getenv("ULTRA_STACK_SCORE"), 95.0))
    ultra_stack_extra_slots: int = field(default_factory=lambda: _parse_int(os.getenv("ULTRA_STACK_EXTRA_SLOTS"), 2))
    daily_loss_limit: float = field(default_factory=lambda: _parse_float(os.getenv("DAILY_LOSS_LIMIT"), 200.0))
    order_cooldown_minutes: int = field(default_factory=lambda: _parse_int(os.getenv("ORDER_COOLDOWN_MINUTES"), 30))
    max_slippage_points: int = field(default_factory=lambda: _parse_int(os.getenv("MAX_SLIPPAGE_POINTS"), 100))
    fixed_lot: float = field(default_factory=lambda: _parse_float(os.getenv("FIXED_LOT"), 0.01))
    magic_number: int = field(default_factory=lambda: _parse_int(os.getenv("MAGIC_NUMBER"), 20260312))
    enable_smart_exit: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_SMART_EXIT"), True))
    enable_break_even: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_BREAK_EVEN"), True))
    break_even_trigger_r: float = field(default_factory=lambda: _parse_float(os.getenv("BREAK_EVEN_TRIGGER_R"), 1.0))
    break_even_lock_r: float = field(default_factory=lambda: _parse_float(os.getenv("BREAK_EVEN_LOCK_R"), 0.1))
    enable_trailing_stop: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_TRAILING_STOP"), True))
    trailing_start_r: float = field(default_factory=lambda: _parse_float(os.getenv("TRAILING_START_R"), 1.5))
    trailing_distance_r: float = field(default_factory=lambda: _parse_float(os.getenv("TRAILING_DISTANCE_R"), 1.0))
    enable_partial_close: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_PARTIAL_CLOSE"), False))
    partial_close_trigger_r: float = field(default_factory=lambda: _parse_float(os.getenv("PARTIAL_CLOSE_TRIGGER_R"), 1.5))
    partial_close_ratio: float = field(default_factory=lambda: _parse_float(os.getenv("PARTIAL_CLOSE_RATIO"), 0.5))
    log_skipped_reasons: list[str] = field(
        default_factory=lambda: _parse_csv(
            os.getenv("LOG_SKIPPED_REASONS"),
            [
                "execution_disabled",
                "execution_mode_not_demo",
                "max_open_positions_reached",
                "daily_loss_limit_reached",
                "account_info_unavailable",
                "account_not_demo",
                "symbol_trade_disabled",
            ],
        )
    )

    weights: dict[str, int] = field(default_factory=lambda: _parse_weights(os.getenv("WEIGHTS")))

    def __post_init__(self) -> None:
        self._apply_signal_profile()
        self.hard_filter_mode = "soft" if self.hard_filter_mode == "soft" else "strict"
        self.m5_min_triggers = max(1, min(4, int(self.m5_min_triggers)))
        if self.min_alert_category not in {"alert", "strong", "premium"}:
            self.min_alert_category = "alert"
        if self.min_execute_category not in {"alert", "strong", "premium"}:
            self.min_execute_category = "strong"
        self.execution_mode = "demo" if self.execution_mode != "live" else "live"
        self.premium_stack_extra_slots = max(0, int(self.premium_stack_extra_slots))
        self.ultra_stack_extra_slots = max(0, int(self.ultra_stack_extra_slots))
        self.ultra_stack_score = max(0.0, float(self.ultra_stack_score))
        self.break_even_trigger_r = max(0.2, float(self.break_even_trigger_r))
        self.break_even_lock_r = max(0.0, float(self.break_even_lock_r))
        self.trailing_start_r = max(0.5, float(self.trailing_start_r))
        self.trailing_distance_r = max(0.2, float(self.trailing_distance_r))
        self.partial_close_trigger_r = max(0.5, float(self.partial_close_trigger_r))
        self.partial_close_ratio = min(0.9, max(0.1, float(self.partial_close_ratio)))

    def _apply_signal_profile(self) -> None:
        if self.signal_profile == "custom":
            return
        preset = PROFILE_PRESETS.get(self.signal_profile)
        if preset is None:
            self.signal_profile = "custom"
            return
        for key, value in preset.items():
            setattr(self, key, value)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


CONFIG = Config()
