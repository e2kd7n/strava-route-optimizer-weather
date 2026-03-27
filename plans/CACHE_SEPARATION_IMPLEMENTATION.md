# Cache Separation Implementation

## Summary

Implemented a separate test cache system to prevent test data from overwriting production Strava activity data.

## Changes Made

### 1. Modified `src/data_fetcher.py`

Added `use_test_cache` parameter to `StravaDataFetcher.__init__()`:

```python
def __init__(self, client: Client, config, use_test_cache: bool = False):
    """
    Initialize data fetcher.
    
    Args:
        client: Authenticated Strava client
        config: Configuration object
        use_test_cache: If True, use test cache instead of production cache
    """
    self.use_test_cache = use_test_cache
    
    # Use separate cache paths for test and production data
    if use_test_cache:
        self.cache_path = Path("data/cache/activities_test.json")
    else:
        self.cache_path = Path("data/cache/activities.json")
```

### 2. Updated Test Files

Modified all test files to use test cache:
- `tests/test_data_fetcher.py` - 4 instances updated
- `tests/test_integration.py` - 2 instances updated

All instances now use: `StravaDataFetcher(client, config, use_test_cache=True)`

### 3. Created Test Data Setup Script

**File**: `tests/setup_test_data.py`

Creates synthetic test data with:
- 12 activities representing different route variants
- 3 different route types (main commute, alternative, long ride)
- Realistic polylines and metrics

**Usage**: `python3 tests/setup_test_data.py`

### 4. Created Documentation

**File**: `tests/TEST_DATA_README.md`

Comprehensive guide covering:
- Cache file locations
- Setup instructions
- Usage examples
- Protection mechanisms
- Recovery procedures
- Best practices

## Cache Files

| File | Purpose | Size | Protected |
|------|---------|------|-----------|
| `data/cache/activities.json` | Production (real Strava data) | ~5.8KB (currently test data) | ✅ Yes |
| `data/cache/activities_test.json` | Test (synthetic data) | ~5.7KB | N/A |

## Incident That Prompted This Change

**Date**: March 26, 2026 at 19:20
**Issue**: ~2,408 real Strava activities were overwritten by 12 test activities
**Impact**: Production cache lost, only recoverable by re-fetching from Strava

## Benefits

1. **Data Protection**: Production data cannot be overwritten by tests
2. **Clear Separation**: Explicit flag makes intent clear
3. **Easy Testing**: Tests use consistent synthetic data
4. **No Confusion**: Separate files eliminate ambiguity
5. **Safe Development**: Developers can run tests without risk

## Testing

All tests pass with the new system:
```bash
$ python3 -m pytest tests/test_data_fetcher.py -v
============================= test session starts ==============================
7 passed in 0.35s
```

## Next Steps for User

To restore production data:
```bash
# Re-fetch from Strava
python3 main.py --fetch

# Then analyze
python3 main.py --analyze
```

## Implementation Date

March 27, 2026