"""
Long Ride Analysis Module

Analyzes non-commute cycling activities for recreational ride recommendations.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from geopy.distance import geodesic
import polyline
from similaritymeasures import frechet_dist
from scipy.spatial.distance import directed_hausdorff

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
    def group_rides_by_name(self, long_ride_activities: List[Activity]) -> Tuple[Dict[str, List[Activity]], List[Activity]]:
        """
        Group long ride activities by their Strava activity name.
        This is the primary grouping mechanism since users often name similar routes the same.
        
        Args:
            long_ride_activities: List of Activity objects
            
        Returns:
            Tuple of (name_groups dict, unnamed_rides list)
        """
        name_groups: Dict[str, List[Activity]] = {}
        unnamed_rides: List[Activity] = []
        
        for activity in long_ride_activities:
            # Handle unnamed or generic names
            if not activity.name or activity.name.strip() in ['', 'Morning Ride', 'Afternoon Ride', 'Evening Ride', 'Lunch Ride']:
                unnamed_rides.append(activity)
                continue
            
            # Normalize the name (strip whitespace, lowercase for comparison)
            normalized_name = activity.name.strip()
            
            if normalized_name not in name_groups:
                name_groups[normalized_name] = []
            name_groups[normalized_name].append(activity)
        
        # Log statistics
        logger.info(f"Grouped {len(long_ride_activities)} long rides into {len(name_groups)} named groups")
        logger.info(f"Found {len(unnamed_rides)} rides with generic/no names")
        
        # Log top groups
        sorted_groups = sorted(name_groups.items(), key=lambda x: len(x[1]), reverse=True)
        for name, activities in sorted_groups[:10]:
            logger.info(f"  '{name}': {len(activities)} rides")
        
        return name_groups, unnamed_rides
    
    def consolidate_named_groups(self, name_groups: Dict[str, List[Activity]]) -> List[LongRide]:
        """
        Consolidate activities with the same name into representative LongRide objects.
        For each named group, select the most recent or best representative ride.
        
        Args:
            name_groups: Dictionary mapping activity names to lists of activities
            
        Returns:
            List of LongRide objects representing each unique named route
        """
        consolidated_rides = []
        
        for route_name, activities in name_groups.items():
            # Sort by date (most recent first)
            sorted_activities = sorted(activities, key=lambda a: a.start_date, reverse=True)
            
            # Use the most recent activity as the representative
            representative = sorted_activities[0]
            
            try:
                # Decode polyline
                if not representative.polyline:
                    continue
                    
                coordinates = polyline.decode(representative.polyline)
                
                # Check if it's a loop (start and end within 500m)
                if representative.start_latlng and representative.end_latlng:
                    start_end_distance = geodesic(
                        representative.start_latlng,
                        representative.end_latlng
                    ).meters
                    is_loop = start_end_distance < 500
                else:
                    is_loop = False
                
                long_ride = LongRide(
                    activity_id=representative.id,
                    name=route_name,  # Use the consistent route name
                    coordinates=coordinates,
                    distance=representative.distance,
                    duration=representative.moving_time,
                    elevation_gain=representative.total_elevation_gain,
                    timestamp=representative.start_date,
                    average_speed=representative.average_speed,
                    start_location=representative.start_latlng or (0.0, 0.0),
                    end_location=representative.end_latlng or (0.0, 0.0),
                    is_loop=is_loop
                )
                
                consolidated_rides.append(long_ride)
                logger.debug(f"Consolidated '{route_name}': {len(activities)} rides -> 1 representative")
                
            except Exception as e:
                logger.warning(f"Failed to process named group '{route_name}': {e}")
                continue
        
        logger.info(f"Consolidated {sum(len(acts) for acts in name_groups.values())} activities into {len(consolidated_rides)} unique named routes")
        
        return consolidated_rides
    def match_unnamed_rides_to_groups(self, unnamed_rides: List[Activity], 
                                     named_groups: Dict[str, List[Activity]],
                                     similarity_threshold: float = 0.15) -> Tuple[Dict[str, List[Activity]], List[Activity]]:
        """
        Match unnamed/generic rides to existing named groups using route similarity.
        Uses Fréchet distance to validate if routes are similar enough to be grouped together.
        
        Args:
            unnamed_rides: List of activities with generic/no names
            named_groups: Dictionary of existing named route groups
            similarity_threshold: Maximum Fréchet distance (km) to consider routes similar
            
        Returns:
            Tuple of (updated_named_groups, still_unnamed_rides)
        """
        still_unnamed = []
        matched_count = 0
        
        # Get representative routes for each named group
        group_representatives = {}
        for name, activities in named_groups.items():
            # Use most recent activity as representative
            rep = sorted(activities, key=lambda a: a.start_date, reverse=True)[0]
            if rep.polyline:
                try:
                    coords = polyline.decode(rep.polyline)
                    group_representatives[name] = np.array(coords)
                except:
                    continue
        
        # Try to match each unnamed ride
        for activity in unnamed_rides:
            if not activity.polyline:
                still_unnamed.append(activity)
                continue
            
            try:
                # Decode route
                route_coords = np.array(polyline.decode(activity.polyline))
                
                # Find best matching group
                best_match = None
                best_distance = float('inf')
                
                for group_name, rep_coords in group_representatives.items():
                    # Calculate Fréchet distance
                    try:
                        frechet_distance = frechet_dist(route_coords, rep_coords)
                        
                        # Also calculate Hausdorff as secondary check
                        hausdorff_dist = max(
                            directed_hausdorff(route_coords, rep_coords)[0],
                            directed_hausdorff(rep_coords, route_coords)[0]
                        )
                        
                        # Use average of both distances
                        combined_distance = (frechet_distance + hausdorff_dist) / 2
                        
                        if combined_distance < best_distance:
                            best_distance = combined_distance
                            best_match = group_name
                    except:
                        continue
                
                # If we found a good match, add to that group
                if best_match and best_distance < similarity_threshold:
                    named_groups[best_match].append(activity)
                    matched_count += 1
                    logger.debug(f"Matched unnamed ride {activity.id} to '{best_match}' (distance: {best_distance:.3f})")
                else:
                    still_unnamed.append(activity)
                    
            except Exception as e:
                logger.warning(f"Failed to match unnamed ride {activity.id}: {e}")
                still_unnamed.append(activity)
                continue
        
        logger.info(f"Matched {matched_count} unnamed rides to existing groups")
        logger.info(f"Remaining unnamed rides: {len(still_unnamed)}")
        
        return named_groups, still_unnamed
    
    def generate_fallback_names(self, unnamed_rides: List[Activity]) -> Dict[str, List[Activity]]:
        """
        Generate geocoded names for rides that couldn't be matched to named groups.
        Only used as a fallback when activity names are absent or too generic.
        
        Args:
            unnamed_rides: List of activities without specific names
            
        Returns:
            Dictionary mapping generated names to activities
        """
        fallback_groups = {}
        
        for activity in unnamed_rides:
            try:
                if not activity.start_latlng:
                    continue
                
                # Generate simple name based on distance and type
                if activity.distance:
                    distance_km = activity.distance / 1000
                    # Determine if it's a loop
                    if activity.start_latlng and activity.end_latlng:
                        start_end_dist = geodesic(activity.start_latlng, activity.end_latlng).meters
                        if start_end_dist < 500:
                            generated_name = f"Loop Ride ({distance_km:.1f}km)"
                        else:
                            generated_name = f"Out & Back ({distance_km:.1f}km)"
                    else:
                        generated_name = f"Ride ({distance_km:.1f}km)"
                else:
                    generated_name = "Unnamed Ride"
                
                if generated_name not in fallback_groups:
                    fallback_groups[generated_name] = []
                fallback_groups[generated_name].append(activity)
                
            except Exception as e:
                logger.warning(f"Failed to generate name for activity {activity.id}: {e}")
                continue
        
        logger.info(f"Generated {len(fallback_groups)} fallback names for unnamed rides")
        
        return fallback_groups
    
    
    
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
                # Skip if missing required data
                if not activity.polyline or not activity.start_latlng or not activity.end_latlng:
                    continue
                
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
                    name=activity.name or "Unnamed Ride",
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
    
    def calculate_wind_score(self, ride: LongRide, current_weather: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate wind favorability score for a ride.
        Strong preference for tailwinds in the second half of the route.
        
        Args:
            ride: LongRide object
            current_weather: Current weather data
            
        Returns:
            Tuple of (score from 0-1 where 1 is best, detailed wind analysis dict)
        """
        if not ride.coordinates or len(ride.coordinates) < 4:
            return 0.5, {'status': 'insufficient_data'}
        
        wind_direction = current_weather.get('wind_direction_deg',
                                            current_weather.get('wind_direction', 0))
        wind_speed = current_weather.get('wind_speed_kph',
                                        current_weather.get('wind_speed', 0))
        
        # Analyze wind for multiple segments to get detailed picture
        num_segments = min(8, len(ride.coordinates) // 10)  # 8 segments or fewer
        segment_size = len(ride.coordinates) // num_segments
        
        segment_analyses = []
        first_half_scores = []
        second_half_scores = []
        
        for i in range(num_segments):
            start_idx = i * segment_size
            end_idx = min((i + 1) * segment_size, len(ride.coordinates) - 1)
            
            if start_idx >= end_idx:
                continue
            
            # Calculate segment bearing
            segment_bearing = self._calculate_bearing(
                ride.coordinates[start_idx],
                ride.coordinates[end_idx]
            )
            
            # Calculate relative wind angle (wind direction is where wind comes FROM)
            relative_angle = (wind_direction - segment_bearing + 180) % 360 - 180
            
            # Determine wind type and score
            if abs(relative_angle) < 45:
                wind_type = "headwind"
                segment_score = 0.3  # Headwind is not ideal
            elif abs(relative_angle) > 135:
                wind_type = "tailwind"
                segment_score = 1.0  # Tailwind is excellent
            elif abs(relative_angle) < 90:
                wind_type = "quartering_headwind"
                segment_score = 0.5
            else:
                wind_type = "quartering_tailwind"
                segment_score = 0.8
            
            segment_analyses.append({
                'segment': i + 1,
                'wind_type': wind_type,
                'relative_angle': relative_angle,
                'score': segment_score
            })
            
            # Categorize by half
            if i < num_segments // 2:
                first_half_scores.append(segment_score)
            else:
                second_half_scores.append(segment_score)
        
        # Calculate average scores for each half
        first_half_avg = np.mean(first_half_scores) if first_half_scores else 0.5
        second_half_avg = np.mean(second_half_scores) if second_half_scores else 0.5
        
        # STRONG preference for tailwinds in second half (70% weight on second half)
        # This ensures routes with good tailwinds coming back are highly ranked
        combined_score = 0.3 * first_half_avg + 0.7 * second_half_avg
        
        # Bonus for consistent tailwinds in second half
        if second_half_avg > 0.8:
            combined_score = min(1.0, float(combined_score * 1.1))  # 10% bonus
        
        # Detailed analysis for reporting
        wind_analysis = {
            'wind_speed_kph': wind_speed,
            'wind_direction_deg': wind_direction,
            'first_half_score': first_half_avg,
            'second_half_score': second_half_avg,
            'combined_score': combined_score,
            'segments': segment_analyses,
            'recommendation': self._get_wind_recommendation(
                float(first_half_avg), float(second_half_avg), float(wind_speed)
            )
        }
        
        return float(combined_score), wind_analysis
    
    def _get_wind_recommendation(self, first_half_score: float,
                                 second_half_score: float, wind_speed: float) -> str:
        """
        Generate human-readable wind recommendation.
        
        Args:
            first_half_score: Score for first half (0-1)
            second_half_score: Score for second half (0-1)
            wind_speed: Wind speed in km/h
            
        Returns:
            Recommendation string
        """
        if wind_speed < 10:
            return "Light winds - minimal impact on ride"
        
        if second_half_score > 0.8:
            if first_half_score < 0.5:
                return "Excellent! Headwind out, strong tailwind back - perfect for a long ride"
            else:
                return "Great tailwinds for the return journey"
        elif second_half_score > 0.6:
            return "Favorable winds on the way back"
        elif second_half_score < 0.4:
            return "Challenging headwinds on return - consider shorter route or different day"
        else:
            return "Mixed wind conditions - manageable but not ideal"
    
    def format_wind_analysis(self, wind_analysis: Dict[str, Any]) -> str:
        """
        Format wind analysis into human-readable description.
        
        Args:
            wind_analysis: Wind analysis dictionary from calculate_wind_score
            
        Returns:
            Formatted string describing wind conditions
        """
        if not wind_analysis or wind_analysis.get('status') == 'insufficient_data':
            return "Wind analysis unavailable"
        
        if wind_analysis.get('status') == 'no_weather_data':
            return "Weather data unavailable"
        
        wind_speed = wind_analysis.get('wind_speed_kph', 0)
        wind_dir = wind_analysis.get('wind_direction_deg', 0)
        first_half = wind_analysis.get('first_half_score', 0.5)
        second_half = wind_analysis.get('second_half_score', 0.5)
        recommendation = wind_analysis.get('recommendation', '')
        
        # Convert wind direction to compass direction
        compass_dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                       'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        compass_idx = int((wind_dir + 11.25) / 22.5) % 16
        compass_dir = compass_dirs[compass_idx]
        
        # Build description
        parts = [
            f"Wind: {wind_speed:.1f} km/h from {compass_dir} ({wind_dir:.0f}°)",
            f"First half score: {first_half:.2f} | Second half score: {second_half:.2f}",
            recommendation
        ]
        
        # Add segment details if available
        segments = wind_analysis.get('segments', [])
        if segments:
            segment_summary = []
            for seg in segments:
                wind_type = seg['wind_type'].replace('_', ' ').title()
                segment_summary.append(f"Seg {seg['segment']}: {wind_type}")
            
            if len(segment_summary) <= 4:
                parts.append(" | ".join(segment_summary))
            else:
                # Show first 2 and last 2 segments
                parts.append(" | ".join(segment_summary[:2] + ['...'] + segment_summary[-2:]))
        
        return "\n".join(parts)
    
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
            weather_data = self.weather_fetcher.get_current_conditions(clicked_lat, clicked_lon)
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
            
            # Calculate wind score and detailed analysis
            if weather_data:
                wind_score, wind_analysis = self.calculate_wind_score(ride, weather_data)
            else:
                wind_score = 0.5
                wind_analysis = {'status': 'no_weather_data'}
            
            # Assess precipitation risk
            if weather_data:
                precip_mm = weather_data.get('precipitation_mm', 0)
                if precip_mm > 5:
                    precipitation_risk = "high"
                elif precip_mm > 2:
                    precipitation_risk = "medium"
                elif precip_mm > 0:
                    precipitation_risk = "low"
                else:
                    precipitation_risk = "none"
            else:
                precipitation_risk = "unknown"
            
            # Filter by target duration/distance if specified
            if target_duration_hours and abs(ride.duration_hours - target_duration_hours) > 1.0:
                continue
            if target_distance_km and abs(ride.distance_km - target_distance_km) > 10:
                continue
            
            # Build enhanced route description with wind info
            wind_desc = wind_analysis.get('recommendation', 'Wind conditions analyzed')
            route_desc = (
                f"{ride.distance_km:.1f}km, {ride.duration_hours:.1f}h | "
                f"Wind score: {wind_score:.2f} | {wind_desc}"
            )
            
            recommendation = RideRecommendation(
                ride=ride,
                distance_to_location=min_distance,
                weather_score=wind_score,
                precipitation_risk=precipitation_risk,
                route_description=route_desc,
                wind_analysis=wind_analysis
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