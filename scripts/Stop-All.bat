@echo off
setlocal
cd /d "%~dp0\.."

set "SILENT=0"
if /I "%~1"=="--silent" set "SILENT=1"
if /I "%~1"=="/silent" set "SILENT=1"

echo [PyTrade] Stopping PyTrade processes...

REM Kill core python processes first
taskkill /IM python.exe /F /T >nul 2>&1
taskkill /IM py.exe /F /T >nul 2>&1
taskkill /IM streamlit.exe /F /T >nul 2>&1

REM Kill cmd windows started by PyTrade launchers
taskkill /FI "WINDOWTITLE eq PyTrade Daemon*" /F /T >nul 2>&1
taskkill /FI "WINDOWTITLE eq PyTrade Dashboard*" /F /T >nul 2>&1
taskkill /FI "WINDOWTITLE eq PyTrade - Start All*" /F /T >nul 2>&1

REM Kill watcher/background PowerShell launched by PyTrade
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -ieq 'powershell.exe' -and $_.CommandLine -like '*Watch-Dashboard-And-Shutdown.ps1*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

REM Kill only Edge app instances created by PyTrade profile (leave normal browser sessions)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -ieq 'msedge.exe' -and $_.CommandLine -like '*PyTradeEdgeDashboardProfile*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [PyTrade] Stop command sent.

if "%SILENT%"=="0" pause
endlocal
