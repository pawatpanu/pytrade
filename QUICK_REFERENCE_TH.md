# PyTrade - สรุปฉบับสั้น (Quick Reference)

## 🎯 ระบบทำงานแล้วไง?

### 1️⃣ **Fetch Data** → ดึงข้อมูล H4/H1/M15/M5

```python
# จาก MetaTrader5
OHLCV (Open, High, Low, Close, Volume)
```

### 2️⃣ **Calculate Indicators** → คำนวณตัวชี้วัด

```
EMA (20, 50, 200) → Trend
RSI, MACD, ADX, ATR, Stochastic, Bollinger, Volume
```

### 3️⃣ **Evaluate Signals** → ประเมิน BUY/SELL

```
Hard Filters (ต้องผ่านก่อน)
  ✓ ADX แข็งแรง
  ✓ ราคาใกล้ entry zone
  ✓ ทิศทาง TF มี alignment
  ✓ ไม่มี conflict

Confidence Scoring (0-100)
  20% Higher TF Alignment
  15% EMA Structure
  10% ADX Strength
  ... (อีก 8 component)
```

### 4️⃣ **Send Alert** → ส่งแจ้งเตือน

```
ถ้า score ≥ alert_threshold
  → Console log
  → Telegram
  → LINE
```

### 5️⃣ **Execute Order** → ส่งคำสั่ง MT5

```
หากข้อมูลทั้งหมดตรงจึงส่ง
  entry = current price
  SL = entry - (ATR × multiplier)
  TP = entry + (ATR × multiplier × risk/reward)
  Size = risk_amount / (entry - SL)
```

### 6️⃣ **Log & Sync** → บันทึกลงฐานข้อมูล

```
บันทึก:
- สัญญาณ (signals table)
- ออเดอร์ (orders table)
- เหตุการณ์ (scan_events table)

ซิงก์สถานะจาก MT5
```

---

## 📊 Score & Category

```
Score         Category       Action
──────────────────────────────────
0-49          ignore         ✗ ignore
50-59         candidate      ✗ skip
60-69         alert          ✓ execute
70-79         strong         ✓ execute
80-100        premium        ✓ execute
```

---

## 🔒 Hard Filters (ต้องผ่านก่อน)

### BUY Signal ต้องผ่าน:

| Check | Condition | Soft Mode | Strict Mode |
|-------|-----------|-----------|-------------|
| **ADX** | ≥ minimum | Yes | Yes |
| **Entry Zone** | ≤ X ATR | Yes (×1.5) | Yes |
| **H4 Trend** | bullish | sideway OK + H1 bullish ~ | bullish only |
| **H1 Trend** | ≠ bearish | bear OK + M15 bull | bearish fail |
| **Lower TF** | NOT both bearish | one OK | one only |

**SELL Signal**: ตรงกันข้าม (bearish แทน bullish)

---

## 📈 Confidence Score Components

```python
# M15 (Setup Timeframe)
_score_higher_tf(H4, H1)           → 0-20 points (weight ×20%)
_score_ema(close vs EMA20/50/200)  → 0-15 points (weight ×15%)
_score_adx(ADX value)              → 0-10 points (weight ×10%)
_score_structure(HH/HL or LH/LL)   → 0-10 points (weight ×10%)
_score_setup_quality(candle type)  → 0-12 points (weight ×12%)
_score_rsi_context(RSI zone)       → 0-8  points (weight ×8%)
_score_macd_confirmation(MACD)     → 0-8  points (weight ×8%)
_score_bollinger_context(bands)    → 0-4  points (weight ×4%)

# M5 (Trigger Timeframe)
_score_stoch_trigger(Stoch %)      → 0-5  points (weight ×5%)
_score_volume_confirmation(spike)  → 0-5  points (weight ×5%)
_score_atr_suitability(ATR ratio)  → 0-3  points (weight ×3%)

TOTAL = (weighted sum) / 100 × 100 = 0-100
```

---

## 🚨 Anti-Duplicate Alert Logic

```
Signal passes score ✓
  ↓
Hard filters passed ✓
  ↓
No prior alert?
  → ALERT (first time!)
  ↓
Same candle as last alert?
  → SKIP (don't repeat same candle)
  ↓
Score improved 5+ points?
  → ALERT (score improved significantly)
  ↓
Was invalidated (dropped below watchlist)?
  → ALERT (new setup!)
  ↓
Otherwise?
  → SKIP (avoid spam)
```

---

## ⚙️ Execution Precheck

```
PRECHECK BEFORE SENDING ORDER:

DRY_RUN enabled?           → SKIP
Below min category?        → SKIP
Daily loss guard active?   → SKIP
Cooldown active?           → SKIP
MT5 not connected?         → SKIP
Symbol disabled?           → SKIP

All OK?
  → GET CURRENT PRICE
  → CALCULATE VOLUME
  → BUILD ORDER
  → SEND TO MT5
```

---

## 💾 Database Schema

### signals table
```
id, timestamp, symbol, normalized_symbol, direction, score, category,
price, reason_summary, timeframe_summary_json, indicator_snapshot_json,
component_scores_json, trade_plan_json, hard_filters_passed,
hard_filter_reasons_json
```

### orders table
```
id, timestamp, symbol, normalized_symbol, direction, category, score,
entry_price, stop_loss, take_profit, volume, risk_amount,
status (sent/failed/closed/skipped), reason,
mt5_order, mt5_position, comment,
partial_close_done, pnl, closed_at
```

### scan_events table
```
id, timestamp, symbol, level (INFO/WARNING), message, details_json
```

### symbol_states table
```
symbol, direction (PK),
last_alert_candle_time, last_score, invalidated
```

---

## 📋 Config Profiles

### PROFILE_PRESETS

```
AGGRESSIVE         NORMAL (Default)    STRICT
─────────────────────────────────────────────
ADX ≥ 12          ADX ≥ 14            ADX ≥ 18
Entry ≤ 3.5 ATR   Entry ≤ 3.0 ATR     Entry ≤ 1.8 ATR
Watchlist ≥ 35    Watchlist ≥ 50      Watchlist ≥ 75
Alert ≥ 45        Alert ≥ 60          Alert ≥ 85

→ More signals    → Balanced          → Fewer, quality
→ More false +    → Standard          → Fewer false +
```

### ASSET_PROFILE_PRESETS

```
DEFAULT                CRYPTO_MAJOR (BTC, ETH)
────────────────────────────────────────────
ADX: inherited         ADX: 14.0 (stricter)
RSI buy: 50-70         RSI buy: 48-68 (tighter)
SL ATR: inherited      SL ATR: 1.60 (wider)
Target RR: inherited   Target RR: 1.90 (tighter)
Risk %: 1.00           Risk %: 0.90 (conservative)
```

---

## 🔄 Running Modes

### Scan Once (One-time scan)
```bash
python main.py --mode scan --once
```
- Scans all symbols once
- Evaluates signals
- Sends alerts
- Tries execution
- Exits

### Daemon (Continuous scanning)
```bash
python main.py --mode scan
```
- Scans continuously every `scan_interval_seconds`
- Keeps running until stopped
- Updates persistent state in DB

### Sync Orders
```bash
python main.py --mode sync
```
- Reads sent orders from DB
- Checks MT5 for status updates
- Updates closed orders and PnL
- Exits

### Dashboard (Web UI)
```bash
streamlit run streamlit_app.py
```
- Opens analytics dashboard
- Read-only operations
- Shows trades, performance, config

---

## 🛡️ Risk Management

### Daily Loss Guard
```
Rule: stop trading if realized_loss > daily_loss_limit_pct

Example:
  Account: $10,000
  Limit: 2% = $200
  
  Closed trades today:
  - Trade 1: -$100
  - Trade 2: +$50
  - Trade 3: -$80
  
  Total: -$130 (safe, within $200 limit)
  
  Trade 4 closes: -$90
  Total: -$220 → EXCEEDS $200
  
  Action: STOP sending new trades until daily reset
  Reset: at 00:00 UTC (configurable)
```

### Cooldown Period
```
Rule: wait N minutes after entry before same direction on same symbol

Example:
  BUY BTCUSD at 10:00
  Cooldown: 60 minutes
  
  Next BUY BTCUSD can be sent after 11:00
  SELL BTCUSD can be sent after 10:00 (different direction, no cooldown)
```

### Per-Trade Risk Sizing
```
Risk = account_balance × (risk_per_trade_pct / 100)
Volume = Risk / (entry - SL)

Example:
  Balance: $10,000
  Risk %: 1% = $100
  Entry: 100
  SL: 98
  
  Volume = $100 / (100 - 98) = 50 contracts
```

---

## 🔗 Configuration Hierarchy

```
Environment Variables (.env)
         ↓
   config.py (parse)
         ↓
   PROFILE_PRESETS[selected_profile]
         ↓
   ASSET_PROFILE_PRESETS[asset_profile]
         ↓
    Final Configuration
```

**Override Priority**:
1. `asset_profile[key]` (if not None) → highest
2. `profile_preset[key]` (if not None)
3. `default_value` → lowest

Example:
```python
# If crypto_major asset profile says:
# "adx_minimum": 14.0
# But "normal" profile says:
# "adx_minimum": 14.0
# → Use 14.0 from asset profile (both same anyway)

# But if profile says:
# "adx_minimum": 14.0
# And asset says:
# "adx_minimum": None
# → Use 14.0 from profile

# And if both None?
# → Use hardcoded default (18.0)
```

---

## 📊 Key Metrics Tracked

| Metric | Definition | Use |
|--------|-----------|-----|
| Win Rate | Wins / Total Trades | Performance |
| Profit Factor | Gross Profit / Gross Loss | Quality |
| Max Drawdown | Peak-to-Trough Loss | Risk |
| Sharpe Ratio | Return / Volatility | Risk-Adjusted Return |
| Daily Realized Loss | Sum of closed PnL today | Risk Guard |
| Equity Curve | Cumulative PnL over time | Progress |

---

## 🔧 Troubleshooting Quick Guide

### Signal not alerting?
```
Check:
1. score < alert_threshold?     → Increase sensitivity
2. hard_filters_passed = False? → Check reason
3. Same candle as last alert?   → Wait for new candle
4. Invalidated state?           → Score needs to improve 5+ pts
```

### Order not executing?
```
Check:
1. dry_run = True?              → Set to False
2. signal.category < min_exec?  → Lower threshold
3. Daily loss guard active?     → Reset or wait
4. Cooldown active?             → Wait for cooldown
5. MT5 not connected?           → Reconnect MT5
6. Symbol trading disabled?     → Check symbol rights
```

### Alert going to Telegram but not LINE?
```
Check:
1. line_enabled = True?         → Set in .env
2. line_token valid?            → Verify token
3. Format correct?              → Should be Bearer token
```

---

## 📚 Files Created by System

### Logging
- `logs/` folder
- `logs/pytrade.log` (main log)
- `logs/pytrade_YYYYMMDD.log` (daily)

### Database
- `trade_signals.db` (SQLite)
  - signals, orders, scan_events, symbol_states, runtime_state, config_audit

### Runtime State
- `.runtime/daemon_pid.json` (process IDs)
- `.runtime/dashboard_port.json` (web server port)

### Configuration
- `.env` (environment variables)
- `config.py` (default settings)

---

## 🚀 Typical Workflow

### Starting Fresh
```
1. Install:     py -m pip install -r requirements.txt
2. Configure:   copy .env.example → .env
3. Edit .env:   MT5_PATH, LOGIN, PASSWORD, SERVER
4. Test:        python main.py --mode scan --once
5. Launch:      scripts/Run-Dashboard.bat + scripts/Run-Daemon.bat
```

### Daily Operations
```
Morning:
  - Open Dashboard (check overnight signals/trades)
  - Monitor daemon process (Task Manager)

During market:
  - Dashboard updates real-time
  - Alerts via Telegram/LINE as they happen

Evening:
  - Review performance in Dashboard
  - Check log files if issues
  - Adjust config if needed (reload daemon)

Before market close:
  - Check if any open positions
  - Consider manual closes if needed
```

### Adjustments
```
If too many false alerts:
  - Increase alert_threshold
  - Switch to "strict" profile
  - Increase ADX_MINIMUM

If too few signals:
  - Decrease watchlist_threshold
  - Switch to "aggressive" profile
  - Decrease entry_zone_max_atr

If execution not firing:
  - Check min_execute_category
  - Verify execution_enabled = True
  - Check daily_loss_limit
```

---

---

**เสร็จสิ้น!**

📖 **สำหรับข้อมูลเพิ่มเติม**:
- `CODE_ANALYSIS_TH.md` - วิเคราะห์โค้ดเชิงลึก
- `DETAILED_FLOW_ANALYSIS_TH.md` - ลำดับการทำงานและ diagrams
- `FUNCTION_REFERENCE_TH.md` - รายละเอียดของแต่ละฟังก์ชัน
