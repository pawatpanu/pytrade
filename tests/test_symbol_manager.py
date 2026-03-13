from core.symbol_manager import normalize_symbol_name


def test_normalize_symbol_exact_and_suffix() -> None:
    available = ["BTCUSDm", "ETHUSD", "XRPUSD.a"]

    assert normalize_symbol_name("ETHUSD", available) == "ETHUSD"
    assert normalize_symbol_name("BTCUSD", available) == "BTCUSDm"
    assert normalize_symbol_name("XRPUSD", available) == "XRPUSD.a"


def test_normalize_symbol_missing() -> None:
    available = ["BTCUSDm", "ETHUSD"]
    assert normalize_symbol_name("SOLUSD", available) is None
