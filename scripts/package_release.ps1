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
$installerFile = Split-Path $installer -Leaf
$releaseNotesFile = Split-Path $releaseNotes -Leaf
$manifest = [ordered]@{
    package_type = "pytrade_release"
    version = $stamp
    build_stamp = $stamp
    built_at = $builtAt
    git_commit = $commit
    installer_file = $installerFile
    release_notes_file = $releaseNotesFile
    default_install_dir = "C:\pytrade"
    supports_upgrade = $true
    supports_rollback = $true
}

$releaseText = @"
# PyTrade Release $stamp

Build time: $builtAt
Git commit: $commit
Installer: $installerFile

## Highlights
- Windows GUI installer (Next > Next > Finish)
- Installer bootstraps Python 3.11 via winget when Python is missing
- Creates .venv and installs project dependencies automatically
- Streamlit control center with dashboard, health checks, support bundle, and quick actions
- MT5 signal scanner, notifier, execution flow, and account-aware database switching
- Batch launcher utilities for dashboard, daemon, sync, scan, restart, and logs
- Release Manager supports choosing a version to install/update/rollback

## Important notes
- MetaTrader 5 must still be installed and logged in on the destination machine
- The installer package excludes your real .env and runtime databases for safety
- Review .env settings after install before enabling live execution
- Upgrade = install a newer release package
- Rollback = install an older release package

## Included files
- Installer executable
- release_manifest.json
- Install-This-Version.bat
- Select-Version.bat
- Release-Manager.ps1
- README.md
- docs/INSTALL_WINDOWS_TH.md
- docs/USER_GUIDE_TH.md
"@

$installThisBat = @"
@echo off
setlocal
cd /d "%~dp0"
start "" "%~dp0$installerFile"
endlocal
"@

$selectVersionBat = @"
@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Release-Manager.ps1" -SearchRoot "%~dp0"
endlocal
"@

$releaseManager = @"
param(
    [string]`$SearchRoot = `$PSScriptRoot,
    [string]`$DefaultInstallDir = "C:\pytrade"
)

`$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-ReleaseManifestFromZip([string]`$ZipPath) {
    `$zip = [System.IO.Compression.ZipFile]::OpenRead(`$ZipPath)
    try {
        `$entry = `$zip.Entries | Where-Object { `$_.FullName -ieq 'release_manifest.json' } | Select-Object -First 1
        if (`$entry) {
            `$reader = New-Object System.IO.StreamReader(`$entry.Open())
            try {
                return (`$reader.ReadToEnd() | ConvertFrom-Json)
            }
            finally {
                `$reader.Dispose()
            }
        }
    }
    finally {
        `$zip.Dispose()
    }

    `$fallback = [System.IO.Path]::GetFileNameWithoutExtension(`$ZipPath).Replace('PyTrade-Release-', '')
    return [pscustomobject]@{
        version = `$fallback
        build_stamp = `$fallback
        git_commit = 'unknown'
        installer_file = "PyTradeSetup-`$fallback.exe"
        package_type = 'pytrade_release'
    }
}

function Get-ReleaseCandidates([string]`$RootPath) {
    `$all = @()
    `$searchPaths = @(`$RootPath)
    `$parent = Split-Path `$RootPath -Parent
    if (`$parent -and `$parent -ne `$RootPath) {
        `$searchPaths += `$parent
    }

    foreach (`$path in `$searchPaths | Select-Object -Unique) {
        if (-not (Test-Path `$path)) { continue }
        `$zips = Get-ChildItem -Path `$path -Filter 'PyTrade-Release-*.zip' -File -ErrorAction SilentlyContinue
        foreach (`$zip in `$zips) {
            `$manifest = Get-ReleaseManifestFromZip `$zip.FullName
            `$all += [pscustomobject]@{
                source_type = 'zip'
                source_path = `$zip.FullName
                version = [string]`$manifest.version
                build_stamp = [string]`$manifest.build_stamp
                git_commit = [string]`$manifest.git_commit
                installer_file = [string]`$manifest.installer_file
            }
        }
    }

    `$localManifest = Join-Path `$RootPath 'release_manifest.json'
    if (Test-Path `$localManifest) {
        `$manifest = Get-Content `$localManifest -Raw -Encoding UTF8 | ConvertFrom-Json
        `$all += [pscustomobject]@{
            source_type = 'folder'
            source_path = `$RootPath
            version = [string]`$manifest.version
            build_stamp = [string]`$manifest.build_stamp
            git_commit = [string]`$manifest.git_commit
            installer_file = [string]`$manifest.installer_file
        }
    }

    return `$all | Sort-Object build_stamp -Descending -Unique version
}

function Invoke-InstallFromCandidate(`$Candidate, [string]`$InstallDir) {
    if (`$Candidate.source_type -eq 'folder') {
        `$installer = Join-Path `$Candidate.source_path `$Candidate.installer_file
        if (-not (Test-Path `$installer)) {
            throw "Installer not found: `$installer"
        }
        Start-Process -FilePath `$installer -ArgumentList "/DIR=`$InstallDir" -Wait
        return
    }

    `$tempDir = Join-Path `$env:TEMP ("pytrade_release_" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path `$tempDir | Out-Null
    try {
        Expand-Archive -Path `$Candidate.source_path -DestinationPath `$tempDir -Force
        `$installer = Join-Path `$tempDir `$Candidate.installer_file
        if (-not (Test-Path `$installer)) {
            `$fallback = Get-ChildItem -Path `$tempDir -Filter 'PyTradeSetup-*.exe' -File | Select-Object -First 1
            if (`$fallback) {
                `$installer = `$fallback.FullName
            }
        }
        if (-not (Test-Path `$installer)) {
            throw "Installer not found inside package: `$(`$Candidate.source_path)"
        }
        Start-Process -FilePath `$installer -ArgumentList "/DIR=`$InstallDir" -Wait
    }
    finally {
        if (Test-Path `$tempDir) {
            Remove-Item `$tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

`$candidates = Get-ReleaseCandidates -RootPath `$SearchRoot
if (-not `$candidates -or `$candidates.Count -eq 0) {
    Write-Host 'No release packages found.' -ForegroundColor Yellow
    Write-Host 'Place multiple PyTrade-Release-*.zip files in one folder, then run this script again.' -ForegroundColor Yellow
    exit 1
}

Write-Host ''
Write-Host 'Available PyTrade versions' -ForegroundColor Cyan
Write-Host '==========================' -ForegroundColor Cyan
for (`$i = 0; `$i -lt `$candidates.Count; `$i++) {
    `$c = `$candidates[`$i]
    `$src = if (`$c.source_type -eq 'folder') { 'extracted' } else { 'zip' }
    Write-Host ("[`$(`$i + 1)] `$(`$c.version)  commit=`$(`$c.git_commit)  source=`$src")
}
Write-Host ''
Write-Host 'Tip: install newer version = update, install older version = rollback' -ForegroundColor DarkGray
`$choice = Read-Host 'Choose version number to install'
if (-not (`$choice -as [int])) {
    throw 'Invalid choice.'
}
`$index = [int]`$choice - 1
if (`$index -lt 0 -or `$index -ge `$candidates.Count) {
    throw 'Choice out of range.'
}
`$selected = `$candidates[`$index]
Write-Host ("Installing version `{0} ..." -f `$selected.version) -ForegroundColor Cyan
Invoke-InstallFromCandidate -Candidate `$selected -InstallDir `$DefaultInstallDir
Write-Host ("Install complete: `{0}" -f `$selected.version) -ForegroundColor Green
"@

Set-Content -Path $releaseNotes -Value $releaseText -Encoding UTF8
Set-Content -Path (Join-Path $tempDir $releaseNotesFile) -Value $releaseText -Encoding UTF8
$manifestJson = ConvertTo-Json $manifest -Depth 4
Set-Content -Path (Join-Path $tempDir "release_manifest.json") -Value $manifestJson -Encoding UTF8
Set-Content -Path (Join-Path $outputDir ("release_manifest_{0}.json" -f $stamp)) -Value $manifestJson -Encoding UTF8
Set-Content -Path (Join-Path $outputDir "release_manifest.json") -Value $manifestJson -Encoding UTF8
Set-Content -Path (Join-Path $tempDir "Install-This-Version.bat") -Value $installThisBat -Encoding ASCII
Set-Content -Path (Join-Path $tempDir "Select-Version.bat") -Value $selectVersionBat -Encoding ASCII
Set-Content -Path (Join-Path $tempDir "Release-Manager.ps1") -Value $releaseManager -Encoding UTF8
Copy-Item $installer -Destination (Join-Path $tempDir $installerFile) -Force
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
