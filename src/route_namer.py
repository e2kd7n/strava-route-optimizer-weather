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
from datetime import datetime, timedelta

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
        
        # Load route naming configuration
        self.sampling_density = self.config.get('route_naming.sampling_density', 10) if config else 10
        self.min_segment_length_pct = self.config.get('route_naming.min_segment_length_pct', 10) if config else 10
        self.enable_segment_naming = self.config.get('route_naming.enable_segment_naming', True) if config else True
        self.show_full_path = self.config.get('route_naming.show_full_path', True) if config else True
        self.max_segments_in_name = self.config.get('route_naming.max_segments_in_name', 3) if config else 3
        
        # Load equivalent streets from config (parallel routes that should be treated as the same)
        default_equivalent_streets = {
            'North Simonds Drive': 'Lakefront Trail',
            'South Simonds Drive': 'Lakefront Trail',
            'Simonds Drive': 'Lakefront Trail',
        }
        self.equivalent_streets = self.config.get('route_naming.equivalent_streets', default_equivalent_streets) if config else default_equivalent_streets
        
        # Initialize geocoder with configurable settings
        geocoder_timeout = self.config.get('route_naming.geocoder_timeout', 10) if config else 10
        geocoder_user_agent = self.config.get('route_naming.geocoder_user_agent', 'strava_commute_analyzer') if config else 'strava_commute_analyzer'
        self.geolocator = Nominatim(user_agent=geocoder_user_agent, timeout=geocoder_timeout)
        
        # Set up persistent cache
        self.cache_dir = "cache"
        self.cache_file = os.path.join(self.cache_dir, "geocoding_cache.json")
        self.rate_limit_file = os.path.join(self.cache_dir, "geocoding_rate_limit.json")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load cache from disk
        self.cache = self._load_cache()
        logger.info(f"Loaded {len(self.cache)} geocoding entries from cache")
        logger.info(f"Route naming config: sampling_density={self.sampling_density}, "
                   f"min_segment_length_pct={self.min_segment_length_pct}, "
                   f"enable_segment_naming={self.enable_segment_naming}")
        
        # Check for rate limiting
        self._check_rate_limit_status()
    
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
    
    def _check_rate_limit_status(self):
        """
        Check if we're currently rate limited.
        
        Note: This method does NOT wait - it just logs the status.
        The route_analyzer checks the rate limit file before starting geocoding.
        This method is only called when RouteNamer is instantiated for actual geocoding work.
        """
        if not os.path.exists(self.rate_limit_file):
            return
        
        try:
            with open(self.rate_limit_file, 'r') as f:
                rate_limit_data = json.load(f)
            
            blocked_until_str = rate_limit_data.get('blocked_until')
            if not blocked_until_str:
                return
            
            blocked_until = datetime.fromisoformat(blocked_until_str)
            now = datetime.now()
            
            if now < blocked_until:
                wait_hours = (blocked_until - now).total_seconds() / 3600
                
                # Format with timezone info
                blocked_until_formatted = blocked_until.strftime('%Y-%m-%d %H:%M:%S %Z').strip()
                if not blocked_until_formatted.endswith('Z') and not any(tz in blocked_until_formatted for tz in ['EST', 'EDT', 'CST', 'CDT', 'MST', 'MDT', 'PST', 'PDT']):
                    # Add local timezone indicator if not present
                    import time as time_module
                    tz_name = time_module.tzname[time_module.daylight]
                    blocked_until_formatted = f"{blocked_until.strftime('%Y-%m-%d %H:%M:%S')} {tz_name}"
                
                logger.warning(f"Geocoding rate limit detected. Self-imposed 4-hour block until {blocked_until_formatted}")
                logger.info(f"Rate limit will expire in {wait_hours:.1f} hours")
            else:
                # Rate limit has expired, remove the file
                logger.info("Rate limit period has expired, removing block file")
                os.remove(self.rate_limit_file)
        except Exception as e:
            logger.warning(f"Failed to check rate limit status: {e}")
    
    def _record_rate_limit(self):
        """Record that we've been rate limited and set a 4-hour self-imposed block."""
        try:
            now = datetime.now()
            blocked_until = now + timedelta(hours=4)
            
            # Format with timezone
            import time as time_module
            tz_name = time_module.tzname[time_module.daylight]
            blocked_until_formatted = f"{blocked_until.strftime('%Y-%m-%d %H:%M:%S')} {tz_name}"
            
            rate_limit_data = {
                'blocked_until': blocked_until.isoformat(),
                'blocked_at': now.isoformat(),
                'reason': 'Nominatim rate limit detected - self-imposed 4-hour pause to prevent IP block',
                'note': 'This is a protective measure, not a Nominatim-imposed block'
            }
            with open(self.rate_limit_file, 'w') as f:
                json.dump(rate_limit_data, f, indent=2)
            logger.error(f"Rate limit detected. Self-imposing 4-hour block until {blocked_until_formatted}")
        except Exception as e:
            logger.error(f"Failed to record rate limit: {e}")
    
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
            print(f"  Naming route {route_id} ({direction})...", end='', flush=True)
            
            # Multi-strategy naming approach
            route_info = self._analyze_route_geography(coordinates)
            
            # Generate name based on available information
            name = self._generate_descriptive_name(route_info, route_id, direction)
            
            print(f" → {name}")
            logger.info(f"Named route {route_id}: {name}")
            return name
            
        except Exception as e:
            print(f" [FAILED: {e}]")
            logger.warning(f"Failed to name route {route_id}: {e}")
            # Fallback to generic name
            direction_label = "to Work" if direction == "home_to_work" else "to Home"
            return f"Route {route_id.split('_')[-1]} {direction_label}"
    
    def _analyze_route_geography(self, coordinates: List[Tuple[float, float]]) -> Dict:
        """
        Analyze route geography including segment identification.
        
        Returns dict with:
        - segments: List of route segments with street names and positions
        - major_streets: List of significant streets (not every small street)
        - neighborhoods: List of neighborhoods/districts traversed
        - landmarks: List of notable landmarks
        - geographic_features: Parks, rivers, etc.
        """
        if not coordinates:
            return {}
        
        # Identify route segments (NEW)
        segments = self._identify_route_segments(coordinates)
        
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
            'segments': segments,  # NEW
            'major_streets': self._filter_significant_streets(streets),
            'neighborhoods': list(neighborhoods),
            'landmarks': landmarks[:2],  # Limit to 2 most prominent
            'geographic_features': features[:1]  # Limit to 1 most prominent
        }
    
    def _get_strategic_sample_points(self, coordinates: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Sample points to capture route structure, focusing on direction changes (turns).
        Returns points based on sampling_density config (default ~10 points).
        """
        if len(coordinates) < 10:
            return coordinates
        
        # Calculate bearing changes to find turns
        turn_points = self._find_significant_turns(coordinates)
        
        # Always include start and end
        points = [coordinates[0]]
        
        # Add turn points (these are the key decision points)
        points.extend(turn_points)
        
        # Add end point
        points.append(coordinates[-1])
        
        # If we don't have enough points, add some evenly spaced ones
        target_points = self.sampling_density
        if len(points) < target_points:
            # Fill in with evenly spaced points
            step = len(coordinates) // (target_points - len(points) + 1)
            for i in range(step, len(coordinates) - step, step):
                if coordinates[i] not in points:
                    points.append(coordinates[i])
                if len(points) >= target_points:
                    break
        
        # Sort by original order in coordinates
        points_with_idx = [(coordinates.index(p), p) for p in points if p in coordinates]
        points_with_idx.sort(key=lambda x: x[0])
        
        return [p for _, p in points_with_idx[:target_points]]
    
    def _find_significant_turns(self, coordinates: List[Tuple[float, float]],
                                min_angle: float = 30.0) -> List[Tuple[float, float]]:
        """
        Find points where the route makes significant direction changes.
        
        Args:
            coordinates: List of (lat, lon) tuples
            min_angle: Minimum angle change (degrees) to consider a significant turn
            
        Returns:
            List of coordinates at turn points
        """
        import math
        
        if len(coordinates) < 3:
            return []
        
        turn_points = []
        
        # Use a sliding window to detect bearing changes
        window_size = min(10, len(coordinates) // 10)  # Adaptive window size
        
        for i in range(window_size, len(coordinates) - window_size, window_size):
            # Calculate bearing before and after this point
            before_bearing = self._calculate_bearing(
                coordinates[i - window_size], coordinates[i]
            )
            after_bearing = self._calculate_bearing(
                coordinates[i], coordinates[i + window_size]
            )
            
            # Calculate angle change
            angle_change = abs(after_bearing - before_bearing)
            # Normalize to 0-180 range
            if angle_change > 180:
                angle_change = 360 - angle_change
            
            # If significant turn, add this point
            if angle_change >= min_angle:
                turn_points.append(coordinates[i])
        
        return turn_points
    
    def _calculate_bearing(self, point1: Tuple[float, float],
                          point2: Tuple[float, float]) -> float:
        """
        Calculate bearing between two points in degrees.
        
        Args:
            point1: (lat, lon) tuple
            point2: (lat, lon) tuple
            
        Returns:
            Bearing in degrees (0-360)
        """
        import math
        
        lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
        lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
        
        dlon = lon2 - lon1
        
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def _normalize_street_name(self, street: str) -> str:
        """
        Normalize street name by replacing with equivalent if defined.
        
        Args:
            street: Original street name
            
        Returns:
            Normalized street name (or original if no equivalent defined)
        """
        if not street:
            return street
        
        # Check if this street has an equivalent
        return self.equivalent_streets.get(street, street)
    
    def _identify_route_segments(self, coordinates: List[Tuple[float, float]]) -> List[Dict]:
        """
        Identify distinct route segments based on street changes.
        
        Returns list of segments with:
        - street: Street name (normalized to handle equivalents)
        - length_pct: Percentage of route on this street
        - position: 'start', 'middle', or 'end'
        - sample_points: Number of sample points on this street
        """
        sample_points = self._get_strategic_sample_points(coordinates)
        
        segments = []
        current_street = None
        current_segment = None
        
        for i, point in enumerate(sample_points):
            location_info = self._get_location_details(point)
            raw_street = location_info.get('street') if location_info else None
            # Normalize street name to handle equivalents (e.g., Simonds Drive → Lakefront Trail)
            street = self._normalize_street_name(raw_street)
            
            if street != current_street:
                # Street changed - start new segment
                if current_segment:
                    segments.append(current_segment)
                
                current_street = street
                current_segment = {
                    'street': street,
                    'start_idx': i,
                    'sample_points': 1
                }
            else:
                # Same street - extend current segment
                if current_segment:
                    current_segment['sample_points'] += 1
        
        # Add final segment
        if current_segment:
            segments.append(current_segment)
        
        # Calculate percentages and positions
        total_points = len(sample_points)
        for i, segment in enumerate(segments):
            segment['length_pct'] = (segment['sample_points'] / total_points) * 100
            
            if i == 0:
                segment['position'] = 'start'
            elif i == len(segments) - 1:
                segment['position'] = 'end'
            else:
                segment['position'] = 'middle'
        
        return segments
    
    def _get_location_details(self, point: Tuple[float, float], retry_count: int = 0) -> Optional[Dict]:
        """
        Get detailed location information for a point with retry logic.
        
        Args:
            point: (lat, lon) tuple
            retry_count: Current retry attempt (for exponential backoff)
        
        Returns dict with street, neighborhood, landmark, feature, and is_major flag.
        """
        # Check cache first
        cache_key = f"details_{point[0]:.4f},{point[1]:.4f}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]
        
        # Rate limiting for API requests - Nominatim requires max 1 req/sec
        # Use 1.1 seconds to provide small safety margin
        print(".", end='', flush=True)  # Show progress dot for each API call
        logger.debug(f"Cache miss for {cache_key}, making API request")
        time.sleep(1.1)
        
        try:
            location = self.geolocator.reverse(point, exactly_one=True, language='en', timeout=10)
            
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
            
        except GeocoderTimedOut as e:
            # Timeout - retry with exponential backoff
            if retry_count < 3:
                wait_time = 2 ** retry_count  # 1s, 2s, 4s
                logger.warning(f"Geocoding timeout for {point}, retrying in {wait_time}s (attempt {retry_count + 1}/3)")
                time.sleep(wait_time)
                return self._get_location_details(point, retry_count + 1)
            else:
                logger.error(f"Geocoding failed after 3 retries for {point}: {e}")
                return None
                
        except GeocoderServiceError as e:
            # Service error (rate limit, blocked IP, etc.) - longer backoff
            error_msg = str(e).lower()
            if 'rate' in error_msg or 'limit' in error_msg or 'blocked' in error_msg:
                if retry_count < 2:
                    wait_time = 5 * (retry_count + 1)  # 5s, 10s
                    logger.warning(f"Rate limit/block detected for {point}, waiting {wait_time}s (attempt {retry_count + 1}/2)")
                    time.sleep(wait_time)
                    return self._get_location_details(point, retry_count + 1)
                else:
                    logger.error(f"Geocoding blocked/rate limited after retries for {point}: {e}")
                    # Record rate limit for 4-hour block
                    self._record_rate_limit()
                    return None
            else:
                logger.warning(f"Geocoding service error for {point}: {e}")
                return None
                
        except Exception as e:
            logger.warning(f"Unexpected error geocoding {point}: {e}")
            return None
        
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
    
    def _is_access_path(self, street_name: str) -> bool:
        """
        Determine if a street is likely an access path/ramp rather than a main street.
        
        Args:
            street_name: Street name to check
            
        Returns:
            True if likely an access path
        """
        if not street_name:
            return False
        
        street_lower = street_name.lower()
        
        # Access path indicators
        access_indicators = [
            'access',
            'path',
            'ramp',
            'entrance',
            'exit'
        ]
        
        # Check for access indicators
        if any(indicator in street_lower for indicator in access_indicators):
            return True
        
        # Check for short "Drive" streets that are likely access roads
        # (but not major streets like "Lake Shore Drive")
        if 'drive' in street_lower:
            # If it has directional prefix (West/East/North/South) and "Drive",
            # it's likely an access road unless it's a known major street
            if any(direction in street_lower for direction in ['west ', 'east ', 'north ', 'south ']):
                # Known major drives that should NOT be filtered
                major_drives = ['lake shore', 'lakeshore', 'martin luther king']
                if not any(major in street_lower for major in major_drives):
                    return True
        
        return False
    
    def _generate_descriptive_name(self, route_info: Dict, route_id: str, direction: str) -> str:
        """
        Generate descriptive name from route segments.
        
        Priority:
        1. Full path (3+ segments): "Start → Main → End"
        2. Main + connection (2 segments): "Main via Connection"
        3. Single route: "Via Main"
        4. Fallback to legacy naming strategies
        """
        segments = route_info.get('segments', [])
        
        # Try segment-based naming first (if enabled)
        if self.enable_segment_naming and segments:
            # Filter out segments that are:
            # 1. Too short (< min_segment_length_pct)
            # 2. Have no street name
            # 3. Are access paths/ramps
            significant_segments = [s for s in segments
                                   if s.get('street')
                                   and s.get('length_pct', 0) >= self.min_segment_length_pct
                                   and not self._is_access_path(s.get('street', ''))]
            
            if len(significant_segments) >= 3:
                # Strategy 1: Full path - but avoid duplicates
                # Get unique streets in order, preserving the path
                unique_streets = []
                seen = set()
                for seg in significant_segments:
                    street = seg['street']
                    if street not in seen:
                        unique_streets.append(seg)
                        seen.add(street)
                
                # If we have 3+ unique streets, show start → middle → end
                if len(unique_streets) >= 3:
                    start = unique_streets[0]['street']
                    # Pick the longest middle segment
                    main = max(unique_streets[1:-1], key=lambda s: s['length_pct'])['street']
                    end = unique_streets[-1]['street']
                    return f"{start} → {main} → {end}"
                elif len(unique_streets) == 2:
                    # Only 2 unique streets, use simpler format
                    return f"{unique_streets[0]['street']} → {unique_streets[1]['street']}"
                else:
                    # Only 1 unique street
                    return f"Via {unique_streets[0]['street']}"
            
            elif len(significant_segments) == 2:
                # Strategy 2: Main + connection
                # Check if they're the same street (duplicate)
                if significant_segments[0]['street'] == significant_segments[1]['street']:
                    return f"Via {significant_segments[0]['street']}"
                
                main = max(significant_segments, key=lambda s: s['length_pct'])
                connection = min(significant_segments, key=lambda s: s['length_pct'])
                
                if main['length_pct'] > 60:
                    return f"{main['street']} via {connection['street']}"
                else:
                    return f"{significant_segments[0]['street']} → {significant_segments[1]['street']}"
            
            elif len(significant_segments) == 1:
                # Strategy 3: Single route
                return f"Via {significant_segments[0]['street']}"
        
        # Fallback to legacy naming strategies
        return self._generate_descriptive_name_legacy(route_info, route_id, direction)
    
    def _generate_descriptive_name_legacy(self, route_info: Dict, route_id: str, direction: str) -> str:
        """
        Legacy naming strategy (pre-segment implementation).
        
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
            
        except GeocoderTimedOut as e:
            # Timeout - retry with exponential backoff
            if retry_count < 3:
                wait_time = 2 ** retry_count  # 1s, 2s, 4s
                logger.warning(f"Geocoding timeout for {point}, retrying in {wait_time}s (attempt {retry_count + 1}/3)")
                time.sleep(wait_time)
                return self._get_street_name(point, retry_count + 1)
            else:
                logger.error(f"Geocoding failed after 3 retries for {point}: {e}")
                return None
                
        except GeocoderServiceError as e:
            # Service error (rate limit, blocked IP, etc.) - longer backoff
            error_msg = str(e).lower()
            if 'rate' in error_msg or 'limit' in error_msg or 'blocked' in error_msg:
                if retry_count < 2:
                    wait_time = 5 * (retry_count + 1)  # 5s, 10s
                    logger.warning(f"Rate limit/block detected for {point}, waiting {wait_time}s (attempt {retry_count + 1}/2)")
                    time.sleep(wait_time)
                    return self._get_street_name(point, retry_count + 1)
                else:
                    logger.error(f"Geocoding blocked/rate limited after retries for {point}: {e}")
                    # Record rate limit for 4-hour block
                    self._record_rate_limit()
                    return None
            else:
                logger.warning(f"Geocoding service error for {point}: {e}")
                return None
                
        except Exception as e:
            logger.warning(f"Unexpected error geocoding {point}: {e}")
            return None
        
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