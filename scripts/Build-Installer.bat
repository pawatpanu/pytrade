@echo off
setlocal
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File ".\scripts\build_installer.ps1"
if errorlevel 1 (
  echo.
  echo Build installer failed.
  exit /b 1
)
echo.
echo Build installer success.
exit /b 0
