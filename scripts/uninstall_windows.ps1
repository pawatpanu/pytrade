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
    }
    else {
        Write-Host "Task not found: $taskName"
    }
}

function Remove-DesktopShortcutSafe([string]$nameNoExt) {
    $desktopPaths = @(
        [Environment]::GetFolderPath("Desktop"),
        [Environment]::GetFolderPath("CommonDesktopDirectory")
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique

    foreach ($desktop in $desktopPaths) {
        if (-not (Test-Path $desktop)) { continue }
        foreach ($ext in @(".lnk", ".url")) {
            $path = Join-Path $desktop ("$nameNoExt$ext")
            if (Test-Path $path) {
                Remove-Item -Force $path
                Write-Host "Removed shortcut: $path" -ForegroundColor Yellow
            }
        }
    }
}

function Remove-StartupShortcutSafe([string]$nameNoExt) {
    $startupDir = [Environment]::GetFolderPath("Startup")
    if ([string]::IsNullOrWhiteSpace($startupDir) -or -not (Test-Path $startupDir)) { return }

    $path = Join-Path $startupDir ("$nameNoExt.lnk")
    if (Test-Path $path) {
        Remove-Item -Force $path
        Write-Host "Removed startup shortcut: $path" -ForegroundColor Yellow
    }
}

$project = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Remove-TaskSafe "PyTradeDaemon"
Remove-TaskSafe "PyTradeDashboard"
Remove-DesktopShortcutSafe "PyTrade Start"
Remove-DesktopShortcutSafe "PyTrade Dashboard"
Remove-StartupShortcutSafe "PyTradeDaemon Startup"
Remove-StartupShortcutSafe "PyTradeDashboard Startup"

if (-not $KeepVenv) {
    $venvDir = Join-Path $project ".venv"
    if (Test-Path $venvDir) {
        Remove-Item -Recurse -Force $venvDir
        Write-Host "Removed .venv" -ForegroundColor Yellow
    }
}

Write-Host "Uninstall complete." -ForegroundColor Green
