param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$MT5Path = "",
    [string]$MT5Login = "",
    [string]$MT5Password = "",
    [string]$MT5Server = "",
    [string]$Symbols = "",
    [ValidateSet("aggressive", "balanced", "premium", "ultra_premium")]
    [string]$Preset = "balanced",
    [string]$TelegramEnabled = "",
    [string]$TelegramToken = "",
    [string]$TelegramChatId = "",
    [string]$RiskPerTradePct = "",
    [string]$DailyLossLimit = "",
    [string]$MaxOpenPositions = "",
    [string]$OrderCooldownMinutes = "",
    [string]$MinExecuteCategory = "",
    [string]$WatchlistThreshold = "",
    [string]$AlertThreshold = "",
    [string]$StrongAlertThreshold = "",
    [string]$PremiumAlertThreshold = "",
    [string]$MinAlertCategory = "",
    [string]$EnableSmartExit = "",
    [string]$EnableBreakEven = "",
    [string]$BreakEvenTriggerR = "",
    [string]$BreakEvenLockR = "",
    [string]$EnableTrailingStop = "",
    [string]$TrailingStartR = "",
    [string]$TrailingDistanceR = "",
    [string]$EnablePartialClose = "",
    [string]$PartialCloseTriggerR = "",
    [string]$PartialCloseRatio = "",
    [string]$EnablePremiumStack = "",
    [string]$PremiumStackExtraSlots = "",
    [string]$EnableUltraStack = "",
    [string]$UltraStackScore = "",
    [string]$UltraStackExtraSlots = "",
    [string]$ScanIntervalSeconds = "",
    [string]$SyncIntervalSeconds = "",
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"

function Read-Default([string]$prompt, [string]$defaultValue) {
    $v = Read-Host "$prompt [$defaultValue]"
    if ([string]::IsNullOrWhiteSpace($v)) { return $defaultValue }
    return $v.Trim()
}

function Upsert-EnvKey([string]$path, [string]$key, [string]$value) {
    $lines = @()
    if (Test-Path $path) { $lines = Get-Content $path -Encoding UTF8 }
    $found = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i].Trim()
        if ($line.StartsWith("$key=")) {
            $lines[$i] = "$key=$value"
            $found = $true
            break
        }
    }
    if (-not $found) { $lines += "$key=$value" }
    Set-Content -Path $path -Encoding UTF8 -Value $lines
}

$project = Resolve-Path $ProjectRoot
$envPath = Join-Path $project ".env"
$envExample = Join-Path $project ".env.example"
$installScript = Join-Path $PSScriptRoot "install_windows.ps1"

if (-not (Test-Path $envPath) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envPath
}
if (-not (Test-Path $envPath)) {
    throw ".env not found and .env.example not found."
}

Write-Host "[PyTrade] One-click installer" -ForegroundColor Cyan

$defaultMt5Path = "C:\Program Files\MetaTrader 5\terminal64.exe"
if ($MT5Path) {
    $mt5Path = $MT5Path
} elseif ($NonInteractive) {
    $mt5Path = $defaultMt5Path
} else {
    $mt5Path = Read-Default "MT5_PATH" $defaultMt5Path
}

if (-not $MT5Login -and -not $NonInteractive) { $MT5Login = Read-Default "MT5_LOGIN" "" }
if (-not $MT5Password -and -not $NonInteractive) { $MT5Password = Read-Host "MT5_PASSWORD" }
if (-not $MT5Server -and -not $NonInteractive) { $MT5Server = Read-Default "MT5_SERVER" "" }
if (-not $Symbols -and -not $NonInteractive) { $Symbols = Read-Default "SYMBOLS" "BTCUSD,ETHUSD,XAUUSD" }
if (-not $Symbols) { $Symbols = "BTCUSD,ETHUSD,XAUUSD" }
if (-not $Preset -and -not $NonInteractive) { $Preset = Read-Default "Preset (aggressive/balanced/premium/ultra_premium)" "balanced" }

Upsert-EnvKey $envPath "MT5_PATH" $mt5Path
Upsert-EnvKey $envPath "MT5_LOGIN" $MT5Login
Upsert-EnvKey $envPath "MT5_PASSWORD" $MT5Password
Upsert-EnvKey $envPath "MT5_SERVER" $MT5Server
Upsert-EnvKey $envPath "SYMBOLS" $Symbols
Upsert-EnvKey $envPath "DRY_RUN" "false"
Upsert-EnvKey $envPath "ENABLE_EXECUTION" "true"
Upsert-EnvKey $envPath "EXECUTION_MODE" "demo"

if ($TelegramEnabled) { Upsert-EnvKey $envPath "TELEGRAM_ENABLED" $TelegramEnabled }
if ($TelegramToken) { Upsert-EnvKey $envPath "TELEGRAM_TOKEN" $TelegramToken }
if ($TelegramChatId) { Upsert-EnvKey $envPath "TELEGRAM_CHAT_ID" $TelegramChatId }
if ($RiskPerTradePct) { Upsert-EnvKey $envPath "RISK_PER_TRADE_PCT" $RiskPerTradePct }
if ($DailyLossLimit) { Upsert-EnvKey $envPath "DAILY_LOSS_LIMIT" $DailyLossLimit }
if ($MaxOpenPositions) { Upsert-EnvKey $envPath "MAX_OPEN_POSITIONS" $MaxOpenPositions }
if ($OrderCooldownMinutes) { Upsert-EnvKey $envPath "ORDER_COOLDOWN_MINUTES" $OrderCooldownMinutes }
if ($MinExecuteCategory) { Upsert-EnvKey $envPath "MIN_EXECUTE_CATEGORY" $MinExecuteCategory }
if ($WatchlistThreshold) { Upsert-EnvKey $envPath "WATCHLIST_THRESHOLD" $WatchlistThreshold }
if ($AlertThreshold) { Upsert-EnvKey $envPath "ALERT_THRESHOLD" $AlertThreshold }
if ($StrongAlertThreshold) { Upsert-EnvKey $envPath "STRONG_ALERT_THRESHOLD" $StrongAlertThreshold }
if ($PremiumAlertThreshold) { Upsert-EnvKey $envPath "PREMIUM_ALERT_THRESHOLD" $PremiumAlertThreshold }
if ($MinAlertCategory) { Upsert-EnvKey $envPath "MIN_ALERT_CATEGORY" $MinAlertCategory }
if ($EnableSmartExit) { Upsert-EnvKey $envPath "ENABLE_SMART_EXIT" $EnableSmartExit }
if ($EnableBreakEven) { Upsert-EnvKey $envPath "ENABLE_BREAK_EVEN" $EnableBreakEven }
if ($BreakEvenTriggerR) { Upsert-EnvKey $envPath "BREAK_EVEN_TRIGGER_R" $BreakEvenTriggerR }
if ($BreakEvenLockR) { Upsert-EnvKey $envPath "BREAK_EVEN_LOCK_R" $BreakEvenLockR }
if ($EnableTrailingStop) { Upsert-EnvKey $envPath "ENABLE_TRAILING_STOP" $EnableTrailingStop }
if ($TrailingStartR) { Upsert-EnvKey $envPath "TRAILING_START_R" $TrailingStartR }
if ($TrailingDistanceR) { Upsert-EnvKey $envPath "TRAILING_DISTANCE_R" $TrailingDistanceR }
if ($EnablePartialClose) { Upsert-EnvKey $envPath "ENABLE_PARTIAL_CLOSE" $EnablePartialClose }
if ($PartialCloseTriggerR) { Upsert-EnvKey $envPath "PARTIAL_CLOSE_TRIGGER_R" $PartialCloseTriggerR }
if ($PartialCloseRatio) { Upsert-EnvKey $envPath "PARTIAL_CLOSE_RATIO" $PartialCloseRatio }
if ($EnablePremiumStack) { Upsert-EnvKey $envPath "ENABLE_PREMIUM_STACK" $EnablePremiumStack }
if ($PremiumStackExtraSlots) { Upsert-EnvKey $envPath "PREMIUM_STACK_EXTRA_SLOTS" $PremiumStackExtraSlots }
if ($EnableUltraStack) { Upsert-EnvKey $envPath "ENABLE_ULTRA_STACK" $EnableUltraStack }
if ($UltraStackScore) { Upsert-EnvKey $envPath "ULTRA_STACK_SCORE" $UltraStackScore }
if ($UltraStackExtraSlots) { Upsert-EnvKey $envPath "ULTRA_STACK_EXTRA_SLOTS" $UltraStackExtraSlots }
if ($ScanIntervalSeconds) { Upsert-EnvKey $envPath "SCAN_INTERVAL_SECONDS" $ScanIntervalSeconds }
if ($SyncIntervalSeconds) { Upsert-EnvKey $envPath "SYNC_INTERVAL_SECONDS" $SyncIntervalSeconds }

switch ($Preset.ToLower()) {
    "aggressive" {
        Upsert-EnvKey $envPath "HARD_FILTER_MODE" "soft"
        Upsert-EnvKey $envPath "ADX_MINIMUM" "12"
        Upsert-EnvKey $envPath "M5_MIN_TRIGGERS" "1"
        Upsert-EnvKey $envPath "WATCHLIST_THRESHOLD" "35"
        Upsert-EnvKey $envPath "ALERT_THRESHOLD" "45"
        Upsert-EnvKey $envPath "STRONG_ALERT_THRESHOLD" "55"
        Upsert-EnvKey $envPath "PREMIUM_ALERT_THRESHOLD" "65"
        Upsert-EnvKey $envPath "MIN_EXECUTE_CATEGORY" "alert"
    }
    "premium" {
        Upsert-EnvKey $envPath "HARD_FILTER_MODE" "strict"
        Upsert-EnvKey $envPath "ADX_MINIMUM" "18"
        Upsert-EnvKey $envPath "M5_MIN_TRIGGERS" "2"
        Upsert-EnvKey $envPath "WATCHLIST_THRESHOLD" "65"
        Upsert-EnvKey $envPath "ALERT_THRESHOLD" "75"
        Upsert-EnvKey $envPath "STRONG_ALERT_THRESHOLD" "85"
        Upsert-EnvKey $envPath "PREMIUM_ALERT_THRESHOLD" "90"
        Upsert-EnvKey $envPath "MIN_EXECUTE_CATEGORY" "premium"
    }
    "ultra_premium" {
        Upsert-EnvKey $envPath "HARD_FILTER_MODE" "strict"
        Upsert-EnvKey $envPath "ADX_MINIMUM" "22"
        Upsert-EnvKey $envPath "M5_MIN_TRIGGERS" "3"
        Upsert-EnvKey $envPath "WATCHLIST_THRESHOLD" "75"
        Upsert-EnvKey $envPath "ALERT_THRESHOLD" "85"
        Upsert-EnvKey $envPath "STRONG_ALERT_THRESHOLD" "90"
        Upsert-EnvKey $envPath "PREMIUM_ALERT_THRESHOLD" "94"
        Upsert-EnvKey $envPath "MIN_EXECUTE_CATEGORY" "premium"
    }
    Default {
        Upsert-EnvKey $envPath "HARD_FILTER_MODE" "soft"
        Upsert-EnvKey $envPath "ADX_MINIMUM" "16"
        Upsert-EnvKey $envPath "M5_MIN_TRIGGERS" "2"
        Upsert-EnvKey $envPath "WATCHLIST_THRESHOLD" "45"
        Upsert-EnvKey $envPath "ALERT_THRESHOLD" "55"
        Upsert-EnvKey $envPath "STRONG_ALERT_THRESHOLD" "65"
        Upsert-EnvKey $envPath "PREMIUM_ALERT_THRESHOLD" "75"
        Upsert-EnvKey $envPath "MIN_EXECUTE_CATEGORY" "strong"
    }
}

& powershell -ExecutionPolicy Bypass -File $installScript -ProjectRoot $project

$venvPython = Join-Path $project ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython main.py --mode reset_loss_guard
    & $venvPython main.py --mode sync
}

Write-Host "Install completed. Open: http://localhost:8501" -ForegroundColor Green
