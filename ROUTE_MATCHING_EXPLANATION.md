# Route Matching Logic Explanation

## Overview
The route matching algorithm uses **Hausdorff distance** to determine if two routes are similar enough to be grouped together.

## Key Parameters

### Similarity Threshold
- **Config value**: `route_analysis.similarity_threshold: 0.70`
- **Meaning**: Routes must have a similarity score ≥ 0.70 to be grouped together

### Distance Threshold
- **Hard-coded value**: `200 meters` (line 191 in route_analyzer.py)
- **Meaning**: Maximum acceptable deviation at ANY single point along the route

## How It Works

### 1. Hausdorff Distance Calculation
The algorithm calculates the **maximum deviation** between two routes:
- Compares every point on Route A to the closest point on Route B
- Compares every point on Route B to the closest point on Route A
- Takes the **maximum** of these two values

This means: **If ANY single point on either route deviates by more than ~200m, the routes are considered different.**

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

**Answer: Just ONE point!**

The Hausdorff distance uses the **maximum** deviation across all points. If even a **single point** on the route deviates by more than ~86 meters (with current threshold of 0.70), the routes will be considered different and placed in separate groups.

## Examples

### Example 1: Routes Grouped Together
- Route A and Route B follow the same path
- At one point, Route B deviates 50m to stop at a coffee shop
- Maximum deviation: 50m
- Similarity score: 1 / (1 + 50/200) = 0.80 ✅ **Grouped**

### Example 2: Routes Separated
- Route A and Route B follow the same path
- At one point, Route B takes a different street 100m away
- Maximum deviation: 100m
- Similarity score: 1 / (1 + 100/200) = 0.67 ❌ **Separate groups**

## Adjusting Sensitivity

To allow more variation (group more routes together):
- **Increase** `similarity_threshold` (e.g., 0.60 → allows ~133m deviation)
- **Increase** `distance_threshold` in code (e.g., 300m → allows more deviation)

To require stricter matching (create more unique routes):
- **Decrease** `similarity_threshold` (e.g., 0.80 → allows only ~50m deviation)
- **Decrease** `distance_threshold` in code (e.g., 100m → requires tighter matching)

## Current Configuration Analysis

With `similarity_threshold: 0.70`:
- **Maximum allowed deviation**: ~86 meters at any single point
- **Practical meaning**: Routes must stay within ~86m of each other along the entire path
- **Use case**: Good for distinguishing between:
  - Different streets (usually >100m apart)
  - Same street with minor detours (coffee shops, bike lane vs road)
  
This is **stricter** than the 200m mentioned in the config comment, which appears to be the hard-coded distance threshold used in the similarity calculation formula, not the actual maximum deviation allowed by the 0.70 threshold.

## Recommendation

If you want routes to be grouped when they deviate up to 200m at any point:
- Change `similarity_threshold` to approximately **0.50**
- This would allow: 1 / (1 + 200/200) = 0.50

Current formula: `similarity = 1 / (1 + deviation / 200)`
- 0.70 threshold → ~86m max deviation
- 0.60 threshold → ~133m max deviation  
- 0.50 threshold → ~200m max deviation
- 0.40 threshold → ~300m max deviation