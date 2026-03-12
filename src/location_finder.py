"""
Location identification module.

Uses clustering algorithms to identify home and work locations from activity data.
"""

import logging
from datetime import time, datetime, timedelta
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import geodesic

from .data_fetcher import Activity

logger = logging.getLogger(__name__)


@dataclass
class Location:
    """Represents a location (home or work)."""
    lat: float
    lon: float
    name: str  # "Home" or "Work"
    activity_count: int
    avg_departure_time: Optional[time] = None
    avg_arrival_time: Optional[time] = None
    radius: float = 0.0  # cluster radius in meters


class LocationFinder:
    """Identifies home and work locations from activity patterns."""
    
    def __init__(self, activities: List[Activity], config):
        """
        Initialize location finder.
        
        Args:
            activities: List of Activity objects
            config: Configuration object
        """
        self.activities = activities
        self.config = config
        self.eps = config.get('location_detection.clustering.eps', 0.002)
        self.min_samples = config.get('location_detection.clustering.min_samples', 5)
        
    def extract_endpoints(self) -> List[Dict]:
        """
        Extract start and end points from all activities.
        
        Returns:
            List of endpoint dictionaries with coordinates and timestamps
        """
        endpoints = []
        
        for activity in self.activities:
            # Parse start date
            start_dt = datetime.fromisoformat(activity.start_date)
            
            # Add start point
            if activity.start_latlng and len(activity.start_latlng) >= 2:
                endpoints.append({
                    'lat': activity.start_latlng[0],
                    'lon': activity.start_latlng[1],
                    'time': start_dt.time(),
                    'datetime': start_dt,
                    'type': 'start',
                    'activity_id': activity.id
                })
            
            # Add end point (approximate end time)
            if activity.end_latlng and len(activity.end_latlng) >= 2:
                end_dt = start_dt + timedelta(seconds=activity.elapsed_time)
                endpoints.append({
                    'lat': activity.end_latlng[0],
                    'lon': activity.end_latlng[1],
                    'time': end_dt.time(),
                    'datetime': end_dt,
                    'type': 'end',
                    'activity_id': activity.id
                })
        
        logger.info(f"Extracted {len(endpoints)} endpoints from {len(self.activities)} activities")
        
        return endpoints
    
    def cluster_locations(self, endpoints: List[Dict]) -> List[Dict]:
        """
        Apply DBSCAN clustering to identify location clusters.
        
        Args:
            endpoints: List of endpoint dictionaries
            
        Returns:
            List of cluster dictionaries
        """
        if len(endpoints) < self.min_samples:
            raise ValueError(f"Need at least {self.min_samples} endpoints for clustering")
        
        # Extract coordinates
        coords = np.array([[ep['lat'], ep['lon']] for ep in endpoints])
        
        # Apply DBSCAN
        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(coords)
        
        # Group endpoints by cluster
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            if label == -1:  # Noise point
                continue
            
            if label not in clusters:
                clusters[label] = []
            
            clusters[label].append(endpoints[idx])
        
        logger.info(f"Found {len(clusters)} location clusters")
        
        # Calculate cluster statistics
        cluster_stats = []
        for label, points in clusters.items():
            # Calculate centroid
            lats = [p['lat'] for p in points]
            lons = [p['lon'] for p in points]
            centroid_lat = np.mean(lats)
            centroid_lon = np.mean(lons)
            
            # Calculate radius (max distance from centroid)
            max_dist = 0
            for p in points:
                dist = geodesic((centroid_lat, centroid_lon), (p['lat'], p['lon'])).meters
                max_dist = max(max_dist, dist)
            
            # Separate by start/end
            starts = [p for p in points if p['type'] == 'start']
            ends = [p for p in points if p['type'] == 'end']
            
            # Calculate average times
            avg_departure = None
            if starts:
                dep_seconds = [t['time'].hour * 3600 + t['time'].minute * 60 + t['time'].second 
                              for t in starts]
                avg_dep_seconds = int(np.mean(dep_seconds))
                avg_departure = time(avg_dep_seconds // 3600, 
                                    (avg_dep_seconds % 3600) // 60,
                                    avg_dep_seconds % 60)
            
            avg_arrival = None
            if ends:
                arr_seconds = [t['time'].hour * 3600 + t['time'].minute * 60 + t['time'].second 
                              for t in ends]
                avg_arr_seconds = int(np.mean(arr_seconds))
                avg_arrival = time(avg_arr_seconds // 3600,
                                  (avg_arr_seconds % 3600) // 60,
                                  avg_arr_seconds % 60)
            
            cluster_stats.append({
                'label': label,
                'centroid': (centroid_lat, centroid_lon),
                'count': len(points),
                'radius': max_dist,
                'starts': len(starts),
                'ends': len(ends),
                'avg_departure': avg_departure,
                'avg_arrival': avg_arrival,
                'points': points
            })
        
        # Sort by frequency
        cluster_stats.sort(key=lambda x: x['count'], reverse=True)
        
        return cluster_stats
    
    def identify_home_work(self) -> Tuple[Location, Location]:
        """
        Identify home and work locations from clusters.
        
        Returns:
            Tuple of (home, work) Location objects
        """
        # Extract endpoints
        endpoints = self.extract_endpoints()
        
        if len(endpoints) < 10:
            raise ValueError(f"Need at least 10 endpoints, found {len(endpoints)}")
        
        # Cluster locations
        clusters = self.cluster_locations(endpoints)
        
        if len(clusters) < 2:
            raise ValueError(f"Need at least 2 location clusters, found {len(clusters)}")
        
        # Get top 2 clusters
        cluster1 = clusters[0]
        cluster2 = clusters[1]
        
        logger.info(f"Top cluster 1: {cluster1['count']} points at ({cluster1['centroid'][0]:.4f}, {cluster1['centroid'][1]:.4f})")
        logger.info(f"Top cluster 2: {cluster2['count']} points at ({cluster2['centroid'][0]:.4f}, {cluster2['centroid'][1]:.4f})")
        
        # Use time-of-day heuristics to identify home vs work
        home_cluster, work_cluster = self._classify_home_work(cluster1, cluster2)
        
        # Create Location objects
        home = Location(
            lat=home_cluster['centroid'][0],
            lon=home_cluster['centroid'][1],
            name="Home",
            activity_count=home_cluster['count'],
            avg_departure_time=home_cluster['avg_departure'],
            avg_arrival_time=home_cluster['avg_arrival'],
            radius=home_cluster['radius']
        )
        
        work = Location(
            lat=work_cluster['centroid'][0],
            lon=work_cluster['centroid'][1],
            name="Work",
            activity_count=work_cluster['count'],
            avg_departure_time=work_cluster['avg_departure'],
            avg_arrival_time=work_cluster['avg_arrival'],
            radius=work_cluster['radius']
        )
        
        logger.info(f"Identified Home: ({home.lat:.4f}, {home.lon:.4f})")
        logger.info(f"Identified Work: ({work.lat:.4f}, {work.lon:.4f})")
        
        return home, work
    
    def _classify_home_work(self, cluster1: Dict, cluster2: Dict) -> Tuple[Dict, Dict]:
        """
        Classify which cluster is home and which is work based on time patterns.
        
        Args:
            cluster1: First cluster dictionary
            cluster2: Second cluster dictionary
            
        Returns:
            Tuple of (home_cluster, work_cluster)
        """
        # Get time windows from config
        morning_start = self._parse_time(self.config.get('location_detection.time_windows.morning_start', '06:00'))
        morning_end = self._parse_time(self.config.get('location_detection.time_windows.morning_end', '10:00'))
        evening_start = self._parse_time(self.config.get('location_detection.time_windows.evening_start', '16:00'))
        evening_end = self._parse_time(self.config.get('location_detection.time_windows.evening_end', '20:00'))
        
        # Score each cluster for "home-ness"
        score1 = self._calculate_home_score(cluster1, morning_start, morning_end, evening_start, evening_end)
        score2 = self._calculate_home_score(cluster2, morning_start, morning_end, evening_start, evening_end)
        
        logger.info(f"Cluster 1 home score: {score1:.2f}")
        logger.info(f"Cluster 2 home score: {score2:.2f}")
        
        if score1 > score2:
            return cluster1, cluster2
        else:
            return cluster2, cluster1
    
    def _calculate_home_score(self, cluster: Dict, morning_start: time, morning_end: time,
                             evening_start: time, evening_end: time) -> float:
        """
        Calculate how likely a cluster is to be home based on time patterns.
        
        Args:
            cluster: Cluster dictionary
            morning_start: Morning window start
            morning_end: Morning window end
            evening_start: Evening window start
            evening_end: Evening window end
            
        Returns:
            Home score (higher = more likely to be home)
        """
        score = 0.0
        
        # Morning departures suggest home
        if cluster['avg_departure']:
            if morning_start <= cluster['avg_departure'] <= morning_end:
                score += 1.0
        
        # Evening arrivals suggest home
        if cluster['avg_arrival']:
            if evening_start <= cluster['avg_arrival'] <= evening_end:
                score += 1.0
        
        return score
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string in HH:MM format."""
        parts = time_str.split(':')
        return time(int(parts[0]), int(parts[1]))
    
    def get_location_statistics(self, location: Location) -> Dict:
        """
        Get detailed statistics for a location.
        
        Args:
            location: Location object
            
        Returns:
            Dictionary of statistics
        """
        return {
            'name': location.name,
            'coordinates': (location.lat, location.lon),
            'activity_count': location.activity_count,
            'avg_departure_time': str(location.avg_departure_time) if location.avg_departure_time else None,
            'avg_arrival_time': str(location.avg_arrival_time) if location.avg_arrival_time else None,
            'radius_meters': location.radius
        }


# Made with Bob
