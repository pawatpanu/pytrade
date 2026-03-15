# เธเธนเนเธกเธทเธญเธเธฒเธฃเนเธเนเธเธฒเธ PyTrade (เธเธเธฑเธเนเธเนเธเธฒเธเธเธฃเธดเธ)

เน€เธญเธเธชเธฒเธฃเธเธตเนเน€เธเนเธเนเธเนเธเธฒเธเธเธฃเธดเธเนเธเธเน€เธเนเธฒเนเธเธเนเธฒเธข

## 1) เนเธเธงเธเธดเธ”เธชเธณเธเธฑเธ
- เธเธฐเนเธเธ `score` เธเธทเธญ **rule-based confidence**
- เธเธฐเนเธเธ **เนเธกเนเนเธเน** win rate
- เนเธเน closed candle เน€เธเนเธเธซเธฅเธฑเธ
- เธฃเธฐเธเธเธกเธต anti-duplicate alert

## 2) เธเธณเธชเธฑเนเธเธซเธฅเธฑเธเธ—เธตเนเนเธเนเธ—เธธเธเธงเธฑเธ
### 2.1 เน€เธฃเธดเนเธกเธงเธฑเธเนเธซเธกเน
```powershell
C:\pytrade\.venv\Scripts\python.exe C:\pytrade\main.py --mode reset_loss_guard
C:\pytrade\.venv\Scripts\python.exe C:\pytrade\main.py --mode sync
```

### 2.2 เธ—เธ”เธชเธญเธเธฃเธญเธเน€เธ”เธตเธขเธง
```powershell
C:\pytrade\.venv\Scripts\python.exe C:\pytrade\main.py --mode scan --once
```

### 2.3 เธฃเธฑเธเธ•เนเธญเน€เธเธทเนเธญเธ
```powershell
C:\pytrade\.venv\Scripts\python.exe C:\pytrade\main.py --mode daemon
```

### 2.4 เธเธดเธเธเนเธชเธ–เธฒเธเธฐเธญเธญเน€เธ”เธญเธฃเน
```powershell
C:\pytrade\.venv\Scripts\python.exe C:\pytrade\main.py --mode sync
```

## 3) เนเธเนเธเนเธฒเธ Dashboard
เน€เธเธดเธ”:
```powershell
py -m streamlit run streamlit_app.py
```

เน€เธเนเธฒ `http://localhost:8501`

### 3.1 เนเธ–เธเธเนเธฒเธข
- `เธชเนเธเธ 1 เธฃเธญเธ`: เธขเธดเธ scan เธซเธเธถเนเธเธเธฃเธฑเนเธ
- `เธเธดเธเธเนเธญเธญเน€เธ”เธญเธฃเน`: เธญเธฑเธเน€เธ”เธ• sent/closed/pnl
- `เน€เธฃเธดเนเธกเน€เธ”เธกเธญเธ` / `เธซเธขเธธเธ”เน€เธ”เธกเธญเธ`
- เนเธชเธ”เธเธซเธกเธงเธ”เนเธเนเธเธฒเธเธ•เธญเธเธเธตเน: profile/filter/min_alert/min_execute

### 3.2 เนเธ—เนเธเนเธ”เธเธเธญเธฃเนเธ”
- เธ เธฒเธเธฃเธงเธกเธญเธญเน€เธ”เธญเธฃเน
- เธเธธเนเธกเธฅเนเธฒเธเธเนเธญเธกเธนเธฅ skipped เธ—เธตเนเนเธกเนเธชเธณเธเธฑเธ
- เธฃเธตเน€เธเนเธ• Daily Loss Guard
- เธเธฃเธฒเธ Equity
- เธ•เธฒเธฃเธฒเธ orders/signals/events

### 3.3 เนเธ—เนเธเธ•เธฑเนเธเธเนเธฒ
- เน€เธฅเธทเธญเธ `เนเธเธฃเนเธเธฅเนเธชเธณเน€เธฃเนเธเธฃเธนเธ` เนเธ”เนเธ—เธฑเธเธ—เธต
- เธเธฃเธฑเธเธเนเธฒเธ—เธธเธเธกเธดเธ•เธดเธเนเธฒเธเธเธญเธฃเนเธก
- เธ”เธน glossary เธเธงเธฒเธกเธซเธกเธฒเธขเธ•เธฑเธงเนเธเธฃ
- เธเธฑเธเธ—เธถเธเนเธฅเนเธงเนเธซเนเธฃเธตเธชเธ•เธฒเธฃเนเธ— daemon

### 3.4 เนเธ—เนเธเธชเธ–เธฒเธเธฐเธเธญเธฃเนเธ•
- เธ”เธถเธเธเนเธญเธกเธนเธฅเธเธฑเธเธเธตเนเธฅเธฐ position เธเธฒเธ MT5

## 4) เธเธฃเธฑเธ โ€เธเธงเธฒเธกเน€เธเนเธกเธเนเธโ€ เน€เธเนเธฒเธญเธญเน€เธ”เธญเธฃเน
### เน€เธเนเธฒเธญเธญเน€เธ”เธญเธฃเนเธกเธฒเธเธเธถเนเธ
- `HARD_FILTER_MODE=soft`
- `M5_MIN_TRIGGERS=1`
- เธฅเธ” thresholds เธฅเธ
- `MIN_EXECUTE_CATEGORY=alert`

### เธเธฑเธ”เธเธธเธ“เธ เธฒเธเน€เธเนเธกเธเธถเนเธ
- `HARD_FILTER_MODE=strict`
- `ADX_MINIMUM` เธชเธนเธเธเธถเนเธ
- `M5_MIN_TRIGGERS=2-3`
- เน€เธเธดเนเธก thresholds
- `MIN_EXECUTE_CATEGORY=strong` เธซเธฃเธทเธญ `premium`

## 5) Premium / Ultra Stack
เธ–เนเธฒเธ•เนเธญเธเธเธฒเธฃเน€เธเธดเธ”เนเธกเนเน€เธเธดเนเธกเนเธกเนเธกเธตเธญเธญเน€เธ”เธญเธฃเนเธเนเธฒเธ:
```env
ENABLE_PREMIUM_STACK=true
PREMIUM_STACK_EXTRA_SLOTS=1
ENABLE_ULTRA_STACK=true
ULTRA_STACK_SCORE=95
ULTRA_STACK_EXTRA_SLOTS=2
```

## 6) เน€เธซเธ•เธธเธเธฅเธ—เธตเนเธกเธฑเธเน€เธเธญเนเธ `orders.reason`
- `below_min_execute_category`: เธเธฐเนเธเธเธ•เนเธณเธเธงเนเธฒเน€เธเธ“เธ‘เนเธชเนเธเธเธณเธชเธฑเนเธ
- `cooldown_active`: เธขเธฑเธเนเธกเนเธเนเธ cooldown
- `max_open_positions_reached`: เธเธณเธเธงเธเนเธกเนเน€เธเธดเธ”เน€เธ•เนเธก
- `daily_loss_limit_reached`: เธเธเน€เธเธ”เธฒเธเธเธฒเธ”เธ—เธธเธเธฃเธฒเธขเธงเธฑเธ
- `symbol_trade_disabled`: เนเธเธฃเธเธเธดเธ”เธเธฒเธฃเน€เธ—เธฃเธ” symbol เธเธตเน

## 7) Query เธ•เธฃเธงเธเธชเธญเธเน€เธฃเนเธง (SQLite)
```powershell
py -m sqlite3 signals.db "SELECT id,timestamp,symbol,status,reason,score,category FROM orders ORDER BY id DESC LIMIT 30;"
py -m sqlite3 signals.db "SELECT id,timestamp,symbol,direction,score,category FROM signals ORDER BY id DESC LIMIT 30;"
py -m sqlite3 signals.db "SELECT id,timestamp,symbol,level,message FROM scan_events ORDER BY id DESC LIMIT 30;"
```

## 8) เนเธซเธกเธ”เธเธฅเธญเธ”เธ เธฑเธขเธเนเธญเธเธเธถเนเธ live
เนเธเธฐเธเธณ:
- `EXECUTION_MODE=demo`
- `RISK_PER_TRADE_PCT` เธ•เนเธณ (0.10-0.30)
- `MAX_OPEN_POSITIONS` เธ•เนเธณ (1-2)
- เน€เธเธดเธ” Smart Exit

## 9) Checklist เธเนเธญเธเธเธฅเนเธญเธขเธฃเธฑเธเธเธฃเธดเธ
1. MT5 login เธชเธณเน€เธฃเนเธ
2. symbols เธ•เธฃเธเธเธฑเธเนเธเธฃเธ
3. sync เธเนเธฒเธ
4. scan --once เธเนเธฒเธ
5. dashboard เนเธชเธ”เธเธเนเธญเธกเธนเธฅเธเธเธ•เธด
6. test เธเนเธฒเธ:
```powershell
py -m pytest -q tests --basetemp C:\pytrade\pytest_work\run1 -p no:cacheprovider
```


