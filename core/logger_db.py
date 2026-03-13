from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone

from core.models import SignalResult, SymbolState

logger = logging.getLogger(__name__)


class SignalDB:
    """SQLite persistence for scan logs, alerts, and symbol alert states."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    normalized_symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    score REAL NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL,
                    reason_summary TEXT,
                    timeframe_summary_json TEXT,
                    indicator_snapshot_json TEXT,
                    component_scores_json TEXT,
                    trade_plan_json TEXT,
                    hard_filters_passed INTEGER NOT NULL,
                    hard_filter_reasons_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS scan_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS symbol_states (
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    last_alert_candle_time TEXT,
                    last_score REAL NOT NULL DEFAULT 0,
                    invalidated INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (symbol, direction)
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    normalized_symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    category TEXT NOT NULL,
                    score REAL NOT NULL,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    volume REAL,
                    risk_amount REAL,
                    status TEXT NOT NULL,
                    reason TEXT,
                    mt5_order INTEGER,
                    mt5_position INTEGER,
                    comment TEXT,
                    partial_close_done INTEGER NOT NULL DEFAULT 0,
                    pnl REAL,
                    closed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS runtime_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS config_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    changes_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            self._ensure_column(conn, "signals", "trade_plan_json", "TEXT")
            self._ensure_column(conn, "orders", "partial_close_done", "INTEGER NOT NULL DEFAULT 0")

    @staticmethod
    def _ensure_column(conn: sqlite3.Connection, table: str, column: str, column_def: str) -> None:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {c[1] for c in cols}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")

    def save_signal_to_db(self, signal: SignalResult) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO signals (
                    timestamp, symbol, normalized_symbol, direction, score, category, price,
                    reason_summary, timeframe_summary_json, indicator_snapshot_json,
                    component_scores_json, trade_plan_json, hard_filters_passed, hard_filter_reasons_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.timestamp.isoformat(),
                    signal.symbol,
                    signal.normalized_symbol,
                    signal.direction,
                    signal.score,
                    signal.category,
                    signal.price,
                    signal.reason_summary,
                    json.dumps(signal.timeframe_summary),
                    json.dumps(signal.indicator_snapshot),
                    json.dumps(signal.component_scores),
                    json.dumps(signal.trade_plan),
                    int(signal.hard_filters_passed),
                    json.dumps(signal.hard_filter_reasons),
                ),
            )

    def log_scan_event(self, symbol: str, level: str, message: str, details: dict | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO scan_events (timestamp, symbol, level, message, details_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    symbol,
                    level,
                    message,
                    json.dumps(details or {}),
                ),
            )

    def get_symbol_state(self, symbol: str, direction: str) -> SymbolState | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT symbol, direction, last_alert_candle_time, last_score, invalidated
                FROM symbol_states WHERE symbol = ? AND direction = ?
                """,
                (symbol, direction),
            ).fetchone()

        if row is None:
            return None

        last_time = datetime.fromisoformat(row["last_alert_candle_time"]) if row["last_alert_candle_time"] else None
        return SymbolState(
            symbol=row["symbol"],
            direction=row["direction"],
            last_alert_candle_time=last_time,
            last_score=float(row["last_score"]),
            invalidated=bool(row["invalidated"]),
        )

    def upsert_symbol_state(self, state: SymbolState) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO symbol_states (symbol, direction, last_alert_candle_time, last_score, invalidated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(symbol, direction)
                DO UPDATE SET
                    last_alert_candle_time = excluded.last_alert_candle_time,
                    last_score = excluded.last_score,
                    invalidated = excluded.invalidated,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    state.symbol,
                    state.direction,
                    state.last_alert_candle_time.isoformat() if state.last_alert_candle_time else None,
                    state.last_score,
                    int(state.invalidated),
                ),
            )

    def log_order(
        self,
        *,
        timestamp: str,
        symbol: str,
        normalized_symbol: str,
        direction: str,
        category: str,
        score: float,
        entry_price: float | None,
        stop_loss: float | None,
        take_profit: float | None,
        volume: float | None,
        risk_amount: float | None,
        status: str,
        reason: str = "",
        mt5_order: int | None = None,
        mt5_position: int | None = None,
        comment: str = "",
        pnl: float | None = None,
        closed_at: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO orders (
                    timestamp, symbol, normalized_symbol, direction, category, score,
                    entry_price, stop_loss, take_profit, volume, risk_amount,
                    status, reason, mt5_order, mt5_position, comment, pnl, closed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    symbol,
                    normalized_symbol,
                    direction,
                    category,
                    score,
                    entry_price,
                    stop_loss,
                    take_profit,
                    volume,
                    risk_amount,
                    status,
                    reason,
                    mt5_order,
                    mt5_position,
                    comment,
                    pnl,
                    closed_at,
                ),
            )

    def count_open_orders(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM orders WHERE status = 'sent'").fetchone()
        return int(row["c"]) if row else 0

    def get_sent_orders(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    id,
                    timestamp,
                    symbol,
                    normalized_symbol,
                    direction,
                    entry_price,
                    stop_loss,
                    take_profit,
                    volume,
                    partial_close_done,
                    mt5_order,
                    mt5_position
                FROM orders
                WHERE status = 'sent'
                ORDER BY id ASC
                """
            ).fetchall()
        return list(rows)

    def update_order_close(self, order_id: int, pnl: float, closed_at: str, reason: str = "closed") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE orders
                SET status = 'closed', pnl = ?, closed_at = ?, reason = ?
                WHERE id = ?
                """,
                (pnl, closed_at, reason, order_id),
            )

    def mark_partial_close_done(self, order_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE orders
                SET partial_close_done = 1
                WHERE id = ?
                """,
                (order_id,),
            )

    def last_sent_order_time(self, normalized_symbol: str, direction: str) -> datetime | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT timestamp
                FROM orders
                WHERE normalized_symbol = ? AND direction = ? AND status = 'sent'
                ORDER BY id DESC
                LIMIT 1
                """,
                (normalized_symbol, direction),
            ).fetchone()
        if not row:
            return None
        return datetime.fromisoformat(row["timestamp"])

    def today_realized_loss(self) -> float:
        now_utc = datetime.now(timezone.utc)
        day_start = datetime.combine(now_utc.date(), datetime.min.time(), tzinfo=timezone.utc).isoformat()
        checkpoint = self.get_runtime_state("daily_loss_reset_at")
        cutoff = day_start
        if checkpoint:
            try:
                cp_dt = datetime.fromisoformat(checkpoint)
                if cp_dt.tzinfo is None:
                    cp_dt = cp_dt.replace(tzinfo=timezone.utc)
                if cp_dt.date() == now_utc.date() and cp_dt.isoformat() > cutoff:
                    cutoff = cp_dt.isoformat()
            except ValueError:
                pass

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(CASE WHEN pnl < 0 THEN pnl ELSE 0 END), 0) AS total
                FROM orders
                WHERE closed_at IS NOT NULL
                  AND substr(closed_at, 1, 10) = ?
                  AND closed_at >= ?
                """,
                (now_utc.date().isoformat(), cutoff),
            ).fetchone()
        return float(row["total"]) if row else 0.0

    def get_runtime_state(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT value
                FROM runtime_state
                WHERE key = ?
                LIMIT 1
                """,
                (key,),
            ).fetchone()
        return str(row["value"]) if row else None

    def set_runtime_state(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (key, value),
            )

    def reset_daily_loss_guard(self) -> str:
        reset_at = datetime.now(timezone.utc).isoformat()
        self.set_runtime_state("daily_loss_reset_at", reset_at)
        return reset_at

    def log_config_change(self, source: str, summary: str, changes: dict[str, str] | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO config_audit (timestamp, source, summary, changes_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    source,
                    summary,
                    json.dumps(changes or {}),
                ),
            )

    def get_recent_config_audit(self, limit: int = 50) -> list[sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, timestamp, source, summary, changes_json
                FROM config_audit
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return list(rows)


def save_signal_to_db(db: SignalDB, signal: SignalResult) -> None:
    """Convenience function for required API surface."""
    db.save_signal_to_db(signal)
