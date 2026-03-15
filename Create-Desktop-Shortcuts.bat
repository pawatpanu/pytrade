@echo off
setlocal
cd /d "%~dp0"

set "PS_CMD=$W=New-Object -ComObject WScript.Shell; $D=[Environment]::GetFolderPath('Desktop');"
set "PS_CMD=%PS_CMD% $items=@("
set "PS_CMD=%PS_CMD% @{Name='PyTrade Dashboard'; Target='%CD%\Run-Dashboard.bat'; Icon='%SystemRoot%\System32\SHELL32.dll,220'},"
set "PS_CMD=%PS_CMD% @{Name='PyTrade Start All'; Target='%CD%\Start-All.bat'; Icon='%SystemRoot%\System32\SHELL32.dll,25'},"
set "PS_CMD=%PS_CMD% @{Name='PyTrade Status Check'; Target='%CD%\Status-Check.bat'; Icon='%SystemRoot%\System32\SHELL32.dll,23'}"
set "PS_CMD=%PS_CMD% );"
set "PS_CMD=%PS_CMD% foreach($i in $items){ $S=$W.CreateShortcut((Join-Path $D ($i.Name + '.lnk'))); $S.TargetPath=$i.Target; $S.WorkingDirectory='%CD%'; $S.IconLocation=$i.Icon; $S.Save() }"
set "PS_CMD=%PS_CMD% ; Write-Host 'Created desktop shortcuts at' $D"

powershell -NoProfile -ExecutionPolicy Bypass -Command "%PS_CMD%"
if errorlevel 1 (
  echo.
  echo [PyTrade] Failed to create desktop shortcuts.
  pause
  exit /b 1
)

echo.
echo [PyTrade] Desktop shortcuts created successfully.
pause
endlocal

