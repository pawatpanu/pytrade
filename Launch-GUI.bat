@echo off
setlocal
cd /d "%~dp0"

REM รันเปิด PowerShell Launcher
powershell -NoProfile -ExecutionPolicy Bypass -File "PyTrade-Launcher.ps1"

endlocal
