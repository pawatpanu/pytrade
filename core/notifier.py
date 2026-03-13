from __future__ import annotations

import logging
from dataclasses import replace

import requests

from config import Config
from core.logger_db import SignalDB
from core.models import SignalResult, SymbolState

logger = logging.getLogger(__name__)

CATEGORY_RANK = {"ignore": 0, "candidate": 1, "alert": 2, "strong": 3, "premium": 4}
CATEGORY_EMOJI = {"alert": "🚨", "strong": "🔥", "premium": "💎"}
DIR_EMOJI = {"BUY": "🟢", "SELL": "🔴"}


class Notifier:
    """Send alerts to console / Telegram / LINE and enforce anti-duplicate rules."""

    def __init__(self, config: Config, db: SignalDB) -> None:
        self.config = config
        self.db = db

    def should_alert(self, signal: SignalResult) -> bool:
        """Return True if signal passes threshold and anti-duplicate policy."""
        if not signal.hard_filters_passed or signal.score < self.config.alert_threshold:
            return False
        if CATEGORY_RANK.get(signal.category, 0) < CATEGORY_RANK.get(self.config.min_alert_category, 2):
            return False

        state = self.db.get_symbol_state(signal.normalized_symbol, signal.direction)
        if state is None:
            return True

        same_candle = state.last_alert_candle_time == signal.timestamp
        score_improved = signal.score >= state.last_score + self.config.anti_dup_score_delta

        if same_candle:
            return False

        if state.invalidated or score_improved:
            return True

        return False

    def mark_invalidation(self, symbol: str, direction: str) -> None:
        """Set invalidation flag when setup quality drops below watchlist threshold."""
        state = self.db.get_symbol_state(symbol, direction)
        if state is None:
            state = SymbolState(symbol=symbol, direction=direction, invalidated=True)
        else:
            state = replace(state, invalidated=True)
        self.db.upsert_symbol_state(state)

    def send_alert(self, signal: SignalResult) -> None:
        """Dispatch alert channels and persist latest alert state."""
        text = self._format_message(signal)
        self._send_console(text)

        if not self.config.dry_run:
            if self.config.telegram_enabled:
                self._send_telegram(text)
            if self.config.line_enabled:
                self._send_line(text)

        self.db.upsert_symbol_state(
            SymbolState(
                symbol=signal.normalized_symbol,
                direction=signal.direction,
                last_alert_candle_time=signal.timestamp,
                last_score=signal.score,
                invalidated=False,
            )
        )

    def _format_message(self, signal: SignalResult) -> str:
        snap = signal.indicator_snapshot
        tf = signal.timeframe_summary
        mode = "[DRY-RUN] " if self.config.dry_run else ""
        sev = signal.category.upper()
        sev_icon = CATEGORY_EMOJI.get(signal.category, "⚠️")
        dir_icon = DIR_EMOJI.get(signal.direction, "•")
        top = sorted(signal.component_scores.items(), key=lambda kv: kv[1], reverse=True)[:3]
        top_text = ", ".join(f"{k}:{v:.1f}" for k, v in top) if top else "-"
        plan = signal.trade_plan or {}
        plan_text = (
            f"SL {plan.get('stop_loss', 0):.5f} | TP {plan.get('take_profit', 0):.5f} | "
            f"Size {plan.get('position_size', 0):.4f} | Risk ${plan.get('risk_amount', 0):.2f}"
        )
        return (
            f"{mode}{sev_icon} {sev} | {dir_icon} {signal.direction} {signal.symbol}\n"
            f"Score {signal.score:.2f} | Price {signal.price:.5f}\n"
            f"TF H4:{tf.get('H4')} H1:{tf.get('H1')} M15:{tf.get('M15')} M5:{tf.get('M5')}\n"
            f"RSI {snap.get('rsi14', 0):.2f} | MACD {snap.get('macd', 0):.4f}/{snap.get('macd_signal', 0):.4f} | ADX {snap.get('adx14', 0):.2f}\n"
            f"{plan_text}\n"
            f"Top factors: {top_text}\n"
            f"{signal.timestamp.isoformat()} | rule-based confidence (not win rate)"
        )

    @staticmethod
    def _send_console(text: str) -> None:
        logger.info("\n%s", text)

    def _send_telegram(self, text: str) -> None:
        if not self.config.telegram_token or not self.config.telegram_chat_id:
            logger.warning("Telegram enabled but token/chat_id missing")
            return
        url = f"https://api.telegram.org/bot{self.config.telegram_token}/sendMessage"
        payload = {"chat_id": self.config.telegram_chat_id, "text": text}
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code >= 300:
                logger.warning("Telegram send failed: %s", resp.text)
        except requests.RequestException as exc:
            logger.error("Telegram send exception: %s", exc)

    def _send_line(self, text: str) -> None:
        if not self.config.line_token:
            logger.warning("LINE enabled but token missing")
            return
        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {self.config.line_token}"}
        payload = {"message": text}
        try:
            resp = requests.post(url, headers=headers, data=payload, timeout=10)
            if resp.status_code >= 300:
                logger.warning("LINE send failed: %s", resp.text)
        except requests.RequestException as exc:
            logger.error("LINE send exception: %s", exc)


def should_alert(notifier: Notifier, signal: SignalResult) -> bool:
    """Convenience function for required API surface."""
    return notifier.should_alert(signal)


def send_alert(notifier: Notifier, signal: SignalResult) -> None:
    """Convenience function for required API surface."""
    notifier.send_alert(signal)
