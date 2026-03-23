# MT5 Crypto Signal Alert System (Python)

ระบบวิเคราะห์สัญญาณและแจ้งเตือน/ส่งคำสั่งเทรดบน MetaTrader 5 แบบ Multi-timeframe

## คุณสมบัติหลัก
- วิเคราะห์ MTF: `H4/H1/M15/M5`
- Indicator หลัก: EMA, RSI, MACD, Bollinger, ADX, ATR, Stoch, Volume
- Scoring แบบ `rule-based confidence` (ไม่ใช่ win rate)
- Hard filters + threshold ปรับได้
- Anti-duplicate alert
- Execution mode พร้อม risk guard, smart exit, partial close
- SQLite logging + Streamlit dashboard

## โครงสร้างหลัก
- `main.py`
- `config.py`
- `streamlit_app.py`
- `core/` (connector, fetcher, signal, scorer, execution, notifier, db)
- `tests/`
- `docs/INSTALL_WINDOWS_TH.md`
- `docs/USER_GUIDE_TH.md`

## ติดตั้งบน Windows
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
copy .env.example .env
```

## เชื่อม MT5
ตั้งค่าใน `.env`:
- `MT5_PATH`
- `MT5_LOGIN`
- `MT5_PASSWORD`
- `MT5_SERVER`

## รันระบบ
สแกน 1 รอบ:
```powershell
C:\pytrade\.venv\Scripts\python.exe C:\pytrade\main.py --mode scan --once
```

ซิงก์สถานะออเดอร์:
```powershell
C:\pytrade\.venv\Scripts\python.exe C:\pytrade\main.py --mode sync
```

เดมอนต่อเนื่อง:
```powershell
C:\pytrade\.venv\Scripts\python.exe C:\pytrade\main.py --mode daemon
```

แดชบอร์ด:
```powershell
py -m streamlit run streamlit_app.py
```

หรือดับเบิลคลิกไฟล์ `.bat` ได้เลย:
- `scripts\Run-Dashboard.bat` เปิด Dashboard
- `scripts\Run-Daemon.bat` รัน Daemon ต่อเนื่อง
- `scripts\Scan-Once.bat` สแกน 1 รอบ
- `scripts\Sync-Orders.bat` ซิงก์สถานะออเดอร์
- `scripts\Reset-Loss-Guard.bat` รีเซ็ต Daily Loss Guard
- `scripts\Start-All.bat` เปิด Daemon + Dashboard พร้อมกัน
- `scripts\Stop-All.bat` ส่งคำสั่งหยุด Python/Streamlit ที่ใช้กับระบบ

มี launcher ซ้ำที่โฟลเดอร์หลัก `C:\pytrade` ด้วย เพื่อกดใช้งานได้เร็ว:
- `Run-Dashboard.bat`
- `Run-Daemon.bat`
- `Start-All.bat`
- `Stop-All.bat`
- `Restart-All.bat`
- `Open-Logs.bat`
- `Status-Check.bat`
- `Update-From-Git.bat`
- `Scan-Once.bat`
- `Sync-Orders.bat`
- `PyTrade Dashboard.url` เปิดหน้า Dashboard ตรงไปที่เบราว์เซอร์
- `Create-Desktop-Shortcuts.bat` สร้าง shortcut บน Desktop ให้อัตโนมัติ
- `Reset-Loss-Guard.bat`

## ไฟล์ช่วยใช้งานเร็ว (.bat)
- `Start-All.bat` เปิด Daemon และ Dashboard พร้อมกัน
- `Stop-All.bat` ส่งคำสั่งหยุด Python/Streamlit ที่ใช้กับระบบ
- `Restart-All.bat` หยุดแล้วเปิดระบบใหม่ทันที
- `Open-Logs.bat` เปิดโฟลเดอร์ logs และไฟล์ log ล่าสุด
- `Status-Check.bat` เช็ก venv, `.env`, pid, port, process แบบเร็ว
- `Update-From-Git.bat` ดึงโค้ดล่าสุดจาก Git, ติดตั้ง dependencies, แล้วรีสตาร์ทระบบ
- `PyTrade Dashboard.url` ใช้เปิดหน้าเว็บ Dashboard ทันที
- `Create-Desktop-Shortcuts.bat` ใช้สร้าง shortcut `PyTrade Dashboard`, `PyTrade Start All`, `PyTrade Status Check` บน Desktop

## ติดตั้งแบบรันถาวร (Auto Start)
ใช้สคริปต์ใน `scripts/`:

แนะนำ: รัน preflight เพื่อตรวจความพร้อมเครื่องปลายทางก่อน
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight_windows.ps1
```
หรือดับเบิลคลิก:
`Preflight-Check.bat`
(รายงานจะถูกบันทึกที่ `logs\preflight_manual_report.txt`)

ติดตั้ง:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows.ps1
```

ถอนติดตั้ง task:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall_windows.ps1
```

ติดตั้งแบบครั้งเดียวพร้อมถามค่า config:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\one_click_installer.ps1
```
หรือดับเบิลคลิก:
`scripts\OneClick-Setup.bat`


## Release Package
สร้างไฟล์ปล่อยใช้งานพร้อมส่งต่อได้ด้วย:
- `scripts\package_release.ps1`
- `scripts\Build-Release.bat`
- `Build-Release.bat`

คำสั่ง:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\package_release.ps1
```

หรือกดครั้งเดียวแบบ launcher:
- `Build-Release.bat`
: build installer + package release ให้เสร็จในรอบเดียว

ผลลัพธ์จะถูกสร้างใน `installer\output` เช่น:
- `PyTradeSetup-<timestamp>.exe`
- `RELEASE-NOTES-<timestamp>.md`
- `PyTrade-Release-<timestamp>.zip`
ใน release zip จะมีเพิ่ม:
- `release_manifest.json`
- `Install-This-Version.bat`
- `Select-Version.bat`
- `Release-Manager.ps1`

การใช้งานบนเครื่องปลายทาง:
- ติดตั้งเวอร์ชันนี้ทันที: แตก zip แล้วดับเบิลคลิก `Install-This-Version.bat`
- อัปเดตเป็นเวอร์ชันใหม่: วางหลายไฟล์ `PyTrade-Release-*.zip` ไว้ในโฟลเดอร์เดียวกัน แล้วรัน `Select-Version.bat` เลือกเวอร์ชันใหม่
- ย้อนกลับเวอร์ชันเก่า: รัน `Select-Version.bat` แล้วเลือกเวอร์ชันเก่ากว่า

หมายเหตุ: ตัว installer จะคงไฟล์ `.env` และฐานข้อมูลเดิมไว้ จึงเหมาะกับการอัปเดต/ย้อนเวอร์ชันโดยไม่ทับข้อมูลใช้งาน
## GUI Installer (Next > Next > Finish)
มีสคริปต์ Inno Setup:
- `installer\PyTradeSetup.iss`

มีสคริปต์ build อัตโนมัติ:
- `scripts\build_installer.ps1`
- `scripts\Build-Installer.bat`

วิธี build:
1. ติดตั้ง Inno Setup 6
2. เปิดไฟล์ `installer\PyTradeSetup.iss`
3. กด Compile
4. ได้ไฟล์ติดตั้งที่ `installer\\output\\PyTradeSetup-<timestamp>.exe`

ตัวติดตั้งจะ:
- คัดลอกไฟล์ระบบ
- ติดตั้งลงโฟลเดอร์เริ่มต้น `C:\pytrade`
- ถ้าเครื่องยังไม่มี Python จะพยายามติดตั้ง `Python 3.11` ผ่าน `winget` อัตโนมัติ
- สร้าง `.venv` และติดตั้ง dependencies จาก `requirements.txt`
- ถามค่า MT5 + preset + symbols + Telegram
- มีหน้าปรับละเอียดเพิ่ม: Risk, Thresholds, Smart Exit
- ตรวจสอบความถูกต้องของค่าก่อนกด Next (ช่วงตัวเลข, true/false, ลำดับ thresholds)
- รัน post-install อัตโนมัติ (config `.env`, ติดตั้ง task, เริ่มระบบ)

สิ่งที่ยังต้องมี/ทำเอง:
- ติดตั้ง MetaTrader 5 และล็อกอินบัญชีให้เรียบร้อย
- เครื่องต้องมีอินเทอร์เน็ตตอนติดตั้งแพ็กเกจ Python
- ถ้าไม่มี `winget` ให้ติดตั้ง Python 3.11+ เองก่อน

รองรับภาษา:
- English
- Thai

ปรับโลโก้/ภาพตัวติดตั้ง (optional):
- วางไฟล์ใน `installer\assets`
- ดูรายละเอียดที่ `installer\assets\README.txt`

Task ที่สร้าง:
- `PyTradeDaemon`
- `PyTradeDashboard`

## ย้ายไปรันอีกเครื่องได้ไหม
ได้ โดยคัดลอกทั้งโฟลเดอร์ไปเครื่องใหม่ แล้วรัน one-click installer ด้านบน  
เครื่องใหม่ควรมี:
- Windows 10/11
- อินเทอร์เน็ตสำหรับติดตั้ง package
- MetaTrader 5

## Dashboard Config Wizard
แท็บ `ตั้งค่า` มี 2 โหมด:
- `Configuration Wizard`: ปรับค่าทุกมิติผ่านฟอร์ม
- `Raw .env editor`: แก้ `.env` โดยตรง
- `Task Scheduler Manager`: ติดตั้ง/ถอนติดตั้ง/Run/Stop งานถาวรจากหน้าเว็บ
- `Config Change History`: ดูประวัติการเปลี่ยนค่าในระบบ (audit trail)

แท็บ `Deploy Wizard`:
- สร้างไฟล์ `zip` สำหรับ deploy รายเครื่อง
- เลือกได้ว่าจะรวมข้อมูลลับ (MT5/Telegram) หรือไม่
- ภายใน zip มี `deploy_profile.env`, `install_profile.ps1`, `README_DEPLOY.txt`
- ฝั่งเครื่องปลายทางแตก zip แล้วรัน `install_profile.ps1` เพื่อ merge ค่าเข้า `.env` และติดตั้ง task อัตโนมัติ
- มีบล็อก `Release Manager` สำหรับ
  - ดูเวอร์ชันล่าสุดใน `installer\output`
  - สั่ง `Build Installer`
  - สั่ง `Package Release`
  - สั่ง `Build All`
  - เปิดโฟลเดอร์ output
  - เปิดตัวเลือกเวอร์ชันด้วย `Select-Version.bat`
  - ดาวน์โหลด `installer / release zip / release notes / manifest` ล่าสุดจากหน้าเว็บได้โดยตรง

Preset:
- `aggressive`
- `balanced`
- `premium`
- `ultra_premium`

ปรับได้ในฟอร์ม:
- Symbols / Hard Filters / Thresholds
- Execution gate (`MIN_EXECUTE_CATEGORY`, cooldown, max open)
- Risk (`RISK_PER_TRADE_PCT`, `DAILY_LOSS_LIMIT`)
- Smart Exit (`BE`, `Trailing`, `Partial Close`)
- Runtime (`SCAN_INTERVAL_SECONDS`, `SYNC_INTERVAL_SECONDS`, `DRY_RUN`)

Lot sizing ตามเงินในบัญชีจริง:
- `USE_MT5_BALANCE_FOR_SIZING=true` ให้ระบบใช้ยอดเงินจริงจาก MT5 ในการคำนวณความเสี่ยงต่อไม้
- `RISK_BALANCE_SOURCE=equity` (แนะนำ) หรือ `balance`
- `RISK_PER_TRADE_PCT` จะถูกคูณกับฐานที่เลือกเพื่อคำนวณ `risk_amount` และ lot อัตโนมัติ

หลังบันทึกให้รีสตาร์ท daemon เพื่อโหลดค่าใหม่

## เปลี่ยนโปรไฟล์ใน Dashboard (ทีละขั้น)
1. เปิด Dashboard: `py -m streamlit run streamlit_app.py`
2. ไปแท็บ `ตั้งค่า`
3. หัวข้อ `ตัวช่วยปรับค่าระบบ` เลือก `โปรไฟล์สำเร็จรูป`
4. กด `ใช้โปรไฟล์นี้`
5. กด `บันทึกค่าจากฟอร์ม`
6. ที่เมนูซ้าย กด `หยุดเดมอน` แล้ว `เริ่มเดมอน` เพื่อให้ค่าใหม่มีผล

ตรวจสอบว่าเปลี่ยนสำเร็จ:
- ดูที่เมนูซ้ายหัวข้อ `หมวดที่ใช้งานตอนนี้`
- ค่า `โปรไฟล์ / โหมดคัดกรอง / แจ้งเตือนขั้นต่ำ / ส่งคำสั่งขั้นต่ำ` ต้องเปลี่ยนตามที่ตั้ง

## Exness: รายการ Symbol แนะนำ (เริ่มใช้งานง่าย)
สำหรับบัญชี Exness แนะนำเริ่มจากชุดนี้ก่อน:

```env
SYMBOLS=BTCUSD,ETHUSD,SOLUSD,BNBUSD,XRPUSD,ADAUSD,DOGEUSD,XAUUSD,XAGUSD,EURUSD,GBPUSD,USDJPY,USOIL,UKOIL
```

หมายเหตุ:
- บางบัญชีอาจมี suffix เช่น `BTCUSDm`, `XAUUSDm` (ระบบมี normalize ให้)
- ถ้า symbol ใดไม่มีในโบรกเกอร์ ระบบจะ log warning และข้าม
- แนะนำเพิ่มทีละ 2-3 ตัว แล้วทดสอบ `scan --once` ก่อนรันเดมอน

## Premium Stack (เปิดไม้เพิ่มเมื่อสัญญาณแรง)
สามารถให้ระบบเปิดไม้เพิ่มได้ แม้มีออเดอร์ค้างอยู่ เมื่อสัญญาณเป็น `premium/ultra`:

```env
ENABLE_PREMIUM_STACK=true
PREMIUM_STACK_EXTRA_SLOTS=1
ENABLE_ULTRA_STACK=true
ULTRA_STACK_SCORE=95
ULTRA_STACK_EXTRA_SLOTS=2
```

- `MAX_OPEN_POSITIONS` คือเพดานฐาน
- ถ้า `category=premium` จะได้ช่องเพิ่มตาม `PREMIUM_STACK_EXTRA_SLOTS`
- ถ้าคะแนน >= `ULTRA_STACK_SCORE` จะได้ช่องเพิ่มอีกตาม `ULTRA_STACK_EXTRA_SLOTS`

## Telegram
ตั้งค่าใน `.env`:
- `TELEGRAM_ENABLED=true`
- `TELEGRAM_TOKEN=...`
- `TELEGRAM_CHAT_ID=...`

## หมายเหตุสำคัญ
- `score` คือ rule-based confidence ไม่ใช่ win rate
- แนะนำใช้บัญชี demo ก่อนเสมอ
- โหมด execution มี demo safety gate ในระบบ

## คู่มือแยก (ภาษาไทย)
- คู่มือติดตั้ง: `docs/INSTALL_WINDOWS_TH.md`
- คู่มือการใช้งาน: `docs/USER_GUIDE_TH.md`








