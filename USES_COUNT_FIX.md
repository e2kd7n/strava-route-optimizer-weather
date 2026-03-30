# Fix: "uses" Field in Long Ride Recommendations

## Issue
The "uses" field in long ride recommendations was always showing a value of 1, even when the same route had been ridden multiple times.

## Root Cause
The issue was in `main.py` in the `_analyze_long_rides()` function. It was calling `extract_long_rides()` which creates individual `LongRide` objects with the default `uses=1` value.

The correct workflow that properly calculates the `uses` count was not being used:
1. `group_rides_by_name()` - Groups activities by their Strava activity names
2. `consolidate_named_groups()` - Creates one `LongRide` per group with `uses=len(activities)`

## Changes Made

### 1. Updated `main.py` - `_analyze_long_rides()` function (lines 383-428)
**Before:**
```python
# Extract long rides
if long_ride_activities:
    long_rides = long_ride_analyzer.extract_long_rides(long_ride_activities)
    logger.info(f"Extracted {len(long_rides)} long rides for analysis")
```

**After:**
```python
# Group and consolidate rides by name
if long_ride_activities:
    # Group rides by their Strava activity names
    name_groups, unnamed_rides = long_ride_analyzer.group_rides_by_name(long_ride_activities)
    
    # Consolidate named groups (this properly sets uses count)
    long_rides = long_ride_analyzer.consolidate_named_groups(name_groups)
    logger.info(f"Consolidated into {len(long_rides)} unique named routes")
    
    # Try to match unnamed rides to existing groups
    if unnamed_rides:
        updated_groups, still_unnamed = long_ride_analyzer.match_unnamed_rides_to_groups(
            unnamed_rides, name_groups
        )
        
        # Re-consolidate with matched rides
        long_rides = long_ride_analyzer.consolidate_named_groups(updated_groups)
        
        # Generate fallback names for remaining unnamed rides
        if still_unnamed:
            fallback_groups = long_ride_analyzer.generate_fallback_names(still_unnamed)
            fallback_rides = long_ride_analyzer.consolidate_named_groups(fallback_groups)
            long_rides.extend(fallback_rides)
```

### 2. Updated `src/api/long_rides_api.py` - Added `uses` field to API response (line 127)
**Before:**
```python
recommendations.append({
    'activity_id': ride.activity_id,
    'name': ride.name,
    'distance_km': ride.distance_km,
    'duration_hours': ride.duration_hours,
    'elevation_gain': ride.elevation_gain,
    'average_speed': ride.average_speed,
    'is_loop': ride.is_loop,
    'start_location': ride.start_location,
    'distance_to_location': ride.distance_to_location,
    'coordinates': ride.coordinates
})
```

**After:**
```python
recommendations.append({
    'activity_id': ride.activity_id,
    'name': ride.name,
    'distance_km': ride.distance_km,
    'duration_hours': ride.duration_hours,
    'elevation_gain': ride.elevation_gain,
    'average_speed': ride.average_speed,
    'is_loop': ride.is_loop,
    'start_location': ride.start_location,
    'distance_to_location': ride.distance_to_location,
    'coordinates': ride.coordinates,
    'uses': ride.uses
})
```

## How It Works Now

1. **Grouping by Name**: Activities with the same Strava name are grouped together
   - Example: Three rides named "Lake Loop" → one group with 3 activities

2. **Consolidation**: Each group is consolidated into a single `LongRide` object
   - The most recent activity is used as the representative
   - `uses` is set to the number of activities in the group
   - Example: "Lake Loop" group with 3 activities → `LongRide` with `uses=3`

3. **Unnamed Rides**: Rides without specific names are:
   - First matched to existing named groups using route similarity
   - If no match, given fallback names like "Loop Ride (50.0km)"

4. **API Response**: The `uses` field is now included in the API response

## Testing

A test script was created at `scripts/test_uses_count.py` that verifies:
- Routes with multiple rides show `uses > 1`
- Routes ridden once show `uses = 1`
- The consolidation process works correctly

Test results:
```
✅ Lake Loop: uses=3, distance=50.0km
✅ River Trail: uses=2, distance=60.0km
✅ Mountain Climb: uses=1, distance=75.0km
```

## Benefits

1. **Better Route Recommendations**: Users can now see which routes they've ridden multiple times
2. **Route Popularity**: The `uses` count indicates favorite or frequently-used routes
3. **Data Accuracy**: The system now properly consolidates duplicate routes instead of showing them separately
4. **Reduced Clutter**: Instead of showing 10 individual rides of the same route, it shows 1 route with `uses=10`

## Impact

- Users will now see accurate usage counts in the long rides recommendations
- The interactive map will show consolidated routes with proper usage statistics
- The API will return the `uses` field for client applications to display