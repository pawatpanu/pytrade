param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$InstallerPath = ""
)

$ErrorActionPreference = "Stop"

function Resolve-LatestInstaller([string]$OutputDir) {
    $candidate = Get-ChildItem $OutputDir -Filter "PyTradeSetup-*.exe" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $candidate) {
        throw "No installer executable found in $OutputDir"
    }
    return $candidate.FullName
}

$project = Resolve-Path $ProjectRoot
$outputDir = Join-Path $project "installer\output"
if (-not (Test-Path $outputDir)) {
    throw "Output directory not found: $outputDir"
}

if ([string]::IsNullOrWhiteSpace($InstallerPath)) {
    $installer = Resolve-LatestInstaller $outputDir
} else {
    $installer = (Resolve-Path $InstallerPath).Path
}

$installerName = [System.IO.Path]::GetFileNameWithoutExtension($installer)
$stamp = $installerName.Replace("PyTradeSetup-", "")
$releaseNotes = Join-Path $outputDir ("RELEASE-NOTES-{0}.md" -f $stamp)
$releaseZip = Join-Path $outputDir ("PyTrade-Release-{0}.zip" -f $stamp)
$tempDir = Join-Path $outputDir ("package-{0}" -f $stamp)

if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "docs") | Out-Null

$git = Get-Command git.exe -ErrorAction SilentlyContinue
$commit = "unknown"
if ($git) {
    try { $commit = (& $git.Source -C $project rev-parse --short HEAD).Trim() } catch {}
}
$builtAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

$releaseText = @"
# PyTrade Release $stamp

Build time: $builtAt
Git commit: $commit
Installer: $(Split-Path $installer -Leaf)

## Highlights
- Windows GUI installer (Next > Next > Finish)
- Installer bootstraps Python 3.11 via winget when Python is missing
- Creates .venv and installs project dependencies automatically
- Streamlit control center with dashboard, health checks, support bundle, and quick actions
- MT5 signal scanner, notifier, execution flow, and account-aware database switching
- Batch launcher utilities for dashboard, daemon, sync, scan, restart, and logs

## Important notes
- MetaTrader 5 must still be installed and logged in on the destination machine
- The installer package excludes your real .env and runtime databases for safety
- Review .env settings after install before enabling live execution

## Included files
- Installer executable
- README.md
- docs/INSTALL_WINDOWS_TH.md
- docs/USER_GUIDE_TH.md
"@

Set-Content -Path $releaseNotes -Value $releaseText -Encoding UTF8
Copy-Item $installer -Destination (Join-Path $tempDir (Split-Path $installer -Leaf)) -Force
Copy-Item $releaseNotes -Destination (Join-Path $tempDir (Split-Path $releaseNotes -Leaf)) -Force
Copy-Item (Join-Path $project "README.md") -Destination (Join-Path $tempDir "README.md") -Force
Copy-Item (Join-Path $project "docs\INSTALL_WINDOWS_TH.md") -Destination (Join-Path $tempDir "docs\INSTALL_WINDOWS_TH.md") -Force
Copy-Item (Join-Path $project "docs\USER_GUIDE_TH.md") -Destination (Join-Path $tempDir "docs\USER_GUIDE_TH.md") -Force

if (Test-Path $releaseZip) {
    Remove-Item $releaseZip -Force
}
Compress-Archive -Path (Join-Path $tempDir "*") -DestinationPath $releaseZip -CompressionLevel Optimal
Remove-Item $tempDir -Recurse -Force

Write-Host "Release notes : $releaseNotes" -ForegroundColor Green
Write-Host "Release zip   : $releaseZip" -ForegroundColor Green
