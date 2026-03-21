# ฟังก์ชันสำคัญและการใช้งาน - PyTrade Code Reference

## Table of Contents
1. [main.py Functions](#mainpy-functions)
2. [Signal Engine Functions](#signal-engine-functions)
3. [Scorer Functions](#scorer-functions)
4. [Execution Functions](#execution-functions)
5. [Database Functions](#database-functions)
6. [Indicator Functions](#indicator-functions)

---

## main.py Functions

### `_prepare_mtf_data(fetcher, symbol, cfg) → dict[str, pd.DataFrame]`

**วัตถุประสงค์**: ดึงข้อมูล OHLCV และคำนวณตัวชี้วัดสำหรับทุก timeframe

**Input**:
- `fetcher: DataFetcher` - Object สำหรับดึงข้อมูล
- `symbol: str` - ชื่อสัญลักษณ์ (ต้อง normalize แล้ว)
- `cfg: Config` - Configuration object

**Process**:
```python
for tf in [cfg.timeframe_primary, cfg.timeframe_confirm, cfg.timeframe_setup, cfg.timeframe_trigger]:
    # tf = "H4", "H1", "M15", "M5"
    
    # Step 1: Fetch OHLCV
    raw = fetcher.fetch_ohlcv(symbol, tf, cfg.bars_to_fetch)
    if raw.empty:
        return {}  # ไม่มีข้อมูล
    
    # Step 2: Calculate indicators
    calc = calculate_indicators(raw, use_vwap=cfg.use_vwap, use_supertrend=cfg.use_supertrend)
    
    # Step 3: Check minimum history
    if len(calc) < 220:
        return {}  # ข้อมูลไม่พอ
    
    # Step 4: Check data freshness
    latest_closed = calc.iloc[-2]["time"]  # candle ที่ปิดล่าสุด
    age_minutes = (now - latest_closed).total_seconds() / 60
    max_age = timeframe_minutes(tf) * 3  # อนุญาต stale 3× TF
    
    if age_minutes > max_age:
        return {}  # ข้อมูลเก่า (feed ไม่สดใหม่)
    
    data[tf] = calc
```

**Output**: `dict[str, pd.DataFrame]`
- Keys: "H4", "H1", "M15", "M5"
- Values: DataFrame พร้อมตัวชี้วัดทั้งหมด
- `{}` ถ้าข้อมูลไม่เพียงพอ

**Error Handling**:
- Log WARNING ถ้าข้อมูลเก่า
- Log WARNING ถ้าข้อมูลไม่เพียงพอ

---

### `_evaluate_symbol(symbol, normalized_symbol, fetcher, db, notifier, executor) → None`

**วัตถุประสงค์**: ประเมินสัญญาณสำหรับสัญลักษณ์หนึ่งตัวครบวงจร

**Process**:
```python
1. Prepare data
   mtf_data = _prepare_mtf_data(...)
   if not mtf_data:
       log WARNING: insufficient_or_stale_data
       return

2. Evaluate signals
   buy = evaluate_buy_signal(symbol, normalized_symbol, mtf_data, cfg)
   sell = evaluate_sell_signal(symbol, normalized_symbol, mtf_data, cfg)

3. Save to DB
   save_signal_to_db(db, buy)
   save_signal_to_db(db, sell)

4. Log hard filter failures
   if not buy.hard_filters_passed:
       log: buy_hard_filter_fail → reasons
   if not sell.hard_filters_passed:
       log: sell_hard_filter_fail → reasons

5. Mark invalidation (if score dropped)
   if buy.score < cfg.watchlist_threshold:
       mark_invalidation(normalized_symbol, "BUY")
   if sell.score < cfg.watchlist_threshold:
       mark_invalidation(normalized_symbol, "SELL")

6. Decide best signal
   best = buy if buy.score >= sell.score else sell

7. Try alert
   if notifier.should_alert(best):
       notifier.send_alert(best)

8. Try execute (if enabled)
   if cfg.execution_enabled:
       executor.try_execute_signal(best)

9. Sync old orders (periodic)
   if scan_count % cfg.sync_interval == 0:
       executor.sync_orders()
```

---

## Signal Engine Functions

### `evaluate_buy_signal(symbol, normalized_symbol, mtf_data, cfg) → SignalResult`

**วัตถุประสงค์**: ประเมิน BUY signal ครบวงจร

**Process**:
```python
1. Hard filters
   hard_filters_passed, reasons, summary, asset_profile = _hard_filters("BUY", ...)

2. Get price
   price = mtf_data[cfg.timeframe_setup].iloc[-2]["close"]
   timestamp = mtf_data[cfg.timeframe_setup].iloc[-2]["time"]

3. Calculate confidence score
   if hard_filters_passed:
       score, component_scores = calculate_confidence("BUY", mtf_data, asset_profile)
   else:
       score = 0

4. Classify category
   category = classify_score(score)  # ignore/candidate/alert/strong/premium

5. Build trade plan
   if score > 0:
       atr = mtf_data[cfg.timeframe_setup].iloc[-2]["atr14"]
       entry = price
       plan = build_trade_plan("BUY", entry, atr, account_balance, ...)
   else:
       plan = {}

6. Build indicator snapshot
   snapshot = _build_indicator_snapshot(mtf_data[cfg.timeframe_setup])

7. Build reason summary
   reason_summary = _format_reason(hard_filter_reasons, component_scores)

8. Return SignalResult
   return SignalResult(
       symbol=symbol,
       normalized_symbol=normalized_symbol,
       direction="BUY",
       score=score,
       category=category,
       price=price,
       timestamp=timestamp,
       timeframe_summary=summary,
       reason_summary=reason_summary,
       indicator_snapshot=snapshot,
       hard_filters_passed=hard_filters_passed,
       hard_filter_reasons=reasons,
       component_scores=component_scores,
       trade_plan=plan,
   )
```

**Output**: `SignalResult` BUY

**Key Variables**:
- `hard_filters_passed: bool` - ผ่านคัดกรองที่เข้มงวดหรือไม่
- `score: float` - 0-100 confidence score
- `category: str` - "ignore" / "candidate" / "alert" / "strong" / "premium"

---

### `evaluate_sell_signal(...) → SignalResult`

เหมือน `evaluate_buy_signal()` แต่สำหรับ SELL signal
- Hard filters ตรวจสอบ bearish trends แทน bullish
- Direction = "SELL"

---

### `_hard_filters(symbol, direction, mtf_data, cfg) → tuple[bool, list[str], dict[str, str], dict[str, Any]]`

**วัตถุประสงค์**: ตัดสินใจว่าสัญญาณควร execute หรือเป็น candidate เท่านั้น

**Return Tuple**:
```python
(
    hard_filters_passed: bool,      # True ถ้าผ่านทั้งหมด
    reasons: list[str],             # เหตุผลที่ไม่ผ่าน (empty ถ้าผ่าน)
    summary: dict[str, str],        # {"H4": "bullish", "H1": "bearish", ...}
    asset_profile: dict[str, Any]   # settings สำหรับ asset นี้
)
```

**Checks for BUY**:
```
1. ADX Check
   ✓ adx_value = max(H1_ADX, M15_ADX)
   ✓ adx_minimum = asset_profile["adx_minimum"]
   ✗ if adx_value < adx_minimum:
       reasons.append(f"ADX too low ({adx_value} < {adx_minimum})")

2. Entry Zone Check
   ✓ entry_distance_atr = abs(close - ema20) / atr14
   ✓ max_zone = asset_profile["entry_zone_max_atr"]
   ✗ if entry_distance_atr > max_zone (× 1.5 in soft mode):
       reasons.append(f"Price too far from entry zone")

3. H4 Trend Check
   ✓ if h4_trend == "bullish":
       continue
   ✓ elif h4_trend == "sideway" AND soft_mode:
       continue if H1 = bullish
   ✗ else:
       reasons.append("H4 bearish conflict" or "H4 not bullish")

4. H1 Trend Check
   ✓ if h1_trend != "bearish" OR (soft_mode AND m15_trend == "bullish"):
       continue
   ✗ else:
       reasons.append("H1 bearish conflict")

5. Lower TF Conflict
   ✗ if m15_trend == "bearish" AND m5_trend == "bearish":
       reasons.append("Severe lower TF conflict")
```

**Checks for SELL**: ตรงกันข้ามกับ BUY

---

## Scorer Functions

### `calculate_confidence(direction, mtf_data, asset_profile, cfg) → tuple[float, dict[str, float]]`

**วัตถุประสงค์**: คำนวณ confidence score จาก 0-100

**Process**:
```python
# M15 (Setup TF) scoring
m15 = mtf_data["M15"]
h4 = mtf_data["H4"]
h1 = mtf_data["H1"]

h4_trend = detect_trend(h4)
h1_trend = detect_trend(h1)
m15_trend = detect_trend(m15)
structure = detect_price_structure(m15)

# Partial scores
higher_tf_score = _score_higher_tf(direction, h4_trend, h1_trend, asset_profile)
ema_score = _score_ema(direction, m15.iloc[-2])
adx_score = _score_adx(m15.iloc[-2]["adx14"], asset_profile)
structure_score = _score_structure_profile(direction, structure, asset_profile)
setup_score = _score_setup_quality(direction, m15.iloc[-2], m15.iloc[-3], asset_profile)
rsi_score = _score_rsi_context(direction, m15.iloc[-2]["rsi14"], asset_profile)
macd_score = _score_macd_confirmation(direction, m15, asset_profile.get("macd_mode"))
bollinger_score = _score_bollinger_context(direction, m15.iloc[-2], asset_profile.get("bollinger_mode"))

# M5 (Trigger TF) scoring
m5 = mtf_data["M5"]
stoch_score = _score_stoch_trigger(direction, m5.iloc[-2], asset_profile.get("stoch_mode"))
volume_score = _score_volume_confirmation(m5, asset_profile["volume_spike_ratio"])
atr_score = _score_atr_suitability(m5.iloc[-2]["atr14"], m15.iloc[-2]["atr14"])

# Weight and aggregate
weights = cfg.scoring_weights  # or from asset_profile
total_score = (
    higher_tf_score * weights["higher_tf"] +
    ema_score * weights["ema_alignment"] +
    adx_score * weights["adx_strength"] +
    structure_score * weights["market_structure"] +
    setup_score * weights["setup_quality"] +
    rsi_score * weights["rsi_context"] +
    macd_score * weights["macd_confirmation"] +
    stoch_score * weights["stoch_trigger"] +
    volume_score * weights["volume_confirmation"] +
    bollinger_score * weights["bollinger_context"] +
    atr_score * weights["atr_suitability"]
) / sum(weights.values())

# Normalize to 0-100
confidence = total_score * 100

component_scores = {
    "higher_tf": higher_tf_score,
    "ema": ema_score,
    "adx": adx_score,
    "structure": structure_score,
    "setup": setup_score,
    "rsi": rsi_score,
    "macd": macd_score,
    "stoch": stoch_score,
    "volume": volume_score,
    "bollinger": bollinger_score,
    "atr": atr_score,
}

return confidence, component_scores
```

**Output**: 
- `float`: 0-100 confidence score
- `dict[str, float]`: component scores

---

## Execution Functions

### `executor.try_execute_signal(signal: SignalResult) → None`

**วัตถุประสงค์**: ส่งออเดอร์ไป MT5 (หรือ skip ถ้าเงื่อนไขไม่เหมาะสม)

**Process**:
```python
1. Precheck
   allowed, reason = executor._precheck(signal)
   if not allowed:
       log: "Execution skipped: {reason}"
       _log(signal, status="skipped", reason=reason)
       return

2. Get MT5 Symbol Info
   symbol_info = mt5.symbol_info(signal.normalized_symbol)
   if symbol_info is None:
       log warning: "symbol_info unavailable"
       _log(signal, status="failed", reason="symbol_info_unavailable")
       return

3. Get Current Tick
   tick = mt5.symbol_info_tick(signal.normalized_symbol)
   if tick is None:
       _log(signal, status="failed", reason="tick_unavailable")
       return

4. Check Trade Enabled
   if not _is_symbol_trade_enabled(symbol_info):
       _log(signal, status="skipped", reason="symbol_trade_disabled")
       return

5. Get Entry Price
   entry = tick.ask if signal.direction == "BUY" else tick.bid

6. Get SL/TP from Trade Plan
   plan = signal.trade_plan or {}
   sl = plan.get("stop_loss", 0.0)
   tp = plan.get("take_profit", 0.0)

7. Resolve Risk Amount
   risk_amount = _resolve_risk_amount(plan)
   # Static: from plan
   # Dynamic: from MT5 balance × risk_per_trade_pct

8. Calculate Volume
   volume = _calc_volume(symbol_info, entry, sl, risk_amount)
   if volume <= 0:
       _log(signal, status="failed", reason="invalid_volume")
       return

9. Build Order Request
   request = {
       "action": mt5.TRADE_ACTION_DEAL,
       "symbol": signal.normalized_symbol,
       "volume": volume,
       "type": mt5.ORDER_TYPE_BUY or ORDER_TYPE_SELL,
       "price": entry,
       "sl": sl,
       "tp": tp,
       "deviation": self.config.max_slippage_points,
       "magic": self.config.magic_number,
       "comment": f"pytrade:{signal.category}:{signal.score:.1f}",
       "type_time": mt5.ORDER_TIME_GTC,
       "type_filling": mt5.ORDER_FILLING_IOC,
   }

10. Send Order
    result = mt5.order_send(request)
    if result is None:
        _log(signal, status="failed", reason="order_send_none")
        return
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        _log(signal, status="failed", reason=f"retcode:{result.retcode}")
        return

11. Log Success
    _log(
        signal,
        status="sent",
        entry=entry, sl=sl, tp=tp, volume=volume,
        mt5_order=result.order,
        mt5_position=result.deal,
        comment=result.comment
    )
    log: "Order sent: {direction} {symbol} vol={volume} entry={entry} sl={sl} tp={tp}"
```

---

### `executor._precheck(signal) → tuple[bool, str]`

**Checks**:
```python
if self.config.dry_run:
    return False, "dry_run_enabled"

if signal.category_rank() < self.config.min_execute_category:
    return False, "below_min_execute_category"

if self.db.get_today_realized_loss() > self.config.daily_loss_limit:
    return False, "daily_loss_guard_active"

if self.db.has_recent_entry(signal.symbol, signal.direction, cooldown_minutes):
    return False, "cooldown_active"

if not self.config.mt5_ready():
    return False, "mt5_not_connected"

return True, ""
```

---

### `executor._calc_volume(symbol_info, entry, sl, risk_amount) → float`

**Formula**:
```python
# Distance in base currency
sl_distance = abs(entry - sl)

# PnL per 1 lot for this symbol
tick_value = symbol_info.trade_tick_value
point = symbol_info.point

# Volume (in lots) to achieve target risk
volume = risk_amount / (sl_distance * tick_value / point)

# Apply symbol constraints
volume = max(volume, symbol_info.volume_min)
volume = min(volume, symbol_info.volume_max)

# Round to symbol precision
volume = round(volume, symbol_info.volume_step)

return volume
```

---

### `executor.sync_orders() → None`

**วัตถุประสงค์**: อัปเดตสถานะของออเดอร์ที่ส่งไปแล้ว

**Process**:
```python
1. Get sent orders from DB
   sent_orders = self.db.get_sent_orders()
   # status = "sent"

2. For each sent order
   for order in sent_orders:
       # Check deal status in MT5
       deal = mt5.deal_get(mt5_deal=order.mt5_position)
       
       if deal is None:
           # Order not filled yet
           continue
       
       if deal.profit != 0 or deal.commission != 0:
           # Order closed
           pnl = deal.profit - deal.commission
           
           self.db.update_order_closed(
               order.id,
               status="closed",
               pnl=pnl,
               closed_at=deal.time
           )
           
           # Log to scan_events
           self.db.log_scan_event(
               order.symbol,
               "INFO",
               "order_closed",
               {"pnl": pnl, "volume": order.volume}
           )

3. Update daily loss
   total_loss = self.db.get_today_realized_loss()
   self.db.set_daily_loss_amount(total_loss)
```

---

## Database Functions

### `save_signal_to_db(db, signal) → None`

```python
def save_signal_to_db(db: SignalDB, signal: SignalResult) -> None:
    db.save_signal_to_db(signal)
    # INSERT into signals table:
    # - timestamp, symbol, normalized_symbol
    # - direction, score, category, price
    # - reason_summary
    # - timeframe_summary_json (serialize dict → JSON)
    # - indicator_snapshot_json
    # - component_scores_json
    # - trade_plan_json
    # - hard_filters_passed, hard_filter_reasons_json
```

---

### `db.log_scan_event(symbol, level, message, details=None) → None`

```python
def log_scan_event(self, symbol, level, message, details=None):
    # INSERT into scan_events:
    # - timestamp (now)
    # - symbol
    # - level ("INFO", "WARNING", "ERROR")
    # - message (short description)
    # - details_json (optional extra data)
```

**Examples**:
```python
db.log_scan_event("BTCUSD", "WARNING", "insufficient_or_stale_data", 
    {"normalized_symbol": "BTCUSDm", "age_minutes": 15})

db.log_scan_event("ETHUSD", "INFO", "buy_hard_filter_fail",
    {"reasons": ["ADX too low", "H4 bearish conflict"]})

db.log_scan_event("LTCUSD", "INFO", "order_sent",
    {"direction": "BUY", "volume": 0.05, "entry": 100.5})
```

---

### `db.get_today_realized_loss() → float`

```python
def get_today_realized_loss(self) -> float:
    # SELECT SUM(pnl) FROM orders
    # WHERE status="closed" AND closed_at >= today_start_utc
    # RETURN: total realized loss (negative) or 0
    
    # Example:
    # Closed orders today:
    # - Order 1: pnl = -50 (loss)
    # - Order 2: pnl = +100 (gain)
    # - Order 3: pnl = -20 (loss)
    # Return: -50 + 100 - 20 = 30 (net profit)
```

---

## Indicator Functions

### `calculate_indicators(df, use_vwap=False, use_supertrend=False) → pd.DataFrame`

```python
def calculate_indicators(df: pd.DataFrame, 
                        use_vwap: bool = False, 
                        use_supertrend: bool = False) -> pd.DataFrame:
    """Add ALL technical indicators to OHLCV DataFrame"""
    
    out = df.copy()
    
    # 1. Moving Averages (EMA)
    out["ema20"] = EMAIndicator(close, window=20).ema_indicator()
    out["ema50"] = EMAIndicator(close, window=50).ema_indicator()
    out["ema200"] = EMAIndicator(close, window=200).ema_indicator()
    
    # 2. RSI (Momentum Oscillator, 0-100)
    out["rsi14"] = RSIIndicator(close, window=14).rsi()
    
    # 3. MACD (Momentum indicator)
    macd = MACD(close, window_fast=12, window_slow=26, window_sign=9)
    out["macd"] = macd.macd()              # MACD line
    out["macd_signal"] = macd.macd_signal()  # Signal line (EMA9)
    out["macd_hist"] = macd.macd_diff()      # Histogram (MACD - Signal)
    
    # 4. Bollinger Bands (Volatility)
    bb = BollingerBands(close, window=20, window_dev=2)
    out["bb_upper"] = bb.bollinger_hband()
    out["bb_middle"] = bb.bollinger_mavg()   # SMA20
    out["bb_lower"] = bb.bollinger_lband()
    
    # 5. ADX (Trend Strength, 0-100)
    out["adx14"] = ADXIndicator(high, low, close, window=14).adx()
    
    # 6. ATR (Volatility, in price units)
    out["atr14"] = AverageTrueRange(high, low, close, window=14).average_true_range()
    
    # 7. Stochastic Oscillator (0-100)
    stoch = StochasticOscillator(high, low, close, 
                                window=14, smooth_window=3)
    out["stoch_k"] = stoch.stoch()          # %K line
    out["stoch_d"] = stoch.stoch_signal()   # %D line (signal)
    
    # 8. Volume SMA
    out["volume_sma20"] = out["volume"].rolling(20).mean()
    
    # 9. Optional: VWAP
    if use_vwap:
        out["vwap"] = VolumeWeightedAveragePrice(
            high, low, close, volume, window=14
        ).volume_weighted_average_price()
    
    # 10. Optional: Supertrend
    if use_supertrend:
        out["supertrend"] = _calc_supertrend(df, period=10, multiplier=3.0)
    
    # Clean NaN/Inf and reset index
    out = out.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
    
    return out
```

---

### `detect_trend(df) → str`

```python
def detect_trend(df: pd.DataFrame) -> str:
    """Detect trend based on EMA alignment"""
    if len(df) < 3:
        return "unknown"
    
    row = df.iloc[-2]  # Latest closed candle
    
    if row["ema20"] > row["ema50"] > row["ema200"]:
        return "bullish"
    elif row["ema20"] < row["ema50"] < row["ema200"]:
        return "bearish"
    else:
        return "sideway"
```

---

### `detect_price_structure(df, lookback=30) → str`

```python
def detect_price_structure(df: pd.DataFrame, lookback: int = 30) -> str:
    """
    Detect market structure:
    HH HL = bullish (higher highs, higher lows)
    LH LL = bearish (lower highs, lower lows)
    mixed = no clear structure
    """
    if len(df) < lookback:
        return "unknown"
    
    sample = df.tail(lookback)
    
    # Find swing highs (local maximum)
    swing_highs = sample.loc[
        sample["high"].rolling(3, center=True).max() == sample["high"], 
        "high"
    ].tail(3).tolist()
    
    # Find swing lows (local minimum)
    swing_lows = sample.loc[
        sample["low"].rolling(3, center=True).min() == sample["low"], 
        "low"
    ].tail(3).tolist()
    
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "mixed"
    
    hh = swing_highs[-1] > swing_highs[-2]    # Higher high?
    hl = swing_lows[-1] > swing_lows[-2]      # Higher low?
    lh = swing_highs[-1] < swing_highs[-2]    # Lower high?
    ll = swing_lows[-1] < swing_lows[-2]      # Lower low?
    
    if hh and hl:
        return "bullish"
    elif lh and ll:
        return "bearish"
    else:
        return "mixed"
```

---

### `_score_higher_tf(direction, h4_trend, h1_trend, profile) → float`

```python
def _score_higher_tf(direction: str, h4_trend: str, h1_trend: str, 
                    profile: dict[str, Any]) -> float:
    """Score higher timeframe (H4/H1) alignment"""
    sideway_score = float(profile.get("higher_tf_sideway_score", 10.0))
    
    if direction == "BUY":
        if h4_trend != "bullish":
            return 0.0  # H4 must support buyer
        
        if h1_trend == "bullish":
            return 20.0  # Perfect: both bullish
        elif h1_trend == "sideway":
            return sideway_score  # OK: H1 not against
        else:  # h1_trend == "bearish"
            return 0.0  # Conflict
    
    else:  # direction == "SELL"
        if h4_trend != "bearish":
            return 0.0
        
        if h1_trend == "bearish":
            return 20.0
        elif h1_trend == "sideway":
            return sideway_score
        else:  # h1_trend == "bullish"
            return 0.0
```

---

เสร็จสิ้นการอธิบายฟังก์ชัน!
