# Weather Analysis Guide

## Overview

The Strava Route Optimizer now includes real-time weather analysis to help you choose the most efficient commute route based on current wind conditions. This feature uses the free Open-Meteo API to fetch weather data and calculates the impact of wind on your cycling performance.

## How It Works

### 1. Weather Data Collection

The system fetches current weather conditions including:
- **Wind Speed**: Measured at 10m height in km/h
- **Wind Direction**: Direction wind is coming FROM (0-360°)
- **Wind Gusts**: Peak wind speeds
- **Temperature**: Current temperature in Celsius
- **Humidity**: Relative humidity percentage
- **Precipitation**: Current rainfall rate

Weather data is sampled at three points along each route (start, middle, end) and averaged for accuracy.

### 2. Wind Impact Calculation

For each route segment, the system calculates:

#### Headwind/Tailwind Component
- **Headwind** (positive value): Wind blowing against your direction of travel
- **Tailwind** (negative value): Wind blowing with your direction of travel
- Calculated using: `headwind = wind_speed × cos(relative_angle)`

#### Crosswind Component
- Wind blowing perpendicular to your direction
- Always treated as a penalty (slows you down)
- Calculated using: `crosswind = wind_speed × |sin(relative_angle)|`

### 3. Performance Impact

The system estimates time penalties based on cycling research:

- **Headwind**: ~1.5% slower per 1 km/h headwind
- **Tailwind**: ~1.0% faster per 1 km/h tailwind
- **Crosswind**: ~0.5% slower per 1 km/h crosswind

**Example**: A 20 km/h headwind on a 30-minute commute would add approximately 9 minutes to your ride time.

### 4. Weather Scoring

Routes receive a weather score (0-100):

- **Base Score**: 50 (neutral)
- **Tailwind Bonus**: Up to +40 points for strong tailwinds (20+ km/h)
- **Headwind Penalty**: Up to -40 points for strong headwinds (20+ km/h)
- **Crosswind Penalty**: Up to -10 points for strong crosswinds

**Wind Favorability Categories**:
- **Favorable**: Average headwind < -5 km/h (tailwind)
- **Neutral**: Average headwind between -5 and +5 km/h
- **Unfavorable**: Average headwind > +5 km/h

## Configuration

### Enable/Disable Weather Analysis

Edit `config/config.yaml`:

```yaml
optimization:
  weather_enabled: true  # Set to false to disable weather analysis
  weights:
    time: 0.35      # 35% weight on speed
    distance: 0.25  # 25% weight on distance
    safety: 0.25    # 25% weight on safety
    weather: 0.15   # 15% weight on weather conditions
```

### Adjust Weather Weight

Increase the weather weight if wind conditions are critical for your commute:

```yaml
optimization:
  weights:
    time: 0.30
    distance: 0.20
    safety: 0.20
    weather: 0.30  # 30% weight - prioritize wind conditions
```

## Understanding the Report

### Weather Information Display

The analysis report shows:

1. **Current Conditions**
   - Wind speed and direction
   - Temperature and humidity
   - Precipitation status

2. **Route-Specific Wind Analysis**
   - Average headwind/tailwind
   - Average crosswind
   - Maximum headwind encountered
   - Wind favorability rating
   - Estimated time impact

3. **Route Recommendations**
   - Routes are ranked considering weather
   - Recommendations include wind condition notes
   - Alternative routes suggested for different wind scenarios

### Example Output

```
Route: Lakefront Trail via Lincoln Park
Weather Score: 72/100 (Favorable)
Wind: 15 km/h from 270° (West)
Average Headwind: -8 km/h (tailwind)
Average Crosswind: 3 km/h
Estimated Time Benefit: -2.5 minutes (faster)
Recommendation: Favorable wind conditions
```

## Best Practices

### 1. Check Weather Before Commuting

Run the analysis just before your commute for the most accurate recommendations:

```bash
python main.py --analyze
```

### 2. Consider Time of Day

Wind patterns often change throughout the day:
- **Morning**: Often calmer winds
- **Afternoon**: Typically stronger winds
- **Evening**: Wind may shift direction

### 3. Route Selection Strategy

- **Strong Headwinds**: Choose the most direct route to minimize exposure
- **Strong Tailwinds**: Consider longer scenic routes to maximize benefit
- **Strong Crosswinds**: Prefer routes with wind protection (buildings, trees)

### 4. Seasonal Considerations

- **Spring**: Variable winds, check frequently
- **Summer**: Generally lighter winds
- **Fall**: Stronger, more consistent winds
- **Winter**: Most variable, highest impact

## Technical Details

### Data Source

- **API**: Open-Meteo (https://open-meteo.com)
- **Cost**: Free, no API key required
- **Update Frequency**: Real-time current conditions
- **Coverage**: Global

### Accuracy

- Wind measurements at 10m height (standard meteorological height)
- Data from multiple weather models combined
- Typical accuracy: ±2-3 km/h for wind speed, ±10° for direction

### Limitations

1. **Microclimate Effects**: Local terrain features may create wind patterns not captured by regional data
2. **Urban Canyons**: Wind can be channeled or blocked by buildings
3. **Elevation Changes**: Wind speed increases with elevation
4. **Forecast vs. Reality**: Conditions may change during your commute

## Troubleshooting

### Weather Data Not Available

If weather data fails to load:

1. **Check Internet Connection**: Weather API requires internet access
2. **API Timeout**: Increase timeout in `src/weather_fetcher.py`
3. **Disable Weather**: Set `weather_enabled: false` in config

### Inaccurate Wind Impact

If estimated time impacts seem off:

1. **Adjust Coefficients**: Modify penalty percentages in `WindImpactCalculator`
2. **Personal Factors**: Your fitness level and bike type affect wind impact
3. **Route Complexity**: Winding routes have more variable wind exposure

### Weather Score Seems Wrong

Check:
1. **Wind Direction**: Ensure your route coordinates are in correct order
2. **Bearing Calculation**: Verify route direction is calculated correctly
3. **Weight Settings**: Adjust weather weight if it's over/under-influencing results

## Advanced Usage

### Custom Weather Sources

To use a different weather API, modify `src/weather_fetcher.py`:

```python
class WeatherFetcher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "your_api_endpoint"
        # Implement your custom API calls
```

### Historical Weather Analysis

To analyze how weather affected past rides:

```python
from src.weather_fetcher import WindImpactCalculator

calculator = WindImpactCalculator()
for activity in activities:
    # Get historical weather for activity.timestamp
    # Calculate wind impact
    impact = calculator.analyze_route_wind_impact(
        activity.coordinates,
        historical_wind_speed,
        historical_wind_direction
    )
```

## Future Enhancements

Planned features:
- [ ] Hourly forecast integration for planning future commutes
- [ ] Historical weather correlation with ride performance
- [ ] Precipitation impact analysis
- [ ] Temperature comfort scoring
- [ ] Wind gust warnings
- [ ] Multi-day weather trends

## References

- [Open-Meteo API Documentation](https://open-meteo.com/en/docs)
- [Cycling Aerodynamics Research](https://www.cyclingpowerlab.com/WindEffect.aspx)
- [Wind Impact on Cycling Performance](https://www.trainingpeaks.com/blog/the-effect-of-wind-on-cycling-performance/)

---

**Note**: Weather analysis is a tool to help optimize your route selection. Always use your judgment and consider safety factors beyond wind conditions.

# Made with Bob