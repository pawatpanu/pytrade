@echo off
setlocal
cd /d "%~dp0"
call ".\scripts\Build-Release.bat"
exit /b %errorlevel%
