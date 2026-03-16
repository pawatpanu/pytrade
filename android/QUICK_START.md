# PyTrade Android - Quick Start Guide 🀖

**ไทย | English**

---

## πŸš€ เริ่มต้นใช้งาน 3 วิธี

### **วิธี 1: PWA บน Chrome (แนะนำ) ⭐**

**ข้อดี**:
- ✅ ไม่ต้องติดตั้ง APK
- ✅ เข้าได้ทั้ง LAN และ Internet
- ✅ Auto-refresh ตัวเอง
- ✅ Load ได้เร็ว

**ขั้นตอน** (5 นาที):

1. **ติดตั้ง PyTrade บน PC** (ตามไฟล์ INSTALL_WINDOWS_TH.md)

2. **รัน PyTrade**:
   ```batch
   cd c:\pytrade
   call Start-All.bat
   ```

3. **บน Android**:
   - เปิด Chrome
   - พิมพ์: `http://192.168.x.x:8501/?lang=th`
     (แก้ x.x เป็น IP ของ PC)
   - Chrome Menu (โอ‰) → "Install app"
   - ✅ ใช้เป็น app ทันที

---

### **วิธี 2: Termux (Advanced)**

**ข้อดี**:
- πŸ'» รัน Python บน Android เอง
- ✅ Standalone (ไม่ต้อง PC)

**ข้อจำกัด**:
- ❌ MT5 ยังต้อง PC (ไม่ได้ run บน Android)
- ❌ ต้องค่อนข้าง technical
- ❌ ใช้ storage และ CPU เยอะ

**ขั้นตอน** (30 นาที):
1. ดาวน์โหลด Termux (F-Droid)
2. รัน: `bash install_termux.sh`
3. รอ dependency install
4. เปิด Dashboard: `http://localhost:8501`

---

### **วิธี 3: Docker Compose (Expert)**

**ข้อดี**:
- πŸ› Containerized environment
- ✅ Isolated & reproducible

**ข้อจำกัด**:
- ❌ Docker บน Termux = ยากมาก
- ❌ ต้องผ่าน Linux experience
- ❌ ใช้ storage 5GB+

**ขั้นตอน**:
```bash
docker-compose -f docker-compose.android.yml up -d
# เข้า: http://localhost:8501
```

---

## πŸ"ƒ ไฟล์ที่รวมไว้

| ไฟล์ | ใช้สำหรับ |
|------|---------|
| `README_ANDROID.md` | คำแนะนำโดยละเอียด |
| `.env.android` | ตั้งค่า IP/PORT |
| `Setup-Android.bat` | Auto setup (Windows) |
| `setup_network.py` | Auto IP detect (Python) |
| `install_termux.sh` | ติดตั้ง Termux |
| `manifest.json` | PWA config |
| `docker-compose.android.yml` | Docker setup |
| `nginx.conf` | Reverse proxy |

---

## 🎯 วิธีที่แนะนำ

```
ใช้บ่อย?           → วิธี 1 (PWA Chrome) ✅
ไม่มี PC อื่น?       → วิธี 2 (Termux)
Sandbox environment? → วิธี 3 (Docker)
```

---

## βš™οΈ Troubleshooting

### "Cannot reach server"
```
βœ" PC และ Android ใน WiFi เดียวกัน?
βœ" IP ถูกต้องใน .env.android?
βœ" Firewall port 8501 open?
βœ" Streamlit running? (ดู cmd window)
```

### "Slow loading"
```
βœ" ปิด app อื่น ๆ บน Android
βœ" ใช้ WiFi 5GHz ถ้ามี
βœ" ลดจำนวน timeframe ใน config
```

### "Orders not working"
```
βœ" MT5 Terminal running บน PC?
βœ" Daemon status OK? (ดู logs)
βœ" Account = DEMO? (ปลอดภัย)
```

---

## πŸ" ความปลอดภัย

⚠️ **เตือน**: ห้ามใช้ Android ทำ Real Orders!

**ปลอดภัยมากขึ้น**:
- ✅ Android = View only
- ✅ Orders = PC + MT5 Terminal
- ✅ ใช้ WiFi ปลอด แต่ไม่ใช้ Public WiFi
- ✅ ปิด Execution ใน config
- ✅ Set Password บน Streamlit

---

## πŸ"— External Links

- **Streamlit Mobile**: https://docs.streamlit.io
- **PWA Guide**: https://web.dev/progressive-web-apps
- **Termux Wiki**: https://wiki.termux.com
- **Docker Docs**: https://docs.docker.com

---

## πŸ"π Network Setup

### Local WiFi (แนะนำ)
```
PC IP       : 192.168.1.100 (หา Windows > Settings > Network)
Android URL : http://192.168.1.100:8501/?lang=th
```

### Internet (Ngrok)
```
1. ngrok http 8501
2. Copy URL: https://xxxx.ngrok.io
3. Android URL: https://xxxx.ngrok.io/?lang=th
```

---

## β‰  Important Notes

- **MT5 Connection**: Requires PC with MT5 Terminal running
- **Demo Mode**: Configured by default (safe for testing)
- **Data Sync**: Database stored on PC (Termux/Docker = local only)
- **Push Notifications**: Not supported yet (future feature)
- **Offline Mode**: Not supported (requires PC connection)

---

## πŸ†š Support

Issues?
1. Check `README_ANDROID.md`
2. Review logs: `cat logs/daemon.log`
3. Check network: `ping 192.168.1.100`
4. Review GitHub issues

---

**Last Updated**: 2026-03-16
**Status**: ✅ Ready to Use
**Tested on**: Android 10-14 | Chrome 120+

---

## πŸŒ„ Next Steps

1. ✅ ติดตั้ง PyTrade บน PC
2. ✅ รัน Start-All.bat
3. βœ… เปิด Chrome บน Android
4. βœ… Install as app
5. βœ… ใช้งาน!

**Enjoy PyTrade on Mobile! 🀖**
