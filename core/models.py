from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class IndicatorSnapshot:
    ema20: float
    ema50: float
    ema200: float
    rsi: float
    macd: float
    macd_signal: float
    macd_hist: float
    adx: float
    atr: float
    stoch_k: float
    stoch_d: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    volume: float
    volume_sma20: float


@dataclass(slots=True)
class SignalResult:
    symbol: str
    normalized_symbol: str
    direction: str
    score: float
    category: str
    price: float
    timestamp: datetime
    timeframe_summary: dict[str, str]
    reason_summary: str
    indicator_snapshot: dict[str, float]
    hard_filters_passed: bool
    hard_filter_reasons: list[str] = field(default_factory=list)
    component_scores: dict[str, float] = field(default_factory=dict)
    trade_plan: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class TradePlan:
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    risk_amount: float
    position_size: float
    atr: float


@dataclass(slots=True)
class SymbolState:
    symbol: str
    direction: str
    last_alert_candle_time: datetime | None = None
    last_score: float = 0.0
    invalidated: bool = True


@dataclass(slots=True)
class ScanContext:
    symbol: str
    normalized_symbol: str
    mtf_data: dict[str, Any]
    scan_time: datetime
