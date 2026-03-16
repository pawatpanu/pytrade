# 🔧 PyTrade Signal Issues - Troubleshooting & Optimization

**วันที่**: 2026-03-16  
**Issue**: ระบบแจ้งเตือน (alert) ออกแต่ไม่ส่งออเดอร์ (execution skipped)

---

## 🚨 Problem: "Execution skipped BUY ... below_min_execute_category"

### 📝 Root Cause

```
Signal met all hard filters ✓
Signal got scored adequately ✓
BUT: signal.category < MIN_EXECUTE_CATEGORY

Current config:
├─ signal.category = "strong" (score 70-80)
├─ MIN_EXECUTE_CATEGORY = "premium" (score 80-93)
└─ Result: "strong" < "premium" → ⏭️ SKIP
```

### 🎯 Why This Happens

Your `.env` is set to:
```
MIN_EXECUTE_CATEGORY=premium     ← Only execute premium+ signals
MIN_ALERT_CATEGORY=premium       ← Only alert premium+ signals
```

This means **BOTH** alert AND execution require "premium" tier.

---

## ✅ Solution Options

### Option 1: Lower MIN_EXECUTE_CATEGORY (Aggressive)

```bash
# .env
MIN_ALERT_CATEGORY=premium          # Keep premium for alerts
MIN_EXECUTE_CATEGORY=strong         # Execute "strong" too
```

**Effect:**
- Still only **alert** on premium+ signals
- But **execute** strong signals too
- More orders processed, more risk

**Config impact:**
```
strong tier = score 70-80
After change: Score 70+ signals CAN execute
```

---

### Option 2: Lower Both to "alert" (Moderate)

```bash
# .env
MIN_ALERT_CATEGORY=alert            # Alert on score 60+
MIN_EXECUTE_CATEGORY=strong         # Execute on score 70+
```

**Effect:**
- More alerts (informational)
- Execute at "strong" tier
- Good compromise

---

### Option 3: Keep Premium But Increase Score Weights (Advanced)

Keep MIN_EXECUTE_CATEGORY=premium BUT increase scoring thresholds:

**Current weights sum = 100 max**

```python
# In config.py, SIGNAL_PROFILE="custom" uses actual scores
# Increase these to let signals reach 80+ more easily:

"higher_tf": 20,            ← already max
"ema_alignment": 15,        ← already max
"setup_quality": 12,        ← consider +1-2
"adx_strength": 10,         ← consider +2
"volume_confirmation": 5,   ← consider +3
```

**To increase total possible:**
1. Read `config.py` ASSET_PROFILE_PRESETS
2. Adjust weights in your signal profile
3. Recalculate: More signals reach "premium" 80+ tier

---

## 🔍 Diagnostic: Why Aren't Signals Reaching Premium?

Run this check to see **actual scores**:

```bash
# Enable DEBUG logging
LOG_LEVEL=DEBUG

# Then check logs for lines like:
# [core.signal_engine] BUY BTCUSD score=75 category=strong components=[...]
```

**Look for:**
- Consistently scoring in 70-75 range? → Missing 5-10 points
- Which components are low? → Adjust those weights

**Common culprits:**

| Component | Issue | Fix |
|-----------|-------|-----|
| `higher_tf` | H4/H1 conflict too often | Lower `hard_filter_mode` to "soft" |
| `setup_quality` | Candlestick patterns weak | Adjust M15 candle parameters |
| `rsi_context` | RSI in wrong zones | Increase `rsi_buy_low`/`rsi_sell_high` ranges |
| `adx_strength` | ADX too strict | Lower `adx_minimum` in asset profile |
| `volume_confirmation` | Low volume baseline | Check data quality from MT5 |

---

## 🎯 Recommended Config (Balanced)

Based on your `.env` current state:

```bash
# .env - RECOMMENDED CHANGES

# Execution Thresholds
MIN_ALERT_CATEGORY=strong           # Alert on 70+
MIN_EXECUTE_CATEGORY=strong         # Execute on 70+
DRY_RUN=false                        # Strict mode OK for safety

# Position Management
MAX_OPEN_POSITIONS=1
PREMIUM_STACK_EXTRA_SLOTS=1         # Reduce to 1 (was 2)
ULTRA_STACK_EXTRA_SLOTS=2           # Reduce to 2 (was 3)

# Risk Management  
DAILY_LOSS_LIMIT=100.00             # Reduce to 100 (was 120) - safer
ORDER_COOLDOWN_MINUTES=20           # Reduce to 20 (was 30) - more frequent
RISK_PER_TRADE_PCT=1.0              # Increase from 0.15 to 1.0

# Scoring Sensitivity
SIGNAL_PROFILE=custom               # Use actual weighted scoring
```

**Rationale:**
- Lower MIN_EXECUTE to "strong" = more execution
- Reduce position limits = safer
- Increase risk% = risk actual capital (not tiny 15 USD)
- Reduce order cooldown = more signal frequency

---

## 🚀 Step-by-Step Fix

### Step 1: Quick Workaround (5 min)
```bash
# Edit .env
MIN_EXECUTE_CATEGORY=strong

# Restart daemon
.\Restart-All.bat
```

### Step 2: Monitor One Cycle
```bash
# Open logs
.\Open-Logs.bat

# Scan once manually
.\Scan-Once.bat

# Watch for:
# - "score=XX category=YYZ"
# - "Execution skipped" or "Order sent"
```

### Step 3: If Still Skipping
```
Check:
1. Signal profile (custom vs preset)?
2. Asset symbol profile assigned?
3. ADX minimum threshold too high?
4. Entry zone distance too tight?
5. Trend conflicts (H4/H1 mismatch)?
```

---

## 📊 Score Distribution Analysis

Here's what scores typically look like:

```
SCENARIO 1: Aggressive market (clear trend)
├─ Hard Filters: Pass ✓
├─ Higher TF: 20/20 ✓
├─ EMA align: 15/15 ✓
├─ ADX strength: 8/10 (decent)
├─ Setup: 10/12 (good candle)
├─ RSI: 6/8 (ok zone)
├─ MACD: 8/8 ✓
├─ Stoch: 5/5 ✓
├─ Volume: 3/5 (ok spike)
├─ Bollinger: 3/4 (acceptable)
├─ ATR: 2/3 (ok range)
└─ Total: 80/100 = "premium" ✓✓✓

SCENARIO 2: Choppy market (weak trend)
├─ Hard Filters: Pass ✓
├─ Higher TF: 15/20 (H1 conflict)
├─ EMA align: 13/15 (tight)
├─ ADX: 4/10 (weak trend) ← Problem
├─ Setup: 8/12 (ok candle)
├─ RSI: 5/8 (neutral zone)
├─ MACD: 5/8 (continuation only)
├─ Stoch: 3/5 (ok cross)
├─ Volume: 2/5 (low volume) ← Problem
├─ Bollinger: 2/4 (outside band)
├─ ATR: 1/3 (small range) ← Problem
└─ Total: 58/100 = "candidate" ✗

→ ADX, Volume, ATR too weak for premium
→ Need 22 more points to reach 80
```

---

## 🔧 Configuration Tuning Guide

### To Reach More Premium Signals:

#### Option A: Relax Hard Filters
```python
# config.py - Edit ASSET_PROFILE_PRESETS["crypto_major"]

"adx_minimum": 14.0,              # Lower from 18
"entry_zone_max_atr": 3.0,        # Relax from 2.6
"m5_min_triggers": 1,              # Lower from 2
```

#### Option B: Increase Scoring Weights
```python
# Redistribute 100 points to favor your indicators

Current conservative:
{
    "higher_tf": 20,
    "ema_alignment": 15,
    "setup_quality": 12,
    ...
}

Aggressive approach:
{
    "higher_tf": 20,               # Keep
    "ema_alignment": 15,           # Keep
    "setup_quality": 15,           # +3
    "rsi_context": 10,             # +2
    "macd_confirmation": 10,       # +2
    ...
}
```

#### Option C: Use Preset Profile
```bash
# .env
SIGNAL_PROFILE=aggressive

# This uses:
# - adx_minimum: 12.0 (vs strict 18)
# - entry_zone: 3.5 ATR (vs strict 1.8)
# - m5_min_triggers: 1 (vs strict 2)
# Result: More signals pass
```

---

## ⚠️ What NOT to Do

### ❌ DON'T: Set MIN_EXECUTE_CATEGORY=ignore
```
Why: Will execute every signal including junk ones (score 0-50)
Risk: Lots of losing trades
```

### ❌ DON'T: Set MIN_EXECUTE_CATEGORY=alert then execute immediately
```
Why: "alert" is only 60+ score (very weak)
Risk: High loss rate
```

### ❌ DON'T: Remove ADX filter entirely
```
Why: ADX is main trendstrength check
Risk: Open in choppy sideways market
```

### ❌ DON'T: Increase risk_per_trade_pct without testing
```
Current: 0.15% (small, safe)
If change to: 5% suddenly
Risk: Account blown in one bad run
```

---

## 📈 Optimal Path Forward

### Week 1: Conservative
```
MIN_EXECUTE_CATEGORY=strong    # Execute 70+
RISK_PER_TRADE_PCT=0.5%        # Small bets
MAX_OPEN_POSITIONS=1           # One at a time
DAILY_LOSS_LIMIT=100           # Tight stop
```

**Expected:** 2-4 signals per day, low DD

### Week 2: Moderate If Profitable
```
MIN_EXECUTE_CATEGORY=strong    # Keep
RISK_PER_TRADE_PCT=1.0%        # Double bet size
MAX_OPEN_POSITIONS=2           # Two parallel
DAILY_LOSS_LIMIT=200           # Loosen stop
```

### Week 3+: Advanced If +ve
```
Enable premium stacking
Unlock ultra signals (93+)
Monitor performance metrics
```

---

## 🎯 Decision Matrix

| Your Goal | Recommendation |
|-----------|-----------------|
| **See more trades** | MIN_EXECUTE=strong |
| **Safer small bets** | RISK_PER_TRADE_PCT=0.5, SCORE>=80 |
| **Higher hit rate** | Keep DRY_RUN=false, ADX>=18 |
| **More consistency** | Increase ORDER_COOLDOWN=30+ |
| **Aggressive growth** | SIGNAL_PROFILE=aggressive, 1% risk |

---

## 🔍 Log Interpretation

When you see:
```
INFO : Execution skipped BUY BTCUSD: below_min_execute_category
```

**Check this:**
1. What was the score? Look for line: `... score=XX category=strong`
2. Is strong < min? MIN_EXECUTE_CATEGORY=premium would skip "strong"
3. Count: How many skips vs executes? Ratio tells you if filters too tight

**To fix:**
```bash
# Edit .env
MIN_EXECUTE_CATEGORY=strong

# No other code changes needed
# Restart:
.\Restart-All.bat
```

---

## ✅ Verification Checklist

After making changes:

- [ ] Edit `.env` file
- [ ] Run `.\Restart-All.bat` (or reactivate daemon)
- [ ] Run `.\Scan-Once.bat` for manual test
- [ ] Check `logs/daemon.log` for execution
- [ ] Verify first order appears in database
- [ ] Check MT5 terminal for fill confirmation
- [ ] Monitor 1-2 cycles before leaving unattended

---

## 📞 Still Not Working?

### Gather Diagnostics:
```bash
# 1. Check environment is active
& c:\pytrade\.venv\Scripts\Activate.ps1

# 2. Run status check
.\Status-Check.bat

# 3. Check logs
type logs/daemon.log | Select-String "score"

# 4. Test one symbol manually
$env:SYMBOLS="BTCUSD"
python main.py --mode scan --once

# 5. Check database
python -c "from core.logger_db import SignalDB; db = SignalDB('signals.db'); print(db.count_open_orders())"
```

### Review:
- Hard filter failures? → Check ADX, entry zone, trends
- Score too low? → Check which component scores are weak
- Still below min? → Need to either lower threshold or tune weights

---

**Bottom Line:** 
🔴 **Most common issue:** MIN_EXECUTE_CATEGORY too high  
✅ **Quick fix:** Lower to "strong" (70+)  
📊 **Better fix:** Increase scoring weights for your asset  
🚀 **Best fix:** Test with conservative risk first, scale gradually
