# การไหลของข้อมูล (Data Flow) และลำดับการทำงาน

## 1. Scan Loop Flow

```
START DAEMON
    ↓
┌─────────────────────────────┐
│  FOR EACH SYMBOL IN LIST    │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│   FETCH MULTI-TIMEFRAME     │
│   H4, H1, M15, M5 (OHLCV)   │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  CALCULATE INDICATORS FOR   │
│  EACH TIMEFRAME             │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  EVALUATE BUY SIGNAL        │
│  (Hard Filters + Scoring)   │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  EVALUATE SELL SIGNAL       │
│  (Hard Filters + Scoring)   │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  DECIDE BEST SIGNAL (BUY    │
│  or SELL based on score)    │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│  SAVE SIGNAL TO DB          │
└─────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  SHOULD ALERT?                  │
│  (Anti-duplicate check)         │
└─────────────────────────────────┘
    ↓
    ├─ YES → SEND ALERT (Console/Telegram/LINE)
    │         UPDATE SYMBOL STATE
    │
    └─ NO → (skip)
    ↓
┌─────────────────────────────────┐
│  EXECUTION ENABLED?             │
└─────────────────────────────────┘
    ├─ YES → TRY EXECUTE SIGNAL
    │         ├─ Precheck (DRY_RUN, Loss Guard, etc.)
    │         ├─ Get MT5 Symbol Info
    │         ├─ Calculate Volume
    │         ├─ Build Order Request
    │         ├─ Send Order
    │         └─ Log to DB
    │
    └─ NO → (skip)
    ↓
┌─────────────────────────────────┐
│  EVERY N SCANS:                 │
│  SYNC OLD ORDERS WITH MT5       │
│  (update status, PnL, etc.)     │
└─────────────────────────────────┘
    ↓
SLEEP(scan_interval)
    ↓
LOOP (if not --once mode)
```

## 2. Signal Evaluation - Hard Filters

```
INPUT: MTF Data (H4, H1, M15, M5) + Config + Asset Profile
    ↓
┌─────────────────────────────────────────────────┐
│  DETECT TRENDS FOR ALL TIMEFRAMES               │
│  (EMA alignment analysis)                        │
│  → H4_trend, H1_trend, M15_trend, M5_trend      │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  CHECK ADX STRENGTH                             │
│  ADX ≥ asset_minimum?                           │
└─────────────────────────────────────────────────┘
    ├─ NO → FAIL: "ADX too low"
    └─ YES → continue
    ↓
┌─────────────────────────────────────────────────┐
│  CHECK ENTRY ZONE (price vs EMA20)              │
│  distance ≤ entry_zone_max_atr?                 │
└─────────────────────────────────────────────────┘
    ├─ NO → FAIL: "Price too far from entry zone"
    └─ YES → continue
    ↓
FOR BUY SIGNAL:
┌─────────────────────────────────────────────────┐
│  CHECK H4 TREND                                 │
│  H4 = bullish?                                  │
│  (or soft mode: H4 sideway + H1 bullish?)       │
└─────────────────────────────────────────────────┘
    ├─ NO → FAIL: "H4 bearish conflict"
    └─ YES → continue
    ↓
┌─────────────────────────────────────────────────┐
│  CHECK H1 TREND                                 │
│  H1 ≠ bearish?                                  │
│  (or soft mode: H1 bearish + M15 bullish?)      │
└─────────────────────────────────────────────────┘
    ├─ NO → FAIL: "H1 bearish conflict"
    └─ YES → continue
    ↓
┌─────────────────────────────────────────────────┐
│  CHECK LOWER TF CONFLICT                        │
│  NOT (M15 bearish + M5 bearish)?                │
└─────────────────────────────────────────────────┘
    ├─ NO → FAIL: "Severe lower TF conflict"
    └─ YES → PASS ALL HARD FILTERS ✓
    ↓
OUTPUT: (hard_filters_passed, reasons_list)
```

## 3. Confidence Score Calculation

```
INPUT: Direction (BUY/SELL) + MTF Data + Asset Profile + Weights
    ↓
M15 (Setup Timeframe):
    ├─ _score_higher_tf()          → points × weight
    ├─ _score_ema()                → points × weight
    ├─ _score_adx()                → points × weight
    ├─ _score_structure()          → points × weight
    ├─ _score_setup_quality()      → points × weight
    ├─ _score_rsi_context()        → points × weight
    ├─ _score_macd_confirmation()  → points × weight
    ├─ _score_bollinger_context()  → points × weight
    └─ SUM_M15 = weighted scores
    ↓
M5 (Trigger Timeframe):
    ├─ _score_stoch_trigger()      → points × weight
    ├─ _score_volume_confirmation()→ points × weight
    ├─ _score_atr_suitability()    → points × weight
    └─ SUM_M5 = weighted scores
    ↓
┌─────────────────────────────────┐
│  NORMALIZE SUM_M15 + SUM_M5     │
│  to 0-100 range                 │
└─────────────────────────────────┘
    ↓
OUTPUT: confidence_score ∈ [0, 100]
        component_scores: {name: points, ...}
```

## 4. Execution Flow

```
INPUT: SignalResult (BUY/SELL)
    ↓
┌──────────────────────────────────┐
│ PRECHECK                         │
└──────────────────────────────────┘
    ├─ DRY_RUN enabled?
    │  └─ YES → SKIP (return "dry_run_enabled")
    │
    ├─ Signal category < min_execute_category?
    │  └─ YES → SKIP (return "below_min_execute_category")
    │
    ├─ Daily Loss Guard triggered?
    │  └─ YES → SKIP (return "daily_loss_guard_active")
    │
    ├─ Cooldown active?
    │  └─ YES → SKIP (return "cooldown_active")
    │
    ├─ MT5 not connected?
    │  └─ YES → SKIP (return "mt5_not_connected")
    │
    └─ ALL OK ✓ → Continue
    ↓
┌──────────────────────────────────┐
│ GET MT5 SYMBOL INFO              │
│ (tick size, volume min, etc.)    │
└──────────────────────────────────┘
    ├─ symbol_info unavailable?
    │  └─ YES → FAIL (log "symbol_info_unavailable")
    │
    ├─ Trading disabled on symbol?
    │  └─ YES → SKIP (log "symbol_trade_disabled")
    │
    └─ INFO OK ✓ → Continue
    ↓
┌──────────────────────────────────┐
│ GET CURRENT PRICE                │
│ (ask for BUY, bid for SELL)      │
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│ RESOLVE RISK AMOUNT              │
│ (Static or Dynamic from MT5)     │
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│ CALCULATE VOLUME                 │
│ volume = risk / (abs(entry - sl) │
│          × point × tick_value)   │
└──────────────────────────────────┘
    ├─ volume ≤ 0?
    │  └─ YES → FAIL (log "invalid_volume")
    │
    └─ volume OK ✓ → Continue
    ↓
┌──────────────────────────────────┐
│ BUILD ORDER REQUEST              │
│ {action, symbol, volume, type,   │
│  price, sl, tp, deviation,       │
│  magic, comment, filling, ...}   │
└──────────────────────────────────┘
    ↓
┌──────────────────────────────────┐
│ SEND ORDER TO MT5                │
│ mt5.order_send(request)          │
└──────────────────────────────────┘
    ├─ order_send returned None?
    │  └─ YES → FAIL (log "order_send_none")
    │
    ├─ retcode ≠ TRADE_RETCODE_DONE?
    │  └─ YES → FAIL (log "retcode: X")
    │
    └─ retcode = TRADE_RETCODE_DONE ✓
    ↓
┌──────────────────────────────────┐
│ LOG SUCCESS: order sent          │
│ Save to orders table (status     │
│ = "sent")                        │
└──────────────────────────────────┘
```

## 5. Anti-Duplicate Alert Logic

```
INPUT: SignalResult
    ↓
┌─────────────────────────────┐
│ SCORE MEETS THRESHOLD?      │
│ score ≥ alert_threshold?    │
└─────────────────────────────┘
    ├─ NO → DON'T ALERT (return False)
    └─ YES → continue
    ↓
┌─────────────────────────────┐
│ HARD FILTERS PASSED?        │
└─────────────────────────────┘
    ├─ NO → DON'T ALERT (return False)
    └─ YES → continue
    ↓
┌─────────────────────────────┐
│ GET LAST SYMBOL STATE       │
│ (symbol, direction)         │
└─────────────────────────────┘
    ├─ No prior state?
    │  └─ ALERT (return True) - First time!
    │
    └─ Has prior state → continue
    ↓
┌─────────────────────────────┐
│ SAME CANDLE?                │
│ last_alert_candle_time ==   │
│ current timestamp?          │
└─────────────────────────────┘
    ├─ YES → DON'T ALERT (return False)
    └─ NO → continue
    ↓
┌─────────────────────────────┐
│ SCORE IMPROVED SIGNIFICANTLY?
│ current_score ≥ last_score  │
│ + anti_dup_score_delta?     │
└─────────────────────────────┘
    ├─ YES → ALERT (return True)
    └─ NO → continue
    ↓
┌─────────────────────────────┐
│ WAS INVALIDATED?            │
│ invalidated = True?         │
└─────────────────────────────┘
    ├─ YES → ALERT (return True) - New setup!
    └─ NO → DON'T ALERT (return False)
```

## 6. Database Operations Timeline

```
SCAN START (t=0)
    ↓
t=0.1: _prepare_mtf_data()
       └─ (no DB writes)
    ↓
t=0.5: evaluate_buy_signal() + evaluate_sell_signal()
       └─ (no DB writes yet)
    ↓
t=1.0: save_signal_to_db(buy_signal)
       └─ INSERT into signals table
    ↓
t=1.1: save_signal_to_db(sell_signal)
       └─ INSERT into signals table
    ↓
t=1.2: mark_invalidation() [if score < watchlist]
       └─ UPDATE symbol_states
    ↓
t=1.3: should_alert() + send_alert()
       ├─ SELECT from symbol_states
       └─ UPSERT into symbol_states
    ↓
t=1.4: executor.try_execute_signal()
       ├─ (MT5 API call)
       └─ (no DB write if skipped, or INSERT into orders)
    ↓
SCAN END (t=1.5)
```

## 7. Module Dependency Graph

```
┌────────────────────────────────────────┐
│         main.py (CLI Entry)            │
└────────────────────────────────────────┘
              │
    ┌─────────┼─────────┬────────────┐
    │         │         │            │
   config   logger_db   DATABASE    mt5_connector
    │         │         INIT        │
    │         │                     │
    v         v                     v
  ┌─────────────────────────────────────┐
  │  Signal Evaluation Loop             │
  ├─────────────────────────────────────┤
  │                                     │
  │  ├─ data_fetcher                   │
  │  │  └─ mt5_connector.get_symbols() │
  │  │                                  │
  │  ├─ symbol_manager                 │
  │  │  └─ normalize_symbol_name()      │
  │  │                                  │
  │  ├─ indicators.calculate_indicators │
  │  │  ├─ EMA, RSI, MACD, ADX, ...    │
  │  │  └─ detect_trend()              │
  │  │                                  │
  │  ├─ signal_engine                  │
  │  │  ├─ evaluate_buy_signal()       │
  │  │  ├─ evaluate_sell_signal()      │
  │  │  └─ _hard_filters()             │
  │  │                                  │
  │  ├─ scorer                         │
  │  │  └─ calculate_confidence()      │
  │  │                                  │
  │  ├─ risk_engine                    │
  │  │  └─ build_trade_plan()          │
  │  │                                  │
  │  ├─ logger_db                      │
  │  │  └─ save_signal_to_db()         │
  │  │                                  │
  │  ├─ notifier                       │
  │  │  ├─ should_alert()              │
  │  │  └─ send_alert()                │
  │  │  └─ mark_invalidation()         │
  │  │                                  │
  │  └─ execution                      │
  │     ├─ try_execute_signal()        │
  │     ├─ _calc_volume()              │
  │     └─ sync_orders()               │
  │                                     │
  └─────────────────────────────────────┘
         │
         v
    ┌──────────────┐
    │  Logger DB   │
    │  (SQLite)    │
    └──────────────┘
         │
         v
    ┌──────────────────────────┐
    │  streamlit_app.py        │
    │  (Dashboard Read-Only)   │
    └──────────────────────────┘
```

## 8. Configuration Profile Impact

```
PROFILE: aggressive
├─ ADX_MINIMUM: 12.0          (most permissive)
├─ ENTRY_ZONE_MAX_ATR: 3.5
├─ WATCHLIST_THRESHOLD: 35
└─ ALERT_THRESHOLD: 45


PROFILE: normal (default)
├─ ADX_MINIMUM: 14.0          (balanced)
├─ ENTRY_ZONE_MAX_ATR: 3.0
├─ WATCHLIST_THRESHOLD: 50
└─ ALERT_THRESHOLD: 60


PROFILE: strict
├─ ADX_MINIMUM: 18.0          (most restrictive)
├─ ENTRY_ZONE_MAX_ATR: 1.8
├─ WATCHLIST_THRESHOLD: 75
└─ ALERT_THRESHOLD: 85
```

## 9. Asset-Specific Profile Overrides

```
ASSET_PROFILE: "crypto_major" (e.g., BTC, ETH)
├─ ADX_MINIMUM: 14.0          (stricter than default)
├─ RSI_BUY_LOW: 48.0
├─ RSI_BUY_HIGH: 68.0         (tighter range)
├─ RSI_SELL_LOW: 32.0
├─ RSI_SELL_HIGH: 52.0
├─ VOLUME_SPIKE_RATIO: 1.15   (less spike required)
├─ STOCH_BUY_MAX: 35.0
├─ STOCH_SELL_MIN: 65.0       (wider band)
├─ SL_ATR_MULTIPLIER: 1.60    (wider stop)
├─ TARGET_RR: 1.90            (tighter ratio)
└─ RISK_PCT_MULTIPLIER: 0.90  (lower risk)
```

---

เสร็จสิ้นการอธิบายลำดับการทำงาน!
