param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

function Resolve-IsccPath {
    $candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$iscc = Resolve-IsccPath
if (-not $iscc) {
    throw "Inno Setup Compiler (ISCC.exe) was not found. Please install Inno Setup 6 first."
}

$issPath = Join-Path $ProjectRoot "installer\PyTradeSetup.iss"
if (-not (Test-Path $issPath)) {
    throw "Installer script not found: $issPath"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputName = "PyTradeSetup-$stamp"

Push-Location (Split-Path $issPath -Parent)
try {
    & $iscc "/DOutputName=$outputName" $issPath
}
finally {
    Pop-Location
}

$outPath = Join-Path $ProjectRoot ("installer\output\{0}.exe" -f $outputName)
if (Test-Path $outPath) {
    Write-Host "Build success: $outPath" -ForegroundColor Green
} else {
    Write-Warning "Compile finished but output file was not found at expected path: $outPath"
}
