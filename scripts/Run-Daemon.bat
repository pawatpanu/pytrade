@echo off
setlocal
cd /d "%~dp0\.."

set "VENV_PY=%CD%\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [PyTrade] Missing %VENV_PY%
  echo Please install the project or create the virtual environment first.
  pause
  exit /b 1
)

"%VENV_PY%" main.py --mode daemon
if errorlevel 1 (
  echo.
  echo [PyTrade] Failed to start Daemon.
  pause
  exit /b 1
)

endlocal
