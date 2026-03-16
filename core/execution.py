from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5

from config import Config
from core.logger_db import SignalDB
from core.models import SignalResult
from core.notifier import CATEGORY_RANK

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Demo-first execution engine with safety guards and DB audit logs."""

    def __init__(self, config: Config, db: SignalDB) -> None:
        self.config = config
        self.db = db

    def try_execute_signal(self, signal: SignalResult) -> None:
        allowed, reason = self._precheck(signal)
        if not allowed:
            logger.info("Execution skipped %s %s: %s", signal.direction, signal.normalized_symbol, reason)
            if reason in set(self.config.log_skipped_reasons):
                self._log(signal, status="skipped", reason=reason)
            return

        symbol_info = mt5.symbol_info(signal.normalized_symbol)
        tick = mt5.symbol_info_tick(signal.normalized_symbol)
        if symbol_info is None or tick is None:
            logger.warning("Execution failed %s %s: symbol/tick unavailable", signal.direction, signal.normalized_symbol)
            self._log(signal, status="failed", reason="symbol_info_or_tick_unavailable")
            return
        if not self._is_symbol_trade_enabled(symbol_info):
            reason = "symbol_trade_disabled"
            logger.info("Execution skipped %s %s: %s", signal.direction, signal.normalized_symbol, reason)
            if reason in set(self.config.log_skipped_reasons):
                self._log(signal, status="skipped", reason=reason)
            return

        entry = float(tick.ask if signal.direction == "BUY" else tick.bid)
        plan = signal.trade_plan or {}
        sl = float(plan.get("stop_loss", 0.0))
        tp = float(plan.get("take_profit", 0.0))
        risk_amount = self._resolve_risk_amount(plan)
        if signal.trade_plan is None:
            signal.trade_plan = {}
        signal.trade_plan["risk_amount"] = risk_amount
        volume = self._calc_volume(symbol_info, entry, sl, risk_amount)
        if volume <= 0:
            logger.warning("Execution failed %s %s: invalid volume", signal.direction, signal.normalized_symbol)
            self._log(signal, status="failed", reason="invalid_volume")
            return

        order_type = mt5.ORDER_TYPE_BUY if signal.direction == "BUY" else mt5.ORDER_TYPE_SELL
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": signal.normalized_symbol,
            "volume": volume,
            "type": order_type,
            "price": entry,
            "sl": sl,
            "tp": tp,
            "deviation": int(self.config.max_slippage_points),
            "magic": int(self.config.magic_number),
            "comment": f"pytrade:{signal.category}:{signal.score:.1f}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result is None:
            code, msg = mt5.last_error()
            logger.warning("Execution failed %s %s: order_send none (%s %s)", signal.direction, signal.normalized_symbol, code, msg)
            self._log(signal, status="failed", reason=f"order_send_none:{code}:{msg}", entry=entry, sl=sl, tp=tp, volume=volume)
            return

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.warning(
                "Execution failed %s %s: retcode=%s",
                signal.direction,
                signal.normalized_symbol,
                result.retcode,
            )
            self._log(
                signal,
                status="failed",
                reason=f"retcode:{result.retcode}",
                entry=entry,
                sl=sl,
                tp=tp,
                volume=volume,
                mt5_order=int(getattr(result, "order", 0) or 0),
                mt5_position=int(getattr(result, "deal", 0) or 0),
                comment=getattr(result, "comment", ""),
            )
            return

        self._log(
            signal,
            status="sent",
            reason="",
            entry=entry,
            sl=sl,
            tp=tp,
            volume=volume,
            mt5_order=int(getattr(result, "order", 0) or 0),
            mt5_position=int(getattr(result, "deal", 0) or 0),
            comment=getattr(result, "comment", ""),
        )
        logger.info(
            "Order sent: %s %s vol=%.4f entry=%.5f sl=%.5f tp=%.5f retcode=%s",
            signal.direction,
            signal.normalized_symbol,
            volume,
            entry,
            sl,
            tp,
            result.retcode,
        )

    def _resolve_risk_amount(self, plan: dict[str, float]) -> float:
        """Resolve risk amount for sizing using live account data when enabled."""
        static_risk = float(plan.get("risk_amount", 0.0) or 0.0)
        if not self.config.use_mt5_balance_for_sizing:
            return max(static_risk, 0.0)

        account_info = mt5.account_info()
        if account_info is None:
            return max(static_risk, 0.0)

        if self.config.risk_balance_source == "balance":
            base = float(getattr(account_info, "balance", 0.0) or 0.0)
        else:
            base = float(getattr(account_info, "equity", 0.0) or 0.0)

        if base <= 0:
            return max(static_risk, 0.0)

        dynamic_risk = base * (float(self.config.risk_per_trade_pct) / 100.0)
        return round(max(dynamic_risk, 0.0), 2)

    def sync_orders(self) -> None:
        """Sync locally-sent orders with MT5 to update close status and realized PnL."""
        sent_orders = self.db.get_sent_orders()
        if not sent_orders:
            return

        now = datetime.now(timezone.utc)
        open_positions = mt5.positions_get() or []
        open_positions_by_symbol: dict[str, list[object]] = {}
        open_by_symbol: dict[str, set[int]] = {}
        for p in open_positions:
            if int(getattr(p, "magic", 0) or 0) != int(self.config.magic_number):
                continue
            sym = str(getattr(p, "symbol", ""))
            ticket = int(getattr(p, "ticket", 0) or 0)
            open_positions_by_symbol.setdefault(sym, []).append(p)
            if sym not in open_by_symbol:
                open_by_symbol[sym] = set()
            if ticket > 0:
                open_by_symbol[sym].add(ticket)

        for row in sent_orders:
            order_id = int(row["id"])
            symbol = str(row["normalized_symbol"])
            direction = str(row["direction"])
            entry_price = float(row["entry_price"] or 0.0)
            initial_stop_loss = float(row["stop_loss"] or 0.0)
            take_profit = float(row["take_profit"] or 0.0)
            initial_volume = float(row["volume"] or 0.0)
            partial_close_done = bool(int(row["partial_close_done"] or 0))
            opened_at = datetime.fromisoformat(str(row["timestamp"]))
            if opened_at.tzinfo is None:
                opened_at = opened_at.replace(tzinfo=timezone.utc)

            mt5_position = int(row["mt5_position"] or 0)
            mt5_order = int(row["mt5_order"] or 0)
            candidates = {x for x in (mt5_position, mt5_order) if x > 0}

            symbol_open = open_by_symbol.get(symbol, set())
            if candidates and (candidates & symbol_open):
                open_position = self._pick_open_position(symbol, direction, candidates, entry_price, open_positions_by_symbol)
                if open_position is not None:
                    self._manage_open_position(
                        order_id=order_id,
                        symbol=symbol,
                        direction=direction,
                        entry_price=entry_price,
                        initial_stop_loss=initial_stop_loss,
                        take_profit=take_profit,
                        initial_volume=initial_volume,
                        partial_close_done=partial_close_done,
                        position=open_position,
                    )
                continue

            start = opened_at - timedelta(days=2)
            deals = mt5.history_deals_get(start, now, group=symbol) or []
            in_deals = [d for d in deals if int(getattr(d, "magic", 0) or 0) == int(self.config.magic_number)]
            if not in_deals:
                continue

            # Match IN deal first to derive true position_id.
            position_ids: set[int] = set()
            for d in in_deals:
                if int(getattr(d, "entry", -1)) != int(mt5.DEAL_ENTRY_IN):
                    continue
                deal_ticket = int(getattr(d, "ticket", 0) or 0)
                deal_order = int(getattr(d, "order", 0) or 0)
                pos_id = int(getattr(d, "position_id", 0) or 0)
                if candidates and (deal_ticket in candidates or deal_order in candidates or pos_id in candidates):
                    if pos_id > 0:
                        position_ids.add(pos_id)

            # Fallback by nearest IN deal around open time with same direction.
            if not position_ids:
                dir_type = mt5.DEAL_TYPE_BUY if direction == "BUY" else mt5.DEAL_TYPE_SELL
                nearest = None
                nearest_score = float("inf")
                for d in in_deals:
                    if int(getattr(d, "entry", -1)) != int(mt5.DEAL_ENTRY_IN):
                        continue
                    if int(getattr(d, "type", -1)) != int(dir_type):
                        continue
                    d_time = datetime.fromtimestamp(int(getattr(d, "time", 0) or 0), tz=timezone.utc)
                    if d_time < opened_at - timedelta(minutes=3):
                        continue
                    d_price = float(getattr(d, "price", 0.0) or 0.0)
                    score = abs((d_time - opened_at).total_seconds()) + abs(d_price - entry_price) * 100000.0
                    if score < nearest_score:
                        nearest_score = score
                        nearest = d
                if nearest is not None:
                    pos_id = int(getattr(nearest, "position_id", 0) or 0)
                    if pos_id > 0:
                        position_ids.add(pos_id)

            if not position_ids:
                continue

            out_deals = []
            for d in deals:
                if int(getattr(d, "entry", -1)) != int(mt5.DEAL_ENTRY_OUT):
                    continue
                pos_id = int(getattr(d, "position_id", 0) or 0)
                if pos_id in position_ids:
                    out_deals.append(d)

            if not out_deals:
                continue

            pnl = 0.0
            latest_time = opened_at
            for d in out_deals:
                pnl += float(getattr(d, "profit", 0.0) or 0.0)
                pnl += float(getattr(d, "swap", 0.0) or 0.0)
                pnl += float(getattr(d, "commission", 0.0) or 0.0)
                t = datetime.fromtimestamp(int(getattr(d, "time", 0) or 0), tz=timezone.utc)
                if t > latest_time:
                    latest_time = t

            self.db.update_order_close(order_id=order_id, pnl=round(pnl, 2), closed_at=latest_time.isoformat())
            logger.info("Order closed sync: id=%s symbol=%s pnl=%.2f", order_id, symbol, pnl)

    def _pick_open_position(
        self,
        symbol: str,
        direction: str,
        candidates: set[int],
        entry_price: float,
        open_positions_by_symbol: dict[str, list[object]],
    ) -> object | None:
        positions = open_positions_by_symbol.get(symbol, [])
        if not positions:
            return None

        filtered = [p for p in positions if self._position_direction(p) == direction]
        if not filtered:
            filtered = positions

        if candidates:
            for p in filtered:
                if int(getattr(p, "ticket", 0) or 0) in candidates:
                    return p

        if entry_price > 0:
            return min(filtered, key=lambda p: abs(float(getattr(p, "price_open", entry_price) or entry_price) - entry_price))
        return filtered[0]

    @staticmethod
    def _position_direction(position: object) -> str:
        ptype = int(getattr(position, "type", -1))
        if ptype == int(mt5.POSITION_TYPE_BUY):
            return "BUY"
        if ptype == int(mt5.POSITION_TYPE_SELL):
            return "SELL"
        return ""

    def _manage_open_position(
        self,
        *,
        order_id: int,
        symbol: str,
        direction: str,
        entry_price: float,
        initial_stop_loss: float,
        take_profit: float,
        initial_volume: float,
        partial_close_done: bool,
        position: object,
    ) -> None:
        if not self.config.enable_smart_exit:
            return

        price_open = float(getattr(position, "price_open", 0.0) or 0.0)
        price_current = float(getattr(position, "price_current", 0.0) or 0.0)
        current_sl = float(getattr(position, "sl", 0.0) or 0.0)
        current_tp = float(getattr(position, "tp", 0.0) or 0.0)
        position_ticket = int(getattr(position, "ticket", 0) or 0)
        if position_ticket <= 0:
            return

        base_entry = entry_price if entry_price > 0 else price_open
        base_sl = initial_stop_loss if initial_stop_loss > 0 else current_sl
        if base_entry <= 0 or base_sl <= 0 or price_current <= 0:
            return

        risk = abs(base_entry - base_sl)
        if risk <= 0:
            return
        if direction == "BUY":
            profit = price_current - base_entry
        else:
            profit = base_entry - price_current
        if profit <= 0:
            return
        profit_r = profit / risk

        if (
            self.config.enable_partial_close
            and (not partial_close_done)
            and profit_r >= self.config.partial_close_trigger_r
        ):
            if self._try_partial_close(symbol, direction, position, initial_volume):
                self.db.mark_partial_close_done(order_id)
                logger.info(
                    "Partial close done: id=%s %s %s at %.2fR",
                    order_id,
                    direction,
                    symbol,
                    profit_r,
                )
                return

        proposed = self._proposed_stop_loss(
            direction=direction,
            entry_price=base_entry,
            initial_stop_loss=base_sl,
            current_price=price_current,
        )
        if proposed is None:
            return

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return

        adjusted_sl = self._adjust_stop_by_broker_rules(
            symbol_info=symbol_info,
            direction=direction,
            current_price=price_current,
            proposed_sl=proposed,
        )
        if adjusted_sl is None:
            return

        eps = max(float(getattr(symbol_info, "point", 0.00001) or 0.00001), 1e-8)
        if current_sl > 0:
            if direction == "BUY" and adjusted_sl <= current_sl + eps:
                return
            if direction == "SELL" and adjusted_sl >= current_sl - eps:
                return

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": symbol,
            "position": position_ticket,
            "sl": adjusted_sl,
            "tp": current_tp if current_tp > 0 else take_profit,
            "magic": int(self.config.magic_number),
        }
        result = mt5.order_send(request)
        if result is None:
            code, msg = mt5.last_error()
            logger.warning("SL update failed %s %s: order_send none (%s %s)", direction, symbol, code, msg)
            return
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.warning("SL update failed %s %s: retcode=%s", direction, symbol, result.retcode)
            return

        logger.info(
            "SL updated: id=%s %s %s old_sl=%.5f new_sl=%.5f current=%.5f",
            order_id,
            direction,
            symbol,
            current_sl,
            adjusted_sl,
            price_current,
        )

    def _try_partial_close(self, symbol: str, direction: str, position: object, initial_volume: float) -> bool:
        symbol_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if symbol_info is None or tick is None:
            return False

        position_ticket = int(getattr(position, "ticket", 0) or 0)
        position_volume = float(getattr(position, "volume", 0.0) or 0.0)
        if position_ticket <= 0 or position_volume <= 0:
            return False

        close_volume = self._calculate_partial_close_volume(
            symbol_info=symbol_info,
            position_volume=position_volume,
            initial_volume=initial_volume,
            ratio=self.config.partial_close_ratio,
        )
        if close_volume <= 0:
            return False

        close_type = mt5.ORDER_TYPE_SELL if direction == "BUY" else mt5.ORDER_TYPE_BUY
        close_price = float(tick.bid if direction == "BUY" else tick.ask)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "position": position_ticket,
            "volume": close_volume,
            "type": close_type,
            "price": close_price,
            "deviation": int(self.config.max_slippage_points),
            "magic": int(self.config.magic_number),
            "comment": "pytrade:partial_close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result is None:
            return False
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.warning("Partial close failed %s %s: retcode=%s", direction, symbol, result.retcode)
            return False
        return True

    @staticmethod
    def _calculate_partial_close_volume(
        *,
        symbol_info: object,
        position_volume: float,
        initial_volume: float,
        ratio: float,
    ) -> float:
        step = float(getattr(symbol_info, "volume_step", 0.01) or 0.01)
        min_lot = float(getattr(symbol_info, "volume_min", 0.01) or 0.01)

        base_volume = initial_volume if initial_volume > 0 else position_volume
        target = base_volume * ratio
        rounded = round(target / step) * step
        close_volume = min(position_volume, rounded)

        # Ensure some volume remains open after partial close.
        remaining = position_volume - close_volume
        if remaining <= 0 or remaining < min_lot:
            # Recalculate to leave at least min_lot open
            if position_volume > min_lot:
                close_volume = position_volume - min_lot
                close_volume = round(close_volume / step) * step
            else:
                # Can't safely partial close if position is too small
                return 0.0

        if close_volume < min_lot or close_volume <= 0:
            return 0.0
        if close_volume > position_volume:
            return 0.0
        return round(close_volume, 6)

    def _proposed_stop_loss(
        self,
        *,
        direction: str,
        entry_price: float,
        initial_stop_loss: float,
        current_price: float,
    ) -> float | None:
        risk = abs(entry_price - initial_stop_loss)
        if risk <= 0:
            return None

        if direction == "BUY":
            profit = current_price - entry_price
        else:
            profit = entry_price - current_price
        if profit <= 0:
            return None

        profit_r = profit / risk
        candidate: float | None = None

        if self.config.enable_break_even and profit_r >= self.config.break_even_trigger_r:
            lock = self.config.break_even_lock_r * risk
            be_sl = entry_price + lock if direction == "BUY" else entry_price - lock
            candidate = be_sl

        if self.config.enable_trailing_stop and profit_r >= self.config.trailing_start_r:
            trail_dist = self.config.trailing_distance_r * risk
            trail_sl = current_price - trail_dist if direction == "BUY" else current_price + trail_dist
            if candidate is None:
                candidate = trail_sl
            else:
                candidate = max(candidate, trail_sl) if direction == "BUY" else min(candidate, trail_sl)

        if candidate is None:
            return None

        if direction == "BUY":
            return max(candidate, initial_stop_loss)
        return min(candidate, initial_stop_loss)

    @staticmethod
    def _adjust_stop_by_broker_rules(
        *,
        symbol_info: object,
        direction: str,
        current_price: float,
        proposed_sl: float,
    ) -> float | None:
        point = float(getattr(symbol_info, "point", 0.0) or 0.0)
        digits = int(getattr(symbol_info, "digits", 5) or 5)
        stops_level = int(getattr(symbol_info, "trade_stops_level", 0) or 0)
        min_gap = max(stops_level * point, point * 2 if point > 0 else 0.0)

        if direction == "BUY":
            max_sl = current_price - min_gap
            if proposed_sl >= max_sl:
                proposed_sl = max_sl
            if proposed_sl <= 0 or proposed_sl >= current_price:
                return None
        else:
            min_sl = current_price + min_gap
            if proposed_sl <= min_sl:
                proposed_sl = min_sl
            if proposed_sl <= current_price:
                return None

        if point > 0:
            step = point
            proposed_sl = round(proposed_sl / step) * step
        return round(proposed_sl, digits)

    def _precheck(self, signal: SignalResult) -> tuple[bool, str]:
        if not self.config.enable_execution:
            return False, "execution_disabled"
        if self.config.execution_mode != "demo":
            return False, "execution_mode_not_demo"
        if CATEGORY_RANK.get(signal.category, 0) < CATEGORY_RANK.get(self.config.min_execute_category, 3):
            return False, "below_min_execute_category"
        if self.db.count_open_orders() >= self._max_open_positions_for_signal(signal):
            return False, "max_open_positions_reached"
        if abs(self.db.today_realized_loss()) >= self.config.daily_loss_limit:
            return False, "daily_loss_limit_reached"

        last_sent = self.db.last_sent_order_time(signal.normalized_symbol, signal.direction)
        if last_sent:
            now = datetime.now(timezone.utc)
            if last_sent.tzinfo is None:
                last_sent = last_sent.replace(tzinfo=timezone.utc)
            if now - last_sent < timedelta(minutes=self.config.order_cooldown_minutes):
                return False, "cooldown_active"

        account_info = mt5.account_info()
        if account_info is None:
            return False, "account_info_unavailable"

        # Demo-first safety gate.
        if account_info.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            return False, "account_not_demo"
        return True, ""

    def _max_open_positions_for_signal(self, signal: SignalResult) -> int:
        max_open = int(self.config.max_open_positions)
        if signal.category == "premium" and self.config.enable_premium_stack:
            max_open += int(self.config.premium_stack_extra_slots)
        # FIX: Check category instead of raw score for consistency
        if signal.category == "ultra" and self.config.enable_ultra_stack:
            max_open += int(self.config.ultra_stack_extra_slots)
        return max(1, max_open)

    def _calc_volume(self, symbol_info: object, entry: float, stop_loss: float, risk_amount: float) -> float:
        step = float(getattr(symbol_info, "volume_step", 0.01) or 0.01)
        min_lot = float(getattr(symbol_info, "volume_min", 0.01) or 0.01)
        max_lot = float(getattr(symbol_info, "volume_max", 100.0) or 100.0)
        contract_size = float(getattr(symbol_info, "trade_contract_size", 1.0) or 1.0)

        sl_distance = abs(entry - stop_loss)
        if sl_distance <= 0 or risk_amount <= 0:
            raw = self.config.fixed_lot
        else:
            loss_per_lot = sl_distance * contract_size
            raw = risk_amount / max(loss_per_lot, 1e-8)

        rounded = round(raw / step) * step
        volume = max(min_lot, min(max_lot, rounded))
        return round(volume, 6)

    @staticmethod
    def _is_symbol_trade_enabled(symbol_info: object) -> bool:
        trade_mode = int(getattr(symbol_info, "trade_mode", 0) or 0)
        return trade_mode != int(mt5.SYMBOL_TRADE_MODE_DISABLED)

    def _log(
        self,
        signal: SignalResult,
        *,
        status: str,
        reason: str,
        entry: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        volume: float | None = None,
        mt5_order: int | None = None,
        mt5_position: int | None = None,
        comment: str = "",
    ) -> None:
        plan = signal.trade_plan or {}
        self.db.log_order(
            timestamp=datetime.now(timezone.utc).isoformat(),
            symbol=signal.symbol,
            normalized_symbol=signal.normalized_symbol,
            direction=signal.direction,
            category=signal.category,
            score=signal.score,
            entry_price=entry if entry is not None else float(plan.get("entry", 0.0) or 0.0),
            stop_loss=sl if sl is not None else float(plan.get("stop_loss", 0.0) or 0.0),
            take_profit=tp if tp is not None else float(plan.get("take_profit", 0.0) or 0.0),
            volume=volume,
            risk_amount=float(plan.get("risk_amount", 0.0) or 0.0),
            status=status,
            reason=reason,
            mt5_order=mt5_order,
            mt5_position=mt5_position,
            comment=comment,
        )
