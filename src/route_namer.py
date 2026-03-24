"""
Route naming module.

Generates human-readable route names based on streets, neighborhoods, landmarks,
and geographic features to clearly indicate where routes actually go.
"""

import logging
from typing import List, Tuple, Optional, Dict, Set
from collections import Counter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import json
import os

logger = logging.getLogger(__name__)


class RouteNamer:
    """Generates descriptive names for routes based on geographic features."""
    
    def __init__(self, config=None):
        """
        Initialize route namer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        # Initialize with 10-second timeout to handle slow Nominatim responses
        self.geolocator = Nominatim(user_agent="strava_commute_analyzer", timeout=10)
        
        # Set up persistent cache
        self.cache_dir = "cache"
        self.cache_file = os.path.join(self.cache_dir, "geocoding_cache.json")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load cache from disk
        self.cache = self._load_cache()
        logger.info(f"Loaded {len(self.cache)} geocoding entries from cache")
    
    def _load_cache(self) -> Dict:
        """Load geocoding cache from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load geocoding cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save geocoding cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save geocoding cache: {e}")
    
    def name_route(self, coordinates: List[Tuple[float, float]],
                   route_id: str, direction: str) -> str:
        """
        Generate a descriptive name for a route using multi-strategy approach:
        1. Major streets (most significant roads along route)
        2. Neighborhoods/districts traversed
        3. Landmarks when available
        4. Geographic features (rivers, parks, etc.)
        
        Args:
            coordinates: List of (lat, lon) tuples
            route_id: Original route ID
            direction: Route direction
            
        Returns:
            Human-readable route name that clearly indicates where route goes
        """
        # Check if geocoding is disabled in config
        if self.config and not self.config.get('route_analysis.enable_geocoding', True):
            direction_label = "to Work" if direction == "home_to_work" else "to Home"
            route_num = route_id.split('_')[-1]
            return f"Route {route_num} {direction_label}"
        
        try:
            # Multi-strategy naming approach
            route_info = self._analyze_route_geography(coordinates)
            
            # Generate name based on available information
            name = self._generate_descriptive_name(route_info, route_id, direction)
            
            logger.info(f"Named route {route_id}: {name}")
            return name
            
        except Exception as e:
            logger.warning(f"Failed to name route {route_id}: {e}")
            # Fallback to generic name
            direction_label = "to Work" if direction == "home_to_work" else "to Home"
            return f"Route {route_id.split('_')[-1]} {direction_label}"
    
    def _analyze_route_geography(self, coordinates: List[Tuple[float, float]]) -> Dict:
        """
        Analyze route geography to extract naming information.
        
        Returns dict with:
        - major_streets: List of significant streets (not every small street)
        - neighborhoods: List of neighborhoods/districts traversed
        - landmarks: List of notable landmarks
        - geographic_features: Parks, rivers, etc.
        """
        if not coordinates:
            return {}
        
        # Sample strategic points along route
        sample_points = self._get_strategic_sample_points(coordinates)
        
        # Collect geographic information
        streets = []
        neighborhoods = set()
        landmarks = []
        features = []
        
        for point in sample_points:
            location_info = self._get_location_details(point)
            
            if location_info:
                # Collect major streets (highways, primary roads)
                if location_info.get('street') and location_info.get('is_major'):
                    streets.append(location_info['street'])
                
                # Collect neighborhoods
                if location_info.get('neighborhood'):
                    neighborhoods.add(location_info['neighborhood'])
                
                # Collect landmarks
                if location_info.get('landmark'):
                    landmarks.append(location_info['landmark'])
                
                # Collect geographic features
                if location_info.get('feature'):
                    features.append(location_info['feature'])
        
        return {
            'major_streets': self._filter_significant_streets(streets),
            'neighborhoods': list(neighborhoods),
            'landmarks': landmarks[:2],  # Limit to 2 most prominent
            'geographic_features': features[:1]  # Limit to 1 most prominent
        }
    
    def _get_strategic_sample_points(self, coordinates: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Get strategic sample points along route for naming.
        Focuses on start, key waypoints, and end.
        """
        if len(coordinates) < 3:
            return coordinates
        
        # Always include start and end
        points = [coordinates[0], coordinates[-1]]
        
        # Add points at 25%, 50%, 75% of route
        for pct in [0.25, 0.5, 0.75]:
            idx = int(len(coordinates) * pct)
            points.append(coordinates[idx])
        
        return points
    
    def _get_location_details(self, point: Tuple[float, float]) -> Optional[Dict]:
        """
        Get detailed location information for a point.
        
        Returns dict with street, neighborhood, landmark, feature, and is_major flag.
        """
        # Check cache first
        cache_key = f"details_{point[0]:.4f},{point[1]:.4f}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]
        
        # Rate limiting for API requests
        logger.debug(f"Cache miss for {cache_key}, making API request")
        time.sleep(1.0)
        
        try:
            location = self.geolocator.reverse(point, exactly_one=True, language='en', timeout=5)
            
            if not location or not location.raw.get('address'):
                return None
            
            address = location.raw['address']
            
            # Extract street information
            street = (address.get('road') or
                     address.get('street') or
                     address.get('cycleway') or
                     address.get('path'))
            
            # Determine if this is a major street
            is_major = self._is_major_street(address)
            
            # Extract neighborhood
            neighborhood = (address.get('neighbourhood') or
                          address.get('suburb') or
                          address.get('quarter') or
                          address.get('district') or
                          address.get('city_district'))
            
            # Extract landmarks
            landmark = (address.get('amenity') or
                       address.get('tourism') or
                       address.get('historic'))
            
            # Extract geographic features
            feature = (address.get('natural') or
                      address.get('water') or
                      address.get('waterway') or
                      address.get('leisure'))
            
            result = {
                'street': street,
                'is_major': is_major,
                'neighborhood': neighborhood,
                'landmark': landmark,
                'feature': feature
            }
            
            # Cache and save
            self.cache[cache_key] = result
            self._save_cache()
            logger.info(f"Geocoded {cache_key} -> {result}")
            
            return result
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.debug(f"Geocoding failed for {point}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error geocoding {point}: {e}")
        
        return None
    
    def _is_major_street(self, address: Dict) -> bool:
        """Determine if a street is major (highway, primary, secondary road)."""
        # Check for highway classification
        highway_type = address.get('highway')
        if highway_type in ['motorway', 'trunk', 'primary', 'secondary', 'tertiary']:
            return True
        
        # Check for named major roads (often have route numbers)
        road = address.get('road', '')
        if any(keyword in road.lower() for keyword in ['highway', 'boulevard', 'avenue', 'parkway']):
            return True
        
        return False
    
    def _filter_significant_streets(self, streets: List[str]) -> List[str]:
        """
        Filter to most significant streets (remove duplicates, keep most frequent).
        Returns up to 3 most significant streets.
        """
        if not streets:
            return []
        
        # Count occurrences
        street_counts = Counter(streets)
        
        # Get top 3 most common
        top_streets = [street for street, count in street_counts.most_common(3)]
        
        return top_streets
    
    def _generate_descriptive_name(self, route_info: Dict, route_id: str, direction: str) -> str:
        """
        Generate descriptive name from route information.
        
        Priority:
        1. Major streets (if 2-3 available): "Street A → Street B"
        2. Neighborhood + major street: "Through [Neighborhood] via [Street]"
        3. Landmark + street: "Past [Landmark] on [Street]"
        4. Geographic feature: "Along [River/Park]"
        5. Fallback: Generic name
        """
        major_streets = route_info.get('major_streets', [])
        neighborhoods = route_info.get('neighborhoods', [])
        landmarks = route_info.get('landmarks', [])
        features = route_info.get('geographic_features', [])
        
        # Strategy 1: Multiple major streets (shows clear path)
        if len(major_streets) >= 2:
            if len(major_streets) == 2:
                return f"{major_streets[0]} → {major_streets[1]}"
            else:
                return f"{major_streets[0]} → {major_streets[1]} → {major_streets[2]}"
        
        # Strategy 2: Single major street with neighborhood
        if len(major_streets) == 1 and neighborhoods:
            return f"Through {neighborhoods[0]} via {major_streets[0]}"
        
        # Strategy 3: Neighborhood with landmark
        if neighborhoods and landmarks:
            return f"Through {neighborhoods[0]} past {landmarks[0]}"
        
        # Strategy 4: Major street with geographic feature
        if major_streets and features:
            return f"{major_streets[0]} along {features[0]}"
        
        # Strategy 5: Just major street
        if major_streets:
            return f"Via {major_streets[0]}"
        
        # Strategy 6: Just neighborhood
        if neighborhoods:
            if len(neighborhoods) >= 2:
                return f"Through {neighborhoods[0]} and {neighborhoods[1]}"
            else:
                return f"Through {neighborhoods[0]}"
        
        # Strategy 7: Geographic feature
        if features:
            return f"Along {features[0]}"
        
        # Fallback: Generic name with direction
        direction_label = "to Work" if direction == "home_to_work" else "to Home"
        route_num = route_id.split('_')[-1]
        return f"Route {route_num} {direction_label}"
    
    def _get_street_name(self, point: Tuple[float, float]) -> Optional[str]:
        """
        Get street name for a point using reverse geocoding.
        (Legacy method - kept for compatibility)
        
        Args:
            point: (lat, lon) tuple
            
        Returns:
            Street name or None
        """
        # Check cache first
        cache_key = f"{point[0]:.4f},{point[1]:.4f}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]
        
        # Rate limiting for API requests
        logger.debug(f"Cache miss for {cache_key}, making API request")
        time.sleep(1.0)
        
        try:
            location = self.geolocator.reverse(point, exactly_one=True, language='en', timeout=5)
            
            if location and location.raw.get('address'):
                address = location.raw['address']
                
                street = (address.get('road') or
                         address.get('street') or
                         address.get('cycleway') or
                         address.get('path') or
                         address.get('footway') or
                         address.get('highway'))
                
                # Cache and save
                self.cache[cache_key] = street
                self._save_cache()
                logger.info(f"Geocoded {cache_key} -> {street}")
                return street
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.debug(f"Geocoding failed for {point}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error geocoding {point}: {e}")
        
        return None
    
    def generate_simple_name(self, route_id: str, direction: str, 
                           rank: int = None) -> str:
        """
        Generate a simple name without geocoding.
        
        Args:
            route_id: Original route ID
            direction: Route direction
            rank: Optional rank number
            
        Returns:
            Simple route name
        """
        direction_label = "to Work" if direction == "home_to_work" else "to Home"
        
        if rank is not None:
            if rank == 1:
                return f"Primary Route {direction_label}"
            elif rank == 2:
                return f"Alternative Route {direction_label}"
            else:
                return f"Route {rank} {direction_label}"
        else:
            route_num = route_id.split('_')[-1]
            return f"Route {route_num} {direction_label}"


# Made with Bob