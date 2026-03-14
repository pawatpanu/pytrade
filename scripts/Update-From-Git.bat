@echo off
setlocal
cd /d "%~dp0\.."
call "..\Update-From-Git.bat"
endlocal
