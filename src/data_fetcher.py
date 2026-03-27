"""
Data fetching module.

Handles retrieving and caching activity data from Strava API.

Copyright (c) 2024-2026 e2kd7n
Licensed under the MIT License - see LICENSE file for details.
"""

import json
import logging
import sys
import os
import contextlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from stravalib.client import Client
import polyline

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def suppress_stderr():
    """Context manager to temporarily suppress stderr output."""
    with open(os.devnull, 'w') as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stderr = old_stderr


@dataclass
class Activity:
    """Represents a Strava activity."""
    id: int
    name: str
    type: str
    start_date: str  # ISO format
    distance: float  # meters
    moving_time: int  # seconds
    elapsed_time: int  # seconds
    total_elevation_gain: float  # meters
    start_latlng: Optional[tuple]
    end_latlng: Optional[tuple]
    polyline: Optional[str]  # encoded polyline
    average_speed: float  # m/s
    max_speed: float  # m/s
    
    @classmethod
    def from_strava_activity(cls, activity, use_detailed_polyline=False):
        """
        Create Activity from Strava API activity object.
        
        Args:
            activity: Strava activity object
            use_detailed_polyline: If True, use detailed polyline instead of summary
        """
        # Helper function to convert time to seconds
        def to_seconds(time_obj):
            if time_obj is None:
                return 0
            # Handle both timedelta and Duration objects
            if hasattr(time_obj, 'total_seconds'):
                return int(time_obj.total_seconds())
            elif hasattr(time_obj, 'seconds'):
                return int(time_obj.seconds)
            else:
                # Assume it's already an integer
                return int(time_obj)
        
        # Choose polyline based on parameter
        # Detailed polyline is only available from get_activity() endpoint
        # Summary polyline is available from get_activities() list endpoint
        if use_detailed_polyline and activity.map and hasattr(activity.map, 'polyline'):
            polyline_data = activity.map.polyline
        elif activity.map:
            polyline_data = activity.map.summary_polyline
        else:
            polyline_data = None
        
        return cls(
            id=activity.id,
            name=activity.name,
            type=str(activity.type) if activity.type else "Unknown",
            start_date=activity.start_date.isoformat() if activity.start_date else None,
            distance=float(activity.distance) if activity.distance else 0.0,
            moving_time=to_seconds(activity.moving_time),
            elapsed_time=to_seconds(activity.elapsed_time),
            total_elevation_gain=float(activity.total_elevation_gain) if activity.total_elevation_gain else 0.0,
            start_latlng=tuple(activity.start_latlng) if activity.start_latlng else None,
            end_latlng=tuple(activity.end_latlng) if activity.end_latlng else None,
            polyline=polyline_data,
            average_speed=float(activity.average_speed) if activity.average_speed else 0.0,
            max_speed=float(activity.max_speed) if activity.max_speed else 0.0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create Activity from dictionary."""
        # Convert tuples back from lists, handling nested structure from Strava API
        def extract_latlng(latlng_data):
            if not latlng_data:
                return None
            # Handle nested structure: [['root', [lat, lon]]]
            if isinstance(latlng_data, list) and len(latlng_data) > 0:
                if isinstance(latlng_data[0], list) and len(latlng_data[0]) > 1:
                    # Extract from nested structure
                    coords = latlng_data[0][1]
                    if isinstance(coords, list) and len(coords) >= 2:
                        return tuple(coords)
                # Simple list [lat, lon]
                elif len(latlng_data) >= 2 and isinstance(latlng_data[0], (int, float)):
                    return tuple(latlng_data)
            return None
        
        if data.get('start_latlng'):
            data['start_latlng'] = extract_latlng(data['start_latlng'])
        if data.get('end_latlng'):
            data['end_latlng'] = extract_latlng(data['end_latlng'])
        return cls(**data)


class StravaDataFetcher:
    """Fetches and caches activity data from Strava API."""
    
    def __init__(self, client: Client, config, use_test_cache: bool = False):
        """
        Initialize data fetcher.
        
        Args:
            client: Authenticated Strava client
            config: Configuration object
            use_test_cache: If True, use test cache instead of production cache
        """
        self.client = client
        self.config = config
        self.use_test_cache = use_test_cache
        
        # Use separate cache paths for test and production data
        if use_test_cache:
            self.cache_path = Path("data/cache/activities_test.json")
            logger.info("Using TEST cache: data/cache/activities_test.json")
        else:
            self.cache_path = Path("data/cache/activities.json")
        
    def fetch_activities(self, limit: Optional[int] = None,
                        after: Optional[datetime] = None,
                        before: Optional[datetime] = None) -> List[Activity]:
        """
        Fetch activities from Strava API.
        
        Args:
            limit: Maximum number of activities to fetch (default from config or 500)
            after: Only fetch activities after this date
            before: Only fetch activities before this date
            
        Returns:
            List of Activity objects
        """
        if limit is None:
            limit = self.config.get('data_fetching.max_activities', 500)
        
        # Print fetch parameters
        print("\n" + "="*70)
        print("📥 FETCHING ACTIVITIES FROM STRAVA")
        print("="*70)
        print(f"Max activities to fetch: {limit}")
        if after and before:
            print(f"Date range: {after.date()} to {before.date()}")
        elif after:
            print(f"Fetching activities after: {after.date()}")
        elif before:
            print(f"Fetching activities before: {before.date()}")
        else:
            print("Fetching most recent activities")
        print("="*70 + "\n")
        
        logger.info(f"Fetching up to {limit} activities from Strava...")
        
        activities = []
        earliest_date = None
        latest_date = None
        
        try:
            # Suppress stravalib's refresh_token warning during iteration
            with suppress_stderr():
                strava_activities = self.client.get_activities(limit=limit, after=after, before=before)
            
            processed_count = 0
            for activity in strava_activities:
                try:
                    act = Activity.from_strava_activity(activity)
                    
                    # If before date specified, filter activities (make before timezone-aware for comparison)
                    if before and act.start_date:
                        act_date = datetime.fromisoformat(act.start_date.replace('Z', '+00:00'))
                        # Make before date timezone-aware (UTC) for comparison
                        from datetime import timezone
                        before_aware = before.replace(tzinfo=timezone.utc)
                        if act_date > before_aware:
                            continue  # Skip activities after the before date
                    
                    activities.append(act)
                    processed_count += 1
                    
                    # Show progress every 100 activities
                    if processed_count % 100 == 0:
                        print(f"  Fetched {processed_count} activities so far...")
                    
                    # Track date range
                    if act.start_date:
                        try:
                            act_date = datetime.fromisoformat(act.start_date.replace('Z', '+00:00'))
                            if earliest_date is None or act_date < earliest_date:
                                earliest_date = act_date
                            if latest_date is None or act_date > latest_date:
                                latest_date = act_date
                        except (ValueError, AttributeError) as e:
                            logger.debug(f"Failed to parse activity date: {e}")
                            pass
                            
                except Exception as e:
                    logger.warning(f"Failed to process activity {activity.id}: {e}")
                    continue
            
            # Print fetch results
            print(f"✓ Fetched {len(activities)} activities from Strava")
            if earliest_date and latest_date:
                print(f"  Date range: {earliest_date.date()} to {latest_date.date()}")
            print()
            
            logger.info(f"Fetched {len(activities)} activities")
            
        except Exception as e:
            logger.error(f"Failed to fetch activities: {e}")
            raise
        
        return activities
    
    def get_activity_details(self, activity_id: int) -> Optional[Activity]:
        """
        Get detailed information for a specific activity.
        
        Args:
            activity_id: Strava activity ID
            
        Returns:
            Activity object or None
        """
        try:
            activity = self.client.get_activity(activity_id)
            return Activity.from_strava_activity(activity, use_detailed_polyline=True)
        except Exception as e:
            logger.error(f"Failed to fetch activity {activity_id}: {e}")
            return None
    
    def enrich_activities_with_detailed_polylines(self, activities: List[Activity]) -> List[Activity]:
        """
        Fetch detailed polylines for activities that only have summary polylines.
        This makes an additional API call per activity, so use sparingly.
        
        Args:
            activities: List of Activity objects with summary polylines
            
        Returns:
            List of Activity objects with detailed polylines
        """
        enriched_activities = []
        
        logger.info(f"Fetching detailed polylines for {len(activities)} activities...")
        
        for i, activity in enumerate(activities):
            try:
                # Fetch detailed activity data
                detailed_activity = self.client.get_activity(activity.id)
                enriched = Activity.from_strava_activity(detailed_activity, use_detailed_polyline=True)
                enriched_activities.append(enriched)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Enriched {i + 1}/{len(activities)} activities")
                    
            except Exception as e:
                logger.warning(f"Failed to enrich activity {activity.id}: {e}")
                # Keep original activity if enrichment fails
                enriched_activities.append(activity)
                continue
        
        logger.info(f"Successfully enriched {len(enriched_activities)} activities with detailed polylines")
        return enriched_activities
    
    def cache_activities(self, activities: List[Activity], merge: bool = True) -> dict:
        """
        Save activities to cache file.
        
        Args:
            activities: List of Activity objects to cache
            merge: If True, merge with existing cache (default). If False, replace cache.
            
        Returns:
            Dictionary with cache statistics: {
                'new': int,
                'updated': int,
                'total': int,
                'previous_total': int
            }
        """
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        stats = {
            'new': 0,
            'updated': 0,
            'total': 0,
            'previous_total': 0
        }
        
        if merge and self.cache_path.exists():
            # Load existing cache
            try:
                existing_activities = self.load_cached_activities()
                stats['previous_total'] = len(existing_activities)
                logger.info(f"Loaded {len(existing_activities)} existing activities from cache")
                
                # Create a dict of existing activities by ID for fast lookup
                existing_by_id = {act.id: act for act in existing_activities}
                
                # Add new activities, replacing any duplicates
                for act in activities:
                    if act.id in existing_by_id:
                        stats['updated'] += 1
                    else:
                        stats['new'] += 1
                    existing_by_id[act.id] = act
                
                # Convert back to list and sort by date (newest first)
                merged_activities = list(existing_by_id.values())
                merged_activities.sort(key=lambda x: x.start_date, reverse=True)
                
                stats['total'] = len(merged_activities)
                
                print("="*70)
                print("💾 CACHE UPDATE SUMMARY")
                print("="*70)
                print(f"Previous cache size: {stats['previous_total']} activities")
                print(f"New activities added: {stats['new']}")
                print(f"Existing activities updated: {stats['updated']}")
                print(f"Total cache size: {stats['total']} activities")
                print(f"Net change: +{stats['total'] - stats['previous_total']} activities")
                print("="*70 + "\n")
                
                logger.info(f"Merged cache: {stats['new']} new, {stats['updated']} updated, {stats['total']} total")
                activities = merged_activities
                
            except Exception as e:
                logger.warning(f"Failed to merge with existing cache: {e}. Replacing cache.")
                stats['new'] = len(activities)
                stats['total'] = len(activities)
        else:
            # Not merging or no existing cache
            stats['new'] = len(activities)
            stats['total'] = len(activities)
            
            print("="*70)
            print("💾 CACHE CREATED")
            print("="*70)
            print(f"Total activities cached: {stats['total']}")
            print("="*70 + "\n")
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'count': len(activities),
            'activities': [act.to_dict() for act in activities]
        }
        
        with open(self.cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        logger.info(f"Cached {len(activities)} activities to {self.cache_path}")
        
        return stats
    
    def load_cached_activities(self) -> List[Activity]:
        """
        Load activities from cache file.
        
        Returns:
            List of Activity objects
        """
        if not self.cache_path.exists():
            logger.warning("No cache file found")
            return []
        
        with open(self.cache_path, 'r') as f:
            cache_data = json.load(f)
        
        activities = [Activity.from_dict(act) for act in cache_data['activities']]
        
        logger.info(f"Loaded {len(activities)} activities from cache")
        logger.info(f"Cache timestamp: {cache_data['timestamp']}")
        
        return activities
    
    def is_cache_valid(self) -> bool:
        """
        Check if cache is still valid based on cache duration.
        
        Returns:
            True if cache is valid, False otherwise
        """
        if not self.cache_path.exists():
            return False
        
        with open(self.cache_path, 'r') as f:
            cache_data = json.load(f)
        
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        cache_duration = timedelta(days=self.config.get('data_fetching.cache_duration_days', 7))
        
        return datetime.now() - cache_time < cache_duration
    
    def filter_commute_activities(self, activities: List[Activity]) -> List[Activity]:
        """
        Filter activities to find potential commutes.
        
        Args:
            activities: List of Activity objects
            
        Returns:
            Filtered list of Activity objects
        """
        min_distance = self.config.get('route_filtering.min_distance_km', 2) * 1000  # Convert to meters
        max_distance = self.config.get('route_filtering.max_distance_km', 30) * 1000
        activity_types = self.config.get('route_filtering.activity_types', ['Ride', 'EBikeRide'])
        exclude_virtual = self.config.get('route_filtering.exclude_virtual', True)
        
        # Commute name patterns
        commute_keywords = ['work', 'commute', 'to work', 'from work', 'home from work']
        
        filtered = []
        
        for activity in activities:
            # Check if activity name contains commute keywords
            activity_name_lower = activity.name.lower() if activity.name else ""
            is_commute_name = any(keyword in activity_name_lower for keyword in commute_keywords)
            
            # If it doesn't have a commute-related name, skip it
            if not is_commute_name:
                continue
            
            # Check activity type (more lenient for commutes)
            if activity.type not in activity_types and 'Ride' not in activity.type:
                continue
            
            # Check distance (use wider range for commutes)
            if activity.distance < min_distance or activity.distance > max_distance:
                continue
            
            # Check for GPS data
            if not activity.start_latlng or not activity.end_latlng:
                continue
            
            # Check for polyline
            if not activity.polyline:
                continue
            
            # Exclude virtual rides
            if exclude_virtual and 'virtual' in activity_name_lower:
                continue
            
            filtered.append(activity)
        
        logger.info(f"Filtered {len(filtered)} potential commute activities from {len(activities)} total")
        
        return filtered
    
    def decode_polyline(self, encoded: str) -> List[tuple]:
        """
        Decode polyline string to list of coordinates.
        
        Args:
            encoded: Encoded polyline string
            
        Returns:
            List of (lat, lon) tuples
        """
        return polyline.decode(encoded)

# Made with Bob
