"""
Commute Forecast Generator Module.

Generates 7-day commute forecasts with weather-aware route recommendations,
optimal departure times, and transit suggestions for bad weather.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CommuteWindow:
    """Represents a commute time window with weather conditions."""
    date: str
    day_name: str
    direction: str  # "to_work" or "to_home"
    window_start: time
    window_end: time
    optimal_departure: time
    temp_c: float
    temp_f: float
    wind_speed_kph: float
    wind_speed_mph: float
    wind_direction_deg: float
    precipitation_prob: float
    precipitation_mm: float
    recommended_route_id: Optional[str]
    recommended_route_name: str
    weather_severity: str  # "good", "fair", "poor", "miserable"
    recommend_transit: bool
    notes: List[str]


@dataclass
class DailyForecast:
    """Represents a full day's commute forecast."""
    date: str
    day_name: str
    morning_commute: CommuteWindow
    evening_commute: CommuteWindow
    overall_rating: str  # "excellent", "good", "fair", "poor", "avoid"


class CommuteForecastGenerator:
    """Generates intelligent commute forecasts with weather-aware recommendations."""
    
    def __init__(self, weather_fetcher, route_groups: Dict, home_location: Tuple[float, float],
                 work_location: Tuple[float, float], unit_system: str = "imperial"):
        """
        Initialize forecast generator.
        
        Args:
            weather_fetcher: WeatherFetcher instance
            route_groups: Dictionary of route groups (to_work and to_home)
            home_location: (lat, lon) tuple for home
            work_location: (lat, lon) tuple for work
            unit_system: "metric" or "imperial"
        """
        self.weather_fetcher = weather_fetcher
        self.route_groups = route_groups
        self.home_location = home_location
        self.work_location = work_location
        self.unit_system = unit_system
        
        # Commute time windows (configurable)
        self.morning_window_start = time(7, 0)  # 7:00 AM
        self.morning_window_end = time(9, 0)    # 9:00 AM
        self.evening_window_start = time(15, 0)  # 3:00 PM
        self.evening_window_end = time(18, 0)    # 6:00 PM
        
    def generate_7day_forecast(self) -> List[DailyForecast]:
        """
        Generate 7-day commute forecast.
        
        Returns:
            List of DailyForecast objects
        """
        logger.info("Generating 7-day commute forecast...")
        
        # Get 7-day weather forecast for work location (midpoint of commute)
        mid_lat = (self.home_location[0] + self.work_location[0]) / 2
        mid_lon = (self.home_location[1] + self.work_location[1]) / 2
        
        daily_weather = self.weather_fetcher.get_daily_forecast(mid_lat, mid_lon, days=7)
        
        if not daily_weather:
            logger.error("Failed to fetch weather forecast")
            return []
        
        forecasts = []
        
        for day_weather in daily_weather:
            date_str = day_weather['date']
            date_obj = datetime.fromisoformat(date_str)
            day_name = date_obj.strftime('%A')
            
            # Generate morning commute forecast
            morning = self._generate_commute_window(
                date_str, day_name, "to_work", day_weather, is_morning=True
            )
            
            # Generate evening commute forecast
            evening = self._generate_commute_window(
                date_str, day_name, "to_home", day_weather, is_morning=False
            )
            
            # Calculate overall day rating
            overall_rating = self._calculate_overall_rating(morning, evening)
            
            daily_forecast = DailyForecast(
                date=date_str,
                day_name=day_name,
                morning_commute=morning,
                evening_commute=evening,
                overall_rating=overall_rating
            )
            
            forecasts.append(daily_forecast)
            
        logger.info(f"Generated forecast for {len(forecasts)} days")
        return forecasts
    
    def _generate_commute_window(self, date_str: str, day_name: str, direction: str,
                                 day_weather: Dict, is_morning: bool) -> CommuteWindow:
        """Generate forecast for a single commute window."""
        
        # Determine time window
        if is_morning:
            window_start = self.morning_window_start
            window_end = self.morning_window_end
        else:
            window_start = self.evening_window_start
            window_end = self.evening_window_end
        
        # Extract weather data
        temp_c = (day_weather['temp_max_c'] + day_weather['temp_min_c']) / 2
        temp_f = temp_c * 9/5 + 32
        wind_speed_kph = day_weather['wind_speed_max_kph']
        wind_speed_mph = wind_speed_kph * 0.621371
        wind_direction_deg = day_weather['wind_direction_dominant_deg']
        precipitation_prob = day_weather['precipitation_prob_max']
        precipitation_mm = day_weather['precipitation_sum_mm']
        
        # Calculate weather severity
        severity = self._calculate_weather_severity(
            temp_c, wind_speed_kph, precipitation_prob, precipitation_mm
        )
        
        # Determine if transit is recommended
        recommend_transit = self._should_recommend_transit(
            temp_c, wind_speed_kph, precipitation_prob, precipitation_mm
        )
        
        # Select optimal route based on weather
        route_id, route_name = self._select_optimal_route(
            direction, wind_direction_deg, wind_speed_kph
        )
        
        # Calculate optimal departure time
        optimal_departure = self._calculate_optimal_departure(
            window_start, window_end, precipitation_prob, is_morning
        )
        
        # Generate notes
        notes = self._generate_notes(
            temp_c, wind_speed_kph, wind_direction_deg, precipitation_prob,
            precipitation_mm, severity, recommend_transit
        )
        
        return CommuteWindow(
            date=date_str,
            day_name=day_name,
            direction=direction,
            window_start=window_start,
            window_end=window_end,
            optimal_departure=optimal_departure,
            temp_c=temp_c,
            temp_f=temp_f,
            wind_speed_kph=wind_speed_kph,
            wind_speed_mph=wind_speed_mph,
            wind_direction_deg=wind_direction_deg,
            precipitation_prob=precipitation_prob,
            precipitation_mm=precipitation_mm,
            recommended_route_id=route_id,
            recommended_route_name=route_name,
            weather_severity=severity,
            recommend_transit=recommend_transit,
            notes=notes
        )
    
    def _calculate_weather_severity(self, temp_c: float, wind_speed_kph: float,
                                    precip_prob: float, precip_mm: float) -> str:
        """
        Calculate weather severity for cycling.
        
        Returns: "good", "fair", "poor", or "miserable"
        """
        severity_score = 0
        
        # Temperature scoring (ideal: 10-25°C / 50-77°F)
        if temp_c < 0:
            severity_score += 3  # Freezing
        elif temp_c < 5:
            severity_score += 2  # Very cold
        elif temp_c < 10:
            severity_score += 1  # Cold
        elif temp_c > 30:
            severity_score += 2  # Very hot
        elif temp_c > 25:
            severity_score += 1  # Hot
        
        # Wind scoring
        if wind_speed_kph > 40:
            severity_score += 3  # Dangerous winds
        elif wind_speed_kph > 30:
            severity_score += 2  # Strong winds
        elif wind_speed_kph > 20:
            severity_score += 1  # Moderate winds
        
        # Precipitation scoring
        if precip_prob > 80 or precip_mm > 10:
            severity_score += 3  # Heavy rain likely
        elif precip_prob > 60 or precip_mm > 5:
            severity_score += 2  # Moderate rain likely
        elif precip_prob > 40 or precip_mm > 2:
            severity_score += 1  # Light rain possible
        
        # Determine severity level
        if severity_score == 0:
            return "good"
        elif severity_score <= 2:
            return "fair"
        elif severity_score <= 4:
            return "poor"
        else:
            return "miserable"
    
    def _should_recommend_transit(self, temp_c: float, wind_speed_kph: float,
                                  precip_prob: float, precip_mm: float) -> bool:
        """
        Determine if transit should be recommended instead of cycling.
        
        Recommend transit when conditions are both wet AND cold/windy.
        """
        is_wet = precip_prob > 70 or precip_mm > 5
        is_cold = temp_c < 5
        is_very_windy = wind_speed_kph > 35
        is_freezing_rain = temp_c < 2 and precip_prob > 50
        
        # Recommend transit if:
        # 1. Wet and cold
        # 2. Wet and very windy
        # 3. Freezing rain
        return (is_wet and is_cold) or (is_wet and is_very_windy) or is_freezing_rain
    
    def _select_optimal_route(self, direction: str, wind_direction_deg: float,
                             wind_speed_kph: float) -> Tuple[Optional[str], str]:
        """
        Select optimal route based on wind conditions.
        
        Returns: (route_id, route_name)
        """
        routes = self.route_groups.get(direction, [])
        
        if not routes:
            return None, "No routes available"
        
        # If wind is light, just return the most frequent route
        if wind_speed_kph < 15:
            most_frequent = max(routes, key=lambda r: r.get('frequency', 0))
            return most_frequent.get('id'), most_frequent.get('name', 'Primary Route')
        
        # For stronger winds, consider wind impact
        # This is a simplified version - in reality, we'd calculate wind components
        # for each route and select the one with least headwind
        
        # For now, return the most frequent route
        # TODO (#70): Implement wind-aware route selection using WindImpactCalculator
        most_frequent = max(routes, key=lambda r: r.get('frequency', 0))
        return most_frequent.get('id'), most_frequent.get('name', 'Primary Route')
    
    def _calculate_optimal_departure(self, window_start: time, window_end: time,
                                    precip_prob: float, is_morning: bool) -> time:
        """
        Calculate optimal departure time within window.
        
        For high precipitation probability, suggest earlier departure to avoid rush
        or later to wait out rain.
        """
        # Default to middle of window
        start_minutes = window_start.hour * 60 + window_start.minute
        end_minutes = window_end.hour * 60 + window_end.minute
        mid_minutes = (start_minutes + end_minutes) // 2
        
        # Adjust based on precipitation
        if precip_prob > 60:
            # High chance of rain - suggest earlier departure
            optimal_minutes = start_minutes + (mid_minutes - start_minutes) // 2
        else:
            optimal_minutes = mid_minutes
        
        optimal_hour = optimal_minutes // 60
        optimal_minute = optimal_minutes % 60
        
        return time(optimal_hour, optimal_minute)
    
    def _generate_notes(self, temp_c: float, wind_speed_kph: float,
                       wind_direction_deg: float, precip_prob: float,
                       precip_mm: float, severity: str, recommend_transit: bool) -> List[str]:
        """Generate helpful notes for the commute."""
        notes = []
        
        # Temperature notes
        if temp_c < 0:
            notes.append("⚠️ Freezing temperatures - dress warmly, watch for ice")
        elif temp_c < 5:
            notes.append("🥶 Very cold - layer up and protect extremities")
        elif temp_c < 10:
            notes.append("🧥 Cold morning - bring extra layers")
        elif temp_c > 30:
            notes.append("🥵 Very hot - stay hydrated, consider earlier/later departure")
        elif temp_c > 25:
            notes.append("☀️ Warm - bring water and sunscreen")
        
        # Wind notes
        if wind_speed_kph > 35:
            notes.append("💨 Dangerous winds - consider transit or alternative route")
        elif wind_speed_kph > 25:
            notes.append("🌬️ Strong winds - allow extra time, be cautious")
        elif wind_speed_kph > 15:
            notes.append("🍃 Moderate winds - may slow you down")
        
        # Precipitation notes
        if precip_prob > 80 or precip_mm > 10:
            notes.append("🌧️ Heavy rain expected - bring rain gear or consider transit")
        elif precip_prob > 60 or precip_mm > 5:
            notes.append("☔ Rain likely - pack rain jacket and fenders")
        elif precip_prob > 40:
            notes.append("🌦️ Possible showers - bring rain jacket just in case")
        
        # Transit recommendation
        if recommend_transit:
            notes.append("🚇 Transit recommended - conditions not ideal for cycling")
        
        # Overall condition note
        if severity == "good":
            notes.append("✅ Excellent cycling conditions!")
        elif severity == "fair":
            notes.append("👍 Good cycling weather with minor considerations")
        
        return notes
    
    def _calculate_overall_rating(self, morning: CommuteWindow,
                                  evening: CommuteWindow) -> str:
        """
        Calculate overall day rating based on both commutes.
        
        Returns: "excellent", "good", "fair", "poor", or "avoid"
        """
        severity_scores = {
            "good": 0,
            "fair": 1,
            "poor": 2,
            "miserable": 3
        }
        
        morning_score = severity_scores.get(morning.weather_severity, 2)
        evening_score = severity_scores.get(evening.weather_severity, 2)
        
        avg_score = (morning_score + evening_score) / 2
        
        # Check if transit recommended for both
        if morning.recommend_transit and evening.recommend_transit:
            return "avoid"
        
        if avg_score == 0:
            return "excellent"
        elif avg_score <= 0.5:
            return "good"
        elif avg_score <= 1.5:
            return "fair"
        elif avg_score <= 2.5:
            return "poor"
        else:
            return "avoid"


# Made with Bob