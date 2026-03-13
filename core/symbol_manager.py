from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def normalize_symbol_name(symbol: str, available_symbols: list[str]) -> str | None:
    """Match generic symbol names to broker-specific variants (e.g., BTCUSDm, BTCUSD.a)."""
    target = symbol.upper()
    normalized_map = {s.upper(): s for s in available_symbols}

    if target in normalized_map:
        return normalized_map[target]

    candidates = [s for s in available_symbols if s.upper().startswith(target)]
    if not candidates:
        return None

    # Prefer shortest suffix match first.
    candidates = sorted(candidates, key=lambda s: (len(s), s))
    return candidates[0]


class SymbolManager:
    """Resolve requested symbols to valid broker symbols."""

    def __init__(self, requested_symbols: list[str], available_symbols: list[str]) -> None:
        self.requested_symbols = requested_symbols
        self.available_symbols = available_symbols

    def resolve(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for symbol in self.requested_symbols:
            normalized = normalize_symbol_name(symbol, self.available_symbols)
            if not normalized:
                logger.warning("Symbol '%s' not found on broker. Skip.", symbol)
                continue
            mapping[symbol] = normalized
        return mapping
