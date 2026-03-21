@echo off
cd /d "%~dp0"
call ".\scripts\Stop-All.bat" --silent
timeout /t 2 >nul
call ".\scripts\Start-All.bat"
