param(
    [switch]$KeepVenv = $true
)

$ErrorActionPreference = "Stop"

function Remove-TaskSafe([string]$taskName) {
    $query = schtasks /Query /TN $taskName 2>$null
    if ($LASTEXITCODE -eq 0) {
        schtasks /End /TN $taskName 2>$null | Out-Null
        schtasks /Delete /F /TN $taskName | Out-Null
        Write-Host "Removed task: $taskName" -ForegroundColor Yellow
    } else {
        Write-Host "Task not found: $taskName"
    }
}

$project = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Remove-TaskSafe "PyTradeDaemon"
Remove-TaskSafe "PyTradeDashboard"

if (-not $KeepVenv) {
    $venvDir = Join-Path $project ".venv"
    if (Test-Path $venvDir) {
        Remove-Item -Recurse -Force $venvDir
        Write-Host "Removed .venv" -ForegroundColor Yellow
    }
}

Write-Host "Uninstall complete." -ForegroundColor Green
