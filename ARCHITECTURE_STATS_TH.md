# PyTrade Architecture & Statistics

## 📐 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│                    PYTRADE TRADING SYSTEM                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ DATA INPUT LAYER                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  MetaTrader5 Terminal                                            │
│    ↓                                                              │
│  MT5Connector (mt5_connector.py)                                 │
│    ├─→ initialize() [attempt 3 times]                            │
│    ├─→ login()                                                   │
│    ├─→ get_available_symbols()                                   │
│    └─→ shutdown()                                                │
│    ↓                                                              │
│  DataFetcher (data_fetcher.py)                                   │
│    ├─→ fetch_ohlcv(symbol, timeframe, bars)                      │
│    └─→ normalize data (time, volume, columns)                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ ANALYSIS LAYER                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Indicators Module (indicators.py)                               │
│    ├─→ EMA (20, 50, 200)                                         │
│    ├─→ RSI (14)                                                  │
│    ├─→ MACD (12/26/9)                                            │
│    ├─→ Bollinger Bands (20, 2)                                   │
│    ├─→ ADX (14)                                                  │
│    ├─→ ATR (14)                                                  │
│    ├─→ Stochastic (14, 3)                                        │
│    ├─→ Volume SMA (20)                                           │
│    ├─→ Optional: VWAP, Supertrend                                │
│    └─→ detect_trend(), detect_price_structure()                  │
│    ↓                                                              │
│  Signal Engine (signal_engine.py)                                │
│    ├─→ evaluate_buy_signal()                                     │
│    ├─→ evaluate_sell_signal()                                    │
│    └─→ _hard_filters() [critical gatekeeper]                     │
│    ↓                                                              │
│  DECISION POINT: Hard filters passed?                            │
│    ├─ NO  → candidate signal (score may be 0)                    │
│    └─ YES → evaluate confidence score                            │
│    ↓                                                              │
│  Scorer Module (scorer.py)                                       │
│    ├─→ _score_higher_tf() [20%]                                  │
│    ├─→ _score_ema() [15%]                                        │
│    ├─→ _score_adx() [10%]                                        │
│    ├─→ _score_structure() [10%]                                  │
│    ├─→ _score_setup_quality() [12%]                              │
│    ├─→ _score_rsi_context() [8%]                                 │
│    ├─→ _score_macd_confirmation() [8%]                           │
│    ├─→ _score_stoch_trigger() [5%]                               │
│    ├─→ _score_volume_confirmation() [5%]                         │
│    ├─→ _score_bollinger_context() [4%]                           │
│    └─→ _score_atr_suitability() [3%]                             │
│    ↓                                                              │
│  OUTPUT: confidence_score (0-100)                                │
│          component_scores (breakdown)                            │
│                                                                   │
│  Risk Engine (risk_engine.py)                                    │
│    ├─→ build_trade_plan()                                        │
│    ├─→ SL = entry ± (ATR × sl_atr_multiplier)                    │
│    ├─→ TP = entry ± (SL_dist × target_rr)                        │
│    ├─→ risk_amount = balance × (risk_pct / 100)                  │
│    └─→ position_size = risk_amount / SL_distance                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ DECISION & CONTROL LAYER                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Logger DB (logger_db.py) - PERSISTANCE                          │
│    ├─→ save_signal_to_db()                                       │
│    ├─→ log_scan_event()                                          │
│    ├─→ upsert_symbol_state() (anti-duplicate tracking)           │
│    └─→ log_order_sent(), sync_orders(), etc.                     │
│                                                                   │
│  Notifier (notifier.py) - ALERT LOGIC                            │
│    ├─→ should_alert()                                            │
│    │   ├─ score ≥ alert_threshold? ✓                             │
│    │   ├─ hard_filters_passed? ✓                                 │
│    │   ├─ not same candle as last alert? ✓                       │
│    │   ├─ score improved 5+ pts? ✓                               │
│    │   └─ was invalidated (new setup)? ✓                         │
│    │                                                              │
│    ├─→ send_alert()                                              │
│    │   ├─ Console (logger)                                       │
│    │   ├─ Telegram (if enabled + token valid)                    │
│    │   ├─ LINE (if enabled + token valid)                        │
│    │   └─ Update symbol_state in DB                              │
│    │                                                              │
│    └─→ mark_invalidation() [score dropped below watchlist]       │
│                                                                   │
│  Execution Engine (execution.py) - ORDER SENDING                 │
│    ├─→ try_execute_signal()                                      │
│    │                                                              │
│    ├─→ _precheck()                                               │
│    │   ├─ DRY_RUN enabled? → SKIP                                │
│    │   ├─ category < min_exec? → SKIP                            │
│    │   ├─ daily_loss_guard active? → SKIP                        │
│    │   ├─ cooldown active? → SKIP                                │
│    │   └─ MT5 ready? → SKIP                                      │
│    │                                                              │
│    ├─→ Get symbol info + tick price                              │
│    ├─→ Resolve risk_amount (static vs dynamic)                   │
│    ├─→ Calculate volume (_calc_volume)                           │
│    ├─→ Build MT5 order request                                   │
│    ├─→ Send order (mt5.order_send)                               │
│    └─→ Log result (sent/failed)                                  │
│                                                                   │
│  Order Synchronization                                           │
│    └─→ sync_orders()                                             │
│        ├─ Query DB for "sent" orders                             │
│        ├─ Check MT5 for deal status                              │
│        ├─ Update order status → "closed"                         │
│        ├─ Calculate PnL                                          │
│        └─ Update daily loss counter                              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PERSISTENCE LAYER                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  SQLite Database (trade_signals.db)                              │
│    ├─ signals (all signal evaluations)                           │
│    ├─ orders (order history + status)                            │
│    ├─ scan_events (event log)                                    │
│    ├─ symbol_states (last alert state per symbol)                │
│    ├─ runtime_state (config, daily loss, etc.)                   │
│    └─ config_audit (config change history)                       │
│                                                                   │
│  Filesystem Logs                                                 │
│    ├─ logs/pytrade.log (current)                                 │
│    └─ logs/pytrade_YYYYMMDD.log (daily)                          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Streamlit Dashboard (streamlit_app.py) [READ-ONLY]              │
│    ├─ Dashboard tab                                              │
│    ├─ Performance analytics                                      │
│    ├─ Portfolio status                                           │
│    ├─ System health                                              │
│    ├─ Configuration editor                                       │
│    ├─ User guide                                                 │
│    └─ Deploy wizard                                              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Code Statistics

### Lines of Code Summary

| Module | Lines | Purpose |
|--------|-------|---------|
| main.py | ~200 | CLI entry, main loop |
| config.py | ~300 | Configuration, profiles |
| streamlit_app.py | ~1500 | Web dashboard |
| signal_engine.py | ~400 | Signal evaluation |
| scorer.py | ~600 | Confidence scoring |
| execution.py | ~400 | Order execution |
| indicators.py | ~200 | Technical indicators |
| notifier.py | ~250 | Alert sending |
| logger_db.py | ~400 | SQLite persistence |
| data_fetcher.py | ~50 | Data fetching |
| risk_engine.py | ~50 | Trade planning |
| symbol_manager.py | ~50 | Symbol normalization |
| models.py | ~100 | Data classes |
| utils.py | ~50 | Utilities |
| tests/ | ~500 | Unit tests |
| **TOTAL** | **~5000** | - |

### Dependencies

- **Core**: MetaTrader5, pandas, numpy
- **Analysis**: ta (technical indicators)
- **Config**: python-dotenv
- **Network**: requests (Telegram/LINE)
- **Scheduling**: schedule
- **UI**: streamlit, streamlit-autorefresh
- **Testing**: pytest

---

## 🎯 Key Features

### ✅ Multi-Timeframe Analysis
- 4 timeframes: H4 (trend), H1 (confirmation), M15 (setup), M5 (trigger)
- Independent evaluation on each timeframe
- Trend alignment checking across timeframes

### ✅ Hard Filters (Quality Gate)
- ADX strength check
- Entry zone proximity check
- Trend alignment verification
- Lower timeframe conflict prevention
- Soft mode: more permissive, Strict mode: more restrictive

### ✅ Confidence Scoring
- 11 components with weighted contributions
- 0-100 point scale
- Component breakdown for transparency
- Configurable weights per profile

### ✅ Risk Management
- Per-trade sizing: risk_amount / (entry - SL)
- Daily loss guard: stop if daily loss > limit
- Cooldown period: prevent rapid re-entry
- ATR-based stop loss + take profit

### ✅ Anti-Duplicate Alerts
- Same-candle detection
- Score improvement threshold (delta)
- Invalidation tracking
- Ensures 1 alert per significant move

### ✅ Multi-Channel Alerts
- Console logging (always)
- Telegram bot (if configured)
- LINE messaging (if configured)
- Formatted messages with all key metrics

### ✅ Order Execution
- Demo mode (dry-run)
- Live execution to MT5
- Slippage management
- Magic number tracking
- Order status tracking + sync

### ✅ Persistent Logging
- SQLite database (not just flat files)
- Referential tables (signals, orders, events)
- JSON fields for complex data
- Query-able analytics

### ✅ Web Dashboard
- Real-time overview
- Trade history + PnL
- Performance metrics (win rate, drawdown, Sharpe)
- Configuration UI
- System health checks

---

## 🔧 Configuration Profile Matrix

```
                    Aggressive      Normal (Def)    Strict
─────────────────────────────────────────────────────────
ADX Minimum         12.0            14.0            18.0
Entry Zone ATR      3.5 (×1.5→5.25) 3.0             1.8
Watchlist Score     35              50              75
Alert Score         45              60              85
Strong Score        55              70              90
Premium Score       65              80              93

Filter Mode         soft            soft            strict

Result              More signals    Balanced        Fewer signals
                    More false +    Standard        Quality focus
```

---

## 🚀 Operation Modes

| Mode | Function | Use Case |
|------|----------|----------|
| `--mode scan --once` | Single scan pass | Testing, manual checks |
| `--mode scan` | Continuous daemon | Live trading |
| `--mode sync` | Update order status | Maintenance |
| `streamlit run` | Web dashboard | Monitoring, analysis |

---

## 📦 Output Structure

### Database (trade_signals.db)

```
SQLite3 database with 6 tables:

1. signals
   - All signal evaluations
   - Indexed by timestamp, symbol
   - Includes full indicator snapshots

2. orders
   - Order lifecycle tracking
   - Status: sent, failed, closed, skipped
   - MT5 order/deal IDs for linking

3. scan_events
   - Debug/info logs
   - Hard filter failures
   - Anomalies and warnings

4. symbol_states
   - Last alert metadata per symbol/direction
   - Invalidation flag (for anti-duplicate)
   - Last score, last candle time

5. runtime_state
   - Key-value configuration
   - Daily loss counter
   - Last scan timestamp

6. config_audit
   - Configuration change history
   - Source (user/system)
   - JSON diff of changes
```

### Log Files

```
logs/
├─ pytrade.log          (current session)
├─ pytrade_20260318.log (daily, UTC date)
├─ pytrade_20260317.log
└─ ...
```

---

## 🔄 Data Flow Timeline (per scan)

```
t=0ms     START SCAN
  ↓
t=10ms    _prepare_mtf_data()
          └─ Fetch H4, H1, M15, M5 OHLCV
          └─ Calculate 11+ indicators
  ↓
t=50ms    evaluate_buy_signal()
          └─ Check hard filters
          └─ Calculate confidence score
  ↓
t=55ms    evaluate_sell_signal()
          └─ Check hard filters
          └─ Calculate confidence score
  ↓
t=60ms    save_signal_to_db()
          └─ INSERT buy_signal
          └─ INSERT sell_signal
  ↓
t=70ms    Decide best (buy vs sell)
  ↓
t=75ms    notifier.should_alert()
          └─ Check thresholds, anti-duplicate
  ↓
t=80ms    (Optional) send_alert()
          └─ Console log
          └─ Telegram/LINE send
  ↓
t=90ms    (Optional) try_execute_signal()
          └─ Precheck
          └─ Get MT5 price/info
          └─ Calculate volume
          └─ Send order
  ↓
t=150ms   (Every N scans) sync_orders()
          └─ Update closed status
          └─ Calculate PnL
  ↓
t=160ms   END SCAN (total ~160ms for 1 symbol)

Multiple symbols processed serially
Next scan after scan_interval_seconds
```

---

## 💡 Key Design Decisions

### 1. Rule-based, not ML
- Transparent, explainable signals
- No black-box predictions
- Easy to audit and adjust
- Faster execution than ML inference

### 2. SQLite, not cloud
- Privacy (no data sent outside)
- Fast local queries
- Offline capability
- Easy backup/migration

### 3. Multi-timeframe mandatory
- Context from longer TFs (trend)
- Trigger from shorter TFs (entry)
- Reduces false signals
- Standard trading methodology

### 4. Hard filters as gatekeeper
- Binary decision: execute or not
- Separated from confidence score
- Prevents "good score but bad setup" executions
- Two-level decision system

### 5. Anti-duplicate by state
- Tracks last alert per symbol/direction
- Prevents alert spam
- Allows new setup detection (via invalidation)
- DB-backed persistence

### 6. ATR-based risk
- Volatility-adjusted
- Works across different markets
- Objective measurement
- Easy to understand and adjust

---

## 🎓 Learning Path

1. **Start**: `QUICK_REFERENCE_TH.md` (this file)
2. **Understand**: `CODE_ANALYSIS_TH.md` (detailed breakdown)
3. **Deep Dive**: `DETAILED_FLOW_ANALYSIS_TH.md` (processes + diagrams)
4. **Reference**: `FUNCTION_REFERENCE_TH.md` (API details)
5. **Source Code**: Read actual Python files once familiar

---

## 📈 Example Signal Lifecycle

```
[10:00] Market candle close
  ↓
[10:01] Daemon fetches H4, H1, M15, M5 data
  ↓
[10:02] Evaluates BTCUSD BUY signal
        ├─ Hard filters: PASS ✓
        ├─ Score: 72.5 (strong)
        └─ Category: "strong"
  ↓
[10:02] Saves to signals table
  ↓
[10:02] Checks: should_alert()?
        ├─ score ≥ 60 ✓
        ├─ hard_filters_passed ✓
        ├─ Not same candle as last alert ✓
        └─ YES → ALERT
  ↓
[10:02] Sends alert
        ├─ Console: "[STRONG] 🟢 BUY BTCUSD Score 72.50..."
        ├─ Telegram: same message sent
        └─ Updates symbol_state in DB
  ↓
[10:02] Checks: execution_enabled?
        ├─ YES
        └─ Runs try_execute_signal()
  ↓
[10:02] Execution precheck
        ├─ not dry_run ✓
        ├─ category ≥ min_exec ✓
        ├─ daily_loss_guard NOT active ✓
        ├─ cooldown NOT active ✓
        └─ ALLOWED
  ↓
[10:02] Gets MT5 price: 43215.52
  ↓
[10:02] Calculates trade plan
        ├─ Entry: 43215.52
        ├─ SL: 42156.80 (1.5 ATR below)
        ├─ TP: 44274.24 (2.0:1 R/R)
        ├─ Risk: $50
        └─ Volume: 0.05 lots
  ↓
[10:02] Sends MT5 order request
        └─ Order accepted, retcode = DONE
  ↓
[10:02] Logs order to orders table
        ├─ status: "sent"
        ├─ mt5_order: 123456789
        └─ entry: 43215.52
  ↓
[Later] Order fills/closes
  ↓
[Next sync] sync_orders() updates status to "closed"
        └─ PnL calculated and stored
  ↓
[Dashboard] Shows in performance metrics
```

---

**System ready to analyze! 🎯**
