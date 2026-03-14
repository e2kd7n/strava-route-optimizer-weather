"""
Visualization module.

Generates interactive maps using Folium.
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
                 work: Location, config, long_rides=None, long_ride_analyzer=None):
        """
        Initialize route visualizer.
        
        Args:
            route_groups: List of RouteGroup objects
            home: Home location
            work: Work location
            config: Configuration object
            long_rides: Optional list of LongRide objects
            long_ride_analyzer: Optional LongRideAnalyzer instance
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
        
        # Add polyline with custom class and data attributes for JavaScript interaction
        folium.PolyLine(
            coords,
            color=color,
            weight=weight,
            opacity=opacity,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{route_name} ({route_group.frequency} uses)",
            className=f"route-line route-{route_group.id} {direction_class}",
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
            
            # Store the color for this route
            self.route_colors[group.id] = color
            
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
        
        # Add JavaScript for route interaction (zoom and fade)
        self._add_route_interaction_javascript()
        
        # Add JavaScript for long rides click handler if long rides are available
        self._add_long_rides_javascript()
        
        # Return HTML
        return self.map._repr_html_()
    
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
                
                long_rides_data.append({
                    'id': ride.activity_id,
                    'name': ride.name,
                    'distance': round(distance_value, 1),  # In target unit
                    'duration_hours': round(ride.duration_hours, 2),
                    'is_loop': ride.is_loop,
                    'midpoint': [midpoint[0], midpoint[1]],
                    'start': [ride.start_location[0], ride.start_location[1]],
                    'strava_url': f'https://www.strava.com/activities/{ride.activity_id}'
                })
        
        long_rides_json = json.dumps(long_rides_data)
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
                       '<p style="font-size: 11px; color: #666; margin: 5px 0;">Search radius: ' + searchRadius + ' km</p>';
            
            if (nearbyRides.length === 0) {{
                html += '<div style="background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #ffc107;">' +
                        '<p style="margin: 0; font-size: 12px;">No rides found within ' + searchRadius + ' km of this location.</p>' +
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
                            '<span>📍 ' + item.distance.toFixed(1) + ' km away</span>' +
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
        
        # Real Strava test routes for zoom testing
        route_data['route-test_ferry'] = {
            'bounds': [[41.98637, -87.66266], [41.9858, -87.66142], [41.98697, -87.66028], [41.98719, -87.65934], [41.98732, -87.65502], [41.98633, -87.65398], [41.98496, -87.65244], [41.98196, -87.65217], [41.97837, -87.65072], [41.97679, -87.64913], [41.9747, -87.64707], [41.96795, -87.64452], [41.96501, -87.63928], [41.96298, -87.63922], [41.96225, -87.64233], [41.96164, -87.64541], [41.95916, -87.64566], [41.95663, -87.64497], [41.95426, -87.64374], [41.94966, -87.64311], [41.9481, -87.64221], [41.94578, -87.64077], [41.94178, -87.63893], [41.93916, -87.63666], [41.93785, -87.6348], [41.93507, -87.63224], [41.9321, -87.63177], [41.93024, -87.63147], [41.92658, -87.62967], [41.92493, -87.6304], [41.92096, -87.62937], [41.91635, -87.62775], [41.91357, -87.62593], [41.91162, -87.62525], [41.91015, -87.62545], [41.90285, -87.62359], [41.90122, -87.6196], [41.89897, -87.61792], [41.89751, -87.61698], [41.89267, -87.61362], [41.8911, -87.61381], [41.88828, -87.61381], [41.88569, -87.61325], [41.88281, -87.61403], [41.88151, -87.61702], [41.87361, -87.61694], [41.86849, -87.61655], [41.86766, -87.61501], [41.86643, -87.61468], [41.8646, -87.61414], [41.86161, -87.61473], [41.85957, -87.61333], [41.85719, -87.6135], [41.85512, -87.61175], [41.85323, -87.6109], [41.85195, -87.61002], [41.84873, -87.60962], [41.84677, -87.6094], [41.84447, -87.60991], [41.84104, -87.60843], [41.83896, -87.60708], [41.83724, -87.60728], [41.83464, -87.60618], [41.83312, -87.60489], [41.83104, -87.60441], [41.82892, -87.60208], [41.82692, -87.60038], [41.82589, -87.59801], [41.82394, -87.59832], [41.82122, -87.59717], [41.82002, -87.59661], [41.81807, -87.59549], [41.81593, -87.5931], [41.81278, -87.59002], [41.80955, -87.58747], [41.80525, -87.58307], [41.80171, -87.58132], [41.79767, -87.58015], [41.79489, -87.57887], [41.79175, -87.57998], [41.78758, -87.57765], [41.78141, -87.5748], [41.77856, -87.57549], [41.77545, -87.57352], [41.77483, -87.56839], [41.77295, -87.56652], [41.76715, -87.56642], [41.7663, -87.56527], [41.76439, -87.56291], [41.75992, -87.55871], [41.75546, -87.55398], [41.75194, -87.54923], [41.7502, -87.54195], [41.74456, -87.54063], [41.73325, -87.54033], [41.72904, -87.54232], [41.72755, -87.54171], [41.72303, -87.53661], [41.72256, -87.53404], [41.71976, -87.53239], [41.71818, -87.53133], [41.71458, -87.53167], [41.71218, -87.53082], [41.70789, -87.52444], [41.70304, -87.51799], [41.70158, -87.51729], [41.69715, -87.51255], [41.69705, -87.51285], [41.69536, -87.51138], [41.69188, -87.50627], [41.69061, -87.50344], [41.68733, -87.49781], [41.68473, -87.49278], [41.68391, -87.48991], [41.68263, -87.48625], [41.68122, -87.48573], [41.67788, -87.48583], [41.67578, -87.48286], [41.66972, -87.473], [41.66652, -87.46911], [41.66154, -87.46691], [41.66074, -87.46727], [41.65404, -87.4576], [41.64972, -87.45168], [41.64803, -87.44985], [41.64217, -87.44976], [41.63899, -87.44945], [41.63825, -87.44217], [41.63666, -87.4339], [41.63339, -87.4277], [41.62767, -87.41927], [41.62023, -87.40857], [41.61088, -87.39533], [41.60588, -87.39311], [41.60369, -87.38893], [41.60368, -87.37661], [41.60258, -87.37195], [41.6019, -87.36556], [41.60191, -87.35755], [41.6019, -87.35045], [41.60199, -87.33713], [41.602, -87.33101], [41.5996, -87.31369], [41.59721, -87.30495], [41.595, -87.29542], [41.59509, -87.28356], [41.59678, -87.27234], [41.59648, -87.26415], [41.59824, -87.26143], [41.60176, -87.25553], [41.60552, -87.24018], [41.61016, -87.22094], [41.61352, -87.20701], [41.61694, -87.18793], [41.61911, -87.17064], [41.61919, -87.15302], [41.61786, -87.13657], [41.61918, -87.12427], [41.62364, -87.11796], [41.62823, -87.10981], [41.63147, -87.0999], [41.63456, -87.08968], [41.6356, -87.08662], [41.63749, -87.08539], [41.63929, -87.07939], [41.64063, -87.07505], [41.64353, -87.06592], [41.64454, -87.06229], [41.64644, -87.05796], [41.64882, -87.05115], [41.65057, -87.04616], [41.65326, -87.03884], [41.65453, -87.03502], [41.65593, -87.03114], [41.65694, -87.02828], [41.65766, -87.02618], [41.65885, -87.02291], [41.65936, -87.0215], [41.66067, -87.01786], [41.66207, -87.01413], [41.66355, -87.01037], [41.66646, -87.00958], [41.66944, -87.00961], [41.67127, -87.00704], [41.67266, -87.00248], [41.67516, -87.00187], [41.67862, -86.99212], [41.68416, -86.97951], [41.68737, -86.97388], [41.6905, -86.96897], [41.6916, -86.96057], [41.69429, -86.95603], [41.7032, -86.93588], [41.70587, -86.92792], [41.70662, -86.92423], [41.71271, -86.91774], [41.7167, -86.91035], [41.71828, -86.9076], [41.71868, -86.90619], [41.72015, -86.90501], [41.72125, -86.90373], [41.72355, -86.90474], [41.72489, -86.90219], [41.72644, -86.89843], [41.72765, -86.89452], [41.73032, -86.88868], [41.73354, -86.88136], [41.73759, -86.87327], [41.74277, -86.86258], [41.74642, -86.8544], [41.74722, -86.85256], [41.75062, -86.84487], [41.75415, -86.83723], [41.75898, -86.82656], [41.76046, -86.82295], [41.76027, -86.82319], [41.76031, -86.81701], [41.76026, -86.81094], [41.76027, -86.80503], [41.75792, -86.80451], [41.7629, -86.79764], [41.7685, -86.78991], [41.77465, -86.78137], [41.77857, -86.77599], [41.77848, -86.77539], [41.78189, -86.77045], [41.78647, -86.76349], [41.79122, -86.75005], [41.79267, -86.74649], [41.79402, -86.74376], [41.79512, -86.74452], [41.79464, -86.74421], [41.79773, -86.74655], [41.80141, -86.74645], [41.80293, -86.74437], [41.80554, -86.73928], [41.80936, -86.73192], [41.81249, -86.72719], [41.81468, -86.72268], [41.81737, -86.71733], [41.81919, -86.7083], [41.82245, -86.70238], [41.82797, -86.69739], [41.83272, -86.6936], [41.83786, -86.68455], [41.83936, -86.68048], [41.84211, -86.6795], [41.84768, -86.67464], [41.8516, -86.66951], [41.85243, -86.66678], [41.85566, -86.66297], [41.85911, -86.65596], [41.86205, -86.65157], [41.86439, -86.64731], [41.86799, -86.63862], [41.87383, -86.62398], [41.87565, -86.61825], [41.88279, -86.61156], [41.8866, -86.60928], [41.88556, -86.60769], [41.88548, -86.5954], [41.88873, -86.58983], [41.89233, -86.59032], [41.89768, -86.58981], [41.89927, -86.58788], [41.89957, -86.58113], [41.89958, -86.57037], [41.90842, -86.57035], [41.91589, -86.57029], [41.9211, -86.56901], [41.92124, -86.5615], [41.92116, -86.55343], [41.9257, -86.55265], [41.93181, -86.55264], [41.94288, -86.55264], [41.946, -86.55259], [41.95081, -86.55262], [41.95585, -86.55259], [41.96334, -86.55186], [41.96841, -86.54875], [41.96874, -86.55242], [41.97808, -86.54524], [41.98122, -86.54553], [41.98546, -86.54544], [41.98578, -86.5421], [41.99655, -86.53818], [42.00761, -86.53416], [42.01068, -86.53509], [42.01232, -86.53359], [42.01795, -86.53347], [42.02411, -86.53347], [42.02886, -86.53347], [42.029, -86.52897], [42.0289, -86.52495], [42.03087, -86.52382], [42.03722, -86.52388], [42.04317, -86.52391], [42.04345, -86.51735], [42.04371, -86.51409], [42.05341, -86.51419], [42.05788, -86.51401], [42.06493, -86.509], [42.073, -86.5068], [42.07989, -86.502], [42.08323, -86.49525], [42.08785, -86.49548], [42.09317, -86.49503], [42.09946, -86.49027], [42.10405, -86.48778], [42.11063, -86.48236], [42.11074, -86.47975], [42.11432, -86.47619], [42.12545, -86.46596], [42.13283, -86.4596], [42.14058, -86.45437], [42.14642, -86.44884], [42.15135, -86.44414], [42.15779, -86.43948], [42.1636, -86.43166], [42.16978, -86.42722], [42.17423, -86.42238], [42.18277, -86.41196], [42.19122, -86.4049], [42.19686, -86.39678], [42.20007, -86.39454], [42.20597, -86.39168], [42.21384, -86.38643], [42.21878, -86.3806], [42.22387, -86.37617], [42.2258, -86.37481], [42.22531, -86.37481], [42.22504, -86.37443], [42.22857, -86.36992], [42.2324, -86.36877], [42.23685, -86.36711], [42.24007, -86.36111], [42.24506, -86.35716], [42.24995, -86.35392], [42.25294, -86.34637], [42.25573, -86.34148], [42.26079, -86.33706], [42.26549, -86.33425], [42.27027, -86.33578], [42.27485, -86.3349], [42.27799, -86.33132], [42.28143, -86.3273], [42.28589, -86.32228], [42.28947, -86.32039], [42.29416, -86.32023], [42.29991, -86.31831], [42.30583, -86.31217], [42.30851, -86.30923], [42.31419, -86.30516], [42.31927, -86.3004], [42.32532, -86.29828], [42.32956, -86.29885], [42.33366, -86.29463], [42.34063, -86.29205], [42.34293, -86.29067], [42.3476, -86.28891], [42.35199, -86.28641], [42.35603, -86.28193], [42.35867, -86.27839], [42.36232, -86.27814], [42.36688, -86.27823], [42.37114, -86.27827], [42.37626, -86.27838], [42.38198, -86.27858], [42.38735, -86.27873], [42.39091, -86.27902], [42.39325, -86.27948], [42.39648, -86.27947], [42.40043, -86.27962], [42.40232, -86.27905], [42.40314, -86.27427], [42.40286, -86.27115], [42.40243, -86.27111], [42.4034, -86.27102], [42.40644, -86.27215], [42.40765, -86.27653], [42.40793, -86.27775], [42.40954, -86.27702], [42.41766, -86.27275], [42.4229, -86.27004], [42.4264, -86.26567], [42.42641, -86.26117], [42.4265, -86.25645], [42.42649, -86.25532], [42.42976, -86.25578], [42.43663, -86.2557], [42.44432, -86.25143], [42.45227, -86.24908], [42.46246, -86.24659], [42.47306, -86.24675], [42.48033, -86.24685], [42.48528, -86.24593], [42.49169, -86.23967], [42.4972, -86.23738], [42.5039, -86.22962], [42.50878, -86.22729], [42.51566, -86.22743], [42.52361, -86.22764], [42.52915, -86.22763], [42.5406, -86.22803], [42.54701, -86.22824], [42.55537, -86.22862], [42.55952, -86.22889], [42.56773, -86.22929], [42.57202, -86.22892], [42.57846, -86.22777], [42.58655, -86.2262], [42.58676, -86.22433], [42.59288, -86.22283], [42.59323, -86.21661], [42.59324, -86.21128], [42.59663, -86.21123], [42.60189, -86.21131], [42.60753, -86.21149], [42.6153, -86.21161], [42.62279, -86.21177], [42.63245, -86.21189], [42.6394, -86.21017], [42.64572, -86.2042], [42.64933, -86.19643], [42.65188, -86.19598], [42.65477, -86.20046], [42.65484, -86.20394], [42.65552, -86.20512], [42.65787, -86.20543], [42.66106, -86.20506], [42.66124, -86.20159], [42.66413, -86.19878], [42.66843, -86.19426], [42.67186, -86.18986], [42.6727, -86.18894], [42.67635, -86.18413], [42.67876, -86.17833], [42.68047, -86.17458], [42.68595, -86.17443], [42.69263, -86.17465], [42.69593, -86.17472], [42.69631, -86.17139], [42.70052, -86.17112], [42.70522, -86.1699], [42.70954, -86.16894], [42.71176, -86.16804], [42.71461, -86.1666], [42.71926, -86.16417], [42.72406, -86.16129], [42.73186, -86.15747], [42.73735, -86.15602], [42.74146, -86.15609], [42.75275, -86.15658], [42.75932, -86.15677], [42.76662, -86.1569], [42.76884, -86.15664], [42.77569, -86.15686], [42.7755, -86.15662], [42.77411, -86.15117], [42.7775, -86.14315], [42.78088, -86.13514], [42.78202, -86.12348], [42.78212, -86.11479], [42.78452, -86.11478], [42.78484, -86.11071], [42.78591, -86.10895], [42.79142, -86.10893], [42.7964, -86.10902], [42.80191, -86.11244], [42.80406, -86.11351], [42.80479, -86.11445], [42.80479, -86.10887], [42.80607, -86.10325], [42.81027, -86.10279], [42.8143, -86.10184], [42.81913, -86.09772], [42.81929, -86.08933], [42.81973, -86.08844]],
            'name': 'TEST: Four States Ferry (267km)',
            'direction': 'test'
        }
        route_data['route-test_unbound'] = {
            'bounds': [[38.41551, -96.17802], [38.41141, -96.17884], [38.40868, -96.17894], [38.40623, -96.17947], [38.40776, -96.18017], [38.41218, -96.18018], [38.41592, -96.18188], [38.42764, -96.18032], [38.43305, -96.18009], [38.43394, -96.18874], [38.43993, -96.18931], [38.44509, -96.19005], [38.44979, -96.18921], [38.45704, -96.18918], [38.465, -96.19065], [38.46673, -96.18939], [38.47309, -96.18944], [38.48483, -96.18954], [38.49218, -96.18956], [38.49277, -96.19859], [38.50586, -96.19826], [38.50652, -96.20636], [38.51246, -96.20725], [38.52163, -96.20698], [38.53149, -96.2069], [38.5355, -96.20903], [38.53746, -96.21623], [38.56118, -96.21612], [38.56471, -96.21431], [38.5653, -96.20695], [38.57523, -96.20691], [38.59443, -96.20682], [38.60785, -96.21076], [38.60791, -96.22475], [38.61416, -96.22486], [38.62177, -96.22526], [38.6331, -96.2253], [38.63647, -96.22554], [38.64392, -96.22491], [38.64437, -96.22042], [38.6581, -96.21992], [38.66788, -96.21999], [38.67985, -96.22011], [38.68993, -96.22032], [38.69514, -96.22154], [38.70192, -96.22354], [38.71942, -96.22365], [38.73232, -96.22371], [38.74301, -96.2238], [38.75106, -96.22388], [38.76117, -96.22391], [38.76845, -96.22397], [38.7753, -96.22404], [38.78202, -96.22414], [38.79, -96.22429], [38.80029, -96.22456], [38.80401, -96.22419], [38.80433, -96.20698], [38.80738, -96.20572], [38.81215, -96.20482], [38.82042, -96.19718], [38.824, -96.18698], [38.82613, -96.17978], [38.82616, -96.15204], [38.82785, -96.15008], [38.83977, -96.15001], [38.84078, -96.13938], [38.84091, -96.11572], [38.84365, -96.11326], [38.85375, -96.11332], [38.85765, -96.10993], [38.85911, -96.10856], [38.86195, -96.11239], [38.86624, -96.11344], [38.87057, -96.11353], [38.87603, -96.1136], [38.8826, -96.1136], [38.88859, -96.11361], [38.88954, -96.11357], [38.89642, -96.11359], [38.90381, -96.11372], [38.91339, -96.11371], [38.91757, -96.11358], [38.92111, -96.11586], [38.92503, -96.11386], [38.93389, -96.11381], [38.94361, -96.11387], [38.95519, -96.11378], [38.95738, -96.12252], [38.95704, -96.1319], [38.95374, -96.13188], [38.94336, -96.13184], [38.93336, -96.13178], [38.92592, -96.13179], [38.91753, -96.13175], [38.91371, -96.13669], [38.91415, -96.14046], [38.91294, -96.14115], [38.91362, -96.14475], [38.91377, -96.15506], [38.91659, -96.15581], [38.91946, -96.16089], [38.92178, -96.16482], [38.9241, -96.1687], [38.92723, -96.1741], [38.92896, -96.17789], [38.93281, -96.17837], [38.93528, -96.17873], [38.93493, -96.18853], [38.93801, -96.19367], [38.94004, -96.19702], [38.94144, -96.20103], [38.94326, -96.20278], [38.94483, -96.20684], [38.94756, -96.20613], [38.95377, -96.20599], [38.95898, -96.20596], [38.96401, -96.20599], [38.9683, -96.20381], [38.96388, -96.20012], [38.96335, -96.19753], [38.96442, -96.18992], [38.96744, -96.17823], [38.97538, -96.1784], [38.97875, -96.17936], [38.98091, -96.18099], [38.98485, -96.17925], [38.99291, -96.17836], [38.99889, -96.17832], [39.00073, -96.18365], [39.00058, -96.18906], [39.00112, -96.19305], [39.00069, -96.19713], [39.00054, -96.20585], [39.00073, -96.21164], [39.00624, -96.21566], [39.01342, -96.21559], [39.0223, -96.21537], [39.02249, -96.22542], [39.02199, -96.24002], [39.02239, -96.24475], [39.02154, -96.25118], [39.01963, -96.25393], [39.02072, -96.25697], [39.02144, -96.25989], [39.0213, -96.26572], [39.02175, -96.27287], [39.022, -96.28535], [39.01992, -96.28877], [39.01927, -96.28653], [39.01849, -96.28749], [39.01838, -96.28846], [39.01738, -96.28939], [39.01438, -96.28958], [39.01284, -96.29225], [39.0145, -96.29784], [39.01475, -96.30884], [39.01477, -96.31846], [39.01465, -96.33135], [39.01573, -96.33778], [39.01835, -96.33783], [39.02028, -96.33173], [39.02193, -96.32652], [39.02426, -96.32007], [39.0267, -96.31441], [39.02922, -96.30362], [39.03273, -96.30769], [39.03559, -96.31521], [39.03661, -96.31959], [39.03641, -96.33091], [39.03773, -96.3358], [39.03889, -96.33859], [39.04143, -96.34682], [39.04317, -96.35061], [39.04345, -96.35959], [39.04286, -96.37224], [39.02534, -96.37226], [39.01353, -96.37219], [39.01141, -96.37441], [39.01275, -96.38159], [39.01237, -96.38781], [39.01113, -96.39531], [39.00868, -96.40023], [39.01068, -96.40549], [39.0135, -96.40755], [39.01485, -96.41131], [39.01505, -96.41678], [39.01459, -96.42936], [39.01453, -96.44613], [39.00731, -96.4466], [39.00574, -96.44974], [39.00271, -96.45242], [38.99904, -96.45439], [38.99649, -96.46402], [38.98252, -96.46413], [38.98316, -96.46204], [38.98324, -96.45824], [38.98124, -96.45554], [38.97795, -96.45523], [38.97617, -96.45504], [38.97115, -96.45547], [38.9711, -96.46696], [38.96652, -96.47353], [38.95718, -96.47351], [38.95651, -96.46434], [38.94935, -96.46419], [38.94655, -96.45819], [38.94891, -96.45285], [38.94943, -96.45001], [38.94939, -96.44699], [38.9476, -96.44127], [38.94587, -96.43898], [38.94321, -96.43636], [38.94208, -96.4287], [38.9411, -96.42697], [38.93849, -96.42223], [38.93823, -96.41979], [38.944, -96.4116], [38.94646, -96.40478], [38.94197, -96.40348], [38.93835, -96.40073], [38.93407, -96.40082], [38.92854, -96.39837], [38.92351, -96.3922], [38.92136, -96.39066], [38.91853, -96.38817], [38.91467, -96.38433], [38.91311, -96.37383], [38.91302, -96.36282], [38.90103, -96.36304], [38.89794, -96.36153], [38.89565, -96.36165], [38.89155, -96.36303], [38.88777, -96.36198], [38.88404, -96.3631], [38.88226, -96.36882], [38.88416, -96.37255], [38.88418, -96.37902], [38.88466, -96.38374], [38.88324, -96.38788], [38.88238, -96.39004], [38.88541, -96.391], [38.88845, -96.39217], [38.88778, -96.39453], [38.8868, -96.40092], [38.88417, -96.40947], [38.87336, -96.40976], [38.8696, -96.42365], [38.86961, -96.43862], [38.86961, -96.44752], [38.86966, -96.4625], [38.86955, -96.48105], [38.86801, -96.48731], [38.86581, -96.48843], [38.86241, -96.48848], [38.86224, -96.48296], [38.85343, -96.48295], [38.83074, -96.48293], [38.826, -96.48273], [38.82477, -96.46888], [38.8188, -96.46752], [38.81589, -96.46141], [38.80526, -96.45931], [38.79701, -96.45445], [38.79778, -96.4401], [38.79709, -96.43673], [38.78924, -96.42673], [38.7845, -96.42991], [38.78263, -96.42921], [38.78264, -96.41264], [38.77218, -96.40834], [38.76985, -96.40956], [38.76844, -96.40837], [38.7623, -96.40836], [38.75423, -96.40824], [38.75377, -96.40042], [38.75798, -96.38985], [38.7677, -96.38978], [38.76818, -96.37684], [38.76813, -96.35261], [38.76817, -96.33197], [38.76106, -96.33019], [38.75363, -96.33038], [38.7536, -96.33784], [38.75362, -96.34826], [38.74921, -96.35279], [38.74146, -96.3528], [38.73899, -96.34964], [38.73262, -96.34866], [38.72451, -96.34932], [38.71922, -96.35301], [38.71148, -96.3531], [38.6981, -96.355], [38.69546, -96.35787], [38.69553, -96.3647], [38.69437, -96.37184], [38.68536, -96.3719], [38.68265, -96.37194], [38.68154, -96.379], [38.68148, -96.38584], [38.68161, -96.39614], [38.68165, -96.41507], [38.68165, -96.42551], [38.67783, -96.4275], [38.67479, -96.42794], [38.66306, -96.42731], [38.65984, -96.42629], [38.65828, -96.42273], [38.65558, -96.42344], [38.64855, -96.42521], [38.64665, -96.43187], [38.64528, -96.4366], [38.64531, -96.44511], [38.64497, -96.45222], [38.64789, -96.45609], [38.65101, -96.46562], [38.6548, -96.47328], [38.66023, -96.47883], [38.66057, -96.48551], [38.6594, -96.48834], [38.65798, -96.48784], [38.65796, -96.48912], [38.65341, -96.48814], [38.6482, -96.49011], [38.64662, -96.50021], [38.64195, -96.50149], [38.63334, -96.50157], [38.63039, -96.50593], [38.62346, -96.50617], [38.62325, -96.51492], [38.6197, -96.51552], [38.61915, -96.52007], [38.60873, -96.52029], [38.60896, -96.53705], [38.60897, -96.53952], [38.60809, -96.54472], [38.60913, -96.56051], [38.6092, -96.57903], [38.60918, -96.59729], [38.59473, -96.59728], [38.57924, -96.59725], [38.57275, -96.59728], [38.56141, -96.59732], [38.55121, -96.59685], [38.55114, -96.58226], [38.5441, -96.58229], [38.53669, -96.58218], [38.53635, -96.55839], [38.53628, -96.53475], [38.53621, -96.52023], [38.52924, -96.52016], [38.52167, -96.51798], [38.52163, -96.48843], [38.5216, -96.47712], [38.52073, -96.47403], [38.52157, -96.46706], [38.52331, -96.46477], [38.52797, -96.46475], [38.53609, -96.46456], [38.53621, -96.4458], [38.53619, -96.43559], [38.52898, -96.42788], [38.52894, -96.42046], [38.5307, -96.41787], [38.52389, -96.4119], [38.52124, -96.41183], [38.51868, -96.40967], [38.51429, -96.40978], [38.50422, -96.41016], [38.49314, -96.41], [38.493, -96.39862], [38.49303, -96.39226], [38.493, -96.37279], [38.49277, -96.3539], [38.50283, -96.35374], [38.50723, -96.35303], [38.50743, -96.3242], [38.5074, -96.31148], [38.50752, -96.2847], [38.50702, -96.26708], [38.5065, -96.24753], [38.50457, -96.24332], [38.49199, -96.24342], [38.49216, -96.22939], [38.49155, -96.21685], [38.48196, -96.21685], [38.47051, -96.21688], [38.47041, -96.20497], [38.47037, -96.18963], [38.47746, -96.18961], [38.47757, -96.18106], [38.47751, -96.1761], [38.47744, -96.16211], [38.47741, -96.15237], [38.46649, -96.15254], [38.45556, -96.15268], [38.45161, -96.15215], [38.44129, -96.15244], [38.43256, -96.15376], [38.4244, -96.16108], [38.41966, -96.16169], [38.41954, -96.17136], [38.42146, -96.17703], [38.42, -96.17689], [38.41649, -96.17681], [38.41226, -96.17704], [38.41192, -96.18015], [38.40731, -96.18016]],
            'name': 'TEST: Unbound 200 (327km)',
            'direction': 'test'
        }
        
        route_data_json = json.dumps(route_data)
        
        js_code = f"""
        <script>
        // Route interaction data
        var routeData = {route_data_json};
        var selectedRoutes = new Set();  // Track multiple selected routes
        var currentFilter = 'all';
        
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
                                // No routes selected - show all
                                resetRouteStyles();
                            }} else {{
                                // Some routes selected - hide unselected, show selected
                                allRouteLines.forEach(function(line) {{
                                    var lineClasses = line.className.baseVal || line.className;
                                    var lineRouteMatch = lineClasses.match(/route-((?:home_to_work|work_to_home)_\\d+)/);
                                    if (!lineRouteMatch) return;
                                    
                                    var lineRouteId = 'route-' + lineRouteMatch[1];
                                    
                                    if (selectedRoutes.has(lineRouteId)) {{
                                        // Selected route - show with original color and thicker line
                                        line.style.display = '';
                                        line.style.opacity = '1.0';
                                        line.style.strokeWidth = '6';
                                        line.style.stroke = '';  // Keep original color
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
        window.filterRoutes = function(filter) {{
            console.log('filterRoutes called with:', filter);
            currentFilter = filter;
            selectedRoute = null;
            
            // Filter routes - need to find SVG path elements
            var routeLines = document.querySelectorAll('path.route-line');
            console.log('Found', routeLines.length, 'route lines');
            
            var visibleCount = 0;
            routeLines.forEach(function(line) {{
                // For SVG elements, use getAttribute to get class
                var classes = line.getAttribute('class') || '';
                
                if (filter === 'all') {{
                    line.style.display = '';
                    line.style.opacity = '';
                    line.style.strokeWidth = '';
                    visibleCount++;
                }} else {{
                    var directionClass = 'direction-' + filter;
                    if (classes.indexOf(directionClass) !== -1) {{
                        line.style.display = '';
                        line.style.opacity = '';
                        line.style.strokeWidth = '';
                        visibleCount++;
                    }} else {{
                        line.style.display = 'none';
                    }}
                }}
            }});
            
            console.log('Visible routes after filter:', visibleCount);
            
            // Auto-zoom to fit visible routes
            if (filter !== 'all') {{
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
                // Reset all styles to show routes normally
                line.style.display = '';
                line.style.opacity = '';
                line.style.strokeWidth = '';
                line.style.stroke = '';  // Clear stroke color override
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
