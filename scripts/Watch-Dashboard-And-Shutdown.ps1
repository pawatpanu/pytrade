param(
    [Parameter(Mandatory = $true)]
    [int]$DashboardPid
)

$ErrorActionPreference = "SilentlyContinue"

# Wait until dashboard host process exits (including manual X close)
Wait-Process -Id $DashboardPid

Write-Host "[PyTrade] Dashboard process exited. Running shutdown-all..."
powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\Shutdown-All-Windows.ps1"

taskkill /IM python.exe /F > $null 2>&1
taskkill /IM py.exe /F > $null 2>&1
taskkill /IM streamlit.exe /F > $null 2>&1
