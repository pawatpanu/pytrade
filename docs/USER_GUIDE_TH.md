# คู่มือการใช้งาน PyTrade (ฉบับใช้งานจริง)

เอกสารนี้เน้นใช้งานจริงแบบเข้าใจง่าย

## 1) แนวคิดสำคัญ
- คะแนน `score` คือ **rule-based confidence**
- คะแนน **ไม่ใช่** win rate
- ใช้ closed candle เป็นหลัก
- ระบบมี anti-duplicate alert

## 2) คำสั่งหลักที่ใช้ทุกวัน
### 2.1 เริ่มวันใหม่
```powershell
py main.py --mode reset_loss_guard
py main.py --mode sync
```

### 2.2 ทดสอบรอบเดียว
```powershell
py main.py --mode scan --once
```

### 2.3 รันต่อเนื่อง
```powershell
py main.py --mode daemon
```

### 2.4 ซิงก์สถานะออเดอร์
```powershell
py main.py --mode sync
```

## 3) ใช้ผ่าน Dashboard
เปิด:
```powershell
py -m streamlit run streamlit_app.py
```

เข้า `http://localhost:8501`

### 3.1 แถบซ้าย
- `สแกน 1 รอบ`: ยิง scan หนึ่งครั้ง
- `ซิงก์ออเดอร์`: อัปเดต sent/closed/pnl
- `เริ่มเดมอน` / `หยุดเดมอน`
- แสดงหมวดใช้งานตอนนี้: profile/filter/min_alert/min_execute

### 3.2 แท็บแดชบอร์ด
- ภาพรวมออเดอร์
- ปุ่มล้างข้อมูล skipped ที่ไม่สำคัญ
- รีเซ็ต Daily Loss Guard
- กราฟ Equity
- ตาราง orders/signals/events

### 3.3 แท็บตั้งค่า
- เลือก `โปรไฟล์สำเร็จรูป` ได้ทันที
- ปรับค่าทุกมิติผ่านฟอร์ม
- ดู glossary ความหมายตัวแปร
- บันทึกแล้วให้รีสตาร์ท daemon

### 3.4 แท็บสถานะพอร์ต
- ดึงข้อมูลบัญชีและ position จาก MT5

## 4) ปรับ “ความเข้มข้น” เข้าออเดอร์
### เข้าออเดอร์มากขึ้น
- `HARD_FILTER_MODE=soft`
- `M5_MIN_TRIGGERS=1`
- ลด thresholds ลง
- `MIN_EXECUTE_CATEGORY=alert`

### คัดคุณภาพเข้มขึ้น
- `HARD_FILTER_MODE=strict`
- `ADX_MINIMUM` สูงขึ้น
- `M5_MIN_TRIGGERS=2-3`
- เพิ่ม thresholds
- `MIN_EXECUTE_CATEGORY=strong` หรือ `premium`

## 5) Premium / Ultra Stack
ถ้าต้องการเปิดไม้เพิ่มแม้มีออเดอร์ค้าง:
```env
ENABLE_PREMIUM_STACK=true
PREMIUM_STACK_EXTRA_SLOTS=1
ENABLE_ULTRA_STACK=true
ULTRA_STACK_SCORE=95
ULTRA_STACK_EXTRA_SLOTS=2
```

## 6) เหตุผลที่มักเจอใน `orders.reason`
- `below_min_execute_category`: คะแนนต่ำกว่าเกณฑ์ส่งคำสั่ง
- `cooldown_active`: ยังไม่พ้น cooldown
- `max_open_positions_reached`: จำนวนไม้เปิดเต็ม
- `daily_loss_limit_reached`: ชนเพดานขาดทุนรายวัน
- `symbol_trade_disabled`: โบรกปิดการเทรด symbol นี้

## 7) Query ตรวจสอบเร็ว (SQLite)
```powershell
py -m sqlite3 signals.db "SELECT id,timestamp,symbol,status,reason,score,category FROM orders ORDER BY id DESC LIMIT 30;"
py -m sqlite3 signals.db "SELECT id,timestamp,symbol,direction,score,category FROM signals ORDER BY id DESC LIMIT 30;"
py -m sqlite3 signals.db "SELECT id,timestamp,symbol,level,message FROM scan_events ORDER BY id DESC LIMIT 30;"
```

## 8) โหมดปลอดภัยก่อนขึ้น live
แนะนำ:
- `EXECUTION_MODE=demo`
- `RISK_PER_TRADE_PCT` ต่ำ (0.10-0.30)
- `MAX_OPEN_POSITIONS` ต่ำ (1-2)
- เปิด Smart Exit

## 9) Checklist ก่อนปล่อยรันจริง
1. MT5 login สำเร็จ
2. symbols ตรงกับโบรก
3. sync ผ่าน
4. scan --once ผ่าน
5. dashboard แสดงข้อมูลปกติ
6. test ผ่าน:
```powershell
py -m pytest -q tests --basetemp C:\pytrade\pytest_work\run1 -p no:cacheprovider
```

