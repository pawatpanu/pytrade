# PyTrade Android Installation & Setup

ติดตั้งและใช้งาน PyTrade บน Android

## 📱 ตัวเลือกการติดตั้ง

### Option 1: Progressive Web App (PWA) - แนะนำ ⭐
ใช้ Streamlit Dashboard บน Chrome Mobile แบบ Installable
- ✅ ไม่ต้องติดตั้ง APK
- ✅ ใช้ได้ทั้ง LAN และ Internet
- ✅ Auto-refresh
- ✅ Fast & responsive

**ขั้นตอน**:
1. ติดตั้ง PyTrade บน PC/Server (ดู INSTALL_WINDOWS_TH.md)
2. เขียน config network (ดู `.env.android`)
3. เปิด Chrome บน Android
4. เข้า PyTrade Dashboard
5. "Install app" (Add to Home Screen)

---

### Option 2: Docker Container
รัน PyTrade ใน Docker บน Android ผ่าน Termux
- ⚠️ ต้องค่อนข้างซับซ้อน
- ✅ True standalone
- ✅ Full control

**ขั้นตอน**:
1. Install Termux จาก F-Droid
2. ติดตั้ง Docker runtime
3. Run Docker image
4. เข้า Dashboard ผ่าน localhost:8501

---

### Option 3: Termux Python Script
รัน PyTrade daemon เบา ๆ บน Android
- πŸ'» Direct Python execution
- βš™οΈ ต้องไป compile dependencies
- ⚠️ ต้อง MT5 Terminal ยังคงต้องรัน PC

**ขั้นตอน**:
1. Install Termux
2. Setup Python environment
3. Run daemon script

---

## πŸš€ Quick Start (Option 1 - Recommended)

### Requirement:
- PC/Server runnning PyTrade daemon
- Android phone with Chrome
- Same WiFi network (หรือ VPN)

### Step 1: Configure Network
```bash
# ในโฟลเดอร์ PyTrade บน PC
nano .env.android
```

File: `.env.android`
```properties
# PyTrade Remote Connection Config
PYTRADE_HOST=192.168.1.100    # [แก้เป็น IP ของ PC]
PYTRADE_PORT=8501             # Streamlit port
PYTRADE_API_PORT=5000         # API port (ถ้าใช้)
PYTRADE_DAEMON_ENABLED=true
```

### Step 2: Start PyTrade on PC
```bash
# บน PC
cd c:\pytrade
call Start-All.bat
# หรือ
python main.py --mode daemon
python -m streamlit run streamlit_app.py --server.port 8501
```

### Step 3: Access from Android

**Manually** (ไม่ install app):
- เปิด Chrome
- ไปที่ `http://192.168.1.100:8501/?lang=th`
- ใช้งานปกติ

**Install as App**:
- Chrome → Menu (βŠ™) 
- "Install app" หรือ "Add to Home Screen"
- ใช้เป็น app แบบ native

---

## πŸ"§ Files Included

| File | Purpose |
|------|---------|
| `.env.android` | Network config |
| `android_dashboard.html` | Standalone PWA manifest |
| `docker-compose.android.yml` | Docker setup |
| `install_termux.sh` | Termux installation script |
| `setup_network.py` | Network auto-discovery |

---

## βš™οΈ Network Configuration

### LAN Setup (Same WiFi)
1. หา IP ของ PC
   ```bash
   # บน PC Windows
   ipconfig
   # ดู IPv4 Address
   ```

2. Update `.env.android`
   ```properties
   PYTRADE_HOST=192.168.x.x
   ```

3. Android Chrome: `http://192.168.x.x:8501`

### Internet Setup (Without Same WiFi)
1. Setup Ngrok หรือ VPN บน PC:
   ```bash
   ngrok http 8501
   ```

2. Copy public URL ใน `.env.android`:
   ```properties
   PYTRADE_HOST=https://xxxx.ngrok.io
   ```

3. Android Chrome: ใช้ URL จาก ngrok

---

## πŸ"" Troubleshooting

### ❌ "Cannot reach server"
1. ✅ Ensure PC and Android on same WiFi
2. ✅ Firewall port 8501 open
3. ✅ PC IP correct
4. ✅ Streamlit running on PC

### ❌ "Dashboard loads slow"
1. ✅ Close other apps
2. ✅ Reduce refresh interval
3. ✅ Use WiFi 5GHz if available

### ❌ "Order functions not working"
1. ✅ Ensure daemon running on PC
2. ✅ MT5 connected on PC
3. ✅ Check daemon logs

---

## πŸ" Security Notes

βš ️ **สำคัญ**: Android ไม่ควรใช้การทำ orders จริง ๆ
- Mobile อาจ disconnect ไปพลัน
- Recommend: View-only mode บน Android
- Real orders: PC + MT5 Terminal only

### Security Best Practices:
- ใช้ Firewall
- ปิด ports ที่ไม่ใช้
- ใช้ VPN for internet access
- Set password/PIN on Android
- ใช้ HTTPS if possible

---

## πŸ"œ File Structures

```
pytrade/
β"œβ"€ android/
β"‚  β"œβ"€ README_ANDROID.md (this file)
β"‚  β"œβ"€ .env.android
β"‚  β"œβ"€ android_dashboard.html
β"‚  β"œβ"€ docker-compose.android.yml
β"‚  β"œβ"€ install_termux.sh
β"‚  └─ setup_network.py
β"œβ"€ streamlit_app.py
β"œβ"€ main.py
└─ config.py
```

---

## πŸ"— References

- Streamlit mobile: https://docs.streamlit.io
- PWA guide: https://web.dev/progressive-web-apps
- Termux guide: https://wiki.termux.com
- Docker guide: https://docs.docker.com

---

**Last Updated**: 2026-03-16  
**Status**: ✅ Ready to Use
