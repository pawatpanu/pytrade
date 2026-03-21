@echo off
setlocal

net session >nul 2>&1
if not %errorlevel%==0 (
  echo [PyTrade] Requesting Administrator privileges...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo [PyTrade] Disabling scheduled tasks...
schtasks /Change /TN PyTradeDashboard /Disable
schtasks /Change /TN PyTradeDaemon /Disable

echo.
echo [PyTrade] Current task states:
schtasks /Query /TN PyTradeDashboard /FO LIST /V | findstr /I "Scheduled Task State"
schtasks /Query /TN PyTradeDaemon /FO LIST /V | findstr /I "Scheduled Task State"

echo.
echo [PyTrade] Done.
pause
endlocal
