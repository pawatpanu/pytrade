@echo off
setlocal
cd /d "%~dp0\.."

set "VENV_PY=%CD%\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [PyTrade] Missing %VENV_PY%
  echo Please install the project or create the virtual environment first.
  exit /b 1
)

set "DASH_URL=http://127.0.0.1:8501/?lang=th"
set "DASH_PID="
for /f %%P in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0\Start-Dashboard-App.ps1" -Url "%DASH_URL%"') do set "DASH_PID=%%P"

if defined DASH_PID (
  echo [PyTrade] Dashboard app PID=%DASH_PID%
  start "PyTrade Dashboard Watcher" powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0\Watch-Dashboard-And-Shutdown.ps1" -DashboardPid %DASH_PID%
) else (
  echo [PyTrade] Failed to start Edge app window.
  echo [PyTrade] Auto-shutdown on X requires Microsoft Edge app mode.
  exit /b 1
)

"%VENV_PY%" -m streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
set "APP_EXIT=%ERRORLEVEL%"

echo [PyTrade] Dashboard server exited (code=%APP_EXIT%).
exit /b 0
