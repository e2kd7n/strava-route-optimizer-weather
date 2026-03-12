"""
Weather data fetcher module.

Fetches weather data from Open-Meteo API (free, no API key required)
to analyze wind conditions and their impact on cycling routes.
"""

import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from geopy.distance import geodesic

logger = logging.getLogger(__name__)


class WeatherFetcher:
    """Fetches weather data from Open-Meteo API (free, no API key needed)."""
    
    def __init__(self):
        """Initialize weather fetcher."""
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.session = requests.Session()
        
    def get_current_conditions(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get current weather conditions for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with current conditions or None if unavailable
        """
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,precipitation,'
                          'wind_speed_10m,wind_direction_10m,wind_gusts_10m',
                'wind_speed_unit': 'kmh',
                'timezone': 'auto'
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'current' not in data:
                return None
            
            current = data['current']
            
            conditions = {
                'timestamp': current.get('time'),
                'temp_c': current.get('temperature_2m'),
                'wind_speed_kph': current.get('wind_speed_10m'),
                'wind_gust_kph': current.get('wind_gusts_10m'),
                'wind_direction_deg': current.get('wind_direction_10m'),
                'humidity': current.get('relative_humidity_2m'),
                'precipitation_mm': current.get('precipitation'),
                'lat': lat,
                'lon': lon
            }
            
            logger.info(f"Fetched weather for ({lat:.4f}, {lon:.4f}): "
                       f"Wind {conditions['wind_speed_kph']:.1f} km/h from {conditions['wind_direction_deg']}°")
            
            return conditions
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather conditions: {e}")
            return None
    
    def get_hourly_forecast(self, lat: float, lon: float, 
                           hours: int = 24) -> Optional[List[Dict]]:
        """
        Get hourly weather forecast.
        
        Args:
            lat: Latitude
            lon: Longitude
            hours: Number of hours to forecast (default 24)
            
        Returns:
            List of hourly forecasts or None if unavailable
        """
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'hourly': 'temperature_2m,wind_speed_10m,wind_direction_10m,'
                         'wind_gusts_10m,precipitation_probability',
                'wind_speed_unit': 'kmh',
                'timezone': 'auto',
                'forecast_days': min((hours // 24) + 1, 7)
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'hourly' not in data:
                return None
            
            hourly = data['hourly']
            forecasts = []
            
            for i in range(min(hours, len(hourly['time']))):
                forecast = {
                    'timestamp': hourly['time'][i],
                    'temp_c': hourly['temperature_2m'][i],
                    'wind_speed_kph': hourly['wind_speed_10m'][i],
                    'wind_gust_kph': hourly['wind_gusts_10m'][i],
                    'wind_direction_deg': hourly['wind_direction_10m'][i],
                    'precipitation_prob': hourly['precipitation_probability'][i]
                }
                forecasts.append(forecast)
            
            return forecasts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching hourly forecast: {e}")
            return None
    
    def get_route_weather(self, coordinates: List[Tuple[float, float]]) -> Dict:
        """
        Get weather conditions along a route.
        
        Args:
            coordinates: List of (lat, lon) tuples representing the route
            
        Returns:
            Dictionary with weather data for the route
        """
        if not coordinates:
            return {}
        
        # Sample weather at start, middle, and end of route
        sample_points = [
            coordinates[0],  # Start
            coordinates[len(coordinates) // 2],  # Middle
            coordinates[-1]  # End
        ]
        
        weather_samples = []
        for lat, lon in sample_points:
            conditions = self.get_current_conditions(lat, lon)
            if conditions:
                weather_samples.append(conditions)
        
        if not weather_samples:
            logger.warning("No weather data available for route")
            return {}
        
        # Average the weather conditions
        avg_conditions = {
            'timestamp': weather_samples[0]['timestamp'],
            'temp_c': np.mean([w['temp_c'] for w in weather_samples if w['temp_c']]),
            'wind_speed_kph': np.mean([w['wind_speed_kph'] for w in weather_samples if w['wind_speed_kph']]),
            'wind_gust_kph': np.mean([w['wind_gust_kph'] for w in weather_samples if w['wind_gust_kph']]),
            'wind_direction_deg': np.mean([w['wind_direction_deg'] for w in weather_samples if w['wind_direction_deg']]),
            'humidity': np.mean([w['humidity'] for w in weather_samples if w['humidity']]),
            'precipitation_mm': np.mean([w['precipitation_mm'] for w in weather_samples if w['precipitation_mm']]),
            'samples': len(weather_samples)
        }
        
        logger.info(f"Route weather: {avg_conditions['wind_speed_kph']:.1f} km/h wind "
                   f"from {avg_conditions['wind_direction_deg']:.0f}°")
        
        return avg_conditions


class WindImpactCalculator:
    """Calculates the impact of wind on cycling routes."""
    
    @staticmethod
    def calculate_bearing(coord1: Tuple[float, float], 
                         coord2: Tuple[float, float]) -> float:
        """
        Calculate bearing between two coordinates.
        
        Args:
            coord1: (lat, lon) of first point
            coord2: (lat, lon) of second point
            
        Returns:
            Bearing in degrees (0-360)
        """
        lat1, lon1 = np.radians(coord1)
        lat2, lon2 = np.radians(coord2)
        
        dlon = lon2 - lon1
        
        x = np.sin(dlon) * np.cos(lat2)
        y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
        
        bearing = np.degrees(np.arctan2(x, y))
        bearing = (bearing + 360) % 360
        
        return bearing
    
    @staticmethod
    def calculate_wind_component(wind_speed: float, wind_direction: float,
                                travel_direction: float) -> Dict[str, float]:
        """
        Calculate headwind/tailwind and crosswind components.
        
        Args:
            wind_speed: Wind speed in km/h
            wind_direction: Wind direction in degrees (where wind is coming FROM)
            travel_direction: Travel direction in degrees
            
        Returns:
            Dictionary with headwind (positive = against, negative = with) 
            and crosswind components
        """
        # Calculate relative wind angle
        # Wind direction is where wind comes FROM, so we need to reverse it
        wind_from = wind_direction
        relative_angle = (wind_from - travel_direction + 180) % 360
        
        # Convert to radians
        angle_rad = np.radians(relative_angle)
        
        # Calculate components
        headwind = wind_speed * np.cos(angle_rad)  # Positive = headwind
        crosswind = abs(wind_speed * np.sin(angle_rad))
        
        return {
            'headwind_kph': headwind,
            'crosswind_kph': crosswind,
            'relative_angle': relative_angle
        }
    
    def analyze_route_wind_impact(self, coordinates: List[Tuple[float, float]],
                                  wind_speed: float, wind_direction: float) -> Dict:
        """
        Analyze wind impact along entire route.
        
        Args:
            coordinates: List of (lat, lon) tuples
            wind_speed: Wind speed in km/h
            wind_direction: Wind direction in degrees
            
        Returns:
            Dictionary with wind impact analysis
        """
        if len(coordinates) < 2:
            return {}
        
        headwinds = []
        crosswinds = []
        segment_distances = []
        
        # Analyze each segment
        for i in range(len(coordinates) - 1):
            coord1 = coordinates[i]
            coord2 = coordinates[i + 1]
            
            # Calculate segment bearing
            bearing = self.calculate_bearing(coord1, coord2)
            
            # Calculate wind components
            components = self.calculate_wind_component(
                wind_speed, wind_direction, bearing
            )
            
            # Calculate segment distance
            distance = geodesic(coord1, coord2).km
            
            headwinds.append(components['headwind_kph'])
            crosswinds.append(components['crosswind_kph'])
            segment_distances.append(distance)
        
        # Calculate weighted averages
        total_distance = sum(segment_distances)
        
        if total_distance > 0:
            avg_headwind = sum(h * d for h, d in zip(headwinds, segment_distances)) / total_distance
            avg_crosswind = sum(c * d for c, d in zip(crosswinds, segment_distances)) / total_distance
        else:
            avg_headwind = 0
            avg_crosswind = 0
        
        # Estimate time penalty (rough approximation based on cycling research)
        # Headwind: ~1.5% slower per 1 km/h headwind
        # Crosswind: ~0.5% slower per 1 km/h crosswind
        # Tailwind: ~1% faster per 1 km/h tailwind (but less efficient than headwind penalty)
        if avg_headwind > 0:
            time_penalty_pct = avg_headwind * 1.5 + avg_crosswind * 0.5
        else:
            time_penalty_pct = avg_headwind * 1.0 + avg_crosswind * 0.5
        
        # Determine wind favorability
        if avg_headwind < -5:
            favorability = 'favorable'
        elif avg_headwind > 5:
            favorability = 'unfavorable'
        else:
            favorability = 'neutral'
        
        return {
            'avg_headwind_kph': avg_headwind,
            'avg_crosswind_kph': avg_crosswind,
            'max_headwind_kph': max(headwinds) if headwinds else 0,
            'max_crosswind_kph': max(crosswinds) if crosswinds else 0,
            'time_penalty_pct': time_penalty_pct,
            'wind_favorability': favorability,
            'estimated_time_impact_min': 0  # Will be calculated based on route duration
        }


# Made with Bob