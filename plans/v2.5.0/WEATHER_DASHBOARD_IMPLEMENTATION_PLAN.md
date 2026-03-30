# Weather Dashboard Implementation Plan

**Issue:** #54 - Weather Dashboard Implementation (Epic)  
**Priority:** P1-high  
**Estimated Effort:** 16-20 hours  
**Target Release:** v2.4.0 or v2.5.0

---

## Overview

Create a comprehensive weather dashboard that provides cyclists with detailed weather information, forecasts, and recommendations for optimal riding conditions. This feature consolidates weather data that's currently scattered across different sections into a unified, actionable view.

## User Stories

1. **As a commuter**, I want to see today's weather at a glance to decide if I should bike to work
2. **As a planner**, I want to see the 7-day forecast to plan my week's commutes
3. **As a cyclist**, I want to understand how weather conditions affect my ride (wind, temperature, precipitation)
4. **As a data-driven user**, I want historical weather patterns to understand typical conditions
5. **As a mobile user**, I want quick access to weather info without scrolling through the entire report

## Requirements

### Functional Requirements

1. **Current Conditions Widget**
   - Temperature (feels like + actual)
   - Wind speed and direction (with compass)
   - Precipitation (current + next hour)
   - Humidity and visibility
   - UV index
   - Air quality index (if available)
   - Sunrise/sunset times
   - Weather icon/animation

2. **Hourly Forecast (Next 24 Hours)**
   - Temperature trend graph
   - Precipitation probability bars
   - Wind speed indicators
   - "Best time to ride" highlighting
   - Commute window overlays (morning/evening)

3. **7-Day Forecast**
   - Daily high/low temperatures
   - Precipitation chance
   - Wind conditions
   - Ride suitability score (Good/Fair/Poor)
   - Expandable details for each day

4. **Weather Alerts**
   - Severe weather warnings
   - Temperature extremes
   - High wind alerts
   - Heavy precipitation alerts
   - Air quality warnings

5. **Historical Patterns**
   - Average conditions for current month
   - Typical precipitation patterns
   - Wind rose diagram (prevailing wind directions)
   - Temperature trends

6. **Ride Recommendations**
   - Best days this week for cycling
   - Optimal departure times
   - Route recommendations based on wind
   - Gear suggestions (layers, rain gear, etc.)

### Non-Functional Requirements

1. **Performance**
   - Dashboard loads in <2 seconds
   - Weather data cached appropriately
   - Smooth animations and transitions

2. **Data Freshness**
   - Current conditions updated every 15 minutes
   - Forecasts updated every hour
   - Clear "last updated" timestamp

3. **Usability**
   - Intuitive layout with clear visual hierarchy
   - Color-coded severity indicators
   - Mobile-responsive design
   - Accessible to screen readers

4. **Reliability**
   - Graceful degradation if weather API fails
   - Cached data fallback
   - Clear error messages

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Report Template                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  New Tab: "Weather Dashboard"                          │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Current Conditions Card                         │ │ │
│  │  │  - Large temp display                            │ │ │
│  │  │  - Weather icon                                  │ │ │
│  │  │  - Key metrics grid                              │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Hourly Forecast Chart                           │ │ │
│  │  │  - Temperature line                              │ │ │
│  │  │  - Precipitation bars                            │ │ │
│  │  │  - Wind indicators                               │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  7-Day Forecast Cards                            │ │ │
│  │  │  [Day 1] [Day 2] [Day 3] [Day 4] [Day 5] ...    │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Ride Recommendations                            │ │ │
│  │  │  - Best days to ride                             │ │ │
│  │  │  - Optimal times                                 │ │ │
│  │  │  - Gear suggestions                              │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌──────────────────┐
│  WeatherFetcher  │ (existing)
│  - Open-Meteo API│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ WeatherDashboard │ (new Python class)
│  - Aggregate data│
│  - Calculate     │
│  - scores        │
│  - Generate      │
│  - recommendations│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Report Generator │
│  - Pass weather  │
│  - data to       │
│  - template      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Report Template  │
│  - Render        │
│  - dashboard     │
│  - with Chart.js │
└──────────────────┘
```

### New Python Module: `weather_dashboard.py`

```python
"""
Weather Dashboard Module

Aggregates and analyzes weather data for cyclist-friendly presentation.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from .weather_fetcher import WeatherFetcher
from .units import UnitConverter

logger = logging.getLogger(__name__)


@dataclass
class CurrentConditions:
    """Current weather conditions."""
    temperature: float
    feels_like: float
    wind_speed: float
    wind_direction: int  # degrees
    precipitation: float
    humidity: int  # percentage
    visibility: float  # km
    uv_index: float
    weather_code: int
    weather_description: str
    timestamp: datetime


@dataclass
class HourlyForecast:
    """Hourly weather forecast."""
    timestamp: datetime
    temperature: float
    precipitation_probability: int  # percentage
    precipitation_amount: float  # mm
    wind_speed: float
    wind_direction: int
    weather_code: int


@dataclass
class DailyForecast:
    """Daily weather forecast."""
    date: datetime
    temp_high: float
    temp_low: float
    precipitation_probability: int
    precipitation_amount: float
    wind_speed_max: float
    weather_code: int
    ride_suitability: str  # "excellent", "good", "fair", "poor", "avoid"
    ride_score: float  # 0-1


@dataclass
class WeatherAlert:
    """Weather alert/warning."""
    severity: str  # "info", "warning", "severe"
    title: str
    description: str
    start_time: datetime
    end_time: datetime


@dataclass
class RideRecommendation:
    """Cycling recommendation based on weather."""
    best_days: List[str]  # ["Monday", "Wednesday", ...]
    best_times_today: List[str]  # ["7:00 AM - 9:00 AM", ...]
    gear_suggestions: List[str]  # ["Light jacket", "Sunglasses", ...]
    route_preference: str  # "sheltered", "open", "any"
    overall_outlook: str  # Description of week's conditions


class WeatherDashboard:
    """Manages weather dashboard data and analysis."""
    
    def __init__(self, location: tuple, config):
        """
        Initialize weather dashboard.
        
        Args:
            location: (latitude, longitude) tuple
            config: Configuration object
        """
        self.location = location
        self.config = config
        self.weather_fetcher = WeatherFetcher()
        self.unit_converter = UnitConverter(config.get('units', 'metric'))
        
    def get_current_conditions(self) -> Optional[CurrentConditions]:
        """Fetch and format current weather conditions."""
        try:
            data = self.weather_fetcher.get_current_weather(
                self.location[0], 
                self.location[1]
            )
            
            return CurrentConditions(
                temperature=data['temperature'],
                feels_like=self._calculate_feels_like(
                    data['temperature'],
                    data['wind_speed'],
                    data['humidity']
                ),
                wind_speed=data['wind_speed'],
                wind_direction=data['wind_direction'],
                precipitation=data.get('precipitation', 0),
                humidity=data.get('humidity', 0),
                visibility=data.get('visibility', 10),
                uv_index=data.get('uv_index', 0),
                weather_code=data['weather_code'],
                weather_description=self._get_weather_description(data['weather_code']),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to fetch current conditions: {e}")
            return None
    
    def get_hourly_forecast(self, hours: int = 24) -> List[HourlyForecast]:
        """Get hourly forecast for next N hours."""
        try:
            data = self.weather_fetcher.get_forecast(
                self.location[0],
                self.location[1],
                days=2  # Need 2 days to cover 24 hours
            )
            
            forecasts = []
            for i in range(min(hours, len(data['hourly']))):
                hour_data = data['hourly'][i]
                forecasts.append(HourlyForecast(
                    timestamp=datetime.fromisoformat(hour_data['time']),
                    temperature=hour_data['temperature'],
                    precipitation_probability=hour_data.get('precipitation_probability', 0),
                    precipitation_amount=hour_data.get('precipitation', 0),
                    wind_speed=hour_data['wind_speed'],
                    wind_direction=hour_data['wind_direction'],
                    weather_code=hour_data['weather_code']
                ))
            
            return forecasts
        except Exception as e:
            logger.error(f"Failed to fetch hourly forecast: {e}")
            return []
    
    def get_daily_forecast(self, days: int = 7) -> List[DailyForecast]:
        """Get daily forecast for next N days."""
        try:
            data = self.weather_fetcher.get_forecast(
                self.location[0],
                self.location[1],
                days=days
            )
            
            forecasts = []
            for day_data in data['daily'][:days]:
                ride_score = self._calculate_ride_suitability_score(day_data)
                forecasts.append(DailyForecast(
                    date=datetime.fromisoformat(day_data['date']),
                    temp_high=day_data['temp_max'],
                    temp_low=day_data['temp_min'],
                    precipitation_probability=day_data.get('precipitation_probability', 0),
                    precipitation_amount=day_data.get('precipitation', 0),
                    wind_speed_max=day_data['wind_speed_max'],
                    weather_code=day_data['weather_code'],
                    ride_suitability=self._score_to_suitability(ride_score),
                    ride_score=ride_score
                ))
            
            return forecasts
        except Exception as e:
            logger.error(f"Failed to fetch daily forecast: {e}")
            return []
    
    def get_weather_alerts(self) -> List[WeatherAlert]:
        """Check for weather alerts and warnings."""
        alerts = []
        
        # Check current and forecast conditions for alerts
        current = self.get_current_conditions()
        if current:
            # Temperature extremes
            if current.temperature < 0:
                alerts.append(WeatherAlert(
                    severity="warning",
                    title="Freezing Temperatures",
                    description="Roads may be icy. Use caution.",
                    start_time=datetime.now(),
                    end_time=datetime.now() + timedelta(hours=12)
                ))
            elif current.temperature > 35:
                alerts.append(WeatherAlert(
                    severity="warning",
                    title="Extreme Heat",
                    description="Stay hydrated and take breaks.",
                    start_time=datetime.now(),
                    end_time=datetime.now() + timedelta(hours=12)
                ))
            
            # High winds
            if current.wind_speed > 40:  # km/h
                alerts.append(WeatherAlert(
                    severity="warning",
                    title="High Winds",
                    description=f"Wind speed {current.wind_speed:.0f} km/h. Cycling may be difficult.",
                    start_time=datetime.now(),
                    end_time=datetime.now() + timedelta(hours=6)
                ))
            
            # Heavy precipitation
            if current.precipitation > 5:  # mm/hour
                alerts.append(WeatherAlert(
                    severity="info",
                    title="Heavy Rain",
                    description="Roads may be wet. Reduce speed and increase following distance.",
                    start_time=datetime.now(),
                    end_time=datetime.now() + timedelta(hours=3)
                ))
        
        return alerts
    
    def get_ride_recommendations(self) -> RideRecommendation:
        """Generate cycling recommendations based on forecast."""
        daily_forecast = self.get_daily_forecast(7)
        hourly_forecast = self.get_hourly_forecast(24)
        
        # Find best days
        sorted_days = sorted(daily_forecast, key=lambda d: d.ride_score, reverse=True)
        best_days = [d.date.strftime("%A") for d in sorted_days[:3] if d.ride_score > 0.6]
        
        # Find best times today
        best_times = self._find_best_times_today(hourly_forecast)
        
        # Generate gear suggestions
        gear = self._suggest_gear(daily_forecast[0] if daily_forecast else None)
        
        # Route preference based on wind
        route_pref = self._determine_route_preference(daily_forecast)
        
        # Overall outlook
        outlook = self._generate_outlook(daily_forecast)
        
        return RideRecommendation(
            best_days=best_days,
            best_times_today=best_times,
            gear_suggestions=gear,
            route_preference=route_pref,
            overall_outlook=outlook
        )
    
    def _calculate_feels_like(self, temp: float, wind_speed: float, humidity: int) -> float:
        """Calculate feels-like temperature (wind chill or heat index)."""
        if temp < 10:  # Wind chill
            return 13.12 + 0.6215 * temp - 11.37 * (wind_speed ** 0.16) + 0.3965 * temp * (wind_speed ** 0.16)
        elif temp > 27:  # Heat index
            return -8.78 + 1.61 * temp + 2.34 * humidity - 0.14 * temp * humidity
        else:
            return temp
    
    def _calculate_ride_suitability_score(self, day_data: Dict) -> float:
        """Calculate 0-1 score for ride suitability."""
        score = 1.0
        
        # Temperature penalty
        temp_avg = (day_data['temp_max'] + day_data['temp_min']) / 2
        if temp_avg < 5 or temp_avg > 32:
            score *= 0.5
        elif temp_avg < 10 or temp_avg > 28:
            score *= 0.7
        
        # Precipitation penalty
        precip_prob = day_data.get('precipitation_probability', 0)
        if precip_prob > 70:
            score *= 0.3
        elif precip_prob > 40:
            score *= 0.6
        
        # Wind penalty
        wind = day_data['wind_speed_max']
        if wind > 40:
            score *= 0.4
        elif wind > 25:
            score *= 0.7
        
        return max(0.0, min(1.0, score))
    
    def _score_to_suitability(self, score: float) -> str:
        """Convert numeric score to text rating."""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        elif score >= 0.2:
            return "poor"
        else:
            return "avoid"
    
    def _find_best_times_today(self, hourly: List[HourlyForecast]) -> List[str]:
        """Find best time windows for cycling today."""
        # Score each hour
        scored_hours = []
        for hour in hourly[:12]:  # Next 12 hours
            score = 1.0
            
            # Precipitation penalty
            if hour.precipitation_probability > 50:
                score *= 0.5
            
            # Wind penalty
            if hour.wind_speed > 30:
                score *= 0.7
            
            # Temperature bonus for comfortable range
            if 15 <= hour.temperature <= 25:
                score *= 1.2
            
            scored_hours.append((hour.timestamp, score))
        
        # Find continuous good windows
        windows = []
        current_window = []
        
        for timestamp, score in scored_hours:
            if score > 0.6:
                current_window.append(timestamp)
            else:
                if len(current_window) >= 2:
                    windows.append((current_window[0], current_window[-1]))
                current_window = []
        
        if len(current_window) >= 2:
            windows.append((current_window[0], current_window[-1]))
        
        # Format windows
        return [f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}" 
                for start, end in windows[:3]]
    
    def _suggest_gear(self, today: Optional[DailyForecast]) -> List[str]:
        """Suggest appropriate cycling gear."""
        if not today:
            return []
        
        gear = []
        
        # Temperature-based
        if today.temp_low < 10:
            gear.append("Arm/leg warmers")
            gear.append("Gloves")
        if today.temp_high > 28:
            gear.append("Sunscreen")
            gear.append("Extra water")
        
        # Precipitation
        if today.precipitation_probability > 40:
            gear.append("Rain jacket")
            gear.append("Fenders")
        
        # Wind
        if today.wind_speed_max > 25:
            gear.append("Wind-resistant jacket")
        
        # Always recommend
        gear.append("Helmet")
        gear.append("Lights")
        
        return gear
    
    def _determine_route_preference(self, forecast: List[DailyForecast]) -> str:
        """Determine route preference based on conditions."""
        if not forecast:
            return "any"
        
        today = forecast[0]
        
        if today.wind_speed_max > 30:
            return "sheltered"
        elif today.precipitation_probability > 50:
            return "covered"
        else:
            return "any"
    
    def _generate_outlook(self, forecast: List[DailyForecast]) -> str:
        """Generate text description of week's outlook."""
        if not forecast:
            return "Weather data unavailable."
        
        good_days = sum(1 for d in forecast if d.ride_score > 0.6)
        avg_score = sum(d.ride_score for d in forecast) / len(forecast)
        
        if avg_score > 0.7:
            return f"Excellent week for cycling! {good_days} out of {len(forecast)} days have good conditions."
        elif avg_score > 0.5:
            return f"Decent week for cycling. {good_days} days look good, plan around the weather."
        else:
            return f"Challenging week ahead. Only {good_days} days have favorable conditions."
    
    def _get_weather_description(self, code: int) -> str:
        """Convert weather code to description."""
        # WMO Weather interpretation codes
        descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return descriptions.get(code, "Unknown")
```

### Template Integration

Add new tab to navigation:

```html
<ul class="nav nav-tabs" role="tablist">
    <li class="nav-item">
        <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#commute-routes">
            Commute Routes
        </button>
    </li>
    <li class="nav-item">
        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#weather-dashboard">
            Weather Dashboard
        </button>
    </li>
    <li class="nav-item">
        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#long-rides">
            Long Rides
        </button>
    </li>
</ul>
```

Weather Dashboard tab content with Chart.js visualizations for hourly forecast.

---

## Implementation Phases

### Phase 1: Backend Module (4-5 hours)
- Create `weather_dashboard.py`
- Implement data classes
- Implement scoring algorithms
- Add unit tests

### Phase 2: Current Conditions Widget (2-3 hours)
- Design and implement UI
- Add weather icons
- Format metrics display
- Add last updated timestamp

### Phase 3: Hourly Forecast Chart (3-4 hours)
- Implement Chart.js visualization
- Temperature line graph
- Precipitation bars
- Wind indicators
- Commute window overlays

### Phase 4: Daily Forecast Cards (2-3 hours)
- Create responsive card layout
- Add ride suitability indicators
- Implement expand/collapse details
- Color-code by suitability

### Phase 5: Alerts & Recommendations (2-3 hours)
- Implement alert detection
- Create alert UI components
- Generate recommendations
- Display gear suggestions

### Phase 6: Polish & Testing (3-4 hours)
- Mobile responsive design
- Accessibility improvements
- Performance optimization
- Integration testing

---

## Success Criteria

1. ✅ Dashboard loads in <2 seconds
2. ✅ All weather metrics displayed accurately
3. ✅ Hourly forecast chart is interactive and readable
4. ✅ Ride recommendations are actionable
5. ✅ Works smoothly on mobile devices
6. ✅ Meets WCAG 2.1 AA accessibility standards
7. ✅ Graceful degradation if API fails

---

## Dependencies

- WeatherFetcher (existing)
- Chart.js (already included)
- Bootstrap 5 (already included)
- Open-Meteo API (already integrated)

---

## Future Enhancements

1. **Radar Map** - Animated precipitation radar
2. **Historical Comparison** - Compare to historical averages
3. **Custom Alerts** - User-defined alert thresholds
4. **Weather Notifications** - Push notifications for alerts
5. **Multiple Locations** - Track weather for different routes
6. **Weather Journal** - Log actual conditions experienced

---

*Created: 2026-03-30*  
*Status: Ready for implementation*  
*Estimated Completion: 16-20 hours*