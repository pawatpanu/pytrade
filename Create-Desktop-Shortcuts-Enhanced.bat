@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PS_CMD=$W=New-Object -ComObject WScript.Shell; $D=[Environment]::GetFolderPath('Desktop'); $P='%CD%';"
set "PS_CMD=!PS_CMD! $items=@("
set "PS_CMD=!PS_CMD! @{Name='PyTrade - Start All'; Target='!CD!\Quick-Start.bat'; Icon='%SystemRoot%\System32\SHELL32.dll,25'},"
set "PS_CMD=!PS_CMD! @{Name='PyTrade - Dashboard'; Target='!CD!\Run-Dashboard.bat'; Icon='%SystemRoot%\System32\SHELL32.dll,220'},"
set "PS_CMD=!PS_CMD! @{Name='PyTrade - Daemon'; Target='!CD!\Run-Daemon.bat'; Icon='%SystemRoot%\System32\SHELL32.dll,108'},"
set "PS_CMD=!PS_CMD! @{Name='PyTrade - Launcher'; Target='!CD!\PyTrade-Launcher.bat'; Icon='%SystemRoot%\System32\SHELL32.dll,44'},"
set "PS_CMD=!PS_CMD! @{Name='PyTrade - Status'; Target='!CD!\Status-Check.bat'; Icon='%SystemRoot%\System32\SHELL32.dll,23'}"
set "PS_CMD=!PS_CMD! );"
set "PS_CMD=!PS_CMD! foreach($i in $items){ $S=$W.CreateShortcut((Join-Path $D ($i.Name + '.lnk'))); $S.TargetPath=$i.Target; $S.WorkingDirectory='!CD!'; $S.IconLocation=$i.Icon; $S.Save() }"

echo.
echo 💾 กำลังสร้าง Desktop Shortcuts...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "!PS_CMD!"
if errorlevel 1 (
  echo.
  echo ❌ ล้มเหลวในการสร้าง Desktop Shortcuts
  pause
  exit /b 1
)

echo.
echo ✅ Desktop Shortcuts สร้างสำเร็จแล้ว
echo.
echo    PyTrade - Start All         (เปิดทั้งหมด)
echo    PyTrade - Dashboard         (เปิด Web เท่านั้น)
echo    PyTrade - Daemon            (เปิด Daemon เท่านั้น)
echo    PyTrade - Launcher          (เมนู Launcher)
echo    PyTrade - Status            (ตรวจสถานะ)
echo.
pause
endlocal
