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

start "PyTrade Daemon" cmd /k "cd /d "%CD%" && "%VENV_PY%" main.py --mode daemon"
timeout /t 2 >nul
start "" "http://127.0.0.1:8501/?lang=th"
start "PyTrade Dashboard" cmd /k "cd /d "%CD%" && "%VENV_PY%" -m streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1"

echo [PyTrade] Started Daemon and Dashboard.
echo [PyTrade] Dashboard URL: http://127.0.0.1:8501/?lang=th
pause
endlocal
