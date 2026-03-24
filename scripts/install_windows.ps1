param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$PythonLauncher = "",
    [switch]$InstallDashboardTask = $true,
    [switch]$SkipPreflight = $false
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$msg) {
    Write-Host "[PyTrade Installer] $msg" -ForegroundColor Cyan
}

function New-DesktopShortcutSafe {
    param(
        [string]$Name,
        [string]$TargetPath,
        [string]$Arguments = "",
        [string]$WorkingDirectory = "",
        [string]$IconLocation = ""
    )

    if (-not (Test-Path $TargetPath)) {
        Write-Host "Shortcut target not found: $TargetPath" -ForegroundColor Yellow
        return
    }

    $desktopPaths = @(
        [Environment]::GetFolderPath("Desktop"),
        [Environment]::GetFolderPath("CommonDesktopDirectory")
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique

    $shell = New-Object -ComObject WScript.Shell
    foreach ($desktop in $desktopPaths) {
        if (-not (Test-Path $desktop)) { continue }
        $shortcutPath = Join-Path $desktop ("$Name.lnk")
        try {
            $shortcut = $shell.CreateShortcut($shortcutPath)
            $shortcut.TargetPath = $TargetPath
            if ($Arguments) { $shortcut.Arguments = $Arguments }
            if ($WorkingDirectory) { $shortcut.WorkingDirectory = $WorkingDirectory }
            if ($IconLocation) { $shortcut.IconLocation = $IconLocation }
            $shortcut.Save()
            Write-Step "Created desktop shortcut: $shortcutPath"
        }
        catch {
            Write-Host "Unable to create shortcut at ${shortcutPath}: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

function New-DesktopUrlShortcutSafe {
    param(
        [string]$Name,
        [string]$Url,
        [string]$IconFile = "",
        [int]$IconIndex = 0
    )

    if ([string]::IsNullOrWhiteSpace($Url)) { return }

    $desktopPaths = @(
        [Environment]::GetFolderPath("Desktop"),
        [Environment]::GetFolderPath("CommonDesktopDirectory")
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique

    foreach ($desktop in $desktopPaths) {
        if (-not (Test-Path $desktop)) { continue }
        $shortcutPath = Join-Path $desktop ("$Name.url")
        try {
            $lines = @(
                "[InternetShortcut]",
                "URL=$Url"
            )
            if ($IconFile) {
                $lines += "IconFile=$IconFile"
                $lines += "IconIndex=$IconIndex"
            }
            Set-Content -Path $shortcutPath -Encoding ASCII -Value $lines
            Write-Step "Created desktop shortcut: $shortcutPath"
        }
        catch {
            Write-Host "Unable to create URL shortcut at ${shortcutPath}: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

function Invoke-ExternalChecked {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$FailureMessage
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (exit code: $LASTEXITCODE)"
    }
}

function New-StartupShortcutSafe {
    param(
        [string]$Name,
        [string]$TargetPath,
        [string]$Arguments = "",
        [string]$WorkingDirectory = ""
    )

    $startupDir = [Environment]::GetFolderPath("Startup")
    if ([string]::IsNullOrWhiteSpace($startupDir) -or -not (Test-Path $startupDir)) {
        Write-Host "Startup folder unavailable; cannot create startup shortcut." -ForegroundColor Yellow
        return $false
    }

    try {
        $shell = New-Object -ComObject WScript.Shell
        $shortcutPath = Join-Path $startupDir ("$Name.lnk")
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $TargetPath
        if ($Arguments) { $shortcut.Arguments = $Arguments }
        if ($WorkingDirectory) { $shortcut.WorkingDirectory = $WorkingDirectory }
        $shortcut.Save()
        Write-Step "Created startup shortcut: $shortcutPath"
        return $true
    }
    catch {
        Write-Host "Unable to create startup shortcut: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

function Try-RegisterScheduledTask {
    param(
        [string]$TaskName,
        [string]$RunnerScriptPath
    )

    & schtasks.exe /Create /F /SC ONLOGON /TN $TaskName /TR "powershell -NoProfile -ExecutionPolicy Bypass -File `"$RunnerScriptPath`""
    if ($LASTEXITCODE -eq 0) {
        return $true
    }

    Write-Host "Task creation failed for $TaskName (exit code: $LASTEXITCODE). Falling back to Startup shortcut." -ForegroundColor Yellow
    return $false
}

function Ensure-PersistentRunner {
    param(
        [string]$TaskName,
        [string]$RunnerScriptPath,
        [string]$StartupShortcutName,
        [string]$ProjectRoot
    )

    if (Try-RegisterScheduledTask -TaskName $TaskName -RunnerScriptPath $RunnerScriptPath) {
        Write-Step "Starting scheduled task now: $TaskName"
        & schtasks.exe /Run /TN $TaskName | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Unable to start task $TaskName immediately (exit code: $LASTEXITCODE). It will run at next logon." -ForegroundColor Yellow
        }
        return "task"
    }

    $startupOk = New-StartupShortcutSafe -Name $StartupShortcutName -TargetPath "powershell.exe" -Arguments "-NoProfile -ExecutionPolicy Bypass -File `"$RunnerScriptPath`"" -WorkingDirectory $ProjectRoot
    if ($startupOk) {
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $RunnerScriptPath -WindowStyle Hidden
        return "startup"
    }

    throw "Failed to configure persistent startup for $TaskName"
}

function Test-PythonCommand([string]$CommandPath) {
    if ([string]::IsNullOrWhiteSpace($CommandPath)) { return $false }
    try {
        & $CommandPath -c "import sys; print(sys.version.split()[0])" > $null 2>&1
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Resolve-PythonCommand([string]$PreferredLauncher) {
    $candidates = @()
    if ($PreferredLauncher) { $candidates += $PreferredLauncher }
    $candidates += @("py", "python")

    foreach ($cmd in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($cmd)) {
            $resolved = Get-Command $cmd -ErrorAction SilentlyContinue
            if ($resolved) {
                $src = $resolved.Source
                if ($src -match "WindowsApps") {
                    continue
                }
                if (Test-PythonCommand $src) {
                    return $src
                }
            }
        }
    }

    $knownPython = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe",
        "$env:ProgramFiles\Python312\python.exe"
    )
    foreach ($path in $knownPython) {
        if ((Test-Path $path) -and (Test-PythonCommand $path)) { return $path }
    }

    return $null
}

function Install-PythonIfMissing {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Python was not found and winget is unavailable. Install Python 3.11+ from python.org, then rerun installer."
    }

    Write-Step "Python not found. Installing Python 3.11 via winget..."
    Invoke-ExternalChecked -FilePath $winget.Source -Arguments @(
        "install", "--id", "Python.Python.3.11", "-e", "--source", "winget",
        "--accept-package-agreements", "--accept-source-agreements", "--silent"
    ) -FailureMessage "winget failed to install Python 3.11"

    Start-Sleep -Seconds 5
    $resolved = Resolve-PythonCommand ""
    if (-not $resolved) {
        throw "Python installation completed but python executable was not found in PATH/known locations."
    }
    return $resolved
}

$project = (Resolve-Path $ProjectRoot).Path
$venvDir = Join-Path $project ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$envFile = Join-Path $project ".env"
$envExample = Join-Path $project ".env.example"
$logDir = Join-Path $project "logs"
$runtimeDir = Join-Path $project ".runtime"
$daemonRunner = Join-Path $PSScriptRoot "run_daemon.ps1"
$dashboardRunner = Join-Path $PSScriptRoot "run_dashboard.ps1"
$preflightScript = Join-Path $PSScriptRoot "preflight_windows.ps1"

Write-Step "Project root: $project"

if (-not $SkipPreflight) {
    Write-Step "Running preflight checks..."
    if (-not (Test-Path $preflightScript)) {
        throw "Preflight script not found: $preflightScript"
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $preflightScript -ProjectRoot $project -ReportPath (Join-Path $logDir "preflight_install_report.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "Preflight checks failed. Fix reported issues then rerun installer."
    }
}

$pythonCmd = Resolve-PythonCommand $PythonLauncher
if (-not $pythonCmd) {
    $pythonCmd = Install-PythonIfMissing
}
Write-Step "Using Python: $pythonCmd"

if (-not (Test-Path $venvPython)) {
    Write-Step "Creating virtual environment..."
    Invoke-ExternalChecked -FilePath $pythonCmd -Arguments @("-m", "venv", "$venvDir") -FailureMessage "Failed to create virtual environment"
}

Write-Step "Installing dependencies..."
Invoke-ExternalChecked -FilePath $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip") -FailureMessage "Failed to upgrade pip"
Invoke-ExternalChecked -FilePath $venvPython -Arguments @("-m", "pip", "install", "-r", (Join-Path $project "requirements.txt")) -FailureMessage "Failed to install dependencies from requirements.txt"

if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Write-Step "Creating .env from .env.example..."
    Copy-Item $envExample $envFile
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

@"
`$ErrorActionPreference = "Stop"
Set-Location "$project"
New-Item -ItemType Directory -Force -Path "$logDir" | Out-Null
& "$venvPython" main.py --mode daemon *>> "$logDir\daemon.log"
"@ | Set-Content -Path $daemonRunner -Encoding UTF8

@"
`$ErrorActionPreference = "Stop"
Set-Location "$project"
New-Item -ItemType Directory -Force -Path "$logDir" | Out-Null
& "$venvPython" -m streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1 *>> "$logDir\dashboard.log"
"@ | Set-Content -Path $dashboardRunner -Encoding UTF8

Write-Step "Configuring persistence for daemon..."
$daemonPersistence = Ensure-PersistentRunner -TaskName "PyTradeDaemon" -RunnerScriptPath $daemonRunner -StartupShortcutName "PyTradeDaemon Startup" -ProjectRoot $project

$dashboardPersistence = "disabled"
if ($InstallDashboardTask) {
    Write-Step "Configuring persistence for dashboard..."
    $dashboardPersistence = Ensure-PersistentRunner -TaskName "PyTradeDashboard" -RunnerScriptPath $dashboardRunner -StartupShortcutName "PyTradeDashboard Startup" -ProjectRoot $project
}

$quickStartBat = Join-Path $project "Quick-Start.bat"
$projectIconPath = Join-Path $project "assets\pytrade.ico"
$defaultIconDll = Join-Path $env:SystemRoot "System32\imageres.dll"
$startShortcutIcon = if (Test-Path $projectIconPath) { "$projectIconPath,0" } elseif (Test-Path $venvPython) { "$venvPython,0" } elseif (Test-Path $defaultIconDll) { "$defaultIconDll,13" } else { "" }
$dashboardIconFile = if (Test-Path $projectIconPath) { $projectIconPath } elseif (Test-Path $defaultIconDll) { $defaultIconDll } else { "" }
$dashboardIconIndex = if (Test-Path $projectIconPath) { 0 } else { 13 }

New-DesktopShortcutSafe -Name "PyTrade Start" -TargetPath $quickStartBat -WorkingDirectory $project -IconLocation $startShortcutIcon
New-DesktopUrlShortcutSafe -Name "PyTrade Dashboard" -Url "http://localhost:8501" -IconFile $dashboardIconFile -IconIndex $dashboardIconIndex

Write-Host ""
Write-Host "Install complete." -ForegroundColor Green
Write-Host "Python              : $pythonCmd"
Write-Host "Daemon persistence  : $daemonPersistence"
if ($InstallDashboardTask) {
    Write-Host "Dashboard persistence: $dashboardPersistence"
}
Write-Host "Logs                : $logDir"
Write-Host "Dashboard URL       : http://localhost:8501"
