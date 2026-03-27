# Route Matching Logic Explanation

## Overview
The route matching algorithm uses **Fréchet distance** (primary) with **percentile-based Hausdorff distance** (secondary validation) to determine if two routes are similar enough to be grouped together.

## Algorithm Evolution

### Current Implementation (v2.0 - Percentile-Based)
**As of 2026-03-26**: The algorithm now uses **95th percentile deviation** instead of maximum deviation, making it robust to GPS glitches and brief detours while still catching substantive route differences.

### Previous Implementation (v1.0 - Maximum Deviation)
Previously used maximum deviation at ANY single point, which was too strict and caused over-clustering.

## Key Parameters

### Similarity Threshold
- **Config value**: `route_analysis.similarity_threshold: 0.70`
- **Meaning**: Routes must have a similarity score ≥ 0.70 to be grouped together

### Outlier Tolerance Percentile
- **Config value**: `route_analysis.outlier_tolerance_percentile: 95.0`
- **Meaning**: Ignore the worst 5% of point deviations when calculating similarity
- **Effect**: Tolerates GPS glitches and brief detours without creating false unique routes

### Distance Threshold
- **Hard-coded value**: `200 meters` (in route_analyzer.py)
- **Meaning**: Reference distance for similarity score calculation

## How It Works

### 1. Percentile-Based Hausdorff Distance Calculation
The algorithm calculates the **95th percentile deviation** between two routes:
- Compares every point on Route A to the closest point on Route B
- Compares every point on Route B to the closest point on Route A
- Takes the **95th percentile** (not maximum) of these deviations
- This allows 5% of points to be outliers without affecting the similarity score

**Key Improvement**: GPS glitches, brief detours, or single-point deviations no longer create false unique routes.

### 2. Similarity Score Formula
```python
normalized_dist = max_dist * 111000  # Convert degrees to meters
similarity = 1 / (1 + normalized_dist / 200)  # 200m threshold
```

### 3. Threshold Interpretation

With `similarity_threshold = 0.70`:
```
similarity = 1 / (1 + normalized_dist / 200) ≥ 0.70
```

Solving for normalized_dist:
```
0.70 = 1 / (1 + normalized_dist / 200)
1 + normalized_dist / 200 = 1 / 0.70
1 + normalized_dist / 200 = 1.43
normalized_dist / 200 = 0.43
normalized_dist = 86 meters
```

**Current Setting**: Routes are grouped if their maximum deviation is ≤ **86 meters** at any point.

## Answer to Your Question

> "How many points on the route can vary by that amount before a unique route is determined?"

**Answer (v2.0 - Percentile-Based): Up to 5% of points!**

With the 95th percentile approach:
- **Up to 5% of points** can deviate by any amount (GPS glitches, detours)
- The remaining **95% of points** must stay within ~86 meters (with threshold 0.70)
- This makes the algorithm robust to outliers while still catching real route differences

**Previous Answer (v1.0 - Maximum): Just ONE point!**
The old algorithm used maximum deviation, so a single outlier point would separate routes.

## Examples

### Example 1: Routes Grouped Together (GPS Glitch Tolerated)
- Route A and Route B follow the same path
- Route B has a GPS glitch at one point (150m deviation) - represents 2% of points
- 95th percentile deviation: ~20m
- Similarity score: 1 / (1 + 20/200) = 0.91 ✅ **Grouped**
- **Old algorithm would have separated these** (max deviation 150m)

### Example 2: Routes Grouped Together (Brief Detour)
- Route A and Route B follow the same path
- Route B stops at coffee shop (50m detour for 3% of route)
- 95th percentile deviation: ~25m
- Similarity score: 1 / (1 + 25/200) = 0.89 ✅ **Grouped**

### Example 3: Routes Separated (Substantive Difference)
- Route A takes Main Street
- Route B takes parallel Oak Street (100m away for 30% of route)
- 95th percentile deviation: ~95m
- Similarity score: 1 / (1 + 95/200) = 0.68 ❌ **Separate groups**

## Adjusting Sensitivity

### Similarity Threshold
To allow more variation (group more routes together):
- **Decrease** `similarity_threshold` (e.g., 0.60 → allows ~133m 95th percentile deviation)
- **Increase** `distance_threshold` in code (e.g., 300m → allows more deviation)

To require stricter matching (create more unique routes):
- **Increase** `similarity_threshold` (e.g., 0.80 → allows only ~50m 95th percentile deviation)
- **Decrease** `distance_threshold` in code (e.g., 100m → requires tighter matching)

### Outlier Tolerance
To tolerate more outliers:
- **Increase** `outlier_tolerance_percentile` (e.g., 99.0 → ignore worst 1% of points)
- More forgiving of GPS glitches and detours

To be more sensitive to outliers:
- **Decrease** `outlier_tolerance_percentile` (e.g., 90.0 → ignore worst 10% of points)
- Stricter matching, but still more robust than old maximum-based approach

## Current Configuration Analysis

With `similarity_threshold: 0.70` and `outlier_tolerance_percentile: 95.0`:
- **95th percentile allowed deviation**: ~86 meters
- **Outlier tolerance**: Up to 5% of points can deviate by any amount
- **Practical meaning**: 95% of route points must stay within ~86m of each other
- **Use case**: Excellent for:
  - Tolerating GPS glitches (typically <5% of points)
  - Allowing brief detours (coffee shops, construction avoidance)
  - Still distinguishing between different streets (>100m apart for >5% of route)

## Threshold Reference Table

Current formula: `similarity = 1 / (1 + percentile_deviation / 200)`

| Similarity Threshold | 95th Percentile Deviation | Use Case |
|---------------------|---------------------------|----------|
| 0.80 | ~50m | Very strict - only minor GPS variations |
| 0.70 | ~86m | **Current** - Good balance |
| 0.60 | ~133m | More forgiving - groups similar routes |
| 0.50 | ~200m | Very forgiving - may group different routes |

## Algorithm Comparison

### Old Algorithm (v1.0 - Maximum Deviation)
- ❌ Single GPS glitch → separate routes
- ❌ Brief detour → separate routes
- ✅ Clear separation of different streets

### New Algorithm (v2.0 - 95th Percentile)
- ✅ Single GPS glitch → same route (if <5% of points)
- ✅ Brief detour → same route (if <5% of points)
- ✅ Clear separation of different streets (if >5% of points differ)
- ✅ Configurable outlier tolerance

## Recommendation

Current settings (`similarity_threshold: 0.70`, `outlier_tolerance_percentile: 95.0`) provide an excellent balance:
- Robust to GPS noise and brief detours
- Still distinguishes between substantively different routes
- Configurable for different use cases

If you experience:
- **Too many route groups** (over-clustering): Decrease `similarity_threshold` to 0.60
- **Routes incorrectly grouped**: Increase `similarity_threshold` to 0.80
- **Too sensitive to GPS glitches**: Increase `outlier_tolerance_percentile` to 97.0 or 99.0