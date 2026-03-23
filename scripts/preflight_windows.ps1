param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$Quiet,
    [string]$ReportPath = ""
)

$ErrorActionPreference = "Stop"

$script:Errors = New-Object System.Collections.Generic.List[string]
$script:Warnings = New-Object System.Collections.Generic.List[string]
$script:Results = New-Object System.Collections.Generic.List[object]

function Add-Result([string]$Level, [string]$Message) {
    $script:Results.Add([PSCustomObject]@{
        level = $Level
        message = $Message
    }) | Out-Null
}

function Add-Error([string]$msg) {
    $script:Errors.Add($msg)
    Add-Result "FAIL" $msg
    if (-not $Quiet) { Write-Host "[FAIL] $msg" -ForegroundColor Red }
}

function Add-Warning([string]$msg) {
    $script:Warnings.Add($msg)
    Add-Result "WARN" $msg
    if (-not $Quiet) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
}

function Add-Ok([string]$msg) {
    Add-Result "OK" $msg
    if (-not $Quiet) { Write-Host "[OK]   $msg" -ForegroundColor Green }
}

function Test-WriteAccess([string]$DirPath) {
    try {
        if (-not (Test-Path $DirPath)) {
            New-Item -ItemType Directory -Path $DirPath -Force | Out-Null
        }
        $probe = Join-Path $DirPath (".preflight_write_test_" + [Guid]::NewGuid().ToString("N") + ".tmp")
        Set-Content -Path $probe -Value "ok" -Encoding ASCII
        Remove-Item -Path $probe -Force -ErrorAction SilentlyContinue
        return $true
    }
    catch {
        return $false
    }
}

function Resolve-PythonCommand {
    $commands = @("py", "python")
    foreach ($cmd in $commands) {
        $resolved = Get-Command $cmd -ErrorAction SilentlyContinue
        if (-not $resolved) { continue }
        $src = $resolved.Source
        if ([string]::IsNullOrWhiteSpace($src)) { continue }
        if ($src -match "WindowsApps") { continue }
        try {
            & $src -c "import sys; print(sys.version_info[0], sys.version_info[1])" > $null 2>&1
            if ($LASTEXITCODE -eq 0) { return $src }
        }
        catch {
        }
    }

    $knownPython = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe",
        "$env:ProgramFiles\Python312\python.exe"
    )
    foreach ($path in $knownPython) {
        if (-not (Test-Path $path)) { continue }
        try {
            & $path -c "import sys; print(sys.version_info[0], sys.version_info[1])" > $null 2>&1
            if ($LASTEXITCODE -eq 0) { return $path }
        }
        catch {
        }
    }

    return $null
}

function Test-HttpReachable([string]$Url) {
    try {
        $null = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec 8 -UseBasicParsing
        return $true
    }
    catch {
        return $false
    }
}

function Resolve-ReportPath([string]$RootPath, [string]$UserPath) {
    if (-not [string]::IsNullOrWhiteSpace($UserPath)) {
        return $UserPath
    }
    return (Join-Path $RootPath "logs\preflight_report_latest.txt")
}

function Write-Report([string]$PathToWrite, [string]$RootPath, [int]$ExitCode) {
    try {
        $reportDir = Split-Path -Path $PathToWrite -Parent
        if (-not [string]::IsNullOrWhiteSpace($reportDir) -and -not (Test-Path $reportDir)) {
            New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
        }

        $lines = New-Object System.Collections.Generic.List[string]
        $lines.Add("PyTrade Preflight Report") | Out-Null
        $lines.Add("Generated: $([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss zzz'))") | Out-Null
        $lines.Add("Project  : $RootPath") | Out-Null
        $lines.Add("Result   : $(if ($ExitCode -eq 0) { 'PASS' } else { 'FAIL' })") | Out-Null
        $lines.Add("Errors   : $($script:Errors.Count)") | Out-Null
        $lines.Add("Warnings : $($script:Warnings.Count)") | Out-Null
        $lines.Add("") | Out-Null
        $lines.Add("Checks") | Out-Null
        $lines.Add("------") | Out-Null
        foreach ($r in $script:Results) {
            $lines.Add("[$($r.level)] $($r.message)") | Out-Null
        }

        Set-Content -Path $PathToWrite -Value $lines -Encoding UTF8
        if (-not $Quiet) {
            Write-Host "Report saved: $PathToWrite" -ForegroundColor Gray
        }
    }
    catch {
        if (-not $Quiet) {
            Write-Host "[WARN] Failed to write report: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

$project = ""
try {
    $project = (Resolve-Path $ProjectRoot).Path
}
catch {
    $project = $ProjectRoot
    Add-Error "Project root not found: $ProjectRoot"
}

if (-not $Quiet) {
    Write-Host "========================================" -ForegroundColor Gray
    Write-Host "PyTrade Preflight Check" -ForegroundColor White
    Write-Host "Root: $project" -ForegroundColor Gray
    Write-Host "========================================" -ForegroundColor Gray
}

if ($PSVersionTable.PSVersion.Major -lt 5) {
    Add-Error "PowerShell 5+ is required. Current: $($PSVersionTable.PSVersion)"
} else {
    Add-Ok "PowerShell version $($PSVersionTable.PSVersion)"
}

if (Test-WriteAccess $project) {
    Add-Ok "Project directory writable"
} else {
    Add-Error "No write permission to project directory: $project"
}

$logsDir = Join-Path $project "logs"
if (Test-WriteAccess $logsDir) {
    Add-Ok "Logs directory writable"
} else {
    Add-Error "Cannot write to logs directory: $logsDir"
}

$taskService = Get-Service -Name "Schedule" -ErrorAction SilentlyContinue
if (-not $taskService) {
    Add-Error "Task Scheduler service not found (Schedule)."
} elseif ($taskService.Status -ne "Running") {
    Add-Error "Task Scheduler service is not running."
} else {
    Add-Ok "Task Scheduler service running"
}

$pythonCmd = Resolve-PythonCommand
if ($pythonCmd) {
    Add-Ok "Python detected: $pythonCmd"
} else {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Add-Warning "Python not found now. Installer will try winget auto-install."
    } else {
        Add-Error "Python not found and winget is unavailable. Install Python 3.11+ first."
    }
}

$pipReachable = Test-HttpReachable "https://pypi.org/simple/pip/"
if ($pipReachable) {
    Add-Ok "Network access to PyPI is available"
} else {
    Add-Warning "Cannot reach PyPI now. Dependency install may fail without internet/proxy setup."
}

$envPath = Join-Path $project ".env"
$envExample = Join-Path $project ".env.example"
if ((Test-Path $envPath) -or (Test-Path $envExample)) {
    Add-Ok ".env source available"
} else {
    Add-Error "Both .env and .env.example are missing."
}

$mt5Path = $null
if (Test-Path $envPath) {
    $line = Get-Content $envPath | Where-Object { $_ -match '^MT5_PATH=' } | Select-Object -First 1
    if ($line) {
        $mt5Path = ($line -replace '^MT5_PATH=', '').Trim()
    }
}
if ([string]::IsNullOrWhiteSpace($mt5Path)) {
    Add-Warning "MT5_PATH is not set yet in .env"
} elseif (Test-Path $mt5Path) {
    Add-Ok "MT5_PATH exists"
} else {
    Add-Warning "MT5_PATH does not exist: $mt5Path"
}

$portBusy = $false
try {
    $listeners = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
    $portBusy = $listeners -and $listeners.Count -gt 0
}
catch {
    $netstatHit = netstat -ano | Select-String -Pattern ':8501\s+LISTENING'
    $portBusy = [bool]$netstatHit
}
if ($portBusy) {
    Add-Warning "Port 8501 is already in use. Dashboard task may fail to start."
} else {
    Add-Ok "Port 8501 is available"
}

$exitCode = 0
if ($Errors.Count -gt 0) {
    $exitCode = 2
}

$finalReportPath = Resolve-ReportPath -RootPath $project -UserPath $ReportPath
Write-Report -PathToWrite $finalReportPath -RootPath $project -ExitCode $exitCode

if (-not $Quiet) {
    Write-Host ""
    Write-Host "Preflight Summary" -ForegroundColor White
    Write-Host "- Errors  : $($Errors.Count)"
    Write-Host "- Warnings: $($Warnings.Count)"
}

exit $exitCode
