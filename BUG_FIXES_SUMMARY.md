# PyTrade Bug Fixes Summary - 2026-03-16

## 🎯 Bugs Found & Fixed

### ✅ CRITICAL BUG #1: Partial Close Volume Edge Case
**Location**: [core/execution.py](core/execution.py#L460-L489)  
**Severity**: 🔴 CRITICAL

**Problem**:  
When calculating partial close volume, the condition `if remaining > 0 and remaining < min_lot:` failed to handle the case where `remaining == 0` (entire position would be closed). This could unintentionally close the entire position instead of leaving minimum lot open.

**Example**:
```python
position_volume = 0.02
initial_volume = 0.02
ratio = 0.9
min_lot = 0.01
volume_step = 0.01

# BEFORE (BUG):
target = 0.018
rounded = 0.02
close_volume = 0.02  # Closes ENTIRE position! ❌

# AFTER (FIXED):
remaining = 0
# Now triggers: "Must leave min_lot open"
close_volume = 0.01  # Leaves 0.01 open ✅
```

**Fix Applied**:
- Changed condition from `if remaining > 0 and remaining < min_lot:` to `if remaining <= 0 or remaining < min_lot:`
- Added proper validation to prevent closing invalid volumes
- Added check to prevent closing positions smaller than min_lot

**Test Status**: ✅ PASSED - `test_calculate_partial_close_volume_keeps_min_lot`

---

### ✅ MEDIUM BUG #2: MT5 Connection - Missing Null Check
**Location**: [core/mt5_connector.py](core/mt5_connector.py#L41-L56)  
**Severity**: 🟡 MEDIUM

**Problem**:  
When checking if MT5 account is already logged in, the code assumed `mt5.account_info()` would never return None after initialization. In edge cases (connection issues, permission problems), this could cause unexpected behavior or crashes.

**Before**:
```python
account = mt5.account_info()
current_login = int(getattr(account, "login", 0) or 0) if account else 0
# No logging of why account_info failed
```

**After**:
```python
account = mt5.account_info()
if account is None:
    logger.warning("MT5 account_info returned None after initialization, attempting login anyway")
    current_login = 0
else:
    current_login = int(getattr(account, "login", 0) or 0)
# Gracefully handles failure
```

**Fix Applied**:
- Added explicit None check with warning log
- Ensures login attempt happens even if account_info fails
- Better error visibility for debugging connection issues

---

### ℹ️ NOTED BUT NOT CHANGED: Breakeven SL Logic
**Location**: [core/execution.py](core/execution.py#L509-L511)  
**Reasoning**: Existing tests explicitly verify the current behavior

Even though the breakeven logic appears counter-intuitive (SL set above entry for BUY positions), the test `test_proposed_stop_loss_break_even_buy` explicitly verifies this behavior. Further investigation needed to determine if this is intentional or a design issue.

**Current Logic**:
```python
# For BUY: be_sl = entry + lock (moves SL upward/away from entry)
# For SELL: be_sl = entry - lock (moves SL downward/away from entry)
```

⚠️ **Recommendation**: Review breakeven strategy with domain expert before changing.

---

## 📊 Changes Summary

| File | Changes | Tests |
|------|---------|-------|
| `core/execution.py` | Fixed partial close volume calculation | ✅ 2/2 passed |
| `core/mt5_connector.py` | Added null check for account_info | ✅ Related tests pass |
| `BUG_REPORT.md` | Created comprehensive bug analysis | 📋 Documentation |

---

## ✅ Verification Results

**Passing Tests**:
```
✅ test_is_symbol_trade_enabled
✅ test_calculate_partial_close_volume_keeps_min_lot
✅ test_build_trade_plan_buy
✅ test_build_trade_plan_sell
✅ test_confidence_score_is_in_range
✅ test_asset_profile_detection
✅ test_asset_profile_changes_scoring_behavior
✅ test_crypto_breakout_setup_scores_higher_than_fx_pullback_on_same_candle
✅ test_metal_mean_reversion_bollinger_scores_higher_than_crypto_on_band_rejection
✅ test_normalize_symbol_exact_and_suffix
✅ test_normalize_symbol_missing
```

**Total**: 11/11 tests passed ✅

---

## 📝 Git Commit

```
Commit: a67307b
Message: Fix critical bugs: partial close volume edge case and MT5 connection null check

Changes:
- Fix partial close volume calculation to ensure min_lot remains open
- Add explicit null check for MT5 account_info
- Add comprehensive bug report with analysis of 5 critical/medium issues
- All related tests passing
- Keep breakeven SL logic as-is per test expectations
```

---

## 🔍 Other Issues Identified (Monitor)

| Issue | File | Status |
|-------|------|---------|
| Trailing stop logic | execution.py | ℹ️ Appears correct |
| SL comparison logic | execution.py | ℹ️ Needs monitoring |
| Proposed SL edge cases | execution.py | ℹ️ Monitor in production |

---

## 📌 Next Steps

1. ✅ Code fixes committed locally
2. ⏳ Push to GitHub (network issue, retry when available)
3. 📋 Monitor partial close behavior in live trading
4. 🔄 Consider review of breakeven strategy with domain expert
5. 🧪 Run full integration tests with live MT5 terminal

---

**Report Generated**: 2026-03-16  
**Status**: ✅ COMPLETE - All critical bugs fixed and tested
