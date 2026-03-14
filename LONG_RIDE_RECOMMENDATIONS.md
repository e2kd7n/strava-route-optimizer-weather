# Long Ride Recommendations - Wind Analysis Feature

## Overview

The long ride recommendation component has been enhanced with sophisticated wind analysis that **prioritizes tailwinds in the second half of routes**. This is based on the cycling principle that it's better to fight headwinds when you're fresh and enjoy tailwinds when you're tired on the way back.

## Key Features

### 1. Enhanced Wind Scoring Algorithm

The new `calculate_wind_score()` method provides:

- **70% weight on second half wind conditions** (up from 60%)
- **30% weight on first half wind conditions** (down from 40%)
- **10% bonus** for routes with consistent strong tailwinds (>0.8 score) in the second half
- Detailed segment-by-segment wind analysis (up to 8 segments)

### 2. Wind Analysis Breakdown

For each route, the system analyzes:

- **Wind Type per Segment**: headwind, tailwind, quartering_headwind, quartering_tailwind
- **Relative Wind Angles**: Precise calculation of wind direction relative to travel direction
- **Segment Scores**: Individual scores for each route segment
- **Half-Route Averages**: Separate scores for first and second halves

### 3. Intelligent Recommendations

The system provides human-readable recommendations:

- ✅ **"Excellent! Headwind out, strong tailwind back - perfect for a long ride"** (score > 0.8 on return)
- 👍 **"Great tailwinds for the return journey"** (score > 0.8 on return, mixed first half)
- 🌬️ **"Favorable winds on the way back"** (score > 0.6 on return)
- ⚠️ **"Challenging headwinds on return - consider shorter route or different day"** (score < 0.4 on return)
- 🤷 **"Mixed wind conditions - manageable but not ideal"** (neutral conditions)
- 💨 **"Light winds - minimal impact on ride"** (wind speed < 10 km/h)

### 4. Detailed Wind Visualization

The `format_wind_analysis()` method provides:

```
Wind: 25.0 km/h from S (180°)
First half score: 1.00 | Second half score: 0.30
Challenging headwinds on return - consider shorter route or different day
Seg 1: Tailwind | Seg 2: Headwind
```

## Scoring System

### Wind Type Scores

- **Tailwind** (relative angle > 135°): 1.0 (excellent)
- **Quartering Tailwind** (90° < angle < 135°): 0.8 (good)
- **Quartering Headwind** (45° < angle < 90°): 0.5 (moderate)
- **Headwind** (angle < 45°): 0.3 (challenging)

### Combined Score Calculation

```python
combined_score = 0.3 * first_half_avg + 0.7 * second_half_avg

# Bonus for excellent second half
if second_half_avg > 0.8:
    combined_score = min(1.0, combined_score * 1.1)
```

## Example Results

From test output showing the preference for tailwinds in the second half:

### North Wind Scenario (20 km/h from 0°)

1. **North Loop Ride**: Score 0.869 ⭐
   - First half: 0.300 (headwind out)
   - Second half: 1.000 (tailwind back)
   - Recommendation: "Excellent! Headwind out, strong tailwind back"

2. **South Loop Ride**: Score 0.510
   - First half: 1.000 (tailwind out)
   - Second half: 0.300 (headwind back)
   - Recommendation: "Challenging headwinds on return"

Notice how the North Loop scores **significantly higher** (0.869 vs 0.510) because it has tailwinds on the return, even though both routes have the same wind conditions, just reversed.

## Integration with Recommendations

The enhanced wind analysis is automatically integrated into:

1. **Route Recommendations**: Sorted by wind score (primary) and distance (secondary)
2. **Route Descriptions**: Include wind score and recommendation text
3. **Precipitation Risk**: Assessed from current weather data
4. **RideRecommendation Objects**: Include full `wind_analysis` dictionary

## Usage Example

```python
from src.long_ride_analyzer import LongRideAnalyzer

# Initialize analyzer
analyzer = LongRideAnalyzer(activities, config)

# Extract long rides
long_rides = analyzer.extract_long_rides(long_ride_activities)

# Get recommendations for a location
recommendations = analyzer.get_ride_recommendations(
    long_rides,
    clicked_lat=41.9281,
    clicked_lon=-87.6298
)

# Access wind analysis
for rec in recommendations:
    print(f"Route: {rec.ride.name}")
    print(f"Wind Score: {rec.weather_score:.3f}")
    print(f"Description: {rec.route_description}")
    
    # Detailed wind analysis
    wind_info = analyzer.format_wind_analysis(rec.wind_analysis)
    print(wind_info)
```

## Benefits

1. **Better Route Selection**: Cyclists get routes optimized for current wind conditions
2. **Energy Management**: Fight headwinds when fresh, enjoy tailwinds when tired
3. **Realistic Expectations**: Clear communication about wind challenges
4. **Data-Driven Decisions**: Objective scoring helps choose the best route

## Technical Implementation

### Files Modified

- `src/long_ride_analyzer.py`: Enhanced wind scoring and analysis
  - `calculate_wind_score()`: Returns tuple of (score, analysis_dict)
  - `format_wind_analysis()`: Formats wind data for display
  - `_get_wind_recommendation()`: Generates human-readable recommendations
  - `get_ride_recommendations()`: Integrates wind analysis into recommendations

### New Test File

- `test_long_ride_recommendations.py`: Comprehensive test suite demonstrating the feature

## Future Enhancements

Potential improvements:

1. **Hourly Wind Forecasts**: Use forecast data to recommend optimal departure times
2. **Route Reversal Suggestions**: Automatically suggest riding a route in reverse if winds favor it
3. **Wind Speed Thresholds**: Adjust scoring based on absolute wind speed (light vs strong winds)
4. **Historical Wind Patterns**: Learn seasonal wind patterns for better long-term planning
5. **Interactive Visualization**: Show wind arrows along route on map

## Testing

Run the test suite:

```bash
python3 test_long_ride_recommendations.py
```

The test creates three loop routes (north, south, east) and tests them against five wind scenarios, demonstrating how the scoring prioritizes tailwinds in the second half.

---

**Made with Bob** - Enhancing cycling route recommendations with intelligent wind analysis