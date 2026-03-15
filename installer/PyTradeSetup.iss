#define MyAppName "PyTrade"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "PyTrade"
#define MyAppExeName "scripts\\OneClick-Setup.bat"
#define AssetsDir "..\\installer\\assets"
#ifndef OutputName
  #define OutputName "PyTradeSetup"
#endif

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
OutputBaseFilename={#OutputName}
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
thai.MsgRequiredMT5Path=Please set MT5_PATH.
thai.MsgRequiredSymbols=Please set SYMBOLS.
thai.MsgPostInstallFail=Post-install configuration failed. You can run scripts\one_click_installer.ps1 manually.

[Files]
Source: "..\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion; Excludes: ".git\*,.venv\*,.env,*.db,logs\*,.runtime\*,__pycache__\*,.pytest_cache\*,.pytest_tmp\*,tmp\*,ptmp*\*,pytest_work\*,*.pyc,output\*,installer\output\*"

[Icons]
Name: "{autodesktop}\PyTrade Control Center"; Filename: "{app}\Run-Dashboard.bat"; WorkingDir: "{app}"
Name: "{group}\PyTrade Control Center"; Filename: "{app}\Run-Dashboard.bat"; WorkingDir: "{app}"

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\install_windows.ps1"" -ProjectRoot ""{app}"""; Flags: runhidden waituntilterminated; StatusMsg: "Configuring PyTrade..."

[Code]
var
  MT5PathPage: TInputDirWizardPage;
  MT5LoginPage: TInputQueryWizardPage;
  StrategyPage: TInputOptionWizardPage;
  SymbolsPage: TInputQueryWizardPage;
  TelegramPage: TInputOptionWizardPage;
  TelegramCfgPage: TInputQueryWizardPage;

function BoolToEnv(Value: Boolean): String;
begin
  if Value then
    Result := 'true'
  else
    Result := 'false';
end;

function GetSelectedProfile: String;
begin
  if StrategyPage.SelectedValueIndex = 0 then Result := 'balanced'
  else if StrategyPage.SelectedValueIndex = 1 then Result := 'aggressive'
  else Result := 'premium';
end;

function TelegramEnabled: Boolean;
begin
  Result := TelegramPage.SelectedValueIndex = 0;
end;

procedure SaveEnvFile;
var
  EnvPath: String;
  Lines: TStringList;
begin
  EnvPath := ExpandConstant('{app}\.env');
  Lines := TStringList.Create;
  try
    Lines.Add('MT5_PATH=' + MT5PathPage.Values[0]);
    Lines.Add('MT5_LOGIN=' + MT5LoginPage.Values[0]);
    Lines.Add('MT5_PASSWORD=' + MT5LoginPage.Values[1]);
    Lines.Add('MT5_SERVER=' + MT5LoginPage.Values[2]);
    Lines.Add('SYMBOLS=' + SymbolsPage.Values[0]);
    Lines.Add('SIGNAL_PROFILE=' + GetSelectedProfile());
    Lines.Add('TELEGRAM_ENABLED=' + BoolToEnv(TelegramEnabled()));
    Lines.Add('TELEGRAM_TOKEN=' + TelegramCfgPage.Values[0]);
    Lines.Add('TELEGRAM_CHAT_ID=' + TelegramCfgPage.Values[1]);
    Lines.SaveToFile(EnvPath);
  finally
    Lines.Free;
  end;
end;

procedure InitializeWizard;
begin
  MT5PathPage := CreateInputDirPage(wpSelectDir, ExpandConstant('{cm:MT5PathTitle}'), ExpandConstant('{cm:MT5PathDesc}'), ExpandConstant('{cm:MT5PathSub}'), False, '');
  MT5PathPage.Add('MT5 terminal64.exe path:');
  MT5PathPage.Values[0] := 'C:\Program Files\MetaTrader 5';

  MT5LoginPage := CreateInputQueryPage(MT5PathPage.ID, ExpandConstant('{cm:MT5LoginTitle}'), ExpandConstant('{cm:MT5LoginDesc}'), ExpandConstant('{cm:MT5LoginSub}'));
  MT5LoginPage.Add('MT5_LOGIN:', False);
  MT5LoginPage.Add('MT5_PASSWORD:', True);
  MT5LoginPage.Add('MT5_SERVER:', False);

  StrategyPage := CreateInputOptionPage(MT5LoginPage.ID, ExpandConstant('{cm:StrategyTitle}'), ExpandConstant('{cm:StrategyDesc}'), ExpandConstant('{cm:StrategySub}'), False, False);
  StrategyPage.Add('balanced');
  StrategyPage.Add('aggressive');
  StrategyPage.Add('premium');
  StrategyPage.SelectedValueIndex := 0;

  SymbolsPage := CreateInputQueryPage(StrategyPage.ID, ExpandConstant('{cm:SymbolsTitle}'), ExpandConstant('{cm:SymbolsDesc}'), ExpandConstant('{cm:SymbolsSub}'));
  SymbolsPage.Add('SYMBOLS:', False);
  SymbolsPage.Values[0] := 'BTCUSD,ETHUSD,XAUUSD';

  TelegramPage := CreateInputOptionPage(SymbolsPage.ID, ExpandConstant('{cm:TelegramTitle}'), ExpandConstant('{cm:TelegramDesc}'), ExpandConstant('{cm:TelegramSub}'), False, False);
  TelegramPage.Add('Enable Telegram');
  TelegramPage.Add('Disable Telegram');
  TelegramPage.SelectedValueIndex := 1;

  TelegramCfgPage := CreateInputQueryPage(TelegramPage.ID, ExpandConstant('{cm:TelegramCfgTitle}'), ExpandConstant('{cm:TelegramCfgDesc}'), ExpandConstant('{cm:TelegramCfgSub}'));
  TelegramCfgPage.Add('TELEGRAM_TOKEN:', False);
  TelegramCfgPage.Add('TELEGRAM_CHAT_ID:', False);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = MT5PathPage.ID) and (Trim(MT5PathPage.Values[0]) = '') then begin
    MsgBox(ExpandConstant('{cm:MsgRequiredMT5Path}'), mbError, MB_OK);
    Result := False;
  end;
  if (CurPageID = SymbolsPage.ID) and (Trim(SymbolsPage.Values[0]) = '') then begin
    MsgBox(ExpandConstant('{cm:MsgRequiredSymbols}'), mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    try
      SaveEnvFile();
    except
      MsgBox(ExpandConstant('{cm:MsgPostInstallFail}'), mbError, MB_OK);
    end;
  end;
end;

