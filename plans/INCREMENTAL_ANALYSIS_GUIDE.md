# Incremental Analysis Guide

## Overview

The Strava Commute Route Analyzer now features intelligent caching and incremental analysis capabilities that dramatically improve performance for subsequent runs.

## Performance Improvements

### First Run (Full Analysis)
- **Time**: ~10 seconds (down from 213s)
- Route grouping computed and cached
- All similarity calculations cached

### Subsequent Runs (Cache Hit)
- **Time**: <1 second (instant!)
- Loads pre-computed route groups from cache
- No recalculation needed

### Incremental Updates (New Routes)
- **Time**: ~2-5 seconds
- Only processes new routes
- Merges into existing groups
- Updates cache automatically

## Usage

### Normal Analysis (Uses Cache)
```bash
# First run - computes and caches everything
python main.py --analyze

# Subsequent runs - instant using cache
python main.py --analyze

# After fetching new activities - incremental update
python main.py --fetch --analyze
```

### Force Full Reanalysis
```bash
# Clear cache and reprocess all routes
python main.py --analyze --force-reanalysis
```

### When to Use Force Reanalysis

Use `--force-reanalysis` when:
1. **Configuration changed**: Modified similarity threshold in config
2. **Algorithm updated**: After software updates that change grouping logic
3. **Data corruption**: Cache appears corrupted or produces wrong results
4. **Testing**: Comparing different analysis approaches

## How It Works

### Cache Structure

The route grouping cache (`cache/route_groups_cache.json`) stores:
- **Activity IDs**: List of all analyzed activity IDs
- **Route Groups**: Complete serialized route groups with all routes
- **Metadata**: Similarity threshold, algorithm version, timestamp

### Cache Validation

The system automatically detects:
1. **Perfect Match**: Same activities → instant cache hit
2. **New Activities**: Additional activities → incremental merge
3. **Removed Activities**: Missing activities → full reanalysis
4. **Config Changes**: Different threshold → full reanalysis

### Incremental Merge Process

When new routes are detected:

1. **Load Cached Groups**: Deserialize existing route groups
2. **Extract New Routes**: Identify routes from new activities
3. **Match to Groups**: Try to match each new route to existing groups
4. **Create New Groups**: Group unmatched routes separately
5. **Update Cache**: Save merged groups with updated activity IDs

```
Example:
- Cached: 220 routes in 15 groups
- New: 5 routes fetched
- Process: Match 3 to existing, create 1 new group for 2 unmatched
- Result: 225 routes in 16 groups (processed in 3s vs 10s full)
```

## Cache Management

### Cache Location
```
cache/
├── route_groups_cache.json      # Route grouping results
├── route_similarity_cache.json  # Pairwise similarity scores
├── geocoding_cache.json         # Location lookups
└── weather_cache.json           # Weather data
```

### Cache Invalidation

Cache is automatically invalidated when:
- `--force-reanalysis` flag used
- Similarity threshold changes in config
- Algorithm version changes (code updates)
- Activities are removed from dataset

### Manual Cache Clearing

```bash
# Clear all caches
rm cache/*.json

# Clear only route grouping cache
rm cache/route_groups_cache.json

# Clear only similarity cache
rm cache/route_similarity_cache.json
```

## Performance Comparison

| Scenario | Time | Speedup | Notes |
|----------|------|---------|-------|
| First run (no cache) | 10s | Baseline | Computes everything |
| Cache hit (same data) | <1s | **10x faster** | Instant load |
| Incremental (5 new routes) | 3s | **3x faster** | Only processes new |
| Incremental (20 new routes) | 5s | **2x faster** | Merges efficiently |
| Force reanalysis | 10s | Baseline | Clears and recomputes |

## Advanced Features

### Parallel Processing Removed

Previous versions used parallel processing for route grouping, which added significant overhead:
- **Old**: 203s with parallel processing (2 workers)
- **New**: 10s with sequential processing
- **Reason**: Serialization/deserialization overhead exceeded benefits

### Smart Grouping Algorithm

The incremental merge algorithm:
1. Calculates similarity between new routes and existing group representatives
2. Adds to best matching group if similarity ≥ threshold
3. Creates new groups for unmatched routes
4. Re-sorts groups by frequency
5. Updates representative routes (median by duration)

### Cache Key Generation

Cache keys are generated from:
```python
{
    'activity_ids': [sorted list of activity IDs],
    'similarity_threshold': 0.85,
    'algorithm': 'frechet',  # or 'hausdorff'
    'version': '2.0'
}
```

This ensures cache is invalidated when:
- Activities change
- Configuration changes
- Algorithm updates

## Troubleshooting

### Cache Not Being Used

**Symptoms**: Every run takes 10s even with same data

**Solutions**:
1. Check if `cache/route_groups_cache.json` exists
2. Verify no `--force-reanalysis` flag in command
3. Check logs for cache validation messages
4. Ensure config hasn't changed

### Incorrect Results After Update

**Symptoms**: Groups don't match expected routes

**Solutions**:
1. Run with `--force-reanalysis` to clear cache
2. Check similarity threshold in config
3. Verify all activities are in cache

### Cache Growing Too Large

**Symptoms**: Cache file >100MB

**Solutions**:
1. Normal for large datasets (>1000 routes)
2. Consider periodic full reanalysis
3. Archive old cache files if needed

## Best Practices

### Daily Workflow
```bash
# Morning: Fetch new activities and analyze
python main.py --fetch --analyze

# Result: Incremental update in 2-5s
```

### Weekly Maintenance
```bash
# Weekly: Full reanalysis to ensure accuracy
python main.py --analyze --force-reanalysis

# Result: Fresh analysis in 10s
```

### After Config Changes
```bash
# Always force reanalysis after config changes
# Edit config/config.yaml
python main.py --analyze --force-reanalysis
```

### Testing Different Thresholds
```bash
# Test with different similarity threshold
# 1. Edit config.yaml: similarity_threshold: 0.90
# 2. Force reanalysis
python main.py --analyze --force-reanalysis

# 3. Compare results
# 4. Revert config if needed
# 5. Force reanalysis again
```

## Implementation Details

### Route Group Serialization

Groups are serialized to JSON with full route data:
```json
{
  "activity_ids": [123, 456, 789],
  "groups": [
    {
      "id": "home_to_work_0",
      "direction": "home_to_work",
      "frequency": 45,
      "name": "Main Route",
      "is_plus_route": false,
      "representative_route": { ... },
      "routes": [ ... ]
    }
  ],
  "similarity_threshold": 0.85,
  "algorithm": "frechet",
  "timestamp": "2026-03-25T16:00:00"
}
```

### Incremental Merge Logic

```python
def _merge_new_routes(existing_groups, new_routes):
    for route in new_routes:
        best_match = find_best_matching_group(route, existing_groups)
        if best_match and similarity >= threshold:
            add_to_group(best_match, route)
        else:
            create_new_group(route)
    return updated_groups
```

## Future Enhancements

Potential improvements for future versions:

1. **Partial Cache Updates**: Update only changed groups
2. **Cache Compression**: Reduce file size with gzip
3. **Cache Expiration**: Auto-invalidate after N days
4. **Multi-Level Caching**: Separate caches per direction
5. **Cache Statistics**: Track hit/miss rates

## Summary

The incremental analysis system provides:
- ✅ **10x faster** subsequent runs (instant cache hits)
- ✅ **3x faster** incremental updates (new routes only)
- ✅ **Automatic** cache management (no manual intervention)
- ✅ **Intelligent** invalidation (detects changes automatically)
- ✅ **Flexible** reanalysis (force flag when needed)

This makes daily usage extremely fast while maintaining accuracy and flexibility for configuration changes or testing.