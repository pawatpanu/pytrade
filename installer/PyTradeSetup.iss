#define MyAppName "PyTrade"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PyTrade"
#define MyAppExeName "scripts\\OneClick-Setup.bat"
#define AssetsDir "..\\installer\\assets"

#ifexist "{#AssetsDir}\\setup.ico"
  #define SetupIconPath "{#AssetsDir}\\setup.ico"
#endif
#ifexist "{#AssetsDir}\\wizard.bmp"
  #define WizardImagePath "{#AssetsDir}\\wizard.bmp"
#endif
#ifexist "{#AssetsDir}\\wizard_small.bmp"
  #define WizardSmallImagePath "{#AssetsDir}\\wizard_small.bmp"
#endif

[Setup]
AppId={{8C66D4E4-9D95-4BBF-9D2A-6A8A4A6A9A31}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName=C:\pytrade
DefaultGroupName=PyTrade
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=PyTradeSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
#ifdef SetupIconPath
SetupIconFile={#SetupIconPath}
#endif
#ifdef WizardImagePath
WizardImageFile={#WizardImagePath}
#endif
#ifdef WizardSmallImagePath
WizardSmallImageFile={#WizardSmallImagePath}
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "thai"; MessagesFile: "compiler:Languages\Thai.isl"

[CustomMessages]
english.MT5PathTitle=MetaTrader 5 Path
english.MT5PathDesc=Set MT5 terminal path
english.MT5PathSub=Please provide MT5 terminal path.
english.MT5LoginTitle=MT5 Account
english.MT5LoginDesc=Set MT5 account credentials
english.MT5LoginSub=Please provide MT5 login info.
english.StrategyTitle=Strategy Profile
english.StrategyDesc=Choose preset
english.StrategySub=Select one preset:
english.SymbolsTitle=Symbols
english.SymbolsDesc=Set symbols list
english.SymbolsSub=Comma-separated symbols to scan/trade.
english.TelegramTitle=Telegram
english.TelegramDesc=Enable Telegram notification
english.TelegramSub=Choose Telegram option:
english.TelegramCfgTitle=Telegram Config
english.TelegramCfgDesc=Set Telegram token/chat id
english.TelegramCfgSub=Fill only if Telegram is enabled.
english.MsgRequiredMT5Path=MT5_PATH is required.
english.MsgRequiredSymbols=SYMBOLS is required.
english.MsgPostInstallFail=Post-install configuration failed. You can run scripts\one_click_installer.ps1 manually.

thai.MT5PathTitle=MetaTrader 5 Path
thai.MT5PathDesc=Set MT5 terminal path
thai.MT5PathSub=Please provide MT5 terminal path.
thai.MT5LoginTitle=MT5 Account
thai.MT5LoginDesc=Set MT5 account credentials
thai.MT5LoginSub=Please provide MT5 login info.
thai.StrategyTitle=Strategy Profile
thai.StrategyDesc=Choose preset
thai.StrategySub=Select one preset:
thai.SymbolsTitle=Symbols
thai.SymbolsDesc=Set symbols list
thai.SymbolsSub=Comma-separated symbols to scan/trade.
thai.TelegramTitle=Telegram
thai.TelegramDesc=Enable Telegram notification
thai.TelegramSub=Choose Telegram option:
thai.TelegramCfgTitle=Telegram Config
thai.TelegramCfgDesc=Set Telegram token/chat id
thai.TelegramCfgSub=Fill only if Telegram is enabled.
thai.MsgRequiredMT5Path=MT5_PATH is required.
thai.MsgRequiredSymbols=SYMBOLS is required.
thai.MsgPostInstallFail=Post-install configuration failed. You can run scripts\one_click_installer.ps1 manually.

english.MsgRiskPct=RISK_PER_TRADE_PCT must be a number between 0.01 and 10.0
english.MsgDailyLoss=DAILY_LOSS_LIMIT must be a number >= 1
english.MsgMaxOpen=MAX_OPEN_POSITIONS must be an integer between 1 and 50
english.MsgCooldown=ORDER_COOLDOWN_MINUTES must be an integer between 0 and 1440
english.MsgMinExecCat=MIN_EXECUTE_CATEGORY must be alert, strong, or premium
english.MsgWatch=WATCHLIST_THRESHOLD must be between 0 and 100
english.MsgAlert=ALERT_THRESHOLD must be between 0 and 100
english.MsgStrong=STRONG_ALERT_THRESHOLD must be between 0 and 100
english.MsgPremium=PREMIUM_ALERT_THRESHOLD must be between 0 and 100
english.MsgThresholdOrder=Thresholds must satisfy WATCHLIST <= ALERT <= STRONG <= PREMIUM
english.MsgMinAlertCat=MIN_ALERT_CATEGORY must be alert, strong, or premium
english.MsgSmartExitBool=ENABLE_SMART_EXIT must be true or false
english.MsgBreakEvenBool=ENABLE_BREAK_EVEN must be true or false
english.MsgTrailingBool=ENABLE_TRAILING_STOP must be true or false
english.MsgPartialBool=ENABLE_PARTIAL_CLOSE must be true or false
english.MsgBreakEvenTrigger=BREAK_EVEN_TRIGGER_R must be between 0.1 and 20
english.MsgBreakEvenLock=BREAK_EVEN_LOCK_R must be between 0.0 and 20
english.MsgTrailingStart=TRAILING_START_R must be between 0.1 and 20
english.MsgTrailingDistance=TRAILING_DISTANCE_R must be between 0.1 and 20
english.MsgPartialTrigger=PARTIAL_CLOSE_TRIGGER_R must be between 0.1 and 20
english.MsgPartialRatio=PARTIAL_CLOSE_RATIO must be between 0.1 and 0.9
thai.MsgRiskPct=RISK_PER_TRADE_PCT must be a number between 0.01 and 10.0
thai.MsgDailyLoss=DAILY_LOSS_LIMIT must be a number >= 1
thai.MsgMaxOpen=MAX_OPEN_POSITIONS must be an integer between 1 and 50
thai.MsgCooldown=ORDER_COOLDOWN_MINUTES must be an integer between 0 and 1440
thai.MsgMinExecCat=MIN_EXECUTE_CATEGORY must be alert, strong, or premium
thai.MsgWatch=WATCHLIST_THRESHOLD must be between 0 and 100
thai.MsgAlert=ALERT_THRESHOLD must be between 0 and 100
thai.MsgStrong=STRONG_ALERT_THRESHOLD must be between 0 and 100
thai.MsgPremium=PREMIUM_ALERT_THRESHOLD must be between 0 and 100
thai.MsgThresholdOrder=Thresholds must satisfy WATCHLIST <= ALERT <= STRONG <= PREMIUM
thai.MsgMinAlertCat=MIN_ALERT_CATEGORY must be alert, strong, or premium
thai.MsgSmartExitBool=ENABLE_SMART_EXIT must be true or false
thai.MsgBreakEvenBool=ENABLE_BREAK_EVEN must be true or false
thai.MsgTrailingBool=ENABLE_TRAILING_STOP must be true or false
thai.MsgPartialBool=ENABLE_PARTIAL_CLOSE must be true or false
thai.MsgBreakEvenTrigger=BREAK_EVEN_TRIGGER_R must be between 0.1 and 20
thai.MsgBreakEvenLock=BREAK_EVEN_LOCK_R must be between 0.0 and 20
thai.MsgTrailingStart=TRAILING_START_R must be between 0.1 and 20
thai.MsgTrailingDistance=TRAILING_DISTANCE_R must be between 0.1 and 20
thai.MsgPartialTrigger=PARTIAL_CLOSE_TRIGGER_R must be between 0.1 and 20
thai.MsgPartialRatio=PARTIAL_CLOSE_RATIO must be between 0.1 and 0.9
[Files]
Source: "..\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion; Excludes: ".venv\*,signals.db,logs\*,.runtime\*,__pycache__\*,.pytest_cache\*,.pytest_tmp\*,tmp\*,ptmp*\*,*.pyc,output\*,installer\output\*"

[Icons]
Name: "{autoprograms}\PyTrade Dashboard"; Filename: "http://localhost:8501"; IconFilename: "{sys}\url.dll"
Name: "{autoprograms}\PyTrade Folder"; Filename: "{app}"

[Code]
var
  MT5PathPage: TInputQueryWizardPage;
  MT5CredPage: TInputQueryWizardPage;
  StrategyPage: TInputOptionWizardPage;
  SymbolsPage: TInputQueryWizardPage;
  TelegramPage: TInputQueryWizardPage;
  EnableTelegramPage: TInputOptionWizardPage;
  RiskPage: TInputQueryWizardPage;
  ThresholdPage: TInputQueryWizardPage;
  ExitPage: TInputQueryWizardPage;

  MT5PathValue: string;
  MT5LoginValue: string;
  MT5PasswordValue: string;
  MT5ServerValue: string;
  SymbolsValue: string;
  PresetValue: string;
  TelegramEnabledValue: string;
  TelegramTokenValue: string;
  TelegramChatValue: string;
  RiskPerTradePctValue: string;
  DailyLossLimitValue: string;
  MaxOpenPositionsValue: string;
  OrderCooldownMinutesValue: string;
  MinExecuteCategoryValue: string;
  WatchlistThresholdValue: string;
  AlertThresholdValue: string;
  StrongAlertThresholdValue: string;
  PremiumAlertThresholdValue: string;
  MinAlertCategoryValue: string;
  EnableSmartExitValue: string;
  EnableBreakEvenValue: string;
  BreakEvenTriggerRValue: string;
  BreakEvenLockRValue: string;
  EnableTrailingStopValue: string;
  TrailingStartRValue: string;
  TrailingDistanceRValue: string;
  EnablePartialCloseValue: string;
  PartialCloseTriggerRValue: string;
  PartialCloseRatioValue: string;

function QuotePS(const S: string): string;
var
  T: string;
begin
  T := S;
  StringChangeEx(T, '"', '\"', True);
  Result := '"' + T + '"';
end;

function NormalizeNum(const S: string): string;
var
  T: string;
begin
  T := Trim(S);
  StringChangeEx(T, ',', '.', True);
  Result := T;
end;

function ParseFloatInRange(const S: string; MinV: Extended; MaxV: Extended; var OutV: Extended): Boolean;
var
  T: string;
begin
  T := NormalizeNum(S);
  try
    OutV := StrToFloat(T);
    Result := (OutV >= MinV) and (OutV <= MaxV);
  except
    Result := False;
  end;
end;

function ParseIntInRange(const S: string; MinV: Integer; MaxV: Integer; var OutV: Integer): Boolean;
var
  T: string;
begin
  T := Trim(S);
  try
    OutV := StrToInt(T);
    Result := (OutV >= MinV) and (OutV <= MaxV);
  except
    Result := False;
  end;
end;

function IsBoolText(const S: string): Boolean;
var
  L: string;
begin
  L := LowerCase(Trim(S));
  Result := (L = 'true') or (L = 'false');
end;

function IsCategoryText(const S: string): Boolean;
var
  L: string;
begin
  L := LowerCase(Trim(S));
  Result := (L = 'alert') or (L = 'strong') or (L = 'premium');
end;

procedure InitializeWizard;
begin
  MT5PathPage := CreateInputQueryPage(
    wpSelectDir,
    ExpandConstant('{cm:MT5PathTitle}'),
    ExpandConstant('{cm:MT5PathDesc}'),
    ExpandConstant('{cm:MT5PathSub}')
  );
  MT5PathPage.Add('MT5_PATH:', False);
  MT5PathPage.Values[0] := 'C:\Program Files\MetaTrader 5\terminal64.exe';

  MT5CredPage := CreateInputQueryPage(
    MT5PathPage.ID,
    ExpandConstant('{cm:MT5LoginTitle}'),
    ExpandConstant('{cm:MT5LoginDesc}'),
    ExpandConstant('{cm:MT5LoginSub}')
  );
  MT5CredPage.Add('MT5_LOGIN:', False);
  MT5CredPage.Add('MT5_PASSWORD:', True);
  MT5CredPage.Add('MT5_SERVER:', False);

  StrategyPage := CreateInputOptionPage(
    MT5CredPage.ID,
    ExpandConstant('{cm:StrategyTitle}'),
    ExpandConstant('{cm:StrategyDesc}'),
    ExpandConstant('{cm:StrategySub}'),
    True,
    False
  );
  StrategyPage.Add('aggressive');
  StrategyPage.Add('balanced');
  StrategyPage.Add('premium');
  StrategyPage.Add('ultra_premium');
  StrategyPage.SelectedValueIndex := 1;

  SymbolsPage := CreateInputQueryPage(
    StrategyPage.ID,
    ExpandConstant('{cm:SymbolsTitle}'),
    ExpandConstant('{cm:SymbolsDesc}'),
    ExpandConstant('{cm:SymbolsSub}')
  );
  SymbolsPage.Add('SYMBOLS:', False);
  SymbolsPage.Values[0] := 'BTCUSD,ETHUSD,XAUUSD';

  EnableTelegramPage := CreateInputOptionPage(
    SymbolsPage.ID,
    ExpandConstant('{cm:TelegramTitle}'),
    ExpandConstant('{cm:TelegramDesc}'),
    ExpandConstant('{cm:TelegramSub}'),
    True,
    False
  );
  EnableTelegramPage.Add('Disable Telegram');
  EnableTelegramPage.Add('Enable Telegram');
  EnableTelegramPage.SelectedValueIndex := 0;

  TelegramPage := CreateInputQueryPage(
    EnableTelegramPage.ID,
    ExpandConstant('{cm:TelegramCfgTitle}'),
    ExpandConstant('{cm:TelegramCfgDesc}'),
    ExpandConstant('{cm:TelegramCfgSub}')
  );
  TelegramPage.Add('TELEGRAM_TOKEN:', False);
  TelegramPage.Add('TELEGRAM_CHAT_ID:', False);

  RiskPage := CreateInputQueryPage(
    TelegramPage.ID,
    'Risk & Execution',
    'Tune execution and risk controls',
    'Leave defaults if unsure.'
  );
  RiskPage.Add('RISK_PER_TRADE_PCT:', False);
  RiskPage.Values[0] := '0.20';
  RiskPage.Add('DAILY_LOSS_LIMIT:', False);
  RiskPage.Values[1] := '150';
  RiskPage.Add('MAX_OPEN_POSITIONS:', False);
  RiskPage.Values[2] := '2';
  RiskPage.Add('ORDER_COOLDOWN_MINUTES:', False);
  RiskPage.Values[3] := '15';
  RiskPage.Add('MIN_EXECUTE_CATEGORY (alert/strong/premium):', False);
  RiskPage.Values[4] := 'strong';

  ThresholdPage := CreateInputQueryPage(
    RiskPage.ID,
    'Thresholds',
    'Tune scoring thresholds',
    '0-100 scale'
  );
  ThresholdPage.Add('WATCHLIST_THRESHOLD:', False);
  ThresholdPage.Values[0] := '45';
  ThresholdPage.Add('ALERT_THRESHOLD:', False);
  ThresholdPage.Values[1] := '55';
  ThresholdPage.Add('STRONG_ALERT_THRESHOLD:', False);
  ThresholdPage.Values[2] := '65';
  ThresholdPage.Add('PREMIUM_ALERT_THRESHOLD:', False);
  ThresholdPage.Values[3] := '75';
  ThresholdPage.Add('MIN_ALERT_CATEGORY (alert/strong/premium):', False);
  ThresholdPage.Values[4] := 'alert';

  ExitPage := CreateInputQueryPage(
    ThresholdPage.ID,
    'Smart Exit',
    'Tune break-even / trailing / partial close',
    'Use true/false for ENABLE_* fields'
  );
  ExitPage.Add('ENABLE_SMART_EXIT (true/false):', False);
  ExitPage.Values[0] := 'true';
  ExitPage.Add('ENABLE_BREAK_EVEN (true/false):', False);
  ExitPage.Values[1] := 'true';
  ExitPage.Add('BREAK_EVEN_TRIGGER_R:', False);
  ExitPage.Values[2] := '1.0';
  ExitPage.Add('BREAK_EVEN_LOCK_R:', False);
  ExitPage.Values[3] := '0.1';
  ExitPage.Add('ENABLE_TRAILING_STOP (true/false):', False);
  ExitPage.Values[4] := 'true';
  ExitPage.Add('TRAILING_START_R:', False);
  ExitPage.Values[5] := '1.5';
  ExitPage.Add('TRAILING_DISTANCE_R:', False);
  ExitPage.Values[6] := '1.0';
  ExitPage.Add('ENABLE_PARTIAL_CLOSE (true/false):', False);
  ExitPage.Values[7] := 'false';
  ExitPage.Add('PARTIAL_CLOSE_TRIGGER_R:', False);
  ExitPage.Values[8] := '1.5';
  ExitPage.Add('PARTIAL_CLOSE_RATIO:', False);
  ExitPage.Values[9] := '0.5';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  F1, F2, F3, F4: Extended;
  I1, I2: Integer;
begin
  Result := True;

  if CurPageID = MT5PathPage.ID then begin
    MT5PathValue := Trim(MT5PathPage.Values[0]);
    if MT5PathValue = '' then begin
      MsgBox(ExpandConstant('{cm:MsgRequiredMT5Path}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;

  if CurPageID = MT5CredPage.ID then begin
    MT5LoginValue := Trim(MT5CredPage.Values[0]);
    MT5PasswordValue := Trim(MT5CredPage.Values[1]);
    MT5ServerValue := Trim(MT5CredPage.Values[2]);
  end;

  if CurPageID = StrategyPage.ID then begin
    if StrategyPage.Values[0] then PresetValue := 'aggressive';
    if StrategyPage.Values[1] then PresetValue := 'balanced';
    if StrategyPage.Values[2] then PresetValue := 'premium';
    if StrategyPage.Values[3] then PresetValue := 'ultra_premium';
  end;

  if CurPageID = SymbolsPage.ID then begin
    SymbolsValue := Trim(SymbolsPage.Values[0]);
    if SymbolsValue = '' then begin
      MsgBox(ExpandConstant('{cm:MsgRequiredSymbols}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;

  if CurPageID = EnableTelegramPage.ID then begin
    if EnableTelegramPage.Values[1] then TelegramEnabledValue := 'true' else TelegramEnabledValue := 'false';
  end;

  if CurPageID = TelegramPage.ID then begin
    TelegramTokenValue := Trim(TelegramPage.Values[0]);
    TelegramChatValue := Trim(TelegramPage.Values[1]);
  end;

  if CurPageID = RiskPage.ID then begin
    RiskPerTradePctValue := Trim(RiskPage.Values[0]);
    DailyLossLimitValue := Trim(RiskPage.Values[1]);
    MaxOpenPositionsValue := Trim(RiskPage.Values[2]);
    OrderCooldownMinutesValue := Trim(RiskPage.Values[3]);
    MinExecuteCategoryValue := LowerCase(Trim(RiskPage.Values[4]));

    if not ParseFloatInRange(RiskPerTradePctValue, 0.01, 10.0, F1) then begin
      MsgBox(ExpandConstant('{cm:MsgRiskPct}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseFloatInRange(DailyLossLimitValue, 1.0, 1000000.0, F1) then begin
      MsgBox(ExpandConstant('{cm:MsgDailyLoss}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseIntInRange(MaxOpenPositionsValue, 1, 50, I1) then begin
      MsgBox(ExpandConstant('{cm:MsgMaxOpen}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseIntInRange(OrderCooldownMinutesValue, 0, 1440, I1) then begin
      MsgBox(ExpandConstant('{cm:MsgCooldown}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not IsCategoryText(MinExecuteCategoryValue) then begin
      MsgBox(ExpandConstant('{cm:MsgMinExecCat}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;

  if CurPageID = ThresholdPage.ID then begin
    WatchlistThresholdValue := Trim(ThresholdPage.Values[0]);
    AlertThresholdValue := Trim(ThresholdPage.Values[1]);
    StrongAlertThresholdValue := Trim(ThresholdPage.Values[2]);
    PremiumAlertThresholdValue := Trim(ThresholdPage.Values[3]);
    MinAlertCategoryValue := LowerCase(Trim(ThresholdPage.Values[4]));

    if not ParseFloatInRange(WatchlistThresholdValue, 0.0, 100.0, F1) then begin
      MsgBox(ExpandConstant('{cm:MsgWatch}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseFloatInRange(AlertThresholdValue, 0.0, 100.0, F2) then begin
      MsgBox(ExpandConstant('{cm:MsgAlert}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseFloatInRange(StrongAlertThresholdValue, 0.0, 100.0, F3) then begin
      MsgBox(ExpandConstant('{cm:MsgStrong}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseFloatInRange(PremiumAlertThresholdValue, 0.0, 100.0, F4) then begin
      MsgBox(ExpandConstant('{cm:MsgPremium}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ((F1 <= F2) and (F2 <= F3) and (F3 <= F4)) then begin
      MsgBox(ExpandConstant('{cm:MsgThresholdOrder}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not IsCategoryText(MinAlertCategoryValue) then begin
      MsgBox(ExpandConstant('{cm:MsgMinAlertCat}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;

  if CurPageID = ExitPage.ID then begin
    EnableSmartExitValue := LowerCase(Trim(ExitPage.Values[0]));
    EnableBreakEvenValue := LowerCase(Trim(ExitPage.Values[1]));
    BreakEvenTriggerRValue := Trim(ExitPage.Values[2]);
    BreakEvenLockRValue := Trim(ExitPage.Values[3]);
    EnableTrailingStopValue := LowerCase(Trim(ExitPage.Values[4]));
    TrailingStartRValue := Trim(ExitPage.Values[5]);
    TrailingDistanceRValue := Trim(ExitPage.Values[6]);
    EnablePartialCloseValue := LowerCase(Trim(ExitPage.Values[7]));
    PartialCloseTriggerRValue := Trim(ExitPage.Values[8]);
    PartialCloseRatioValue := Trim(ExitPage.Values[9]);

    if not IsBoolText(EnableSmartExitValue) then begin
      MsgBox(ExpandConstant('{cm:MsgSmartExitBool}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not IsBoolText(EnableBreakEvenValue) then begin
      MsgBox(ExpandConstant('{cm:MsgBreakEvenBool}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not IsBoolText(EnableTrailingStopValue) then begin
      MsgBox(ExpandConstant('{cm:MsgTrailingBool}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not IsBoolText(EnablePartialCloseValue) then begin
      MsgBox(ExpandConstant('{cm:MsgPartialBool}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseFloatInRange(BreakEvenTriggerRValue, 0.1, 20.0, F1) then begin
      MsgBox(ExpandConstant('{cm:MsgBreakEvenTrigger}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseFloatInRange(BreakEvenLockRValue, 0.0, 20.0, F1) then begin
      MsgBox(ExpandConstant('{cm:MsgBreakEvenLock}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseFloatInRange(TrailingStartRValue, 0.1, 20.0, F1) then begin
      MsgBox(ExpandConstant('{cm:MsgTrailingStart}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseFloatInRange(TrailingDistanceRValue, 0.1, 20.0, F1) then begin
      MsgBox(ExpandConstant('{cm:MsgTrailingDistance}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseFloatInRange(PartialCloseTriggerRValue, 0.1, 20.0, F1) then begin
      MsgBox(ExpandConstant('{cm:MsgPartialTrigger}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if not ParseFloatInRange(PartialCloseRatioValue, 0.1, 0.9, F1) then begin
      MsgBox(ExpandConstant('{cm:MsgPartialRatio}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Cmd: string;
  ExitCode: Integer;
  Ok: Boolean;
begin
  if CurStep <> ssPostInstall then
    Exit;

  if PresetValue = '' then PresetValue := 'balanced';
  if TelegramEnabledValue = '' then TelegramEnabledValue := 'false';

  Cmd :=
    '-ExecutionPolicy Bypass -File ' + QuotePS(ExpandConstant('{app}\scripts\one_click_installer.ps1')) +
    ' -ProjectRoot ' + QuotePS(ExpandConstant('{app}')) +
    ' -MT5Path ' + QuotePS(MT5PathValue) +
    ' -MT5Login ' + QuotePS(MT5LoginValue) +
    ' -MT5Password ' + QuotePS(MT5PasswordValue) +
    ' -MT5Server ' + QuotePS(MT5ServerValue) +
    ' -Symbols ' + QuotePS(SymbolsValue) +
    ' -Preset ' + QuotePS(PresetValue) +
    ' -TelegramEnabled ' + QuotePS(TelegramEnabledValue) +
    ' -TelegramToken ' + QuotePS(TelegramTokenValue) +
    ' -TelegramChatId ' + QuotePS(TelegramChatValue) +
    ' -RiskPerTradePct ' + QuotePS(RiskPerTradePctValue) +
    ' -DailyLossLimit ' + QuotePS(DailyLossLimitValue) +
    ' -MaxOpenPositions ' + QuotePS(MaxOpenPositionsValue) +
    ' -OrderCooldownMinutes ' + QuotePS(OrderCooldownMinutesValue) +
    ' -MinExecuteCategory ' + QuotePS(MinExecuteCategoryValue) +
    ' -WatchlistThreshold ' + QuotePS(WatchlistThresholdValue) +
    ' -AlertThreshold ' + QuotePS(AlertThresholdValue) +
    ' -StrongAlertThreshold ' + QuotePS(StrongAlertThresholdValue) +
    ' -PremiumAlertThreshold ' + QuotePS(PremiumAlertThresholdValue) +
    ' -MinAlertCategory ' + QuotePS(MinAlertCategoryValue) +
    ' -EnableSmartExit ' + QuotePS(EnableSmartExitValue) +
    ' -EnableBreakEven ' + QuotePS(EnableBreakEvenValue) +
    ' -BreakEvenTriggerR ' + QuotePS(BreakEvenTriggerRValue) +
    ' -BreakEvenLockR ' + QuotePS(BreakEvenLockRValue) +
    ' -EnableTrailingStop ' + QuotePS(EnableTrailingStopValue) +
    ' -TrailingStartR ' + QuotePS(TrailingStartRValue) +
    ' -TrailingDistanceR ' + QuotePS(TrailingDistanceRValue) +
    ' -EnablePartialClose ' + QuotePS(EnablePartialCloseValue) +
    ' -PartialCloseTriggerR ' + QuotePS(PartialCloseTriggerRValue) +
    ' -PartialCloseRatio ' + QuotePS(PartialCloseRatioValue) +
    ' -NonInteractive';

  Ok := Exec('powershell.exe', Cmd, ExpandConstant('{app}'), SW_SHOW, ewWaitUntilTerminated, ExitCode);
  if (not Ok) or (ExitCode <> 0) then begin
    MsgBox(
      ExpandConstant('{cm:MsgPostInstallFail}') + #13#10 +
      'ExitCode=' + IntToStr(ExitCode),
      mbError, MB_OK
    );
  end;
end;

[Run]
Filename: "http://localhost:8501"; Flags: shellexec postinstall skipifsilent; Description: "Open PyTrade Dashboard"


