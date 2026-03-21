from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import ADXIndicator, EMAIndicator, MACD
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import VolumeWeightedAveragePrice

logger = logging.getLogger(__name__)


def _calc_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    """Minimal Supertrend calculation for optional feature."""
    atr = AverageTrueRange(df["high"], df["low"], df["close"], window=period).average_true_range()
    hl2 = (df["high"] + df["low"]) / 2.0
    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)

    for i in range(len(df)):
        if i == 0:
            supertrend.iloc[i] = upperband.iloc[i]
            direction.iloc[i] = 1
            continue

        prev_st = supertrend.iloc[i - 1]
        prev_dir = direction.iloc[i - 1]

        curr_upper = upperband.iloc[i]
        curr_lower = lowerband.iloc[i]

        if prev_dir == 1:
            curr_lower = max(curr_lower, lowerband.iloc[i - 1])
        else:
            curr_upper = min(curr_upper, upperband.iloc[i - 1])

        if df["close"].iloc[i] > curr_upper:
            direction.iloc[i] = 1
            supertrend.iloc[i] = curr_lower
        elif df["close"].iloc[i] < curr_lower:
            direction.iloc[i] = -1
            supertrend.iloc[i] = curr_upper
        else:
            direction.iloc[i] = prev_dir
            supertrend.iloc[i] = curr_lower if prev_dir == 1 else curr_upper

    return supertrend


def calculate_indicators(df: pd.DataFrame, use_vwap: bool = False, use_supertrend: bool = False) -> pd.DataFrame:
    """Calculate indicators required by scoring engine."""
    if df.empty:
        return df

    out = df.copy()

    out["ema20"] = EMAIndicator(out["close"], window=20).ema_indicator()
    out["ema50"] = EMAIndicator(out["close"], window=50).ema_indicator()
    out["ema200"] = EMAIndicator(out["close"], window=200).ema_indicator()

    out["rsi14"] = RSIIndicator(out["close"], window=14).rsi()

    macd = MACD(out["close"], window_fast=12, window_slow=26, window_sign=9)
    out["macd"] = macd.macd()
    out["macd_signal"] = macd.macd_signal()
    out["macd_hist"] = macd.macd_diff()

    bb = BollingerBands(out["close"], window=20, window_dev=2)
    out["bb_upper"] = bb.bollinger_hband()
    out["bb_middle"] = bb.bollinger_mavg()
    out["bb_lower"] = bb.bollinger_lband()

    adx = ADXIndicator(out["high"], out["low"], out["close"], window=14)
    out["adx14"] = adx.adx()
    out["plus_di14"] = adx.adx_pos()
    out["minus_di14"] = adx.adx_neg()
    out["atr14"] = AverageTrueRange(out["high"], out["low"], out["close"], window=14).average_true_range()

    stoch = StochasticOscillator(out["high"], out["low"], out["close"], window=14, smooth_window=3)
    out["stoch_k"] = stoch.stoch()
    out["stoch_d"] = stoch.stoch_signal()

    out["volume_sma20"] = out["volume"].rolling(20).mean()

    if use_vwap:
        out["vwap"] = VolumeWeightedAveragePrice(
            high=out["high"], low=out["low"], close=out["close"], volume=out["volume"], window=14
        ).volume_weighted_average_price()

    if use_supertrend:
        out["supertrend"] = _calc_supertrend(out)

    out = out.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
    return out


def detect_price_structure(df: pd.DataFrame, lookback: int = 30) -> str:
    """Detect HH/HL or LH/LL style market structure."""
    if len(df) < lookback:
        return "unknown"

    sample = df.tail(lookback).copy()
    highs = sample["high"].rolling(3, center=True).max() == sample["high"]
    lows = sample["low"].rolling(3, center=True).min() == sample["low"]

    swing_highs = sample.loc[highs, "high"].tail(3).tolist()
    swing_lows = sample.loc[lows, "low"].tail(3).tolist()

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "mixed"

    hh = swing_highs[-1] > swing_highs[-2]
    hl = swing_lows[-1] > swing_lows[-2]
    lh = swing_highs[-1] < swing_highs[-2]
    ll = swing_lows[-1] < swing_lows[-2]

    if hh and hl:
        return "bullish"
    if lh and ll:
        return "bearish"
    return "mixed"


def detect_trend(df: pd.DataFrame) -> str:
    """Detect directional trend using EMA alignment and close location."""
    if len(df) < 3:
        return "unknown"

    row = df.iloc[-2]
    # Use alignment-first classification to avoid over-filtering on temporary pullbacks.
    if row["ema20"] > row["ema50"] > row["ema200"]:
        return "bullish"
    if row["ema20"] < row["ema50"] < row["ema200"]:
        return "bearish"
    return "sideway"


def detect_support_resistance(df: pd.DataFrame, lookback: int = 100) -> tuple[float | None, float | None]:
    """Estimate support/resistance from recent swing lows/highs."""
    if len(df) < 20:
        return None, None

    sample = df.tail(lookback)
    curr = float(sample.iloc[-2]["close"])

    resistance_candidates = sample.loc[sample["high"].rolling(3, center=True).max() == sample["high"], "high"]
    support_candidates = sample.loc[sample["low"].rolling(3, center=True).min() == sample["low"], "low"]

    resistance = resistance_candidates[resistance_candidates > curr].min() if not resistance_candidates.empty else np.nan
    support = support_candidates[support_candidates < curr].max() if not support_candidates.empty else np.nan

    support_val = float(support) if pd.notna(support) else None
    resistance_val = float(resistance) if pd.notna(resistance) else None
    return support_val, resistance_val
