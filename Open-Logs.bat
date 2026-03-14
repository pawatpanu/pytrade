@echo off
setlocal
cd /d "%~dp0"
if not exist ".\logs" (
  echo [PyTrade] Log folder not found: %CD%\logs
  pause
  exit /b 1
)
start "" explorer.exe "%CD%\logs"
if exist "%CD%\logs\daemon.log" start "" notepad.exe "%CD%\logs\daemon.log"
if exist "%CD%\logs\dashboard.log" start "" notepad.exe "%CD%\logs\dashboard.log"
endlocal
