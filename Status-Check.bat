@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=%CD%\.venv\Scripts\python.exe"
set "DB_PATH=%CD%\signals.db"
set "PID_FILE=%CD%\.runtime\daemon_pid.json"

echo ========================================
echo PyTrade Status Check
echo Root: %CD%
echo ========================================
echo.

if exist "%VENV_PY%" (
  echo [OK] Venv Python found: %VENV_PY%
) else (
  echo [ERR] Venv Python missing: %VENV_PY%
)

echo.
if exist "%CD%\.env" (
  echo [OK] .env found
) else (
  echo [ERR] .env missing
)

echo.
if exist "%PID_FILE%" (
  echo [OK] Daemon PID file found: %PID_FILE%
  type "%PID_FILE%"
) else (
  echo [INFO] Daemon PID file not found
)

echo.
if exist "%DB_PATH%" (
  echo [OK] Database found: %DB_PATH%
) else (
  echo [INFO] Database not found at default path: %DB_PATH%
)

echo.
echo [INFO] Checking local ports...
netstat -ano | findstr ":8501 "
netstat -ano | findstr ":8502 "

echo.
echo [INFO] Checking running processes...
tasklist | findstr /I "python.exe py.exe streamlit.exe terminal64.exe"

echo.
if exist "%VENV_PY%" (
  echo [INFO] Python environment:
  "%VENV_PY%" -c "import sys; print(sys.executable)"
)

echo.
pause
endlocal
