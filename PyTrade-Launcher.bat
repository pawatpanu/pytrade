@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

color 0A
title PyTrade Launcher

:menu
cls
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                  🚀 PyTrade Launcher 🚀                   ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo  [1] ▶️  เปิดทั้งหมด (Start All)
echo       - เปิด Daemon + Dashboard ทีเดียว
echo.
echo  [2] 📊 เปิด Dashboard เท่านั้น
echo       - เปิด Web Dashboard
echo.
echo  [3] 👁️  เปิด Daemon เท่านั้น
echo       - รันการสแกนอัตโนมัติ
echo.
echo  [4] 📂 สร้าง Desktop Shortcuts
echo       - สร้าย shortcut บนหน้าจอ
echo.
echo  [5] 📋 ตรวจสถานะระบบ
echo       - Status Check
echo.
echo  [6] 📂 เปิดโฟลเดอร์ Logs
echo       - ดู Log files
echo.
echo  [0] ❌ ออก
echo.
echo ═══════════════════════════════════════════════════════════
set /p choice="เลือกตัวเลือก (0-6): "

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto dashboard_only
if "%choice%"=="3" goto daemon_only
if "%choice%"=="4" goto create_shortcuts
if "%choice%"=="5" goto status_check
if "%choice%"=="6" goto open_logs
if "%choice%"=="0" goto exit_launcher
goto menu

:start_all
cls
echo.
echo ⏳ กำลังเปิด Daemon และ Dashboard...
echo.
call ".\scripts\Start-All.bat"
goto menu

:dashboard_only
cls
echo.
echo ⏳ กำลังเปิด Dashboard เท่านั้น...
echo.
call ".\Run-Dashboard.bat"
goto menu

:daemon_only
cls
echo.
echo ⏳ กำลังเปิด Daemon เท่านั้น...
echo.
call ".\Run-Daemon.bat"
goto menu

:create_shortcuts
cls
echo.
echo 💾 กำลังสร้าง Desktop Shortcuts...
echo.
call ".\Create-Desktop-Shortcuts.bat"
echo.
echo ✅ Shortcuts สร้างเสร็จแล้ว! ตรวจสอบ Desktop ของคุณ
echo.
pause
goto menu

:status_check
cls
echo.
echo 📋 ตรวจสถานะระบบ...
echo.
call ".\Status-Check.bat"
goto menu

:open_logs
cls
echo.
echo 📂 เปิดโฟลเดอร์ Logs...
echo.
call ".\Open-Logs.bat"
goto menu

:exit_launcher
cls
echo.
echo 👋 ยินดีต้อนรับสำหรับการใช้ PyTrade!
echo.
timeout /t 2 >nul
exit /b 0
