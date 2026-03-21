# 🚀 PyTrade Launcher - คู่มือด่วน

## ⚡ วิธีเปิดทีเดียว (Open Everything At Once)

### 📌 ตัวเลือกที่ 1: Quick Start (แนะนำ)
**ไฟล์:** `Quick-Start.bat`
- ✅ เปิด Daemon (ตรวจสัญญาณ)
- ✅ เปิด Dashboard (Web UI)
- ✅ เปิด Browser โดยอัตโนมัติ
- ⏱️ เวลา: น้อยกว่า 10 วินาที

**วิธีใช้:**
```bash
# ดับเบิลคลิก Quick-Start.bat
# หรือ
cd C:\pytrade
Quick-Start.bat
```

---

### 📌 ตัวเลือกที่ 2: Interactive Launcher Menu
**ไฟล์:** `PyTrade-Launcher.bat`
- 🎯 เมนูเลือกทำงาน (Batch Version)
- เลือกอะไรจะเปิด ได้เลย
- ✓ Start All (เปิดทั้งหมด)
- ✓ Dashboard only
- ✓ Daemon only
- ✓ สร้าง Desktop Shortcuts
- ✓ Status Check

**วิธีใช้:**
```bash
PyTrade-Launcher.bat
```

---

### 📌 ตัวเลือกที่ 3: GUI Launcher (Modern)
**ไฟล์:** `Launch-GUI.bat` 
- 🎨 หน้าจอ GUI สวย ๆ (Windows Forms)
- มีสีแต่ละปุ่ม
- ปุ่มขนาดใหญ่ ใช้ง่าย

**วิธีใช้:**
```bash
Launch-GUI.bat
# หรือ
powershell -NoProfile -ExecutionPolicy Bypass -File "PyTrade-Launcher.ps1"
```

---

### 📌 ตัวเลือกที่ 4: Desktop Shortcuts
**ไฟล์:** `Create-Desktop-Shortcuts-Enhanced.bat`
- 💾 สร้าง Shortcuts บน Desktop
- คลิก 1 ครั้งเปิด PyTrade
- 5 shortcuts ให้เลือก

**ขั้นตอน:**
1. รัน: `Create-Desktop-Shortcuts-Enhanced.bat`
2. Shortcuts จะปรากฏบน Desktop
3. ดับเบิลคลิก shortcut ที่ต้องการ

**Shortcuts ที่สร้าง:**
- 🚀 PyTrade - Start All
- 📊 PyTrade - Dashboard
- 👁️ PyTrade - Daemon
- 🧰 PyTrade - Launcher
- 📋 PyTrade - Status

---

## 🎯 ตารางเปรียบเทียบ

| วิธี | ความง่าย | GUI | ความเร็ว | แนะนำ |
|------|---------|-----|---------|-------|
| Quick-Start.bat | ⭐⭐⭐⭐⭐ | ❌ | เร็วที่สุด | ✅ |
| PyTrade-Launcher.bat | ⭐⭐⭐⭐ | ❌ | ปกติ | ✅ |
| Launch-GUI.bat | ⭐⭐⭐⭐⭐ | ✅ | ปกติ | ✅ |
| Desktop Shortcuts | ⭐⭐⭐⭐⭐ | ✅ | ปกติ | ✅ |

---

## 💡 Tips

### 1️⃣ ถ้าต้องการเปิดแบบ "ไม่ต้องคิด"
👉 **ใช้ Quick-Start.bat** (ดับเบิลคลิกแค่ครั้งเดียว)

### 2️⃣ ถ้าต้องการเลือกอะไรจะเปิด
👉 **ใช้ PyTrade-Launcher.bat** หรือ **Launch-GUI.bat**

### 3️⃣ ถ้าต้องการคลิกจาก Desktop
👉 **รัน Create-Desktop-Shortcuts-Enhanced.bat** แล้วคลิก Shortcut

### 4️⃣ ถ้า Dashboard ค้าง หรือ Port 8501 ไม่ว่าง
🔧 ปิด Browser ก่อน หรือ:
```bash
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

---

## 🔧 Troubleshooting

### ❌ "ไม่พบ Virtual Environment"
```bash
# ติดตั้งใหม่
.\scripts\OneClick-Setup.bat
```

### ❌ "ไม่พบ .env"
```bash
# สร้าง .env จากตัวอย่าง
copy .env.example .env
# แล้วแก้ไขค่า MT5 login/server/password
```

### ❌ "Port 8501 ถูกใช้งานอยู่"
```bash
# หาและปิด Process
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

---

## 📞 รายการ Batch Files ทั้งหมด

```
รากโปรเจ็ก/
├── Quick-Start.bat ⭐ (เปิดทีเดียว - แนะนำ)
├── PyTrade-Launcher.bat (เมนูเลือก)
├── Launch-GUI.bat (GUI สวย)
├── Create-Desktop-Shortcuts-Enhanced.bat (สร้าย Shortcuts)
├── Start-All.bat (ใช้ใน scripts/)
├── Run-Dashboard.bat
├── Run-Daemon.bat
├── Status-Check.bat
├── Stop-All.bat
├── Restart-All.bat
└── ...
```

---

## ✅ ตรวจสอบว่าเปิดสำเร็จ

1. **Daemon กำลังทำงาน** 
   - ดู Log: `logs/daemon.log`
   - ดู Status: `Status-Check.bat`

2. **Dashboard เปิด**
   - ไปที่: http://127.0.0.1:8501/?lang=th
   - ควร เห็น UI เขียว/ฟ้า

3. **Database พร้อม**
   - ไฟล์: `signals.db` ควรมี
   - ดู Dashboard → Health Tab

---

## 🚀 ถัดไป?

หลังจากเปิด Launcher:
1. ✅ ตรวจสถานะ System (Health Tab)
2. ✅ ปรับ Settings (Configuration Tab)
3. ✅ ทดลอง Scan (`Scan-Once.bat`)
4. ✅ เริ่ม Auto Trading (`Start-All.bat`)

---

**Support:** ✉️ ดู README.md หลัก
