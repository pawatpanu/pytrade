@echo off
setlocal
cd /d "%~dp0\.."

echo [PyTrade] Closing all visible app windows...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0\Shutdown-All-Windows.ps1"

echo [PyTrade] Stopping Python/Streamlit processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM py.exe /F >nul 2>&1
taskkill /IM streamlit.exe /F >nul 2>&1

echo [PyTrade] Shutdown completed.
pause
endlocal
