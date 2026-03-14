@echo off
setlocal
cd /d "%~dp0"

set "GIT_EXE=C:\Program Files\Git\cmd\git.exe"
if not exist "%GIT_EXE%" (
  echo [ERR] Git not found: %GIT_EXE%
  echo Please install Git for Windows first.
  pause
  exit /b 1
)

echo [PyTrade] Fetching latest changes...
"%GIT_EXE%" pull --ff-only
if errorlevel 1 (
  echo.
  echo [PyTrade] Git pull failed.
  pause
  exit /b 1
)

echo.
echo [PyTrade] Updating Python packages...
if exist "%CD%\.venv\Scripts\python.exe" (
  "%CD%\.venv\Scripts\python.exe" -m pip install -r requirements.txt
) else (
  echo [WARN] .venv not found, skip pip install.
)

echo.
echo [PyTrade] Restarting services...
call ".\Restart-All.bat"
endlocal
