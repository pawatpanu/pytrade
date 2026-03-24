from __future__ import annotations

import io
import hmac
import json
import re
import sqlite3
import subprocess
import time
import zipfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from config import CONFIG
from core.logger_db import SignalDB

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
PID_DIR = ROOT / ".runtime"
PID_FILE = PID_DIR / "daemon_pid.json"
TASK_DAEMON = "PyTradeDaemon"
TASK_DASHBOARD = "PyTradeDashboard"
BANGKOK_TZ = "Asia/Bangkok"
USD_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

TXT = {
    "th": {
        "title": "ศูนย์จัดการระบบ",
        "tab_dashboard": "แดชบอร์ด",
        "tab_performance": "ผลงาน",
        "tab_portfolio": "สถานะพอร์ต",
        "tab_health": "สุขภาพระบบ",
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
        "db_fallback": "กำลังแสดงข้อมูลย้อนหลังจากฐานข้อมูลเดิม",
        "scan_once": "สแกน 1 รอบ",
        "sync": "ซิงก์ออเดอร์",
        "start_daemon": "เริ่มเดมอน",
        "stop_daemon": "หยุดเดมอน",
        "language": "ภาษา",
        "auto_refresh": "รีเฟรชอัตโนมัติ",
        "refresh_sec": "ทุกกี่วินาที",
        "refresh_hint": "เมื่อเปิด ระบบจะรีโหลดหน้าเว็บอัตโนมัติทุก N วินาที",
        "refresh_paused": "หน้านี้หยุดรีเฟรชอัตโนมัติชั่วคราว เพื่อให้อ่านข้อมูลได้ต่อเนื่อง",
        "overview": "ภาพรวมการเทรด",
        "open": "ธุรกรรมเปิด",
        "sent": "ส่งแล้ว",
        "closed": "ปิดแล้ว",
        "failed": "ล้มเหลว",
        "today_pnl": "กำไร/ขาดทุน วันนี้",
        "net_pnl_all": "กำไร/ขาดทุนสะสม",
        "cleanup": "ควบคุมข้อมูล",
        "del_below": "ลบ skipped: below_min_execute_category",
        "del_cooldown": "ลบ skipped: cooldown_active",
        "reset_loss_guard": "รีเซ็ต Daily Loss Guard (UTC)",
        "loss_guard_reset_at": "รีเซ็ตล่าสุด (UTC)",
        "loss_guard_effective": "Realized Loss หลังรีเซ็ต",
        "equity": "กราฟ Equity Curve (จากออเดอร์ปิด)",
        "orders": "ธุรกรรมล่าสุด",
        "signals": "สัญญาณล่าสุด",
        "events": "เหตุการณ์สแกนล่าสุด",
        "manual_orders": "ธุรกรรมที่ดำเนินการเอง (ระบบ)",
        "manual_open_positions": "ธุรกรรมเปิดเอง (ยังถืออยู่)",
        "bot_open_positions": "ธุรกรรมระบบที่เปิดอยู่",
        "bot_open_positions_live": "ธุรกรรมระบบที่เปิดอยู่ (ตาม Sync)",
        "bot_open_none": "ไม่มีธุรกรรมระบบที่เปิดอยู่",
        "manual_closed_deals": "ธุรกรรมปิดเองล่าสุด",
        "manual_none_open": "ไม่พบธุรกรรมเปิดเอง",
        "manual_none_closed": "ไม่พบธุรกรรมปิดเองล่าสุด",
        "manual_days": "ดูย้อนหลัง (วัน)",
        "manual_error": "ดึงข้อมูลออเดอร์เปิด/ปิดเองไม่สำเร็จ",
        "sizing_title": "สถานะการคำนวณขนาด",
        "sizing_mode": "โหมดคำนวณ",
        "sizing_last_risk": "Risk ล่าสุด",
        "sizing_last_volume": "ปริมาณล่าสุด",
        "sizing_last_symbol": "สัญลักษณ์ล่าสุด",
        "sizing_dynamic": "Dynamic จาก MT5",
        "sizing_static": "Static จากแผนสัญญาณ",
        "performance_title": "ผลงานทั้งหมด (พร้อมตัวกรอง)",
        "perf_date_range": "ช่วงวันที่",
        "perf_quick_range": "ช่วงเวลาเร็ว",
        "perf_today": "วันนี้",
        "perf_7d": "7 วัน",
        "perf_30d": "30 วัน",
        "perf_all": "ทั้งหมด",
        "perf_symbol": "สัญลักษณ์",
        "perf_status": "สถานะ",
        "perf_direction": "ทิศทาง",
        "perf_reason": "เหตุผล",
        "perf_category": "หมวดสัญญาณ",
        "perf_asset_profile": "Asset Profile",
        "perf_closed_only": "เฉพาะออเดอร์ปิดแล้ว",
        "perf_profile_summary": "สรุปผลงานตามประเภททรัพย์",
        "perf_symbol_summary": "สรุปผลงานตามสัญลักษณ์",
        "perf_rows": "จำนวนรายการ",
        "perf_net_pnl": "กำไร/ขาดทุนสุทธิ",
        "perf_win_rate": "อัตราชนะ",
        "perf_profit_factor": "Profit Factor",
        "perf_avg_pnl": "เฉลี่ยต่อออเดอร์",
        "perf_pnl_curve": "กราฟกำไร/ขาดทุนสะสม",
        "perf_no_data": "ไม่มีข้อมูลตามตัวกรอง",
        "perf_download": "ดาวน์โหลดผลลัพธ์ (CSV)",
        "no_orders": "ยังไม่มีธุรกรรม",
        "no_signals": "ยังไม่มีสัญญาณ",
        "no_events": "ยังไม่มีเหตุการณ์สแกน",
        "no_closed": "ยังไม่มีธุรกรรมที่ปิดพร้อมผลลัพธ์",
        "order_symbol": "สัญลักษณ์ธุรกรรม",
        "order_status": "สถานะธุรกรรม",
        "order_reason": "เหตุผลธุรกรรม",
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
        "account_switcher": "สวิตช์สลับบัญชี MT5",
        "account_mode": "โหมดบัญชีที่ใช้งาน",
        "account_demo": "บัญชี Demo",
        "account_live": "บัญชีจริง",
        "account_login": "MT5_LOGIN",
        "account_password": "MT5_PASSWORD",
        "account_server": "MT5_SERVER",
        "save_account_profiles": "บันทึกชุดบัญชี",
        "apply_account_mode": "สลับบัญชีมาใช้งานทันที",
        "account_saved": "บันทึกชุดบัญชีเรียบร้อย",
        "account_switched": "สลับบัญชีที่ใช้งานเรียบร้อย",
        "account_missing": "ข้อมูลบัญชีโหมดที่เลือกไม่ครบ",
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
        "deploy_release_title": "Release Manager / แพ็กปล่อยใช้งาน",
        "deploy_release_output": "โฟลเดอร์ output",
        "deploy_release_latest": "เวอร์ชันล่าสุด",
        "deploy_release_installer": "Installer ล่าสุด",
        "deploy_release_notes": "Release Notes ล่าสุด",
        "deploy_release_zip": "Release ZIP ล่าสุด",
        "deploy_release_manifest": "Manifest ล่าสุด",
        "deploy_release_none": "ยังไม่พบไฟล์ release ใน installer/output",
        "deploy_release_build_installer": "Build Installer",
        "deploy_release_package": "Package Release",
        "deploy_release_build_all": "Build All",
        "deploy_release_open_output": "เปิดโฟลเดอร์ Output",
        "deploy_release_select_version": "เลือกเวอร์ชันเพื่อติดตั้ง/อัปเดต",
        "deploy_release_refresh": "รีเฟรชข้อมูล release",
        "deploy_release_built": "Build สำเร็จ",
        "deploy_release_packaged": "Package สำเร็จ",
        "deploy_release_failed": "คำสั่ง release ล้มเหลว",
        "deploy_release_download_installer": "ดาวน์โหลด Installer ล่าสุด",
        "deploy_release_download_zip": "ดาวน์โหลด Release ZIP ล่าสุด",
        "deploy_release_download_notes": "ดาวน์โหลด Release Notes ล่าสุด",
        "deploy_release_download_manifest": "ดาวน์โหลด Manifest ล่าสุด",
        "deploy_release_manifest_preview": "ตัวอย่าง Manifest ล่าสุด",
        "health_title": "System Health",
        "health_venv": "Python/Virtual Env",
        "health_env": "ไฟล์ตั้งค่า",
        "health_db": "ฐานข้อมูล",
        "health_pid": "Daemon PID",
        "health_ports": "พอร์ตที่ใช้งาน",
        "health_process": "Process ที่เกี่ยวข้อง",
        "health_logs": "ตัวอย่าง Log ล่าสุด",
        "health_exists": "พร้อมใช้งาน",
        "health_missing": "ไม่พบ",
        "health_running": "กำลังทำงาน",
        "health_not_running": "ไม่ทำงาน",
        "health_open_logs": "เปิด Logs",
        "health_status_check": "เปิด Status Check",
        "health_tail_empty": "ยังไม่มี log",
        "health_self_heal": "Self-Heal / แก้ปัญหาเบื้องต้น",
        "health_clear_stale_pid": "ล้าง stale PID",
        "health_run_sync_now": "ซิงก์ทันที",
        "health_restart_all": "รีสตาร์ททั้งระบบ",
        "health_ok_label": "OK",
        "health_warn_label": "WARN",
        "health_error_label": "ERROR",
        "health_mt5_test": "ทดสอบ MT5",
        "health_mt5_ok": "เชื่อม MT5 สำเร็จ",
        "health_mt5_fail": "เชื่อม MT5 ไม่สำเร็จ",
        "health_mt5_status": "สถานะ MT5 ล่าสุด",
        "health_mt5_ready": "พร้อมใช้งาน",
        "health_mt5_timeout": "ตอบช้า/timeout",
        "health_mt5_error": "ผิดพลาด",
        "health_mt5_retry_note": "ระบบจะ retry สั้นๆ อัตโนมัติและจะไม่ login ซ้ำถ้าบัญชีเดิมยังเชื่อมอยู่",
        "health_import_mt5_history": "นำเข้าประวัติ MT5",
        "health_import_mt5_days": "นำเข้าย้อนหลัง (วัน)",
        "health_import_mt5_done": "นำเข้าประวัติ MT5 เรียบร้อย",
        "health_import_mt5_fail": "นำเข้าประวัติ MT5 ไม่สำเร็จ",
        "dashboard_import_hint": "พบประวัติบอทใน MT5 แต่ฐานข้อมูลบัญชีนี้ยังว่าง",
        "dashboard_import_done": "นำเข้าประวัติจากหน้าแดชบอร์ดเรียบร้อย",
        "health_support_bundle": "ดาวน์โหลด Support Bundle",
        "health_support_preview": "สรุปข้อมูลสำหรับตรวจปัญหา",
        "health_version": "เวอร์ชันระบบ",
        "health_git_branch": "สาขา Git",
        "health_git_commit": "Commit ปัจจุบัน",
        "health_git_commit_time": "เวลา commit ล่าสุด",
        "access_title": "สิทธิ์การใช้งาน",
        "access_mode": "โหมดปัจจุบัน",
        "access_viewer": "ผู้ชม",
        "access_admin": "ผู้ดูแล",
        "access_password": "รหัสผ่านผู้ดูแล",
        "access_unlock": "ปลดล็อกโหมดผู้ดูแล",
        "access_lock": "กลับเป็นโหมดผู้ชม",
        "access_unlock_failed": "รหัสผ่านไม่ถูกต้อง",
        "access_limited_tools": "ลิงก์นี้ดูข้อมูลได้ แต่เมนูแก้ไขระบบ สั่งงาน และปล่อยเวอร์ชันถูกปิดไว้",
        "access_admin_only": "ส่วนนี้เปิดได้เฉพาะผู้ดูแลระบบ",
    },
    "en": {
        "title": "System Manager",
        "tab_dashboard": "Dashboard",
        "tab_performance": "Performance",
        "tab_portfolio": "Portfolio",
        "tab_health": "System Health",
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
        "db_fallback": "Showing historical data from legacy database",
        "scan_once": "Run Scan Once",
        "sync": "Run Sync",
        "start_daemon": "Start Daemon",
        "stop_daemon": "Stop Daemon",
        "language": "Language",
        "auto_refresh": "Auto Refresh",
        "refresh_sec": "Refresh seconds",
        "refresh_hint": "When enabled, this page auto-reloads every N seconds.",
        "refresh_paused": "Auto refresh is paused on this page so you can read without interruption.",
        "overview": "Trading Overview",
        "open": "Open Transactions",
        "sent": "Sent",
        "closed": "Closed",
        "failed": "Failed",
        "today_pnl": "Today PnL",
        "net_pnl_all": "Net PnL",
        "cleanup": "Data Cleanup",
        "del_below": "Delete skipped: below_min_execute_category",
        "del_cooldown": "Delete skipped: cooldown_active",
        "reset_loss_guard": "Reset Daily Loss Guard (UTC)",
        "loss_guard_reset_at": "Last reset (UTC)",
        "loss_guard_effective": "Realized Loss after reset",
        "equity": "Equity Curve (Closed PnL)",
        "orders": "Recent Transactions",
        "signals": "Recent Signals",
        "events": "Recent Scan Events",
        "manual_orders": "Manual Transactions (System)",
        "manual_open_positions": "Manual Open Transactions",
        "bot_open_positions": "System Open Transactions",
        "bot_open_positions_live": "System Open Transactions (Live Sync)",
        "bot_open_none": "No open system transactions",
        "manual_closed_deals": "Recent Manual Closed Transactions",
        "manual_none_open": "No manual open transactions",
        "manual_none_closed": "No recent manual closed transactions",
        "manual_days": "History lookback (days)",
        "manual_error": "Failed to fetch manual order data",
        "sizing_title": "Position Sizing Status",
        "sizing_mode": "Sizing mode",
        "sizing_last_risk": "Last risk amount",
        "sizing_last_volume": "Last lot size",
        "sizing_last_symbol": "Last symbol",
        "sizing_dynamic": "Dynamic from MT5",
        "sizing_static": "Static from signal plan",
        "performance_title": "All Performance (Filterable)",
        "perf_date_range": "Date Range",
        "perf_quick_range": "Quick Range",
        "perf_today": "Today",
        "perf_7d": "7 Days",
        "perf_30d": "30 Days",
        "perf_all": "All",
        "perf_symbol": "Symbol",
        "perf_status": "Status",
        "perf_direction": "Direction",
        "perf_reason": "Reason",
        "perf_category": "Signal Category",
        "perf_asset_profile": "Asset Profile",
        "perf_closed_only": "Closed orders only",
        "perf_profile_summary": "Performance by Asset Profile",
        "perf_symbol_summary": "Performance by Symbol",
        "perf_rows": "Rows",
        "perf_net_pnl": "Net PnL",
        "perf_win_rate": "Win Rate",
        "perf_profit_factor": "Profit Factor",
        "perf_avg_pnl": "Avg PnL / trade",
        "perf_pnl_curve": "Cumulative PnL Curve",
        "perf_no_data": "No data for selected filters",
        "perf_download": "Download filtered results (CSV)",
        "no_orders": "No transactions yet",
        "no_signals": "No signals yet",
        "no_events": "No scan events",
        "no_closed": "No closed transactions with results",
        "order_symbol": "Transaction Symbol",
        "order_status": "Transaction Status",
        "order_reason": "Transaction Reason",
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
        "account_switcher": "MT5 Account Switcher",
        "account_mode": "Active account mode",
        "account_demo": "Demo Account",
        "account_live": "Live Account",
        "account_login": "MT5_LOGIN",
        "account_password": "MT5_PASSWORD",
        "account_server": "MT5_SERVER",
        "save_account_profiles": "Save account profiles",
        "apply_account_mode": "Apply selected account now",
        "account_saved": "Account profiles saved",
        "account_switched": "Active account switched",
        "account_missing": "Selected account profile is incomplete",
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
        "deploy_release_title": "Release Manager",
        "deploy_release_output": "Output folder",
        "deploy_release_latest": "Latest version",
        "deploy_release_installer": "Latest installer",
        "deploy_release_notes": "Latest release notes",
        "deploy_release_zip": "Latest release zip",
        "deploy_release_manifest": "Latest manifest",
        "deploy_release_none": "No release artifacts found in installer/output",
        "deploy_release_build_installer": "Build Installer",
        "deploy_release_package": "Package Release",
        "deploy_release_build_all": "Build All",
        "deploy_release_open_output": "Open Output Folder",
        "deploy_release_select_version": "Select version to install/update",
        "deploy_release_refresh": "Refresh release info",
        "deploy_release_built": "Build completed",
        "deploy_release_packaged": "Packaging completed",
        "deploy_release_failed": "Release command failed",
        "deploy_release_download_installer": "Download latest installer",
        "deploy_release_download_zip": "Download latest release zip",
        "deploy_release_download_notes": "Download latest release notes",
        "deploy_release_download_manifest": "Download latest manifest",
        "deploy_release_manifest_preview": "Latest manifest preview",
        "health_title": "System Health",
        "health_venv": "Python/Virtual Env",
        "health_env": "Config File",
        "health_db": "Database",
        "health_pid": "Daemon PID",
        "health_ports": "Open Ports",
        "health_process": "Relevant Processes",
        "health_logs": "Recent Log Samples",
        "health_exists": "Available",
        "health_missing": "Missing",
        "health_running": "Running",
        "health_not_running": "Not running",
        "health_open_logs": "Open Logs",
        "health_status_check": "Open Status Check",
        "health_tail_empty": "No log content yet",
        "health_self_heal": "Self-Heal",
        "health_clear_stale_pid": "Clear stale PID",
        "health_run_sync_now": "Run Sync Now",
        "health_restart_all": "Restart All",
        "health_ok_label": "OK",
        "health_warn_label": "WARN",
        "health_error_label": "ERROR",
        "health_mt5_test": "Test MT5",
        "health_mt5_ok": "MT5 connection successful",
        "health_mt5_fail": "MT5 connection failed",
        "health_mt5_status": "Latest MT5 status",
        "health_mt5_ready": "Ready",
        "health_mt5_timeout": "Slow response / timeout",
        "health_mt5_error": "Error",
        "health_mt5_retry_note": "The system retries briefly and skips redundant login when the same account is already connected",
        "health_import_mt5_history": "Import MT5 History",
        "health_import_mt5_days": "Import lookback (days)",
        "health_import_mt5_done": "MT5 history imported",
        "health_import_mt5_fail": "Failed to import MT5 history",
        "dashboard_import_hint": "Bot history exists in MT5 but this account database is still empty",
        "dashboard_import_done": "Dashboard import completed",
        "health_support_bundle": "Download Support Bundle",
        "health_support_preview": "Support diagnostics summary",
        "health_version": "System Version",
        "health_git_branch": "Git Branch",
        "health_git_commit": "Current Commit",
        "health_git_commit_time": "Last Commit Time",
        "access_title": "Access",
        "access_mode": "Current mode",
        "access_viewer": "Viewer",
        "access_admin": "Admin",
        "access_password": "Admin password",
        "access_unlock": "Unlock admin mode",
        "access_lock": "Switch back to viewer",
        "access_unlock_failed": "Incorrect password",
        "access_limited_tools": "This link can view data, but config, system control, and release tools are disabled.",
        "access_admin_only": "This section is available to admins only.",
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
        "use_mt5_balance_for_sizing": "ใช้ยอดเงินบัญชี MT5 ปัจจุบันคำนวณขนาดไม้แบบไดนามิก",
        "risk_balance_source": "เลือกใช้ equity (แนะนำ) หรือ balance เป็นฐานคำนวณ lot",
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
        "wick_entry_enabled": "Enable/disable wick rejection entry trigger",
        "risk_per_trade_pct": "Risk per trade as % of account",
        "use_mt5_balance_for_sizing": "Use live MT5 account value for dynamic position sizing",
        "risk_balance_source": "Choose equity (recommended) or balance as lot sizing base",
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


# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

def _setup_page_config() -> None:
    """Configure Streamlit page with modern styling"""
    st.set_page_config(
        page_title="System Manager",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/system-manager",
            "Report a bug": "https://github.com/system-manager/issues",
            "About": "## System Manager v1.0 - Professional Automation Platform",
        }
    )
    
    # Modern CSS styling - Dark Professional Mode
    st.markdown("""
    <style>
    /* Global Styles - Professional Neutral Palette */
    :root {
        --primary-color: #CCCCCC;
        --success-color: #FFFFFF;
        --danger-color: #FF6B6B;
        --warning-color: #FFB266;
        --dark-bg: #0a0e27;
        --card-bg: #1a2332;
        --border-color: #3a3a3a;
    }
    
    /* Main Container */
    .main {
        padding: 0px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a1a 0%, #252525 100%);
        border-right: 2px solid var(--border-color);
    }
    
    /* Header Styling - Professional Dark Mode */
    .header-main {
        background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
        color: #EEEEEE;
        padding: 30px 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(255, 255, 255, 0.05);
        text-align: center;
        border: 2px solid #4a4a4a;
    }
    
    .header-main h1 {
        margin: 0;
        font-size: 2.5em;
        font-weight: 800;
        letter-spacing: 1px;
        color: #FFFFFF;
    }
    
    .header-main p {
        margin: 5px 0 0 0;
        font-size: 0.95em;
        opacity: 0.85;
        color: #CCCCCC;
    }
    
    /* Card Styling - Professional Dark Mode */
    .metric-card {
        background: linear-gradient(135deg, #2a2a2a 0%, #353535 100%);
        border: 2px solid #4a4a4a;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: #6a6a6a;
        box-shadow: 0 6px 20px rgba(255, 255, 255, 0.08);
        transform: translateY(-2px);
    }
    
    .metric-card p,
    .metric-card span,
    .metric-card div {
        color: #DDDDDD !important;
        font-weight: 500;
    }
    
    .metric-label {
        font-size: 0.85em;
        color: #AAAAAA;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        font-weight: 500;
    }
    
    .metric-value {
        font-size: 1.8em;
        font-weight: 700;
        color: #FFFFFF;
    }
    
    .metric-value.positive {
        color: #FFFFFF;
    }
    
    .metric-value.negative {
        color: #FF8888;
    }
    
    /* Tab Styling - Dark Mode */
    [data-baseweb="tab-list"] {
        border-bottom: 2px solid #4a4a4a;
    }
    
    [data-testid="stTab"] {
        border-radius: 8px 8px 0px 0px;
        background: transparent;
    }
    
    [data-testid="stTab"] p {
        font-weight: 700;
        color: #999999 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stTab"]:not([aria-selected="false"]) {
        background: linear-gradient(180deg, rgba(100, 100, 100, 0.2) 0%, rgba(100, 100, 100, 0.1) 100%);
        border-bottom: 3px solid #CCCCCC;
    }
    
    [data-testid="stTab"]:not([aria-selected="false"]) p {
        color: #FFFFFF !important;
        font-weight: 700;
    }
    
    /* Button Styling - Dark Professional */
    .stButton > button {
        background: linear-gradient(135deg, #3a3a3a 0%, #4a4a4a 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #5a5a5a !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        font-size: 0.95em !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        text-transform: uppercase !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #4a4a4a 0%, #5a5a5a 100%) !important;
        box-shadow: 0 6px 20px rgba(255, 255, 255, 0.1) !important;
        transform: translateY(-2px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* All Button Types - Force Dark Mode */
    button {
        background: linear-gradient(135deg, #3a3a3a 0%, #4a4a4a 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #5a5a5a !important;
        font-weight: 700 !important;
    }
    
    button:hover {
        background: linear-gradient(135deg, #4a4a4a 0%, #5a5a5a 100%) !important;
        box-shadow: 0 6px 20px rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Secondary Button */
    button[kind="secondary"] {
        background: linear-gradient(135deg, #4a4a4a 0%, #5a5a5a 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid #6a6a6a !important;
    }
    
    button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #5a5a5a 0%, #6a6a6a 100%) !important;
        box-shadow: 0 6px 20px rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Danger Button - Softer Red */
    button[kind="tertiary"] {
        background: linear-gradient(135deg, #8B4444 0%, #664444 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid #7a5a5a !important;
    }
    
    button[kind="tertiary"]:hover {
        background: linear-gradient(135deg, #9B5454 0%, #774444 100%) !important;
        box-shadow: 0 6px 20px rgba(255, 100, 100, 0.2) !important;
    }
    
    /* Sidebar Text */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: #CCCCCC !important;
    }
    
    [data-testid="stSidebar"] button {
        color: #FFFFFF !important;
    }
    
    /* Data Table Styling */
    .stDataFrame {
        border-collapse: collapse;
    }
    
    .stDataFrame thead {
        background: linear-gradient(90deg, rgba(100, 100, 100, 0.2) 0%, rgba(100, 100, 100, 0.1) 100%);
        border-bottom: 2px solid #6a6a6a;
    }
    
    .stDataFrame thead th {
        color: #FFFFFF !important;
        font-weight: 700;
    }
    
    .stDataFrame tbody td {
        color: #DDDDDD !important;
    }
    
    .stDataFrame tbody tr:hover {
        background-color: rgba(100, 100, 100, 0.1);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background: #2a2a2a;
        border: 2px solid #4a4a4a;
        color: #FFFFFF !important;
        border-radius: 6px;
        padding: 10px 12px;
        font-size: 0.95em;
        font-weight: 500;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stNumberInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #888888 !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #CCCCCC;
        box-shadow: 0 0 10px rgba(200, 200, 200, 0.2);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #353535 0%, #2a2a2a 100%);
        border: 2px solid #4a4a4a;
        border-radius: 8px;
        padding: 15px;
        font-weight: 700;
        color: #CCCCCC !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #6a6a6a;
        background: linear-gradient(135deg, #3a3a3a 0%, #2f2f2f 100%);
        color: #FFFFFF !important;
    }
    
    .streamlit-expanderHeader p {
        color: #CCCCCC !important;
        font-weight: 700;
    }
    
    /* Status Indicators */
    .status-running {
        color: var(--success-color) !important;
        font-weight: 700;
    }
    
    .status-stopped {
        color: var(--danger-color) !important;
        font-weight: 700;
    }
    
    .status-warning {
        color: var(--warning-color) !important;
        font-weight: 700;
    }
    
    /* Caption and Label Text */
    .stCaption {
        color: #AABBCC !important;
        font-weight: 500;
    }
    
    .stSelectboxOption {
        color: #DDDDDD !important;
    }
    
    /* Metric and Number Display */
    .stMetric label {
        color: #CCCCCC !important;
        font-weight: 700;
    }
    
    .stMetric > div > div {
        color: #FFFFFF !important;
        font-weight: 700;
    }
    
    /* Alert Boxes */
    .stSuccess {
        background: linear-gradient(135deg, rgba(100, 255, 100, 0.1) 0%, rgba(80, 200, 80, 0.1) 100%);
        border: 2px solid #88FF88;
        border-radius: 8px;
    }
    
    .stSuccess p {
        color: #CCFFCC !important;
        font-weight: 600;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(255, 100, 100, 0.1) 0%, rgba(220, 50, 50, 0.1) 100%);
        border: 2px solid #FF8888;
        border-radius: 8px;
    }
    
    .stError p {
        color: #FFCCCC !important;
        font-weight: 600;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(255, 180, 100, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%);
        border: 2px solid #FFB266;
        border-radius: 8px;
    }
    
    .stWarning p {
        color: #FFD9B3 !important;
        font-weight: 600;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(150, 150, 150, 0.1) 0%, rgba(120, 120, 120, 0.1) 100%);
        border: 2px solid #CCCCCC;
        border-radius: 8px;
    }
    
    .stInfo p {
        color: #DDDDDD !important;
        font-weight: 600;
    }
    
    /* Form Input Labels */
    .stSelectbox label,
    .stTextInput label,
    .stNumberInput label,
    .stPasswordInput label,
    .stTextArea label,
    .stSlider label,
    .stCheckbox label,
    .stRadio label,
    .stDateInput label,
    .stTimeInput label,
    .stSelectSlider label {
        color: #CCCCCC !important;
        font-weight: 600 !important;
    }
    
    /* Code Block */
    .stCode {
        background: rgba(20, 20, 20, 0.9) !important;
        border: 2px solid #5a5a5a !important;
        border-radius: 8px;
    }
    
    .stCode code {
        color: #CCCCCC !important;
        font-weight: 500;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #CCCCCC 0%, #999999 100%);
    }
    
    /* Column Headers in Dataframe */
    thead th {
        background: linear-gradient(135deg, #4a4a4a 0%, #5a5a5a 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        padding: 12px !important;
        border-color: #6a6a6a !important;
    }
    
    /* Dataframe Rows */
    tbody td {
        color: #DDDDDD !important;
        border-color: #3a3a3a !important;
    }
    
    tbody tr:hover {
        background: rgba(100, 100, 100, 0.2) !important;
    }
    
    /* Divider */
    .stDivider {
        border-color: #4a4a4a;
    }
    
    /* Text and Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    p, span, div {
        color: #DDDDDD !important;
    }
    
    /* Link Styling */
    a {
        color: #FFFFFF !important;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    a:hover {
        color: #FFB800 !important;
        text-decoration: underline;
    }
    
    /* Code Styling */
    code {
        background: #243447;
        border-radius: 4px;
        padding: 2px 6px;
        color: #FFD700;
        font-family: 'Monaco', 'Menlo', monospace;
    }
    
    /* Responsive */
    @media (max-width: 992px) {
        .header-main h1 {
            font-size: 2em;
        }
        
        .metric-card {
            padding: 15px;
        }
    }
    </style>
    """, unsafe_allow_html=True)


_setup_page_config()


def t(key: str) -> str:
    lang = st.session_state.get("lang", "th")
    return TXT.get(lang, TXT["th"]).get(key, key)


def _parse_bool_text(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}




def _safe_calendar_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _normalize_calendar_value(value: str) -> str:
    txt = _safe_calendar_text(value)
    if not txt:
        return "-"
    lowered = txt.lower()
    if lowered in {"na", "n/a", "none", "-"}:
        return "-"
    return txt


def _parse_calendar_datetime_utc(date_text: str, time_text: str, timestamp_text: str = "") -> datetime | None:
    ts = _safe_calendar_text(timestamp_text)
    if ts.isdigit():
        try:
            return datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except Exception:
            pass

    d = _safe_calendar_text(date_text)
    t_raw = _safe_calendar_text(time_text)
    if not d:
        return None

    t_lower = t_raw.lower()
    if not t_raw or t_lower in {"all day", "tentative", ""}:
        return None

    d_formats = ["%m-%d-%Y", "%Y-%m-%d", "%b %d %Y", "%B %d %Y", "%a %b %d %Y", "%A %B %d %Y"]
    t_formats = ["%I:%M%p", "%I%p", "%H:%M"]
    base_date: datetime | None = None

    for dfmt in d_formats:
        try:
            base_date = datetime.strptime(d, dfmt)
            break
        except Exception:
            continue

    if base_date is None:
        return None

    t_compact = t_raw.replace(" ", "").upper()
    for tfmt in t_formats:
        try:
            parsed_time = datetime.strptime(t_compact, tfmt)
            return datetime(
                base_date.year,
                base_date.month,
                base_date.day,
                parsed_time.hour,
                parsed_time.minute,
                tzinfo=timezone.utc,
            )
        except Exception:
            continue

    return None


@st.cache_data(ttl=300)
def _fetch_usd_high_impact_calendar(
    limit: int = 20,
    window_minutes: int = 180,
    strict_red_only: bool = True,
) -> tuple[pd.DataFrame, str | None]:
    req = urllib.request.Request(
        USD_CALENDAR_URL,
        headers={"User-Agent": "pytrade-calendar/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read()
    except Exception as exc:
        return pd.DataFrame(), str(exc)

    try:
        root = ET.fromstring(raw)
    except Exception as exc:
        return pd.DataFrame(), f"xml_parse_error: {exc}"

    window_minutes = max(0, min(1440, int(window_minutes)))
    now_utc = datetime.now(timezone.utc)
    max_utc = now_utc + timedelta(minutes=window_minutes)
    rows: list[dict[str, object]] = []

    for event in root.findall(".//event"):
        fields: dict[str, str] = {}
        for child in list(event):
            fields[child.tag.lower()] = _safe_calendar_text(child.text)

        currency = _safe_calendar_text(fields.get("currency") or fields.get("country"))
        if currency.upper() != "USD":
            continue

        impact_raw = _safe_calendar_text(fields.get("impact") or fields.get("impacttitle") or fields.get("impact_type"))
        impact_lower = impact_raw.lower()
        if strict_red_only and not ("high" in impact_lower or "red" in impact_lower):
            continue

        dt_utc = _parse_calendar_datetime_utc(fields.get("date", ""), fields.get("time", ""), fields.get("timestamp", ""))
        if dt_utc is None or dt_utc < now_utc - timedelta(minutes=5):
            continue
        if dt_utc > max_utc:
            continue

        dt_bkk = dt_utc.astimezone(timezone(timedelta(hours=7)))
        minutes_left = max(0, int((dt_utc - now_utc).total_seconds() // 60))
        rows.append(
            {
                "time_bkk": dt_bkk.strftime("%Y-%m-%d %H:%M"),
                "in_min": minutes_left,
                "event": _safe_calendar_text(fields.get("title") or fields.get("event") or "-") or "-",
                "previous": _normalize_calendar_value(fields.get("previous", "")),
                "forecast": _normalize_calendar_value(fields.get("forecast", "")),
                "actual": _normalize_calendar_value(fields.get("actual", "")),
                "impact": impact_raw or "High",
            }
        )

    if not rows:
        return pd.DataFrame(), None

    df = pd.DataFrame(rows).sort_values(by=["in_min", "time_bkk", "event"], ascending=[True, True, True]).head(max(1, int(limit)))
    return df, None


def _render_usd_red_news_table(env: dict[str, str]) -> None:
    st.markdown("---")
    strict_red_only = _parse_bool_env(env, "USD_CALENDAR_STRICT_RED_ONLY", True)
    window_minutes = max(0, min(1440, _parse_int_env(env, "USD_CALENDAR_WINDOW_MINUTES", 180)))
    mode_text = "Strict Red-Only" if strict_red_only else "All Impacts"
    st.subheader("USD News (Upcoming)")
    st.caption(f"Filter: {mode_text} | Window: 0-{window_minutes} min")

    cal_df, cal_err = _fetch_usd_high_impact_calendar(limit=20, window_minutes=window_minutes, strict_red_only=strict_red_only)
    if cal_err:
        st.caption(f"News calendar unavailable: {cal_err}")

    if cal_df.empty:
        st.info("No USD events found in the configured window.")
        return

    display_cols = ["time_bkk", "in_min", "event", "previous", "forecast", "actual", "impact"]
    label_map = {
        "time_bkk": "Time (Bangkok)",
        "in_min": "In (min)",
        "event": "Event",
        "previous": "Previous",
        "forecast": "Forecast",
        "actual": "Actual",
        "impact": "Impact",
    }
    show_df = cal_df[display_cols].rename(columns=label_map)
    st.dataframe(show_df, use_container_width=True, height=260)

def _init_ui_state_from_query() -> None:
    """Restore UI prefs from URL query params once, then keep session changes."""
    try:
        qp = st.query_params
        if "auto_refresh" not in st.session_state:
            st.session_state["auto_refresh"] = _parse_bool_text(qp.get("ar"), default=True)

        if "refresh_sec" not in st.session_state:
            rs_raw = qp.get("rs")
            rs = int(rs_raw) if rs_raw is not None and str(rs_raw).strip() else 15
            st.session_state["refresh_sec"] = max(5, min(300, rs))

        if "lang" not in st.session_state:
            lang = str(qp.get("lang", "th")).lower()
            st.session_state["lang"] = lang if lang in {"th", "en"} else "th"
        if "active_tab" not in st.session_state:
            st.session_state["active_tab"] = str(qp.get("tab", "dashboard"))
    except Exception:
        if "auto_refresh" not in st.session_state:
            st.session_state["auto_refresh"] = True
        if "refresh_sec" not in st.session_state:
            st.session_state["refresh_sec"] = 15
        if "active_tab" not in st.session_state:
            st.session_state["active_tab"] = "dashboard"


def _persist_ui_state_to_query() -> None:
    try:
        st.query_params["ar"] = "1" if bool(st.session_state.get("auto_refresh", False)) else "0"
        st.query_params["rs"] = str(int(st.session_state.get("refresh_sec", 15)))
        st.query_params["lang"] = str(st.session_state.get("lang", "th"))
        st.query_params["tab"] = str(st.session_state.get("active_tab", "dashboard"))
    except Exception:
        pass


def _add_thai_time_columns(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Add Bangkok time columns from ISO/UTC timestamp columns."""
    if df.empty:
        return df
    out = df.copy()
    for source_col, target_col in mapping.items():
        if source_col not in out.columns:
            continue
        parsed = pd.to_datetime(out[source_col], utc=True, errors="coerce")
        out[target_col] = parsed.dt.tz_convert(BANGKOK_TZ).dt.strftime("%Y-%m-%d %H:%M:%S")
    return out


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
        "wick_entry_enabled": "WICK_ENTRY_ENABLED",
        "risk_per_trade_pct": "RISK_PER_TRADE_PCT",
        "use_mt5_balance_for_sizing": "USE_MT5_BALANCE_FOR_SIZING",
        "risk_balance_source": "RISK_BALANCE_SOURCE",
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


def _app_admin_password(env: dict[str, str]) -> str:
    return str(env.get("APP_ADMIN_PASSWORD", "")).strip()


def _app_default_role(env: dict[str, str]) -> str:
    raw = str(env.get("APP_DEFAULT_ROLE", "")).strip().lower()
    if raw in {"viewer", "admin"}:
        return raw
    return "viewer" if _app_admin_password(env) else "admin"


def _is_admin() -> bool:
    return str(st.session_state.get("access_role", "viewer")) == "admin"


def _ensure_access_session(env: dict[str, str]) -> None:
    if "access_role" not in st.session_state:
        st.session_state["access_role"] = _app_default_role(env)
    if not _app_admin_password(env):
        st.session_state["access_role"] = "admin"


def _render_access_controls(env: dict[str, str]) -> None:
    st.sidebar.markdown(f"### {t('access_title')}")
    is_admin = _is_admin()
    mode_label = t("access_admin") if is_admin else t("access_viewer")
    st.sidebar.caption(f"{t('access_mode')}: **{mode_label}**")

    admin_password = _app_admin_password(env)
    if not admin_password:
        return

    if is_admin:
        if st.sidebar.button(t("access_lock"), width="stretch"):
            st.session_state["access_role"] = "viewer"
            st.rerun()
        return

    entered = st.sidebar.text_input(t("access_password"), type="password", key="access_password_input")
    if st.sidebar.button(t("access_unlock"), width="stretch"):
        if hmac.compare_digest(entered, admin_password):
            st.session_state["access_role"] = "admin"
            st.rerun()
        else:
            st.sidebar.error(t("access_unlock_failed"))


def _asset_profile_name(symbol: str) -> str:
    return CONFIG.asset_profile_name(str(symbol or ""))


def _mt5_direction_label(raw_type: object) -> str:
    try:
        value = int(raw_type)
    except (ValueError, TypeError):
        return str(raw_type or "")
    if value == 0:
        return "BUY"
    if value in (1, -1):
        return "SELL"
    return str(value)


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


def _mt5_initialize_and_login(
    env: dict[str, str],
    *,
    retries: int = 3,
    delay_seconds: float = 0.75,
) -> tuple[object | None, str | None]:
    try:
        import MetaTrader5 as mt5
    except Exception as exc:
        return None, str(exc)

    kwargs = {}
    if env.get("MT5_PATH"):
        kwargs["path"] = env["MT5_PATH"]

    last_error = "initialize_failed"
    for attempt in range(max(1, retries)):
        if mt5.initialize(**kwargs):
            break
        code, msg = mt5.last_error()
        last_error = f"{code} {msg}"
        if attempt < retries - 1:
            time.sleep(delay_seconds * (attempt + 1))
    else:
        return None, last_error

    try:
        login = env.get("MT5_LOGIN")
        password = env.get("MT5_PASSWORD")
        server = env.get("MT5_SERVER")
        if login and password and server:
            target_login = int(login)
            account = mt5.account_info()
            current_login = int(getattr(account, "login", 0) or 0) if account else 0
            if current_login != target_login:
                ok = mt5.login(login=target_login, password=password, server=server)
                if not ok:
                    code, msg = mt5.last_error()
                    mt5.shutdown()
                    return None, f"{code} {msg}"
        return mt5, None
    except Exception as exc:
        try:
            mt5.shutdown()
        except Exception:
            pass
        return None, str(exc)


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


def _account_db_path(mode: str, login: str) -> str:
    safe_mode = _sanitize_name(mode or "account", "account")
    safe_login = _sanitize_name(login or "default", "default")
    return f"signals_{safe_mode}_{safe_login}.db"


def _build_deploy_profile_lines(env: dict[str, str], include_sensitive: bool) -> list[str]:
    keys = list(DEPLOY_BASE_KEYS)
    if include_sensitive:
        keys += DEPLOY_SENSITIVE_KEYS
    lines = ["# Generated by System Manager Deploy Wizard", f"# UTC: {datetime.now(timezone.utc).isoformat()}"]
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

    readme_text = f"""System Manager Deploy Package
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

    file_name = f"system_manager_deploy_{safe_machine}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return mem.getvalue(), file_name, profile_text


def _load_env_db_path() -> Path:
    env = _load_env_map()
    return (ROOT / env.get("DB_PATH", "signals.db")).resolve()


def _db_orders_count(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    try:
        with _db_connect(db_path) as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM orders").fetchone()
            return int(row["c"] or 0) if row else 0
    except sqlite3.Error:
        return 0


def _resolve_display_db_path(configured_db_path: Path) -> tuple[Path, bool]:
    """Return the best DB for read-only dashboard display, with legacy fallback."""
    if _db_orders_count(configured_db_path) > 0:
        return configured_db_path, False
    legacy_db = (ROOT / "signals.db").resolve()
    if legacy_db != configured_db_path and _db_orders_count(legacy_db) > 0:
        return legacy_db, True
    return configured_db_path, False


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


def _run_batch_file(path: Path, detached: bool = False) -> tuple[bool, str]:
    if not path.exists():
        return False, f"Launcher not found: {path}"

    creationflags = 0
    if detached:
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)

    try:
        if detached:
            subprocess.Popen(
                ["cmd.exe", "/c", str(path)],
                cwd=str(ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                shell=False,
            )
            return True, f"Started launcher: {path.name}"

        proc = subprocess.run(["cmd.exe", "/c", str(path)], cwd=str(ROOT), capture_output=True, text=True, timeout=300, shell=False)
        msg = proc.stdout.strip() or proc.stderr.strip() or path.name
        return proc.returncode == 0, msg
    except Exception as exc:
        return False, str(exc)


def _tail_text(path: Path, lines: int = 20) -> str:
    if not path.exists():
        return t("health_tail_empty")
    try:
        content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        tail = content[-max(1, lines) :]
        return "\n".join(tail) if tail else t("health_tail_empty")
    except Exception as exc:
        return str(exc)


def _port_snapshot(ports: list[int]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for port in ports:
        code, out, err = _run_command(["netstat", "-ano"])
        text = out if code == 0 else (err or "")
        matches = [line.strip() for line in text.splitlines() if f":{port} " in line]
        if matches:
            for line in matches:
                rows.append({"port": str(port), "status": t("health_running"), "details": line})
        else:
            rows.append({"port": str(port), "status": t("health_not_running"), "details": ""})
    return pd.DataFrame(rows)


def _process_snapshot() -> pd.DataFrame:
    code, out, err = _run_command(["tasklist"])
    text = out if code == 0 else (err or "")
    keep = ("python.exe", "py.exe", "streamlit.exe", "terminal64.exe")
    rows = []
    for line in text.splitlines():
        if any(k.lower() in line.lower() for k in keep):
            rows.append({"process": line})
    return pd.DataFrame(rows)


def _status_badge(label: str, level: str) -> str:
    color_map = {
        "ok": "#16a34a",
        "warn": "#ca8a04",
        "error": "#dc2626",
    }
    bg_map = {
        "ok": "rgba(22,163,74,0.12)",
        "warn": "rgba(202,138,4,0.12)",
        "error": "rgba(220,38,38,0.12)",
    }
    color = color_map.get(level, "#94a3b8")
    bg = bg_map.get(level, "rgba(148,163,184,0.12)")
    return (
        f"<span style='display:inline-block;padding:4px 10px;border-radius:999px;"
        f"background:{bg};border:1px solid {color};color:{color};font-weight:600'>{label}</span>"
    )


def _masked_env(env: dict[str, str]) -> dict[str, str]:
    masked = dict(env)
    secret_keys = {
        "MT5_PASSWORD",
        "MT5_PASSWORD_DEMO",
        "MT5_PASSWORD_LIVE",
        "TELEGRAM_TOKEN",
        "LINE_TOKEN",
    }
    for key in list(masked.keys()):
        if key in secret_keys:
            masked[key] = "***MASKED***"
    return masked


def _test_mt5_connection(env: dict[str, str]) -> tuple[bool, dict[str, object]]:
    mt5, error = _mt5_initialize_and_login(env)
    if mt5 is None:
        return False, {"error": error or "mt5_unavailable"}

    try:
        account = mt5.account_info()
        if not account:
            return True, {"login": env.get("MT5_LOGIN", "-"), "server": env.get("MT5_SERVER", "-")}
        return True, {
            "login": int(getattr(account, "login", 0) or 0),
            "server": env.get("MT5_SERVER", "-"),
            "balance": float(getattr(account, "balance", 0.0) or 0.0),
            "equity": float(getattr(account, "equity", 0.0) or 0.0),
            "profit": float(getattr(account, "profit", 0.0) or 0.0),
        }
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def _mt5_health_badge(env: dict[str, str]) -> tuple[str, str, str]:
    ok, payload = _test_mt5_connection(env)
    if ok:
        login = payload.get("login", "-")
        server = payload.get("server", "-")
        return "ok", t("health_mt5_ready"), f"login={login} | server={server}"

    error = str(payload.get("error", "") or "")
    if "10005" in error or "timeout" in error.lower():
        return "warn", t("health_mt5_timeout"), error
    return "error", t("health_mt5_error"), error or "unknown error"


def _build_support_bundle(env: dict[str, str], db_path: Path) -> tuple[bytes, str, dict[str, object]]:
    masked_env = _masked_env(env)
    pid_info = _read_pid_info() or {}
    daemon_pid = int(pid_info.get("pid", 0) or 0)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "db_path": str(db_path),
        "db_exists": db_path.exists(),
        "env_exists": ENV_PATH.exists(),
        "venv_exists": (ROOT / ".venv" / "Scripts" / "python.exe").exists(),
        "daemon_pid": daemon_pid,
        "daemon_running": daemon_pid > 0 and _is_pid_running(daemon_pid),
    }
    ports_df = _port_snapshot([8501, 8502])
    proc_df = _process_snapshot()

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("summary.json", json.dumps(summary, ensure_ascii=False, indent=2).encode("utf-8"))
        zf.writestr("env_masked.json", json.dumps(masked_env, ensure_ascii=False, indent=2).encode("utf-8"))
        zf.writestr("pid_info.json", json.dumps(pid_info, ensure_ascii=False, indent=2).encode("utf-8"))
        zf.writestr("ports.csv", ports_df.to_csv(index=False).encode("utf-8"))
        zf.writestr("processes.csv", proc_df.to_csv(index=False).encode("utf-8"))
        zf.writestr("daemon_tail.log", _tail_text(ROOT / "logs" / "daemon.log", lines=50).encode("utf-8"))
        zf.writestr("dashboard_tail.log", _tail_text(ROOT / "logs" / "dashboard.log", lines=50).encode("utf-8"))

    file_name = f"system_manager_support_bundle_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return mem.getvalue(), file_name, summary


def _git_version_info() -> dict[str, str]:
    branch = "-"
    commit = "-"
    commit_time = "-"
    try:
        code, out, _ = _run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=20)
        if code == 0 and out:
            branch = out.strip()
    except Exception:
        pass
    try:
        code, out, _ = _run_command(["git", "rev-parse", "--short", "HEAD"], timeout=20)
        if code == 0 and out:
            commit = out.strip()
    except Exception:
        pass
    try:
        code, out, _ = _run_command(["git", "log", "-1", "--format=%cI"], timeout=20)
        if code == 0 and out:
            commit_time = out.strip()
    except Exception:
        pass
    return {
        "branch": branch,
        "commit": commit,
        "commit_time": commit_time,
    }


def _release_output_dir() -> Path:
    return ROOT / "installer" / "output"


def _latest_release_artifacts() -> dict[str, object]:
    output_dir = _release_output_dir()
    result: dict[str, object] = {
        "output_dir": output_dir,
        "version": "-",
        "installer": None,
        "release_notes": None,
        "release_zip": None,
        "manifest": None,
    }
    if not output_dir.exists():
        return result

    installer = next(iter(sorted(output_dir.glob("PyTradeSetup-*.exe"), key=lambda p: p.stat().st_mtime, reverse=True)), None)
    release_notes = next(iter(sorted(output_dir.glob("RELEASE-NOTES-*.md"), key=lambda p: p.stat().st_mtime, reverse=True)), None)
    release_zip = next(iter(sorted(output_dir.glob("PyTrade-Release-*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)), None)

    manifest_path = output_dir / "release_manifest.json"
    if not manifest_path.exists() and release_zip:
        manifest_name = release_zip.stem.replace("PyTrade-Release-", "")
        candidate = output_dir / f"release_manifest_{manifest_name}.json"
        if candidate.exists():
            manifest_path = candidate

    version = "-"
    if installer:
        version = installer.stem.replace("PyTradeSetup-", "")
    elif release_zip:
        version = release_zip.stem.replace("PyTrade-Release-", "")

    result.update(
        {
            "version": version,
            "installer": installer,
            "release_notes": release_notes,
            "release_zip": release_zip,
            "manifest": manifest_path if manifest_path.exists() else None,
        }
    )
    return result


def _run_powershell_script(path: Path, timeout: int = 900) -> tuple[int, str, str]:
    return _run_command(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(path)], timeout=timeout)


def _project_python() -> str:
    venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return "py"


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
    py_exec = _project_python()
    PID_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(
        json.dumps(
            {
                "pid": pid,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "cmd": f"\"{py_exec}\" main.py --mode daemon",
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
    py_exec = _project_python()
    proc = subprocess.Popen(
        [py_exec, "main.py", "--mode", "daemon"],
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


def _metrics(db_path: Path, live_open_count: int | None = None) -> dict[str, float]:
    if not db_path.exists():
        open_count = int(live_open_count or 0)
        return {"open": open_count, "sent": open_count, "closed": 0, "failed": 0, "today_pnl": 0.0, "net_pnl_all": 0.0}
    df = _query_df(
        db_path,
        """
        SELECT
          SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent_count,
          SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed_count,
          SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed_count,
          COALESCE(SUM(CASE WHEN status='closed' THEN pnl ELSE 0 END), 0) AS net_pnl_all,
          COALESCE(
            SUM(
              CASE
                WHEN status='closed'
                  AND date(datetime(replace(substr(closed_at,1,19),'T',' '), '+7 hours')) = date(datetime('now', '+7 hours'))
                THEN pnl ELSE 0
              END
            ),
            0
          ) AS today_pnl
        FROM orders
        """,
    )
    if df.empty:
        open_count = int(live_open_count or 0)
        return {"open": open_count, "sent": open_count, "closed": 0, "failed": 0, "today_pnl": 0.0, "net_pnl_all": 0.0}
    r = df.iloc[0]
    sent_count = int(r.get("sent_count", 0) or 0)
    open_count = int(live_open_count) if live_open_count is not None else sent_count
    return {
        "open": open_count,
        "sent": sent_count,
        "closed": int(r.get("closed_count", 0) or 0),
        "failed": int(r.get("failed_count", 0) or 0),
        "today_pnl": float(r.get("today_pnl", 0.0) or 0.0),
        "net_pnl_all": float(r.get("net_pnl_all", 0.0) or 0.0),
    }


def _fetch_manual_mt5_activity(env: dict[str, str], lookback_days: int = 7, limit: int = 200) -> tuple[pd.DataFrame, pd.DataFrame, str | None]:
    """Fetch manual open positions and closed deals directly from MT5."""
    mt5, error = _mt5_initialize_and_login(env)
    if mt5 is None:
        return pd.DataFrame(), pd.DataFrame(), error or "mt5_unavailable"

    try:
        bot_magic = _parse_int_env(env, "MAGIC_NUMBER", 20260312)

        positions = mt5.positions_get() or []
        open_rows: list[dict[str, object]] = []
        for p in positions:
            magic = int(getattr(p, "magic", 0) or 0)
            if magic == bot_magic:
                continue
            direction = _mt5_direction_label(getattr(p, "type", -1))
            open_rows.append(
                {
                    "ticket": int(getattr(p, "ticket", 0) or 0),
                    "position_id": int(getattr(p, "identifier", 0) or 0),
                    "symbol": str(getattr(p, "symbol", "")),
                    "direction": direction,
                    "volume": float(getattr(p, "volume", 0.0) or 0.0),
                    "price_open": float(getattr(p, "price_open", 0.0) or 0.0),
                    "price_now": float(getattr(p, "price_current", 0.0) or 0.0),
                    "profit": float(getattr(p, "profit", 0.0) or 0.0),
                    "magic": magic,
                    "comment": str(getattr(p, "comment", "")),
                    "timestamp": datetime.fromtimestamp(int(getattr(p, "time", 0) or 0), timezone.utc).isoformat(),
                }
            )
        open_df = _add_thai_time_columns(pd.DataFrame(open_rows), {"timestamp": "timestamp_th"})

        time_to = datetime.now(timezone.utc)
        time_from = time_to - timedelta(days=max(1, lookback_days))
        deals = mt5.history_deals_get(time_from, time_to) or []
        closed_rows: list[dict[str, object]] = []
        for d in deals:
            magic = int(getattr(d, "magic", 0) or 0)
            if magic == bot_magic:
                continue
            entry = int(getattr(d, "entry", -1) or -1)
            if entry not in (1, 3):
                continue
            direction = _mt5_direction_label(getattr(d, "type", -1))
            closed_rows.append(
                {
                    "deal": int(getattr(d, "ticket", 0) or 0),
                    "position_id": int(getattr(d, "position_id", 0) or 0),
                    "symbol": str(getattr(d, "symbol", "")),
                    "direction": direction,
                    "volume": float(getattr(d, "volume", 0.0) or 0.0),
                    "price": float(getattr(d, "price", 0.0) or 0.0),
                    "profit": float(getattr(d, "profit", 0.0) or 0.0),
                    "commission": float(getattr(d, "commission", 0.0) or 0.0),
                    "swap": float(getattr(d, "swap", 0.0) or 0.0),
                    "magic": magic,
                    "comment": str(getattr(d, "comment", "")),
                    "timestamp": datetime.fromtimestamp(int(getattr(d, "time", 0) or 0), timezone.utc).isoformat(),
                }
            )
        closed_df = pd.DataFrame(closed_rows)
        if not closed_df.empty:
            closed_df = closed_df.sort_values("deal", ascending=False).head(max(1, limit))
        closed_df = _add_thai_time_columns(closed_df, {"timestamp": "timestamp_th"})
        return open_df, closed_df, None
    except Exception as exc:
        return pd.DataFrame(), pd.DataFrame(), str(exc)
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def _fetch_bot_mt5_positions(env: dict[str, str], limit: int = 50) -> tuple[pd.DataFrame, str | None]:
    """Fetch live open positions for this bot directly from MT5 using MAGIC_NUMBER."""
    mt5, error = _mt5_initialize_and_login(env)
    if mt5 is None:
        return pd.DataFrame(), error or "mt5_unavailable"

    try:
        bot_magic = _parse_int_env(env, "MAGIC_NUMBER", 20260312)
        positions = mt5.positions_get() or []
        rows: list[dict[str, object]] = []
        for p in positions:
            magic = int(getattr(p, "magic", 0) or 0)
            if magic != bot_magic:
                continue
            direction = _mt5_direction_label(getattr(p, "type", -1))
            rows.append(
                {
                    "ticket": int(getattr(p, "ticket", 0) or 0),
                    "position_id": int(getattr(p, "identifier", 0) or 0),
                    "symbol": str(getattr(p, "symbol", "")),
                    "direction": direction,
                    "volume": float(getattr(p, "volume", 0.0) or 0.0),
                    "price_open": float(getattr(p, "price_open", 0.0) or 0.0),
                    "price_now": float(getattr(p, "price_current", 0.0) or 0.0),
                    "sl": float(getattr(p, "sl", 0.0) or 0.0),
                    "tp": float(getattr(p, "tp", 0.0) or 0.0),
                    "profit": float(getattr(p, "profit", 0.0) or 0.0),
                    "magic": magic,
                    "comment": str(getattr(p, "comment", "")),
                    "timestamp": datetime.fromtimestamp(int(getattr(p, "time", 0) or 0), timezone.utc).isoformat(),
                }
            )

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("ticket", ascending=False).head(max(1, limit))
        df = _add_thai_time_columns(df, {"timestamp": "timestamp_th"})
        return df, None
    except Exception as exc:
        return pd.DataFrame(), str(exc)
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def _order_exists(db_path: Path, *, mt5_position: int | None = None, mt5_order: int | None = None, status: str | None = None) -> bool:
    if not db_path.exists():
        return False
    clauses: list[str] = []
    params: list[object] = []
    if mt5_position and mt5_position > 0:
        clauses.append("mt5_position = ?")
        params.append(int(mt5_position))
    if mt5_order and mt5_order > 0:
        clauses.append("mt5_order = ?")
        params.append(int(mt5_order))
    if not clauses:
        return False
    sql = f"SELECT 1 FROM orders WHERE ({' OR '.join(clauses)})"
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " LIMIT 1"
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(sql, params).fetchone()
    return row is not None


def _import_mt5_history_to_db(
    env: dict[str, str],
    db_path: Path,
    *,
    lookback_days: int = 30,
) -> tuple[dict[str, int], str | None]:
    db = SignalDB(str(db_path))
    mt5, error = _mt5_initialize_and_login(env)
    if mt5 is None:
        return {}, error or "mt5_unavailable"

    stats = {"open_imported": 0, "closed_imported": 0, "skipped": 0}
    try:
        bot_magic = _parse_int_env(env, "MAGIC_NUMBER", 20260312)

        positions = mt5.positions_get() or []
        for p in positions:
            magic = int(getattr(p, "magic", 0) or 0)
            if magic != bot_magic:
                continue
            ticket = int(getattr(p, "ticket", 0) or 0)
            if _order_exists(db_path, mt5_position=ticket, mt5_order=ticket):
                stats["skipped"] += 1
                continue
            direction = _mt5_direction_label(getattr(p, "type", -1))
            opened_at = datetime.fromtimestamp(int(getattr(p, "time", 0) or 0), timezone.utc).isoformat()
            db.log_order(
                timestamp=opened_at,
                symbol=str(getattr(p, "symbol", "")),
                normalized_symbol=str(getattr(p, "symbol", "")),
                direction=direction,
                category="imported",
                score=0.0,
                entry_price=float(getattr(p, "price_open", 0.0) or 0.0),
                stop_loss=float(getattr(p, "sl", 0.0) or 0.0) or None,
                take_profit=float(getattr(p, "tp", 0.0) or 0.0) or None,
                volume=float(getattr(p, "volume", 0.0) or 0.0) or None,
                risk_amount=None,
                status="sent",
                reason="imported_open",
                mt5_order=ticket,
                mt5_position=ticket,
                comment="imported_from_mt5_open",
            )
            stats["open_imported"] += 1

        time_to = datetime.now(timezone.utc)
        time_from = time_to - timedelta(days=max(1, lookback_days))
        deals = mt5.history_deals_get(time_from, time_to) or []
        grouped: dict[int, list[object]] = {}
        for d in deals:
            magic = int(getattr(d, "magic", 0) or 0)
            if magic != bot_magic:
                continue
            position_id = int(getattr(d, "position_id", 0) or 0)
            if position_id <= 0:
                continue
            grouped.setdefault(position_id, []).append(d)

        for position_id, group in grouped.items():
            if _order_exists(db_path, mt5_position=position_id, status="closed"):
                stats["skipped"] += 1
                continue
            in_deals: list[object] = []
            out_deals: list[object] = []
            for d in group:
                entry = int(getattr(d, "entry", -1) or -1)
                d_type = int(getattr(d, "type", -1) or -1)
                profit = float(getattr(d, "profit", 0.0) or 0.0)
                # Exness can expose opening deals as entry=-1 with BUY/SELL type.
                if entry == 0 or (entry == -1 and d_type in (0, 1)):
                    in_deals.append(d)
                elif entry in (1, 3) or d_type not in (0, 1) or abs(profit) > 1e-12:
                    out_deals.append(d)
            if not in_deals or not out_deals:
                stats["skipped"] += 1
                continue

            in_deals.sort(key=lambda d: int(getattr(d, "time", 0) or 0))
            out_deals.sort(key=lambda d: int(getattr(d, "time", 0) or 0))
            first_in = in_deals[0]
            last_out = out_deals[-1]
            direction = _mt5_direction_label(getattr(first_in, "type", -1))
            opened_at = datetime.fromtimestamp(int(getattr(first_in, "time", 0) or 0), timezone.utc).isoformat()
            closed_at = datetime.fromtimestamp(int(getattr(last_out, "time", 0) or 0), timezone.utc).isoformat()
            total_pnl = sum(
                float(getattr(d, "profit", 0.0) or 0.0)
                + float(getattr(d, "commission", 0.0) or 0.0)
                + float(getattr(d, "swap", 0.0) or 0.0)
                for d in out_deals
            )
            db.log_order(
                timestamp=opened_at,
                symbol=str(getattr(first_in, "symbol", "")),
                normalized_symbol=str(getattr(first_in, "symbol", "")),
                direction=direction,
                category="imported",
                score=0.0,
                entry_price=float(getattr(first_in, "price", 0.0) or 0.0),
                stop_loss=None,
                take_profit=None,
                volume=float(getattr(first_in, "volume", 0.0) or 0.0) or None,
                risk_amount=None,
                status="closed",
                reason="imported_history",
                mt5_order=int(getattr(last_out, "order", 0) or 0) or position_id,
                mt5_position=position_id,
                comment="imported_from_mt5_history",
                pnl=round(total_pnl, 2),
                closed_at=closed_at,
            )
            stats["closed_imported"] += 1

        return stats, None
    except Exception as exc:
        return stats, str(exc)
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def _mt5_bot_activity_summary(env: dict[str, str], *, lookback_days: int = 30) -> tuple[dict[str, int], str | None]:
    mt5, error = _mt5_initialize_and_login(env)
    if mt5 is None:
        return {}, error or "mt5_unavailable"
    try:
        bot_magic = _parse_int_env(env, "MAGIC_NUMBER", 20260312)
        open_positions = [p for p in (mt5.positions_get() or []) if int(getattr(p, "magic", 0) or 0) == bot_magic]
        time_to = datetime.now(timezone.utc)
        time_from = time_to - timedelta(days=max(1, lookback_days))
        deals = mt5.history_deals_get(time_from, time_to) or []
        closed_positions = {
            int(getattr(d, "position_id", 0) or 0)
            for d in deals
            if int(getattr(d, "magic", 0) or 0) == bot_magic and int(getattr(d, "entry", -1) or -1) in (1, 3)
        }
        return {"open": len(open_positions), "closed": len([x for x in closed_positions if x > 0])}, None
    except Exception as exc:
        return {}, str(exc)
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def _render_controls(db_path: Path, is_admin: bool) -> None:
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
    st.sidebar.checkbox(t("auto_refresh"), key="auto_refresh")
    st.sidebar.number_input(t("refresh_sec"), min_value=5, max_value=300, step=5, key="refresh_sec")
    st.sidebar.caption(t("refresh_hint"))
    _render_access_controls(env)
    _persist_ui_state_to_query()

    refreshable_tabs = {"dashboard", "portfolio", "health"}
    active_tab = str(st.session_state.get("active_tab", "dashboard"))
    if st.session_state.get("auto_refresh") and active_tab in refreshable_tabs:
        sec = int(st.session_state.get("refresh_sec", 15))
        if st_autorefresh is not None:
            st_autorefresh(interval=sec * 1000, key="pytrade_soft_refresh")
        else:
            st.caption("Tip: install `streamlit-autorefresh` for smoother refresh without full page reload.")
            st.markdown(f"<meta http-equiv='refresh' content='{sec}'>", unsafe_allow_html=True)
    elif st.session_state.get("auto_refresh") and active_tab not in refreshable_tabs:
        st.sidebar.caption(t("refresh_paused"))

    if is_admin:
        if st.sidebar.button(t("scan_once"), width="stretch"):
            with st.sidebar.status("...", expanded=True) as status:
                code, out, err = _run_command([_project_python(), "main.py", "--mode", "scan", "--once"], timeout=600)
                status.write(out or "(no stdout)")
                if err:
                    status.write(err)
                status.update(label=f"Done (code={code})", state="complete")

        if st.sidebar.button(t("sync"), width="stretch"):
            with st.sidebar.status("...", expanded=True) as status:
                code, out, err = _run_command([_project_python(), "main.py", "--mode", "sync"], timeout=300)
                status.write(out or "(no stdout)")
                if err:
                    status.write(err)
                status.update(label=f"Done (code={code})", state="complete")

        c1, c2 = st.sidebar.columns(2)
        with c1:
            if st.button(t("start_daemon"), width="stretch"):
                ok, msg = _start_daemon()
                (st.success if ok else st.warning)(msg)
        with c2:
            if st.button(t("stop_daemon"), width="stretch"):
                ok, msg = _stop_daemon()
                (st.success if ok else st.warning)(msg)

        st.sidebar.caption("Quick Launchers")
        q1, q2 = st.sidebar.columns(2)
        with q1:
            if st.button("Start All", width="stretch"):
                ok, msg = _run_batch_file(ROOT / "Start-All.bat", detached=True)
                (st.success if ok else st.warning)(msg)
        with q2:
            if st.button("Stop All", width="stretch"):
                ok, msg = _run_batch_file(ROOT / "Stop-All.bat")
                (st.success if ok else st.warning)(msg)

        q3, q4 = st.sidebar.columns(2)
        with q3:
            if st.button("Restart All", width="stretch"):
                ok, msg = _run_batch_file(ROOT / "Restart-All.bat", detached=True)
                (st.success if ok else st.warning)(msg)
        with q4:
            if st.button("Open Logs", width="stretch"):
                ok, msg = _run_batch_file(ROOT / "Open-Logs.bat", detached=True)
                (st.success if ok else st.warning)(msg)

        if st.sidebar.button("Status Check", width="stretch"):
            ok, msg = _run_batch_file(ROOT / "Status-Check.bat", detached=True)
            (st.success if ok else st.warning)(msg)
    else:
        st.sidebar.info(t("access_limited_tools"))


def _render_dashboard(db_path: Path, is_admin: bool) -> None:
    """Render main trading dashboard with modern UI"""
    st.subheader("📊 " + t("overview"))
    
    env = _load_env_map()
    bot_open_df, bot_open_err = _fetch_bot_mt5_positions(env, limit=20)
    
    # Status bar with current configuration
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a2332 0%, #243447 100%);
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;">
        <p style="margin: 0; color: #888; font-size: 0.85em;">
            <strong style="color: #CCCCCC;">Active Configuration:</strong><br>
            Profile: <code>""" + env.get('SIGNAL_PROFILE', 'custom') + """</code> | 
            Filter Mode: <code>""" + env.get('HARD_FILTER_MODE', 'strict') + """</code> | 
            Alert Category: <code>""" + env.get('MIN_ALERT_CATEGORY', 'alert') + """</code> | 
            Execution Category: <code>""" + env.get('MIN_EXECUTE_CATEGORY', 'strong') + """</code>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    _render_usd_red_news_table(env)

    # Key metrics with modern card design
    live_open_count = None if bot_open_err else len(bot_open_df.index)
    m = _metrics(db_path, live_open_count=live_open_count)
    pnl_value = float(m["today_pnl"])
    net_pnl_all = float(m.get("net_pnl_all", 0.0))
    pnl_text = f"{pnl_value:+.2f}" if abs(pnl_value) > 1e-12 else "0.00"
    net_pnl_text = f"{net_pnl_all:+.2f}" if abs(net_pnl_all) > 1e-12 else "0.00"
    
    # Metrics in modern cards
    cols = st.columns(6, gap="medium")
    
    metrics_data = [
        (t("open"), m["open"], "🟢"),
        (t("sent"), m["sent"], "📤"),
        (t("closed"), m["closed"], "✅"),
        (t("failed"), m["failed"], "❌"),
        (t("today_pnl"), pnl_text, "📈" if pnl_value >= 0 else "📉"),
        (t("net_pnl_all"), net_pnl_text, "💰" if net_pnl_all >= 0 else "📊"),
    ]
    
    for col, (label, value, icon) in zip(cols, metrics_data):
        with col:
            color = "#FFFFFF" if label != t("failed") and (label != t("today_pnl") and label != t("net_pnl_all") or float(value.replace(",", ".")) >= 0) else "#CCCCCC" if label == t("net_pnl_all") else "#FF6B6B" if label == t("failed") else "#FFB266"
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <div style="font-size: 2em; margin-bottom: 10px;">{icon}</div>
                    <div class="metric-label">{label}</div>
                    <div class="metric-value" style="color: {color};">{value}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Position sizing section
    st.markdown("---")
    st.subheader("💼 " + t("sizing_title"))
    
    sizing_mode = t("sizing_dynamic") if _parse_bool_env(env, "USE_MT5_BALANCE_FOR_SIZING", True) else t("sizing_static")
    sizing_base = env.get("RISK_BALANCE_SOURCE", "equity")
    last_sent = _query_df(
        db_path,
        """
        SELECT symbol, normalized_symbol, volume, risk_amount, timestamp
        FROM orders
        WHERE status='sent'
        ORDER BY id DESC
        LIMIT 1
        """,
    )
    if last_sent.empty:
        last_sent = _query_df(
            db_path,
            """
            SELECT symbol, normalized_symbol, volume, risk_amount, timestamp, closed_at, status
            FROM orders
            ORDER BY COALESCE(closed_at, timestamp) DESC, id DESC
            LIMIT 1
            """,
        )
    
    sizing_cols = st.columns(4, gap="medium")
    sizing_metrics = [
        (t("sizing_mode"), f"{sizing_mode} ({sizing_base})", "⚙️"),
        (t("sizing_last_symbol"), str(last_sent.iloc[0].get("normalized_symbol") or last_sent.iloc[0].get("symbol") or "-") if not last_sent.empty else "-", "📍"),
        (t("sizing_last_risk"), f"{float(last_sent.iloc[0].get('risk_amount') or 0.0):.2f}" if not last_sent.empty else "-", "💵"),
        (t("sizing_last_volume"), f"{float(last_sent.iloc[0].get('volume') or 0.0):.4f}" if not last_sent.empty else "-", "📦"),
    ]
    
    for col, (label, value, icon) in zip(sizing_cols, sizing_metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <div style="font-size: 1.8em; margin-bottom: 8px;">{icon}</div>
                    <div class="metric-label">{label}</div>
                    <div style="font-size: 1.3em; font-weight: 600; color: #CCCCCC;">{value}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Live MT5 positions
    st.markdown("---")
    st.subheader("📍 " + t("bot_open_positions_live"))
    
    if bot_open_err:
        st.warning(f"⚠️ {t('mt5_error')}: {bot_open_err}")
    elif bot_open_df.empty:
        st.info(f"✅ {t('bot_open_none')}")
    else:
        open_cols = [
            c
            for c in [
                "ticket",
                "symbol",
                "direction",
                "volume",
                "price_open",
                "price_now",
                "sl",
                "tp",
                "profit",
                "timestamp_th",
                "timestamp",
            ]
            if c in bot_open_df.columns
        ]
        
        # Format dataframe for display
        display_df = bot_open_df[open_cols].copy()
        st.markdown("""
        <style>
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.dataframe(display_df, use_container_width=True, height=250)

    # Admin cleanup and loss guard
    if is_admin:
        st.markdown("---")
        st.subheader("🧹 " + t("cleanup"))
        
        cleanup_cols = st.columns(3, gap="small")
        with cleanup_cols[0]:
            if st.button("🗑️ " + t("del_below"), use_container_width=True):
                _exec_sql(db_path, "DELETE FROM orders WHERE status='skipped' AND reason='below_min_execute_category'")
                st.success("✅ Cleaned!")
        
        with cleanup_cols[1]:
            if st.button("🗑️ " + t("del_cooldown"), use_container_width=True):
                _exec_sql(db_path, "DELETE FROM orders WHERE status='skipped' AND reason='cooldown_active'")
                st.success("✅ Cleaned!")
        
        with cleanup_cols[2]:
            if st.button("🔄 " + t("reset_loss_guard"), use_container_width=True):
                if db_path.exists():
                    db = SignalDB(str(db_path))
                    reset_at = db.reset_daily_loss_guard()
                    st.success(f"✅ Reset at: {reset_at}")
                else:
                    st.warning("⚠️ DB not found")
    
    # Loss guard status
    if db_path.exists():
        st.markdown("---")
        db = SignalDB(str(db_path))
        reset_at = db.get_runtime_state("daily_loss_reset_at") or "-"
        effective_loss = db.today_realized_loss()
        
        guard_cols = st.columns(2, gap="medium")
        with guard_cols[0]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🔐 {t('loss_guard_reset_at')}</div>
                <div style="font-size: 1.1em; color: #CCCCCC; margin-top: 8px;">{reset_at}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with guard_cols[1]:
            loss_color = "#FFFFFF" if effective_loss >= 0 else "#FF6B6B"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">📊 {t('loss_guard_effective')}</div>
                <div style="font-size: 1.1em; color: {loss_color}; margin-top: 8px;">{effective_loss:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    st.subheader(t("equity"))
    pnl_df = _query_df(
        db_path,
        "SELECT id, pnl FROM orders WHERE status='closed' AND pnl IS NOT NULL ORDER BY id ASC",
    )
    if pnl_df.empty:
        st.info(t("no_closed"))
    else:
        pnl_df["equity_curve"] = pnl_df["pnl"].cumsum()
        st.markdown("---")
        st.subheader("📈 " + t("equity"))
        st.line_chart(pnl_df[["id", "equity_curve"]].set_index("id"), width="stretch", height=300)

    st.markdown("---")
    st.subheader("📋 " + t("orders"))
    orders = _query_df(
        db_path,
        """
        SELECT id, timestamp, symbol, direction, status, reason, score, volume, risk_amount, entry_price, stop_loss, take_profit, pnl, closed_at
        FROM orders ORDER BY id DESC LIMIT 200
        """,
    )
    orders = _add_thai_time_columns(
        orders,
        {
            "timestamp": "timestamp_th",
            "closed_at": "closed_at_th",
        },
    )
    if orders.empty:
        st.info("✅ " + t("no_orders"))
    else:
        all_label = t("all")
        filter_cols = st.columns(3, gap="medium")
        with filter_cols[0]:
            f_symbol = st.selectbox(
                t("order_symbol"), 
                [all_label] + sorted(orders["symbol"].dropna().astype(str).unique().tolist()),
                key="order_symbol_filter"
            )
        with filter_cols[1]:
            f_status = st.selectbox(
                t("order_status"), 
                [all_label] + sorted(orders["status"].dropna().astype(str).unique().tolist()),
                key="order_status_filter"
            )
        with filter_cols[2]:
            f_reason = st.selectbox(
                t("order_reason"), 
                [all_label] + sorted(orders["reason"].dropna().astype(str).unique().tolist()),
                key="order_reason_filter"
            )

        view = orders.copy()
        if f_symbol != all_label:
            view = view[view["symbol"] == f_symbol]
        if f_status != all_label:
            view = view[view["status"] == f_status]
        if f_reason != all_label:
            view = view[view["reason"] == f_reason]

        st.dataframe(view, use_container_width=True, height=350)
        
        # Download button with better styling
        button_cols = st.columns([1, 1, 3], gap="small")
        with button_cols[0]:
            st.download_button(
                "⬇️ CSV",
                data=view.to_csv(index=False),
                file_name="orders_filtered.csv",
                mime="text/csv",
                use_container_width=True
            )
        with button_cols[1]:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

    st.markdown("---")
    st.subheader("🔔 " + t("signals"))
    signals = _query_df(
        db_path,
        "SELECT id, timestamp, symbol, direction, score, category, hard_filters_passed FROM signals ORDER BY id DESC LIMIT 200",
    )
    signals = _add_thai_time_columns(signals, {"timestamp": "timestamp_th"})
    if signals.empty:
        st.info("✅ " + t("no_signals"))
    else:
        all_label = t("all")
        signal_filter_cols = st.columns(3, gap="medium")
        with signal_filter_cols[0]:
            s_symbol = st.selectbox(
                t("signal_symbol"), 
                [all_label] + sorted(signals["symbol"].dropna().astype(str).unique().tolist()),
                key="signal_symbol_filter"
            )
        with signal_filter_cols[1]:
            s_cat = st.selectbox(
                t("signal_category"), 
                [all_label] + sorted(signals["category"].dropna().astype(str).unique().tolist()),
                key="signal_cat_filter"
            )
        with signal_filter_cols[2]:
            s_dir = st.selectbox(
                t("signal_direction"), 
                [all_label] + sorted(signals["direction"].dropna().astype(str).unique().tolist()),
                key="signal_dir_filter"
            )

        sview = signals.copy()
        if s_symbol != all_label:
            sview = sview[sview["symbol"] == s_symbol]
        if s_cat != all_label:
            sview = sview[sview["category"] == s_cat]
        if s_dir != all_label:
            sview = sview[sview["direction"] == s_dir]

        st.dataframe(sview, use_container_width=True, height=350)
        
        signal_button_cols = st.columns([1, 1, 3], gap="small")
        with signal_button_cols[0]:
            st.download_button(
                "⬇️ CSV",
                data=sview.to_csv(index=False),
                file_name="signals_filtered.csv",
                mime="text/csv",
                use_container_width=True
            )
        with signal_button_cols[1]:
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_signals"):
                st.rerun()

    st.markdown("---")
    st.subheader("📡 " + t("events"))
    events = _query_df(
        db_path,
        "SELECT id, timestamp, symbol, level, message FROM scan_events ORDER BY id DESC LIMIT 200",
    )
    events = _add_thai_time_columns(events, {"timestamp": "timestamp_th"})
    if events.empty:
        st.info(t("no_events"))
    else:
        st.dataframe(events, width="stretch", height=260)
        st.download_button(t("download_events"), data=events.to_csv(index=False), file_name="events_recent.csv", mime="text/csv")

    st.subheader(t("manual_orders"))
    lookback_days = st.slider(t("manual_days"), min_value=1, max_value=90, value=7, step=1, key="manual_lookback_days")
    open_manual, closed_manual, manual_err = _fetch_manual_mt5_activity(env, lookback_days=lookback_days, limit=200)
    if manual_err:
        st.warning(f"{t('manual_error')}: {manual_err}")
    st.caption(t("manual_open_positions"))
    if open_manual.empty:
        st.info(t("manual_none_open"))
    else:
        open_cols = [c for c in ["ticket", "position_id", "timestamp_th", "timestamp", "symbol", "direction", "volume", "price_open", "price_now", "profit", "magic", "comment"] if c in open_manual.columns]
        st.dataframe(open_manual[open_cols], width="stretch", height=220)

    st.caption(t("manual_closed_deals"))
    if closed_manual.empty:
        st.info(t("manual_none_closed"))
    else:
        close_cols = [c for c in ["deal", "position_id", "timestamp_th", "timestamp", "symbol", "direction", "volume", "price", "profit", "commission", "swap", "magic", "comment"] if c in closed_manual.columns]
        st.dataframe(closed_manual[close_cols], width="stretch", height=260)


def _render_performance(db_path: Path) -> None:
    st.subheader("📊 " + t("performance_title"))
    orders = _query_df(
        db_path,
        """
        SELECT id, timestamp, symbol, direction, status, reason, score, category, volume, entry_price, stop_loss, take_profit, pnl, closed_at
        FROM orders ORDER BY id DESC LIMIT 5000
        """,
    )
    if orders.empty:
        st.info(t("perf_no_data"))
        return

    orders = _add_thai_time_columns(
        orders,
        {
            "timestamp": "timestamp_th",
            "closed_at": "closed_at_th",
        },
    )
    orders["timestamp_utc_dt"] = pd.to_datetime(orders["timestamp"], utc=True, errors="coerce")
    orders["closed_at_utc_dt"] = pd.to_datetime(orders["closed_at"], utc=True, errors="coerce")
    orders["timestamp_bkk_dt"] = orders["timestamp_utc_dt"].dt.tz_convert(BANGKOK_TZ)
    orders["effective_utc_dt"] = orders["closed_at_utc_dt"].combine_first(orders["timestamp_utc_dt"])
    orders["effective_bkk_dt"] = orders["effective_utc_dt"].dt.tz_convert(BANGKOK_TZ)
    orders["pnl"] = pd.to_numeric(orders["pnl"], errors="coerce")
    orders["asset_profile"] = orders["symbol"].fillna("").astype(str).map(_asset_profile_name)

    effective_dates = orders["effective_bkk_dt"].dropna().dt.date
    default_end = effective_dates.max() if not effective_dates.empty else datetime.now().date()
    default_start = max((effective_dates.min() if not effective_dates.empty else default_end), default_end - timedelta(days=30))

    # Quick range selection
    st.markdown("**⏱️ " + t("perf_quick_range") + "**")
    quick_opts = [t("perf_today"), t("perf_7d"), t("perf_30d"), t("perf_all")]
    quick_cols = st.columns(4, gap="small")
    for idx, (col, opt) in enumerate(zip(quick_cols, quick_opts)):
        with col:
            if st.button(opt, use_container_width=True, key=f"quick_perf_{idx}"):
                st.session_state.quick_perf = opt
    
    quick = st.session_state.get("quick_perf", quick_opts[1])
    st.markdown("---")

    # Advanced filters
    st.markdown("**🔍 " + t("perf_filters") + "**" if "perf_filters" in TXT else "**🔍 Filters**")
    filt_col1, filt_col2, filt_col3 = st.columns(3, gap="medium")
    with filt_col1:
        date_range = st.date_input(
            t("perf_date_range"),
            value=(default_start, default_end),
        )
    with filt_col2:
        sym_opts = sorted(orders["symbol"].dropna().astype(str).unique().tolist())
        f_symbols = st.multiselect(t("perf_symbol"), options=sym_opts, default=sym_opts)
    with filt_col3:
        closed_only = st.checkbox(t("perf_closed_only"), value=False)

    filt_col4, filt_col5, filt_col6, filt_col7, filt_col8 = st.columns(5, gap="medium")
    with filt_col4:
        status_opts = sorted(orders["status"].dropna().astype(str).unique().tolist())
        f_status = st.multiselect(t("perf_status"), options=status_opts, default=status_opts, key="perf_status_filter")
    with filt_col5:
        dir_opts = sorted(orders["direction"].dropna().astype(str).unique().tolist())
        f_dirs = st.multiselect(t("perf_direction"), options=dir_opts, default=dir_opts, key="perf_dir_filter")
    with filt_col6:
        cat_opts = sorted(orders["category"].dropna().astype(str).unique().tolist())
        f_cat = st.multiselect(t("perf_category"), options=cat_opts, default=cat_opts, key="perf_cat_filter")
    with filt_col7:
        reason_opts = sorted(orders["reason"].fillna("").astype(str).unique().tolist())
        f_reason = st.multiselect(t("perf_reason"), options=reason_opts, default=reason_opts, key="perf_reason_filter")
    with filt_col8:
        profile_opts = sorted(orders["asset_profile"].dropna().astype(str).unique().tolist())
        f_profiles = st.multiselect(t("perf_asset_profile"), options=profile_opts, default=profile_opts, key="perf_profile_filter")

    view = orders.copy()
    quick_end = default_end
    if quick == t("perf_today"):
        d0, d1 = quick_end, quick_end
    elif quick == t("perf_7d"):
        d0, d1 = quick_end - timedelta(days=6), quick_end
    elif quick == t("perf_30d"):
        d0, d1 = quick_end - timedelta(days=29), quick_end
    elif isinstance(date_range, tuple) and len(date_range) == 2:
        d0, d1 = date_range
    else:
        d0, d1 = None, None

    if quick != t("perf_all") and d0 and d1:
        view = view[view["effective_bkk_dt"].dt.date.between(d0, d1)]
    if f_symbols:
        view = view[view["symbol"].astype(str).isin(f_symbols)]
    if f_status:
        view = view[view["status"].astype(str).isin(f_status)]
    if f_dirs:
        view = view[view["direction"].astype(str).isin(f_dirs)]
    if f_cat:
        view = view[view["category"].astype(str).isin(f_cat)]
    if f_reason:
        view = view[view["reason"].fillna("").astype(str).isin(f_reason)]
    if f_profiles:
        view = view[view["asset_profile"].astype(str).isin(f_profiles)]
    if closed_only:
        view = view[view["status"] == "closed"]

    if view.empty:
        st.info(t("perf_no_data"))
        return

    st.markdown("---")
    closed = view[view["status"] == "closed"].copy()
    closed = closed[closed["pnl"].notna()]
    wins = float((closed["pnl"] > 0).sum())
    losses = float((closed["pnl"] < 0).sum())
    win_rate = (wins / (wins + losses) * 100.0) if (wins + losses) > 0 else 0.0
    gross_profit = float(closed.loc[closed["pnl"] > 0, "pnl"].sum()) if not closed.empty else 0.0
    gross_loss_abs = abs(float(closed.loc[closed["pnl"] < 0, "pnl"].sum())) if not closed.empty else 0.0
    profit_factor = (gross_profit / gross_loss_abs) if gross_loss_abs > 0 else (999.0 if gross_profit > 0 else 0.0)
    net_pnl = float(closed["pnl"].sum()) if not closed.empty else 0.0
    avg_pnl = float(closed["pnl"].mean()) if not closed.empty else 0.0

    # Modern metrics display
    st.markdown("**📈 " + t("perf_summary") + "**" if "perf_summary" in TXT else "**📈 Performance Summary**")
    m_cols = st.columns(5, gap="medium")
    metrics_data = [
        (t("perf_rows"), str(len(view)), "📊"),
        (t("perf_net_pnl"), f"{net_pnl:+.2f}", "💰" if net_pnl >= 0 else "📉"),
        (t("perf_win_rate"), f"{win_rate:.1f}%", "✅"),
        (t("perf_profit_factor"), f"{profit_factor:.2f}", "🎯"),
        (t("perf_avg_pnl"), f"{avg_pnl:+.2f}", "📊"),
    ]
    for col, (label, value, icon) in zip(m_cols, metrics_data):
        with col:
            color = "#FFFFFF" if (label == t("perf_net_pnl") and net_pnl >= 0) or label == t("perf_win_rate") or label == t("perf_rows") else "#CCCCCC"
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <div style="font-size: 1.8em; margin-bottom: 8px;">{icon}</div>
                    <div class="metric-label">{label}</div>
                    <div class="metric-value" style="color: {color};">{value}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    if not closed.empty:
        st.markdown("---")
        curve = closed.sort_values("closed_at_utc_dt").copy()
        curve["cum_pnl"] = curve["pnl"].cumsum()
        st.markdown("**📈 " + t("perf_pnl_curve") + "**")
        st.line_chart(curve[["closed_at_utc_dt", "cum_pnl"]].set_index("closed_at_utc_dt"), width="stretch", height=300)

        st.markdown("---")
        st.markdown("**🏢 " + t("perf_profile_summary") + "**")
        profile_summary = (
            closed.groupby("asset_profile", dropna=False)
            .agg(
                trades=("id", "count"),
                net_pnl=("pnl", "sum"),
                avg_pnl=("pnl", "mean"),
                wins=("pnl", lambda s: int((s > 0).sum())),
                losses=("pnl", lambda s: int((s < 0).sum())),
            )
            .reset_index()
        )
        profile_summary["win_rate_pct"] = (
            profile_summary["wins"] / (profile_summary["wins"] + profile_summary["losses"]).replace(0, pd.NA) * 100.0
        ).fillna(0.0)
        profile_summary["net_pnl"] = profile_summary["net_pnl"].round(2)
        profile_summary["avg_pnl"] = profile_summary["avg_pnl"].round(2)
        profile_summary["win_rate_pct"] = profile_summary["win_rate_pct"].round(2)
        st.dataframe(profile_summary, use_container_width=True, height=250)

        st.markdown("---")
        st.markdown("**🎯 " + t("perf_symbol_summary") + "**")
        symbol_summary = (
            closed.groupby(["asset_profile", "symbol"], dropna=False)
            .agg(
                trades=("id", "count"),
                net_pnl=("pnl", "sum"),
                avg_pnl=("pnl", "mean"),
                wins=("pnl", lambda s: int((s > 0).sum())),
                losses=("pnl", lambda s: int((s < 0).sum())),
            )
            .reset_index()
            .sort_values(["net_pnl", "trades"], ascending=[False, False])
        )
        symbol_summary["win_rate_pct"] = (
            symbol_summary["wins"] / (symbol_summary["wins"] + symbol_summary["losses"]).replace(0, pd.NA) * 100.0
        ).fillna(0.0)
        symbol_summary["net_pnl"] = symbol_summary["net_pnl"].round(2)
        symbol_summary["avg_pnl"] = symbol_summary["avg_pnl"].round(2)
        symbol_summary["win_rate_pct"] = symbol_summary["win_rate_pct"].round(2)
        st.dataframe(symbol_summary, use_container_width=True, height=300)

    st.markdown("---")
    st.markdown("**📋 " + t("perf_detail_orders") + "**" if "perf_detail_orders" in TXT else "**📋 Orders Detail**")
    show_cols = [
        "id",
        "asset_profile",
        "timestamp_th",
        "timestamp",
        "symbol",
        "direction",
        "status",
        "reason",
        "score",
        "category",
        "volume",
        "entry_price",
        "stop_loss",
        "take_profit",
        "pnl",
        "closed_at_th",
        "closed_at",
    ]
    show_cols = [c for c in show_cols if c in view.columns]
    out = view[show_cols].copy()
    st.dataframe(out, use_container_width=True, height=380)
    
    # Download button
    dl_cols = st.columns([1, 4], gap="small")
    with dl_cols[0]:
        st.download_button(
            "⬇️ CSV",
            data=out.to_csv(index=False),
            file_name="performance_filtered.csv",
            mime="text/csv",
            use_container_width=True
        )


def _render_portfolio() -> None:
    st.subheader("💼 " + t("portfolio"))
    
    refresh_cols = st.columns([1, 4], gap="small")
    with refresh_cols[0]:
        if st.button("🔄 " + t("refresh_portfolio"), use_container_width=True):
            st.rerun()

    env = _load_env_map()
    try:
        mt5, error = _mt5_initialize_and_login(env)
        if mt5 is None:
            st.error(f"❌ {t('mt5_error')}: {error}")
            return

        account = mt5.account_info()
        if account:
            st.markdown("---")
            st.markdown("**🏦 " + t("account") + "**")
            
            # Account info as modern cards
            acc_cols = st.columns(6, gap="medium")
            account_data = {
                "login": int(getattr(account, "login", 0) or 0),
                "balance": float(getattr(account, "balance", 0.0) or 0.0),
                "equity": float(getattr(account, "equity", 0.0) or 0.0),
                "margin": float(getattr(account, "margin", 0.0) or 0.0),
                "profit": float(getattr(account, "profit", 0.0) or 0.0),
                "free_margin": float(getattr(account, "margin", 0.0) or 0.0) - float(getattr(account, "margin_used", 0.0) or 0.0),
            }
            
            account_display = [
                (t("account_login") if "account_login" in TXT else "Login", str(account_data["login"]), "🔐"),
                (t("account_balance") if "account_balance" in TXT else "Balance", f"{account_data['balance']:.2f}", "💵"),
                (t("account_equity") if "account_equity" in TXT else "Equity", f"{account_data['equity']:.2f}", "📊"),
                (t("account_margin") if "account_margin" in TXT else "Margin", f"{account_data['margin']:.2f}", "📌"),
                (t("account_profit") if "account_profit" in TXT else "Profit", f"{account_data['profit']:+.2f}", "📈" if account_data['profit'] >= 0 else "📉"),
                (t("account_free_margin") if "account_free_margin" in TXT else "Free Margin", f"{account_data['free_margin']:.2f}", "💚"),
            ]
            
            for col, (label, value, icon) in zip(acc_cols, account_display):
                with col:
                    color = "#FFFFFF" if (label.lower() in ["balance", "equity", "login"] or ("profit" in label.lower() and account_data['profit'] >= 0)) else "#CCCCCC"
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="text-align: center;">
                            <div style="font-size: 1.8em; margin-bottom: 8px;">{icon}</div>
                            <div class="metric-label">{label}</div>
                            <div class="metric-value" style="color: {color};">{value}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        positions = mt5.positions_get() or []
        rows = []
        for p in positions:
            rows.append(
                {
                    "ticket": int(getattr(p, "ticket", 0) or 0),
                    "symbol": str(getattr(p, "symbol", "")),
                    "direction": _mt5_direction_label(getattr(p, "type", 0)),
                    "volume": float(getattr(p, "volume", 0.0) or 0.0),
                    "price_open": float(getattr(p, "price_open", 0.0) or 0.0),
                    "sl": float(getattr(p, "sl", 0.0) or 0.0),
                    "tp": float(getattr(p, "tp", 0.0) or 0.0),
                    "profit": float(getattr(p, "profit", 0.0) or 0.0),
                    "magic": int(getattr(p, "magic", 0) or 0),
                }
            )

        st.markdown("---")
        st.markdown("**📍 " + t("positions") + "**")
        if not rows:
            st.info("✅ " + t("no_positions"))
        else:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=350)

    except Exception as exc:
        st.error(f"❌ {str(exc)}")
    finally:
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
        except Exception:
            pass


def _render_system_health(db_path: Path, is_admin: bool) -> None:
    st.subheader("⚙️ " + t("health_title"))
    env = _load_env_map()
    db = SignalDB(str(db_path))
    venv_py = ROOT / ".venv" / "Scripts" / "python.exe"
    pid_info = _read_pid_info() or {}
    daemon_pid = int(pid_info.get("pid", 0) or 0)
    daemon_running = daemon_pid > 0 and _is_pid_running(daemon_pid)
    stale_pid = PID_FILE.exists() and not daemon_running
    db_exists = db_path.exists()
    env_exists = ENV_PATH.exists()
    venv_exists = venv_py.exists()
    git_info = _git_version_info()

    # Status indicators
    st.markdown("**📋 System Status**")
    status_cols = st.columns(4, gap="medium")
    status_data = [
        ("Venv", t("health_exists") if venv_exists else t("health_missing"), "✅" if venv_exists else "❌"),
        ("Env", t("health_exists") if env_exists else t("health_missing"), "✅" if env_exists else "❌"),
        ("Database", t("health_exists") if db_exists else t("health_missing"), "✅" if db_exists else "❌"),
        ("Daemon", str(daemon_pid) if daemon_pid else "-", "✅" if daemon_running else "⚠️"),
    ]
    
    for col, (label, status_text, icon) in zip(status_cols, status_data):
        with col:
            color = "#FFFFFF" if "✅" in icon else "#FFB266"
            st.markdown(f"""
            <div class="metric-card">
                <div style="text-align: center;">
                    <div style="font-size: 1.8em; margin-bottom: 8px;">{icon}</div>
                    <div class="metric-label">{label}</div>
                    <div class="metric-value" style="color: {color};">{status_text}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**📡 Configuration**")
    st.caption(
        f"🔑 Login: {env.get('MT5_LOGIN', '-') or '-'} | "
        f"🌐 Server: {env.get('MT5_SERVER', '-') or '-'} | "
        f"📁 Database: {env.get('DB_PATH', 'signals.db')}"
    )

    st.markdown("---")
    mt5_level, mt5_label, mt5_details = _mt5_health_badge(env)
    st.markdown(f"**🔌 MT5 Status: {_status_badge(mt5_label, mt5_level)}**", unsafe_allow_html=True)
    if mt5_details:
        st.caption(mt5_details)
    st.caption(t("health_mt5_retry_note"))

    st.markdown("---")
    st.markdown("**📦 Version Info**")
    v_cols = st.columns(3, gap="medium")
    version_data = [
        ("📍 Branch", git_info["branch"]),
        ("🔗 Commit", git_info["commit"]),
        ("⏰ Time", git_info["commit_time"]),
    ]
    for col, (label, value) in zip(v_cols, version_data):
        with col:
            st.metric(label, value)

    if is_admin:
        st.markdown("---")
        st.markdown("**🔧 Admin Tools**")
        
        import_days = st.number_input(t("health_import_mt5_days"), min_value=1, max_value=365, value=30, step=1)

        # Test and import buttons
        tool_cols = st.columns(3, gap="medium")
        with tool_cols[0]:
            if st.button("🧪 " + t("health_mt5_test"), use_container_width=True):
                ok, payload = _test_mt5_connection(env)
                if ok:
                    db.log_scan_event("SYSTEM", "INFO", "health_mt5_test_ok", payload)
                    st.success("✅ " + t("health_mt5_ok"))
                    st.json(payload)
                else:
                    db.log_scan_event("SYSTEM", "ERROR", "health_mt5_test_fail", payload)
                    st.error(f"❌ {t('health_mt5_fail')}: {payload.get('error', 'unknown error')}")
        with tool_cols[1]:
            if st.button("📥 " + t("health_import_mt5_history"), use_container_width=True):
                stats, error = _import_mt5_history_to_db(env, db_path, lookback_days=int(import_days))
                if error:
                    db.log_scan_event("SYSTEM", "ERROR", "health_import_mt5_history_fail", {"error": error, "days": int(import_days), **stats})
                    st.error(f"❌ {t('health_import_mt5_fail')}: {error}")
                else:
                    db.log_scan_event("SYSTEM", "INFO", "health_import_mt5_history_done", {"days": int(import_days), **stats})
                    st.success(
                        f"✅ {t('health_import_mt5_done')}: "
                        f"open={stats.get('open_imported', 0)} "
                        f"closed={stats.get('closed_imported', 0)} "
                        f"skipped={stats.get('skipped', 0)}"
                    )
                    st.json(stats)
        with tool_cols[2]:
            bundle_bytes, bundle_name, bundle_summary = _build_support_bundle(env, db_path)
            downloaded = st.download_button(
                "📦 " + t("health_support_bundle"),
                data=bundle_bytes,
                file_name=bundle_name,
                mime="application/zip",
                use_container_width=True,
            )
            with st.expander("📋 " + t("health_support_preview"), expanded=False):
                st.json(bundle_summary)
            if downloaded:
                db.log_scan_event("SYSTEM", "INFO", "health_support_bundle_downloaded", {"file_name": bundle_name, **bundle_summary})

        st.markdown("---")
        st.markdown("**🚀 Quick Actions**")
        action_cols = st.columns(2, gap="medium")
        with action_cols[0]:
            if st.button("📂 " + t("health_open_logs"), use_container_width=True):
                ok, msg = _run_batch_file(ROOT / "Open-Logs.bat", detached=True)
                (st.success if ok else st.warning)("✅ " + msg if ok else "⚠️ " + msg)
        with action_cols[1]:
            if st.button("📊 " + t("health_status_check"), use_container_width=True):
                ok, msg = _run_batch_file(ROOT / "Status-Check.bat", detached=True)
                (st.success if ok else st.warning)("✅ " + msg if ok else "⚠️ " + msg)

        st.markdown("---")
        st.markdown("**🔨 " + t("health_self_heal") + "**")
        heal_cols = st.columns(3, gap="medium")
        with heal_cols[0]:
            if st.button("🗑️ " + t("health_clear_stale_pid"), use_container_width=True):
                if stale_pid:
                    _clear_pid_info()
                    db.log_scan_event("SYSTEM", "INFO", "health_clear_stale_pid", {"cleared": True})
                    st.success("✅ Cleared stale PID file")
                else:
                    db.log_scan_event("SYSTEM", "INFO", "health_clear_stale_pid", {"cleared": False})
                    st.info("ℹ️ No stale PID to clear")
        with heal_cols[1]:
            if st.button("🔀 " + t("health_run_sync_now"), use_container_width=True):
                with st.status("⏳ Running...", expanded=True) as status:
                    code, out, err = _run_command([_project_python(), "main.py", "--mode", "sync"], timeout=300)
                    status.write(out or "(no stdout)")
                    if err:
                        status.write(err)
                    status.update(label=f"✅ Done (code={code})", state="complete")
                    db.log_scan_event("SYSTEM", "INFO" if code == 0 else "ERROR", "health_run_sync_now", {"code": code, "stdout": out, "stderr": err})
        with heal_cols[2]:
            if st.button("🔄 " + t("health_restart_all"), use_container_width=True):
                ok, msg = _run_batch_file(ROOT / "Restart-All.bat", detached=True)
                db.log_scan_event("SYSTEM", "INFO" if ok else "ERROR", "health_restart_all", {"message": msg})
                (st.success if ok else st.warning)("✅ " + msg if ok else "⚠️ " + msg)
    else:
        st.info("ℹ️ " + t("access_admin_only"))

    st.markdown("---")
    st.markdown("**🔌 Network Ports**")
    st.dataframe(_port_snapshot([8501, 8502]), use_container_width=True, height=180)

    st.markdown("---")
    st.markdown("**⚙️ Processes**")
    proc_df = _process_snapshot()
    if proc_df.empty:
        st.info("ℹ️ " + t("health_not_running"))
    else:
        st.dataframe(proc_df, use_container_width=True, height=220)

    st.markdown("---")
    st.markdown("**📜 Recent Logs**")
    log_cols = st.columns(2, gap="medium")
    with log_cols[0]:
        st.markdown("**📝 daemon.log**")
        st.code(_tail_text(ROOT / "logs" / "daemon.log", lines=20), language="log")
    with log_cols[1]:
        st.markdown("**📝 dashboard.log**")
        st.code(_tail_text(ROOT / "logs" / "dashboard.log", lines=20), language="log")


def _render_config_editor() -> None:
    st.subheader("⚙️ " + t("env_editor"))
    if not ENV_PATH.exists():
        st.warning("⚠️ .env not found")
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

    st.markdown("**🔧 " + t("config_wizard") + "**")
    st.markdown("---")
    st.markdown("**🔀 " + t("account_switcher") + "**")
    default_mode = env.get("ACCOUNT_MODE", env.get("EXECUTION_MODE", "demo")).strip().lower()
    if default_mode not in {"demo", "live"}:
        default_mode = "demo"

    with st.form("account_switch_form", clear_on_submit=False):
        st.markdown("**Select Account Mode:**")
        active_mode = st.radio(
            t("account_mode"),
            options=["demo", "live"],
            index=0 if default_mode == "demo" else 1,
            horizontal=True,
        )
        a1, a2 = st.columns(2, gap="medium")
        with a1:
            st.markdown("**📝 " + t("account_demo") + "**")
            demo_login = st.text_input(f"🔐 {t('account_login')} (DEMO)", value=env.get("MT5_LOGIN_DEMO", env.get("MT5_LOGIN", "")))
            demo_password = st.text_input(f"🔑 {t('account_password')} (DEMO)", value=env.get("MT5_PASSWORD_DEMO", env.get("MT5_PASSWORD", "")), type="password")
            demo_server = st.text_input(f"🌐 {t('account_server')} (DEMO)", value=env.get("MT5_SERVER_DEMO", env.get("MT5_SERVER", "")))
        with a2:
            st.markdown("**📝 " + t("account_live") + "**")
            live_login = st.text_input(f"🔐 {t('account_login')} (LIVE)", value=env.get("MT5_LOGIN_LIVE", ""))
            live_password = st.text_input(f"🔑 {t('account_password')} (LIVE)", value=env.get("MT5_PASSWORD_LIVE", ""), type="password")
            live_server = st.text_input(f"🌐 {t('account_server')} (LIVE)", value=env.get("MT5_SERVER_LIVE", ""))

        b1, b2 = st.columns(2, gap="medium")
        save_profiles = b1.form_submit_button("💾 " + t("save_account_profiles"), use_container_width=True)
        apply_switch = b2.form_submit_button("✅ " + t("apply_account_mode"), use_container_width=True)

        profile_updates = {
            "ACCOUNT_MODE": active_mode,
            "MT5_LOGIN_DEMO": demo_login.strip(),
            "MT5_PASSWORD_DEMO": demo_password.strip(),
            "MT5_SERVER_DEMO": demo_server.strip(),
            "MT5_LOGIN_LIVE": live_login.strip(),
            "MT5_PASSWORD_LIVE": live_password.strip(),
            "MT5_SERVER_LIVE": live_server.strip(),
            "DB_PATH_DEMO": _account_db_path("demo", demo_login.strip()),
            "DB_PATH_LIVE": _account_db_path("live", live_login.strip()),
        }

        if save_profiles:
            _upsert_env_values(profile_updates)
            db.log_config_change(source="streamlit_account", summary="save_account_profiles", changes={"ACCOUNT_MODE": active_mode})
            st.success("✅ " + t("account_saved"))
            st.info("ℹ️ " + t("restart_hint"))
            st.rerun()

        if apply_switch:
            selected = {
                "demo": (demo_login.strip(), demo_password.strip(), demo_server.strip()),
                "live": (live_login.strip(), live_password.strip(), live_server.strip()),
            }.get(active_mode, ("", "", ""))
            login_v, password_v, server_v = selected
            if not (login_v and password_v and server_v):
                st.warning("⚠️ " + t("account_missing"))
            else:
                apply_updates = dict(profile_updates)
                apply_updates.update(
                    {
                        "MT5_LOGIN": login_v,
                        "MT5_PASSWORD": password_v,
                        "MT5_SERVER": server_v,
                        "EXECUTION_MODE": "demo" if active_mode == "demo" else "live",
                        "DB_PATH": _account_db_path(active_mode, login_v),
                    }
                )
                _upsert_env_values(apply_updates)
                db.log_config_change(
                    source="streamlit_account",
                    summary=f"apply_account_mode:{active_mode}",
                    changes={"ACCOUNT_MODE": active_mode, "EXECUTION_MODE": apply_updates["EXECUTION_MODE"]},
                )
                st.success("✅ " + t("account_switched"))
                st.info("ℹ️ " + t("restart_hint"))
                st.rerun()

    st.markdown("---")
    with st.expander("📖 ความหมายแต่ละหัวข้อ / Section meanings", expanded=False):
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
    with st.expander("📚 พจนานุกรมค่าตั้งค่า / Config glossary", expanded=False):
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
        if st.button(t("apply_preset"), width="stretch"):
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
            wick_entry_enabled = st.checkbox("WICK_ENTRY_ENABLED", value=_parse_bool_env(env, "WICK_ENTRY_ENABLED", True), help=h("wick_entry_enabled"))
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
            use_mt5_balance_for_sizing = st.checkbox(
                "USE_MT5_BALANCE_FOR_SIZING",
                value=_parse_bool_env(env, "USE_MT5_BALANCE_FOR_SIZING", True),
                help=h("use_mt5_balance_for_sizing"),
            )
            risk_balance_source = st.selectbox(
                "RISK_BALANCE_SOURCE",
                ["equity", "balance"],
                index=0 if env.get("RISK_BALANCE_SOURCE", "equity").strip().lower() == "equity" else 1,
                help=h("risk_balance_source"),
            )

        st.markdown("#### USD News Table")
        n1, n2 = st.columns(2)
        with n1:
            usd_calendar_strict_red_only = st.checkbox(
                "USD_CALENDAR_STRICT_RED_ONLY",
                value=_parse_bool_env(env, "USD_CALENDAR_STRICT_RED_ONLY", True),
                help="If enabled, table shows only high-impact/red USD events.",
            )
        with n2:
            usd_calendar_window_minutes = st.number_input(
                "USD_CALENDAR_WINDOW_MINUTES",
                min_value=0,
                max_value=1440,
                value=_parse_int_env(env, "USD_CALENDAR_WINDOW_MINUTES", 180),
                step=15,
                help="Upcoming time window in minutes (0-1440).",
            )

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
                "WICK_ENTRY_ENABLED": str(wick_entry_enabled).lower(),
                "RISK_PER_TRADE_PCT": f"{risk_pct:.2f}",
                "USE_MT5_BALANCE_FOR_SIZING": str(use_mt5_balance_for_sizing).lower(),
                "RISK_BALANCE_SOURCE": risk_balance_source,
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
                "USD_CALENDAR_STRICT_RED_ONLY": str(usd_calendar_strict_red_only).lower(),
                "USD_CALENDAR_WINDOW_MINUTES": str(int(usd_calendar_window_minutes)),
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
        if st.button(t("install_tasks"), width="stretch"):
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
        if st.button(t("uninstall_tasks"), width="stretch"):
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
        if st.button(f"{t('task_run')} {t('task_daemon')}", width="stretch"):
            ok, info = _task_action(TASK_DAEMON, "run")
            (st.success if ok else st.warning)(info)
        if st.button(f"{t('task_stop')} {t('task_daemon')}", width="stretch"):
            ok, info = _task_action(TASK_DAEMON, "stop")
            (st.success if ok else st.warning)(info)
        with st.expander(f"{t('task_status')} {t('task_daemon')} (raw)"):
            st.text(msg or "-")
    with q2:
        exists, msg = _task_query(TASK_DASHBOARD)
        st.caption(f"{t('task_status')} {t('task_dashboard')}: {'OK' if exists else 'N/A'}")
        if st.button(f"{t('task_run')} {t('task_dashboard')}", width="stretch"):
            ok, info = _task_action(TASK_DASHBOARD, "run")
            (st.success if ok else st.warning)(info)
        if st.button(f"{t('task_stop')} {t('task_dashboard')}", width="stretch"):
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
        st.dataframe(audit_df, width="stretch", height=240)

    st.markdown(f"### {t('raw_editor')}")
    text = ENV_PATH.read_text(encoding="utf-8")
    updated = st.text_area(t("env_label"), value=text, height=600)
    if st.button(t("save_env"), type="primary"):
        ENV_PATH.write_text(updated, encoding="utf-8")
        db.log_config_change(source="streamlit_raw", summary="save_raw_env", changes={})
        st.success(t("saved"))


def _render_guide() -> None:
    st.subheader("📖 " + ("คู่มือใช้งาน" if st.session_state.get("lang", "th") == "th" else "User Guide"))
    
    if st.session_state.get("lang", "th") == "th":
        st.markdown(
            """
## 📋 คู่มือใช้งานระบบ (SOP)

### 1️⃣ เปิดระบบประจำวัน
```powershell
C:/pytrade/.venv/Scripts/python.exe C:/pytrade/main.py --mode reset_loss_guard
C:/pytrade/.venv/Scripts/python.exe C:/pytrade/main.py --mode sync
C:/pytrade/.venv/Scripts/python.exe C:/pytrade/main.py --mode scan --once
```

**หรือใช้ไฟล์คลิกได้:**
- 🔄 `Reset-Loss-Guard.bat`
- 🔀 `Sync-Orders.bat`
- 🔍 `Scan-Once.bat`
- ▶️ `Start-All.bat`

### 2️⃣ โหมดใช้งาน
- 🔍 `scan --once`: สแกน 1 รอบ
- 🔀 `sync`: ซิงก์สถานะออเดอร์/PnL
- 👁️ `daemon`: รันต่อเนื่อง

### 3️⃣ ลำดับการใช้งานใน Dashboard
1. ✅ ตรวจสถานะเดมอนและบัญชี MT5
2. ⚙️ ปรับค่าในแท็บ `ตั้งค่า` (Configuration Wizard)
3. 🔄 กด `ซิงก์ออเดอร์` ก่อนเสมอ
4. 🔍 กด `สแกน 1 รอบ` เพื่อทดสอบ
5. ▶️ ถ้าปกติค่อย `เริ่มเดมอน`

### 4️⃣ การปรับความเข้มข้น
- 🚀 `aggressive`: เข้าเยอะ
- ⚖️ `balanced`: สมดุล
- 💎 `premium`: คัดเข้ม
- 👑 `ultra_premium`: คัดโหด

### 5️⃣ เหตุผลที่มักเจอ
- ❌ `below_min_execute_category`: คะแนนยังไม่ถึงขั้นต่ำส่งคำสั่ง
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
C:/pytrade/.venv/Scripts/python.exe -m pytest -q
C:/pytrade/.venv/Scripts/python.exe -m sqlite3 signals.db "SELECT id,timestamp,symbol,status,reason,score,category FROM orders ORDER BY id DESC LIMIT 30;"
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
C:/pytrade/.venv/Scripts/python.exe C:/pytrade/main.py --mode reset_loss_guard
C:/pytrade/.venv/Scripts/python.exe C:/pytrade/main.py --mode sync
C:/pytrade/.venv/Scripts/python.exe C:/pytrade/main.py --mode scan --once
```

Or use the clickable launchers:
- `Reset-Loss-Guard.bat`
- `Sync-Orders.bat`
- `Scan-Once.bat`
- `Start-All.bat`

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
C:/pytrade/.venv/Scripts/python.exe -m pytest -q
C:/pytrade/.venv/Scripts/python.exe -m sqlite3 signals.db "SELECT id,timestamp,symbol,status,reason,score,category FROM orders ORDER BY id DESC LIMIT 30;"
```

#### 8) Safety notes
- Keep `EXECUTION_MODE=demo` until stable
- Score is rule-based confidence, not win rate
- Avoid increasing risk during drawdown
            """
        )


def _render_deploy_wizard() -> None:
    st.subheader("🚀 " + t("deploy_title"))
    env = _load_env_map()
    db_path = _load_env_db_path()
    db = SignalDB(str(db_path))

    st.markdown("---")
    st.markdown("**📦 " + t("deploy_release_title") + "**")
    artifacts = _latest_release_artifacts()
    output_dir = Path(str(artifacts["output_dir"]))
    if artifacts["installer"] or artifacts["release_zip"] or artifacts["release_notes"]:
        r1, r2, r3, r4 = st.columns(4, gap="medium")
        r1.metric("📌 " + t("deploy_release_latest"), str(artifacts["version"]))
        r2.metric("💾 " + t("deploy_release_installer"), Path(artifacts["installer"]).name if artifacts["installer"] else "-")
        r3.metric("📦 " + t("deploy_release_zip"), Path(artifacts["release_zip"]).name if artifacts["release_zip"] else "-")
        r4.metric("📄 " + t("deploy_release_notes"), Path(artifacts["release_notes"]).name if artifacts["release_notes"] else "-")
    else:
        st.info("ℹ️ " + t("deploy_release_none"))

    st.caption(f"📁 {t('deploy_release_output')}: {output_dir}")

    st.markdown("---")
    st.markdown("**🔨 Build Tools**")
    rr1, rr2, rr3 = st.columns(3, gap="medium")
    with rr1:
        if st.button("🏗️ " + t("deploy_release_build_installer"), use_container_width=True):
            code, out, err = _run_powershell_script(ROOT / "scripts" / "build_installer.ps1", timeout=1800)
            if code == 0:
                db.log_scan_event("SYSTEM", "INFO", "deploy_build_installer", {"stdout": out})
                st.success("✅ " + (out or t("deploy_release_built")))
                st.rerun()
            else:
                db.log_scan_event("SYSTEM", "ERROR", "deploy_build_installer_fail", {"stdout": out, "stderr": err})
                st.error("❌ " + (err or out or t("deploy_release_failed")))
    with rr2:
        if st.button("📦 " + t("deploy_release_package"), use_container_width=True):
            code, out, err = _run_powershell_script(ROOT / "scripts" / "package_release.ps1", timeout=1800)
            if code == 0:
                db.log_scan_event("SYSTEM", "INFO", "deploy_package_release", {"stdout": out})
                st.success("✅ " + (out or t("deploy_release_packaged")))
                st.rerun()
            else:
                db.log_scan_event("SYSTEM", "ERROR", "deploy_package_release_fail", {"stdout": out, "stderr": err})
                st.error("❌ " + (err or out or t("deploy_release_failed")))
    with rr3:
        if st.button("⚙️ " + t("deploy_release_build_all"), use_container_width=True):
            ok, msg = _run_batch_file(ROOT / "Build-Release.bat", detached=False)
            db.log_scan_event("SYSTEM", "INFO" if ok else "ERROR", "deploy_build_all", {"message": msg})
            (st.success if ok else st.error)(("✅ " if ok else "❌ ") + msg)
            if ok:
                st.rerun()

    st.markdown("---")
    st.markdown("**📂 File Management**")
    rr4, rr5, rr6 = st.columns(3, gap="medium")
    with rr4:
        if st.button("📂 " + t("deploy_release_open_output"), use_container_width=True):
            try:
                subprocess.Popen(["explorer.exe", str(output_dir)], cwd=str(ROOT), shell=False)
                st.success("✅ " + str(output_dir))
            except Exception as exc:
                st.error("❌ " + str(exc))
    with rr5:
        if st.button("🔀 " + t("deploy_release_select_version"), use_container_width=True):
            ok, msg = _run_batch_file(ROOT / "scripts" / "Select-Version.bat", detached=True)
            (st.success if ok else st.warning)(("✅ " if ok else "⚠️ ") + msg)
    with rr6:
        if st.button("🔄 " + t("deploy_release_refresh"), use_container_width=True):
            st.rerun()

    st.markdown("---")
    st.markdown("**⬇️ Downloads**")
    dl1, dl2, dl3, dl4 = st.columns(4, gap="medium")
    with dl1:
        installer_path = artifacts["installer"]
        if installer_path and Path(installer_path).exists():
            p = Path(installer_path)
            st.download_button(
                "💾 " + t("deploy_release_download_installer"),
                data=p.read_bytes(),
                file_name=p.name,
                mime="application/vnd.microsoft.portable-executable",
                use_container_width=True,
            )
    with dl2:
        zip_path = artifacts["release_zip"]
        if zip_path and Path(zip_path).exists():
            p = Path(zip_path)
            st.download_button(
                "📦 " + t("deploy_release_download_zip"),
                data=p.read_bytes(),
                file_name=p.name,
                mime="application/zip",
                use_container_width=True,
            )
    with dl3:
        notes_path = artifacts["release_notes"]
        if notes_path and Path(notes_path).exists():
            p = Path(notes_path)
            st.download_button(
                "📄 " + t("deploy_release_download_notes"),
                data=p.read_bytes(),
                file_name=p.name,
                mime="text/markdown",
                use_container_width=True,
            )
    with dl4:
        manifest_path = artifacts["manifest"]
        if manifest_path and Path(manifest_path).exists():
            p = Path(manifest_path)
            st.download_button(
                "📋 " + t("deploy_release_download_manifest"),
                data=p.read_bytes(),
                file_name=p.name,
                mime="application/json",
                use_container_width=True,
            )

    st.markdown("---")
    with st.expander("📦 Release artifacts", expanded=False):
        preview_rows = []
        for label, key in [
            (t("deploy_release_installer"), "installer"),
            (t("deploy_release_zip"), "release_zip"),
            (t("deploy_release_notes"), "release_notes"),
            (t("deploy_release_manifest"), "manifest"),
        ]:
            path = artifacts[key]
            if path:
                p = Path(path)
                preview_rows.append(
                    {
                        "artifact": label,
                        "file": p.name,
                        "updated_at": datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
                        "size_bytes": p.stat().st_size,
                    }
                )
        if preview_rows:
            st.dataframe(pd.DataFrame(preview_rows), width="stretch", height=220)
        else:
            st.info(t("deploy_release_none"))

    manifest_path = artifacts["manifest"]
    if manifest_path and Path(manifest_path).exists():
        with st.expander(t("deploy_release_manifest_preview"), expanded=False):
            try:
                st.json(json.loads(Path(manifest_path).read_text(encoding="utf-8")))
            except Exception as exc:
                st.error(str(exc))

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
        width="stretch",
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
    """Main application entry point with modern UI"""
    _init_ui_state_from_query()
    if "lang" not in st.session_state:
        st.session_state["lang"] = "th"
    
    # Modern header
    st.markdown("""
    <div class="header-main">
        <h1>📊 PyTrade Control Center</h1>
        <p>Professional Trading Automation Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    env = _load_env_map()
    _ensure_access_session(env)
    is_admin = _is_admin()
    db_path = _load_env_db_path()
    
    # Render controls in sidebar
    with st.sidebar:
        st.markdown("---")
        _render_controls(db_path, is_admin)
        st.markdown("---")
    
    # Build tab configuration (ordered by usage frequency)
    tab_options = [
        ("dashboard", "📊 " + t("tab_dashboard")),
        ("performance", "📈 " + t("tab_performance")),
        ("portfolio", "💼 " + t("tab_portfolio")),
        ("health", "🏥 " + t("tab_health")),
        ("guide", "📖 " + t("tab_guide")),
    ]
    if is_admin:
        tab_options.extend([
            ("config", "⚙️ " + t("tab_config")),
            ("deploy", "🚀 " + t("tab_deploy"))
        ])
    
    # Get current active tab
    current_key = str(st.session_state.get("active_tab", "dashboard"))
    valid_keys = {key for key, _ in tab_options}
    if current_key not in valid_keys:
        current_key = "dashboard"
        st.session_state["active_tab"] = current_key
    
    # Create tab navigation with equal-sized buttons - responsive layout
    if len(tab_options) <= 4:
        nav_buttons = st.columns(len(tab_options), gap="small")
    elif len(tab_options) <= 6:
        nav_buttons = st.columns(5, gap="small")
    else:
        nav_buttons = st.columns(5, gap="small")
    
    nav_idx = 0
    for key, label in tab_options:
        if nav_idx >= len(nav_buttons):
            st.write("")  # New line
            nav_buttons = st.columns(len(tab_options) - nav_idx, gap="small")
            nav_idx = 0
        
        with nav_buttons[nav_idx]:
            if st.button(label, use_container_width=True, key=f"nav_{key}"):
                st.session_state["active_tab"] = key
                st.rerun()
        nav_idx += 1
    
    st.markdown("---")
    _persist_ui_state_to_query()
    
    # Render selected tab
    selected_key = str(st.session_state.get("active_tab", "dashboard"))
    
    try:
        if selected_key == "dashboard":
            _render_dashboard(db_path, is_admin)
        elif selected_key == "performance":
            _render_performance(db_path)
        elif selected_key == "portfolio":
            _render_portfolio()
        elif selected_key == "health":
            _render_system_health(db_path, is_admin)
        elif selected_key == "config":
            if is_admin:
                _render_config_editor()
            else:
                st.error(t("access_admin_only"))
        elif selected_key == "guide":
            _render_guide()
        elif selected_key == "deploy":
            if is_admin:
                _render_deploy_wizard()
            else:
                st.error(t("access_admin_only"))
        else:
            st.warning("Unknown tab")
    except Exception as exc:
        st.error(f"Error rendering tab: {exc}")


if __name__ == "__main__":
    main()
