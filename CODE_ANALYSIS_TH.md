# การวิเคราะห์โค้ด PyTrade - ระบบวิเคราะห์สัญญาณ MT5

## 📋 สารบัญ
1. [ภาพรวมของระบบ](#ภาพรวมของระบบ)
2. [สถาปัตยกรรมโครงการ](#สถาปัตยกรรมโครงการ)
3. [รายละเอียดโมดูล](#รายละเอียดโมดูล)
4. [ลำดับการทำงาน](#ลำดับการทำงาน)
5. [ระบบการให้คะแนน](#ระบบการให้คะแนน)
6. [ระบบการขาย/ซื้อ](#ระบบการขายซื้อ)

---

## ภาพรวมของระบบ

### วัตถุประสงค์
PyTrade เป็น **ระบบวิเคราะห์สัญญาณเทรดอัตโนมัติ** สำหรับสกุลเงินดิจิทัล (Crypto) บน MetaTrader 5 โดยวิเคราะห์ราคาข้อมูลจากหลายระยะเวลา (Multi-timeframe) และให้คะแนนสัญญาณตามกฎการวิเคราะห์ทางเทคนิค

### คุณสมบัติหลัก
- **Multi-timeframe Analysis**: วิเคราะห์ H4/H1/M15/M5 พร้อมกัน
- **Rule-based Scoring**: ให้คะแนนตามกฎวิเคราะห์ (ไม่ใช่ AI/ML)
- **Risk Management**: ป้องกัน drawdown รายวันด้วย Daily Loss Guard
- **Multi-Channel Alerts**: ส่งแจ้งเตือนผ่าน Console/Telegram/LINE
- **Execution Engine**: ส่งคำสั่งอัตโนมัติไปยัง MT5
- **SQLite Logging**: เก็บประวัติแบบเดตเบสเพื่อวิเคราะห์ย้อนหลัง
- **Streamlit Dashboard**: แดชบอร์ดเว็บแสดงสถานะและผลงาน

### โหมดการทำงาน
```
1. --mode scan --once    : สแกนสัญญาณ 1 รอบแล้วจบ
2. --mode scan           : สแกนสัญญาณแบบต่อเนื่อง (demon)
3. --mode sync           : ซิงก์สถานะออเดอร์จาก MT5
4. streamlit_app.py      : เรียกหน้าแดชบอร์ดเว็บ
```

---

## สถาปัตยกรรมโครงการ

### โครงสร้างโฟลเดอร์

```
pytrade/
├── core/                 # โมดูลหลักของระบบ
│   ├── models.py         # Data classes (SignalResult, TradePlan, SymbolState)
│   ├── mt5_connector.py  # การเชื่อมต่อ MetaTrader5
│   ├── data_fetcher.py   # ดึงข้อมูล OHLCV จาก MT5
│   ├── indicators.py     # คำนวณตัวชี้วัดเทคนิค
│   ├── signal_engine.py  # ประเมินสัญญาณ BUY/SELL
│   ├── scorer.py         # ให้คะแนนสัญญาณ
│   ├── execution.py      # ส่งคำสั่งไป MT5
│   ├── risk_engine.py    # สร้างแผนเทรด (SL/TP/Size)
│   ├── symbol_manager.py # แมปชื่อสัญลักษณ์
│   ├── notifier.py       # ส่งแจ้งเตือน
│   └── logger_db.py      # บันทึกลงฐานข้อมูล SQLite
│
├── main.py               # entry point (CLI)
├── config.py             # การตั้งค่าและโปรไฟล์
├── streamlit_app.py      # แดชบอร์ดเว็บ
├── .env.example          # ตัวอย่างไฟล์สภาวะแวดล้อม
├── requirements.txt      # dependencies
└── tests/                # unit tests

```

### ความสัมพันธ์ระหว่างโมดูล

```
┌─────────────────┐
│    main.py      │     CLI entry point
└────────┬────────┘
         │
         ├─→ config.py          (โหลดการตั้งค่า)
         │
         ├─→ mt5_connector.py   (เชื่อมต่อ MT5)
         │
         ├─→ data_fetcher.py    (ดึง OHLCV)
         │
         ├─→ indicators.py      (คำนวณตัวชี้วัด)
         │
         ├─→ signal_engine.py   (ประเมินสัญญาณ)
         │   ├─→ scorer.py      (ให้คะแนน)
         │   ├─→ risk_engine.py (แผนเทรด)
         │   └─→ logger_db.py   (บันทึก DB)
         │
         ├─→ execution.py       (ส่งคำสั่ง)
         │   └─→ logger_db.py   (บันทึกออเดอร์)
         │
         └─→ notifier.py        (แจ้งเตือน)

┌──────────────────┐
│ streamlit_app.py │     Dashboard
└──────────────────┘
     ↓
 logger_db.py      (อ่านข้อมูลจากฐาน)
```

---

## รายละเอียดโมดูล

### 1. **config.py** - ระบบการตั้งค่า

**หน้าที่**: โหลดการตั้งค่ากรรมสิทธิ์ من `.env` และมี preset profiles

#### โปรไฟล์หลัก (PROFILE_PRESETS)
```
- aggressive  : ADX≥12, watchlist≥35, alert≥45
- normal      : ADX≥14, watchlist≥50, alert≥60
- strict      : ADX≥18, watchlist≥75, alert≥85
```

#### โปรไฟล์สินทรัพย์ (ASSET_PROFILE_PRESETS)
```
- default       : การตั้งค่ามาตรฐาน
- crypto_major  : สำหรับ BTC/ETH (ADX≥14, miner settings)
```

#### ตัวแปรสำคัญ จากเทมเพลต

```python
# MT5 Connection
MT5_PATH          # Path to MT5 terminal
MT5_LOGIN         # Account login
MT5_PASSWORD      # Account password
MT5_SERVER        # Server name

# Symbol Settings
WATCH_SYMBOLS     # Symbols to scan (comma-separated)
ASSET_PROFILE     # Which preset to use

# Signal Thresholds
WATCHLIST_THRESHOLD      # Min score to track (default: 50)
ALERT_THRESHOLD          # Min score to alert (default: 60)
STRONG_ALERT_THRESHOLD   # Min score for "strong" (default: 70)
PREMIUM_ALERT_THRESHOLD  # Min score for "premium" (default: 80)

# Execution
EXECUTION_ENABLED         # Enable order sending
MIN_EXECUTE_CATEGORY      # Min signal category to execute
USE_MT5_BALANCE_FOR_SIZING # Dynamic sizing from account
RISK_PER_TRADE_PCT        # Risk percentage per trade

# Alerts
TELEGRAM_ENABLED   # Enable Telegram
TELEGRAM_TOKEN     # Bot token
TELEGRAM_CHAT_ID   # Chat ID
LINE_ENABLED       # Enable LINE
LINE_TOKEN         # LINE token

# Risk Management
DAILY_LOSS_LIMIT_PCT       # Max loss per day (%)
ALLOW_LOSS_CATCH_UP_AFTER  # Minutes before allowing recovery trades
```

---

### 2. **models.py** - Data Classes

**หน้าที่**: กำหนดโครงสร้างข้อมูลหลักที่ใช้ทั่วระบบ

#### IndicatorSnapshot (ตัวชี้วัดท่าทาง)
```python
@dataclass
class IndicatorSnapshot:
    ema20, ema50, ema200       # เส้นค่าเฉลี่ยเคลื่อนที่
    rsi                         # ดัชนีแรงซื้อขาย
    macd, macd_signal, macd_hist # Moving Avg Convergence/Divergence
    adx                         # Average Directional Index (แรงทิศทาง)
    atr                         # Average True Range (ความผันผวน)
    stoch_k, stoch_d            # Stochastic Oscillator
    bb_upper, bb_middle, bb_lower # Bollinger Bands
    volume, volume_sma20        # ปริมาณซื้อขายและค่าเฉลี่ย
```

#### SignalResult (ผลลัพธ์สัญญาณ)
```python
@dataclass
class SignalResult:
    symbol                  # ชื่อสัญลักษณ์เดิม
    normalized_symbol       # ชื่อสัญลักษณ์ที่ normalize
    direction               # "BUY" หรือ "SELL"
    score                   # คะแนนสัญญาณ (0-100)
    category                # ประเภท: "ignore", "candidate", "alert", "strong", "premium"
    price                   # ราคาในขณะประเมิน
    timestamp               # เวลาประเมิน
    timeframe_summary       # สรุปทิศทางแต่ละ TF
    reason_summary          # เหตุผลด้านบน 3 ประการ
    indicator_snapshot      # ค่าตัวชี้วัดทั้งหมด
    hard_filters_passed     # ผ่านคัดกรองที่เข้มงวดหรือไม่
    hard_filter_reasons     # เหตุผลที่ไม่ผ่าน (ถ้ามี)
    component_scores        # คะแนนย่อย (EMA, ADX, etc.)
    trade_plan              # แผนเทรด (SL/TP/Size)
```

#### TradePlan (แผนเทรด)
```python
@dataclass
class TradePlan:
    entry: float         # ราคาเข้า
    stop_loss: float     # ราคา stop loss
    take_profit: float   # ราคา take profit
    risk_reward: float   # อัตราส่วน risk/reward
    risk_amount: float   # เงินเสี่ยง (USD)
    position_size: float # ขนาดตำแหน่ง (lot)
    atr: float          # ค่า ATR ใช้ในการคำนวณ
```

#### SymbolState (สถานะสัญลักษณ์)
```python
@dataclass
class SymbolState:
    symbol: str              # ชื่อสัญลักษณ์
    direction: str           # BUY/SELL
    last_alert_candle_time   # เวลา candle ของแจ้งเตือนล่าสุด
    last_score: float        # คะแนนล่าสุด
    invalidated: bool        # ถูกยกเลิกหรือไม่
```

---

### 3. **mt5_connector.py** - การเชื่อมต่อ MT5

**หน้าที่**: เป็นตัวห่อหุ้มสำหรับการเชื่อมต่อ MetaTrader5

```python
class MT5Connector:
    def connect_mt5(self) -> bool:
        """เชื่อมต่อ MT5 terminal พร้อมการ login (ถ้าต้องการ)"""
        # 1. Initialize MT5 (พยายาม 3 ครั้ง)
        # 2. Check if already logged in
        # 3. Login ถ้าต้องการเข้าบัญชีอื่น
        # 4. Return success/failure
    
    def disconnect(self) -> None:
        """ปิดการเชื่อมต่อ MT5"""
    
    def get_available_symbols(self) -> list[str]:
        """ดึงรายชื่อสัญลักษณ์ทั้งหมด"""
```

**จุดสำคัญ**
- ทำการ retry 3 ครั้งเพื่อความน่าเชื่อถือ
- ตรวจสอบการ login ปัจจุบันก่อนเข้าระบบใหม่
- Error handling ที่ละเอียด

---

### 4. **data_fetcher.py** - ดึงข้อมูล

**หน้าที่**: ดึง OHLCV (Open, High, Low, Close, Volume) จาก MT5

```python
class DataFetcher:
    def fetch_ohlcv(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        """
        ดึงข้อมูลแท่งเทียน
        - symbol: ชื่อสัญลักษณ์ (ต้อง normalize ก่อน)
        - timeframe: "H4", "H1", "M15", "M5"
        - bars: จำนวนแท่งที่ต้องการ (เช่น 300)
        
        Return: DataFrame with [time, open, high, low, close, volume]
        """
        mt5_tf = to_mt5_timeframe(timeframe)  # Convert "H4" → mt5.TIMEFRAME_H4
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, bars)
        # Clean and return as DataFrame
```

**จุดสำคัญ**
- ตรวจสอบว่า데이터ว่างหรือไม่
- Convert timestamp เป็น UTC datetime
- Rename column "tick_volume" → "volume"

---

### 5. **indicators.py** - คำนวณตัวชี้วัด

**หน้าที่**: คำนวณตัวชี้วัดเทคนิคทั้งหมด

#### ตัวชี้วัดหลัก
```python
def calculate_indicators(df: pd.DataFrame, use_vwap=False, use_supertrend=False) -> pd.DataFrame:
    """
    Inputs: Raw OHLCV DataFrame
    
    Outputs: DataFrame พร้อมตัวชี้วัด:
    """
    
    # Trend Followers
    out['ema20']    = EMA 20 periods
    out['ema50']    = EMA 50 periods
    out['ema200']   = EMA 200 periods
    
    # Oscillators
    out['rsi14']    = RSI 14 periods (0-100)
    out['stoch_k']  = Stochastic %K
    out['stoch_d']  = Stochastic %D (signal)
    
    # Momentum
    out['macd']           = MACD line
    out['macd_signal']    = MACD signal line
    out['macd_hist']      = MACD histogram
    
    # Volatility
    out['atr14']        = Average True Range
    out['bb_upper']     = Bollinger Band Upper
    out['bb_middle']    = Bollinger Band Middle (SMA20)
    out['bb_lower']     = Bollinger Band Lower
    
    # Volume
    out['volume_sma20'] = 20-period volume average
    
    # Optional
    if use_vwap:
        out['vwap'] = Volume Weighted Avg Price
    if use_supertrend:
        out['supertrend'] = Supertrend indicator
```

#### ฟังก์ชันการวิเคราะห์ตัวชี้วัด
```python
def detect_trend(df: pd.DataFrame) -> str:
    """ตรวจสอบทิศทาง (bullish/bearish/sideway) จาก EMA alignment"""
    # ema20 > ema50 > ema200 → bullish
    # ema20 < ema50 < ema200 → bearish
    # อื่น ๆ → sideway

def detect_price_structure(df: pd.DataFrame, lookback: int = 30) -> str:
    """ตรวจสอบโครงสร้างราคา (HH/HL/LH/LL)"""
    # bullish (HH HL)    = recently higher highs + higher lows
    # bearish (LH LL)    = recently lower highs + lower lows
    # mixed = ไม่ชัดเจน

def detect_support_resistance(df: pd.DataFrame, lookback: int = 100) -> tuple[float | None, float | None]:
    """ค้นหาระดับ Support/Resistance จากการสวิง"""
```

---

### 6. **signal_engine.py** - ประเมินสัญญาณ

**หน้าที่**: ประเมิน BUY/SELL signals ด้วยกฎหลายข้อ

#### ฟังก์ชั่นหลัก

```python
def evaluate_buy_signal(symbol: str, normalized_symbol: str, 
                        mtf_data: dict[str, pd.DataFrame], cfg: Config) -> SignalResult:
    """
    ประเมินสัญญาณ BUY ครบวงจร
    
    1. Hard Filters - คัดกรองที่เข้มงวด
    2. ตรวจสอบ: ADX, entry zone, trend alignment
    3. หากผ่าน: คำนวณ confidence score
    4. Return: SignalResult พร้อมข้อมูลทั้งหมด
    """

def evaluate_sell_signal(...) -> SignalResult:
    """ประเมินสัญญาณ SELL (ตรงกันข้ามกับ BUY)"""
```

#### Hard Filters (คัดกรองที่เข้มงวด)

Hard filters ตัดสินว่าสัญญาณจะมีสถานะ "passed" หรือ "failed"

```
✓ PASSED    : สามารถส่งแจ้งเตือนและ alert/execute
✗ FAILED    : ม้วนอยู่ใน candidate (low priority)
```

**เงื่อนไข Hard Filters**:

| เชค | คำอธิบาย | Soft Mode | Strict Mode |
|-----|---------|----------|------------|
| ADX | แรงทิศทาง | ADX ≥ asset_minimum | ADX ≥ asset_minimum |
| Entry Zone | ราคาใกล้ EMA20 | ≤ 3.0 ATR (x1.5) | ≤ 1.8 ATR |
| H4 Trend | ทิศทางระยะยาว | H4=bullish สำหรับ BUY | ต้องตรงกับทิศทาง |
| Lower TF Conflict | ข้อขัดแย้งระหว่าง M15/M5 | อนุญาตถ้า 1 TF ตรง | ห้าม |

**ตัวอย่าง BUY Hard Filters**
```
✓ ADX(14) ≥ 14.0
✓ Entry distance ≤ 2.6 ATR
✓ H4 = bullish
✓ H1 ≠ bearish (หรือมี soft mode)
✓ ไม่ 2 timeframe lower เป็น bearish พร้อมกัน

หากล้มเหลว → reasons = ["ADX too low", "H4 bearish conflict", ...]
```

---

### 7. **scorer.py** - ให้คะแนน

**หน้าที่**: คำนวณ confidence score จาก 0-100 ด้วยระบบการให้คะแนนที่มีน้ำหนัก

#### องค์ประกอบคะแนน (Weighting System)

```python
SCORING_WEIGHTS = {
    "higher_tf": 20,           # ทิศทาง H4/H1
    "ema_alignment": 15,       # การจัดตำแหน่ง EMA
    "adx_strength": 10,        # ความแข็งแรง ADX
    "market_structure": 10,    # โครงสร้างราคา HH/LL
    "setup_quality": 12,       # คุณภาพการตั้งค่า
    "rsi_context": 8,          # บริบท RSI
    "macd_confirmation": 8,    # การยืนยัน MACD
    "stoch_trigger": 5,        # ตัวกระตุ้น Stochastic
    "volume_confirmation": 5,  # ยืนยันจากปริมาณ
    "bollinger_context": 4,    # บริบท Bollinger Bands
    "atr_suitability": 3,      # ความเหมาะสม ATR
}
# รวม: ~100 points
```

#### ฟังก์ชั่นการให้คะแนนย่อย

```python
_score_higher_tf(direction, h4_trend, h1_trend, profile)
    # BUY: H4=bullish → 20 points (H1=bullish), 10 (H1=sideway), 0 (H1=bearish)
    # SELL: H4=bearish → 20 points (H1=bearish), 10 (H1=sideway), 0 (H1=bullish)

_score_ema(direction, row)
    # Check close position relative to EMA20/50/200
    # BUY: close ≥ EMA20 → 15, pullback → 13, weak → 8
    # SELL: close ≤ EMA20 → 15, ส่วนเบี่ยง → 13, weak → 8

_score_adx(adx, profile)
    # ADX ≥ minimum+14 → 10
    # ADX ≥ minimum+10 → 8
    # ...
    # ADX < minimum → 0

_score_setup_quality(direction, row, prev_row, profile)
    # ตรวจสอบ: breakout, reversal, pullback
    # Pullback style: high (10), medium (6), low (2)

_score_rsi_context(direction, rsi, profile)
    # BUY: อยู่ใน RSI_BUY_LOW-HIGH zone → full score, นอก zone → penalty

_score_macd_confirmation(direction, macd, signal, histogram, mode)
    # "cross" mode: MACD cross signal → full score
    # "continuation" mode: MACD > signal ยาว ๆ → score higher

_score_stoch_trigger(direction, stoch_k, stoch_d, mode)
    # "cross" mode: K cross D ใน overbought/oversold → trigger
    # BUY: Stoch K < 30 → potential, K in 30-50 → normal

_score_volume_confirmation(volume, volume_sma20, ratio)
    # volume spike ≥ ratio × volume_sma20 → 5 points

_score_bollinger_context(direction, close, bb_lower, bb_upper, mode)
    # "squeeze": Bollinger Bands แคบ ๆ → ready for move
    # "mean_revert": price at band → reversion potential
```

#### คำนวณคะแนนรวม
```python
def calculate_confidence(direction, mtf_data, asset_profile) -> tuple[float, dict]:
    """
    1. คำนวณ partial scores สำหรับ M15 (setup timeframe)
    2. คำนวณ partial scores สำหรับ M5 (trigger timeframe)
    3. Weight โดยรวม: composition from all components
    4. Return: (score, component_scores_dict)
    
    # ผลลัพธ์: score ∈ [0, 100]
    """
```

#### ประเภทเชื่อมั่น (Categories)

```
ignore       : score < watchlist_threshold (< 50 default)
candidate    : watchlist_threshold ≤ score < alert_threshold (50-60)
alert        : alert_threshold ≤ score < strong_threshold (60-70)
strong       : strong_threshold ≤ score < premium_threshold (70-80)
premium      : score ≥ premium_threshold (≥ 80)
```

---

### 8. **risk_engine.py** - การจัดการความเสี่ยง

**หน้าที่**: สร้างแผนเทรด ATR-based

```python
def build_trade_plan(direction, entry_price, atr, account_balance, 
                     risk_per_trade_pct, sl_atr_multiplier, target_rr) -> TradePlan:
    """
    สร้างแผนเทรด
    
    INPUT:
    - direction: "BUY" หรือ "SELL"
    - entry_price: ราคาเข้า
    - atr: ค่า Average True Range (วัดความผันผวน)
    - account_balance: ยอดเงินบัญชี
    - risk_per_trade_pct: % ของบัญชีที่เสี่ยง (เช่น 1%)
    - sl_atr_multiplier: จำนวน ATR สำหรับ stop loss (เช่น 1.5)
    - target_rr: อัตracious risk/reward ratio (เช่น 2.0)
    
    PROCESS:
    1. risk_amount = account_balance × (risk_per_trade_pct / 100)
    2. sl_distance = ATR × sl_atr_multiplier
    
    FOR BUY:
        stop_loss = entry - sl_distance
        take_profit = entry + (sl_distance × target_rr)
    
    FOR SELL:
        stop_loss = entry + sl_distance
        take_profit = entry - (sl_distance × target_rr)
    
    3. position_size = risk_amount / sl_distance
    
    OUTPUT: TradePlan object
    """
```

**ตัวอย่าง**
```
Entry: 100
ATR: 2.2
SL multiplier: 1.5
Target RR: 2.0

BUY:
    SL distance = 2.2 × 1.5 = 3.3
    Stop Loss = 100 - 3.3 = 96.7
    Take Profit = 100 + (3.3 × 2.0) = 106.6
    Risk: 3.3 pts | Reward: 6.6 pts (2:1)
```

---

### 9. **execution.py** - ส่งคำสั่งไป MT5

**หน้าที่**: ส่งออเดอร์ไป MetaTrader5 พร้อม risk guards

```python
class ExecutionEngine:
    def try_execute_signal(self, signal: SignalResult) -> None:
        """
        ขั้นตอน:
        1. Precheck: ทำ dry-run, ตรวจ Daily Loss Guard, ตรวจ cooldown
        2. Get symbol info: ตรวจว่า symbol สามารถเทรดได้หรือไม่
        3. Calculate volume: จากแผนความเสี่ยงและข้อมูล MT5
        4. Build request: MT5 order request
        5. Send order: order_send ไป MT5
        6. Log result: บันทึกลงฐานข้อมูล
        """
```

#### Precheck

```python
def _precheck(self, signal) -> tuple[bool, str]:
    """
    ตัดสินว่าส่งคำสั่งไปหรือไม่
    
    Checks:
    ✓ DRY_RUN?            → skip
    ✓ Below min category? → skip (if configured)
    ✓ Daily loss exceed?  → skip (loss guard)
    ✓ Cooldown active?    → skip (anti-dual entry)
    ✓ Account login?      → skip if no MT5 connection
    
    Return: (allowed, reason)
    """
```

#### Order Request

```python
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": signal.normalized_symbol,
    "volume": volume,                           # ขนาดลอต
    "type": mt5.ORDER_TYPE_BUY / ORDER_TYPE_SELL,
    "price": entry,                             # ราคาปัจจุบัน
    "sl": sl,                                   # Stop loss
    "tp": tp,                                   # Take profit
    "deviation": max_slippage_points,           # ยอมรับ slippage สูงสุด
    "magic": magic_number,                      # Magic number (identifier)
    "comment": f"pytrade:{category}:{score:.1f}",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,      # Fill or Kill
}

result = mt5.order_send(request)
```

#### Sizing

```python
def _calc_volume(self, symbol_info, entry, sl, risk_amount) -> float:
    """
    คำนวณ volume
    volume = risk_amount / (abs(entry - sl) × symbol_info.point × symbol_info.trade_tick_value)
    
    Risk amount มาจาก:
    1. Static: จากแผนเทรด (trade_plan['risk_amount'])
    2. Dynamic: from MT5 balance × risk_per_trade_pct (ถ้า enabled)
    """
```

#### Order Tracking

```python
def sync_orders(self) -> None:
    """
    ซิงก์สถานะออเดอร์ที่เคยส่ง
    1. ดึงออเดอร์ที่ status="sent"
    2. Query MT5 deals/positions
    3. Update closed orders: status="closed" + PnL
    4. Handle partial close (smart exit rules)
    """
```

---

### 10. **notifier.py** - ส่งแจ้งเตือน

**หน้าที่**: ส่งแจ้งเตือนและปกป้องจากการซ้ำซ้อน

```python
class Notifier:
    def should_alert(self, signal: SignalResult) -> bool:
        """
        ตรวจสอบว่าควรแจ้งเตือนหรือไม่
        
        Conditions:
        1. hard_filters_passed == True
        2. score ≥ alert_threshold
        3. signal.category ≥ min_alert_category
        4. Anti-duplicate check:
           - ไม่ใช่ candle เดียวกัน
           - หรือคะแนนดีขึ้นมากกว่า anti_dup_score_delta
           - หรือสัญญาณเก่าถูกยกเลิก
        
        Return: bool
        """
    
    def mark_invalidation(self, symbol: str, direction: str) -> None:
        """
        ตั้ง invalidation flag เมื่อคุณภาพลดลงต่ำกว่า watchlist
        → หากมีสัญญาณใหม่: ถือว่า setup ใหม่ = alert
        """
    
    def send_alert(self, signal: SignalResult) -> None:
        """
        ส่งแจ้งเตือนไป:
        1. Console (logger)
        2. Telegram (ถ้าเปิด)
        3. LINE (ถ้าเปิด)
        
        บันทึกสถานะล่าสุด: last_alert_candle_time, last_score, invalidated=False
        """
```

#### รูปแบบข้อความ

```
🚨 PREMIUM | 🟢 BUY BTCUSD
Score 82.50 | Price 43215.52000
TF H4:bullish H1:bullish M15:bullish M5:bullish
RSI 65.32 | MACD 0.0123/0.0098 | ADX 28.45
SL 42156.80000 | TP 44274.24000 | Size 0.0500 | Risk $50.00
Top factors: higher_tf:20.0, setup_quality:12.0, ema_alignment:11.5
2026-03-18T15:30:45+00:00 | rule-based confidence (not win rate)
```

---

### 11. **symbol_manager.py** - จัดการชื่อสัญลักษณ์

**หน้าที่**: Normalize ชื่อสัญลักษณ์เพื่อให้ตรงกับ broker

```python
def normalize_symbol_name(symbol: str, available_symbols: list[str]) -> str | None:
    """
    แปลง generic symbol name เป็นชื่อ broker-specific
    
    ตัวอย่าง:
    Input: "BTCUSD", available = ["BTCUSDm", "BTCUSD.a"]
    Output: "BTCUSDm"  (หรือ "BTCUSD.a" ถ้า exact match ไม่พบ)
    
    Process:
    1. ลองหา exact match (case-insensitive)
    2. ลองหา candidates ที่ขึ้นต้นด้วย symbol
    3. เลือก shortest candidate (prefer minimal suffix)
    """

class SymbolManager:
    def resolve(self) -> dict[str, str]:
        """
        Map requested symbols → broker symbols
        
        Example:
        requested = ["BTC", "ETH"]
        available = ["BTCUSDm", "BTCUSDmQ", "ETH..."]
        
        Return:
        {
            "BTC": "BTCUSDm",
            "ETH": "ETH...",
        }
        """
```

---

### 12. **logger_db.py** - ฐานข้อมูล SQLite

**หน้าที่**: บันทึกประวัติการสแกน สัญญาณ และออเดอร์

#### ตาราง (Tables)

```sql
signals
├── timestamp, symbol, normalized_symbol
├── direction (BUY/SELL), score, category
├── price, reason_summary
├── timeframe_summary_json, indicator_snapshot_json
├── component_scores_json, trade_plan_json
├── hard_filters_passed, hard_filter_reasons_json

scan_events
├── timestamp, symbol, level (INFO/WARNING)
├── message, details_json

symbol_states
├── symbol, direction (PK)
├── last_alert_candle_time, last_score
├── invalidated (0/1)

orders
├── timestamp, symbol, normalized_symbol, direction
├── category, score
├── entry_price, stop_loss, take_profit, volume
├── risk_amount, status (sent/failed/closed/skipped)
├── reason, mt5_order, mt5_position, comment
├── partial_close_done, pnl, closed_at

runtime_state
├── key: "last_scan_time", "daily_loss_amount", etc.

config_audit
├── timestamp, source, summary, changes_json
```

#### API หลัก

```python
class SignalDB:
    def save_signal_to_db(self, signal: SignalResult) -> None:
        """บันทึกสัญญาณลงตาราง signals"""
    
    def log_scan_event(self, symbol: str, level: str, message: str, 
                      details: dict | None = None) -> None:
        """บันทึกเหตุการณ์สแกนลงตาราง scan_events"""
    
    def upsert_symbol_state(self, state: SymbolState) -> None:
        """บันทึก/อัปเดตสถานะสัญลักษณ์"""
    
    def get_symbol_state(self, symbol: str, direction: str) -> SymbolState | None:
        """อ่านสถานะสัญลักษณ์ล่าสุด"""
    
    def log_order_sent(self, signal: SignalResult, entry, sl, tp, volume) -> None:
        """บันทึกออเดอร์ที่ส่งไป MT5"""
    
    def sync_orders(self) -> None:
        """ซิงก์สถานะออเดอร์ที่เก่า"""
    
    def get_today_realized_loss(self) -> float:
        """ดึงการขาดทุนที่เกิดขึ้นจริง (realized loss) วันนี้"""
    
    def reset_daily_loss_guard(self) -> None:
        """รีเซ็ต daily loss counter"""
```

---

## ลำดับการทำงาน

### 1. **Main Scan Loop** (main.py)

```python
def main():
    # 1. Setup
    setup_logging()
    cfg = load_config_from_env()
    connector = connect_mt5(cfg)  # เชื่อมต่อ MT5
    
    # 2. Initialize
    db = SignalDB(db_path)
    fetcher = DataFetcher(connector)
    symbol_manager = SymbolManager(cfg.watch_symbols, connector.get_available_symbols())
    executor = ExecutionEngine(cfg, db)
    notifier = Notifier(cfg, db)
    
    # 3. Scan Loop
    while True:
        for symbol in symbol_manager.resolve().items():
            _evaluate_symbol(symbol, fetcher, db, notifier, executor)
        
        if args.once:
            break
        
        time.sleep(cfg.scan_interval_seconds)
```

### 2. **Symbol Evaluation** (_evaluate_symbol)

```python
def _evaluate_symbol(symbol, normalized_symbol, fetcher, db, notifier, executor):
    # Step 1: Fetch multi-timeframe data
    mtf_data = _prepare_mtf_data(fetcher, normalized_symbol, cfg)
    if not mtf_data:
        db.log_scan_event(symbol, "WARNING", "insufficient_data")
        return
    
    # Step 2: Evaluate BUY signal
    buy_signal = evaluate_buy_signal(symbol, normalized_symbol, mtf_data, cfg)
    buy_signal.score = calculate_confidence(buy_signal_result, cfg)
    save_signal_to_db(db, buy_signal)
    
    # Step 3: Evaluate SELL signal
    sell_signal = evaluate_sell_signal(symbol, normalized_symbol, mtf_data, cfg)
    sell_signal.score = calculate_confidence(sell_signal_result, cfg)
    save_signal_to_db(db, sell_signal)
    
    # Step 4: Mark invalidation (if below watchlist threshold)
    if buy_signal.score < cfg.watchlist_threshold:
        notifier.mark_invalidation(normalized_symbol, "BUY")
    if sell_signal.score < cfg.watchlist_threshold:
        notifier.mark_invalidation(normalized_symbol, "SELL")
    
    # Step 5: Alert & Execute
    best = buy_signal if buy_signal.score >= sell_signal.score else sell_signal
    
    if notifier.should_alert(best):
        notifier.send_alert(best)
    
    if cfg.execution_enabled:
        executor.try_execute_signal(best)
    
    # Step 6: Sync old orders (every N scans)
    if scan_count % cfg.sync_interval == 0:
        executor.sync_orders()
```

### 3. **Data Preparation** (_prepare_mtf_data)

```
สำหรับแต่ละ timeframe (H4, H1, M15, M5):
    1. Fetch OHLCV → fetcher.fetch_ohlcv()
    2. Calculate indicators → calculate_indicators()
    3. Check if fresh (age ≤ 3 × TF minutes)
    4. Ensure sufficient history (≥ 220 bars)
    5. Return dict of: { "H4": df, "H1": df, ... }
```

---

## ระบบการให้คะแนน

### คะแนน 0-100 ประกอบด้วย

```
┌─────────────────────────────────────┐
│    TOTAL CONFIDENCE SCORE (0-100)   │
├─────────────────────────────────────┤
│ 1. Higher TF (H4/H1) Alignment  20% │ → _score_higher_tf()
│ 2. EMA Structure & Position     15% │ → _score_ema()
│ 3. Trend Strength (ADX)         10% │ → _score_adx()
│ 4. Price Structure (HH/LL)      10% │ → _score_structure()
│ 5. Setup Candle Quality         12% │ → _score_setup_quality()
│ 6. RSI Context & Zone            8% │ → _score_rsi_context()
│ 7. MACD Confirmation             8% │ → _score_macd_confirmation()
│ 8. Stochastic Trigger            5% │ → _score_stoch_trigger()
│ 9. Volume Confirmation           5% │ → _score_volume_confirmation()
│ 10. Bollinger Bands Context      4% │ → _score_bollinger_context()
│ 11. ATR Suitability              3% │ → _score_atr_suitability()
└─────────────────────────────────────┘
         ↓
   CONFIDENCE SCORE
```

### ประเภทสัญญาณตาม Score

| Category | Score Range | Description | Default Execute? |
|----------|------------|-------------|------------------|
| **ignore** | 0-49 | ไม่น่าสนใจ | ✗ |
| **candidate** | 50-59 | ติดตามได้ | ✗ |
| **alert** | 60-69 | ส่งแจ้งเตือน | ✓ |
| **strong** | 70-79 | สัญญาณแรง | ✓ |
| **premium** | 80-100 | สัญญาณพรีเมียม | ✓ |

---

## ระบบการขาย/ซื้อ

### Hard Filters ว่างาน (การคัดกรอง)

Hard filters เป็นการตัดสินใจว่า "สัญญาณนี้ควร execute หรือเป็น candidate เท่านั้น"

#### สำหรับ BUY Signal

```
✓ PASS hard_filters ถ้า:
  1. ADX ≥ minimum (จากโปรไฟล์สินทรัพย์)
  2. Entry distance ≤ max_atr (ราคาใกล้ EMA20)
  3. H4 = bullish (โหมด soft: อนุญาต sideway + H1 bullish)
  4. H1 ≠ bearish (หรือ soft mode: อนุญาต bearish ถ้า M15 bullish)
  5. ไม่มี "severe conflict": M15 bearish + M5 bearish
  
✗ FAIL hard_filters ถ้า:
  - ADX too low
  - Entry zone too large
  - H4 bearish (conflict)
  - Higher TF misalignment
  - Lower TF conflict
```

#### สำหรับ SELL Signal

```
✓ PASS เหมือน BUY แต่:
  - H4 = bearish แล้ว H1 ≠ bullish
  - Lower TF: ไม่ 2 TF bullish พร้อมกัน
```

### Anti-Duplicate Policy

หลีกเลี่ยงการแจ้งเตือนซ้ำซ้อน:

```python
def should_alert(signal: SignalResult) -> bool:
    # Check 1: Score meets threshold
    if signal.score < cfg.alert_threshold:
        return False
    
    # Check 2: Hard filters passed
    if not signal.hard_filters_passed:
        return False
    
    # Check 3: Get last alert state
    state = db.get_symbol_state(symbol, direction)
    if state is None:
        return True  # First time → alert
    
    # Check 4: Same candle?
    if state.last_alert_candle_time == signal.timestamp:
        return False  # Don't repeat on same candle
    
    # Check 5: Score improved?
    if signal.score >= state.last_score + cfg.anti_dup_score_delta:
        return True  # Score improved significantly
    
    # Check 6: Was invalidated?
    if state.invalidated:
        return True  # New setup
    
    return False
```

---

## ไฟล์ Dashboard (streamlit_app.py)

**หน้าที่**: แสดงสถานะระบบ ผลการเทรด และการตั้งค่า

### แท็บหลัก

1. **Dashboard** - ภาพรวมการเทรด
   - สถานะเดมอน (running/stopped)
   - ออเดอร์เปิด/ปิด/ล้มเหลว
   - PnL วันนี้ และสะสม
   - Equity Curve จากออเดอร์ปิด

2. **Performance** - ผลงานโดยละเอียด
   - Filter by date range
   - Win rate, profit factor, drawdown
   - แบ่งตามประเภท/สัญลักษณ์/ทิศทาง

3. **Portfolio** - สถานะพอร์ต
   - ออเดอร์เปิดจาก MT5 (bot vs manual)
   - ออเดอร์ปิดล่าสุด
   - Sizing status (dynamic/static)

4. **Health** - สุขภาพระบบ
   - Process status (daemon/dashboard)
   - Database integrity
   - Config audit trail

5. **Config** - ตั้งค่า
   - Profile selector (aggressive/normal/strict)
   - Alert thresholds
   - Execution toggles
   - Risk limits

6. **Guide** - คู่มือ

7. **Deploy Wizard** - ติดตั้ง/อัปเดต

---

## สรุป Dependencies

```
MetaTrader5>=5.0.45      # MT5 API
pandas>=2.2.0             # Data manipulation
numpy>=1.26.0             # Numerical computing
ta>=0.11.0                # Technical Analysis library
python-dotenv>=1.0.1      # Environment variables
requests>=2.32.0          # HTTP requests (Telegram/LINE)
schedule>=1.2.0           # Job scheduling
streamlit>=1.44.0         # Web dashboard
streamlit-autorefresh     # Auto-refresh
pytest>=8.2.0             # Unit testing
```

---

## สรุปสถาปัตยกรรม

```
┌─────────────────────────────────────────────────────────┐
│                   DATA LAYER                             │
├─────────────────────────────────────────────────────────┤
│ MetaTrader5 Terminal  ← → MT5Connector ← → DataFetcher   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                 ANALYSIS LAYER                           │
├─────────────────────────────────────────────────────────┤
│ Indicators → Signal Engine → Scorer ([0-100])            │
│                               ↓                           │
│                        + Hard Filters                     │
│                        + Risk Engine (Trade Plan)         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│               CONTROL & PERSISTENCE                      │
├─────────────────────────────────────────────────────────┤
│ Notifier ← → Execution ← → Logger DB (SQLite)            │
│   │           │                        │                  │
│   ├→ Console  ├→ MT5 Order             └→ Signals        │
│   ├→ Telegram ├→ Order Sync                Orders        │
│   └→ LINE     └→ Risk Guards            Events          │
└─────────────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────────────┐
│                PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────┤
│            Streamlit Dashboard Web UI                    │
└─────────────────────────────────────────────────────────┘
```

---

## Key Performance Metrics ที่ติดตาม

1. **Daily Realized Loss** - ขาดทุนที่เกิดขึ้นจริง (จาก closed orders)
2. **Equity Curve** - กราฟกำไร/ขาดทุนสะสม
3. **Win Rate** - จำนวน winning trades / total trades
4. **Profit Factor** - Gross Profit / Gross Loss
5. **Max Drawdown** - ความลดลงสูงสุดจาก peak
6. **Sharpe Ratio** - Risk-adjusted returns

---

เสร็จสิ้นการวิเคราะห์โค้ด PyTrade!
