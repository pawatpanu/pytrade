@echo off
setlocal
cd /d "%~dp0\.."
call ".\Stop-All.bat" --silent
timeout /t 2 >nul
call ".\Start-All.bat"
endlocal
