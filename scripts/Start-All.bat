@echo off
setlocal
cd /d "%~dp0\.."

REM Always cleanup leftovers first to avoid duplicate windows/processes
call ".\Stop-All.bat" --silent >nul 2>&1
timeout /t 1 >nul

set "VENV_PY=%CD%\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [PyTrade] Missing %VENV_PY%
  echo Please install the project or create the virtual environment first.
  exit /b 1
)

start "PyTrade Daemon" cmd /c "cd /d "%CD%" && "%VENV_PY%" main.py --mode daemon"
timeout /t 2 >nul
start "PyTrade Dashboard" cmd /c "cd /d "%CD%" && call .\scripts\Run-Dashboard.bat"

echo [PyTrade] Started Daemon and Dashboard.
echo [PyTrade] Dashboard URL: http://127.0.0.1:8501/?lang=th
echo [PyTrade] Closing Dashboard app window (X) will shutdown all.
endlocal
exit /b 0
