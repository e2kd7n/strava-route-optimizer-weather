"""
Route analysis module.

Extracts, groups, and analyzes route variants between home and work.

Copyright (c) 2024-2026 e2kd7n
Licensed under the MIT License - see LICENSE file for details.
"""

import logging
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, asdict

import numpy as np
from scipy.spatial.distance import directed_hausdorff
from geopy.distance import geodesic
import polyline
from tqdm import tqdm

from .data_fetcher import Activity
from .location_finder import Location
from .route_namer import RouteNamer

logger = logging.getLogger(__name__)

try:
    import similaritymeasures
    FRECHET_AVAILABLE = True
except ImportError:
    FRECHET_AVAILABLE = False
    logger.warning("similaritymeasures not available, using Hausdorff distance only")


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
    is_plus_route: bool = False  # True if distance is >25% above median


@dataclass
class RouteGroup:
    """Represents a group of similar routes."""
    id: str
    direction: str
    routes: List[Route]
    representative_route: Route
    frequency: int
    name: Optional[str] = None
    is_plus_route: bool = False  # True if this is a "plus route" group
    
    
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
                 work: Location, config, n_workers=2, force_reanalysis=False):
        """
        Initialize route analyzer.
        
        Args:
            activities: List of Activity objects
            home: Home location
            work: Work location
            config: Configuration object
            n_workers: Number of parallel workers for route grouping (1-8)
            force_reanalysis: If True, clear cache and reprocess all routes
        """
        self.activities = activities
        self.home = home
        self.work = work
        self.config = config
        self.n_workers = max(1, min(8, n_workers))  # Clamp between 1 and 8
        self.similarity_threshold = config.get('route_analysis.similarity_threshold', 0.85)
        self.route_namer = RouteNamer(config)
        self.force_reanalysis = force_reanalysis
        
        # Initialize caches
        self.cache_dir = Path('cache')
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / 'route_similarity_cache.json'
        self.similarity_cache = self._load_similarity_cache()
        
        # Route grouping cache
        self.groups_cache_file = self.cache_dir / 'route_groups_cache.json'
        
        # Clear cache if force reanalysis
        if force_reanalysis and self.groups_cache_file.exists():
            tqdm.write("   🗑️  Clearing route groups cache (force reanalysis)")
            self.groups_cache_file.unlink()
            self.groups_cache = {}
        else:
            self.groups_cache = self._load_groups_cache()
        
    def _load_similarity_cache(self) -> Dict[str, float]:
        """Load similarity cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                logger.info(f"Loaded {len(cache)} cached similarity calculations")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load similarity cache: {e}")
                return {}
        return {}
    
    def _save_similarity_cache(self):
        """Save similarity cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.similarity_cache, f)
            logger.info(f"Saved {len(self.similarity_cache)} similarity calculations to cache")
        except Exception as e:
            logger.warning(f"Failed to save similarity cache: {e}")
    
    def _load_groups_cache(self) -> Dict[str, Any]:
        """Load route groups cache from disk."""
        if self.groups_cache_file.exists():
            try:
                with open(self.groups_cache_file, 'r') as f:
                    cache = json.load(f)
                logger.info(f"Loaded route groups cache (key: {cache.get('cache_key', 'unknown')[:8]}...)")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load groups cache: {e}")
                return {}
        return {}
    
    def _save_groups_cache(self, cache_key: str, groups: List[RouteGroup]):
        """Save route groups cache to disk (legacy method)."""
        # Extract activity IDs from groups
        activity_ids = []
        for group in groups:
            for route in group.routes:
                if route.activity_id not in activity_ids:
                    activity_ids.append(route.activity_id)
        self._save_groups_cache_with_ids(activity_ids, groups)
    
    def _save_groups_cache_with_ids(self, activity_ids: List[int], groups: List[RouteGroup]):
        """Save route groups cache to disk with activity ID tracking."""
        try:
            # Serialize groups to JSON-compatible format
            serialized_groups = []
            for group in groups:
                serialized_group = {
                    'id': group.id,
                    'direction': group.direction,
                    'frequency': group.frequency,
                    'name': group.name,
                    'is_plus_route': group.is_plus_route,
                    'representative_route': {
                        'activity_id': group.representative_route.activity_id,
                        'direction': group.representative_route.direction,
                        'coordinates': group.representative_route.coordinates,
                        'distance': group.representative_route.distance,
                        'duration': group.representative_route.duration,
                        'elevation_gain': group.representative_route.elevation_gain,
                        'timestamp': group.representative_route.timestamp,
                        'average_speed': group.representative_route.average_speed,
                        'is_plus_route': group.representative_route.is_plus_route
                    },
                    'routes': [
                        {
                            'activity_id': r.activity_id,
                            'direction': r.direction,
                            'coordinates': r.coordinates,
                            'distance': r.distance,
                            'duration': r.duration,
                            'elevation_gain': r.elevation_gain,
                            'timestamp': r.timestamp,
                            'average_speed': r.average_speed,
                            'is_plus_route': r.is_plus_route
                        }
                        for r in group.routes
                    ]
                }
                serialized_groups.append(serialized_group)
            
            cache_data = {
                'activity_ids': activity_ids,
                'groups': serialized_groups,
                'similarity_threshold': self.similarity_threshold,
                'algorithm': 'frechet' if FRECHET_AVAILABLE else 'hausdorff',
                'timestamp': str(np.datetime64('now'))
            }
            
            with open(self.groups_cache_file, 'w') as f:
                json.dump(cache_data, f)
            logger.info(f"Saved {len(groups)} route groups to cache ({len(activity_ids)} activities)")
        except Exception as e:
            logger.warning(f"Failed to save groups cache: {e}")
    
    def _deserialize_groups(self, serialized_groups: List[Dict]) -> List[RouteGroup]:
        """Deserialize route groups from JSON format."""
        groups = []
        for sg in serialized_groups:
            # Deserialize representative route
            rep_data = sg['representative_route']
            representative = Route(
                activity_id=rep_data['activity_id'],
                direction=rep_data['direction'],
                coordinates=[(lat, lon) for lat, lon in rep_data['coordinates']],
                distance=rep_data['distance'],
                duration=rep_data['duration'],
                elevation_gain=rep_data['elevation_gain'],
                timestamp=rep_data['timestamp'],
                average_speed=rep_data['average_speed'],
                is_plus_route=rep_data['is_plus_route']
            )
            
            # Deserialize routes
            routes = []
            for r_data in sg['routes']:
                route = Route(
                    activity_id=r_data['activity_id'],
                    direction=r_data['direction'],
                    coordinates=[(lat, lon) for lat, lon in r_data['coordinates']],
                    distance=r_data['distance'],
                    duration=r_data['duration'],
                    elevation_gain=r_data['elevation_gain'],
                    timestamp=r_data['timestamp'],
                    average_speed=r_data['average_speed'],
                    is_plus_route=r_data['is_plus_route']
                )
                routes.append(route)
            
            # Create route group
            group = RouteGroup(
                id=sg['id'],
                direction=sg['direction'],
                routes=routes,
                representative_route=representative,
                frequency=sg['frequency'],
                name=sg['name'],
                is_plus_route=sg['is_plus_route']
            )
            groups.append(group)
        
        return groups
    
    def _generate_cache_key(self, routes: List[Route]) -> str:
        """
        Generate cache key based on route activity IDs and config.
        
        Args:
            routes: List of routes
            
        Returns:
            Cache key string
        """
        # Sort activity IDs for consistent key
        activity_ids = sorted([r.activity_id for r in routes])
        
        # Include similarity threshold and algorithm version in key
        key_data = {
            'activity_ids': activity_ids,
            'similarity_threshold': self.similarity_threshold,
            'algorithm': 'frechet' if FRECHET_AVAILABLE else 'hausdorff',
            'version': '2.0'  # Increment when algorithm changes
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _get_route_hash(self, route: Route) -> str:
        """
        Generate a unique hash for a route based on its coordinates.
        
        Args:
            route: Route object
            
        Returns:
            Hash string
        """
        # Create a string representation of coordinates (first, middle, last points)
        coords = route.coordinates
        if len(coords) > 10:
            # Sample points to keep hash manageable
            sample_coords = [coords[0], coords[len(coords)//4], coords[len(coords)//2],
                           coords[3*len(coords)//4], coords[-1]]
        else:
            sample_coords = coords
        
        coord_str = ','.join([f"{lat:.6f},{lon:.6f}" for lat, lon in sample_coords])
        return hashlib.sha256(coord_str.encode()).hexdigest()[:16]
    
    def _get_cache_key(self, route1: Route, route2: Route) -> str:
        """
        Generate cache key for a route pair.
        
        Args:
            route1: First route
            route2: Second route
            
        Returns:
            Cache key string
        """
        hash1 = self._get_route_hash(route1)
        hash2 = self._get_route_hash(route2)
        # Sort hashes to ensure same key regardless of order
        return f"{min(hash1, hash2)}_{max(hash1, hash2)}"
        
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
        Calculate similarity between two routes using Fréchet distance as primary metric.
        
        Fréchet distance is superior for route comparison because:
        - Considers the order of points (path similarity, like walking a dog)
        - Better captures whether routes follow the same path
        - More robust to GPS sampling differences
        
        Hausdorff is used as a secondary validation check.
        
        Results are cached to avoid expensive recalculations.
        
        Args:
            route1: First route
            route2: Second route
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Check cache first
        cache_key = self._get_cache_key(route1, route2)
        if cache_key in self.similarity_cache:
            logger.debug(f"Using cached similarity for {cache_key}")
            return self.similarity_cache[cache_key]
        
        # Calculate similarity
        coords1 = np.array(route1.coordinates)
        coords2 = np.array(route2.coordinates)
        
        # Calculate Fréchet distance (primary metric)
        if FRECHET_AVAILABLE:
            frechet_sim = self._calculate_frechet_similarity(coords1, coords2)
            
            # Calculate Hausdorff as secondary validation
            hausdorff_sim = self._calculate_hausdorff_similarity(coords1, coords2)
            
            # Use Fréchet as primary, but require Hausdorff to not strongly disagree
            # If Hausdorff is very low (<0.50), it indicates routes are spatially far apart
            if hausdorff_sim < 0.50:
                # Routes are too far apart spatially, reduce Fréchet score
                combined_similarity = frechet_sim * 0.7  # Penalize by 30%
                logger.debug(f"Fréchet: {frechet_sim:.3f}, Hausdorff: {hausdorff_sim:.3f} (spatial disagreement), Combined: {combined_similarity:.3f}")
            else:
                # Hausdorff agrees or is neutral, use Fréchet as-is
                combined_similarity = frechet_sim
                logger.debug(f"Fréchet: {frechet_sim:.3f} (primary), Hausdorff: {hausdorff_sim:.3f} (validates)")
        else:
            # Fallback to Hausdorff if Fréchet not available
            combined_similarity = self._calculate_hausdorff_similarity(coords1, coords2)
            logger.debug(f"Hausdorff only (Fréchet unavailable): {combined_similarity:.3f}")
        
        # Cache the result
        self.similarity_cache[cache_key] = combined_similarity
        
        return combined_similarity
    
    def _calculate_hausdorff_similarity(self, coords1: np.ndarray, coords2: np.ndarray) -> float:
        """
        Calculate similarity using percentile-based Hausdorff distance.
        
        Instead of using the maximum deviation (which is sensitive to outliers),
        uses the Nth percentile of deviations. This allows X% of points to be
        outliers (GPS glitches, brief detours) while still detecting substantive
        route differences.
        
        Args:
            coords1: First route coordinates
            coords2: Second route coordinates
            
        Returns:
            Similarity score (0-1)
        """
        from scipy.spatial.distance import cdist
        
        # Get percentile from config (default 95.0 = ignore worst 5% of deviations)
        percentile = self.config.get('route_analysis.outlier_tolerance_percentile', 95.0)
        
        # Distance from each point in coords1 to nearest point in coords2
        distances_1_to_2 = cdist(coords1, coords2).min(axis=1)
        
        # Distance from each point in coords2 to nearest point in coords1
        distances_2_to_1 = cdist(coords2, coords1).min(axis=1)
        
        # Use percentile instead of max to tolerate outliers
        percentile_dist_1 = np.percentile(distances_1_to_2, percentile)
        percentile_dist_2 = np.percentile(distances_2_to_1, percentile)
        
        # Take the larger of the two percentile distances
        percentile_dist = max(percentile_dist_1, percentile_dist_2)
        
        # Convert degrees to meters (approximate)
        # At Chicago's latitude (~42°), 1 degree ≈ 111km latitude, ~82km longitude
        # Using 111km as conservative estimate
        normalized_dist = percentile_dist * 111000
        
        # Convert to similarity score (0-1)
        # Routes are considered similar if percentile deviation is within 200m
        distance_threshold = 200  # meters
        similarity = 1 / (1 + normalized_dist / distance_threshold)
        
        return similarity
    
    def _calculate_frechet_similarity(self, coords1: np.ndarray, coords2: np.ndarray) -> float:
        """
        Calculate similarity using Fréchet distance.
        
        Fréchet distance considers the order of points, like walking a dog on a leash.
        It's better at detecting routes that follow the same path vs routes that are
        spatially close but follow different paths.
        
        Args:
            coords1: First route coordinates
            coords2: Second route coordinates
            
        Returns:
            Similarity score (0-1)
        """
        try:
            # Calculate Fréchet distance
            # Note: similaritymeasures expects (n, 2) arrays
            frechet_dist = similaritymeasures.frechet_dist(coords1, coords2)
            
            # Convert degrees to meters
            normalized_dist = frechet_dist * 111000
            
            # Convert to similarity score
            # Fréchet distance is typically larger than Hausdorff, so use larger threshold
            distance_threshold = 300  # meters - allow more variation for path-based comparison
            similarity = 1 / (1 + normalized_dist / distance_threshold)
            
            return similarity
            
        except Exception as e:
            logger.warning(f"Fréchet distance calculation failed: {e}, falling back to Hausdorff")
            return self._calculate_hausdorff_similarity(coords1, coords2)
    
    def group_similar_routes(self, routes: List[Route] = None) -> List[RouteGroup]:
        """
        Group similar routes with intelligent caching and incremental analysis.
        
        Uses cached groups when possible, only processes new routes incrementally,
        and only uses parallelism when beneficial (>100 new routes).
        
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
        
        # Check for cached groups
        if not self.force_reanalysis and self.groups_cache:
            cached_activity_ids = set(self.groups_cache.get('activity_ids', []))
            current_activity_ids = set(r.activity_id for r in routes)
            
            # Check if we can use incremental analysis
            new_activity_ids = current_activity_ids - cached_activity_ids
            removed_activity_ids = cached_activity_ids - current_activity_ids
            
            if not new_activity_ids and not removed_activity_ids:
                # Perfect cache hit - no changes
                tqdm.write("   💾 Using cached route groups (instant!)")
                cached_groups = self._deserialize_groups(self.groups_cache['groups'])
                logger.info(f"Loaded {len(cached_groups)} route groups from cache")
                return cached_groups
            
            elif new_activity_ids and not removed_activity_ids:
                # Incremental analysis - only new routes
                tqdm.write(f"   ⚡ Incremental analysis: {len(new_activity_ids)} new routes")
                new_routes = [r for r in routes if r.activity_id in new_activity_ids]
                cached_groups = self._deserialize_groups(self.groups_cache['groups'])
                
                # Merge new routes into existing groups
                updated_groups = self._merge_new_routes(cached_groups, new_routes)
                
                # Save updated cache
                all_activity_ids = list(current_activity_ids)
                self._save_groups_cache_with_ids(all_activity_ids, updated_groups)
                self._save_similarity_cache()
                
                return updated_groups
            
            else:
                # Routes removed or config changed - full reanalysis needed
                if removed_activity_ids:
                    tqdm.write(f"   🔄 Full reanalysis: {len(removed_activity_ids)} routes removed")
                else:
                    tqdm.write("   🔄 Full reanalysis: configuration changed")
        
        # Full analysis (no cache or force reanalysis)
        tqdm.write(f"   🔄 Full analysis: {len(routes)} routes")
        
        # Separate by direction
        home_to_work = [r for r in routes if r.direction == 'home_to_work']
        work_to_home = [r for r in routes if r.direction == 'work_to_home']
        
        # Sequential processing (parallel removed - adds overhead without benefit)
        groups = []
        
        if home_to_work:
            tqdm.write(f"   → Processing {len(home_to_work)} home→work routes")
            htw_groups = self._group_routes_by_similarity(home_to_work, 'home_to_work')
            groups.extend(htw_groups)
            tqdm.write(f"   ✓ {len(htw_groups)} groups")
        
        if work_to_home:
            tqdm.write(f"   → Processing {len(work_to_home)} work→home routes")
            wth_groups = self._group_routes_by_similarity(work_to_home, 'work_to_home')
            groups.extend(wth_groups)
            tqdm.write(f"   ✓ {len(wth_groups)} groups")
        
        tqdm.write(f"   Total: {len(groups)} groups")
        logger.info(f"Created {len(groups)} route groups from {len(routes)} routes")
        
        # Mark plus routes (routes >15% longer than median)
        groups = self._mark_plus_routes(groups)
        
        # Save to cache
        activity_ids = [r.activity_id for r in routes]
        self._save_groups_cache_with_ids(activity_ids, groups)
        
        # Save similarity cache after grouping
        self._save_similarity_cache()
        
        return groups
    
    def _merge_new_routes(self, existing_groups: List[RouteGroup],
                         new_routes: List[Route]) -> List[RouteGroup]:
        """
        Merge new routes into existing groups incrementally.
        
        Args:
            existing_groups: Existing route groups from cache
            new_routes: New routes to merge
            
        Returns:
            Updated list of route groups
        """
        if not new_routes:
            return existing_groups
        
        tqdm.write(f"   → Merging {len(new_routes)} new routes into {len(existing_groups)} groups")
        
        # Separate new routes by direction
        new_htw = [r for r in new_routes if r.direction == 'home_to_work']
        new_wth = [r for r in new_routes if r.direction == 'work_to_home']
        
        # Separate existing groups by direction
        htw_groups = [g for g in existing_groups if g.direction == 'home_to_work']
        wth_groups = [g for g in existing_groups if g.direction == 'work_to_home']
        
        # Merge each direction
        updated_groups = []
        
        if new_htw:
            updated_htw = self._merge_routes_into_groups(htw_groups, new_htw, 'home_to_work')
            updated_groups.extend(updated_htw)
            tqdm.write(f"   ✓ Merged into {len(updated_htw)} home→work groups")
        else:
            updated_groups.extend(htw_groups)
        
        if new_wth:
            updated_wth = self._merge_routes_into_groups(wth_groups, new_wth, 'work_to_home')
            updated_groups.extend(updated_wth)
            tqdm.write(f"   ✓ Merged into {len(updated_wth)} work→home groups")
        else:
            updated_groups.extend(wth_groups)
        
        # Re-mark plus routes after merge
        updated_groups = self._mark_plus_routes(updated_groups)
        
        return updated_groups
    
    def _merge_routes_into_groups(self, groups: List[RouteGroup],
                                  new_routes: List[Route],
                                  direction: str) -> List[RouteGroup]:
        """
        Merge new routes into existing groups for a specific direction.
        
        Args:
            groups: Existing route groups
            new_routes: New routes to merge
            direction: Route direction
            
        Returns:
            Updated list of route groups
        """
        if not new_routes:
            return groups
        
        # Try to match each new route to existing groups
        unmatched_routes = []
        
        for route in new_routes:
            matched = False
            best_similarity = 0
            best_group_idx = -1
            
            # Find best matching group
            for idx, group in enumerate(groups):
                similarity = self.calculate_route_similarity(
                    route, group.representative_route
                )
                if similarity >= self.similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_group_idx = idx
                    matched = True
            
            if matched:
                # Add to existing group
                groups[best_group_idx].routes.append(route)
                groups[best_group_idx].frequency += 1
                # Update representative if needed (keep median)
                groups[best_group_idx].representative_route = self._select_representative_route(
                    groups[best_group_idx].routes
                )
            else:
                unmatched_routes.append(route)
        
        # Create new groups for unmatched routes
        if unmatched_routes:
            new_groups = self._group_routes_by_similarity(unmatched_routes, direction)
            # Renumber new group IDs to avoid conflicts
            next_id = len(groups)
            for group in new_groups:
                group.id = f"{direction}_{next_id}"
                next_id += 1
            groups.extend(new_groups)
        
        # Re-sort by frequency
        groups.sort(key=lambda g: g.frequency, reverse=True)
        
        return groups
    
    def _mark_plus_routes(self, groups: List[RouteGroup]) -> List[RouteGroup]:
        """
        Mark route groups that are significantly longer than typical commutes.
        
        A "plus route" is one where the distance is >15% above the median distance
        for that direction (home_to_work or work_to_home).
        
        Args:
            groups: List of route groups
            
        Returns:
            Updated list of route groups with is_plus_route flag set
        """
        if not groups:
            return groups
        
        # Separate by direction
        htw_groups = [g for g in groups if g.direction == 'home_to_work']
        wth_groups = [g for g in groups if g.direction == 'work_to_home']
        
        # Calculate median distance for each direction
        for direction_groups in [htw_groups, wth_groups]:
            if not direction_groups:
                continue
            
            # Get all distances
            distances = []
            for group in direction_groups:
                for route in group.routes:
                    distances.append(route.distance)
            
            if not distances:
                continue
            
            # Calculate median
            median_distance = np.median(distances)
            threshold = median_distance * 1.15  # 15% above median
            
            direction = direction_groups[0].direction
            direction_label = direction.replace('_', '→')
            
            # Mark groups where representative route exceeds threshold
            plus_count = 0
            for group in direction_groups:
                if group.representative_route.distance > threshold:
                    group.is_plus_route = True
                    # Also mark individual routes
                    for route in group.routes:
                        if route.distance > threshold:
                            route.is_plus_route = True
                    plus_count += 1
            
            if plus_count > 0:
                tqdm.write(f"   ⭐ {plus_count} {direction_label} PLUS routes")
                tqdm.write(f"      (>{median_distance/1000:.1f}km + 15%)")
        
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
            
            # Generate route ID
            route_id = f"{direction}_{group_id}"
            
            # Generate descriptive route name using RouteNamer
            try:
                route_name = self.route_namer.name_route(
                    representative.coordinates,
                    route_id,
                    direction
                )
            except Exception as e:
                logger.warning(f"Failed to generate name for {route_id}, using fallback: {e}")
                route_name = f"Route {group_id}"
            
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
    
    @staticmethod
    def _group_routes_by_similarity_static(routes: List[Route], direction: str, 
                                          similarity_threshold: float,
                                          similarity_cache: Dict[str, float]) -> List[RouteGroup]:
        """
        Static method for parallel route grouping.
        
        This is a static method so it can be pickled for multiprocessing.
        
        Args:
            routes: List of routes to group
            direction: Route direction
            similarity_threshold: Similarity threshold for grouping
            similarity_cache: Cached similarity calculations
            
        Returns:
            List of RouteGroup objects
        """
        if not routes:
            return []
        
        groups = []
        ungrouped = routes.copy()
        group_id = 0
        
        # Helper function to calculate similarity (simplified for static context)
        def calc_similarity(route1: Route, route2: Route) -> float:
            # Check cache first
            cache_key = f"{route1.activity_id}_{route2.activity_id}"
            if cache_key in similarity_cache:
                return similarity_cache[cache_key]
            
            # Calculate Fréchet distance if available
            coords1 = np.array(route1.coordinates)
            coords2 = np.array(route2.coordinates)
            
            if FRECHET_AVAILABLE:
                try:
                    frechet_dist = similaritymeasures.frechet_dist(coords1, coords2)
                    normalized_dist = frechet_dist * 111000
                    distance_threshold = 200
                    similarity = 1 / (1 + normalized_dist / distance_threshold)
                    return similarity
                except (ValueError, IndexError, TypeError) as e:
                    logger.debug(f"Fréchet distance calculation failed, falling back to Hausdorff: {e}")
                    pass
            
            # Fallback to Hausdorff
            dist_forward = directed_hausdorff(coords1, coords2)[0]
            dist_backward = directed_hausdorff(coords2, coords1)[0]
            max_dist = max(dist_forward, dist_backward)
            normalized_dist = max_dist * 111000
            distance_threshold = 200
            similarity = 1 / (1 + normalized_dist / distance_threshold)
            return similarity
        
        while ungrouped:
            # Start new group with first ungrouped route
            current = ungrouped.pop(0)
            group = [current]
            
            # Find similar routes
            to_remove = []
            for i, route in enumerate(ungrouped):
                similarity = calc_similarity(current, route)
                if similarity >= similarity_threshold:
                    group.append(route)
                    to_remove.append(i)
            
            # Remove grouped routes
            for i in reversed(to_remove):
                ungrouped.pop(i)
            
            # Select representative route (median by duration)
            sorted_routes = sorted(group, key=lambda r: r.duration)
            representative = sorted_routes[len(sorted_routes) // 2]
            
            # Create route group
            route_id = f"{direction}_{group_id}"
            route_name = f"Route {group_id}"
            
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
