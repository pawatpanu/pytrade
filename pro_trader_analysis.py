#!/usr/bin/env python3
"""
Professional Trader MTF Confluence Analysis
Shows exactly why a signal gets its score (breakdown by component + TF)
"""

import MetaTrader5 as mt5
from config import CONFIG
from core.mt5_connector import connect_mt5
from core.data_fetcher import DataFetcher
from core.indicators import calculate_indicators, detect_trend, detect_price_structure
from core.signal_engine import evaluate_buy_signal, evaluate_sell_signal
import json

if not connect_mt5(CONFIG):
    print("❌ MT5 not available")
    exit(1)

fetcher = DataFetcher(None)

# Test symbols
test_symbols = [
    ("BTCUSD", "BTCUSDm"),
    ("ETHUSD", "ETHUSDm"),
    ("XRPUSD", "XRPUSDm"),
]

print("\n" + "="*80)
print("PROFESSIONAL TRADER MTF CONFLUENCE ANALYSIS")
print("="*80)

for symbol, normalized in test_symbols:
    print(f"\n📊 {symbol} ANALYSIS\n")
    
    # Prepare MTF data
    mtf_data = {}
    tf_list = [CONFIG.timeframe_primary, CONFIG.timeframe_confirm, CONFIG.timeframe_setup, CONFIG.timeframe_trigger]
    
    for tf in tf_list:
        raw = fetcher.fetch_ohlcv(normalized, tf, CONFIG.bars_to_fetch)
        if raw.empty:
            print(f"  {tf}: ❌ No data")
            break
        calc = calculate_indicators(raw)
        if len(calc) < 220:
            print(f"  {tf}: ❌ Insufficient bars ({len(calc)})")
            break
        mtf_data[tf] = calc
    
    if len(mtf_data) < 4:
        print(f"  ⚠️  Incomplete MTF data, skipping\n")
        continue
    
    # Get signal
    buy_signal = evaluate_buy_signal(symbol, normalized, mtf_data, CONFIG)
    sell_signal = evaluate_sell_signal(symbol, normalized, mtf_data, CONFIG)
    
    best = buy_signal if buy_signal.score >= sell_signal.score else sell_signal
    
    # Display
    print(f"  Direction: {best.direction}")
    print(f"  Score: {best.score:.1f} / 100")
    print(f"  Category: {best.category.upper()}")
    print(f"  Hard Filters Passed: {'✅' if best.hard_filters_passed else '❌'}")
    
    if not best.hard_filters_passed:
        print(f"  Reasons: {best.hard_filter_reasons}")
    
    # Component breakdown (Confluence view)
    if best.component_scores:
        print(f"\n  CONFLUENCE BREAKDOWN:")
        components = sorted(best.component_scores.items(), key=lambda x: x[1], reverse=True)
        for name, score in components:
            if score > 0:
                pct = (score / 100) * 100 if 100 > 0 else 0
                bar = "█" * int(score/3) + "░" * (33-int(score/3))
                print(f"    {name:20} {score:5.1f}  {bar}")
    
    # TF Summary
    print(f"\n  TREND ACROSS TF:")
    for tf in tf_list:
        if tf in mtf_data:
            trend = detect_trend(mtf_data[tf])
            last = mtf_data[tf].iloc[-2]
            adx = last['adx14']
            print(f"    {tf}: {trend:10} (ADX={adx:.1f})")
    
    # Entry quality
    if best.component_scores:
        setup_score = best.component_scores.get('setup_quality', 0)
        trigger_score = best.component_scores.get('stoch_trigger', 0) + \
                       best.component_scores.get('volume_confirmation', 0)
        
        print(f"\n  ENTRY QUALITY (Pro Check):")
        print(f"    Setup Quality: {'✅ GOOD' if setup_score >= 8 else '⚠️  WEAK'} ({setup_score:.1f})")
        print(f"    M5 Triggers: {'✅ STRONG' if trigger_score >= 8 else '⚠️  WEAK'} ({trigger_score:.1f})")
        
        if best.trade_plan:
            tp = best.trade_plan.get('take_profit', 0)
            sl = best.trade_plan.get('stop_loss', 0)
            entry = best.trade_plan.get('entry', best.price)
            if entry and sl and tp:
                risk = abs(entry - sl)
                reward = abs(tp - entry)
                rr = reward / risk if risk > 0 else 0
                print(f"    Risk/Reward: {'✅ OK' if rr >= 1.8 else '❌ LOW'} - RR={rr:.2f}:1")
    
    print(f"\n  EXECUTION: {'✅ WOULD EXECUTE' if best.category in ['strong', 'premium', 'ultra'] else '⏭️  SKIP (below threshold)'}")
    print("-" * 80)

mt5.shutdown()
print("\n✅ Analysis complete\n")
