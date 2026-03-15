@echo off
setlocal
cd /d "%~dp0\.."

echo.
echo [1/2] Building installer...
powershell -ExecutionPolicy Bypass -File ".\scripts\build_installer.ps1"
if errorlevel 1 (
  echo.
  echo Build installer failed.
  exit /b 1
)

echo.
echo [2/2] Packaging release...
powershell -ExecutionPolicy Bypass -File ".\scripts\package_release.ps1"
if errorlevel 1 (
  echo.
  echo Package release failed.
  exit /b 1
)

echo.
echo Build release success.
exit /b 0
