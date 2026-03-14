param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$PythonLauncher = "",
    [switch]$InstallDashboardTask = $true
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$msg) {
    Write-Host "[PyTrade Installer] $msg" -ForegroundColor Cyan
}

function Resolve-PythonCommand([string]$PreferredLauncher) {
    $candidates = @()
    if ($PreferredLauncher) { $candidates += $PreferredLauncher }
    $candidates += @("py", "python")

    foreach ($cmd in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($cmd)) {
            $resolved = Get-Command $cmd -ErrorAction SilentlyContinue
            if ($resolved) { return $resolved.Source }
        }
    }

    $knownPython = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe",
        "$env:ProgramFiles\Python312\python.exe"
    )
    foreach ($path in $knownPython) {
        if (Test-Path $path) { return $path }
    }

    return $null
}

function Install-PythonIfMissing {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Python was not found and winget is unavailable. Please install Python 3.11+ manually."
    }

    Write-Step "Python not found. Installing Python 3.11 via winget..."
    & $winget.Source install --id Python.Python.3.11 -e --source winget --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) {
        throw "winget failed to install Python 3.11."
    }

    Start-Sleep -Seconds 5
    $resolved = Resolve-PythonCommand ""
    if (-not $resolved) {
        throw "Python installation completed but python executable was not found."
    }
    return $resolved
}

$project = Resolve-Path $ProjectRoot
$venvDir = Join-Path $project ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$envFile = Join-Path $project ".env"
$envExample = Join-Path $project ".env.example"
$logDir = Join-Path $project "logs"
$runtimeDir = Join-Path $project ".runtime"
$daemonRunner = Join-Path $PSScriptRoot "run_daemon.ps1"
$dashboardRunner = Join-Path $PSScriptRoot "run_dashboard.ps1"

Write-Step "Project root: $project"

$pythonCmd = Resolve-PythonCommand $PythonLauncher
if (-not $pythonCmd) {
    $pythonCmd = Install-PythonIfMissing
}

if (-not (Test-Path $venvPython)) {
    Write-Step "Creating virtual environment..."
    & $pythonCmd -m venv $venvDir
}

Write-Step "Installing dependencies..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $project "requirements.txt")

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
schtasks /Create /F /SC ONLOGON /TN "PyTradeDaemon" /TR "powershell -NoProfile -ExecutionPolicy Bypass -File `"$daemonRunner`"" | Out-Null

if ($InstallDashboardTask) {
    Write-Step "Registering scheduled task: PyTradeDashboard"
    schtasks /Create /F /SC ONLOGON /TN "PyTradeDashboard" /TR "powershell -NoProfile -ExecutionPolicy Bypass -File `"$dashboardRunner`"" | Out-Null
}

Write-Step "Starting daemon task now..."
schtasks /Run /TN "PyTradeDaemon" | Out-Null

if ($InstallDashboardTask) {
    Write-Step "Starting dashboard task now..."
    schtasks /Run /TN "PyTradeDashboard" | Out-Null
}

Write-Host ""
Write-Host "Install complete." -ForegroundColor Green
Write-Host "Python         : $pythonCmd"
Write-Host "Daemon task    : PyTradeDaemon"
if ($InstallDashboardTask) {
    Write-Host "Dashboard task : PyTradeDashboard"
}
Write-Host "Logs           : $logDir"
Write-Host "Dashboard URL  : http://localhost:8501"
