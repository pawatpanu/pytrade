@echo off
REM PyTrade MT5 Connection Setup Helper
REM Windows Batch Script

setlocal enabledelayedexpansion

color 0B
title PyTrade MT5 Setup

cls
echo.
echo ============================================
echo PyTrade MT5 Connection Setup
echo ============================================
echo.
echo This wizard will help you connect to MT5
echo.
pause

REM ============================================
REM Check if MT5 is installed
REM ============================================
echo Checking for MetaTrader 5...
echo.

set "mt5_found=0"
for %%D in (
    "C:\Program Files\MetaTrader 5\terminal64.exe"
    "C:\Program Files\MetaTrader 5\terminal.exe"
    "C:\Program Files (x86)\MetaTrader 5\terminal64.exe"
    "C:\Program Files (x86)\MetaTrader 5\terminal.exe"
) do (
    if exist %%D (
        set "MT5_PATH=%%D"
        set "mt5_found=1"
        echo Found: %%D
    )
)

if !mt5_found! == 0 (
    echo ERROR: MetaTrader 5 Terminal not found
    echo Please install from: https://www.metaquotes.net/
    pause
    exit /b 1
)

echo.
echo ============================================
echo Enter your MT5 Account Details
echo ============================================
echo.

REM Account number
:login_input
set /p MT5_LOGIN="MT5 Account Number (LOGIN): "
if "!MT5_LOGIN!" == "" goto login_input
echo Account: !MT5_LOGIN!

REM Password
:password_input
set /p MT5_PASSWORD="MT5 Password: "
if "!MT5_PASSWORD!" == "" goto password_input
echo Password: ******* (hidden)

REM Server
echo.
echo Common servers:
echo  - Exness-MT5Trial
echo  - Exness-MT5
echo  - ThailandFutures-Demo
echo.
:server_input
set /p MT5_SERVER="MT5 Server Name: "
if "!MT5_SERVER!" == "" goto server_input
echo Server: !MT5_SERVER!

echo.
echo ============================================
echo Updating .env file...
echo ============================================
echo.

REM Check if .env exists
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo Created .env from .env.example
    ) else (
        echo ERROR: .env.example not found
        pause
        exit /b 1
    )
)

REM Simple .env update (batch is limited, so we do line-by-line)
setlocal disableDelayedExpansion
for /f "delims=" %%i in (.env) do (
    set "line=%%i"
    setlocal enableDelayedExpansion
    if "!line:~0,11!" == "MT5_LOGIN=" (
        echo MT5_LOGIN=!MT5_LOGIN!
    ) else if "!line:~0,14!" == "MT5_PASSWORD=" (
        echo MT5_PASSWORD=!MT5_PASSWORD!
    ) else if "!line:~0,11!" == "MT5_SERVER=" (
        echo MT5_SERVER=!MT5_SERVER!
    ) else if "!line:~0,8!" == "MT5_PATH=" (
        echo MT5_PATH=!MT5_PATH!
    ) else (
        echo !line!
    )
    endlocal
) > .env.tmp

move /y .env.tmp .env >nul

echo .env file updated successfully!
echo.

echo ============================================
echo Updated Configuration:
echo ============================================
echo MT5_LOGIN=!MT5_LOGIN!
echo MT5_SERVER=!MT5_SERVER!
echo MT5_PATH=!MT5_PATH!
echo.

REM ============================================
REM Optional: Run Python setup tester
REM ============================================
echo.
echo Would you like to test the connection?
echo.
set /p test_conn="Test MT5 connection? (y/n): "

if /i "!test_conn!"=="y" (
    echo.
    echo Activating virtual environment...
    call .\.venv\Scripts\Activate.ps1
    
    echo Running connection test...
    python setup_mt5.py
) else (
    echo Skipping connection test
)

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Start PyTrade daemon:
echo    Run-Daemon.bat
echo.
echo 2. Open Dashboard:
echo    Run-Dashboard.bat
echo.
echo For detailed info:
echo    - Read: MT5_CONNECTION_GUIDE.md
echo    - Follow: README.md
echo.
echo Happy trading! ^_^
echo.
pause
