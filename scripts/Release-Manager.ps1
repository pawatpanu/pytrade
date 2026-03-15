param(
    [string]$SearchRoot = $PSScriptRoot,
    [string]$DefaultInstallDir = "C:\pytrade"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-ReleaseManifestFromZip([string]$ZipPath) {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        $entry = $zip.Entries | Where-Object { $_.FullName -ieq 'release_manifest.json' } | Select-Object -First 1
        if ($entry) {
            $reader = New-Object System.IO.StreamReader($entry.Open())
            try {
                return ($reader.ReadToEnd() | ConvertFrom-Json)
            }
            finally {
                $reader.Dispose()
            }
        }
    }
    finally {
        $zip.Dispose()
    }

    $fallback = [System.IO.Path]::GetFileNameWithoutExtension($ZipPath).Replace('PyTrade-Release-', '')
    return [pscustomobject]@{
        version = $fallback
        build_stamp = $fallback
        git_commit = 'unknown'
        installer_file = "PyTradeSetup-$fallback.exe"
        package_type = 'pytrade_release'
    }
}

function Get-ReleaseCandidates([string]$RootPath) {
    $all = @()
    $searchPaths = @($RootPath)
    $parent = Split-Path $RootPath -Parent
    if ($parent -and $parent -ne $RootPath) {
        $searchPaths += $parent
    }

    foreach ($path in $searchPaths | Select-Object -Unique) {
        if (-not (Test-Path $path)) { continue }
        $zips = Get-ChildItem -Path $path -Filter 'PyTrade-Release-*.zip' -File -ErrorAction SilentlyContinue
        foreach ($zip in $zips) {
            $manifest = Get-ReleaseManifestFromZip $zip.FullName
            $all += [pscustomobject]@{
                source_type = 'zip'
                source_path = $zip.FullName
                version = [string]$manifest.version
                build_stamp = [string]$manifest.build_stamp
                git_commit = [string]$manifest.git_commit
                installer_file = [string]$manifest.installer_file
            }
        }
    }

    $localManifest = Join-Path $RootPath 'release_manifest.json'
    if (Test-Path $localManifest) {
        $manifest = Get-Content $localManifest -Raw -Encoding UTF8 | ConvertFrom-Json
        $all += [pscustomobject]@{
            source_type = 'folder'
            source_path = $RootPath
            version = [string]$manifest.version
            build_stamp = [string]$manifest.build_stamp
            git_commit = [string]$manifest.git_commit
            installer_file = [string]$manifest.installer_file
        }
    }

    return $all | Sort-Object build_stamp -Descending -Unique version
}

function Invoke-InstallFromCandidate($Candidate, [string]$InstallDir) {
    if ($Candidate.source_type -eq 'folder') {
        $installer = Join-Path $Candidate.source_path $Candidate.installer_file
        if (-not (Test-Path $installer)) {
            throw "Installer not found: $installer"
        }
        Start-Process -FilePath $installer -ArgumentList "/DIR=$InstallDir" -Wait
        return
    }

    $tempDir = Join-Path $env:TEMP ("pytrade_release_" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    try {
        Expand-Archive -Path $Candidate.source_path -DestinationPath $tempDir -Force
        $installer = Join-Path $tempDir $Candidate.installer_file
        if (-not (Test-Path $installer)) {
            $fallback = Get-ChildItem -Path $tempDir -Filter 'PyTradeSetup-*.exe' -File | Select-Object -First 1
            if ($fallback) {
                $installer = $fallback.FullName
            }
        }
        if (-not (Test-Path $installer)) {
            throw "Installer not found inside package: $($Candidate.source_path)"
        }
        Start-Process -FilePath $installer -ArgumentList "/DIR=$InstallDir" -Wait
    }
    finally {
        if (Test-Path $tempDir) {
            Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

$candidates = Get-ReleaseCandidates -RootPath $SearchRoot
if (-not $candidates -or $candidates.Count -eq 0) {
    Write-Host 'No release packages found.' -ForegroundColor Yellow
    Write-Host 'Place multiple PyTrade-Release-*.zip files in one folder, then run this script again.' -ForegroundColor Yellow
    exit 1
}

Write-Host ''
Write-Host 'Available PyTrade versions' -ForegroundColor Cyan
Write-Host '==========================' -ForegroundColor Cyan
for ($i = 0; $i -lt $candidates.Count; $i++) {
    $c = $candidates[$i]
    $src = if ($c.source_type -eq 'folder') { 'extracted' } else { 'zip' }
    Write-Host ("[{0}] {1}  commit={2}  source={3}" -f ($i + 1), $c.version, $c.git_commit, $src)
}
Write-Host ''
Write-Host 'Tip: install newer version = update, install older version = rollback' -ForegroundColor DarkGray
$choice = Read-Host 'Choose version number to install'
if (-not ($choice -as [int])) {
    throw 'Invalid choice.'
}
$index = [int]$choice - 1
if ($index -lt 0 -or $index -ge $candidates.Count) {
    throw 'Choice out of range.'
}
$selected = $candidates[$index]
Write-Host ("Installing version {0} ..." -f $selected.version) -ForegroundColor Cyan
Invoke-InstallFromCandidate -Candidate $selected -InstallDir $DefaultInstallDir
Write-Host ("Install complete: {0}" -f $selected.version) -ForegroundColor Green
