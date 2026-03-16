# πŸ—Ό MT5 Connection Guide - PyTrade

**πŸ‡ΉπŸ‡­ ภาษาไทย | English**

---

## 1️⃣ ข้อมูลที่ต้องเตรียม

### πŸ"Ί สำคัญ!
ต้องติดตั้ง **MetaTrader 5 Terminal** บน PC ก่อน
- Download จาก: https://www.metaquotes.net/en/metatrader5
- หรือชาร์ท Exness / Thailand Futures ฯลฯ

### πŸ"' ข้อมูล Account MT5
ที่ต้องการ:
```
MT5_LOGIN       = Account number (ตัวเลข)
MT5_PASSWORD    = Password
MT5_SERVER      = Server name (เช่น Exness-MT5Trial)
MT5_PATH        = Path ไป MT5 executable
```

---

## 2️⃣ หาข้อมูล MT5

### πŸ"£ Account Number (MT5_LOGIN)
เปิด MetaTrader 5 Terminal:
```
1. ดู Title bar ด้านบน
   "MetaTrader 5 - Account 433329124 - Exness-MT5Trial"
   
2. หรือไปที่:
   File → Account Information
   
3. หาคำว่า "Login" หรือ "Account"
   → ที่นี่คือ account number

Example: 433329124
```

### πŸ" Password (MT5_PASSWORD)
```
ใช้ Password เดียวกับที่ login MT5 Terminal
โดยปกติจะเป็นรหัส 6-12 ตัวอักษร
```

### 🌐 Server Name (MT5_SERVER)
```
ดู MT5 Terminal Title bar หรือ:
File → Account Information → Server

Common servers:
- Exness-MT5Trial          (Exness Demo)
- Exness-MT5              (Exness Live)
- ThailandFutures-Demo    (Thailand)
- Phoenix-MT5             (ETC)
```

### πŸ—„οΈ MT5 Path (MT5_PATH)
เตอร์มิแนล executable ที่ติดตั้ง:

**Windows (Default)**:
```
C:\Program Files\MetaTrader 5\terminal64.exe
C:\Program Files (x86)\MetaTrader 5\terminal.exe
```

**Find MT5 Path**:
1. เปิด File Explorer
2. ค้นหา "terminal64.exe" หรือ "terminal.exe"
3. Right-click → Properties → Location
4. Copy full path

---

## 3️⃣ ตั้งค่า .env file

### πŸ" Edit `.c:\pytrade\.env`

```bash
# MT5 Connection
MT5_LOGIN=433329124
MT5_PASSWORD=YourPassword123
MT5_SERVER=Exness-MT5Trial
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# Symbols
SYMBOLS=BTCUSD,ETHUSD,SOLUSD

# ส่วนที่เหลือ (ปล่อยไว้เหมือนเดิม)
...
```

### βœ… Check:
```
✓ LOGIN = ตัวเลข 6-10 หลัก (ไม่ใช่ email)
✓ PASSWORD = รหัส MT5 ถูกต้อง
✓ SERVER = ชื่อ server ที่เห็นใน MT5
✓ PATH = ตรวจสอบ terminal executable มีจริง
```

---

## 4️⃣ ทดสอบ Connection

### πŸ"Š Test 1: ตรวจสอบ Path

```bash
# Windows PowerShell
Test-Path "C:\Program Files\MetaTrader 5\terminal64.exe"

# Output ควรเป็น True
True
```

### πŸ"Š Test 2: ตรวจสอบ Config

```bash
cd c:\pytrade
python -c "from config import CONFIG; print(f'Login: {CONFIG.mt5_login}, Server: {CONFIG.mt5_server}')"

# Output ควรเป็น:
# Login: 433329124, Server: Exness-MT5Trial
```

### πŸ"Š Test 3: ทดสอบ Connection

```bash
# Win เปิด Command Prompt/PowerShell ที่โฟลเดอร์ pytrade

# Active virtual environment
.\.venv\Scripts\Activate.ps1

# Run test
python -c "
from core.mt5_connector import connect_mt5
from config import CONFIG
try:
    connector = connect_mt5(CONFIG)
    print('βœ… MT5 Connected Successfully!')
    symbols = connector.get_available_symbols()
    print(f'Found {len(symbols)} symbols')
except Exception as e:
    print(f'❌ Connection Failed: {e}')
"
```

**Output ที่ดี**:
```
βœ… MT5 Connected Successfully!
Found 1000+ symbols
```

**Output ที่ไม่ดี**:
```
❌ Connection Failed: Cannot connect MetaTrader5...
```

---

## 5️⃣ Troubleshooting

### ❌ "Cannot find terminal64.exe"

**Fix**:
```
1. ตรวจสอบ path ถูกต้อง:
   Test-Path "C:\Program Files\MetaTrader 5\terminal64.exe"
   
2. ถ้า False, หา path ที่ถูก:
   Get-ChildItem -Path "C:\" -Filter "terminal*.exe" -Recurse
   
3. Update .env ด้วย path ที่ถูก
```

### ❌ "Invalid login or password"

**Fix**:
```
1. ตรวจสอบ MT5_LOGIN:
   - ต้องเป็นตัวเลข (ไม่มี @ หรือ email)
   - ตัวอย่าง: 433329124 βœ"
   - ตัวอย่างท้องถิ่น: user@gmail.com ❌
   
2. ตรวจสอบ MT5_PASSWORD:
   - ใช้รหัส password MT5 ที่ถูก
   - ไม่ใช่ password broker website
   - Demo vs Live password ต่างกัน!
   
3. ลองเปิด MT5 Terminal ด้วยตัวเอง:
   - ถ้าเข้าไม่ได้ → password ผิด
   - ถ้าเข้าได้ → ใช้ password นั้น
```

### ❌ "Server not found"

**Fix**:
```
1. เปิด MT5 Terminal
2. File → Account Information
3. ดู "Server" field ให้ชัดเจน
4. Copy เต็ม ๆ ลง .env
   หมายเหตุ: คำว่า "-" เวอร์ชั่น เวอร์ชั่น เป็น part ของ server name
   
   ตัวอย่าง:
   - "Exness-MT5Trial17" ❌ (อาจมีตัวเลข)
   - "Exness-MT5Trial" βœ" (ชื่อ server ที่ถูก)
```

### ❌ "MT5 Terminal not running"

** Fix**:
```
1. PyTrade ต้องให้ MT5 Terminal เปิดอยู่เสมอ
2. เปิด MetaTrader 5 Terminal ตรง ๆ:
   C:\Program Files\MetaTrader 5\terminal64.exe
   
3. ให้มันพร้อม (logged in)
   
4. จากนั้นรัน PyTrade
   
5. ถ้าพลัด connection:
   - PyTrade จะลองเชื่อมต่อใหม่อัตโนมัติ
   - ดู logs (-ข ที่ config)
```

### ❌ "DLL Load Failed"  (Windows)

**Fix**:
```
1. ติดตั้ง Visual C++ Redistributable:
   https://support.microsoft.com/en-us/help/2977003
   
2. ติดตั้ง Python 64-bit (ต้อง):
   python --version  (ต้องเป็น 64-bit)
   
3. Reinstall MetaTrader5 package:
   pip uninstall MetaTrader5 -y
   pip install MetaTrader5
```

---

## 6️⃣ Demo vs Live Account

### πŸ"² Demo Account

**สำหรับ Testing**:
```
✓ ปลอดภัย (เงินปลอม)
✓ ไม่กลัวขาดทุน
✓ Fast reconnection
✓ ใช้สำหรับทดลอง PyTrade

ตั้งค่า:
EXECUTION_MODE=demo
DRY_RUN=true  (ไม่ส่ง order จริง)
```

**How to create**:
1. เปิด Exness / Broker website
2. "Create Demo Account"
3. Copy login + password
4. ใส่ใน .env

### πŸ'° Live Account  

**For Real Trading**:
```
⚠️  RISKY - ใช้เงินจริง
⚠️  ต้องทดสอบ Demo ก่อน
✓ Larger trade size
✓ Real money

ตั้งค่า:
EXECUTION_MODE=live
DRY_RUN=false  (ส่ง order จริง!)
DAILY_LOSS_LIMIT=5000  (เพื่อป้องกัน)
```

---

## 7️⃣ Connection Verification

### πŸ"ƒ Connection Status

เช็ค daemon log:
```bash
type logs\daemon.log | tail -50

# มองหา:
# βœ… "MT5 connected successfully"
# βœ… "Account info retrieved"
# ❌ "MT5 initialize failed" = problem
```

### πŸ"ƒ Account Info Check

```bash
python pro_trader_analysis.py

# Output:
# Account Balance: $10,000.00
# Equity: $10,000.00
# Symbols available: 1000+
```

---

## 8️⃣ Advanced: Multiple Accounts

ถ้าต้องการเชื่อม 2 account คนละ:

### Option 1: Run 2 instances
```bash
# Instance 1 (Command Prompt 1)
cd c:\pytrade
SET MT5_LOGIN=433329124
SET MT5_SERVER=Exness-MT5Trial
python main.py --mode daemon

# Instance 2 (Command Prompt 2)
cd c:\pytrade_account2
SET MT5_LOGIN=433329125
SET MT5_SERVER=Exness-MT5Trial
python main.py --mode daemon
```

### Option 2: Docker containers
```bash
docker run -e MT5_LOGIN=433329124 pytrade:latest
docker run -e MT5_LOGIN=433329125 pytrade:latest
```

---

## 9️⃣ Security Best Practices

### πŸ"' Keep Safe:
```
✓ ไม่ share .env file ใคร
✓ ไม่ upload .env ไป GitHub
✓ MD5 hash password ถ้าต้องหนักแน่น
✓ ปล่อย DRY_RUN=true ตลอดในตอนแรก
✓ ใช้ Demo account ก่อน Live
✓ ตั้ง DAILY_LOSS_LIMIT สูง
```

### πŸ" .env Protection:
```
# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore

# ตรวจดู:
git status | grep ".env"
# ควร NOT เห็นไฟล์ .env
```

---

## πŸ"™ Config Reference

**ไฟล์**: `config.py`

```python
# MT5 Settings
mt5_login: int | None           # Account number
mt5_password: str | None        # Login password
mt5_server: str | None          # Server name
mt5_path: str | None            # Terminal path

# Connection retry
mt5_reconnect_attempts: int = 3 # Auto reconnect count
mt5_timeout_seconds: int = 30   # Connection timeout
```

---

## πŸ"— Extra Resources

- **MetaTrader5 Python Docs**: https://www.mql5.com/en/docs/python_api
- **Exness**: https://www.exnessdev.com
- **PyTrade GitHub**: https://github.com/pawatpanu/pytrade

---

## πŸ"‹ Checklist

- [ ] ติดตั้ง MT5 Terminal
- [ ] มี Demo/Live account
- [ ] หา MT5_LOGIN
- [ ] หา MT5_PASSWORD
- [ ] หา MT5_SERVER
- [ ] หา MT5_PATH
- [ ] แก้ .env file
- [ ] Test connection
- [ ] ตรวจสอบ symbols
- [ ] Ready to trade! πŸš€

---

**Last Updated**: 2026-03-16  
**Status**: ✅ Complete
**Tested on**: MT5 Terminal 5.0+

---

## ❓ Still having issues?

1. ✓ ดู logs: `type logs\daemon.log`
2. ✓ Check .env: `type .env` (ไม่ show password)
3. ✓ Verify MT5 running: Task Manager > Python/MT5
4. ✓ Restart everything
5. ✓ Ask on GitHub issues

**πŸ€ Good luck! Ready to trade?**
