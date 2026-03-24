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
        [string]$Url
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
            @"
[InternetShortcut]
URL=$Url
"@ | Set-Content -Path $shortcutPath -Encoding ASCII
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

Write-Step "Registering scheduled task: PyTradeDaemon"
Invoke-ExternalChecked -FilePath "schtasks.exe" -Arguments @("/Create", "/F", "/SC", "ONLOGON", "/TN", "PyTradeDaemon", "/TR", "powershell -NoProfile -ExecutionPolicy Bypass -File `"$daemonRunner`"") -FailureMessage "Failed to create scheduled task PyTradeDaemon"

if ($InstallDashboardTask) {
    Write-Step "Registering scheduled task: PyTradeDashboard"
    Invoke-ExternalChecked -FilePath "schtasks.exe" -Arguments @("/Create", "/F", "/SC", "ONLOGON", "/TN", "PyTradeDashboard", "/TR", "powershell -NoProfile -ExecutionPolicy Bypass -File `"$dashboardRunner`"") -FailureMessage "Failed to create scheduled task PyTradeDashboard"
}

Write-Step "Starting daemon task now..."
Invoke-ExternalChecked -FilePath "schtasks.exe" -Arguments @("/Run", "/TN", "PyTradeDaemon") -FailureMessage "Failed to start PyTradeDaemon"

if ($InstallDashboardTask) {
    Write-Step "Starting dashboard task now..."
    Invoke-ExternalChecked -FilePath "schtasks.exe" -Arguments @("/Run", "/TN", "PyTradeDashboard") -FailureMessage "Failed to start PyTradeDashboard"
}

$quickStartBat = Join-Path $project "Quick-Start.bat"
New-DesktopShortcutSafe -Name "PyTrade Start" -TargetPath $quickStartBat -WorkingDirectory $project
New-DesktopUrlShortcutSafe -Name "PyTrade Dashboard" -Url "http://localhost:8501"

Write-Host ""
Write-Host "Install complete." -ForegroundColor Green
Write-Host "Python         : $pythonCmd"
Write-Host "Daemon task    : PyTradeDaemon"
if ($InstallDashboardTask) {
    Write-Host "Dashboard task : PyTradeDashboard"
}
Write-Host "Logs           : $logDir"
Write-Host "Dashboard URL  : http://localhost:8501"
