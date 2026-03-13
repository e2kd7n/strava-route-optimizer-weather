"""
Route naming module.

Generates human-readable route names based on streets and geographic features.
"""

import logging
from typing import List, Tuple, Optional, Dict
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
        Generate a descriptive name for a route based on:
        1. First street/trail taken
        2. Street/trail that represents the majority of the route
        3. Neighborhood name if there are many streets
        
        Args:
            coordinates: List of (lat, lon) tuples
            route_id: Original route ID
            direction: Route direction
            
        Returns:
            Human-readable route name
        """
        # Check if geocoding is disabled in config
        if self.config and not self.config.get('route_analysis.enable_geocoding', True):
            direction_label = "to Work" if direction == "home_to_work" else "to Home"
            route_num = route_id.split('_')[-1]
            return f"Route {route_num} {direction_label}"
        
        try:
            # Get first street (near start of route)
            first_street = self._get_first_street(coordinates)
            
            # Get all streets along the route
            all_streets = self._get_all_streets(coordinates)
            
            # Find the dominant street (most frequent)
            dominant_street = self._get_dominant_street(all_streets)
            
            # Check if route has many different streets (fragmented)
            is_fragmented = len(set(all_streets)) > 8
            
            # Generate name based on what we found
            if is_fragmented:
                # Use neighborhood name if too many streets
                neighborhood = self._get_neighborhood(coordinates)
                if neighborhood and first_street:
                    name = f"{first_street} via {neighborhood}"
                elif neighborhood:
                    name = f"Via {neighborhood}"
                elif first_street and dominant_street and first_street != dominant_street:
                    name = f"{first_street} → {dominant_street}"
                elif first_street:
                    name = f"Via {first_street}"
                else:
                    direction_label = "to Work" if direction == "home_to_work" else "to Home"
                    name = f"Route {route_id.split('_')[-1]} {direction_label}"
            else:
                # Use first street and dominant street
                if first_street and dominant_street and first_street != dominant_street:
                    name = f"{first_street} → {dominant_street}"
                elif dominant_street:
                    name = f"Via {dominant_street}"
                elif first_street:
                    name = f"Via {first_street}"
                else:
                    direction_label = "to Work" if direction == "home_to_work" else "to Home"
                    name = f"Route {route_id.split('_')[-1]} {direction_label}"
            
            logger.info(f"Named route {route_id}: {name}")
            return name
            
        except Exception as e:
            logger.warning(f"Failed to name route {route_id}: {e}")
            # Fallback to generic name
            direction_label = "to Work" if direction == "home_to_work" else "to Home"
            return f"Route {route_id.split('_')[-1]} {direction_label}"
    
    def _get_first_street(self, coordinates: List[Tuple[float, float]]) -> Optional[str]:
        """
        Get the first street/trail name near the start of the route.
        
        Args:
            coordinates: List of (lat, lon) tuples
            
        Returns:
            First street name or None
        """
        if len(coordinates) < 2:
            return None
        
        # Check first few points (within first 10% of route)
        sample_size = max(2, len(coordinates) // 10)
        for i in range(min(sample_size, len(coordinates))):
            street = self._get_street_name(coordinates[i])
            if street:
                return street
        
        return None
    
    def _get_all_streets(self, coordinates: List[Tuple[float, float]],
                         sample_rate: int = 10) -> List[str]:
        """
        Get all street names along the route.
        
        Args:
            coordinates: List of (lat, lon) tuples
            sample_rate: Sample every Nth point
            
        Returns:
            List of street names
        """
        streets = []
        
        # Sample points along the route
        for i in range(0, len(coordinates), sample_rate):
            street = self._get_street_name(coordinates[i])
            if street:
                streets.append(street)
        
        return streets
    
    def _get_dominant_street(self, streets: List[str]) -> Optional[str]:
        """
        Find the street that appears most frequently (represents majority of route).
        
        Args:
            streets: List of street names
            
        Returns:
            Most common street name or None
        """
        if not streets:
            return None
        
        # Count occurrences
        street_counts = Counter(streets)
        
        # Return most common
        most_common = street_counts.most_common(1)
        if most_common:
            return most_common[0][0]
        
        return None
    
    def _get_neighborhood(self, coordinates: List[Tuple[float, float]]) -> Optional[str]:
        """
        Get neighborhood name for the route.
        
        Args:
            coordinates: List of (lat, lon) tuples
            
        Returns:
            Neighborhood name or None
        """
        if not coordinates:
            return None
        
        # Use midpoint of route
        mid_idx = len(coordinates) // 2
        point = coordinates[mid_idx]
        
        # Check cache first - return immediately if found
        cache_key = f"neighborhood_{point[0]:.4f},{point[1]:.4f}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]
        
        # Rate limiting ONLY for actual API requests (1 second per Nominatim usage policy)
        logger.debug(f"Cache miss for {cache_key}, making API request")
        time.sleep(1.0)
        
        try:
            # Reverse geocode
            location = self.geolocator.reverse(point, exactly_one=True, language='en', timeout=5)
            
            if location and location.raw.get('address'):
                address = location.raw['address']
                
                # Try to get neighborhood or suburb
                neighborhood = (address.get('neighbourhood') or
                              address.get('suburb') or
                              address.get('quarter') or
                              address.get('district'))
                
                # Cache result and save to disk
                self.cache[cache_key] = neighborhood
                self._save_cache()
                logger.info(f"Geocoded {cache_key} -> {neighborhood}")
                return neighborhood
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.debug(f"Geocoding failed for {point}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error geocoding {point}: {e}")
        
        return None
    
    def _get_street_name(self, point: Tuple[float, float]) -> Optional[str]:
        """
        Get street name for a point using reverse geocoding.
        
        Args:
            point: (lat, lon) tuple
            
        Returns:
            Street name or None
        """
        # Check cache first - return immediately if found
        cache_key = f"{point[0]:.4f},{point[1]:.4f}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]
        
        # Rate limiting ONLY for actual API requests (1 second per Nominatim usage policy)
        logger.debug(f"Cache miss for {cache_key}, making API request")
        time.sleep(1.0)
        
        try:
            # Reverse geocode
            location = self.geolocator.reverse(point, exactly_one=True, language='en', timeout=5)
            
            if location and location.raw.get('address'):
                address = location.raw['address']
                
                # Try to get street name (including trails/paths)
                street = (address.get('road') or
                         address.get('street') or
                         address.get('cycleway') or
                         address.get('path') or
                         address.get('footway') or
                         address.get('highway'))
                
                # Cache result and save to disk
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