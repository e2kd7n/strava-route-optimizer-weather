# Epic: Segment-Based Route Naming with Connection Streets

## Epic Description

Improve route naming to show the complete journey: connection streets from origin/destination + main route + connection streets. Current implementation only shows the main street/path and misses important context about how riders get to/from that main route.

**Current Problem:**
- Route names like "Via Lakefront Trail" don't show connection streets
- Only samples 5 points, missing street transitions
- Doesn't identify route segments (start → middle → end)

**Desired Outcome:**
- Route names like "Wells St → Lakefront Trail → North Ave"
- Shows connection streets at start and end
- Identifies main route used for majority of journey

**Priority:** P2-medium  
**Epic Label:** epic  
**Estimated Total Time:** 4-5 hours

---

## Sub-Issues

### Issue 1: Increase Route Sampling Density

**Title:** Increase route sampling density to capture street transitions

**Description:**
Update `_get_strategic_sample_points()` to sample 10-12 points instead of 5 to better capture street transitions and route structure.

**Current Behavior:**
- Samples only 5 points: start, end, 25%, 50%, 75%
- Misses street transitions and connection streets

**Proposed Changes:**
- Sample first 3 points (capture start street)
- Sample at 20%, 40%, 60%, 80% (capture middle transitions)
- Sample last 3 points (capture end street)
- Total: 10-12 points

**Implementation:**
```python
def _get_strategic_sample_points(self, coordinates):
    """
    Sample points to capture route structure.
    Returns ~10 points including start, transitions, and end.
    """
    if len(coordinates) < 10:
        return coordinates
    
    points = []
    
    # First 3 points (start street)
    points.extend(coordinates[:3])
    
    # Middle points at key percentages
    for pct in [0.2, 0.4, 0.6, 0.8]:
        idx = int(len(coordinates) * pct)
        points.append(coordinates[idx])
    
    # Last 3 points (end street)
    points.extend(coordinates[-3:])
    
    return points
```

**Files to Modify:**
- `src/route_namer.py` - `_get_strategic_sample_points()` method

**Testing:**
- Run `test_route_naming.py` to verify 10+ points sampled
- Check that start and end streets are captured

**Estimated Time:** 30 minutes  
**Priority:** P2-medium  
**Labels:** enhancement, route-naming

---

### Issue 2: Implement Route Segment Identification

**Title:** Add route segment identification to detect street transitions

**Description:**
Create new method to identify distinct route segments by detecting where street names change along the route.

**Current Behavior:**
- No segment detection
- Treats entire route as single entity

**Proposed Implementation:**
```python
def _identify_route_segments(self, coordinates: List[Tuple[float, float]]) -> List[Dict]:
    """
    Identify distinct route segments based on street changes.
    
    Returns list of segments with:
    - street: Street name
    - length_pct: Percentage of route on this street
    - position: 'start', 'middle', or 'end'
    - sample_points: Number of sample points on this street
    """
    sample_points = self._get_strategic_sample_points(coordinates)
    
    segments = []
    current_street = None
    current_segment = None
    
    for i, point in enumerate(sample_points):
        location_info = self._get_location_details(point)
        street = location_info.get('street') if location_info else None
        
        if street != current_street:
            # Street changed - start new segment
            if current_segment:
                segments.append(current_segment)
            
            current_street = street
            current_segment = {
                'street': street,
                'start_idx': i,
                'sample_points': 1
            }
        else:
            # Same street - extend current segment
            if current_segment:
                current_segment['sample_points'] += 1
    
    # Add final segment
    if current_segment:
        segments.append(current_segment)
    
    # Calculate percentages and positions
    total_points = len(sample_points)
    for i, segment in enumerate(segments):
        segment['length_pct'] = (segment['sample_points'] / total_points) * 100
        
        if i == 0:
            segment['position'] = 'start'
        elif i == len(segments) - 1:
            segment['position'] = 'end'
        else:
            segment['position'] = 'middle'
    
    return segments
```

**Files to Modify:**
- `src/route_namer.py` - Add new `_identify_route_segments()` method

**Testing:**
- Test with route that has 3 distinct streets
- Verify segment lengths calculated correctly
- Check position classification (start/middle/end)

**Estimated Time:** 1-2 hours  
**Priority:** P2-medium  
**Labels:** enhancement, route-naming

---

### Issue 3: Implement Segment-Based Name Generation

**Title:** Generate route names showing connection streets and main route

**Description:**
Update `_generate_descriptive_name()` to use segment information and generate names in format: "Start St → Main St → End St"

**Current Behavior:**
- Names like "Via Lakefront Trail" (missing connections)
- Doesn't show route structure

**Proposed Naming Strategies:**

**Strategy 1: Full Path (3+ segments)**
```python
if len(segments) >= 3:
    # Show start → main → end
    start = segments[0]['street']
    main = max(segments[1:-1], key=lambda s: s['length_pct'])['street']
    end = segments[-1]['street']
    return f"{start} → {main} → {end}"
```

**Strategy 2: Main Route with Connection (2 segments)**
```python
if len(segments) == 2:
    main = max(segments, key=lambda s: s['length_pct'])
    connection = min(segments, key=lambda s: s['length_pct'])
    
    if main['length_pct'] > 60:
        return f"{main['street']} via {connection['street']}"
    else:
        return f"{segments[0]['street']} → {segments[1]['street']}"
```

**Strategy 3: Single Dominant Route**
```python
if len(segments) == 1 or segments[0]['length_pct'] > 80:
    return f"Via {segments[0]['street']}"
```

**Implementation:**
```python
def _generate_descriptive_name(self, route_info: Dict, route_id: str, direction: str) -> str:
    """
    Generate descriptive name from route segments.
    
    Priority:
    1. Full path (3+ segments): "Start → Main → End"
    2. Main + connection (2 segments): "Main via Connection"
    3. Single route: "Via Main"
    4. Fallback: Generic name
    """
    segments = route_info.get('segments', [])
    
    if not segments:
        # Fallback to old logic
        return self._generate_descriptive_name_legacy(route_info, route_id, direction)
    
    # Filter out segments that are too short (<10%)
    significant_segments = [s for s in segments if s['length_pct'] >= 10]
    
    if len(significant_segments) >= 3:
        # Strategy 1: Full path
        start = significant_segments[0]['street']
        main = max(significant_segments[1:-1], key=lambda s: s['length_pct'])['street']
        end = significant_segments[-1]['street']
        return f"{start} → {main} → {end}"
    
    elif len(significant_segments) == 2:
        # Strategy 2: Main + connection
        main = max(significant_segments, key=lambda s: s['length_pct'])
        connection = min(significant_segments, key=lambda s: s['length_pct'])
        
        if main['length_pct'] > 60:
            return f"{main['street']} via {connection['street']}"
        else:
            return f"{significant_segments[0]['street']} → {significant_segments[1]['street']}"
    
    elif len(significant_segments) == 1:
        # Strategy 3: Single route
        return f"Via {significant_segments[0]['street']}"
    
    # Fallback
    direction_label = "to Work" if direction == "home_to_work" else "to Home"
    route_num = route_id.split('_')[-1]
    return f"Route {route_num} {direction_label}"
```

**Files to Modify:**
- `src/route_namer.py` - Update `_generate_descriptive_name()` method
- `src/route_namer.py` - Rename old method to `_generate_descriptive_name_legacy()`

**Testing:**
- Test with 3-segment route → expect "Start → Main → End"
- Test with 2-segment route → expect "Main via Connection"
- Test with 1-segment route → expect "Via Main"
- Test with no segments → expect fallback name

**Estimated Time:** 1 hour  
**Priority:** P2-medium  
**Labels:** enhancement, route-naming

---

### Issue 4: Update Route Analysis Integration

**Title:** Integrate segment-based naming into route analysis workflow

**Description:**
Update `_analyze_route_geography()` to call segment identification and pass segment info to name generation.

**Current Behavior:**
- Analyzes geography but doesn't identify segments
- Passes generic route_info to name generation

**Proposed Changes:**
```python
def _analyze_route_geography(self, coordinates: List[Tuple[float, float]]) -> Dict:
    """
    Analyze route geography including segment identification.
    """
    if not coordinates:
        return {}
    
    # Identify route segments (NEW)
    segments = self._identify_route_segments(coordinates)
    
    # Get strategic sample points
    sample_points = self._get_strategic_sample_points(coordinates)
    
    # Collect geographic information (existing logic)
    streets = []
    neighborhoods = set()
    landmarks = []
    features = []
    
    for point in sample_points:
        location_info = self._get_location_details(point)
        # ... existing collection logic ...
    
    return {
        'segments': segments,  # NEW
        'major_streets': self._filter_significant_streets(streets),
        'neighborhoods': list(neighborhoods),
        'landmarks': landmarks[:2],
        'geographic_features': features[:1]
    }
```

**Files to Modify:**
- `src/route_namer.py` - Update `_analyze_route_geography()` method

**Testing:**
- Verify segments are included in route_info
- Check that name generation receives segment data
- Test end-to-end route naming

**Estimated Time:** 30 minutes  
**Priority:** P2-medium  
**Labels:** enhancement, route-naming

---

### Issue 5: Add Configuration Options for Route Naming

**Title:** Add configuration options for segment-based route naming

**Description:**
Add configuration parameters to control route naming behavior.

**Configuration Options:**
```yaml
route_naming:
  sampling_density: 10  # Number of points to sample along route
  min_segment_length_pct: 10  # Minimum % to be considered significant segment
  show_full_path: true  # Show start → middle → end format
  max_segments_in_name: 3  # Maximum segments to include in name
  enable_segment_naming: true  # Feature flag to enable/disable
```

**Implementation:**
- Add config section to `config/config.yaml`
- Update RouteNamer to read config values
- Use config values in segment identification and naming

**Files to Modify:**
- `config/config.yaml` - Add route_naming section
- `src/route_namer.py` - Read and use config values

**Testing:**
- Test with different sampling_density values
- Test with min_segment_length_pct variations
- Test with enable_segment_naming=false (fallback to old logic)

**Estimated Time:** 30 minutes  
**Priority:** P2-medium  
**Labels:** enhancement, configuration, route-naming

---

### Issue 6: Clear Geocoding Cache and Test with Real Data

**Title:** Clear geocoding cache and validate segment-based naming with real routes

**Description:**
After implementing segment-based naming, clear the geocoding cache to force re-analysis with new logic and validate results with real route data.

**Tasks:**
1. Clear `cache/geocoding_cache.json`
2. Run full analysis with real Strava data
3. Review generated route names
4. Verify names show connection streets + main route
5. Check for edge cases (single street, no geocoding, etc.)

**Validation Criteria:**
- ✅ Route names show connection streets from origin/destination
- ✅ Route names show main street/path for majority of route
- ✅ Format is clear: "Start → Main → End"
- ✅ Handles edge cases gracefully
- ✅ No excessive API calls (uses cache)

**Expected Results:**
- Before: "Via Lakefront Trail"
- After: "Wells St → Lakefront Trail → North Ave"

**Files to Modify:**
- None (testing only)

**Commands:**
```bash
# Clear cache
rm cache/geocoding_cache.json

# Run analysis
python main.py --analyze --config config/config.yaml

# Review results in generated report
```

**Estimated Time:** 1 hour  
**Priority:** P2-medium  
**Labels:** testing, validation, route-naming

---

## Success Criteria

- [ ] Route names show connection streets from origin/destination
- [ ] Route names show main street/path used for majority of route
- [ ] Format is clear and consistent: "Start → Main → End"
- [ ] Handles edge cases (single street, no geocoding, API failures)
- [ ] No excessive API calls (effective caching)
- [ ] Backward compatible (existing routes still work)
- [ ] Configurable behavior via config.yaml

## Related Issues

- Supersedes #51 - Significantly Improve Route Naming Mechanism
- Related to #23 - Color code route names (can be done after this epic)

## Timeline

**Total Estimated Time:** 4-5 hours
- Issue 1: 30 minutes
- Issue 2: 1-2 hours
- Issue 3: 1 hour
- Issue 4: 30 minutes
- Issue 5: 30 minutes
- Issue 6: 1 hour

## Labels

- epic
- enhancement
- route-naming
- P2-medium