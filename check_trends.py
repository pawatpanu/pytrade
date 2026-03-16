import MetaTrader5 as mt5
from config import CONFIG
from core.mt5_connector import connect_mt5
from core.indicators import calculate_indicators, detect_trend
from core.data_fetcher import DataFetcher

# Connect
if not connect_mt5(CONFIG):
    print("MT5 not available")
    exit(1)

fetcher = DataFetcher(None)

# Check BTCUSD trends
symbol = "BTCUSDm"
timeframes = ["H4", "H1", "M15", "M5"]

print(f"\n=== Market Trends for {symbol} ===\n")

for tf in timeframes:
    # Fetch data
    raw = fetcher.fetch_ohlcv(symbol, tf, 100)
    if raw.empty:
        print(f"{tf}: ❌ No data")
        continue
    
    # Calculate indicators
    calc = calculate_indicators(raw)
    trend = detect_trend(calc)
    
    # Get last candle
    if len(calc) > 2:
        last = calc.iloc[-2]
        print(f"{tf}: {trend:10} | Close={last['close']:.2f} EMA20={last['ema20']:.2f} ADX={last['adx14']:.2f}")
    elif len(calc) > 0:
        last = calc.iloc[-1]
        print(f"{tf}: {trend:10} | Close={last['close']:.2f} EMA20={last['ema20']:.2f} ADX={last['adx14']:.2f} [last only]")
    else:
        print(f"{tf}: ❌ Empty after indicators")

mt5.shutdown()
