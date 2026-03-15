@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Release-Manager.ps1" -SearchRoot "%~dp0"
endlocal
