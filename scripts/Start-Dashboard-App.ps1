param(
    [Parameter(Mandatory = $true)]
    [string]$Url
)

$ErrorActionPreference = "Stop"

$edgeCandidates = @(
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    (Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"),
    (Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe")
)

# Registry App Paths fallback
try {
    $reg = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe" -ErrorAction Stop
    $regPath = $reg."(default)"
    if ($regPath) { $edgeCandidates += [string]$regPath }
} catch {}

# PATH fallback
try {
    $where = (where.exe msedge 2>$null | Select-Object -First 1)
    if ($where) { $edgeCandidates += [string]$where }
} catch {}

$edgeExe = $edgeCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $edgeExe) {
    Write-Error "Microsoft Edge not found."
    exit 1
}

$p = Start-Process -FilePath $edgeExe -ArgumentList @("--new-window", "--app=$Url", "--disable-background-mode", "--no-first-run", "--no-default-browser-check", "--user-data-dir=$env:TEMP\PyTradeEdgeDashboardProfile") -PassThru
if (-not $p) {
    Write-Error "Failed to start Edge app window."
    exit 1
}

Write-Output $p.Id
exit 0
