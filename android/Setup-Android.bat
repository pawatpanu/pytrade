@echo off
REM PyTrade Android Setup Helper for Windows
REM Automates Android setup: IP detection, port checking, QR code generation

setlocal enabledelayedexpansion

REM Colors (limited in batch)
color 0B
title PyTrade Android Setup

cls
echo ============================================
echo PyTrade Android Setup Helper
echo ============================================
echo.

REM ============================================
REM Find Local IP
REM ============================================
echo Finding your PC IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    set "tmp=%%a"
    if not "!ipaddr!" == "" (
        set "ipaddr=!tmp:~1!"
    )
)

if "!ipaddr!" == "" (
    echo ERROR: Could not find IP address
    echo Please check Settings ^> Network ^> Status
    pause
    exit /b 1
)

echo Found IP: !ipaddr!
echo.

REM ============================================
REM Check if Streamlit is running
REM ============================================
echo Checking if Streamlit is running...
netstat -an | find "8501" >nul
if %errorlevel% == 0 (
    echo Found Streamlit running on port 8501
) else (
    echo WARNING: Streamlit not found on port 8501
    echo Please run: python -m streamlit run streamlit_app.py
)
echo.

REM ============================================
REM Generate URLs
REM ============================================
set "DIRECT_URL=http://!ipaddr!:8501"
set "MOBILE_URL=http://!ipaddr!:8501/?lang=th"

echo Android Connection URLs:
echo ============================================
echo Direct:  !DIRECT_URL!
echo Mobile:  !MOBILE_URL!
echo.

REM ============================================
REM Update .env.android
REM ============================================
if exist ".env.android" (
    echo Updating .env.android...
    
    REM Simple text replacement (works for basic cases)
    setlocal disableDelayedExpansion
    for /f "delims=" %%i in (.env.android) do (
        set "line=%%i"
        setlocal enableDelayedExpansion
        if "!line:~0,14!" == "PYTRADE_HOST=" (
            echo PYTRADE_HOST=!ipaddr!
        ) else (
            echo !line!
        )
        endlocal
    ) > .env.android.tmp
    
    move /y .env.android.tmp .env.android >nul
    echo Updated .env.android
) else (
    echo .env.android not found, skipping update
)
echo.

REM ============================================
REM Copy URL to clipboard (PowerShell)
REM ============================================
echo Copying URL to clipboard...
powershell -Command "Add-Type –AssemblyName System.windows.forms; [System.Windows.Forms.Clipboard]::SetText('!MOBILE_URL!')"
echo Copied: !MOBILE_URL!
echo.

REM ============================================
REM Display Instructions
REM ============================================
echo ============================================
echo INSTRUCTIONS FOR ANDROID
echo ============================================
echo.
echo 1. Ensure PC and Android are on SAME WiFi
echo.
echo 2. Open Chrome on Android phone
echo.
echo 3. Enter this URL in address bar:
echo    !MOBILE_URL!
echo    ^(already copied to clipboard^)
echo.
echo 4. To install as app:
echo    - Chrome Menu (3 dots) ^> "Install app"
echo    - Or: Menu ^> "Add to Home Screen"
echo    - App will appear on home screen
echo.
echo 5. For internet access (outside WiFi):
echo    - Download Ngrok: https://ngrok.com
echo    - Run: ngrok http 8501
echo    - Copy the ngrok URL (https://xxxx.ngrok.io)
echo    - Edit .env.android: PYTRADE_HOST=https://xxxx.ngrok.io
echo.

REM ============================================
REM Troubleshooting
REM ============================================
echo ============================================
echo TROUBLESHOOTING
echo ============================================
echo.
echo Cannot connect?
echo.
echo 1. Check same WiFi:
echo    - PC WiFi network name
echo    - Android WiFi network name (should match)
echo.
echo 2. Check Firewall:
echo    - Windows Defender Firewall
echo    - Allow Python on Private/Public networks
echo.
echo 3. Verify Streamlit running:
echo    - Check this window (should show "Streamlit running")
echo    - If not, run: python -m streamlit run streamlit_app.py
echo.
echo 4. Restart services:
echo    - Close Chrome on Android
echo    - Restart Streamlit on PC
echo    - Try again
echo.
echo 5. Use IP instead of hostname:
echo    - !ipaddr! instead of computer name
echo.

REM ============================================
REM Optional: Generate QR Code
REM ============================================
echo.
echo Would you like to generate a QR code?
echo This QR code can be scanned by Android for quick setup.
echo.
set /p "generate_qr=Generate QR code (y/n)? "
if /i "!generate_qr!"=="y" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "if (Get-Command qrcode -ErrorAction SilentlyContinue) {" ^
        "  qrcode -Text '!MOBILE_URL!' -OutPath 'pytrade_qr_code.png'" ^
        "  Write-Host 'QR code saved: pytrade_qr_code.png'" ^
        "} else {" ^
        "  Write-Host 'qrcode command not found. Install: pip install qrcode[pil]'" ^
        "}"
)
echo.

REM ============================================
REM Complete
REM ============================================
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Keep this window open to monitor Streamlit
echo Press CTRL+C to stop
echo.

pause
