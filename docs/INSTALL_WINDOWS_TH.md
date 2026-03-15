# เธเธนเนเธกเธทเธญเธ•เธดเธ”เธ•เธฑเนเธ PyTrade เธเธ Windows (เธเธเธฑเธเธเนเธฒเธข)

เน€เธญเธเธชเธฒเธฃเธเธตเนเธเธฒเนเธเธ•เธฑเนเธเนเธ•เนเน€เธเธฃเธทเนเธญเธเนเธซเธกเนเธเธเธฃเธฑเธเธฃเธฐเธเธเนเธ”เนเธเธฃเธดเธ

## 1) เธชเธดเนเธเธ—เธตเนเธ•เนเธญเธเธกเธต
- Windows 10/11
- เธ•เธดเธ”เธ•เธฑเนเธ MetaTrader 5 เนเธฅเนเธงเธฅเนเธญเธเธญเธดเธเธเธฑเธเธเธต `demo` เนเธ”เน
- เธ•เธดเธ”เธ•เธฑเนเธ Python 3.11+ เนเธฅเธฐเนเธเนเธเธณเธชเธฑเนเธ `py --version` เนเธ”เน
- เธญเธดเธเน€เธ—เธญเธฃเนเน€เธเนเธ• (เธ•เธญเธเธ•เธดเธ”เธ•เธฑเนเธเนเธเนเธเน€เธเธ)

## 2) เธ•เธดเธ”เธ•เธฑเนเธเนเธเธเน€เธฃเนเธง (เนเธเธฐเธเธณ)
เธ—เธตเนเนเธเธฅเน€เธ”เธญเธฃเนเนเธเธฃเน€เธเธเธ•เน `C:\pytrade`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
copy .env.example .env
powershell -ExecutionPolicy Bypass -File .\scripts\one_click_installer.ps1
```

เธชเธเธฃเธดเธเธ•เนเธเธฐเธเนเธงเธขเธ•เธฑเนเธเธเนเธฒ `.env`, เธ•เธดเธ”เธ•เธฑเนเธ Task Scheduler, เนเธฅเธฐเน€เธ•เธฃเธตเธขเธกเธฃเธฐเธเธเธฃเธฑเธเธ–เธฒเธงเธฃ

## 3) เธ•เธดเธ”เธ•เธฑเนเธเนเธเธ GUI (Next > Next > Finish)
### 3.1 เธชเธฃเนเธฒเธเนเธเธฅเนเธ•เธดเธ”เธ•เธฑเนเธ
1. เธ•เธดเธ”เธ•เธฑเนเธ Inno Setup 6
2. เธ—เธตเนเนเธเธฅเน€เธ”เธญเธฃเนเนเธเธฃเน€เธเธเธ•เน เธฃเธฑเธ:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1
```

เธซเธฃเธทเธญเธ”เธฑเธเน€เธเธดเธฅเธเธฅเธดเธ `scripts\Build-Installer.bat`

3. เนเธ”เนเนเธเธฅเนเธ•เธดเธ”เธ•เธฑเนเธเธ—เธตเน:
`installer\output\PyTradeSetup.exe`

### 3.2 เนเธเนเธเธฒเธเนเธเธฅเนเธ•เธดเธ”เธ•เธฑเนเธ
1. เน€เธเธดเธ” `PyTradeSetup.exe`
2. เธเธ” `Next` เธ•เธฒเธกเธเธฑเนเธเธ•เธญเธ
3. เธเธฃเธญเธเธเนเธฒ MT5 / preset / symbols / telegram
4. เธเธ” `Finish`

## 4) เธ•เธฃเธงเธเธชเธญเธเธซเธฅเธฑเธเธ•เธดเธ”เธ•เธฑเนเธ
```powershell
C:\pytrade\.venv\Scripts\python.exe C:\pytrade\main.py --mode sync
C:\pytrade\.venv\Scripts\python.exe C:\pytrade\main.py --mode scan --once
```

เน€เธเธดเธ”เนเธ”เธเธเธญเธฃเนเธ”:
```powershell
py -m streamlit run streamlit_app.py
```
เธเธฒเธเธเธฑเนเธเน€เธเนเธฒ `http://localhost:8501`

## 5) เธ•เธดเธ”เธ•เธฑเนเธเธฃเธฑเธเธ–เธฒเธงเธฃ (Auto Start)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows.ps1
```

เธ–เธญเธเธญเธญเธ:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall_windows.ps1
```

## 6) เธเธฑเธเธซเธฒเธ—เธตเนเธเธเธเนเธญเธข
### 6.1 `No installed Python found`
- เธ•เธดเธ”เธ•เธฑเนเธ Python เธเธฒเธ python.org
- เน€เธเธดเธ”เธเธณเธชเธฑเนเธเนเธซเธกเน เนเธฅเนเธงเธฅเธญเธ `py --version`

### 6.2 Activate venv เนเธกเนเนเธ”เน
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 6.3 MT5 connect เนเธ”เน เนเธ•เนเนเธกเนเธชเนเธเธญเธญเน€เธ”เธญเธฃเน
เน€เธเนเธ `.env`:
- `ENABLE_EXECUTION=true`
- `EXECUTION_MODE=demo`
- `MIN_EXECUTE_CATEGORY` เนเธกเนเธชเธนเธเน€เธเธดเธเนเธ
- เนเธกเนเธกเธตเน€เธเธทเนเธญเธเนเธ block เน€เธเนเธ `daily_loss_limit_reached`, `max_open_positions_reached`

### 6.4 pytest permission error
เธฃเธฑเธ:
```powershell
py -m pytest -q tests --basetemp C:\pytrade\pytest_work\run1 -p no:cacheprovider
```


