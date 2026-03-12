"""
Long Ride Analysis Module

Analyzes non-commute cycling activities for recreational ride recommendations.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from geopy.distance import geodesic
import polyline

from .data_fetcher import Activity
from .route_namer import RouteNamer
from .weather_fetcher import WeatherFetcher

logger = logging.getLogger(__name__)


@dataclass
class LongRide:
    """Represents a long/recreational ride."""
    activity_id: int
    name: str
    coordinates: List[Tuple[float, float]]
    distance: float  # meters
    duration: int  # seconds
    elevation_gain: float  # meters
    timestamp: str  # ISO format
    average_speed: float  # m/s
    start_location: Tuple[float, float]
    end_location: Tuple[float, float]
    is_loop: bool  # True if start and end are close
    
    @property
    def distance_km(self) -> float:
        """Distance in kilometers."""
        return self.distance / 1000
    
    @property
    def duration_hours(self) -> float:
        """Duration in hours."""
        return self.duration / 3600
    
    @property
    def midpoint(self) -> Tuple[float, float]:
        """Calculate midpoint of the ride."""
        if not self.coordinates:
            return self.start_location
        mid_idx = len(self.coordinates) // 2
        return self.coordinates[mid_idx]


@dataclass
class RideRecommendation:
    """Represents a ride recommendation for a clicked location."""
    ride: LongRide
    distance_to_location: float  # meters from clicked location
    weather_score: float  # 0-1, based on wind direction preference
    precipitation_risk: str  # "none", "low", "medium", "high"
    recommended_start_time: Optional[str] = None
    estimated_duration: Optional[float] = None  # hours
    route_description: str = ""
    wind_analysis: Optional[Dict[str, Any]] = None


class LongRideAnalyzer:
    """Analyzes non-commute rides for recreational recommendations."""
    
    def __init__(self, activities: List[Activity], config):
        """
        Initialize long ride analyzer.
        
        Args:
            activities: List of all Activity objects
            config: Configuration object
        """
        self.activities = activities
        self.config = config
        self.route_namer = RouteNamer(config)
        self.weather_fetcher = WeatherFetcher()  # WeatherFetcher doesn't take config parameter
        
    def classify_activities(self, commute_activities: List[Activity]) -> Tuple[List[Activity], List[Activity]]:
        """
        Classify activities into commutes and long rides.
        
        Args:
            commute_activities: List of identified commute activities
            
        Returns:
            Tuple of (commute_activities, long_ride_activities)
        """
        commute_ids = {act.id for act in commute_activities}
        
        # Filter for cycling activities that are not commutes
        long_rides = []
        for activity in self.activities:
            # Skip if it's a commute
            if activity.id in commute_ids:
                continue
            
            # Must be a cycling activity
            if 'Ride' not in activity.type:
                continue
            
            # Must have GPS data
            if not activity.start_latlng or not activity.end_latlng or not activity.polyline:
                continue
            
            # Skip virtual rides
            if activity.name and 'virtual' in activity.name.lower():
                continue
            
            # Apply distance filter (configurable, default > 15km for long rides)
            min_distance = self.config.get('long_rides.min_distance_km', 15) * 1000
            if activity.distance < min_distance:
                continue
            
            long_rides.append(activity)
        
        logger.info(f"Classified {len(commute_activities)} commutes and {len(long_rides)} long rides")
        
        return commute_activities, long_rides
    
    def extract_long_rides(self, long_ride_activities: List[Activity]) -> List[LongRide]:
        """
        Convert activities to LongRide objects.
        
        Args:
            long_ride_activities: List of Activity objects
            
        Returns:
            List of LongRide objects
        """
        long_rides = []
        
        for activity in long_ride_activities:
            try:
                # Decode polyline
                coordinates = polyline.decode(activity.polyline)
                
                # Check if it's a loop (start and end within 500m)
                start_end_distance = geodesic(
                    activity.start_latlng,
                    activity.end_latlng
                ).meters
                is_loop = start_end_distance < 500
                
                long_ride = LongRide(
                    activity_id=activity.id,
                    name=activity.name,
                    coordinates=coordinates,
                    distance=activity.distance,
                    duration=activity.moving_time,
                    elevation_gain=activity.total_elevation_gain,
                    timestamp=activity.start_date,
                    average_speed=activity.average_speed,
                    start_location=activity.start_latlng,
                    end_location=activity.end_latlng,
                    is_loop=is_loop
                )
                
                long_rides.append(long_ride)
                
            except Exception as e:
                logger.warning(f"Failed to process long ride {activity.id}: {e}")
                continue
        
        logger.info(f"Extracted {len(long_rides)} long rides")
        
        return long_rides
    
    def find_rides_near_location(self, long_rides: List[LongRide], 
                                 clicked_lat: float, clicked_lon: float,
                                 search_radius_km: float = 5.0) -> List[LongRide]:
        """
        Find rides that pass near a clicked location.
        
        Args:
            long_rides: List of LongRide objects
            clicked_lat: Latitude of clicked location
            clicked_lon: Longitude of clicked location
            search_radius_km: Search radius in kilometers
            
        Returns:
            List of LongRide objects that pass near the location
        """
        clicked_location = (clicked_lat, clicked_lon)
        nearby_rides = []
        
        for ride in long_rides:
            # Check if any point on the route is within search radius
            min_distance = float('inf')
            
            for coord in ride.coordinates:
                distance = geodesic(clicked_location, coord).kilometers
                min_distance = min(min_distance, distance)
                
                # Early exit if we found a close point
                if min_distance <= search_radius_km:
                    nearby_rides.append(ride)
                    break
        
        logger.info(f"Found {len(nearby_rides)} rides within {search_radius_km}km of location")
        
        return nearby_rides
    
    def calculate_wind_score(self, ride: LongRide, current_weather: Dict[str, Any]) -> float:
        """
        Calculate wind favorability score for a ride.
        Prefers headwind in first half, tailwind in second half.
        
        Args:
            ride: LongRide object
            current_weather: Current weather data
            
        Returns:
            Score from 0-1 (1 is best)
        """
        if not ride.coordinates or len(ride.coordinates) < 4:
            return 0.5  # Neutral score if insufficient data
        
        wind_direction = current_weather.get('wind_direction', 0)
        
        # Calculate bearing for first and second half of ride
        first_quarter_idx = len(ride.coordinates) // 4
        mid_idx = len(ride.coordinates) // 2
        three_quarter_idx = 3 * len(ride.coordinates) // 4
        
        # First half bearing (outbound)
        outbound_bearing = self._calculate_bearing(
            ride.coordinates[first_quarter_idx],
            ride.coordinates[mid_idx]
        )
        
        # Second half bearing (return)
        return_bearing = self._calculate_bearing(
            ride.coordinates[mid_idx],
            ride.coordinates[three_quarter_idx]
        )
        
        # Calculate relative wind angles
        outbound_wind_angle = abs((wind_direction - outbound_bearing + 180) % 360 - 180)
        return_wind_angle = abs((wind_direction - return_bearing + 180) % 360 - 180)
        
        # Ideal: headwind outbound (angle close to 0), tailwind return (angle close to 180)
        # Score outbound: prefer headwind (0-45 degrees)
        outbound_score = 1.0 if outbound_wind_angle < 45 else (1.0 - outbound_wind_angle / 180)
        
        # Score return: prefer tailwind (135-180 degrees)
        if return_wind_angle > 135:
            return_score = 1.0
        else:
            return_score = return_wind_angle / 180
        
        # Combined score (weighted: 40% outbound, 60% return - prefer tailwind coming home)
        combined_score = 0.4 * outbound_score + 0.6 * return_score
        
        return combined_score
    
    def _calculate_bearing(self, point1: Tuple[float, float], 
                          point2: Tuple[float, float]) -> float:
        """
        Calculate bearing between two points.
        
        Args:
            point1: (lat, lon) tuple
            point2: (lat, lon) tuple
            
        Returns:
            Bearing in degrees (0-360)
        """
        lat1, lon1 = np.radians(point1[0]), np.radians(point1[1])
        lat2, lon2 = np.radians(point2[0]), np.radians(point2[1])
        
        dlon = lon2 - lon1
        
        x = np.sin(dlon) * np.cos(lat2)
        y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
        
        bearing = np.degrees(np.arctan2(x, y))
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def get_ride_recommendations(self, long_rides: List[LongRide],
                                clicked_lat: float, clicked_lon: float,
                                target_duration_hours: Optional[float] = None,
                                target_distance_km: Optional[float] = None) -> List[RideRecommendation]:
        """
        Get ride recommendations for a clicked location with weather analysis.
        
        Args:
            long_rides: List of LongRide objects
            clicked_lat: Latitude of clicked location
            clicked_lon: Longitude of clicked location
            target_duration_hours: Desired ride duration in hours (optional)
            target_distance_km: Desired ride distance in km (optional)
            
        Returns:
            List of RideRecommendation objects, sorted by score
        """
        # Find rides near the location
        nearby_rides = self.find_rides_near_location(long_rides, clicked_lat, clicked_lon)
        
        if not nearby_rides:
            logger.warning("No rides found near clicked location")
            return []
        
        # Get current weather for the area
        try:
            weather_data = self.weather_fetcher.get_current_weather(clicked_lat, clicked_lon)
        except Exception as e:
            logger.warning(f"Failed to fetch weather: {e}")
            weather_data = {}
        
        recommendations = []
        
        for ride in nearby_rides:
            # Calculate distance from clicked location to ride
            min_distance = min(
                geodesic((clicked_lat, clicked_lon), coord).meters
                for coord in ride.coordinates
            )
            
            # Calculate wind score
            wind_score = self.calculate_wind_score(ride, weather_data) if weather_data else 0.5
            
            # Assess precipitation risk (placeholder - would need forecast data)
            precipitation_risk = "low"  # TODO: Implement with forecast API
            
            # Filter by target duration/distance if specified
            if target_duration_hours and abs(ride.duration_hours - target_duration_hours) > 1.0:
                continue
            if target_distance_km and abs(ride.distance_km - target_distance_km) > 10:
                continue
            
            recommendation = RideRecommendation(
                ride=ride,
                distance_to_location=min_distance,
                weather_score=wind_score,
                precipitation_risk=precipitation_risk,
                route_description=f"{ride.distance_km:.1f}km, {ride.duration_hours:.1f}h"
            )
            
            recommendations.append(recommendation)
        
        # Sort by combined score (wind score primary, distance secondary)
        recommendations.sort(
            key=lambda r: (r.weather_score, -r.distance_to_location),
            reverse=True
        )
        
        logger.info(f"Generated {len(recommendations)} ride recommendations")
        
        return recommendations


# Made with Bob