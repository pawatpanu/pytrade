from __future__ import annotations

import logging

import pandas as pd

from core.mt5_connector import MT5Connector
from core.utils import to_mt5_timeframe

logger = logging.getLogger(__name__)


class DataFetcher:
    """Load OHLCV candles from MetaTrader5."""

    def __init__(self, connector: MT5Connector) -> None:
        self.connector = connector

    def fetch_ohlcv(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        """Fetch OHLCV data and normalize into a DataFrame."""
        import MetaTrader5 as mt5

        mt5_tf = to_mt5_timeframe(timeframe)
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, bars)
        if rates is None or len(rates) == 0:
            code, msg = mt5.last_error()
            logger.warning("No data for %s %s: %s (%s)", symbol, timeframe, code, msg)
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df = df.rename(columns={"tick_volume": "volume"})
        keep_cols = ["time", "open", "high", "low", "close", "volume"]
        df = df[keep_cols].dropna().reset_index(drop=True)
        return df


def fetch_ohlcv(fetcher: DataFetcher, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
    """Convenience function for required API surface."""
    return fetcher.fetch_ohlcv(symbol, timeframe, bars)
