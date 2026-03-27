"""
Visualization module.

Generates interactive maps using Folium.

Copyright (c) 2024-2026 e2kd7n
Licensed under the MIT License - see LICENSE file for details.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

import folium
from folium import plugins
from geopy.distance import geodesic

from .route_analyzer import RouteGroup
from .location_finder import Location
from .route_namer import RouteNamer
from .units import UnitConverter

logger = logging.getLogger(__name__)


class RouteVisualizer:
    """Creates interactive map visualizations of routes."""
    
    def __init__(self, route_groups: List[RouteGroup], home: Location,
                 work: Location, config, long_rides=None, long_ride_analyzer=None,
                 weather_fetcher=None):
        """
        Initialize route visualizer.
        
        Args:
            route_groups: List of RouteGroup objects
            home: Home location
            work: Work location
            config: Configuration object
            long_rides: Optional list of LongRide objects
            long_ride_analyzer: Optional LongRideAnalyzer instance
            weather_fetcher: Optional WeatherFetcher instance for current conditions
        """
        self.route_groups = route_groups
        self.home = home
        self.work = work
        self.config = config
        self.map = None
        self.route_namer = RouteNamer(config)
        self.route_names = {}  # Map route_id to human-readable name
        self.route_colors = {}  # Map route_id to color
        self.long_rides = long_rides or []
        self.long_ride_analyzer = long_ride_analyzer
        self.weather_fetcher = weather_fetcher
        
        # Initialize unit converter
        unit_system = config.get('units.system', 'metric')
        self.units = UnitConverter(unit_system)
        
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
        
        # Create map without tiles initially (we'll add them in order)
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles=None,  # Don't add default tiles
            height='800px',  # Increased from default 600px
            control_scale=True
        )
        
        # Add basemap layers in order - last one added will be the default visible layer
        # OpenStreetMap (colorful, detailed)
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='OpenStreetMap',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Satellite imagery (Esri World Imagery)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        # CartoDB Positron (clean grayscale) - add last so it's the default
        folium.TileLayer(
            tiles='CartoDB Positron',
            name='CartoDB Positron',
            overlay=False,
            control=True
        ).add_to(m)
        
        logger.info(f"Created base map centered at ({center_lat:.4f}, {center_lon:.4f}) with multiple basemap options (default: CartoDB Positron)")
        
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
        
        if not coords:
            logger.warning(f"Route {route_group.id} has no coordinates")
            return
        
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
        
        # Store route bounds for zoom functionality
        route_bounds = [[coord[0], coord[1]] for coord in coords]
        
        # Determine direction class for filtering
        direction_class = f"direction-{route_group.direction}"
        
        # Determine plus route class for filtering
        plus_class = "plus-route" if route_group.is_plus_route else ""
        
        # Build className with all applicable classes
        class_names = f"route-line route-{route_group.id} {direction_class} {plus_class}".strip()
        
        # Add polyline with custom class and data attributes for JavaScript interaction
        folium.PolyLine(
            coords,
            color=color,
            weight=weight,
            opacity=opacity,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{route_name} ({route_group.frequency} uses)",
            className=class_names,
            # Store bounds as data attribute for JavaScript access
            name=f"route-{route_group.id}"
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
    
    def add_weather_display(self) -> None:
        """Add current weather conditions display to the map."""
        if self.map is None:
            raise ValueError("Map not initialized. Call create_base_map() first.")
        
        if self.weather_fetcher is None:
            logger.debug("No weather fetcher provided, skipping weather display")
            return
        
        try:
            # Get weather for the center point between home and work
            center_lat = (self.home.lat + self.work.lat) / 2
            center_lon = (self.home.lon + self.work.lon) / 2
            
            conditions = self.weather_fetcher.get_current_conditions(center_lat, center_lon)
            
            if not conditions:
                logger.warning("Could not fetch current weather conditions")
                return
            
            # Convert temperature based on unit system
            temp_c = conditions.get('temp_c', 0)
            if self.units.system == 'imperial':
                temp = temp_c * 9/5 + 32
                temp_unit = '°F'
            else:
                temp = temp_c
                temp_unit = '°C'
            
            # Convert wind speed based on unit system
            wind_kph = conditions.get('wind_speed_kph', 0)
            if self.units.system == 'imperial':
                wind_speed = wind_kph * 0.621371  # Convert to mph
                wind_unit = 'mph'
            else:
                wind_speed = wind_kph
                wind_unit = 'km/h'
            
            # Get wind direction
            wind_dir = conditions.get('wind_direction_cardinal', 'N/A')
            wind_deg = conditions.get('wind_direction_deg', 0)
            
            # Get precipitation
            precip_mm = conditions.get('precipitation_mm', 0)
            if self.units.system == 'imperial':
                precip = precip_mm * 0.0393701  # Convert to inches
                precip_unit = 'in'
            else:
                precip = precip_mm
                precip_unit = 'mm'
            
            # Create weather info HTML
            weather_html = f"""
            <div style="position: fixed;
                        top: 10px;
                        right: 60px;
                        width: 200px;
                        background-color: white;
                        border: 2px solid #ccc;
                        border-radius: 5px;
                        padding: 10px;
                        font-family: Arial, sans-serif;
                        font-size: 12px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                        z-index: 1000;">
                <h4 style="margin: 0 0 8px 0; font-size: 14px; color: #333;">
                    🌤️ Current Conditions
                </h4>
                <div style="line-height: 1.6;">
                    <div><b>🌡️ Temp:</b> {temp:.1f}{temp_unit}</div>
                    <div><b>💨 Wind:</b> {wind_speed:.1f} {wind_unit} {wind_dir}</div>
                    <div style="font-size: 10px; color: #666; margin-left: 20px;">
                        ({wind_deg}°)
                    </div>
                    <div><b>💧 Precip:</b> {precip:.1f} {precip_unit}</div>
                </div>
                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee;
                            font-size: 10px; color: #666;">
                    Updated: {conditions.get('timestamp', 'N/A')}
                </div>
            </div>
            """
            
            # Add weather display to map
            self.map.get_root().html.add_child(folium.Element(weather_html))
            
            logger.info(f"Added weather display: {temp:.1f}{temp_unit}, "
                       f"Wind {wind_speed:.1f} {wind_unit} from {wind_dir}")
            
        except Exception as e:
            logger.error(f"Failed to add weather display: {e}")
    
    def add_heatmap_layer(self) -> None:
        """Add heatmap overlay showing most frequently used paths."""
        if self.map is None:
            raise ValueError("Map not initialized. Call create_base_map() first.")
        
        # Collect all coordinates from all routes
        heat_data = []
        
        for group in self.route_groups:
            for route in group.routes:
                # Add all coordinates
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
            
            logger.info(f"Added heatmap with {len(heat_data)} points (trimmed for privacy)")
    
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
        
        # Guard against empty route groups
        if not routes:
            return "<div>No route data available</div>"
        
        durations = [r.duration for r in routes]
        distances = [r.distance for r in routes]
        
        import numpy as np
        avg_duration = np.mean(durations) / 60  # Convert to minutes
        avg_distance_m = np.mean(distances)  # meters
        
        # Format distance using unit converter
        distance_str = self.units.distance(avg_distance_m)
        
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
                    <td>{distance_str}</td>
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
        
        # Generate route names using geocoding
        if ranked_routes:
            for rank, (group, score, breakdown) in enumerate(ranked_routes, 1):
                # Use name_route() to get geocoded street names if available
                if group.representative_route and group.representative_route.coordinates:
                    route_name = self.route_namer.name_route(
                        group.representative_route.coordinates,
                        group.id,
                        group.direction
                    )
                else:
                    # Fallback to simple name if no coordinates available
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
            
            # Store the color for this route
            self.route_colors[group.id] = color
            
            route_name = self.route_names.get(group.id)
            self.add_route_layer(group, color, weight, is_optimal, route_name)
        
        # Add location markers
        self.add_location_markers()
        
        # Add current weather display
        self.add_weather_display()
        
        # Add layer control
        folium.LayerControl().add_to(self.map)
        
        # Save to file if path provided
        if output_path:
            self.map.save(output_path)
            logger.info(f"Map saved to {output_path}")
        
        # Add JavaScript for route interaction (zoom and fade)
        self._add_route_interaction_javascript()
        
        # Add JavaScript for long rides click handler if long rides are available
        self._add_long_rides_javascript()
        
        # Return HTML
        return self.map._repr_html_()
    
    def generate_preview_map(self, optimal_route: RouteGroup) -> str:
        """
        Generate a small preview map showing only the optimal route.
        
        Args:
            optimal_route: RouteGroup to display
            
        Returns:
            HTML string of the preview map
        """
        # Create a smaller base map
        center_lat = (self.home.lat + self.work.lat) / 2
        center_lon = (self.home.lon + self.work.lon) / 2
        
        preview_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=self.config.get('visualization.map.zoom_level', 13),
            tiles=None,
            height='200px',  # Small preview pane
            control_scale=False
        )
        
        # Add CartoDB Positron basemap
        folium.TileLayer(
            tiles='CartoDB Positron',
            name='CartoDB Positron',
            overlay=False,
            control=False
        ).add_to(preview_map)
        
        # Add only the optimal route
        optimal_color = self.config.get('visualization.colors.optimal', '#FF0000')
        optimal_weight = self.config.get('visualization.route_weight.optimal', 5)
        
        if optimal_route.representative_route and optimal_route.representative_route.coordinates:
            coords = optimal_route.representative_route.coordinates
            
            # Add route polyline
            folium.PolyLine(
                coords,
                color=optimal_color,
                weight=optimal_weight,
                opacity=0.8,
                popup=f"<b>Optimal Route</b><br>{self.route_names.get(optimal_route.id, optimal_route.id)}"
            ).add_to(preview_map)
            
            # Fit bounds to route
            preview_map.fit_bounds(coords)
        
        # Add home and work markers
        folium.Marker(
            [self.home.lat, self.home.lon],
            popup='<b>🏠 Home</b>',
            icon=folium.Icon(color='green', icon='home', prefix='fa')
        ).add_to(preview_map)
        
        folium.Marker(
            [self.work.lat, self.work.lon],
            popup='<b>🏢 Work</b>',
            icon=folium.Icon(color='blue', icon='building', prefix='fa')
        ).add_to(preview_map)
        
        # Add click handler to scroll to full map
        from folium.elements import Element
        js_code = """
        <script>
        // Add click handler to preview map to scroll to full map
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(function() {
                var previewMap = document.querySelector('#preview-map-container .folium-map');
                if (previewMap) {
                    previewMap.style.cursor = 'pointer';
                    previewMap.addEventListener('click', function() {
                        document.getElementById('full-map-section').scrollIntoView({behavior: 'smooth'});
                    });
                }
            }, 500);
        });
        </script>
        """
        preview_map.get_root().html.add_child(Element(js_code))
        
        return preview_map._repr_html_()
    
    def get_route_colors(self) -> Dict[str, str]:
        """
        Get mapping of route IDs to their colors.
        
        Returns:
            Dictionary mapping route_id to color hex code
        """
        return self.route_colors.copy()
    
    def _add_long_rides_javascript(self) -> None:
        """Add JavaScript for interactive long ride recommendations on map click."""
        if self.map is None:
            return
        
        # Prepare long rides data for JavaScript
        import json
        long_rides_data = []
        if self.long_rides and self.long_ride_analyzer:
            for ride in self.long_rides[:100]:  # Limit to 100 rides for performance
                # Get midpoint for each ride
                mid_idx = len(ride.coordinates) // 2 if ride.coordinates else 0
                midpoint = ride.coordinates[mid_idx] if ride.coordinates else ride.start_location
                
                # Convert distance to appropriate unit
                distance_m = ride.distance_km * 1000
                distance_value = self.units.distance_value(distance_m)
                
                # Clean activity name - remove newlines and other problematic characters
                clean_name = ride.name.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                # Remove multiple spaces
                clean_name = ' '.join(clean_name.split())
                
                long_rides_data.append({
                    'id': ride.activity_id,
                    'name': clean_name,
                    'distance': round(distance_value, 1),  # In target unit
                    'duration_hours': round(ride.duration_hours, 2),
                    'is_loop': ride.is_loop,
                    'midpoint': [midpoint[0], midpoint[1]],
                    'start': [ride.start_location[0], ride.start_location[1]],
                    'strava_url': f'https://www.strava.com/activities/{ride.activity_id}'
                })
        
        # Convert to JSON for JavaScript embedding
        long_rides_json = json.dumps(long_rides_data, ensure_ascii=False)
        num_long_rides = len(long_rides_data)
        
        # Get unit labels for JavaScript
        distance_unit = self.units.distance_unit()
        
        # JavaScript code for click handling with embedded data
        js_code = f"""
        <script>
        // Long Rides Data (embedded from Python)
        var longRidesData = {long_rides_json};
        var longRidesEnabled = false;  // Disabled on commute map, only for long rides tab
        var clickMarker = null;
        var recommendationLayers = [];
        var distanceUnit = '{distance_unit}';
        
        // Calculate distance between two points (Haversine formula)
        function calculateDistance(lat1, lon1, lat2, lon2) {{
            var R = 6371; // Earth's radius in km
            var dLat = (lat2 - lat1) * Math.PI / 180;
            var dLon = (lon2 - lon1) * Math.PI / 180;
            var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                    Math.sin(dLon/2) * Math.sin(dLon/2);
            var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return R * c;
        }}
        
        // Find rides near a location
        function findNearbyRides(lat, lon, radiusKm, targetDistance, targetDuration) {{
            var nearby = [];
            for (var i = 0; i < longRidesData.length; i++) {{
                var ride = longRidesData[i];
                var distance = calculateDistance(lat, lon, ride.midpoint[0], ride.midpoint[1]);
                
                if (distance <= radiusKm) {{
                    // Apply filters if specified
                    if (targetDistance && Math.abs(ride.distance_km - targetDistance) > 20) continue;
                    if (targetDuration && Math.abs(ride.duration_hours - targetDuration) > 1.5) continue;
                    
                    nearby.push({{
                        ride: ride,
                        distance: distance
                    }});
                }}
            }}
            
            // Sort by distance to clicked location
            nearby.sort(function(a, b) {{ return a.distance - b.distance; }});
            return nearby.slice(0, 5); // Return top 5
        }}
        
        // Add click event listener to map
        document.addEventListener('DOMContentLoaded', function() {{
            // Try multiple ways to find the Leaflet map
            var map = null;
            var mapElement = document.querySelector('.folium-map');
            
            // Method 1: Try _leaflet_id
            if (mapElement && mapElement._leaflet_id) {{
                map = window[mapElement._leaflet_id];
                console.log('Method 1 (_leaflet_id):', map ? 'Found' : 'Not found');
            }}
            
            // Method 2: Try finding in window.L.Map instances
            if (!map && typeof L !== 'undefined' && L.Map) {{
                for (var key in window) {{
                    if (window[key] instanceof L.Map) {{
                        map = window[key];
                        console.log('Method 2 (L.Map instance):', 'Found as window.' + key);
                        break;
                    }}
                }}
            }}
            
            // Method 3: Check if map is stored differently
            if (!map) {{
                console.log('Available window properties with "map":', Object.keys(window).filter(function(k) {{ return k.toLowerCase().includes('map'); }}));
                console.log('mapElement._leaflet_id:', mapElement ? mapElement._leaflet_id : 'no element');
            }}
            
            if (map && typeof map.on === 'function') {{
                console.log('Long rides: Leaflet map found, attaching click handler');
                map.on('click', function(e) {{
                    if (!longRidesEnabled) return;
                    
                    var lat = e.latlng.lat;
                    var lon = e.latlng.lng;
                    
                    // Remove previous marker and layers
                    if (clickMarker) {{
                        map.removeLayer(clickMarker);
                    }}
                    recommendationLayers.forEach(function(layer) {{
                        map.removeLayer(layer);
                    }});
                    recommendationLayers = [];
                    
                    // Add new marker
                    clickMarker = L.marker([lat, lon], {{
                        icon: L.icon({{
                            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
                            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                            iconSize: [25, 41],
                            iconAnchor: [12, 41],
                            popupAnchor: [1, -34],
                            shadowSize: [41, 41]
                        }})
                    }}).addTo(map);
                    
                    // Show loading
                    var loadingHtml = '<div style="text-align: center; padding: 10px;">' +
                                     '<b>Finding Long Rides...</b><br>' +
                                     '<small>Searching {num_long_rides} rides</small></div>';
                    clickMarker.bindPopup(loadingHtml).openPopup();
                    
                    // Find nearby rides
                    setTimeout(function() {{
                        var searchRadius = 10; // km
                        var targetDist = null;
                        var targetDur = null;
                        var nearbyRides = findNearbyRides(lat, lon, searchRadius, targetDist, targetDur);
                        
                        var html = createRecommendationHtml(lat, lon, nearbyRides, searchRadius);
                        clickMarker.getPopup().setContent(html);
                    }}, 100);
                }});
            }} else {{
                console.warn('Leaflet map object not found for long rides click handler');
            }}
        }});
        
        function createRecommendationHtml(lat, lon, nearbyRides, searchRadius) {{
            var html = '<div style="font-family: Arial, sans-serif; min-width: 300px; max-width: 400px;">' +
                       '<h4 style="margin: 0 0 10px 0; color: #8B008B;">🚴 Long Ride Recommendations</h4>' +
                       '<p style="font-size: 11px; color: #666; margin: 5px 0;">Location: ' + lat.toFixed(4) + ', ' + lon.toFixed(4) + '</p>' +
                       '<p style="font-size: 11px; color: #666; margin: 5px 0;">Search radius: ' + searchRadius + ' ' + distanceUnit + '</p>';
            
            if (nearbyRides.length === 0) {{
                html += '<div style="background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #ffc107;">' +
                        '<p style="margin: 0; font-size: 12px;">No rides found within ' + searchRadius + ' ' + distanceUnit + ' of this location.</p>' +
                        '<p style="margin: 5px 0 0 0; font-size: 11px; color: #666;">Try clicking closer to areas you have ridden before.</p>' +
                        '</div>';
            }} else {{
                html += '<div style="margin: 10px 0;"><b style="font-size: 12px;">Found ' + nearbyRides.length + ' rides:</b></div>';
                
                nearbyRides.forEach(function(item, index) {{
                    var ride = item.ride;
                    var bgColor = index === 0 ? '#e8f5e9' : '#f5f5f5';
                    var borderColor = index === 0 ? '#4caf50' : '#ddd';
                    
                    html += '<div style="background: ' + bgColor + '; padding: 8px; border-radius: 4px; margin: 5px 0; border-left: 3px solid ' + borderColor + ';">' +
                            '<div style="font-size: 12px; font-weight: bold; margin-bottom: 3px;">' + (index + 1) + '. ' + ride.name + '</div>' +
                            '<div style="font-size: 11px; color: #666;">' +
                            '<span>📏 ' + ride.distance + ' ' + distanceUnit + '</span> | ' +
                            '<span>⏱️ ' + ride.duration_hours.toFixed(1) + ' hrs</span> | ' +
                            '<span>📍 ' + item.distance.toFixed(1) + ' ' + distanceUnit + ' away</span>' +
                            (ride.is_loop ? ' | <span style="color: #4caf50;">🔄 Loop</span>' : '') +
                            '</div>' +
                            '<a href="' + ride.strava_url + '" target="_blank" style="font-size: 10px; color: #fc4c02; text-decoration: none;">View on Strava →</a>' +
                            '</div>';
                }});
            }}
            
            html += '<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 10px; color: #999;">' +
                    'Showing rides from your Strava history. Weather analysis coming soon!' +
                    '</div></div>';
            
            return html;
        }}
        
        // Toggle long rides feature
        function toggleLongRides() {{
            longRidesEnabled = !longRidesEnabled;
            console.log('Long rides feature:', longRidesEnabled ? 'enabled' : 'disabled');
        }}
        </script>
        """
        
        # Add the JavaScript to the map
        from folium import Element
        self.map.get_root().html.add_child(Element(js_code))
        
        logger.info(f"Added long rides JavaScript with {len(long_rides_data)} rides embedded")
    
    def _add_route_interaction_javascript(self) -> None:
        """Add JavaScript for route click interactions (zoom and fade) and filter buttons."""
        if self.map is None:
            return
        
        # Collect route bounds for each route group
        import json
        route_data = {}
        for group in self.route_groups:
            # Collect ALL coordinates from ALL routes in the group to ensure bounds encompass every variation
            all_coords = []
            for route in group.routes:
                if route.coordinates:
                    all_coords.extend([[coord[0], coord[1]] for coord in route.coordinates])
            
            if all_coords:
                route_data[f"route-{group.id}"] = {
                    'bounds': all_coords,
                    'name': self.route_names.get(group.id, group.id),
                    'direction': group.direction
                }
        
        
        route_data_json = json.dumps(route_data)
        
        js_code = f"""
        <script>
        // Route interaction data
        var routeData = {route_data_json};
        var selectedRoutes = new Set();  // Track multiple selected routes
        var currentFilter = 'all';
        var showPlusRoutes = true;  // Track plus routes filter state
        
        // Wait for map to be ready
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Route interaction: DOMContentLoaded fired');
            setTimeout(function() {{
                console.log('Route interaction: setTimeout fired');
                
                // Make all attribution links open in new tabs
                var attributionLinks = document.querySelectorAll('.leaflet-control-attribution a');
                attributionLinks.forEach(function(link) {{
                    link.setAttribute('target', '_blank');
                    link.setAttribute('rel', 'noopener noreferrer');
                }});
                console.log('Route interaction: Set', attributionLinks.length, 'attribution links to open in new tabs');
                
                // Find all route polylines - use path.route-line for SVG elements
                var routeLines = document.querySelectorAll('path.route-line');
                console.log('Route interaction: Found', routeLines.length, 'route lines');
                
                // Make routes clickable by setting CSS
                routeLines.forEach(function(routeLine) {{
                    routeLine.style.cursor = 'pointer';
                    routeLine.style.pointerEvents = 'auto';
                    routeLine.style.zIndex = '1000';
                }});
                
                // Disable pointer events on tile pane so clicks reach routes
                var tilePane = document.querySelector('.leaflet-tile-pane');
                if (tilePane) {{
                    tilePane.style.pointerEvents = 'none';
                    console.log('Route interaction: Disabled tile pane pointer events');
                }}
                
                // Set overlay pane to pass through clicks, but individual paths will catch them
                var overlayPane = document.querySelector('.leaflet-overlay-pane');
                if (overlayPane) {{
                    overlayPane.style.zIndex = '1000';
                    overlayPane.style.pointerEvents = 'none';  // Let clicks pass through
                    console.log('Route interaction: Set overlay pane to pass-through mode');
                }}
                
                // Find SVG element and enable pointer events on it
                var svgElement = document.querySelector('.leaflet-overlay-pane svg');
                if (svgElement) {{
                    svgElement.style.pointerEvents = 'auto';  // SVG catches clicks
                    console.log('Route interaction: Enabled SVG pointer events');
                }}
                
                // Attach listener to map container to catch all clicks
                var mapContainer = document.querySelector('.folium-map');
                if (mapContainer) {{
                    console.log('Route interaction: Found map container, attaching delegated listener');
                    
                    mapContainer.addEventListener('click', function(e) {{
                        console.log('Map clicked! Target:', e.target.tagName, 'Classes:', e.target.className);
                        var target = e.target;
                        
                        // Check if clicked element is a route line (path with route-line class)
                        if (target.tagName && target.tagName.toLowerCase() === 'path' &&
                            target.classList && target.classList.contains('route-line')) {{
                            console.log('Route clicked via delegation!');
                            e.stopPropagation();
                            e.preventDefault();
                            // Get route ID from class name - need to match the actual route ID, not "route-line"
                            var classes = target.className.baseVal || target.className;
                            console.log('Route classes:', classes);
                            // Match pattern like "route-home_to_work_63" or "route-work_to_home_76"
                            var routeMatch = classes.match(/route-((?:home_to_work|work_to_home)_\\d+)/);
                            if (!routeMatch) {{
                                console.log('No route match found in classes:', classes);
                                return;
                            }}
                            
                            var routeId = 'route-' + routeMatch[1];
                            console.log('Route ID:', routeId);
                            var data = routeData[routeId];
                            if (!data) {{
                                console.log('No data found for route:', routeId);
                                return;
                            }}
                            console.log('Route data:', data);
                            
                            // Toggle selection
                            if (selectedRoutes.has(routeId)) {{
                                // Deselect this route
                                selectedRoutes.delete(routeId);
                                console.log('Deselected route:', routeId);
                            }} else {{
                                // Select this route
                                selectedRoutes.add(routeId);
                                console.log('Selected route:', routeId);
                            }}
                            
                            // Update all route visibility
                            var allRouteLines = document.querySelectorAll('path.route-line');
                            if (selectedRoutes.size === 0) {{
                                // No routes selected - show all (respecting filters)
                                resetRouteStyles();
                            }} else {{
                                // Some routes selected - hide unselected, show selected
                                allRouteLines.forEach(function(line) {{
                                    var lineClasses = line.className.baseVal || line.className;
                                    var lineRouteMatch = lineClasses.match(/route-((?:home_to_work|work_to_home)_\\d+)/);
                                    if (!lineRouteMatch) return;
                                    
                                    var lineRouteId = 'route-' + lineRouteMatch[1];
                                    
                                    // Check if route should be visible based on current filters
                                    var matchesDirection = (currentFilter === 'all') || (lineClasses.indexOf('direction-' + currentFilter) !== -1);
                                    var isPlus = lineClasses.indexOf('plus-route') !== -1;
                                    var matchesPlusFilter = showPlusRoutes || !isPlus;
                                    var shouldBeVisible = matchesDirection && matchesPlusFilter;
                                    
                                    if (!shouldBeVisible) {{
                                        // Route is filtered out - keep it hidden
                                        line.style.display = 'none';
                                    }} else if (selectedRoutes.has(lineRouteId)) {{
                                        // Selected route - show with original color and thicker line
                                        line.style.display = '';
                                        line.style.opacity = '1.0';
                                        line.style.strokeWidth = '6';
                                        line.style.stroke = '';  // Keep original color
                                        // Bring to front by moving to end of parent (SVG rendering order)
                                        if (line.parentNode) {{
                                            line.parentNode.appendChild(line);
                                        }}
                                    }} else {{
                                        // Unselected route - subdue with low opacity and gray color
                                        line.style.display = '';
                                        line.style.opacity = '0.15';
                                        line.style.strokeWidth = '2';
                                        line.style.stroke = '#999999';  // Gray color
                                    }}
                                }});
                                
                                // Zoom to show all selected routes
                                zoomToSelectedRoutes();
                            }}
                        }}
                    }}, true); // Use capture phase
                    console.log('Route interaction: Attached delegated click listener to map container');
                }} else {{
                    console.warn('Route interaction: Map container not found, cannot attach delegated listener');
                }}
                
                // Click on map background to reset
                // Try multiple ways to find the Leaflet map
                var map = null;
                var mapElement = document.querySelector('.folium-map');
                
                // Method 1: Try _leaflet_id
                if (mapElement && mapElement._leaflet_id) {{
                    map = window[mapElement._leaflet_id];
                    console.log('Route reset: Method 1 (_leaflet_id):', map ? 'Found' : 'Not found');
                }}
                
                // Method 2: Try finding in window.L.Map instances
                if (!map && typeof L !== 'undefined' && L.Map) {{
                    for (var key in window) {{
                        if (window[key] instanceof L.Map) {{
                            map = window[key];
                            console.log('Route reset: Method 2 (L.Map instance):', 'Found as window.' + key);
                            break;
                        }}
                    }}
                }}
                
                if (map && typeof map.on === 'function') {{
                    console.log('Route reset: Leaflet map found, attaching click handler');
                    map.on('click', function(e) {{
                        // Only reset if not clicking on a route
                        if (selectedRoutes.size > 0 && !e.originalEvent.target.classList.contains('route-line')) {{
                            selectedRoutes.clear();
                            resetRouteStyles();
                        }}
                    }});
                }} else {{
                    console.warn('Route reset: Leaflet map object not found, map click handler not attached');
                }}
            }}, 500); // Wait for map to fully initialize
        }});
        
        // Expose filterRoutes globally so report buttons can call it
        window.filterRoutes = function(filter, showPlusRoutes) {{
            console.log('filterRoutes called with:', filter, 'showPlusRoutes:', showPlusRoutes);
            currentFilter = filter;
            selectedRoutes.clear();  // Clear selections when filtering
            
            // Default showPlusRoutes to true if not provided
            if (typeof showPlusRoutes === 'undefined') {{
                showPlusRoutes = true;
            }}
            
            // Filter routes - need to find SVG path elements
            var routeLines = document.querySelectorAll('path.route-line');
            console.log('Found', routeLines.length, 'route lines');
            
            var visibleCount = 0;
            routeLines.forEach(function(line) {{
                // For SVG elements, use getAttribute to get class
                var classes = line.getAttribute('class') || '';
                
                // Check direction filter
                var matchesDirection = (filter === 'all') || (classes.indexOf('direction-' + filter) !== -1);
                
                // Check plus route filter
                var isPlus = classes.indexOf('plus-route') !== -1;
                var matchesPlusFilter = showPlusRoutes || !isPlus;
                
                // Show only if BOTH conditions are met
                if (matchesDirection && matchesPlusFilter) {{
                    line.style.display = '';
                    line.style.opacity = '';
                    line.style.strokeWidth = '';
                    visibleCount++;
                }} else {{
                    line.style.display = 'none';
                }}
            }});
            
            console.log('Visible routes after filter:', visibleCount);
            
            // Auto-zoom to fit visible routes
            if (filter !== 'all' || !showPlusRoutes) {{
                zoomToFilteredRoutes(filter);
            }} else {{
                resetMapView();
            }}
        }};  // Close window.filterRoutes
        
        // Helper function to find the Leaflet map object
        function findLeafletMap() {{
            var map = null;
            var mapElement = document.querySelector('.folium-map');
            
            // Method 1: Try _leaflet_id
            if (mapElement && mapElement._leaflet_id) {{
                map = window[mapElement._leaflet_id];
            }}
            
            // Method 2: Try finding in window.L.Map instances (this works!)
            if (!map && typeof L !== 'undefined' && L.Map) {{
                for (var key in window) {{
                    if (window[key] instanceof L.Map) {{
                        map = window[key];
                        break;
                    }}
                }}
            }}
            
            return map;
        }}
        
        // Expose zoom functions globally for report to call
        window.zoomToRouteById = function(routeId) {{
            console.log('zoomToRouteById called with:', routeId);
            var fullRouteId = 'route-' + routeId;
            console.log('Looking for route data:', fullRouteId);
            var data = routeData[fullRouteId];
            console.log('Found route data:', data);
            if (data && data.bounds) {{
                console.log('Calling zoomToRoute with bounds:', data.bounds);
                zoomToRoute(data.bounds);
                
                // Also trigger route selection to highlight the route
                selectedRoutes.clear();
                selectedRoutes.add(fullRouteId);
                console.log('Selected route from table click:', fullRouteId);
                
                // Update all route visibility
                var allRouteLines = document.querySelectorAll('path.route-line');
                allRouteLines.forEach(function(line) {{
                    var lineClasses = line.className.baseVal || line.className;
                    var lineRouteMatch = lineClasses.match(/route-((?:home_to_work|work_to_home|test)_\\w+)/);
                    if (!lineRouteMatch) return;
                    
                    var lineRouteId = 'route-' + lineRouteMatch[1];
                    
                    if (selectedRoutes.has(lineRouteId)) {{
                        // Selected route - show with original color and thicker line
                        line.style.display = '';
                        line.style.opacity = '1.0';
                        line.style.strokeWidth = '6';
                        line.style.stroke = '';  // Keep original color
                        // Bring to front by moving to end of parent (SVG rendering order)
                        if (line.parentNode) {{
                            line.parentNode.appendChild(line);
                        }}
                    }} else {{
                        // Unselected route - subdue with low opacity and gray color
                        line.style.display = '';
                        line.style.opacity = '0.15';
                        line.style.strokeWidth = '2';
                        line.style.stroke = '#999999';  // Gray color
                    }}
                }});
            }} else {{
                console.error('No data or bounds found for route:', fullRouteId);
            }}
        }};
        
        window.resetMapView = resetMapView;
        
        function zoomToRoute(bounds) {{
            try {{
                console.log('zoomToRoute called with bounds:', bounds);
                var map = findLeafletMap();
                console.log('Found map:', map);
                if (map && typeof map.fitBounds === 'function') {{
                    console.log('Bounds array length:', bounds.length);
                    console.log('First bound:', bounds[0], 'Last bound:', bounds[bounds.length - 1]);
                    var latLngBounds = L.latLngBounds(bounds);
                    console.log('Created latLngBounds:', latLngBounds);
                    var sw = latLngBounds.getSouthWest();
                    var ne = latLngBounds.getNorthEast();
                    console.log('Southwest:', sw, 'Northeast:', ne);
                    console.log('Lat range:', ne.lat - sw.lat, 'Lng range:', ne.lng - sw.lng);
                    
                    // Calculate the center of the route bounds
                    var center = latLngBounds.getCenter();
                    console.log('Route center:', center);
                    
                    // Invalidate map size to force recalculation
                    map.invalidateSize(false);
                    
                    // Use much larger padding to ensure routes are comfortably visible
                    // Map is 583x800, so use 20% padding on each side
                    var paddingOptions = {{
                        padding: [120, 120],
                        animate: true,
                        duration: 0.5,
                        // Force reset of zoom/pan constraints
                        reset: true
                    }};
                    console.log('Calling fitBounds with padding:', paddingOptions);
                    
                    // Call fitBounds - this should now properly fit the entire route
                    map.fitBounds(latLngBounds, paddingOptions);
                    
                    // Get the zoom level Leaflet chose
                    var chosenZoom = map.getZoom();
                    console.log('Leaflet chose zoom level:', chosenZoom);
                    
                    // Verify the route is actually visible by checking pixel bounds
                    var mapBounds = map.getBounds();
                    console.log('Map bounds after fitBounds - SW:', mapBounds.getSouthWest(), 'NE:', mapBounds.getNorthEast());
                    
                    // Check if corners are visible in viewport
                    var swPoint = map.latLngToContainerPoint(sw);
                    var nePoint = map.latLngToContainerPoint(ne);
                    var mapSize = map.getSize();
                    console.log('SW pixel:', swPoint, 'NE pixel:', nePoint, 'Map size:', mapSize);
                    console.log('SW visible?', swPoint.x >= 0 && swPoint.x <= mapSize.x && swPoint.y >= 0 && swPoint.y <= mapSize.y);
                    console.log('NE visible?', nePoint.x >= 0 && nePoint.x <= mapSize.x && nePoint.y >= 0 && nePoint.y <= mapSize.y);
                }} else {{
                    console.error('Map not found or fitBounds not available. map:', map);
                }}
            }} catch (err) {{
                console.error('Error zooming to route:', err);
            }}
        }}
        
        function zoomToFilteredRoutes(filter) {{
            try {{
                var map = findLeafletMap();
                if (!map) return;
                
                var allBounds = [];
                
                // Collect bounds from all visible routes
                for (var routeId in routeData) {{
                    var data = routeData[routeId];
                    if (data.direction === filter) {{
                        allBounds = allBounds.concat(data.bounds);
                    }}
                }}
                
                if (allBounds.length > 0) {{
                    var latLngBounds = L.latLngBounds(allBounds);
                    map.fitBounds(latLngBounds, {{padding: [100, 100], maxZoom: 15}});
                }}
            }} catch (err) {{
                console.error('Error zooming to filtered routes:', err);
            }}
        }}
        
        function resetMapView() {{
            try {{
                var map = findLeafletMap();
                if (!map) return;
                
                var allBounds = [];
                
                // Collect bounds from all routes
                for (var routeId in routeData) {{
                    allBounds = allBounds.concat(routeData[routeId].bounds);
                }}
                
                if (allBounds.length > 0) {{
                    var latLngBounds = L.latLngBounds(allBounds);
                    map.fitBounds(latLngBounds, {{padding: [100, 100], maxZoom: 15}});
                }}
            }} catch (err) {{
                console.error('Error resetting map view:', err);
            }}
        }}
        
        function resetRouteStyles() {{
            var routeLines = document.querySelectorAll('path.route-line');
            routeLines.forEach(function(line) {{
                var classes = line.getAttribute('class') || '';
                
                // Check if route should be visible based on current filters
                var matchesDirection = (currentFilter === 'all') || (classes.indexOf('direction-' + currentFilter) !== -1);
                var isPlus = classes.indexOf('plus-route') !== -1;
                var matchesPlusFilter = showPlusRoutes || !isPlus;
                var shouldBeVisible = matchesDirection && matchesPlusFilter;
                
                if (!shouldBeVisible) {{
                    // Route is filtered out - keep it hidden
                    line.style.display = 'none';
                }} else {{
                    // Reset styles to show route normally
                    line.style.display = '';
                    line.style.opacity = '';
                    line.style.strokeWidth = '';
                    line.style.stroke = '';  // Clear stroke color override
                }}
            }});
        }}
        
        function zoomToSelectedRoutes() {{
            try {{
                var map = findLeafletMap();
                if (!map) return;
                
                var allBounds = [];
                
                // Collect bounds from all selected routes
                selectedRoutes.forEach(function(routeId) {{
                    var data = routeData[routeId];
                    if (data && data.bounds) {{
                        allBounds = allBounds.concat(data.bounds);
                    }}
                }});
                
                if (allBounds.length > 0) {{
                    var latLngBounds = L.latLngBounds(allBounds);
                    map.fitBounds(latLngBounds, {{padding: [100, 100], maxZoom: 15}});
                }}
            }} catch (err) {{
                console.error('Error zooming to selected routes:', err);
            }}
        }}
        </script>
        """
        
        from folium import Element
        self.map.get_root().html.add_child(Element(js_code))
        
        logger.info("Added route interaction JavaScript with filter buttons for zoom and fade effects")
    
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
