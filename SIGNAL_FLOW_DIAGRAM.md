# Complete Signal Generation & Execution Flow

```mermaid
graph TD
    START([SCAN START]) --> MTF["📊 Fetch MTF Data<br/>H4 | H1 | M15 | M5"]
    
    MTF --> CALC["🔧 Calculate Indicators<br/>EMA | RSI | MACD | Stoch<br/>ATR | BB | Volume | ADX"]
    
    CALC --> EVAL["⬤ Evaluate Directions<br/>BUY Signal? | SELL Signal?"]
    
    EVAL --> HF["⛔ HARD FILTERS (Must All Pass)"]
    
    HF --> HF1["✓ ADX >= Minimum?<br/>max(H1.adx, M15.adx) >= 18"]
    HF --> HF2["✓ Entry Zone OK?<br/>distance <= 1.8 * ATR"]
    HF --> HF3["✓ Trend Alignment?<br/>H4 bullish, H1 not bearish"]
    HF --> HF4["✓ No Severe Conflict?<br/>Not (M15 bearish AND M5 bearish)"]
    
    HF1 & HF2 & HF3 & HF4 --> HFR{All Filters<br/>Pass?}
    
    HFR -->|NO| IGNORE["❌ Category=IGNORE<br/>Reason: HF Failed"]
    HFR -->|YES| SCORE["🎯 SCORING (11 Components)<br/>Max 100 points"]
    
    SCORE --> S1["higher_tf: +20"]
    SCORE --> S2["ema_alignment: +15"]
    SCORE --> S3["adx_strength: +10"]
    SCORE --> S4["market_structure: +10"]
    SCORE --> S5["setup_quality: +12"]
    SCORE --> S6["rsi_context: +8"]
    SCORE --> S7["macd_confirmation: +8"]
    SCORE --> S8["stoch_trigger: +5"]
    SCORE --> S9["volume_confirmation: +5"]
    SCORE --> S10["bollinger_context: +4"]
    SCORE --> S11["atr_suitability: +3"]
    
    S1 & S2 & S3 & S4 & S5 & S6 & S7 & S8 & S9 & S10 & S11 --> TOTAL["Total Score = Σ Clamped"]
    
    TOTAL --> TRIG["🔥 M5 TRIGGERS (Must Have Min Required)"]
    TRIG --> T1["1️⃣ Momentum Candle?<br/>Body/Range >= 50% + breaks"]
    TRIG --> T2["2️⃣ MACD Cross?<br/>Below → Above signal line"]
    TRIG --> T3["3️⃣ Stoch Cross?<br/>K cross above D + low zone"]
    TRIG --> T4["4️⃣ Volume Spike?<br/>Vol >= 1.2x SMA20"]
    
    T1 & T2 & T3 & T4 --> TRIGC{Trigger Count<br/>>= Min?}
    
    TRIGC -->|NO| CAND["📌 Category=CANDIDATE<br/>Score confirmed but awaiting trigger"]
    TRIGC -->|YES| CAT["📊 Classify by Score"]
    
    CAT --> CATCHECK{"Score<br/>Range?"}
    CATCHECK -->|< 50| CAT1["❌ ignore"]
    CATCHECK -->|50-60| CAT2["🟡 candidate"]
    CATCHECK -->|60-70| CAT3["🟢 alert"]
    CATCHECK -->|70-80| CAT4["🔵 strong"]
    CATCHECK -->|80-93| CAT5["🟣 premium"]
    CATCHECK -->|>= 93| CAT6["🌟 ultra"]
    
    CAT1 & CAT2 & CAT3 & CAT4 & CAT5 & CAT6 --> ALERT["📢 Send Alert?<br/>category >= MIN_ALERT_CATEGORY"]
    
    ALERT --> EXEC["⚙️  PRE-EXECUTION CHECKS"]
    EXEC --> E1["✓ ENABLE_EXECUTION=true?"]
    EXEC --> E2["✓ EXECUTION_MODE=demo?"]
    EXEC --> E3["✓ signal.category >= MIN_EXECUTE?<br/>premium >= premium"]
    EXEC --> E4["✓ Open Orders < Max?<br/>1 + 2 + 3 = 6 max"]
    EXEC --> E5["✓ Daily Loss < 120 USD?"]
    EXEC --> E6["✓ Cooldown Passed?<br/>30 min since last"]
    EXEC --> E7["✓ Account Trade Mode = DEMO?"]
    
    E1 & E2 & E3 & E4 & E5 & E6 & E7 --> EXECR{All Checks<br/>Pass?}
    
    EXECR -->|NO| SKIP["⏭️ SKIP<br/>Reason logged"]
    EXECR -->|YES| RISK["💰 RISK CALC"]
    
    RISK --> R1["Risk Amount = 10000 * 0.15% = 15 USD"]
    RISK --> R2["SL Distance = ATR * 1.5"]
    RISK --> R3["TP Distance = SL * 1.8 (RR)"]
    RISK --> R4["Volume = Risk / SL_Distance"]
    
    R1 & R2 & R3 & R4 --> ORDER["📝 Build MT5 Order"]
    ORDER --> SEND["📤 mt5.order_send()"]
    
    SEND --> SENDOK{Order<br/>Sent?}
    SENDOK -->|REJECTED| FAIL["❌ FAILED<br/>Log: refcode"]
    SENDOK -->|SENT| DB["✅ Log to Database<br/>status=SENT"]
    
    DB --> SYNC["🔄 SYNC PHASE (every 30s)"]
    SYNC --> SYNCK["✓ Check MT5 orders<br/>✓ Update position status<br/>✓ Calculate realized PnL<br/>✓ Update daily loss"]
    
    SYNCK --> REPEAT["🔁 Repeat next scan cycle"]
    
    IGNORE --> REPEAT
    CAND --> REPEAT
    SKIP --> REPEAT
    FAIL --> REPEAT
    
    REPEAT --> START
    
    style HF fill:#ff9999
    style SCORE fill:#99ccff
    style TRIG fill:#ffcc99
    style EXEC fill:#ff99ff
    style RISK fill:#99ff99
    style DB fill:#90EE90
    style START fill:#FFE4B5
```

---

## Signal Status Examples

### ✅ Example 1: SUCCESSFUL EXECUTION
```
BTCUSD BUY
├─ Hard Filters: ✓✓✓✓ (All pass)
├─ Score: 87/100 = "premium"
├─ M5 Triggers: 4/4 (All present)
├─ Pre-Exec: ✓✓✓✓✓✓✓ (All clear)
├─ Risk: 15 USD on 1.5 ATR SL
├─ Volume: 0.1 lot
└─ Status: ✅ SENT to MT5
```

### ⚠️ Example 2: HARD FILTER REJECTION
```
ETHUSD BUY
├─ Hard Filters:
│  ├─ ADX: 12.5 < 18.0 ✗ REJECT
│  ├─ Entry Zone: OK ✓
│  ├─ Trend: OK ✓
│  └─ Conflict: OK ✓
├─ Score: Not calculated (early exit)
└─ Status: ❌ IGNORE (reason: ADX too low)
```

### ⏸️ Example 3: INSUFFICIENT M5 TRIGGERS
```
SOCUSD BUY
├─ Hard Filters: ✓✓✓✓ (All pass)
├─ Score: 72/100 = "strong"
├─ M5 Triggers: 2/4
│  ├─ Momentum: YES ✓
│  ├─ MACD: NO ✗
│  ├─ Stoch: YES ✓
│  └─ Volume: NO ✗
├─ Min Required: 2
└─ Status: 📌 CANDIDATE (score ok, awaiting trigger completion)
```

### 🚫 Example 4: MIN_EXECUTE_CATEGORY REJECTION
```
XRPUSD BUY
├─ Hard Filters: ✓✓✓✓
├─ Score: 75/100 = "strong"
├─ M5 Triggers: ✓✓✓✓
├─ Category: "strong" < "premium" (MIN_EXECUTE)
└─ Status: ⏭️ SKIPPED (reason: below_min_execute_category)
           (Alert sent if >= alert_threshold, but NOT executed)
```

### 💼 Example 5: MAX POSITIONS REACHED
```
6th Signal Arrives
├─ All checks pass ✓
├─ Current open: 6/6 (1 base + 2 premium + 3 ultra)
└─ Status: ⏭️ SKIPPED (reason: max_open_positions_reached)
           (Will retry when position closes)
```

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ⛔ | Hard filter stage |
| 🎯 | Scoring stage |
| 🔥 | Trigger verification |
| ⚙️ | Pre-execution checks |
| 💰 | Risk management |
| ✅ | Success |
| ❌ | Failure/Rejected |
| ⏭️ | Skipped |
| 📌 | Waiting/Candidate |
| 🔄 | Loop/Repeat |
| 📢 | Alert notification |
| 📤 | Order submission |

---

## Key Decision Points Summary

| Gate | Input | Output | Failure Action |
|------|-------|--------|-----------------|
| Hard Filters | MTF trends, ADX, entry zone | Pass/Fail | → IGNORE |
| Scoring | 11 indicators | Score 0-100 | N/A (categorize) |
| M5 Triggers | 4 candle confirms | Count 0-4 | → CANDIDATE (if insufficient) |
| Signal Category | Score threshold | ignore/candidate/alert/.../ultra | Depends on threshold |
| Pre-Exec Checks | 7 system conditions | Pass/Fail | → SKIP |
| Risk Calc | Balance, ATR, RR | Risk amount, volume | Set defaults |
| Order Send | MT5 API | Sent/Failed | → ERROR LOG |

