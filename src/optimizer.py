"""
Route optimization module.

Scores and ranks routes based on multiple criteria.
"""

import logging
from typing import List, Tuple, Dict, Any

import numpy as np

from .route_analyzer import RouteGroup, RouteMetrics, RouteAnalyzer

logger = logging.getLogger(__name__)


class RouteOptimizer:
    """Optimizes route selection using multi-criteria scoring."""
    
    def __init__(self, route_groups: List[RouteGroup], config):
        """
        Initialize route optimizer.
        
        Args:
            route_groups: List of RouteGroup objects
            config: Configuration object
        """
        self.route_groups = route_groups
        self.config = config
        self.weights = {
            'time': config.get('optimization.weights.time', 0.4),
            'distance': config.get('optimization.weights.distance', 0.3),
            'safety': config.get('optimization.weights.safety', 0.3)
        }
        
        # Calculate metrics for all groups
        self.analyzer = None  # Will be set if needed
        self.metrics = {}
        self._calculate_all_metrics()
        
        # Find min/max values for normalization
        self._find_normalization_bounds()
    
    def _calculate_all_metrics(self):
        """Calculate metrics for all route groups."""
        from .route_analyzer import RouteAnalyzer
        
        for group in self.route_groups:
            # Calculate metrics inline
            routes = group.routes
            durations = [r.duration for r in routes]
            distances = [r.distance for r in routes]
            speeds = [r.average_speed for r in routes]
            elevations = [r.elevation_gain for r in routes]
            
            avg_duration = np.mean(durations)
            std_duration = np.std(durations)
            avg_distance = np.mean(distances)
            avg_speed = np.mean(speeds)
            avg_elevation = np.mean(elevations)
            
            if avg_duration > 0:
                cv = std_duration / avg_duration
                consistency_score = max(0, 1 - cv)
            else:
                consistency_score = 0
            
            from .route_analyzer import RouteMetrics
            self.metrics[group.id] = RouteMetrics(
                avg_duration=avg_duration,
                std_duration=std_duration,
                avg_distance=avg_distance,
                avg_speed=avg_speed,
                avg_elevation=avg_elevation,
                consistency_score=consistency_score,
                usage_frequency=len(routes)
            )
    
    def _find_normalization_bounds(self):
        """Find min/max values for normalization."""
        if not self.metrics:
            return
        
        durations = [m.avg_duration for m in self.metrics.values()]
        distances = [m.avg_distance for m in self.metrics.values()]
        frequencies = [m.usage_frequency for m in self.metrics.values()]
        elevations = [m.avg_elevation for m in self.metrics.values()]
        
        self.min_duration = min(durations)
        self.max_duration = max(durations)
        self.min_distance = min(distances)
        self.max_distance = max(distances)
        self.max_frequency = max(frequencies)
        self.max_elevation = max(elevations) if max(elevations) > 0 else 1
    
    def calculate_time_score(self, metrics: RouteMetrics) -> float:
        """
        Calculate time score for a route.
        
        Args:
            metrics: RouteMetrics object
            
        Returns:
            Time score (0-100)
        """
        # Normalize duration (faster = higher score)
        if self.max_duration == self.min_duration:
            duration_score = 100
        else:
            normalized = (metrics.avg_duration - self.min_duration) / (self.max_duration - self.min_duration)
            duration_score = 100 * (1 - normalized)
        
        # Bonus for consistency (low variance)
        consistency_bonus = metrics.consistency_score * 10
        
        # Combine
        time_score = min(100, duration_score + consistency_bonus)
        
        return time_score
    
    def calculate_distance_score(self, metrics: RouteMetrics) -> float:
        """
        Calculate distance score for a route.
        
        Args:
            metrics: RouteMetrics object
            
        Returns:
            Distance score (0-100)
        """
        # Normalize distance (shorter = higher score)
        if self.max_distance == self.min_distance:
            distance_score = 100
        else:
            normalized = (metrics.avg_distance - self.min_distance) / (self.max_distance - self.min_distance)
            distance_score = 100 * (1 - normalized)
        
        return distance_score
    
    def calculate_safety_score(self, route_group: RouteGroup) -> float:
        """
        Calculate safety score for a route.
        
        Args:
            route_group: RouteGroup object
            
        Returns:
            Safety score (0-100)
        """
        metrics = self.metrics[route_group.id]
        
        # Frequency component (40%) - more used = more familiar = safer
        if self.max_frequency > 0:
            frequency_score = (metrics.usage_frequency / self.max_frequency) * 100
        else:
            frequency_score = 100
        
        # Elevation component (30%) - flatter = safer
        elevation_penalty = min(50, metrics.avg_elevation / 10)  # -5 points per 100m
        elevation_score = 100 - elevation_penalty
        
        # Road type inference (30%) - based on speed consistency
        # More consistent speed suggests better road conditions
        road_score = metrics.consistency_score * 100
        
        # Combine components
        safety_score = (
            frequency_score * 0.4 +
            elevation_score * 0.3 +
            road_score * 0.3
        )
        
        return safety_score
    
    def calculate_composite_score(self, route_group: RouteGroup) -> float:
        """
        Calculate composite score for a route.
        
        Args:
            route_group: RouteGroup object
            
        Returns:
            Composite score (0-100)
        """
        metrics = self.metrics[route_group.id]
        
        time_score = self.calculate_time_score(metrics)
        distance_score = self.calculate_distance_score(metrics)
        safety_score = self.calculate_safety_score(route_group)
        
        composite = (
            time_score * self.weights['time'] +
            distance_score * self.weights['distance'] +
            safety_score * self.weights['safety']
        )
        
        logger.debug(f"Route {route_group.id}: time={time_score:.1f}, "
                    f"distance={distance_score:.1f}, safety={safety_score:.1f}, "
                    f"composite={composite:.1f}")
        
        return composite
    
    def rank_routes(self) -> List[Tuple[RouteGroup, float, Dict[str, float]]]:
        """
        Rank all routes by composite score.
        
        Returns:
            List of tuples (RouteGroup, composite_score, score_breakdown)
        """
        ranked = []
        
        for group in self.route_groups:
            metrics = self.metrics[group.id]
            
            time_score = self.calculate_time_score(metrics)
            distance_score = self.calculate_distance_score(metrics)
            safety_score = self.calculate_safety_score(group)
            composite_score = self.calculate_composite_score(group)
            
            score_breakdown = {
                'time': time_score,
                'distance': distance_score,
                'safety': safety_score,
                'composite': composite_score
            }
            
            ranked.append((group, composite_score, score_breakdown))
        
        # Sort by composite score (highest first)
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Ranked {len(ranked)} route groups")
        for i, (group, score, _) in enumerate(ranked[:3]):
            logger.info(f"  {i+1}. {group.id}: {score:.2f} points ({group.frequency} uses)")
        
        return ranked
    
    def get_optimal_route(self) -> Tuple[RouteGroup, float, Dict[str, float]]:
        """
        Get the optimal route (highest composite score).
        
        Returns:
            Tuple of (RouteGroup, composite_score, score_breakdown)
        """
        ranked = self.rank_routes()
        
        if not ranked:
            raise ValueError("No routes to optimize")
        
        return ranked[0]
    
    def get_route_recommendations(self) -> Dict[str, Any]:
        """
        Get route recommendations with explanations.
        
        Returns:
            Dictionary with recommendations
        """
        ranked = self.rank_routes()
        
        if not ranked:
            return {'error': 'No routes available'}
        
        optimal = ranked[0]
        optimal_group, optimal_score, optimal_breakdown = optimal
        optimal_metrics = self.metrics[optimal_group.id]
        
        # Find best alternative (different route with good score)
        alternative = None
        for group, score, breakdown in ranked[1:]:
            # Check if it's significantly different from optimal
            similarity_threshold = 0.9  # Would need actual similarity calculation
            alternative = (group, score, breakdown)
            break
        
        recommendations = {
            'optimal': {
                'id': optimal_group.id,
                'direction': optimal_group.direction,
                'score': optimal_score,
                'breakdown': optimal_breakdown,
                'frequency': optimal_group.frequency,
                'avg_duration_min': optimal_metrics.avg_duration / 60,
                'avg_distance_km': optimal_metrics.avg_distance / 1000,
                'avg_speed_kmh': optimal_metrics.avg_speed * 3.6,
                'consistency': optimal_metrics.consistency_score,
                'reason': self._generate_recommendation_reason(optimal_breakdown)
            }
        }
        
        if alternative:
            alt_group, alt_score, alt_breakdown = alternative
            alt_metrics = self.metrics[alt_group.id]
            recommendations['alternative'] = {
                'id': alt_group.id,
                'direction': alt_group.direction,
                'score': alt_score,
                'breakdown': alt_breakdown,
                'frequency': alt_group.frequency,
                'avg_duration_min': alt_metrics.avg_duration / 60,
                'avg_distance_km': alt_metrics.avg_distance / 1000,
                'avg_speed_kmh': alt_metrics.avg_speed * 3.6,
                'reason': 'Good alternative for variety'
            }
        
        return recommendations
    
    def _generate_recommendation_reason(self, breakdown: Dict[str, float]) -> str:
        """
        Generate human-readable reason for recommendation.
        
        Args:
            breakdown: Score breakdown dictionary
            
        Returns:
            Reason string
        """
        reasons = []
        
        if breakdown['time'] > 80:
            reasons.append("fastest route")
        if breakdown['distance'] > 80:
            reasons.append("shortest distance")
        if breakdown['safety'] > 80:
            reasons.append("most familiar and safe")
        
        if not reasons:
            reasons.append("best overall balance")
        
        return "Recommended as " + " and ".join(reasons)

# Made with Bob
