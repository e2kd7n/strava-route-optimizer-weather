"""
Route analysis module.

Extracts, groups, and analyzes route variants between home and work.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field

import numpy as np
from scipy.spatial.distance import directed_hausdorff
from geopy.distance import geodesic
import polyline

from .data_fetcher import Activity
from .location_finder import Location
from .route_namer import RouteNamer

logger = logging.getLogger(__name__)


@dataclass
class Route:
    """Represents a single route."""
    activity_id: int
    direction: str  # "home_to_work" or "work_to_home"
    coordinates: List[Tuple[float, float]]
    distance: float  # meters
    duration: int  # seconds
    elevation_gain: float  # meters
    timestamp: str  # ISO format
    average_speed: float  # m/s


@dataclass
class RouteGroup:
    """Represents a group of similar routes."""
    id: str
    direction: str
    routes: List[Route]
    representative_route: Route
    frequency: int
    name: Optional[str] = None
    
    
@dataclass
class RouteMetrics:
    """Metrics for a route group."""
    avg_duration: float  # seconds
    std_duration: float
    avg_distance: float  # meters
    avg_speed: float  # m/s
    avg_elevation: float  # meters
    consistency_score: float  # 0-1, higher is more consistent
    usage_frequency: int


class RouteAnalyzer:
    """Analyzes and groups routes between home and work."""
    
    def __init__(self, activities: List[Activity], home: Location,
                 work: Location, config):
        """
        Initialize route analyzer.
        
        Args:
            activities: List of Activity objects
            home: Home location
            work: Work location
            config: Configuration object
        """
        self.activities = activities
        self.home = home
        self.work = work
        self.config = config
        self.similarity_threshold = config.get('route_analysis.similarity_threshold', 0.85)
        self.route_namer = RouteNamer(config)
        
    def extract_routes(self, direction: str = 'both') -> List[Route]:
        """
        Extract routes between home and work.
        
        Args:
            direction: 'home_to_work', 'work_to_home', or 'both'
            
        Returns:
            List of Route objects
        """
        routes = []
        
        for activity in self.activities:
            if not activity.polyline:
                continue
            
            # Determine route direction
            route_direction = self._determine_direction(activity)
            
            if route_direction is None:
                continue
            
            if direction != 'both' and route_direction != direction:
                continue
            
            # Decode polyline
            try:
                coordinates = polyline.decode(activity.polyline)
            except Exception as e:
                logger.warning(f"Failed to decode polyline for activity {activity.id}: {e}")
                continue
            
            # Create route object
            route = Route(
                activity_id=activity.id,
                direction=route_direction,
                coordinates=coordinates,
                distance=activity.distance,
                duration=activity.moving_time,
                elevation_gain=activity.total_elevation_gain,
                timestamp=activity.start_date,
                average_speed=activity.average_speed
            )
            
            routes.append(route)
        
        logger.info(f"Extracted {len(routes)} routes (direction: {direction})")
        
        return routes
    
    def _determine_direction(self, activity: Activity) -> str:
        """
        Determine if route is home-to-work or work-to-home.
        
        Args:
            activity: Activity object
            
        Returns:
            'home_to_work', 'work_to_home', or None
        """
        if not activity.start_latlng or not activity.end_latlng:
            return None
        
        # Calculate distances
        start_to_home = geodesic(activity.start_latlng, (self.home.lat, self.home.lon)).meters
        start_to_work = geodesic(activity.start_latlng, (self.work.lat, self.work.lon)).meters
        end_to_home = geodesic(activity.end_latlng, (self.home.lat, self.home.lon)).meters
        end_to_work = geodesic(activity.end_latlng, (self.work.lat, self.work.lon)).meters
        
        # Use larger radius for matching (500m)
        max_distance = 500
        
        # Check if starts near home and ends near work
        if start_to_home < max_distance and end_to_work < max_distance:
            return 'home_to_work'
        
        # Check if starts near work and ends near home
        if start_to_work < max_distance and end_to_home < max_distance:
            return 'work_to_home'
        
        return None
    
    def calculate_route_similarity(self, route1: Route, route2: Route) -> float:
        """
        Calculate similarity between two routes using Hausdorff distance.
        
        Args:
            route1: First route
            route2: Second route
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        coords1 = np.array(route1.coordinates)
        coords2 = np.array(route2.coordinates)
        
        # Calculate Hausdorff distance in both directions
        dist_forward = directed_hausdorff(coords1, coords2)[0]
        dist_backward = directed_hausdorff(coords2, coords1)[0]
        
        # Use maximum distance
        max_dist = max(dist_forward, dist_backward)
        
        # Convert degrees to meters (approximate)
        normalized_dist = max_dist * 111000
        
        # Convert to similarity score (0-1)
        # Use configurable distance threshold
        # With threshold=0.65, routes within ~500m get similarity >= 0.65
        distance_threshold = 500  # meters - routes within this distance are considered similar
        similarity = 1 / (1 + normalized_dist / distance_threshold)
        
        return similarity
    
    def group_similar_routes(self, routes: List[Route] = None) -> List[RouteGroup]:
        """
        Group similar routes together.
        
        Args:
            routes: List of routes to group (if None, extracts all routes)
            
        Returns:
            List of RouteGroup objects
        """
        if routes is None:
            routes = self.extract_routes()
        
        if not routes:
            logger.warning("No routes to group")
            return []
        
        # Separate by direction
        home_to_work = [r for r in routes if r.direction == 'home_to_work']
        work_to_home = [r for r in routes if r.direction == 'work_to_home']
        
        # Group each direction separately
        groups = []
        
        if home_to_work:
            htw_groups = self._group_routes_by_similarity(home_to_work, 'home_to_work')
            groups.extend(htw_groups)
        
        if work_to_home:
            wth_groups = self._group_routes_by_similarity(work_to_home, 'work_to_home')
            groups.extend(wth_groups)
        
        logger.info(f"Created {len(groups)} route groups from {len(routes)} routes")
        
        return groups
    
    def _group_routes_by_similarity(self, routes: List[Route], direction: str) -> List[RouteGroup]:
        """
        Group routes by similarity using threshold-based clustering.
        
        Args:
            routes: List of routes
            direction: Route direction
            
        Returns:
            List of RouteGroup objects
        """
        if not routes:
            return []
        
        groups = []
        ungrouped = routes.copy()
        group_id = 0
        
        while ungrouped:
            # Start new group with first ungrouped route
            current = ungrouped.pop(0)
            group = [current]
            
            # Find similar routes
            to_remove = []
            for i, route in enumerate(ungrouped):
                similarity = self.calculate_route_similarity(current, route)
                if similarity >= self.similarity_threshold:
                    group.append(route)
                    to_remove.append(i)
            
            # Remove grouped routes
            for i in reversed(to_remove):
                ungrouped.pop(i)
            
            # Create route group
            representative = self._select_representative_route(group)
            
            # Generate descriptive name for the route
            route_id = f"{direction}_{group_id}"
            route_name = self.route_namer.name_route(
                representative.coordinates,
                route_id,
                direction
            )
            
            route_group = RouteGroup(
                id=route_id,
                direction=direction,
                routes=group,
                representative_route=representative,
                frequency=len(group),
                name=route_name
            )
            
            groups.append(route_group)
            group_id += 1
        
        # Sort by frequency
        groups.sort(key=lambda g: g.frequency, reverse=True)
        
        return groups
    
    def _select_representative_route(self, routes: List[Route]) -> Route:
        """
        Select representative route from group (median by duration).
        
        Args:
            routes: List of routes in group
            
        Returns:
            Representative Route object
        """
        # Sort by duration
        sorted_routes = sorted(routes, key=lambda r: r.duration)
        
        # Return median route
        median_idx = len(sorted_routes) // 2
        return sorted_routes[median_idx]
    
    def calculate_route_metrics(self, route_group: RouteGroup) -> RouteMetrics:
        """
        Calculate metrics for a route group.
        
        Args:
            route_group: RouteGroup object
            
        Returns:
            RouteMetrics object
        """
        routes = route_group.routes
        
        # Calculate averages
        durations = [r.duration for r in routes]
        distances = [r.distance for r in routes]
        speeds = [r.average_speed for r in routes]
        elevations = [r.elevation_gain for r in routes]
        
        avg_duration = np.mean(durations)
        std_duration = np.std(durations)
        avg_distance = np.mean(distances)
        avg_speed = np.mean(speeds)
        avg_elevation = np.mean(elevations)
        
        # Calculate consistency score (1 - coefficient of variation)
        if avg_duration > 0:
            cv = std_duration / avg_duration
            consistency_score = max(0, 1 - cv)
        else:
            consistency_score = 0
        
        return RouteMetrics(
            avg_duration=avg_duration,
            std_duration=std_duration,
            avg_distance=avg_distance,
            avg_speed=avg_speed,
            avg_elevation=avg_elevation,
            consistency_score=consistency_score,
            usage_frequency=len(routes)
        )
    
    def get_route_statistics(self, route_group: RouteGroup) -> Dict[str, Any]:
        """
        Get detailed statistics for a route group.
        
        Args:
            route_group: RouteGroup object
            
        Returns:
            Dictionary of statistics
        """
        metrics = self.calculate_route_metrics(route_group)
        
        return {
            'id': route_group.id,
            'direction': route_group.direction,
            'frequency': route_group.frequency,
            'avg_duration_min': metrics.avg_duration / 60,
            'std_duration_min': metrics.std_duration / 60,
            'avg_distance_km': metrics.avg_distance / 1000,
            'avg_speed_kmh': metrics.avg_speed * 3.6,
            'avg_elevation_m': metrics.avg_elevation,
            'consistency_score': metrics.consistency_score
        }

# Made with Bob
