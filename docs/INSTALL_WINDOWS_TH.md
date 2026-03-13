# คู่มือติดตั้ง PyTrade บน Windows (ฉบับง่าย)

เอกสารนี้พาไปตั้งแต่เครื่องใหม่จนรันระบบได้จริง

## 1) สิ่งที่ต้องมี
- Windows 10/11
- ติดตั้ง MetaTrader 5 แล้วล็อกอินบัญชี `demo` ได้
- ติดตั้ง Python 3.11+ และใช้คำสั่ง `py --version` ได้
- อินเทอร์เน็ต (ตอนติดตั้งแพ็กเกจ)

## 2) ติดตั้งแบบเร็ว (แนะนำ)
ที่โฟลเดอร์โปรเจกต์ `C:\pytrade`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
copy .env.example .env
powershell -ExecutionPolicy Bypass -File .\scripts\one_click_installer.ps1
```

สคริปต์จะช่วยตั้งค่า `.env`, ติดตั้ง Task Scheduler, และเตรียมระบบรันถาวร

## 3) ติดตั้งแบบ GUI (Next > Next > Finish)
### 3.1 สร้างไฟล์ติดตั้ง
1. ติดตั้ง Inno Setup 6
2. ที่โฟลเดอร์โปรเจกต์ รัน:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1
```

หรือดับเบิลคลิก `scripts\Build-Installer.bat`

3. ได้ไฟล์ติดตั้งที่:
`installer\output\PyTradeSetup.exe`

### 3.2 ใช้งานไฟล์ติดตั้ง
1. เปิด `PyTradeSetup.exe`
2. กด `Next` ตามขั้นตอน
3. กรอกค่า MT5 / preset / symbols / telegram
4. กด `Finish`

## 4) ตรวจสอบหลังติดตั้ง
```powershell
py main.py --mode sync
py main.py --mode scan --once
```

เปิดแดชบอร์ด:
```powershell
py -m streamlit run streamlit_app.py
```
จากนั้นเข้า `http://localhost:8501`

## 5) ติดตั้งรันถาวร (Auto Start)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows.ps1
```

ถอนออก:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall_windows.ps1
```

## 6) ปัญหาที่พบบ่อย
### 6.1 `No installed Python found`
- ติดตั้ง Python จาก python.org
- เปิดคำสั่งใหม่ แล้วลอง `py --version`

### 6.2 Activate venv ไม่ได้
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 6.3 MT5 connect ได้ แต่ไม่ส่งออเดอร์
เช็ค `.env`:
- `ENABLE_EXECUTION=true`
- `EXECUTION_MODE=demo`
- `MIN_EXECUTE_CATEGORY` ไม่สูงเกินไป
- ไม่มีเงื่อนไข block เช่น `daily_loss_limit_reached`, `max_open_positions_reached`

### 6.4 pytest permission error
รัน:
```powershell
py -m pytest -q tests --basetemp C:\pytrade\pytest_work\run1 -p no:cacheprovider
```

