from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timezone
from statistics import mean

import pandas as pd

from config import CONFIG
from core.data_fetcher import DataFetcher
from core.execution import ExecutionEngine
from core.indicators import calculate_indicators
from core.logger_db import SignalDB, save_signal_to_db
from core.mt5_connector import connect_mt5, get_available_symbols
from core.notifier import Notifier, send_alert, should_alert
from core.signal_engine import evaluate_buy_signal, evaluate_sell_signal
from core.symbol_manager import SymbolManager
from core.utils import setup_logging, timeframe_minutes

logger = logging.getLogger(__name__)


def _prepare_mtf_data(fetcher: DataFetcher, symbol: str, cfg=CONFIG) -> dict[str, pd.DataFrame]:
    tf_list = [cfg.timeframe_primary, cfg.timeframe_confirm, cfg.timeframe_setup, cfg.timeframe_trigger]
    data: dict[str, pd.DataFrame] = {}
    for tf in tf_list:
        raw = fetcher.fetch_ohlcv(symbol, tf, cfg.bars_to_fetch)
        if raw.empty:
            return {}
        calc = calculate_indicators(raw, use_vwap=cfg.use_vwap, use_supertrend=cfg.use_supertrend)
        if len(calc) < 220:
            return {}
        # Skip stale feeds (e.g., symbol exists but no fresh quotes).
        latest_closed = pd.Timestamp(calc.iloc[-2]["time"]).to_pydatetime()
        if latest_closed.tzinfo is None:
            latest_closed = latest_closed.replace(tzinfo=timezone.utc)
        age_minutes = (datetime.now(timezone.utc) - latest_closed).total_seconds() / 60.0
        max_age = timeframe_minutes(tf) * 3
        if age_minutes > max_age:
            logger.warning(
                "Stale data for %s %s: age=%.1f min > %s min",
                symbol,
                tf,
                age_minutes,
                max_age,
            )
            return {}
        data[tf] = calc
    return data


def _evaluate_symbol(
    symbol: str,
    normalized_symbol: str,
    fetcher: DataFetcher,
    db: SignalDB,
    notifier: Notifier,
    executor: ExecutionEngine,
) -> None:
    cfg = CONFIG
    mtf_data = _prepare_mtf_data(fetcher, normalized_symbol, cfg)
    if not mtf_data:
        db.log_scan_event(
            symbol,
            "WARNING",
            "insufficient_or_stale_data",
            {"normalized_symbol": normalized_symbol},
        )
        return

    buy = evaluate_buy_signal(symbol, normalized_symbol, mtf_data, cfg)
    sell = evaluate_sell_signal(symbol, normalized_symbol, mtf_data, cfg)

    save_signal_to_db(db, buy)
    save_signal_to_db(db, sell)

    if not buy.hard_filters_passed:
        db.log_scan_event(
            symbol,
            "INFO",
            "buy_hard_filter_fail",
            {"normalized_symbol": normalized_symbol, "reasons": buy.hard_filter_reasons},
        )
    if not sell.hard_filters_passed:
        db.log_scan_event(
            symbol,
            "INFO",
            "sell_hard_filter_fail",
            {"normalized_symbol": normalized_symbol, "reasons": sell.hard_filter_reasons},
        )

    if buy.score < cfg.watchlist_threshold or not buy.hard_filters_passed:
        notifier.mark_invalidation(normalized_symbol, "BUY")
    if sell.score < cfg.watchlist_threshold or not sell.hard_filters_passed:
        notifier.mark_invalidation(normalized_symbol, "SELL")

    best = buy if buy.score >= sell.score else sell
    db.log_scan_event(
        symbol,
        "INFO",
        "scan_complete",
        {
            "normalized_symbol": normalized_symbol,
            "buy_score": buy.score,
            "sell_score": sell.score,
            "best_direction": best.direction,
            "best_category": best.category,
        },
    )

    if should_alert(notifier, best):
        send_alert(notifier, best)

    # Execution guard is handled inside ExecutionEngine (category, cooldown, limits, demo-only).
    # Keep it independent from alert de-dup so execution can still be audited each scan.
    executor.try_execute_signal(best)


def _scan_cycle(connector: object, fetcher: DataFetcher, db: SignalDB, notifier: Notifier, executor: ExecutionEngine) -> None:
    available_symbols = get_available_symbols(connector)
    mapping = SymbolManager(CONFIG.symbols, available_symbols).resolve()
    if not mapping:
        logger.warning("No valid symbols resolved. Check broker symbol names.")
        return

    for symbol, normalized in mapping.items():
        try:
            _evaluate_symbol(symbol, normalized, fetcher, db, notifier, executor)
        except Exception as exc:
            logger.exception("Scan failed for %s (%s): %s", symbol, normalized, exc)
            db.log_scan_event(symbol, "ERROR", "scan_exception", {"error": str(exc)})


def run_scanner(once: bool = False) -> None:
    """Run live scanner loop (analysis + alert only, no auto-trade)."""
    setup_logging(CONFIG.log_level)
    logger.info(
        "Scanner config: profile=%s mode=%s adx_min=%.2f entry_zone_max_atr=%.2f m5_min_triggers=%s min_alert_category=%s thresholds=[%s,%s,%s,%s] risk=[bal=%.2f pct=%.2f sl_atr=%.2f rr=%.2f] exec=[enabled=%s mode=%s min_cat=%s max_open=%s day_loss=%.2f cooldown=%s]",
        CONFIG.signal_profile,
        CONFIG.hard_filter_mode,
        CONFIG.adx_minimum,
        CONFIG.entry_zone_max_atr,
        CONFIG.m5_min_triggers,
        CONFIG.min_alert_category,
        CONFIG.watchlist_threshold,
        CONFIG.alert_threshold,
        CONFIG.strong_alert_threshold,
        CONFIG.premium_alert_threshold,
        CONFIG.account_balance,
        CONFIG.risk_per_trade_pct,
        CONFIG.sl_atr_multiplier,
        CONFIG.target_rr,
        CONFIG.enable_execution,
        CONFIG.execution_mode,
        CONFIG.min_execute_category,
        CONFIG.max_open_positions,
        CONFIG.daily_loss_limit,
        CONFIG.order_cooldown_minutes,
    )
    db = SignalDB(CONFIG.db_path)
    connector = connect_mt5(CONFIG)
    fetcher = DataFetcher(connector)
    notifier = Notifier(CONFIG, db)
    executor = ExecutionEngine(CONFIG, db)

    try:
        while True:
            executor.sync_orders()
            _scan_cycle(connector, fetcher, db, notifier, executor)

            if once:
                break
            time.sleep(CONFIG.scan_interval_seconds)
    finally:
        connector.disconnect()


def run_backtest() -> None:
    """Basic backtest mode using the same live signal logic."""
    setup_logging(CONFIG.log_level)
    connector = connect_mt5(CONFIG)
    fetcher = DataFetcher(connector)

    results: list[float] = []
    total_signals = 0
    threshold_counts = {
        CONFIG.watchlist_threshold: 0,
        CONFIG.alert_threshold: 0,
        CONFIG.strong_alert_threshold: 0,
        CONFIG.premium_alert_threshold: 0,
    }

    try:
        mapping = SymbolManager(CONFIG.symbols, get_available_symbols(connector)).resolve()
        for symbol, normalized in mapping.items():
            tf_data: dict[str, pd.DataFrame] = {}
            for tf in [CONFIG.timeframe_primary, CONFIG.timeframe_confirm, CONFIG.timeframe_setup, CONFIG.timeframe_trigger]:
                raw = fetcher.fetch_ohlcv(normalized, tf, CONFIG.backtest_bars)
                calc = calculate_indicators(raw, use_vwap=CONFIG.use_vwap, use_supertrend=CONFIG.use_supertrend)
                if len(calc) < 240:
                    tf_data = {}
                    break
                tf_data[tf] = calc
            if not tf_data:
                logger.warning("Backtest skipped %s due to insufficient data", symbol)
                continue

            m5 = tf_data[CONFIG.timeframe_trigger]
            time_to_idx = {pd.Timestamp(t): i for i, t in enumerate(m5["time"]) }

            # Backtest should evaluate on a closed candle using the same -2 convention as live mode.
            # So we cut data at the NEXT candle timestamp, making the intended signal candle appear at index -2.
            for i in range(220, len(m5) - CONFIG.backtest_forward_bars - 2):
                ts = pd.Timestamp(m5.iloc[i + 1]["time"])

                sliced: dict[str, pd.DataFrame] = {}
                valid = True
                for tf, df in tf_data.items():
                    part = df[df["time"] <= ts]
                    if len(part) < 220:
                        valid = False
                        break
                    sliced[tf] = part
                if not valid:
                    continue

                buy = evaluate_buy_signal(symbol, normalized, sliced, CONFIG)
                sell = evaluate_sell_signal(symbol, normalized, sliced, CONFIG)
                sig = buy if buy.score >= sell.score else sell

                if not sig.hard_filters_passed or sig.score < CONFIG.watchlist_threshold or sig.category == "ignore":
                    continue

                total_signals += 1
                for th in threshold_counts:
                    if sig.score >= th:
                        threshold_counts[th] += 1

                sig_idx = time_to_idx.get(pd.Timestamp(sig.timestamp))
                if sig_idx is None:
                    continue

                if sig_idx + CONFIG.backtest_forward_bars >= len(m5):
                    continue

                entry = float(m5.iloc[sig_idx]["close"])
                future = float(m5.iloc[sig_idx + CONFIG.backtest_forward_bars]["close"])
                move = ((future - entry) / entry) * 100.0
                if sig.direction == "SELL":
                    move = -move
                results.append(move)

        avg_move = mean(results) if results else 0.0
        logger.info("BACKTEST SUMMARY")
        logger.info("Total signals: %s", total_signals)
        logger.info("Average move after signal (%s bars): %.4f%%", CONFIG.backtest_forward_bars, avg_move)
        logger.info("Threshold sensitivity: %s", threshold_counts)
    finally:
        connector.disconnect()


def run_sync() -> None:
    """Sync existing sent orders with MT5 history/positions only (no scanning, no new orders)."""
    setup_logging(CONFIG.log_level)
    logger.info("Sync mode: start order status/PnL synchronization")
    db = SignalDB(CONFIG.db_path)
    connector = connect_mt5(CONFIG)
    executor = ExecutionEngine(CONFIG, db)
    try:
        executor.sync_orders()
        logger.info("Sync mode: completed")
    finally:
        connector.disconnect()


def run_daemon() -> None:
    """Run scan + sync in one continuous loop using independent intervals."""
    setup_logging(CONFIG.log_level)
    logger.info(
        "Daemon mode: scan_interval=%ss sync_interval=%ss summary_interval=%ss",
        CONFIG.scan_interval_seconds,
        CONFIG.sync_interval_seconds,
        CONFIG.summary_interval_seconds,
    )
    db = SignalDB(CONFIG.db_path)
    connector = connect_mt5(CONFIG)
    fetcher = DataFetcher(connector)
    notifier = Notifier(CONFIG, db)
    executor = ExecutionEngine(CONFIG, db)

    now = time.time()
    next_scan = now
    next_sync = now
    next_summary = now

    try:
        while True:
            tick = time.time()
            if tick >= next_sync:
                executor.sync_orders()
                next_sync = tick + max(1, CONFIG.sync_interval_seconds)

            if tick >= next_scan:
                _scan_cycle(connector, fetcher, db, notifier, executor)
                next_scan = tick + max(1, CONFIG.scan_interval_seconds)

            if tick >= next_summary:
                logger.info(
                    "Daemon summary: open_orders=%s today_realized_loss=%.2f",
                    db.count_open_orders(),
                    db.today_realized_loss(),
                )
                next_summary = tick + max(10, CONFIG.summary_interval_seconds)

            time.sleep(1)
    finally:
        connector.disconnect()


def run_reset_loss_guard() -> None:
    """Reset daily loss guard checkpoint (UTC) without deleting order history."""
    setup_logging(CONFIG.log_level)
    db = SignalDB(CONFIG.db_path)
    reset_at = db.reset_daily_loss_guard()
    logger.info("Daily loss guard reset at UTC: %s", reset_at)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MT5 Crypto Signal Alert Scanner")
    parser.add_argument("--mode", choices=["scan", "backtest", "sync", "daemon", "reset_loss_guard"], default="scan")
    parser.add_argument("--once", action="store_true", help="Run single scan iteration then exit (scan mode only)")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.mode == "backtest":
        run_backtest()
    elif args.mode == "sync":
        run_sync()
    elif args.mode == "daemon":
        run_daemon()
    elif args.mode == "reset_loss_guard":
        run_reset_loss_guard()
    else:
        run_scanner(once=args.once)


if __name__ == "__main__":
    main()
