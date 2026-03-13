from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import MetaTrader5 as mt5

TIMEFRAME_MAP: dict[str, int] = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}

TIMEFRAME_MINUTES: dict[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger for console output."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def now_utc() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def to_mt5_timeframe(timeframe: str) -> int:
    """Map human-readable timeframe to MT5 constant."""
    tf = timeframe.upper()
    if tf not in TIMEFRAME_MAP:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return TIMEFRAME_MAP[tf]


def timeframe_minutes(timeframe: str) -> int:
    """Return timeframe duration in minutes."""
    tf = timeframe.upper()
    if tf not in TIMEFRAME_MINUTES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return TIMEFRAME_MINUTES[tf]


def safe_json(value: Any) -> Any:
    """Convert values to JSON-safe forms for SQLite storage."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def classify_score(
    score: float,
    watchlist_threshold: int,
    alert_threshold: int,
    strong_alert_threshold: int,
    premium_alert_threshold: int,
) -> str:
    """Classify score range into candidate/alert tiers."""
    if score >= premium_alert_threshold:
        return "premium"
    if score >= strong_alert_threshold:
        return "strong"
    if score >= alert_threshold:
        return "alert"
    if score >= watchlist_threshold:
        return "candidate"
    return "ignore"
