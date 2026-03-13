from __future__ import annotations

import io
import json
import re
import sqlite3
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from core.logger_db import SignalDB

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
PID_DIR = ROOT / ".runtime"
PID_FILE = PID_DIR / "daemon_pid.json"
TASK_DAEMON = "PyTradeDaemon"
TASK_DASHBOARD = "PyTradeDashboard"

TXT = {
    "th": {
        "title": "ศูนย์ควบคุม PyTrade",
        "tab_dashboard": "แดชบอร์ด",
        "tab_portfolio": "สถานะพอร์ต",
        "tab_config": "ตั้งค่า",
        "tab_guide": "คู่มือใช้งาน",
        "tab_deploy": "Deploy Wizard",
        "controls": "เมนูควบคุม",
        "daemon": "สถานะเดมอน",
        "active_mode": "หมวดที่ใช้งานตอนนี้",
        "profile_now": "โปรไฟล์",
        "alert_cat_now": "แจ้งเตือนขั้นต่ำ",
        "exec_cat_now": "ส่งคำสั่งขั้นต่ำ",
        "filter_mode_now": "โหมดคัดกรอง",
        "db": "ฐานข้อมูล",
        "scan_once": "สแกน 1 รอบ",
        "sync": "ซิงก์ออเดอร์",
        "start_daemon": "เริ่มเดมอน",
        "stop_daemon": "หยุดเดมอน",
        "language": "ภาษา",
        "auto_refresh": "รีเฟรชอัตโนมัติ",
        "refresh_sec": "ทุกกี่วินาที",
        "refresh_hint": "เมื่อเปิด ระบบจะรีโหลดหน้าเว็บอัตโนมัติทุก N วินาที",
        "overview": "ภาพรวมการเทรด",
        "open": "ออเดอร์เปิด",
        "sent": "ส่งแล้ว",
        "closed": "ปิดแล้ว",
        "failed": "ล้มเหลว",
        "today_pnl": "กำไร/ขาดทุน วันนี้",
        "cleanup": "ล้างข้อมูลรบกวน",
        "del_below": "ลบ skipped: below_min_execute_category",
        "del_cooldown": "ลบ skipped: cooldown_active",
        "reset_loss_guard": "รีเซ็ต Daily Loss Guard (UTC)",
        "loss_guard_reset_at": "รีเซ็ตล่าสุด (UTC)",
        "loss_guard_effective": "Realized Loss หลังรีเซ็ต",
        "equity": "กราฟ Equity Curve (จากออเดอร์ปิด)",
        "orders": "ออเดอร์ล่าสุด",
        "signals": "สัญญาณล่าสุด",
        "events": "เหตุการณ์สแกนล่าสุด",
        "no_orders": "ยังไม่มีออเดอร์",
        "no_signals": "ยังไม่มีสัญญาณ",
        "no_events": "ยังไม่มีเหตุการณ์สแกน",
        "no_closed": "ยังไม่มีออเดอร์ที่ปิดพร้อม PnL",
        "order_symbol": "สัญลักษณ์ออเดอร์",
        "order_status": "สถานะออเดอร์",
        "order_reason": "เหตุผลออเดอร์",
        "signal_symbol": "สัญลักษณ์สัญญาณ",
        "signal_category": "หมวดสัญญาณ",
        "signal_direction": "ทิศทาง",
        "download_orders": "ดาวน์โหลด Orders (CSV)",
        "download_signals": "ดาวน์โหลด Signals (CSV)",
        "download_events": "ดาวน์โหลด Events (CSV)",
        "portfolio": "สถานะพอร์ต MT5",
        "refresh_portfolio": "รีเฟรชพอร์ต MT5",
        "positions": "ตำแหน่งที่เปิดอยู่",
        "account": "ข้อมูลบัญชี",
        "no_positions": "ไม่มีตำแหน่งที่เปิดอยู่",
        "mt5_error": "เชื่อม MT5 ไม่สำเร็จ",
        "env_editor": "แก้ไขไฟล์ .env",
        "env_label": "แก้ไขค่า .env",
        "save_env": "บันทึก .env",
        "saved": "บันทึก .env เรียบร้อย",
        "config_wizard": "ตัวช่วยปรับค่าระบบ",
        "preset": "โปรไฟล์สำเร็จรูป",
        "apply_preset": "ใช้โปรไฟล์นี้",
        "preset_applied": "อัปเดตโปรไฟล์เรียบร้อย",
        "save_structured": "บันทึกค่าจากฟอร์ม",
        "saved_structured": "บันทึกค่าจากฟอร์มเรียบร้อย",
        "restart_hint": "หลังบันทึก ให้รีสตาร์ทเดมอน/สแกนใหม่เพื่อโหลดค่าใหม่",
        "raw_editor": "โหมดแก้ไขดิบ (.env)",
        "task_manager": "ตัวจัดการงานถาวร (Task Scheduler)",
        "install_tasks": "ติดตั้งงานถาวร",
        "uninstall_tasks": "ถอนงานถาวร",
        "task_daemon": "งาน Daemon",
        "task_dashboard": "งาน Dashboard",
        "task_run": "Run",
        "task_stop": "Stop",
        "task_status": "สถานะงาน",
        "config_audit": "ประวัติการปรับค่า",
        "no_audit": "ยังไม่มีประวัติการปรับค่า",
        "all": "ALL",
        "deploy_title": "สร้างแพ็ก deploy รายเครื่อง",
        "deploy_machine": "ชื่อเครื่อง/ไซต์",
        "deploy_target_root": "โฟลเดอร์ปลายทางของโปรเจกต์",
        "deploy_include_secret": "รวมข้อมูลลับ (MT5/Telegram)",
        "deploy_install_tasks": "ให้สคริปต์ติดตั้งงาน Task Scheduler",
        "deploy_run_sync": "ให้สคริปต์รัน reset_loss_guard + sync หลังติดตั้ง",
        "deploy_start_daemon": "ให้สคริปต์สั่ง Start งาน Daemon หลังติดตั้ง",
        "deploy_start_dashboard": "ให้สคริปต์สั่ง Start งาน Dashboard หลังติดตั้ง",
        "deploy_download": "ดาวน์โหลดแพ็ก deploy (.zip)",
        "deploy_preview": "ตัวอย่างค่าใน deploy_profile.env",
        "deploy_note": "นำ zip ไปเครื่องปลายทาง แตกไฟล์ แล้วรัน install_profile.ps1",
    },
    "en": {
        "title": "PyTrade Control Center",
        "tab_dashboard": "Dashboard",
        "tab_portfolio": "Portfolio",
        "tab_config": "Config",
        "tab_guide": "Guide",
        "tab_deploy": "Deploy Wizard",
        "controls": "Controls",
        "daemon": "Daemon",
        "active_mode": "Active Mode",
        "profile_now": "Profile",
        "alert_cat_now": "Min Alert Category",
        "exec_cat_now": "Min Execute Category",
        "filter_mode_now": "Filter Mode",
        "db": "Database",
        "scan_once": "Run Scan Once",
        "sync": "Run Sync",
        "start_daemon": "Start Daemon",
        "stop_daemon": "Stop Daemon",
        "language": "Language",
        "auto_refresh": "Auto Refresh",
        "refresh_sec": "Refresh seconds",
        "refresh_hint": "When enabled, this page auto-reloads every N seconds.",
        "overview": "Trading Overview",
        "open": "Open",
        "sent": "Sent",
        "closed": "Closed",
        "failed": "Failed",
        "today_pnl": "Today PnL",
        "cleanup": "Cleanup",
        "del_below": "Delete skipped: below_min_execute_category",
        "del_cooldown": "Delete skipped: cooldown_active",
        "reset_loss_guard": "Reset Daily Loss Guard (UTC)",
        "loss_guard_reset_at": "Last reset (UTC)",
        "loss_guard_effective": "Realized Loss after reset",
        "equity": "Equity Curve (Closed PnL)",
        "orders": "Recent Orders",
        "signals": "Recent Signals",
        "events": "Recent Scan Events",
        "no_orders": "No orders yet",
        "no_signals": "No signals yet",
        "no_events": "No scan events",
        "no_closed": "No closed orders with PnL",
        "order_symbol": "Order Symbol",
        "order_status": "Order Status",
        "order_reason": "Order Reason",
        "signal_symbol": "Signal Symbol",
        "signal_category": "Signal Category",
        "signal_direction": "Direction",
        "download_orders": "Download Orders (CSV)",
        "download_signals": "Download Signals (CSV)",
        "download_events": "Download Events (CSV)",
        "portfolio": "MT5 Portfolio Status",
        "refresh_portfolio": "Refresh MT5 Portfolio",
        "positions": "Open Positions",
        "account": "Account Info",
        "no_positions": "No open positions",
        "mt5_error": "MT5 connection failed",
        "env_editor": "Edit .env",
        "env_label": "Edit .env content",
        "save_env": "Save .env",
        "saved": ".env saved",
        "config_wizard": "Configuration Wizard",
        "preset": "Preset",
        "apply_preset": "Apply preset",
        "preset_applied": "Preset applied",
        "save_structured": "Save form settings",
        "saved_structured": "Form settings saved",
        "restart_hint": "After saving, restart daemon/scan to reload new settings",
        "raw_editor": "Raw .env editor",
        "task_manager": "Task Scheduler Manager",
        "install_tasks": "Install persistent tasks",
        "uninstall_tasks": "Uninstall persistent tasks",
        "task_daemon": "Daemon Task",
        "task_dashboard": "Dashboard Task",
        "task_run": "Run",
        "task_stop": "Stop",
        "task_status": "Task status",
        "config_audit": "Config Change History",
        "no_audit": "No config change history",
        "all": "ALL",
        "deploy_title": "Create machine-specific deploy package",
        "deploy_machine": "Machine/Site name",
        "deploy_target_root": "Target project folder",
        "deploy_include_secret": "Include secrets (MT5/Telegram)",
        "deploy_install_tasks": "Install Task Scheduler jobs in script",
        "deploy_run_sync": "Run reset_loss_guard + sync after install",
        "deploy_start_daemon": "Start Daemon task after install",
        "deploy_start_dashboard": "Start Dashboard task after install",
        "deploy_download": "Download deploy package (.zip)",
        "deploy_preview": "Preview deploy_profile.env",
        "deploy_note": "Copy zip to target machine, extract, then run install_profile.ps1",
    },
}

HELP = {
    "th": {
        "preset": "ชุดค่าพร้อมใช้ตามสไตล์การเทรด",
        "symbols": "รายชื่อสินทรัพย์ที่ระบบจะสแกน (คั่นด้วย comma)",
        "hard_filter_mode": "strict = คัดเข้ม, soft = ผ่อนเงื่อนไข",
        "adx_minimum": "ค่า ADX ขั้นต่ำ ยิ่งสูงยิ่งเน้นเทรนด์ชัด",
        "entry_zone_max_atr": "ระยะห่างจากโซนเข้า (ATR) ยิ่งต่ำยิ่งไม่ไล่ราคา",
        "m5_min_triggers": "จำนวน trigger M5 ขั้นต่ำก่อนผ่านเงื่อนไขเข้า",
        "risk_per_trade_pct": "เปอร์เซ็นต์ความเสี่ยงต่อไม้เทียบทุน",
        "daily_loss_limit": "ขาดทุนสะสมต่อวันสูงสุดก่อนหยุดส่งคำสั่ง",
        "max_open_positions": "จำนวนออเดอร์เปิดพร้อมกันสูงสุด (ฐาน)",
        "order_cooldown_minutes": "เวลาพักก่อนเข้าออเดอร์ซ้ำสัญลักษณ์เดิม",
        "min_execute_category": "ระดับสัญญาณขั้นต่ำที่อนุญาตให้ส่งคำสั่งจริง",
        "watchlist_threshold": "คะแนนขั้นต่ำสำหรับ candidate",
        "alert_threshold": "คะแนนขั้นต่ำสำหรับ alert",
        "strong_alert_threshold": "คะแนนขั้นต่ำสำหรับ strong",
        "premium_alert_threshold": "คะแนนขั้นต่ำสำหรับ premium",
        "min_alert_category": "ระดับสัญญาณขั้นต่ำที่จะแจ้งเตือน",
        "enable_smart_exit": "เปิดระบบบริหารการออกออเดอร์อัตโนมัติ",
        "enable_break_even": "เปิดการย้าย SL ไปจุดคุ้มทุน",
        "break_even_trigger_r": "กำไรถึงกี่ R จึงเริ่มย้าย SL",
        "break_even_lock_r": "ล็อกกำไรเพิ่มจากคุ้มทุนอีกกี่ R",
        "enable_trailing_stop": "เปิดการเลื่อน SL ตามราคา",
        "trailing_start_r": "เริ่ม trailing เมื่อกำไรถึงกี่ R",
        "trailing_distance_r": "ระยะ trailing เป็นกี่ R",
        "enable_partial_close": "เปิดการปิดกำไรบางส่วน",
        "partial_close_trigger_r": "กำไรถึงกี่ R จึงปิดบางส่วน",
        "partial_close_ratio": "สัดส่วนที่ปิดบางส่วน (0.3 = 30%)",
        "scan_interval_seconds": "ความถี่สแกนเป็นวินาที",
        "sync_interval_seconds": "ความถี่ซิงก์สถานะออเดอร์เป็นวินาที",
        "dry_run": "เปิดแล้วจะไม่ส่งคำสั่งจริง",
        "enable_execution": "เปิดการส่งคำสั่งเทรด",
        "execution_mode": "แนะนำใช้ demo ในการทดสอบ",
        "sl_atr_multiplier": "ระยะ Stop Loss เทียบ ATR",
        "target_rr": "อัตรา Reward:Risk เป้าหมาย",
        "enable_premium_stack": "อนุญาตเพิ่มสล็อตเมื่อสัญญาณ premium",
        "premium_stack_extra_slots": "จำนวนสล็อตเพิ่มสำหรับ premium",
        "enable_ultra_stack": "อนุญาตเพิ่มสล็อตเมื่อคะแนน ultra",
        "ultra_stack_score": "คะแนนขั้นต่ำที่ถือเป็น ultra",
        "ultra_stack_extra_slots": "จำนวนสล็อตเพิ่มสำหรับ ultra",
    },
    "en": {
        "preset": "Ready-made parameter pack by trading style",
        "symbols": "Assets to scan (comma-separated)",
        "hard_filter_mode": "strict = tighter filter, soft = looser filter",
        "adx_minimum": "Minimum ADX; higher means stronger trend requirement",
        "entry_zone_max_atr": "Max distance from entry zone in ATR",
        "m5_min_triggers": "Minimum number of M5 triggers before entry",
        "risk_per_trade_pct": "Risk per trade as % of account",
        "daily_loss_limit": "Daily realized loss cap before blocking new orders",
        "max_open_positions": "Base max concurrent open orders",
        "order_cooldown_minutes": "Cooldown before same-symbol re-entry",
        "min_execute_category": "Minimum signal category allowed for execution",
        "watchlist_threshold": "Minimum score for candidate",
        "alert_threshold": "Minimum score for alert",
        "strong_alert_threshold": "Minimum score for strong",
        "premium_alert_threshold": "Minimum score for premium",
        "min_alert_category": "Minimum signal category for notifications",
        "enable_smart_exit": "Enable automated in-trade exit management",
        "enable_break_even": "Move SL to break-even when conditions met",
        "break_even_trigger_r": "R multiple required to trigger break-even",
        "break_even_lock_r": "Extra R locked beyond break-even",
        "enable_trailing_stop": "Enable trailing stop logic",
        "trailing_start_r": "R multiple to start trailing",
        "trailing_distance_r": "Trailing distance in R",
        "enable_partial_close": "Enable partial profit-taking",
        "partial_close_trigger_r": "R multiple to trigger partial close",
        "partial_close_ratio": "Portion to close (0.3 = 30%)",
        "scan_interval_seconds": "Scan loop interval in seconds",
        "sync_interval_seconds": "Order sync interval in seconds",
        "dry_run": "If enabled, do not send real orders",
        "enable_execution": "Enable order execution",
        "execution_mode": "Recommended to keep demo for testing",
        "sl_atr_multiplier": "Stop-loss distance in ATR multiples",
        "target_rr": "Target reward-to-risk ratio",
        "enable_premium_stack": "Allow extra slots for premium signals",
        "premium_stack_extra_slots": "Extra slots for premium signals",
        "enable_ultra_stack": "Allow extra slots for ultra score signals",
        "ultra_stack_score": "Score threshold considered ultra",
        "ultra_stack_extra_slots": "Extra slots for ultra signals",
    },
}


def t(key: str) -> str:
    lang = st.session_state.get("lang", "th")
    return TXT.get(lang, TXT["th"]).get(key, key)


def h(key: str) -> str:
    lang = st.session_state.get("lang", "th")
    return HELP.get(lang, HELP["th"]).get(key, "")


def _config_help_df() -> pd.DataFrame:
    labels = {
        "symbols": "SYMBOLS",
        "hard_filter_mode": "HARD_FILTER_MODE",
        "adx_minimum": "ADX_MINIMUM",
        "entry_zone_max_atr": "ENTRY_ZONE_MAX_ATR",
        "m5_min_triggers": "M5_MIN_TRIGGERS",
        "risk_per_trade_pct": "RISK_PER_TRADE_PCT",
        "daily_loss_limit": "DAILY_LOSS_LIMIT",
        "max_open_positions": "MAX_OPEN_POSITIONS",
        "order_cooldown_minutes": "ORDER_COOLDOWN_MINUTES",
        "min_execute_category": "MIN_EXECUTE_CATEGORY",
        "watchlist_threshold": "WATCHLIST_THRESHOLD",
        "alert_threshold": "ALERT_THRESHOLD",
        "strong_alert_threshold": "STRONG_ALERT_THRESHOLD",
        "premium_alert_threshold": "PREMIUM_ALERT_THRESHOLD",
        "min_alert_category": "MIN_ALERT_CATEGORY",
        "enable_smart_exit": "ENABLE_SMART_EXIT",
        "enable_break_even": "ENABLE_BREAK_EVEN",
        "break_even_trigger_r": "BREAK_EVEN_TRIGGER_R",
        "break_even_lock_r": "BREAK_EVEN_LOCK_R",
        "enable_trailing_stop": "ENABLE_TRAILING_STOP",
        "trailing_start_r": "TRAILING_START_R",
        "trailing_distance_r": "TRAILING_DISTANCE_R",
        "enable_partial_close": "ENABLE_PARTIAL_CLOSE",
        "partial_close_trigger_r": "PARTIAL_CLOSE_TRIGGER_R",
        "partial_close_ratio": "PARTIAL_CLOSE_RATIO",
        "scan_interval_seconds": "SCAN_INTERVAL_SECONDS",
        "sync_interval_seconds": "SYNC_INTERVAL_SECONDS",
        "dry_run": "DRY_RUN",
        "enable_execution": "ENABLE_EXECUTION",
        "execution_mode": "EXECUTION_MODE",
        "sl_atr_multiplier": "SL_ATR_MULTIPLIER",
        "target_rr": "TARGET_RR",
        "enable_premium_stack": "ENABLE_PREMIUM_STACK",
        "premium_stack_extra_slots": "PREMIUM_STACK_EXTRA_SLOTS",
        "enable_ultra_stack": "ENABLE_ULTRA_STACK",
        "ultra_stack_score": "ULTRA_STACK_SCORE",
        "ultra_stack_extra_slots": "ULTRA_STACK_EXTRA_SLOTS",
    }
    rows = [{"key": env_key, "meaning": h(help_key)} for help_key, env_key in labels.items()]
    return pd.DataFrame(rows)


def _load_env_map() -> dict[str, str]:
    data: dict[str, str] = {}
    if not ENV_PATH.exists():
        return data
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def _parse_int_env(env: dict[str, str], key: str, default: int) -> int:
    try:
        return int(str(env.get(key, default)))
    except (ValueError, TypeError):
        return default


def _parse_float_env(env: dict[str, str], key: str, default: float) -> float:
    try:
        return float(str(env.get(key, default)))
    except (ValueError, TypeError):
        return default


def _parse_bool_env(env: dict[str, str], key: str, default: bool) -> bool:
    raw = str(env.get(key, "true" if default else "false")).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _upsert_env_values(updates: dict[str, str]) -> None:
    if not ENV_PATH.exists():
        base = ""
    else:
        base = ENV_PATH.read_text(encoding="utf-8")
    lines = base.splitlines()
    out: list[str] = []
    replaced: set[str] = set()

    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            out.append(line)
            continue
        key, _ = line.split("=", 1)
        k = key.strip()
        if k in updates:
            if k in replaced:
                continue
            out.append(f"{k}={updates[k]}")
            replaced.add(k)
        else:
            out.append(line)

    missing = [k for k in updates if k not in replaced]
    if missing:
        if out and out[-1].strip():
            out.append("")
        out.append("# Auto-updated by Streamlit Config Wizard")
        for k in missing:
            out.append(f"{k}={updates[k]}")

    ENV_PATH.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


DEPLOY_BASE_KEYS = [
    "SYMBOLS",
    "TIMEFRAME_PRIMARY",
    "TIMEFRAME_CONFIRM",
    "TIMEFRAME_SETUP",
    "TIMEFRAME_TRIGGER",
    "BARS_TO_FETCH",
    "SCAN_INTERVAL_SECONDS",
    "SYNC_INTERVAL_SECONDS",
    "SUMMARY_INTERVAL_SECONDS",
    "SIGNAL_PROFILE",
    "WATCHLIST_THRESHOLD",
    "ALERT_THRESHOLD",
    "STRONG_ALERT_THRESHOLD",
    "PREMIUM_ALERT_THRESHOLD",
    "ADX_MINIMUM",
    "ENTRY_ZONE_MAX_ATR",
    "HARD_FILTER_MODE",
    "M5_MIN_TRIGGERS",
    "ANTI_DUP_SCORE_DELTA",
    "MIN_ALERT_CATEGORY",
    "ACCOUNT_BALANCE",
    "RISK_PER_TRADE_PCT",
    "SL_ATR_MULTIPLIER",
    "TARGET_RR",
    "DRY_RUN",
    "ENABLE_EXECUTION",
    "EXECUTION_MODE",
    "MIN_EXECUTE_CATEGORY",
    "MAX_OPEN_POSITIONS",
    "ENABLE_PREMIUM_STACK",
    "PREMIUM_STACK_EXTRA_SLOTS",
    "ENABLE_ULTRA_STACK",
    "ULTRA_STACK_SCORE",
    "ULTRA_STACK_EXTRA_SLOTS",
    "DAILY_LOSS_LIMIT",
    "ORDER_COOLDOWN_MINUTES",
    "MAX_SLIPPAGE_POINTS",
    "FIXED_LOT",
    "MAGIC_NUMBER",
    "ENABLE_SMART_EXIT",
    "ENABLE_BREAK_EVEN",
    "BREAK_EVEN_TRIGGER_R",
    "BREAK_EVEN_LOCK_R",
    "ENABLE_TRAILING_STOP",
    "TRAILING_START_R",
    "TRAILING_DISTANCE_R",
    "ENABLE_PARTIAL_CLOSE",
    "PARTIAL_CLOSE_TRIGGER_R",
    "PARTIAL_CLOSE_RATIO",
    "LOG_SKIPPED_REASONS",
]

DEPLOY_SENSITIVE_KEYS = [
    "MT5_PATH",
    "MT5_LOGIN",
    "MT5_PASSWORD",
    "MT5_SERVER",
    "TELEGRAM_ENABLED",
    "TELEGRAM_TOKEN",
    "TELEGRAM_CHAT_ID",
    "LINE_ENABLED",
    "LINE_TOKEN",
]


def _sanitize_name(value: str, fallback: str = "machine") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", (value or "").strip())
    cleaned = cleaned.strip("-._")
    return cleaned or fallback


def _build_deploy_profile_lines(env: dict[str, str], include_sensitive: bool) -> list[str]:
    keys = list(DEPLOY_BASE_KEYS)
    if include_sensitive:
        keys += DEPLOY_SENSITIVE_KEYS
    lines = ["# Generated by PyTrade Deploy Wizard", f"# UTC: {datetime.now(timezone.utc).isoformat()}"]
    for key in keys:
        if key in env:
            lines.append(f"{key}={env[key]}")
    return lines


def _build_deploy_package(
    *,
    env: dict[str, str],
    machine_name: str,
    target_root: str,
    include_sensitive: bool,
    install_tasks: bool,
    run_sync: bool,
    start_daemon: bool,
    start_dashboard: bool,
) -> tuple[bytes, str, str]:
    safe_machine = _sanitize_name(machine_name, "site")
    profile_lines = _build_deploy_profile_lines(env, include_sensitive)
    profile_text = "\n".join(profile_lines).rstrip() + "\n"

    manifest = {
        "machine_name": machine_name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_root": target_root,
        "include_sensitive": include_sensitive,
        "install_tasks": install_tasks,
        "run_sync": run_sync,
        "start_daemon": start_daemon,
        "start_dashboard": start_dashboard,
    }

    installer_ps1 = """param(
    [string]$ProjectRoot = "C:\\pytrade"
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$profilePath = Join-Path $here "deploy_profile.env"
$projectRootResolved = (Resolve-Path $ProjectRoot).Path
$envPath = Join-Path $projectRootResolved ".env"

if (!(Test-Path $profilePath)) { throw "ไม่พบ deploy_profile.env" }
if (!(Test-Path $envPath)) { throw "ไม่พบ .env ที่ปลายทาง: $envPath" }

function Upsert-EnvKey([string]$path, [string]$key, [string]$value) {
    $lines = @()
    if (Test-Path $path) { $lines = Get-Content $path -Encoding UTF8 }
    $found = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i].Trim()
        if ($line.StartsWith("$key=")) {
            $lines[$i] = "$key=$value"
            $found = $true
            break
        }
    }
    if (-not $found) { $lines += "$key=$value" }
    Set-Content -Path $path -Encoding UTF8 -Value $lines
}

$pairs = Get-Content $profilePath -Encoding UTF8 | Where-Object {
    $_ -and (-not $_.StartsWith("#")) -and ($_.Contains("="))
}
foreach ($line in $pairs) {
    $k, $v = $line.Split("=", 2)
    Upsert-EnvKey -path $envPath -key $k.Trim() -value $v
}

$manifest = Get-Content (Join-Path $here "deploy_manifest.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$installScript = Join-Path $projectRootResolved "scripts\\install_windows.ps1"
if ($manifest.install_tasks -and (Test-Path $installScript)) {
    powershell -ExecutionPolicy Bypass -File $installScript -ProjectRoot $projectRootResolved
}

$venvPy = Join-Path $projectRootResolved ".venv\\Scripts\\python.exe"
if ($manifest.run_sync -and (Test-Path $venvPy)) {
    & $venvPy main.py --mode reset_loss_guard
    & $venvPy main.py --mode sync
}

if ($manifest.start_daemon) {
    schtasks /Run /TN "PyTradeDaemon" | Out-Null
}
if ($manifest.start_dashboard) {
    schtasks /Run /TN "PyTradeDashboard" | Out-Null
}

Write-Host "Deploy apply เสร็จสิ้น" -ForegroundColor Green
"""

    readme_text = f"""PyTrade Deploy Package
Machine: {machine_name}
Generated(UTC): {manifest["generated_at_utc"]}

วิธีใช้บนเครื่องปลายทาง:
1) วางโฟลเดอร์โปรเจกต์ไว้ที่: {target_root}
2) แตกไฟล์ zip นี้
3) เปิด PowerShell (Run as Administrator)
4) รัน:
   powershell -ExecutionPolicy Bypass -File .\\install_profile.ps1 -ProjectRoot "{target_root}"

ไฟล์นี้จะ:
- merge ค่าใน deploy_profile.env เข้า .env ปลายทาง
- ติดตั้งงาน Task Scheduler (ถ้าเปิดไว้)
- สั่ง reset_loss_guard + sync (ถ้าเปิดไว้)
"""

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("deploy_profile.env", profile_text.encode("utf-8"))
        zf.writestr("deploy_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
        zf.writestr("install_profile.ps1", installer_ps1.encode("utf-8"))
        zf.writestr("README_DEPLOY.txt", readme_text.encode("utf-8"))

    file_name = f"pytrade_deploy_{safe_machine}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return mem.getvalue(), file_name, profile_text


def _load_env_db_path() -> Path:
    env = _load_env_map()
    return (ROOT / env.get("DB_PATH", "signals.db")).resolve()


def _db_connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _query_df(db_path: Path, sql: str) -> pd.DataFrame:
    if not db_path.exists():
        return pd.DataFrame()
    with _db_connect(db_path) as conn:
        return pd.read_sql_query(sql, conn)


def _exec_sql(db_path: Path, sql: str) -> None:
    if not db_path.exists():
        return
    with _db_connect(db_path) as conn:
        conn.execute(sql)
        conn.commit()


def _run_command(args: list[str], timeout: int = 180) -> tuple[int, str, str]:
    proc = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout, shell=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _task_query(task_name: str) -> tuple[bool, str]:
    code, out, err = _run_command(["schtasks", "/Query", "/TN", task_name, "/FO", "LIST", "/V"], timeout=30)
    if code != 0:
        return False, err or out
    return True, out


def _task_action(task_name: str, action: str) -> tuple[bool, str]:
    if action == "run":
        code, out, err = _run_command(["schtasks", "/Run", "/TN", task_name], timeout=30)
    elif action == "stop":
        code, out, err = _run_command(["schtasks", "/End", "/TN", task_name], timeout=30)
    else:
        return False, "invalid_action"
    return code == 0, (out or err or "ok")


def _is_pid_running(pid: int) -> bool:
    code, out, _ = _run_command(["tasklist", "/FI", f"PID eq {pid}"])
    return code == 0 and str(pid) in out


def _read_pid_info() -> dict | None:
    if not PID_FILE.exists():
        return None
    try:
        return json.loads(PID_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_pid_info(pid: int) -> None:
    PID_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(
        json.dumps(
            {
                "pid": pid,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "cmd": "py main.py --mode daemon",
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )


def _clear_pid_info() -> None:
    if PID_FILE.exists():
        PID_FILE.unlink()


def _start_daemon() -> tuple[bool, str]:
    info = _read_pid_info()
    if info and _is_pid_running(int(info.get("pid", 0))):
        return False, f"Daemon already running (PID={info['pid']})"

    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    proc = subprocess.Popen(
        ["py", "main.py", "--mode", "daemon"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        shell=False,
    )
    _write_pid_info(proc.pid)
    return True, f"Daemon started (PID={proc.pid})"


def _stop_daemon() -> tuple[bool, str]:
    info = _read_pid_info()
    if not info:
        return False, "No daemon PID file found"
    pid = int(info.get("pid", 0))
    if pid <= 0:
        _clear_pid_info()
        return False, "Invalid PID in file"

    code, out, err = _run_command(["taskkill", "/PID", str(pid), "/T", "/F"])
    _clear_pid_info()
    if code == 0:
        return True, f"Daemon stopped (PID={pid})"
    return False, f"Failed to stop daemon: {err or out}"


def _daemon_status() -> str:
    info = _read_pid_info()
    if not info:
        return "Stopped"
    pid = int(info.get("pid", 0))
    if pid > 0 and _is_pid_running(pid):
        return f"Running (PID={pid})"
    return "Stopped (stale pid file)"


def _metrics(db_path: Path) -> dict[str, float]:
    if not db_path.exists():
        return {"open": 0, "sent": 0, "closed": 0, "failed": 0, "today_pnl": 0.0}
    df = _query_df(
        db_path,
        """
        SELECT
          SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent_count,
          SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed_count,
          SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed_count,
          COALESCE(SUM(CASE WHEN status='closed' AND substr(closed_at,1,10)=date('now') THEN pnl ELSE 0 END), 0) AS today_pnl
        FROM orders
        """,
    )
    if df.empty:
        return {"open": 0, "sent": 0, "closed": 0, "failed": 0, "today_pnl": 0.0}
    r = df.iloc[0]
    sent_count = int(r.get("sent_count", 0) or 0)
    return {
        "open": sent_count,
        "sent": sent_count,
        "closed": int(r.get("closed_count", 0) or 0),
        "failed": int(r.get("failed_count", 0) or 0),
        "today_pnl": float(r.get("today_pnl", 0.0) or 0.0),
    }


def _render_controls(db_path: Path) -> None:
    st.sidebar.header(t("controls"))
    st.sidebar.caption(f"{t('db')}: {db_path}")
    st.sidebar.write(f"{t('daemon')}: **{_daemon_status()}**")
    env = _load_env_map()
    signal_profile = env.get("SIGNAL_PROFILE", "custom")
    min_alert = env.get("MIN_ALERT_CATEGORY", "alert")
    min_exec = env.get("MIN_EXECUTE_CATEGORY", "strong")
    filter_mode = env.get("HARD_FILTER_MODE", "strict")
    st.sidebar.markdown(f"**{t('active_mode')}**")
    st.sidebar.caption(
        f"{t('profile_now')}: `{signal_profile}`  \n"
        f"{t('filter_mode_now')}: `{filter_mode}`  \n"
        f"{t('alert_cat_now')}: `{min_alert}`  \n"
        f"{t('exec_cat_now')}: `{min_exec}`"
    )

    st.sidebar.selectbox(t("language"), ["th", "en"], key="lang")
    st.sidebar.checkbox(t("auto_refresh"), key="auto_refresh", value=False)
    st.sidebar.number_input(t("refresh_sec"), min_value=5, max_value=300, value=15, step=5, key="refresh_sec")
    st.sidebar.caption(t("refresh_hint"))

    if st.session_state.get("auto_refresh"):
        sec = int(st.session_state.get("refresh_sec", 15))
        st.markdown(f"<meta http-equiv='refresh' content='{sec}'>", unsafe_allow_html=True)

    if st.sidebar.button(t("scan_once"), use_container_width=True):
        with st.sidebar.status("...", expanded=True) as status:
            code, out, err = _run_command(["py", "main.py", "--mode", "scan", "--once"], timeout=600)
            status.write(out or "(no stdout)")
            if err:
                status.write(err)
            status.update(label=f"Done (code={code})", state="complete")

    if st.sidebar.button(t("sync"), use_container_width=True):
        with st.sidebar.status("...", expanded=True) as status:
            code, out, err = _run_command(["py", "main.py", "--mode", "sync"], timeout=300)
            status.write(out or "(no stdout)")
            if err:
                status.write(err)
            status.update(label=f"Done (code={code})", state="complete")

    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.button(t("start_daemon"), use_container_width=True):
            ok, msg = _start_daemon()
            (st.success if ok else st.warning)(msg)
    with c2:
        if st.button(t("stop_daemon"), use_container_width=True):
            ok, msg = _stop_daemon()
            (st.success if ok else st.warning)(msg)


def _render_dashboard(db_path: Path) -> None:
    st.subheader(t("overview"))
    env = _load_env_map()
    st.caption(
        f"{t('active_mode')}: "
        f"{t('profile_now')}=`{env.get('SIGNAL_PROFILE', 'custom')}` | "
        f"{t('filter_mode_now')}=`{env.get('HARD_FILTER_MODE', 'strict')}` | "
        f"{t('alert_cat_now')}=`{env.get('MIN_ALERT_CATEGORY', 'alert')}` | "
        f"{t('exec_cat_now')}=`{env.get('MIN_EXECUTE_CATEGORY', 'strong')}`"
    )
    m = _metrics(db_path)
    pnl_value = float(m["today_pnl"])
    pnl_text = f"{pnl_value:+.2f}" if abs(pnl_value) > 1e-12 else "0.00"
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t("open"), m["open"])
    c2.metric(t("sent"), m["sent"])
    c3.metric(t("closed"), m["closed"])
    c4.metric(t("failed"), m["failed"])
    c5.metric(t("today_pnl"), pnl_text)

    st.subheader(t("cleanup"))
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        if st.button(t("del_below"), use_container_width=True):
            _exec_sql(db_path, "DELETE FROM orders WHERE status='skipped' AND reason='below_min_execute_category'")
            st.success("OK")
    with cc2:
        if st.button(t("del_cooldown"), use_container_width=True):
            _exec_sql(db_path, "DELETE FROM orders WHERE status='skipped' AND reason='cooldown_active'")
            st.success("OK")
    with cc3:
        if st.button(t("reset_loss_guard"), use_container_width=True):
            if db_path.exists():
                db = SignalDB(str(db_path))
                reset_at = db.reset_daily_loss_guard()
                st.success(f"OK: {reset_at}")
            else:
                st.warning("DB not found")

    if db_path.exists():
        db = SignalDB(str(db_path))
        reset_at = db.get_runtime_state("daily_loss_reset_at") or "-"
        effective_loss = db.today_realized_loss()
        i1, i2 = st.columns(2)
        i1.caption(f"{t('loss_guard_reset_at')}: {reset_at}")
        i2.caption(f"{t('loss_guard_effective')}: {effective_loss:.2f}")

    st.subheader(t("equity"))
    pnl_df = _query_df(
        db_path,
        "SELECT id, pnl FROM orders WHERE status='closed' AND pnl IS NOT NULL ORDER BY id ASC",
    )
    if pnl_df.empty:
        st.info(t("no_closed"))
    else:
        pnl_df["equity_curve"] = pnl_df["pnl"].cumsum()
        st.line_chart(pnl_df[["id", "equity_curve"]].set_index("id"), use_container_width=True, height=220)

    st.subheader(t("orders"))
    orders = _query_df(
        db_path,
        """
        SELECT id, timestamp, symbol, direction, status, reason, score, volume, entry_price, stop_loss, take_profit, pnl, closed_at
        FROM orders ORDER BY id DESC LIMIT 200
        """,
    )
    if orders.empty:
        st.info(t("no_orders"))
    else:
        all_label = t("all")
        c1, c2, c3 = st.columns(3)
        with c1:
            f_symbol = st.selectbox(t("order_symbol"), [all_label] + sorted(orders["symbol"].dropna().astype(str).unique().tolist()))
        with c2:
            f_status = st.selectbox(t("order_status"), [all_label] + sorted(orders["status"].dropna().astype(str).unique().tolist()))
        with c3:
            f_reason = st.selectbox(t("order_reason"), [all_label] + sorted(orders["reason"].dropna().astype(str).unique().tolist()))

        view = orders.copy()
        if f_symbol != all_label:
            view = view[view["symbol"] == f_symbol]
        if f_status != all_label:
            view = view[view["status"] == f_status]
        if f_reason != all_label:
            view = view[view["reason"] == f_reason]

        st.dataframe(view, use_container_width=True, height=320)
        st.download_button(t("download_orders"), data=view.to_csv(index=False), file_name="orders_filtered.csv", mime="text/csv")

    st.subheader(t("signals"))
    signals = _query_df(
        db_path,
        "SELECT id, timestamp, symbol, direction, score, category, hard_filters_passed FROM signals ORDER BY id DESC LIMIT 200",
    )
    if signals.empty:
        st.info(t("no_signals"))
    else:
        all_label = t("all")
        c1, c2, c3 = st.columns(3)
        with c1:
            s_symbol = st.selectbox(t("signal_symbol"), [all_label] + sorted(signals["symbol"].dropna().astype(str).unique().tolist()))
        with c2:
            s_cat = st.selectbox(t("signal_category"), [all_label] + sorted(signals["category"].dropna().astype(str).unique().tolist()))
        with c3:
            s_dir = st.selectbox(t("signal_direction"), [all_label] + sorted(signals["direction"].dropna().astype(str).unique().tolist()))

        sview = signals.copy()
        if s_symbol != all_label:
            sview = sview[sview["symbol"] == s_symbol]
        if s_cat != all_label:
            sview = sview[sview["category"] == s_cat]
        if s_dir != all_label:
            sview = sview[sview["direction"] == s_dir]

        st.dataframe(sview, use_container_width=True, height=320)
        st.download_button(t("download_signals"), data=sview.to_csv(index=False), file_name="signals_filtered.csv", mime="text/csv")

    st.subheader(t("events"))
    events = _query_df(
        db_path,
        "SELECT id, timestamp, symbol, level, message FROM scan_events ORDER BY id DESC LIMIT 200",
    )
    if events.empty:
        st.info(t("no_events"))
    else:
        st.dataframe(events, use_container_width=True, height=260)
        st.download_button(t("download_events"), data=events.to_csv(index=False), file_name="events_recent.csv", mime="text/csv")


def _render_portfolio() -> None:
    st.subheader(t("portfolio"))
    if st.button(t("refresh_portfolio")):
        st.rerun()

    env = _load_env_map()
    try:
        import MetaTrader5 as mt5

        kwargs = {}
        if env.get("MT5_PATH"):
            kwargs["path"] = env["MT5_PATH"]
        if not mt5.initialize(**kwargs):
            code, msg = mt5.last_error()
            st.error(f"{t('mt5_error')}: {code} {msg}")
            return

        login = env.get("MT5_LOGIN")
        password = env.get("MT5_PASSWORD")
        server = env.get("MT5_SERVER")
        if login and password and server:
            mt5.login(login=int(login), password=password, server=server)

        account = mt5.account_info()
        if account:
            st.write(t("account"))
            st.json({
                "login": int(getattr(account, "login", 0) or 0),
                "balance": float(getattr(account, "balance", 0.0) or 0.0),
                "equity": float(getattr(account, "equity", 0.0) or 0.0),
                "margin": float(getattr(account, "margin", 0.0) or 0.0),
                "profit": float(getattr(account, "profit", 0.0) or 0.0),
                "trade_mode": int(getattr(account, "trade_mode", 0) or 0),
            })

        positions = mt5.positions_get() or []
        rows = []
        for p in positions:
            rows.append(
                {
                    "ticket": int(getattr(p, "ticket", 0) or 0),
                    "symbol": str(getattr(p, "symbol", "")),
                    "type": int(getattr(p, "type", 0) or 0),
                    "volume": float(getattr(p, "volume", 0.0) or 0.0),
                    "price_open": float(getattr(p, "price_open", 0.0) or 0.0),
                    "sl": float(getattr(p, "sl", 0.0) or 0.0),
                    "tp": float(getattr(p, "tp", 0.0) or 0.0),
                    "profit": float(getattr(p, "profit", 0.0) or 0.0),
                    "magic": int(getattr(p, "magic", 0) or 0),
                }
            )

        st.write(t("positions"))
        if not rows:
            st.info(t("no_positions"))
        else:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=340)

    except Exception as exc:
        st.error(str(exc))
    finally:
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
        except Exception:
            pass


def _render_config_editor() -> None:
    st.subheader(t("env_editor"))
    if not ENV_PATH.exists():
        st.warning(".env not found")
        return

    env = _load_env_map()
    db_path = _load_env_db_path()
    db = SignalDB(str(db_path))
    exec_options = ["alert", "strong", "premium"]
    min_exec_env = env.get("MIN_EXECUTE_CATEGORY", "strong")
    if min_exec_env not in exec_options:
        min_exec_env = "strong"
    min_alert_env = env.get("MIN_ALERT_CATEGORY", "alert")
    if min_alert_env not in exec_options:
        min_alert_env = "alert"

    st.markdown(f"### {t('config_wizard')}")
    with st.expander("ความหมายแต่ละหัวข้อ / Section meanings", expanded=False):
        if st.session_state.get("lang", "th") == "th":
            st.markdown(
                """
- **โปรไฟล์สำเร็จรูป (Preset)**: ชุดค่าพร้อมใช้ตามสไตล์การเทรด (aggressive/balanced/premium/ultra_premium)
- **SYMBOLS**: รายชื่อสินทรัพย์ที่ระบบจะสแกนและพิจารณาเข้าออเดอร์
- **Hard Filter**: กรองสัญญาณขั้นต้นก่อนให้คะแนน (เช่น ADX, ระยะห่างจากโซนเข้า, จำนวน trigger M5)
- **Thresholds**: เส้นแบ่งคะแนนของ candidate/alert/strong/premium
- **Execution Gate**: เงื่อนไขขั้นต่ำก่อนส่งคำสั่งจริง เช่น `MIN_EXECUTE_CATEGORY`, cooldown, จำนวนออเดอร์เปิดสูงสุด
- **Risk**: การคุมความเสี่ยงต่อไม้และต่อวัน เช่น `RISK_PER_TRADE_PCT`, `DAILY_LOSS_LIMIT`
- **Smart Exit**: กฎจัดการกำไร/ขาดทุนระหว่างถือออเดอร์ (Break-even, Trailing Stop, Partial Close)
- **Runtime**: ค่าความถี่การทำงานของระบบ (scan/sync interval, dry-run, execution mode)
- **Premium Stack**: อนุญาตให้เปิดออเดอร์เพิ่มได้แม้มีออเดอร์ค้างอยู่ เมื่อสัญญาณเป็น premium หรือคะแนนถึง ultra
                """
            )
        else:
            st.markdown(
                """
- **Preset**: Ready-made parameter packs by trading style (aggressive/balanced/premium/ultra_premium)
- **SYMBOLS**: Assets to scan and evaluate for entries
- **Hard Filter**: Pre-score gate (ADX, entry-zone distance, M5 trigger count)
- **Thresholds**: Score bands for candidate/alert/strong/premium
- **Execution Gate**: Minimum conditions before live order send (`MIN_EXECUTE_CATEGORY`, cooldown, max open positions)
- **Risk**: Per-trade and daily risk controls (`RISK_PER_TRADE_PCT`, `DAILY_LOSS_LIMIT`)
- **Smart Exit**: In-trade management (Break-even, Trailing Stop, Partial Close)
- **Runtime**: Engine frequency and mode settings (scan/sync interval, dry-run, execution mode)
- **Premium Stack**: Allow extra concurrent orders when signal is premium/ultra
                """
            )
    with st.expander("พจนานุกรมค่าตั้งค่า / Config glossary", expanded=False):
        st.dataframe(_config_help_df(), use_container_width=True, height=320)

    preset_map = {
        "ultra_premium": {
            "HARD_FILTER_MODE": "strict",
            "ADX_MINIMUM": "22",
            "ENTRY_ZONE_MAX_ATR": "1.3",
            "M5_MIN_TRIGGERS": "3",
            "WATCHLIST_THRESHOLD": "75",
            "ALERT_THRESHOLD": "85",
            "STRONG_ALERT_THRESHOLD": "90",
            "PREMIUM_ALERT_THRESHOLD": "94",
            "MIN_EXECUTE_CATEGORY": "premium",
            "MAX_OPEN_POSITIONS": "1",
            "ORDER_COOLDOWN_MINUTES": "45",
            "RISK_PER_TRADE_PCT": "0.10",
            "DAILY_LOSS_LIMIT": "100",
        },
        "premium": {
            "HARD_FILTER_MODE": "strict",
            "ADX_MINIMUM": "18",
            "ENTRY_ZONE_MAX_ATR": "1.8",
            "M5_MIN_TRIGGERS": "2",
            "WATCHLIST_THRESHOLD": "65",
            "ALERT_THRESHOLD": "75",
            "STRONG_ALERT_THRESHOLD": "85",
            "PREMIUM_ALERT_THRESHOLD": "90",
            "MIN_EXECUTE_CATEGORY": "premium",
            "MAX_OPEN_POSITIONS": "1",
            "ORDER_COOLDOWN_MINUTES": "30",
            "RISK_PER_TRADE_PCT": "0.15",
            "DAILY_LOSS_LIMIT": "120",
        },
        "balanced": {
            "HARD_FILTER_MODE": "soft",
            "ADX_MINIMUM": "16",
            "ENTRY_ZONE_MAX_ATR": "2.2",
            "M5_MIN_TRIGGERS": "2",
            "WATCHLIST_THRESHOLD": "45",
            "ALERT_THRESHOLD": "55",
            "STRONG_ALERT_THRESHOLD": "65",
            "PREMIUM_ALERT_THRESHOLD": "75",
            "MIN_EXECUTE_CATEGORY": "strong",
            "MAX_OPEN_POSITIONS": "2",
            "ORDER_COOLDOWN_MINUTES": "15",
            "RISK_PER_TRADE_PCT": "0.20",
            "DAILY_LOSS_LIMIT": "150",
        },
        "aggressive": {
            "HARD_FILTER_MODE": "soft",
            "ADX_MINIMUM": "12",
            "ENTRY_ZONE_MAX_ATR": "3.5",
            "M5_MIN_TRIGGERS": "1",
            "WATCHLIST_THRESHOLD": "35",
            "ALERT_THRESHOLD": "45",
            "STRONG_ALERT_THRESHOLD": "55",
            "PREMIUM_ALERT_THRESHOLD": "65",
            "MIN_EXECUTE_CATEGORY": "alert",
            "MAX_OPEN_POSITIONS": "3",
            "ORDER_COOLDOWN_MINUTES": "10",
            "RISK_PER_TRADE_PCT": "0.30",
            "DAILY_LOSS_LIMIT": "200",
        },
    }
    p1, p2 = st.columns([2, 1])
    with p1:
        preset = st.selectbox(t("preset"), list(preset_map.keys()), index=2, help=h("preset"))
    with p2:
        # Align button baseline with preset selectbox control.
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        if st.button(t("apply_preset"), use_container_width=True):
            _upsert_env_values(preset_map[preset])
            db.log_config_change(
                source="streamlit_preset",
                summary=f"apply_preset:{preset}",
                changes=preset_map[preset],
            )
            st.success(t("preset_applied"))
            st.info(t("restart_hint"))
            st.rerun()

    with st.form("config_wizard_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            symbols = st.text_input("SYMBOLS", value=env.get("SYMBOLS", "BTCUSD,ETHUSD,XAUUSD"), help=h("symbols"))
            hard_mode = st.selectbox("HARD_FILTER_MODE", ["strict", "soft"], index=0 if env.get("HARD_FILTER_MODE", "strict") == "strict" else 1, help=h("hard_filter_mode"))
            adx_min = st.number_input("ADX_MINIMUM", min_value=5.0, max_value=50.0, value=_parse_float_env(env, "ADX_MINIMUM", 18.0), step=0.5, help=h("adx_minimum"))
            entry_zone = st.number_input("ENTRY_ZONE_MAX_ATR", min_value=0.5, max_value=5.0, value=_parse_float_env(env, "ENTRY_ZONE_MAX_ATR", 1.8), step=0.1, help=h("entry_zone_max_atr"))
            m5_triggers = st.slider("M5_MIN_TRIGGERS", min_value=1, max_value=4, value=_parse_int_env(env, "M5_MIN_TRIGGERS", 2), help=h("m5_min_triggers"))
        with c2:
            risk_pct = st.number_input("RISK_PER_TRADE_PCT", min_value=0.05, max_value=5.0, value=_parse_float_env(env, "RISK_PER_TRADE_PCT", 0.2), step=0.05, format="%.2f", help=h("risk_per_trade_pct"))
            daily_loss = st.number_input("DAILY_LOSS_LIMIT", min_value=10.0, max_value=5000.0, value=_parse_float_env(env, "DAILY_LOSS_LIMIT", 150.0), step=10.0, help=h("daily_loss_limit"))
            max_open = st.slider("MAX_OPEN_POSITIONS", min_value=1, max_value=10, value=_parse_int_env(env, "MAX_OPEN_POSITIONS", 2), help=h("max_open_positions"))
            cooldown = st.slider("ORDER_COOLDOWN_MINUTES", min_value=1, max_value=180, value=_parse_int_env(env, "ORDER_COOLDOWN_MINUTES", 15), help=h("order_cooldown_minutes"))
            min_exec = st.selectbox("MIN_EXECUTE_CATEGORY", exec_options, index=exec_options.index(min_exec_env), help=h("min_execute_category"))
        with c3:
            watch_th = st.slider("WATCHLIST_THRESHOLD", min_value=0, max_value=100, value=_parse_int_env(env, "WATCHLIST_THRESHOLD", 45), help=h("watchlist_threshold"))
            alert_th = st.slider("ALERT_THRESHOLD", min_value=0, max_value=100, value=_parse_int_env(env, "ALERT_THRESHOLD", 55), help=h("alert_threshold"))
            strong_th = st.slider("STRONG_ALERT_THRESHOLD", min_value=0, max_value=100, value=_parse_int_env(env, "STRONG_ALERT_THRESHOLD", 65), help=h("strong_alert_threshold"))
            premium_th = st.slider("PREMIUM_ALERT_THRESHOLD", min_value=0, max_value=100, value=_parse_int_env(env, "PREMIUM_ALERT_THRESHOLD", 75), help=h("premium_alert_threshold"))
            min_alert = st.selectbox("MIN_ALERT_CATEGORY", exec_options, index=exec_options.index(min_alert_env), help=h("min_alert_category"))

        st.markdown("#### Smart Exit")
        e1, e2, e3 = st.columns(3)
        with e1:
            enable_smart = st.checkbox("ENABLE_SMART_EXIT", value=_parse_bool_env(env, "ENABLE_SMART_EXIT", True), help=h("enable_smart_exit"))
            enable_be = st.checkbox("ENABLE_BREAK_EVEN", value=_parse_bool_env(env, "ENABLE_BREAK_EVEN", True), help=h("enable_break_even"))
            be_trigger = st.number_input("BREAK_EVEN_TRIGGER_R", min_value=0.2, max_value=5.0, value=_parse_float_env(env, "BREAK_EVEN_TRIGGER_R", 1.0), step=0.1, help=h("break_even_trigger_r"))
            be_lock = st.number_input("BREAK_EVEN_LOCK_R", min_value=0.0, max_value=2.0, value=_parse_float_env(env, "BREAK_EVEN_LOCK_R", 0.1), step=0.05, help=h("break_even_lock_r"))
        with e2:
            enable_trail = st.checkbox("ENABLE_TRAILING_STOP", value=_parse_bool_env(env, "ENABLE_TRAILING_STOP", True), help=h("enable_trailing_stop"))
            trail_start = st.number_input("TRAILING_START_R", min_value=0.5, max_value=10.0, value=_parse_float_env(env, "TRAILING_START_R", 1.5), step=0.1, help=h("trailing_start_r"))
            trail_dist = st.number_input("TRAILING_DISTANCE_R", min_value=0.2, max_value=10.0, value=_parse_float_env(env, "TRAILING_DISTANCE_R", 1.0), step=0.1, help=h("trailing_distance_r"))
        with e3:
            enable_pc = st.checkbox("ENABLE_PARTIAL_CLOSE", value=_parse_bool_env(env, "ENABLE_PARTIAL_CLOSE", True), help=h("enable_partial_close"))
            pc_trigger = st.number_input("PARTIAL_CLOSE_TRIGGER_R", min_value=0.5, max_value=10.0, value=_parse_float_env(env, "PARTIAL_CLOSE_TRIGGER_R", 1.5), step=0.1, help=h("partial_close_trigger_r"))
            pc_ratio = st.number_input("PARTIAL_CLOSE_RATIO", min_value=0.1, max_value=0.9, value=_parse_float_env(env, "PARTIAL_CLOSE_RATIO", 0.5), step=0.05, format="%.2f", help=h("partial_close_ratio"))

        st.markdown("#### Runtime")
        r1, r2, r3 = st.columns(3)
        with r1:
            scan_interval = st.number_input("SCAN_INTERVAL_SECONDS", min_value=5, max_value=3600, value=_parse_int_env(env, "SCAN_INTERVAL_SECONDS", 15), step=5, help=h("scan_interval_seconds"))
            sync_interval = st.number_input("SYNC_INTERVAL_SECONDS", min_value=5, max_value=3600, value=_parse_int_env(env, "SYNC_INTERVAL_SECONDS", 30), step=5, help=h("sync_interval_seconds"))
        with r2:
            dry_run = st.checkbox("DRY_RUN", value=_parse_bool_env(env, "DRY_RUN", True), help=h("dry_run"))
            enable_exec = st.checkbox("ENABLE_EXECUTION", value=_parse_bool_env(env, "ENABLE_EXECUTION", False), help=h("enable_execution"))
            exec_mode = st.selectbox("EXECUTION_MODE", ["demo", "live"], index=0 if env.get("EXECUTION_MODE", "demo") == "demo" else 1, help=h("execution_mode"))
        with r3:
            sl_mult = st.number_input("SL_ATR_MULTIPLIER", min_value=0.5, max_value=10.0, value=_parse_float_env(env, "SL_ATR_MULTIPLIER", 1.5), step=0.1, help=h("sl_atr_multiplier"))
            target_rr = st.number_input("TARGET_RR", min_value=0.5, max_value=10.0, value=_parse_float_env(env, "TARGET_RR", 1.8), step=0.1, help=h("target_rr"))

        st.markdown("#### Premium Stack")
        ps1, ps2, ps3 = st.columns(3)
        with ps1:
            enable_premium_stack = st.checkbox("ENABLE_PREMIUM_STACK", value=_parse_bool_env(env, "ENABLE_PREMIUM_STACK", True), help=h("enable_premium_stack"))
            premium_extra_slots = st.number_input("PREMIUM_STACK_EXTRA_SLOTS", min_value=0, max_value=10, value=_parse_int_env(env, "PREMIUM_STACK_EXTRA_SLOTS", 1), step=1, help=h("premium_stack_extra_slots"))
        with ps2:
            enable_ultra_stack = st.checkbox("ENABLE_ULTRA_STACK", value=_parse_bool_env(env, "ENABLE_ULTRA_STACK", True), help=h("enable_ultra_stack"))
            ultra_score = st.number_input("ULTRA_STACK_SCORE", min_value=0.0, max_value=100.0, value=_parse_float_env(env, "ULTRA_STACK_SCORE", 95.0), step=1.0, help=h("ultra_stack_score"))
        with ps3:
            ultra_extra_slots = st.number_input("ULTRA_STACK_EXTRA_SLOTS", min_value=0, max_value=10, value=_parse_int_env(env, "ULTRA_STACK_EXTRA_SLOTS", 2), step=1, help=h("ultra_stack_extra_slots"))

        submitted = st.form_submit_button(t("save_structured"), type="primary")
        if submitted:
            updates = {
                "SYMBOLS": symbols,
                "HARD_FILTER_MODE": hard_mode,
                "ADX_MINIMUM": f"{adx_min:.2f}",
                "ENTRY_ZONE_MAX_ATR": f"{entry_zone:.2f}",
                "M5_MIN_TRIGGERS": str(m5_triggers),
                "RISK_PER_TRADE_PCT": f"{risk_pct:.2f}",
                "DAILY_LOSS_LIMIT": f"{daily_loss:.2f}",
                "MAX_OPEN_POSITIONS": str(max_open),
                "ORDER_COOLDOWN_MINUTES": str(cooldown),
                "MIN_EXECUTE_CATEGORY": min_exec,
                "WATCHLIST_THRESHOLD": str(watch_th),
                "ALERT_THRESHOLD": str(alert_th),
                "STRONG_ALERT_THRESHOLD": str(strong_th),
                "PREMIUM_ALERT_THRESHOLD": str(premium_th),
                "MIN_ALERT_CATEGORY": min_alert,
                "ENABLE_SMART_EXIT": str(enable_smart).lower(),
                "ENABLE_BREAK_EVEN": str(enable_be).lower(),
                "BREAK_EVEN_TRIGGER_R": f"{be_trigger:.2f}",
                "BREAK_EVEN_LOCK_R": f"{be_lock:.2f}",
                "ENABLE_TRAILING_STOP": str(enable_trail).lower(),
                "TRAILING_START_R": f"{trail_start:.2f}",
                "TRAILING_DISTANCE_R": f"{trail_dist:.2f}",
                "ENABLE_PARTIAL_CLOSE": str(enable_pc).lower(),
                "PARTIAL_CLOSE_TRIGGER_R": f"{pc_trigger:.2f}",
                "PARTIAL_CLOSE_RATIO": f"{pc_ratio:.2f}",
                "SCAN_INTERVAL_SECONDS": str(int(scan_interval)),
                "SYNC_INTERVAL_SECONDS": str(int(sync_interval)),
                "DRY_RUN": str(dry_run).lower(),
                "ENABLE_EXECUTION": str(enable_exec).lower(),
                "EXECUTION_MODE": exec_mode,
                "SL_ATR_MULTIPLIER": f"{sl_mult:.2f}",
                "TARGET_RR": f"{target_rr:.2f}",
                "ENABLE_PREMIUM_STACK": str(enable_premium_stack).lower(),
                "PREMIUM_STACK_EXTRA_SLOTS": str(int(premium_extra_slots)),
                "ENABLE_ULTRA_STACK": str(enable_ultra_stack).lower(),
                "ULTRA_STACK_SCORE": f"{ultra_score:.0f}",
                "ULTRA_STACK_EXTRA_SLOTS": str(int(ultra_extra_slots)),
            }
            _upsert_env_values(updates)
            db.log_config_change(
                source="streamlit_form",
                summary="save_structured_form",
                changes=updates,
            )
            st.success(t("saved_structured"))
            st.info(t("restart_hint"))
            st.rerun()

    st.markdown(f"### {t('task_manager')}")
    t1, t2 = st.columns(2)
    with t1:
        if st.button(t("install_tasks"), use_container_width=True):
            code, out, err = _run_command(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str((ROOT / "scripts" / "install_windows.ps1"))],
                timeout=600,
            )
            if code == 0:
                db.log_config_change(source="streamlit_task", summary="install_tasks", changes={})
                st.success(out or "installed")
            else:
                st.error(err or out or "install failed")
    with t2:
        if st.button(t("uninstall_tasks"), use_container_width=True):
            code, out, err = _run_command(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", str((ROOT / "scripts" / "uninstall_windows.ps1"))],
                timeout=300,
            )
            if code == 0:
                db.log_config_change(source="streamlit_task", summary="uninstall_tasks", changes={})
                st.success(out or "uninstalled")
            else:
                st.error(err or out or "uninstall failed")

    q1, q2 = st.columns(2)
    with q1:
        exists, msg = _task_query(TASK_DAEMON)
        st.caption(f"{t('task_status')} {t('task_daemon')}: {'OK' if exists else 'N/A'}")
        if st.button(f"{t('task_run')} {t('task_daemon')}", use_container_width=True):
            ok, info = _task_action(TASK_DAEMON, "run")
            (st.success if ok else st.warning)(info)
        if st.button(f"{t('task_stop')} {t('task_daemon')}", use_container_width=True):
            ok, info = _task_action(TASK_DAEMON, "stop")
            (st.success if ok else st.warning)(info)
        with st.expander(f"{t('task_status')} {t('task_daemon')} (raw)"):
            st.text(msg or "-")
    with q2:
        exists, msg = _task_query(TASK_DASHBOARD)
        st.caption(f"{t('task_status')} {t('task_dashboard')}: {'OK' if exists else 'N/A'}")
        if st.button(f"{t('task_run')} {t('task_dashboard')}", use_container_width=True):
            ok, info = _task_action(TASK_DASHBOARD, "run")
            (st.success if ok else st.warning)(info)
        if st.button(f"{t('task_stop')} {t('task_dashboard')}", use_container_width=True):
            ok, info = _task_action(TASK_DASHBOARD, "stop")
            (st.success if ok else st.warning)(info)
        with st.expander(f"{t('task_status')} {t('task_dashboard')} (raw)"):
            st.text(msg or "-")

    st.markdown(f"### {t('config_audit')}")
    audit_rows = db.get_recent_config_audit(limit=50)
    if not audit_rows:
        st.info(t("no_audit"))
    else:
        audit_df = pd.DataFrame([dict(r) for r in audit_rows])
        st.dataframe(audit_df, use_container_width=True, height=240)

    st.markdown(f"### {t('raw_editor')}")
    text = ENV_PATH.read_text(encoding="utf-8")
    updated = st.text_area(t("env_label"), value=text, height=600)
    if st.button(t("save_env"), type="primary"):
        ENV_PATH.write_text(updated, encoding="utf-8")
        db.log_config_change(source="streamlit_raw", summary="save_raw_env", changes={})
        st.success(t("saved"))


def _render_guide() -> None:
    if st.session_state.get("lang", "th") == "th":
        st.markdown(
            """
### คู่มือใช้งานระบบ (SOP)

#### 1) เปิดระบบประจำวัน
```powershell
py main.py --mode reset_loss_guard
py main.py --mode sync
py main.py --mode scan --once
```

#### 2) โหมดใช้งาน
- `scan --once`: สแกน 1 รอบ
- `sync`: ซิงก์สถานะออเดอร์/PnL
- `daemon`: รันต่อเนื่อง

#### 3) ลำดับการใช้งานใน Dashboard
1. ตรวจสถานะเดมอนและบัญชี MT5
2. ปรับค่าในแท็บ `ตั้งค่า` (Configuration Wizard)
3. กด `ซิงก์ออเดอร์` ก่อนเสมอ
4. กด `สแกน 1 รอบ` เพื่อทดสอบ
5. ถ้าปกติค่อย `เริ่มเดมอน`

#### 4) การปรับความเข้มข้น
- เข้าเยอะ: `aggressive`
- สมดุล: `balanced`
- คัดเข้ม: `premium`
- คัดโหด: `ultra_premium`

#### 5) เหตุผลที่มักเจอ
- `below_min_execute_category`: คะแนนยังไม่ถึงขั้นต่ำส่งคำสั่ง
- `cooldown_active`: ยังไม่พ้นเวลาพักของสัญลักษณ์
- `max_open_positions_reached`: จำนวนไม้เปิดเต็ม
- `daily_loss_limit_reached`: ชนเพดานขาดทุนรายวัน
- `symbol_trade_disabled`: โบรกไม่เปิดให้เทรด symbol นี้

#### 6) วิธีแก้เร็วเมื่อไม่เข้าออเดอร์
1. กด `รีเซ็ต Daily Loss Guard (UTC)`
2. กด `ซิงก์ออเดอร์`
3. เช็ก `MIN_EXECUTE_CATEGORY` และ thresholds
4. เช็ก cooldown (`ORDER_COOLDOWN_MINUTES`)

#### 7) คำสั่งตรวจสอบสำคัญ
```powershell
py -m pytest -q
py -m sqlite3 signals.db "SELECT id,timestamp,symbol,status,reason,score,category FROM orders ORDER BY id DESC LIMIT 30;"
```

#### 8) ความปลอดภัย
- แนะนำให้ใช้ `EXECUTION_MODE=demo` จนกว่าจะมั่นใจ
- `score` คือ rule-based confidence ไม่ใช่ win rate
- หลีกเลี่ยงการเพิ่ม risk หลังขาดทุนต่อเนื่อง
            """
        )
    else:
        st.markdown(
            """
### Operations Guide (SOP)

#### 1) Daily startup
```powershell
py main.py --mode reset_loss_guard
py main.py --mode sync
py main.py --mode scan --once
```

#### 2) Main modes
- `scan --once`: run one scan cycle
- `sync`: sync order status/PnL
- `daemon`: run continuously

#### 3) Dashboard workflow
1. Check daemon and MT5 account status
2. Adjust parameters in `Config` tab (Configuration Wizard)
3. Run `Sync` first
4. Run `Scan once` for validation
5. Start daemon for continuous operation

#### 4) Intensity presets
- High frequency: `aggressive`
- Balanced: `balanced`
- Strict: `premium`
- Very strict: `ultra_premium`

#### 5) Common execution reasons
- `below_min_execute_category`
- `cooldown_active`
- `max_open_positions_reached`
- `daily_loss_limit_reached`
- `symbol_trade_disabled`

#### 6) Quick recovery when no new orders
1. Reset Daily Loss Guard
2. Run Sync
3. Verify `MIN_EXECUTE_CATEGORY` and thresholds
4. Verify cooldown settings

#### 7) Useful commands
```powershell
py -m pytest -q
py -m sqlite3 signals.db "SELECT id,timestamp,symbol,status,reason,score,category FROM orders ORDER BY id DESC LIMIT 30;"
```

#### 8) Safety notes
- Keep `EXECUTION_MODE=demo` until stable
- Score is rule-based confidence, not win rate
- Avoid increasing risk during drawdown
            """
        )


def _render_deploy_wizard() -> None:
    st.subheader(t("deploy_title"))
    env = _load_env_map()
    db_path = _load_env_db_path()
    db = SignalDB(str(db_path))

    c1, c2 = st.columns(2)
    with c1:
        machine_name = st.text_input(t("deploy_machine"), value="site-01")
        target_root = st.text_input(t("deploy_target_root"), value="C:\\pytrade")
        include_sensitive = st.checkbox(t("deploy_include_secret"), value=False)
    with c2:
        install_tasks = st.checkbox(t("deploy_install_tasks"), value=True)
        run_sync = st.checkbox(t("deploy_run_sync"), value=True)
        start_daemon = st.checkbox(t("deploy_start_daemon"), value=False)
        start_dashboard = st.checkbox(t("deploy_start_dashboard"), value=False)

    pkg_bytes, pkg_name, preview = _build_deploy_package(
        env=env,
        machine_name=machine_name,
        target_root=target_root,
        include_sensitive=include_sensitive,
        install_tasks=install_tasks,
        run_sync=run_sync,
        start_daemon=start_daemon,
        start_dashboard=start_dashboard,
    )

    st.caption(t("deploy_note"))
    downloaded = st.download_button(
        label=t("deploy_download"),
        data=pkg_bytes,
        file_name=pkg_name,
        mime="application/zip",
        use_container_width=True,
    )

    st.markdown(f"### {t('deploy_preview')}")
    st.code(preview, language="dotenv")

    if downloaded:
        db.log_config_change(
            source="streamlit_deploy",
            summary="download_deploy_package",
            changes={
                "machine_name": machine_name,
                "include_sensitive": str(include_sensitive).lower(),
                "install_tasks": str(install_tasks).lower(),
                "run_sync": str(run_sync).lower(),
                "start_daemon": str(start_daemon).lower(),
                "start_dashboard": str(start_dashboard).lower(),
            },
        )


def main() -> None:
    # Must be the first Streamlit command.
    st.set_page_config(page_title="PyTrade Control Center", layout="wide")

    if "lang" not in st.session_state:
        st.session_state["lang"] = "th"
    st.title(t("title"))

    db_path = _load_env_db_path()
    _render_controls(db_path)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [t("tab_dashboard"), t("tab_portfolio"), t("tab_config"), t("tab_guide"), t("tab_deploy")]
    )
    with tab1:
        _render_dashboard(db_path)
    with tab2:
        _render_portfolio()
    with tab3:
        _render_config_editor()
    with tab4:
        _render_guide()
    with tab5:
        _render_deploy_wizard()


if __name__ == "__main__":
    main()
