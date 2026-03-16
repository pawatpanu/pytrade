# PyTrade สัญญาณเทรดและการทำงาน - การวิเคราะห์ความสมบูรณ์

**วันที่อัปเดต**: 2026-03-16  
**สถานะ**: ✅ ระบบการหาสัญญาณและการตัดสินใจเทรดออกแบบอย่างมีเหตุผล

---

## 📊 1. ขั้นตอนการสร้างสัญญาณ (Signal Generation Pipeline)

### 1.1 ข้อมูลหลัก (MTF Data Fetching)
```
main.py → _prepare_mtf_data()
  ├─ H4 (Primary Trend)      → ตรวจสอบแนวโน้มหลัก
  ├─ H1 (Confirmation)       → ยืนยันแนวโน้ม
  ├─ M15 (Setup Detection)   → ตั้งค่าการเข้า
  └─ M5 (Trigger Signal)     → ไทริกเกอร์การเข้า
```

### 1.2 การประเมินสัญญาณสองทิศ (Bi-directional Evaluation)
สำหรับแต่ละสัญลักษณ์ตรวจสอบทั้ง:
- **BUY Signal** - เงื่อนไขบอลิช
- **SELL Signal** - เงื่อนไขเบิร์นช

---

## ⛔ 2. ตัวกรองแข็ง (Hard Filters) - ต้องผ่านทั้งหมด

### 2.1 ADX Strength Filter
```python
ADX_VALUE = max(H1.adx14, M15.adx14)  # ใช้ค่าสูงสุด
MIN_ADX = asset_profile["adx_minimum"]

✓ PASS: ADX_VALUE >= MIN_ADX
✗ FAIL: ADX_VALUE < MIN_ADX → หลีกเลี่ยงการเข้าในตลาดไม่มีทิศทาง
```

**ค่าตัวอย่างจาก config (.env):**
- Signal Profile: `custom` (ใช้ default = strict)
- ADX Minimum: 18.0

### 2.2 Entry Zone Distance Filter
```python
entry_distance_atr = abs(M15.close - M15.ema20) / M15.atr14
base_entry_zone = asset_profile["entry_zone_max_atr"]
allowed_zone = base_entry_zone * 1.5 (soft mode) หรือ base_entry_zone (strict mode)

✓ PASS: entry_distance_atr <= allowed_zone
✗ FAIL: Price หลีกไปจาก EMA20 มากเกินไป → เข้าที่ไม่ดี
```

### 2.3 Trend Alignment Filter

#### สำหรับ BUY Signal:
```
H4 MUST BE:  bullish หรือ sideway (ไม่มี bearish conflict)
H1 NOT BE:   bearish (ยกเว้น M15 bullish ใน soft mode)
M15+M5:      ห้าม "Severe conflict" (ทั้งคู่ bearish)
```

#### สำหรับ SELL Signal (ตรงข้าม):
```
H4 MUST BE:  bearish หรือ sideway
H1 NOT BE:   bullish
M15+M5:      ห้าม "Severe conflict" (ทั้งคู่ bullish)
```

**Soft Mode (DRY_RUN=true):**
- ผ่อนปรนกว่า - ให้ M15/M5 overrule H4 sideway

**Strict Mode (DRY_RUN=false):**
- เข้มงวด - H4/H1 conflict = reject ทันที

---

## 🎯 3. ระบบการให้คะแนน (Scoring System)

### 3.1 11 องค์ประกอบการให้คะแนน

| ชื่อ | น้ำหนัก | อธิบาย |
|------|--------|--------|
| `higher_tf` | 20 | H4+H1 trend alignment |
| `ema_alignment` | 15 | EMA 20/50/200 positioning |
| `adx_strength` | 10 | Trend strength (4-10 pts) |
| `market_structure` | 10 | Bullish/Bearish/Mixed pattern |
| `setup_quality` | 12 | Candle quality (breakout/reversal/pullback) |
| `rsi_context` | 8 | RSI oversold/overbought + direction |
| `macd_confirmation` | 8 | MACD cross/momentum |
| `stoch_trigger` | 5 | Stoch cross in extremes |
| `volume_confirmation` | 5 | Volume spike detection |
| `bollinger_context` | 4 | BB band position & mode |
| `atr_suitability` | 3 | ATR ratio vs baseline |
| **TOTAL MAX** | **100** | **Max possible score** |

### 3.2 การให้คะแนนจะถูกจำกัด (Clamped)
```python
for each_component:
    raw_score = calculate(component)
    max_weight = config.weights[component]
    clamped = min(raw_score, max_weight)  # ไม่เกินน้ำหนักสูงสุด
    total += clamped
```

**ตัวอย่าง:**
- `ema_alignment` raw = 20 แต่ max_weight = 15 → ใช้ 15 เท่านั้น

---

## 🔥 4. Trigger Conditions (M5 Verification) - ต้องผ่าน 2/4 หรือ 1/4 (ขึ้นอยู่กับ asset)

ถ้าสัญญาณผ่านทุก hard filter และได้คะแนนสูง ตอนนี้ตรวจสอบ **M5 Trigger** (ช่วงเวลา 5 นาที):

### 4.1 Momentum Candle Check
```python
# BUY: แท่งเทียนสีเขียวแข็ง
close > open AND
(body / candle_range) >= 0.5 AND  # รศ. >= 50%
(close > prev_high OR close > prev_close)

# SELL: แท่งเทียนสีแดงแข็ง
close < open AND
(body / candle_range) >= 0.5 AND
(close < prev_low OR close < prev_close)
```

### 4.2 MACD Cross Detection
```python
# BUY Cross
prev.macd <= prev.macd_signal AND  # ข้ามขึ้นจากล่าง
current.macd > current.macd_signal

# SELL Cross (ตรงข้าม)
```

**+Continuation:** If MACD > signal และ histogram > prev_histogram

### 4.3 Stochastic Cross
```python
# BUY Cross
prev.stoch_k <= prev.stoch_d AND
current.stoch_k > current.stoch_d

# +Continuation: If K > D และ K > prev_K
```

### 4.4 Volume Spike
```python
current.volume >= volume_spike_ratio * current.volume_sma20
(default: 1.20 = 20% above 20-SMA)
```

### 4.5 ตรวจนับ Triggers
```python
trigger_count = count([momentum, macd_cross, stoch_cross, volume_spike])
min_required = asset_profile["m5_min_triggers"]  # default 1-2

✓ PASS: trigger_count >= min_required
✗ FAIL: → Signal becomes "candidate" (ยังไม่พร้อม)
```

---

## 📋 5. การจัดหมวดหมู่สัญญาณ (Signal Categories)

### 5.1 Category Rank (ระดับความเชื่อมั่น)

```
  rank 0 = "ignore"    (คะแนน < 50)
  rank 1 = "candidate" (คะแนน 50-60, ผ่าน hard filters แต่น้อย trigger)
  rank 2 = "alert"     (คะแนน 60-70)
  rank 3 = "strong"    (คะแนน 70-80)
  rank 4 = "premium"   (คะแนน 80-93)
  rank 5 = "ultra"     (คะแนน >= 93)
```

**Thresholds จาก .env:**
- `MIN_ALERT_CATEGORY=premium` → ใช้ alert ขึ้นไปเท่านั้น
- `MIN_EXECUTE_CATEGORY=premium` → ใช้ execute premium+ เท่านั้น

---

## ⚙️ 6. Pre-Execution Checks (ก่อนส่งออเดอร์)

ถ้า signal ได้ "premium" หรือสูงกว่า ตรวจสอบ **6 เงื่อนไข**:

### ✓ 1. Execution Must Be Enabled
```
ENABLE_EXECUTION=true
```

### ✓ 2. Execution Mode Must Be DEMO
```
EXECUTION_MODE=demo
(production/live mode ยังไม่รองรับ)
```

### ✓ 3. Signal Category ≥ Min Execute Category
```
signal.category >= MIN_EXECUTE_CATEGORY
Current: "premium" >= "premium" ✓
```

### ✓ 4. Max Open Positions Check
```
current_open_orders < max_allowed

base = MAX_OPEN_POSITIONS = 1
if signal == "premium" && ENABLE_PREMIUM_STACK:
    max += PREMIUM_STACK_EXTRA_SLOTS (2)
if score >= 93 && ENABLE_ULTRA_STACK:
    max += ULTRA_STACK_EXTRA_SLOTS (3)

Current max = 1 + 2 + 3 = 6 (ทั้งหมด)
Limit: 6 ออเดอร์พร้อมกัน
```

### ✓ 5. Daily Loss Guard
```
abs(today_realized_loss) < DAILY_LOSS_LIMIT
Current limit: 120.00 USD

If today loss >= 120 → ปิดระบบให้ 24 ชั่วโมง
```

### ✓ 6. Order Cooldown
```
time_since_last_order[symbol][direction] >= ORDER_COOLDOWN_MINUTES
Current: 30 นาที

Example: ถ้าเพิ่ง BUY BTCUSD เมื่อ 14:00
        ห้ามออเดอร์ BUY BTCUSD อีก จนถึง 14:30
```

### ✓ 7. Account Info Safety Checks
```
account_info available ✓
account_trade_mode == DEMO ✓
(ป้องกัน live trading โดยไม่ตั้งใจ)
```

---

## 💰 7. Risk Management & Position Sizing

### 7.1 Trade Plan Creation
```python
risk_amount = account_balance * (risk_per_trade_pct / 100)
risk_amount *= asset_profile["risk_pct_multiplier"]

# Default:
risk_amount = 10000 * (0.15 / 100) * 1.0 = 15.00 USD

# For crypto (0.90x):
risk_amount = 10000 * (0.15 / 100) * 0.9 = 13.50 USD
```

### 7.2 Stop Loss Calculation
```python
stop_loss = entry_price ± (atr14 * sl_atr_multiplier)

# BUY: SL = entry - (atr * 1.5)
# SELL: SL = entry + (atr * 1.5)
```

### 7.3 Take Profit Calculation
```python
risk_reward_ratio = target_rr (default 1.8)
tp_distance = sl_distance * risk_reward_ratio
take_profit = entry_price ± tp_distance
```

### 7.4 Volume Calculation
```
volume = risk_amount / (sl_distance * contract_size)

Constraints:
├─ min_volume (usually 0.01 lot)
├─ max_volume (symbol limit)
└─ step (0.01 increment)
```

---

## 📊 8. สถานะการออเดอร์ (Order Lifecycle)

```
SENT      → ส่งไป MT5 แล้ว (awaiting execution)
FILLED    → MT5 confirm execution completed
SKIPPED   → ห้ามออเดอร์ (logic reason)
FAILED    → MT5 reject หรือ error
CLOSED    → ปิดตำแหน่ง (profit/loss บันทึก)
```

---

## 🔍 9. ผลการตรวจสอบระบบปัจจุบัน

### ✅ ตรวจสอบแล้ว - ถูกต้อง

| จุด | สถานะ | หมายเหตุ |
|-----|-------|---------|
| Hard Filter Logic | ✅ | ADX, entry zone, trend alignment ครบ |
| 11-Component Scoring | ✅ | ทั้งหมดมี default weights |
| M5 Trigger (4 types) | ✅ | Momentum, MACD, Stoch, Volume ครบ |
| Pre-execution Checks | ✅ | 7 checks รวม daily loss guard |
| Risk Management | ✅ | Risk amount, SL, TP, volume sizing ครบ |
| Order Cooldown | ✅ | 30 min cooldown per symbol/direction |
| Demo Mode Safety | ✅ | Account trade_mode check ✓ |
| Position Stacking | ✅ | Base 1 + premium 2 + ultra 3 = max 6 |

---

## ⚠️ 10. ปัญหาจากระบบ (Log Analysis)

### 🔴 From Screenshot Log:

```
"Execution skipped BUY ... below_min_execute_category"
```

**สาเหตุ:** Signal category ต่ำกว่า MIN_EXECUTE_CATEGORY

**แก้ไข:**
```
SET: MIN_EXECUTE_CATEGORY=strong  (แทน premium)
หรือ
INCREASE: ปรับน้ำหนัก scoring weights ให้สูงขึ้น
```

### 🟡 "Stale data for XXXX ... > 720 min"

**สาเหตุ:** Data source (MT5) ไม่ส่งข้อมูลอัปเดต

**แก้ไข:**
```
1. ตรวจสอบเชื่อมต่อ MT5
2. ตรวจสอบ symbol trading hours
3. ลดค่า stale data threshold
```

---

## 🎬 11. Full Trading Flow Example

```
1. main.py SCAN INTERVAL (15 sec)
   ├─ Fetch BTCUSD H4, H1, M15, M5 candles
   ├─ Calc indicators (EMA, RSI, MACD, Stoch, ATR, BB, Volume)
   └─ For BTCUSD, evaluate_buy_signal() + evaluate_sell_signal()

2. HARD FILTERS (for BUY signal)
   ├─ ADX >= 18.0? ✓
   ├─ Entry zone <= 1.8 ATR? ✓  
   ├─ H4 trend bullish? ✓
   ├─ H1 not bearish? ✓
   ├─ No severe M15+M5 conflict? ✓
   └─ → Pass all hard filters

3. SCORING (11 components)
   ├─ higher_tf: 20 pts
   ├─ ema_alignment: 15 pts
   ├─ adx_strength: 8 pts
   ├─ ... (others)
   └─ Total = 87.5 pts → "premium" category

4. M5 TRIGGER CHECK
   ├─ Momentum candle? ✓
   ├─ MACD cross? ✓
   ├─ Stoch cross? ✓
   ├─ Volume spike? ✓
   └─ 4/4 triggers → Signal ready

5. SEND ALERT (if notifier enabled)
   └─ "BTCUSD BUY premium 87.5"

6. PRE-EXECUTION CHECKS
   ├─ ENABLE_EXECUTION=true? ✓
   ├─ EXECUTION_MODE=demo? ✓
   ├─ signal >= premium? ✓
   ├─ open_orders < 6? ✓
   ├─ daily_loss < 120? ✓
   ├─ cooldown passed? ✓
   ├─ account info demo? ✓
   └─ → All clear

7. EXECUTE
   ├─ Calc risk_amount = 15.00 USD
   ├─ Calc volume = 0.1 lot
   ├─ Set SL = entry - (ATR * 1.5)
   ├─ Set TP = entry + (ATR * 1.5 * 1.8)
   ├─ Send order_send() to MT5
   └─ Log to database

8. SYNC PHASE (every 30 sec)
   ├─ Check MT5 for filled orders
   ├─ Update position status
   ├─ Calc realized PnL
   └─ Update daily loss tracking
```

---

## 📝 12. Configuration Checklist

### Current .env Settings:
```
✓ SIGNAL_PROFILE=custom (ใช้ hardcoded defaults)
✓ DRY_RUN=false (strict mode activated)
✓ MIN_ALERT_CATEGORY=premium (สูง)
✓ MIN_EXECUTE_CATEGORY=premium (สูง)
✓ ENABLE_EXECUTION=true
✓ EXECUTION_MODE=demo
✓ ENABLE_PREMIUM_STACK=true (max +2)
✓ ENABLE_ULTRA_STACK=true (max +3)
✓ DAILY_LOSS_LIMIT=120.00
✓ ORDER_COOLDOWN_MINUTES=30
✓ MAX_OPEN_POSITIONS=1
```

---

## 🤔 13. สรุป: ระบบสมบูรณ์หรือไม่?

### ✅ สมบูรณ์:
- Hard filters ครบ (ADX, entry zone, trend alignment)
- Scoring 11 components ครบ
- M5 triggers 4 types ครบ  
- Risk management ครบ (SL, TP, volume, position sizing)
- Safety guards ครบ (daily loss, cooldown, demo mode check)
- Pre-execution checks ครบ 7 เงื่อนไข

### ⚠️ ข้อสังเกต:
- **MIN_EXECUTE_CATEGORY=premium** อาจสูงเกินไป → ลด signal frequency
- **DRY_RUN=false** (strict mode) → เข้มงวด อาจ reject สัญญาณที่ดี
- **Stale data warnings** → ตรวจสอบเชื่อมต่อ MT5

---

**สรุปสุดท้าย:** ✅ ระบบการหาสัญญาณและการตัดสินใจเทรดมีเหตุผล เบื้องต้นครบถ้วน
