# Parallelism Configuration Guide

## Overview
The ride optimizer uses intelligent parallelism that automatically enables parallel processing only when beneficial, avoiding coordination overhead for small datasets.

## Automatic Thresholds (Built-in)

### 1. Route Similarity Matching (`match_unnamed_rides_to_groups`)
**Automatic behavior:**
- **< 10 unnamed rides**: Sequential processing (no overhead)
- **≥ 10 unnamed rides**: Parallel processing across CPU cores

**Why this threshold?**
- Process pool creation overhead: ~50-100ms
- Each route comparison: ~5-20ms
- Break-even point: ~10 comparisons
- With 817 long rides and ~100 unnamed rides, parallel processing saves significant time

### 2. Similar Named Groups Consolidation (`consolidate_similar_named_groups`)
**Current behavior:** Sequential (not parallelized yet)
**Reason:** Typically <100 named groups, sequential is faster

## Configuration Options

### Enable/Disable Features

Add to `config/config.yaml`:

```yaml
long_rides:
  # Core grouping (always fast, always enabled)
  enabled: true
  min_distance_km: 15
  
  # Expensive operations (disabled by default)
  match_unnamed_rides: false  # Enable if you have many unnamed rides
  consolidate_similar_routes: false  # Enable to merge route variations
  
  # Thresholds
  similarity_threshold_km: 0.05  # Strict: only merge nearly identical routes
  
  # Parallelism (automatic by default)
  parallel_threshold: 10  # Minimum items before using parallel processing
  max_workers: null  # null = use CPU count, or set specific number
```

### When to Enable Each Feature

#### `match_unnamed_rides: true`
**Enable when:**
- You have >50 rides with generic names ("Morning Ride", etc.)
- You want to consolidate unnamed rides with named routes
- You have CPU cores available

**Cost:** O(n*m) comparisons where n=unnamed rides, m=named groups
- 100 unnamed × 500 named = 50,000 comparisons
- With parallelism: ~5-10 seconds
- Without parallelism: ~30-60 seconds

#### `consolidate_similar_routes: true`
**Enable when:**
- You have many route variations with different names
- Example: "Old School", "Old School / Lake Bluff", "Old School / Lagoon"
- You want to see total usage across all variations

**Cost:** O(n²) comparisons where n=named groups
- 500 named groups = 125,000 comparisons
- Currently sequential: ~60-120 seconds
- **Recommendation:** Keep disabled unless specifically needed

**Warning:** Be careful with threshold - routes with different returns (Lake Bluff vs Lagoon) are different rides!

## Performance Characteristics

### Fast Operations (Always Enabled)
1. **Group by exact name**: O(n) - instant
2. **Consolidate named groups**: O(n) - instant
3. **Generate fallback names**: O(n) - instant

### Expensive Operations (Disabled by Default)
1. **Match unnamed rides**: O(n*m) - seconds to minutes
2. **Consolidate similar routes**: O(n²) - seconds to minutes

## Recommended Configurations

### Default (Fast, Most Users)
```yaml
long_rides:
  enabled: true
  match_unnamed_rides: false
  consolidate_similar_routes: false
```
**Result:** Instant grouping by exact name, proper `uses` counts

### Power User (More Consolidation)
```yaml
long_rides:
  enabled: true
  match_unnamed_rides: true  # Match unnamed rides
  consolidate_similar_routes: false  # Keep route variations separate
  parallel_threshold: 10
  max_workers: null  # Use all CPU cores
```
**Result:** Unnamed rides matched to groups, still fast with parallelism

### Aggressive Consolidation (Use with Caution)
```yaml
long_rides:
  enabled: true
  match_unnamed_rides: true
  consolidate_similar_routes: true
  similarity_threshold_km: 0.05  # Very strict - only nearly identical
  parallel_threshold: 10
```
**Result:** Maximum consolidation, but may merge routes that should be separate

## Monitoring Performance

Check the logs to see what's happening:
```bash
tail -f logs/debug.log | grep "long rides"
```

You'll see:
- "Grouped X long rides into Y named groups" (instant)
- "Using parallel processing to match X unnamed rides..." (if enabled)
- "Consolidating X named groups into Y groups" (if enabled)
- "Step 5 completed in X.XXs" (total time)

## Troubleshooting

### Analysis is slow
1. Check if `match_unnamed_rides: true` - disable if not needed
2. Check if `consolidate_similar_routes: true` - disable if not needed
3. Reduce `parallel_threshold` if you have many CPU cores

### Not enough consolidation
1. Enable `match_unnamed_rides: true` for unnamed rides
2. Increase `similarity_threshold_km` (carefully!)
3. Check that rides actually have the same name

### Too much consolidation
1. Disable `consolidate_similar_routes`
2. Decrease `similarity_threshold_km` to be more strict
3. Ensure route names are descriptive and different

## Technical Details

### Parallel Processing Implementation
- Uses `ProcessPoolExecutor` (not threads) for CPU-bound work
- Each worker process handles route comparisons independently
- No shared state between workers (no coordination overhead)
- Results collected asynchronously with `as_completed()`

### Why Process Pool vs Thread Pool?
- Route similarity calculations are CPU-intensive (Fréchet distance, Hausdorff distance)
- Python GIL prevents true parallelism with threads
- Process pool bypasses GIL, uses all CPU cores
- Overhead is acceptable for >10 comparisons

### Automatic Threshold Logic
```python
if use_parallel and len(activities_data) > parallel_threshold:
    # Use parallel processing
else:
    # Use sequential processing
```

This ensures you never pay coordination overhead for small datasets.