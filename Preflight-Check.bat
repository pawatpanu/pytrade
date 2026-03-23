@echo off
setlocal
cd /d "%~dp0"
set "REPORT=%CD%\logs\preflight_manual_report.txt"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\preflight_windows.ps1" -ProjectRoot "%CD%" -ReportPath "%REPORT%"
set "RC=%ERRORLEVEL%"
echo.
echo Report: %REPORT%
if not "%RC%"=="0" (
  echo Preflight failed with exit code %RC%.
)
pause
exit /b %RC%
