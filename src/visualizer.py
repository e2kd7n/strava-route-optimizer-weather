"""
Visualization module.

Generates interactive maps using Folium.
"""

import logging
from typing import List, Dict, Any, Optional

import folium
from folium import plugins

from .route_analyzer import RouteGroup
from .location_finder import Location
from .route_namer import RouteNamer

logger = logging.getLogger(__name__)


class RouteVisualizer:
    """Creates interactive map visualizations of routes."""
    
    def __init__(self, route_groups: List[RouteGroup], home: Location,
                 work: Location, config):
        """
        Initialize route visualizer.
        
        Args:
            route_groups: List of RouteGroup objects
            home: Home location
            work: Work location
            config: Configuration object
        """
        self.route_groups = route_groups
        self.home = home
        self.work = work
        self.config = config
        self.map = None
        self.route_namer = RouteNamer(config)
        self.route_names = {}  # Map route_id to human-readable name
        
    def create_base_map(self) -> folium.Map:
        """
        Create base map centered between home and work.
        
        Returns:
            Folium Map object
        """
        # Calculate center point
        center_lat = (self.home.lat + self.work.lat) / 2
        center_lon = (self.home.lon + self.work.lon) / 2
        
        # Get zoom level from config
        zoom_level = self.config.get('visualization.map.zoom_level', 13)
        tile_layer = self.config.get('visualization.map.tile_layer', 'OpenStreetMap')
        
        # Create map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles=tile_layer
        )
        
        logger.info(f"Created base map centered at ({center_lat:.4f}, {center_lon:.4f})")
        
        return m
    
    def add_route_layer(self, route_group: RouteGroup, color: str,
                       weight: int, is_optimal: bool = False,
                       route_name: Optional[str] = None) -> None:
        """
        Add route layer to map.
        
        Args:
            route_group: RouteGroup object
            color: Line color
            weight: Line weight
            is_optimal: Whether this is the optimal route
            route_name: Human-readable route name
        """
        if self.map is None:
            raise ValueError("Map not initialized. Call create_base_map() first.")
        
        # Get representative route coordinates
        coords = route_group.representative_route.coordinates
        
        # Use provided name or generate one
        if route_name is None:
            route_name = self.route_namer.generate_simple_name(
                route_group.id, route_group.direction
            )
        
        # Store route name
        self.route_names[route_group.id] = route_name
        
        # Create popup with statistics
        popup_html = self._create_popup_html(route_group, route_name)
        
        # Determine opacity
        opacity = 0.9 if is_optimal else 0.6
        
        # Add polyline with custom class for JavaScript interaction
        folium.PolyLine(
            coords,
            color=color,
            weight=weight,
            opacity=opacity,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{route_name} ({route_group.frequency} uses)",
            className=f"route-line route-{route_group.id}"
        ).add_to(self.map)
        
        logger.debug(f"Added route layer: {route_name} ({color})")
    
    def add_location_markers(self) -> None:
        """Add markers for home and work locations."""
        if self.map is None:
            raise ValueError("Map not initialized. Call create_base_map() first.")
        
        # Home marker (green house icon)
        folium.Marker(
            [self.home.lat, self.home.lon],
            popup=f"<b>Home</b><br>{self.home.activity_count} activities",
            tooltip="Home",
            icon=folium.Icon(color='green', icon='home', prefix='fa')
        ).add_to(self.map)
        
        # Work marker (blue building icon)
        folium.Marker(
            [self.work.lat, self.work.lon],
            popup=f"<b>Work</b><br>{self.work.activity_count} activities",
            tooltip="Work",
            icon=folium.Icon(color='blue', icon='building', prefix='fa')
        ).add_to(self.map)
        
        logger.info("Added location markers")
    
    def add_heatmap_layer(self) -> None:
        """Add heatmap overlay showing most frequently used paths."""
        if self.map is None:
            raise ValueError("Map not initialized. Call create_base_map() first.")
        
        # Collect all coordinates from all routes
        heat_data = []
        
        for group in self.route_groups:
            for route in group.routes:
                # Add coordinates with weight based on frequency
                for coord in route.coordinates:
                    heat_data.append([coord[0], coord[1]])
        
        if heat_data:
            # Create heatmap
            plugins.HeatMap(
                heat_data,
                radius=15,
                blur=20,
                max_zoom=13,
                gradient={0.4: 'blue', 0.6: 'lime', 0.8: 'yellow', 1.0: 'red'}
            ).add_to(self.map)
            
            logger.info(f"Added heatmap with {len(heat_data)} points")
    
    def _create_popup_html(self, route_group: RouteGroup, route_name: str) -> str:
        """
        Create HTML popup content for route.
        
        Args:
            route_group: RouteGroup object
            route_name: Human-readable route name
            
        Returns:
            HTML string
        """
        # Calculate metrics
        routes = route_group.routes
        durations = [r.duration for r in routes]
        distances = [r.distance for r in routes]
        
        import numpy as np
        avg_duration = np.mean(durations) / 60  # Convert to minutes
        avg_distance = np.mean(distances) / 1000  # Convert to km
        
        html = f"""
        <div style="font-family: Arial, sans-serif;">
            <h4 style="margin: 0 0 10px 0;">{route_name}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr>
                    <td><b>Direction:</b></td>
                    <td>{route_group.direction.replace('_', ' ').title()}</td>
                </tr>
                <tr>
                    <td><b>Frequency:</b></td>
                    <td>{route_group.frequency} times</td>
                </tr>
                <tr>
                    <td><b>Avg Duration:</b></td>
                    <td>{avg_duration:.1f} min</td>
                </tr>
                <tr>
                    <td><b>Avg Distance:</b></td>
                    <td>{avg_distance:.2f} km</td>
                </tr>
            </table>
        </div>
        """
        
        return html
    
    def generate_map(self, optimal_route: Optional[RouteGroup] = None,
                    output_path: Optional[str] = None,
                    ranked_routes: Optional[List[tuple]] = None) -> str:
        """
        Generate complete interactive map.
        
        Args:
            optimal_route: Optional RouteGroup to highlight as optimal
            output_path: Optional path to save HTML file
            ranked_routes: Optional list of (RouteGroup, score, breakdown) tuples for naming
            
        Returns:
            HTML string of the map
        """
        # Create base map
        self.map = self.create_base_map()
        
        # Get colors from config
        optimal_color = self.config.get('visualization.colors.optimal', '#FF0000')
        alternative_colors = self.config.get('visualization.colors.alternative',
                                            ['#00FF00', '#0000FF', '#FFA500', '#800080'])
        
        optimal_weight = self.config.get('visualization.route_weight.optimal', 5)
        alternative_weight = self.config.get('visualization.route_weight.alternative', 3)
        
        # Generate route names
        if ranked_routes:
            for rank, (group, score, breakdown) in enumerate(ranked_routes, 1):
                route_name = self.route_namer.generate_simple_name(
                    group.id, group.direction, rank
                )
                self.route_names[group.id] = route_name
        
        # Add route layers
        color_idx = 0
        for group in self.route_groups:
            is_optimal = (optimal_route is not None and group.id == optimal_route.id)
            
            if is_optimal:
                color = optimal_color
                weight = optimal_weight
            else:
                color = alternative_colors[color_idx % len(alternative_colors)]
                weight = alternative_weight
                color_idx += 1
            
            route_name = self.route_names.get(group.id)
            self.add_route_layer(group, color, weight, is_optimal, route_name)
        
        # Add location markers
        self.add_location_markers()
        
        # Add layer control
        folium.LayerControl().add_to(self.map)
        
        # Save to file if path provided
        if output_path:
            self.map.save(output_path)
            logger.info(f"Map saved to {output_path}")
        
        # Return HTML
        return self.map._repr_html_()
    
    def get_route_names(self) -> Dict[str, str]:
        """
        Get mapping of route IDs to human-readable names.
        
        Returns:
            Dictionary mapping route_id to route_name
        """
        return self.route_names.copy()
    
    def create_legend_html(self, ranked_routes: List[tuple]) -> str:
        """
        Create HTML legend for route comparison.
        
        Args:
            ranked_routes: List of (RouteGroup, score, breakdown) tuples
            
        Returns:
            HTML string
        """
        html = """
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h3>Route Comparison</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #f0f0f0;">
                        <th style="padding: 8px; border: 1px solid #ddd;">Rank</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Route</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Score</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Uses</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for i, (group, score, breakdown) in enumerate(ranked_routes[:5]):
            html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{i+1}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{group.id}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{score:.1f}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{group.frequency}</td>
                </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html

# Made with Bob
