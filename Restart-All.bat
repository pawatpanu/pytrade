@echo off
cd /d "%~dp0"
call ".\Stop-All.bat"
timeout /t 2 >nul
call ".\Start-All.bat"
