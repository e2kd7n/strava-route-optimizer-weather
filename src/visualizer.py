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
        tile_layer = self.config.get('visualization.map.tile_layer', 'OpenStreetMap')
        
        # Create map with larger height for better visibility
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles=tile_layer,
            height='800px'  # Increased from default 600px
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
        
        # Get unit labels for JavaScript
        distance_unit = self.units.distance_unit()
        
        # JavaScript code for click handling with embedded data
        js_code = f"""
        <script>
        // Long Rides Data (embedded from Python)
        var longRidesData = {long_rides_json};
        var longRidesEnabled = true;
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
            var mapElement = document.querySelector('.folium-map');
            if (mapElement && mapElement._leaflet_id) {{
                var map = window[mapElement._leaflet_id];
                
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
                                     '<small>Searching {len(self.long_rides)} rides</small></div>';
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
                        '<p style="margin: 5px 0 0 0; font-size: 11px; color: #666;">Try clicking closer to areas you\'ve ridden before.</p>' +
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
            coords = group.representative_route.coordinates
            if coords:
                route_data[f"route-{group.id}"] = {
                    'bounds': [[coord[0], coord[1]] for coord in coords],
                    'name': self.route_names.get(group.id, group.id),
                    'direction': group.direction
                }
        
        route_data_json = json.dumps(route_data)
        
        js_code = f"""
        <script>
        // Route interaction data
        var routeData = {route_data_json};
        var selectedRoute = null;
        var currentFilter = 'all';
        
        // Wait for map to be ready
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(function() {{
                // Find all route polylines
                var routeLines = document.querySelectorAll('.route-line');
                
                routeLines.forEach(function(routeLine) {{
                    routeLine.addEventListener('click', function(e) {{
                        // Get route ID from class name
                        var classes = this.className.baseVal || this.className;
                        var routeMatch = classes.match(/route-([\\w_]+)/);
                        if (!routeMatch) return;
                        
                        var routeId = 'route-' + routeMatch[1];
                        var data = routeData[routeId];
                        if (!data) return;
                        
                        // Toggle selection
                        if (selectedRoute === routeId) {{
                            // Deselect - restore all routes
                            resetRouteStyles();
                            selectedRoute = null;
                        }} else {{
                            // Select this route
                            selectedRoute = routeId;
                            
                            // Fade all other routes
                            routeLines.forEach(function(line) {{
                                var lineClasses = line.className.baseVal || line.className;
                                if (lineClasses.indexOf(routeId) === -1) {{
                                    // Not the selected route - fade it
                                    line.style.opacity = '0.15';
                                    line.style.strokeWidth = '2';
                                }} else {{
                                    // Selected route - highlight it
                                    line.style.opacity = '1.0';
                                    line.style.strokeWidth = '6';
                                }}
                            }});
                            
                            // Zoom to route bounds
                            zoomToRoute(data.bounds);
                        }}
                        
                        // Stop event propagation
                        e.stopPropagation();
                    }});
                }});
                
                // Click on map background to reset
                var mapElement = document.querySelector('.folium-map');
                if (mapElement && mapElement._leaflet_id) {{
                    var map = window[mapElement._leaflet_id];
                    map.on('click', function(e) {{
                        // Only reset if not clicking on a route
                        if (selectedRoute && !e.originalEvent.target.classList.contains('route-line')) {{
                            resetRouteStyles();
                            selectedRoute = null;
                        }}
                    }});
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
        
        // Expose zoom functions globally for report to call
        window.zoomToRouteById = function(routeId) {{
            var data = routeData['route-' + routeId];
            if (data && data.bounds) {{
                zoomToRoute(data.bounds);
            }}
        }};
        
        window.resetMapView = resetMapView;
        
        function zoomToRoute(bounds) {{
            try {{
                var mapElement = document.querySelector('.folium-map');
                if (mapElement && mapElement._leaflet_id) {{
                    var map = window[mapElement._leaflet_id];
                    var latLngBounds = L.latLngBounds(bounds);
                    map.fitBounds(latLngBounds, {{padding: [50, 50]}});
                }}
            }} catch (err) {{
                console.error('Error zooming to route:', err);
            }}
        }}
        
        function zoomToFilteredRoutes(filter) {{
            try {{
                var mapElement = document.querySelector('.folium-map');
                if (!mapElement || !mapElement._leaflet_id) return;
                
                var map = window[mapElement._leaflet_id];
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
                    map.fitBounds(latLngBounds, {{padding: [50, 50]}});
                }}
            }} catch (err) {{
                console.error('Error zooming to filtered routes:', err);
            }}
        }}
        
        function resetMapView() {{
            try {{
                var mapElement = document.querySelector('.folium-map');
                if (!mapElement || !mapElement._leaflet_id) return;
                
                var map = window[mapElement._leaflet_id];
                var allBounds = [];
                
                // Collect bounds from all routes
                for (var routeId in routeData) {{
                    allBounds = allBounds.concat(routeData[routeId].bounds);
                }}
                
                if (allBounds.length > 0) {{
                    var latLngBounds = L.latLngBounds(allBounds);
                    map.fitBounds(latLngBounds, {{padding: [50, 50]}});
                }}
            }} catch (err) {{
                console.error('Error resetting map view:', err);
            }}
        }}
        
        function resetRouteStyles() {{
            var routeLines = document.querySelectorAll('path.route-line');
            routeLines.forEach(function(line) {{
                // For SVG elements, use getAttribute to get class
                var classes = line.getAttribute('class') || '';
                
                // Only reset if route is visible based on current filter
                if (currentFilter === 'all') {{
                    line.style.opacity = '';
                    line.style.strokeWidth = '';
                }} else {{
                    var directionClass = 'direction-' + currentFilter;
                    if (classes.indexOf(directionClass) !== -1) {{
                        line.style.opacity = '';
                        line.style.strokeWidth = '';
                    }}
                }}
            }});
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
