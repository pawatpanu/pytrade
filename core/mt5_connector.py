from __future__ import annotations

import logging
import time
from typing import Any

import MetaTrader5 as mt5

from config import Config

logger = logging.getLogger(__name__)


class MT5Connector:
    """Wrapper around MetaTrader5 connection lifecycle."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.connected = False

    def connect_mt5(self) -> bool:
        """Initialize MT5 terminal and optionally login."""
        kwargs: dict[str, Any] = {}
        if self.config.mt5_path:
            kwargs["path"] = self.config.mt5_path

        connected = False
        for attempt in range(3):
            if mt5.initialize(**kwargs):
                connected = True
                break
            code, msg = mt5.last_error()
            logger.error("MT5 initialize failed: %s (%s) [attempt %s/3]", code, msg, attempt + 1)
            if attempt < 2:
                time.sleep(0.75 * (attempt + 1))
        if not connected:
            return False

        if self.config.mt5_login and self.config.mt5_password and self.config.mt5_server:
            account = mt5.account_info()
            current_login = int(getattr(account, "login", 0) or 0) if account else 0
            if current_login != int(self.config.mt5_login):
                logged_in = mt5.login(
                    login=self.config.mt5_login,
                    password=self.config.mt5_password,
                    server=self.config.mt5_server,
                )
                if not logged_in:
                    code, msg = mt5.last_error()
                    logger.error("MT5 login failed: %s (%s)", code, msg)
                    mt5.shutdown()
                    return False

        self.connected = True
        logger.info("MT5 connected successfully")
        return True

    def disconnect(self) -> None:
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("MT5 disconnected")

    def get_available_symbols(self) -> list[str]:
        """Return all symbols visible from current MT5 terminal."""
        symbols = mt5.symbols_get()
        if symbols is None:
            code, msg = mt5.last_error()
            logger.error("Unable to fetch symbols: %s (%s)", code, msg)
            return []
        return [s.name for s in symbols]


def connect_mt5(config: Config) -> MT5Connector:
    """Factory helper to connect and return initialized MT5Connector."""
    connector = MT5Connector(config)
    if not connector.connect_mt5():
        raise RuntimeError("Cannot connect MetaTrader5. Please verify terminal/login settings.")
    return connector


def get_available_symbols(connector: MT5Connector) -> list[str]:
    """Convenience function for required API surface."""
    return connector.get_available_symbols()
