"""
Report generation module.

Creates comprehensive HTML reports with embedded maps and statistics.

Copyright (c) 2024-2026 e2kd7n
Licensed under the MIT License - see LICENSE file for details.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates HTML reports from analysis results."""
    
    def __init__(self, analysis_results: Dict[str, Any]):
        """
        Initialize report generator.
        
        Args:
            analysis_results: Dictionary containing all analysis results
        """
        self.results = analysis_results
        self.template_dir = Path("templates")
        
    def generate_report(self, output_path: str) -> None:
        """
        Generate complete HTML report.
        
        Args:
            output_path: Path to save the report
        """
        logger.info("Generating HTML report...")
        
        # Prepare context
        context = self._prepare_context()
        
        # Render template
        html = self._render_template(context)
        
        # Save report
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Report saved to {output_path}")
    
    def _prepare_context(self) -> Dict[str, Any]:
        """
        Prepare template context from analysis results.
        
        Returns:
            Dictionary with template variables
        """
        recommendations = self.results.get('recommendations', {})
        optimal = recommendations.get('optimal', {})
        alternative = recommendations.get('alternative')
        
        # Get route names and colors from visualizer
        visualizer = self.results.get('visualizer')
        route_names = visualizer.get_route_names() if visualizer else {}
        route_colors = visualizer.get_route_colors() if visualizer else {}
        
        # Prepare ranked routes with metrics, names, Strava links, and prevailing wind
        ranked_routes = []
        for group, score, breakdown in self.results.get('ranked_routes', []):
            metrics = self.results.get('optimizer').metrics.get(group.id)
            route_name = route_names.get(group.id, group.id)
            
            # Get most recent activity ID for this route group
            most_recent_activity_id = None
            if group.routes:
                # Sort by timestamp to get most recent
                sorted_routes = sorted(group.routes, key=lambda r: r.timestamp, reverse=True)
                most_recent_activity_id = sorted_routes[0].activity_id
            
            # Get prevailing wind direction for this route
            from .weather_fetcher import WeatherFetcher
            if group.representative_route and group.representative_route.coordinates:
                # Use midpoint of route for location
                mid_idx = len(group.representative_route.coordinates) // 2
                mid_lat, mid_lon = group.representative_route.coordinates[mid_idx]
                prevailing_wind = WeatherFetcher.get_prevailing_wind_direction(mid_lat, mid_lon)
            else:
                prevailing_wind = None
            
            ranked_routes.append({
                'group': group,
                'score': score,
                'breakdown': breakdown,
                'metrics': metrics,
                'name': route_name,
                'color': route_colors.get(group.id, '#808080'),  # Default to gray if not found
                'strava_url': f"https://www.strava.com/activities/{most_recent_activity_id}" if most_recent_activity_id else None,
                'prevailing_wind': prevailing_wind
            })
        
        # Add test routes to verify zoom functionality
        class TestGroup:
            def __init__(self, id, direction):
                self.id = id
                self.direction = direction
        
        test_metrics = type('obj', (object,), {
            'avg_duration': 0,
            'avg_duration_min': 0,
            'avg_distance': 0,
            'avg_distance_m': 0,
            'use_count': 0
        })()
        
        ranked_routes.insert(0, {
            'group': TestGroup('test_ferry', 'test'),
            'score': 999.0,
            'breakdown': {'time': 100, 'distance': 100, 'safety': 100},
            'metrics': test_metrics,
            'name': 'TEST: Four States Ferry (267km)',
            'color': '#FF0000',
            'strava_url': 'https://www.strava.com/activities/9458631701',
            'prevailing_wind': None
        })
        
        ranked_routes.insert(1, {
            'group': TestGroup('test_unbound', 'test'),
            'score': 998.0,
            'breakdown': {'time': 100, 'distance': 100, 'safety': 100},
            'metrics': test_metrics,
            'name': 'TEST: Unbound 200 (327km)',
            'color': '#0000FF',
            'strava_url': 'https://www.strava.com/activities/11551867398',
            'prevailing_wind': None
        })
        
        # Calculate statistics
        total_activities = len(self.results.get('all_activities', []))
        commute_activities = len(self.results.get('commute_activities', []))
        route_variants = len(self.results.get('route_groups', []))
        
        # Get date range
        activities = self.results.get('all_activities', [])
        if activities:
            dates = [a.start_date for a in activities]
            date_range = f"{min(dates)[:10]} to {max(dates)[:10]}"
        else:
            date_range = "N/A"
        
        # Prepare long rides data
        long_rides = self.results.get('long_rides', [])
        long_rides_stats = {}
        distance_bins = []
        
        if long_rides:
            distances = [r.distance_km for r in long_rides]
            loop_count = sum(1 for r in long_rides if r.is_loop)
            
            # Calculate distance distribution bins (10km intervals)
            min_dist = min(distances)
            max_dist = max(distances)
            bin_size = 10  # 10km bins
            num_bins = int((max_dist - min_dist) / bin_size) + 1
            
            # Create bins
            bins = {}
            for i in range(num_bins):
                bin_start = int(min_dist / bin_size) * bin_size + i * bin_size
                bin_end = bin_start + bin_size
                bin_label = f"{bin_start}-{bin_end}km"
                bins[bin_label] = 0
            
            # Count rides in each bin
            for dist in distances:
                bin_index = int((dist - (int(min_dist / bin_size) * bin_size)) / bin_size)
                bin_start = int(min_dist / bin_size) * bin_size + bin_index * bin_size
                bin_end = bin_start + bin_size
                bin_label = f"{bin_start}-{bin_end}km"
                if bin_label in bins:
                    bins[bin_label] += 1
            
            distance_bins = [{'label': k, 'count': v} for k, v in bins.items()]
            
            long_rides_stats = {
                'total_rides': len(long_rides),
                'total_distance_km': sum(distances),
                'avg_distance_km': sum(distances) / len(distances),
                'min_distance_km': min(distances),
                'max_distance_km': max(distances),
                'loop_count': loop_count,
                'loop_percentage': (loop_count / len(long_rides)) * 100,
                'point_to_point_count': len(long_rides) - loop_count
            }
        
        context = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'optimal': optimal,
            'alternative': alternative,
            'ranked_routes': ranked_routes,
            'map_html': self.results.get('map_html', ''),
            'home': self.results.get('home'),
            'work': self.results.get('work'),
            'route_names': route_names,
            'statistics': {
                'total_activities': total_activities,
                'commute_activities': commute_activities,
                'route_variants': route_variants,
                'date_range': date_range
            },
            'long_rides': long_rides,
            'long_rides_stats': long_rides_stats,
            'distance_bins': distance_bins
        }
        
        return context
    
    def _render_template(self, context: Dict[str, Any]) -> str:
        """
        Render HTML template with context.
        
        Args:
            context: Template context dictionary
            
        Returns:
            Rendered HTML string
        """
        # Use inline template for simplicity
        template_str = self._get_inline_template()
        template = Template(template_str)
        
        return template.render(**context)
    
    def _get_inline_template(self) -> str:
        """Get inline HTML template."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Strava Commute Analysis Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f8f9fa; }
        .container-fluid { padding: 30px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; }
        .card { border: none; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .card-header { background-color: #667eea; color: white; font-weight: bold; }
        .metric { text-align: center; padding: 20px; }
        .metric-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .metric-label { color: #6c757d; font-size: 0.9em; }
        .map-container { height: 800px; border-radius: 10px; overflow: hidden; position: sticky; top: 20px; }
        .map-container iframe { height: 800px !important; width: 100% !important; }
        .route-row { cursor: pointer; transition: background-color 0.2s; }
        .route-row:hover { background-color: #f0f0f0; }
        .route-row.selected { background-color: #d4edda; font-weight: bold; }
        .route-row.highlighted { background-color: #fff3cd; }
        .route-row.page-hidden { display: none; }
        .route-row.direction-hidden { display: none; }
        .comparison-section { display: flex; gap: 20px; }
        .comparison-table { flex: 1; }
        .map-pane { flex: 1; min-width: 500px; }
        .pagination-controls { margin: 15px 0; display: flex; justify-content: space-between; align-items: center; }
        .pagination-controls button { margin: 0 5px; }
        .page-info { color: #6c757d; }
        .direction-filter { margin-bottom: 15px; }
        .direction-filter .btn-group { box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .direction-filter .btn { border-radius: 0; }
        .direction-filter .btn:first-child { border-radius: 5px 0 0 5px; }
        .direction-filter .btn:last-child { border-radius: 0 5px 5px 0; }
        .coming-soon { text-align: center; padding: 100px 20px; color: #6c757d; }
        .coming-soon h2 { font-size: 3em; margin-bottom: 20px; }
        .coming-soon p { font-size: 1.2em; }
        .nav-tabs .nav-link { color: #667eea; font-weight: 500; }
        .nav-tabs .nav-link.active { background-color: #667eea; color: white; }
        .score-link { cursor: pointer; color: #667eea; text-decoration: underline; }
        .score-link:hover { color: #764ba2; }
        [data-bs-toggle="tooltip"] { cursor: help; border-bottom: 1px dotted #667eea; }
    </style>
</head>
<body>
    <!-- Anti-Piracy Protection -->
    <script>
        (function() {
            // Check if this is being hosted on an unauthorized domain
            const authorizedDomains = ['localhost', '127.0.0.1'];
            const currentHost = window.location.hostname || '';
            const protocol = window.location.protocol;
            
            // Allow file:// protocol (for local viewing on desktop/mobile)
            // Allow localhost and 127.0.0.1 (for local development)
            const isAuthorized = protocol === 'file:' ||
                                authorizedDomains.some(domain => currentHost.includes(domain));
            
            // Check for suspicious indicators (ads, redirects, etc.)
            const hasSuspiciousElements = document.querySelectorAll('iframe[src*="ads"], script[src*="doubleclick"], script[src*="googlesyndication"]').length > 0;
            
            // Only block if hosted on unauthorized web domain with suspicious content
            if (!isAuthorized && (hasSuspiciousElements || window.location.href.includes('porn') || window.location.href.includes('redirect'))) {
                // Replace entire page with piracy warning
                document.addEventListener('DOMContentLoaded', function() {
                    document.body.innerHTML = `
                        <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: white;">
                            <div style="max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.3);">
                                <h1 style="color: #dc3545; font-size: 3em; margin-bottom: 20px;">🏴‍☠️ ARRR! YE BE CAUGHT! 🏴‍☠️</h1>
                                
                                <div style="font-size: 8em; margin: 30px 0;">🏴‍☠️</div>
                                
                                <h2 style="color: #333; margin-bottom: 20px;">Unauthorized Use Detected</h2>
                                
                                <div style="background: #fff3cd; border: 3px solid #ffc107; border-radius: 10px; padding: 30px; margin: 30px 0; color: #333;">
                                    <p style="font-size: 1.3em; font-weight: bold; margin-bottom: 15px;">
                                        This software has been stolen and is being hosted without authorization.
                                    </p>
                                    <p style="font-size: 1.1em; line-height: 1.6;">
                                        You should be <strong>ashamed</strong> of yourself for:
                                    </p>
                                    <ul style="text-align: left; display: inline-block; font-size: 1.1em; line-height: 1.8;">
                                        <li>Stealing open-source software</li>
                                        <li>Hosting it with ads and malicious redirects</li>
                                        <li>Violating the MIT License terms</li>
                                        <li>Disrespecting the developer's work</li>
                                    </ul>
                                </div>
                                
                                <div style="background: #f8d7da; border: 3px solid #dc3545; border-radius: 10px; padding: 30px; margin: 30px 0; color: #721c24;">
                                    <h3 style="margin-bottom: 15px;">⚠️ This Application Requires Authentication ⚠️</h3>
                                    <p style="font-size: 1.1em; line-height: 1.6;">
                                        This software <strong>requires valid Strava API credentials</strong> to function.
                                        It cannot be run without proper authentication.
                                    </p>
                                    <p style="font-size: 1.1em; line-height: 1.6; margin-top: 15px;">
                                        If you want to use this software legitimately:
                                    </p>
                                    <ol style="text-align: left; display: inline-block; font-size: 1.1em; line-height: 1.8;">
                                        <li>Get the source code from the official repository</li>
                                        <li>Obtain your own FREE Strava API credentials</li>
                                        <li>Run it locally on your own computer</li>
                                        <li>Respect the open-source license</li>
                                    </ol>
                                </div>
                                
                                <div style="margin-top: 40px; padding: 20px; background: #d4edda; border-radius: 10px; color: #155724;">
                                    <h3>Get the Legitimate Version</h3>
                                    <p style="font-size: 1.1em; margin: 15px 0;">
                                        This is open-source software. Get it for FREE from the official source.
                                    </p>
                                    <p style="font-size: 0.9em; color: #666; margin-top: 20px;">
                                        Strava Commute Route Analyzer - MIT License
                                    </p>
                                </div>
                                
                                <div style="margin-top: 40px; font-size: 4em;">
                                    🏴‍☠️ ⚓ 🦜
                                </div>
                                
                                <p style="color: #666; margin-top: 30px; font-style: italic;">
                                    "A pirate's life is not for thee. Use software legitimately!"
                                </p>
                            </div>
                        </div>
                    `;
                    
                    // Prevent any further JavaScript execution
                    throw new Error('Unauthorized use detected');
                });
            }
        })();
    </script>
    
    <div class="container-fluid">
        <div class="header">
            <h1>🚴 Strava Commute Analysis</h1>
            <p>Generated on {{ timestamp }}</p>
            <button onclick="refreshReport()" class="btn btn-light" style="margin-top: 10px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: text-bottom;">
                    <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                    <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
                </svg>
                Refresh Report
            </button>
        </div>

        <!-- Navigation Tabs -->
        <ul class="nav nav-tabs" id="reportTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="commute-tab" data-bs-toggle="tab" data-bs-target="#commute" type="button" role="tab">
                    🚴 Commute Routes
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="howitworks-tab" data-bs-toggle="tab" data-bs-target="#howitworks" type="button" role="tab">
                    📊 How It Works
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="forecast-tab" data-bs-toggle="tab" data-bs-target="#forecast" type="button" role="tab">
                    🌤️ Commute Forecast
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="longrides-tab" data-bs-toggle="tab" data-bs-target="#longrides" type="button" role="tab">
                    🚵 Long Rides
                </button>
            </li>
        </ul>

        <!-- Tab Content -->
        <div class="tab-content" id="reportTabContent" style="margin-top: 20px;">
            <!-- Commute Routes Tab -->
            <div class="tab-pane fade show active" id="commute" role="tabpanel" aria-labelledby="commute-tab">

        <div class="card">
            <div class="card-header"><h3>🏆 Recommended Optimal Route</h3></div>
            <div class="card-body">
                <div class="alert alert-success">
                    <h4>{{ route_names.get(optimal.id, optimal.id) }}</h4>
                    <p><strong>Direction:</strong> {{ optimal.direction.replace('_', ' ').title() }}</p>
                    <p><strong>Reason:</strong> {{ optimal.reason }}</p>
                </div>
                <div class="row">
                    <div class="col-md-2">
                        <div class="metric">
                            <div class="metric-value">{{ "%.1f"|format(optimal.avg_duration_min) }}</div>
                            <div class="metric-label">Minutes</div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="metric">
                            <div class="metric-value">{{ "%.2f"|format(optimal.avg_distance_km) }}</div>
                            <div class="metric-label">Kilometers</div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="metric">
                            <div class="metric-value">{{ "%.1f"|format(optimal.avg_speed_kmh) }}</div>
                            <div class="metric-label">km/h</div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="metric">
                            <div class="metric-value">{{ optimal.frequency }}</div>
                            <div class="metric-label">Times Used</div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="metric">
                            <div class="metric-value">{{ "%.0f"|format(optimal.breakdown.get('weather', 50)) }}</div>
                            <div class="metric-label">Weather Score</div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="metric">
                            {% if optimal.breakdown.get('weather_details') %}
                                {% set wd = optimal.breakdown.weather_details %}
                                <div class="metric-value" style="font-size: 1.5em;">
                                    {% if wd.wind_favorability == 'favorable' %}🌬️✅{% elif wd.wind_favorability == 'unfavorable' %}🌬️⚠️{% else %}🌬️{% endif %}
                                </div>
                                <div class="metric-label">{{ wd.wind_favorability|title }} Wind</div>
                            {% else %}
                                <div class="metric-value" style="font-size: 1.5em;">🌤️</div>
                                <div class="metric-label">No Weather Data</div>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% if optimal.breakdown.get('weather_details') %}
                {% set wd = optimal.breakdown.weather_details %}
                <div class="alert alert-info mt-3">
                    <h6>🌤️ Current Weather Conditions</h6>
                    <div class="row">
                        <div class="col-md-4">
                            <strong>Wind:</strong> {{ "%.1f"|format(wd.wind_speed_kph) }} km/h from {{ "%.0f"|format(wd.wind_direction_deg) }}°
                        </div>
                        <div class="col-md-4">
                            <strong>Avg Headwind:</strong>
                            {% if wd.avg_headwind_kph < 0 %}
                                <span class="text-success">{{ "%.1f"|format(wd.avg_headwind_kph|abs) }} km/h tailwind</span>
                            {% else %}
                                <span class="text-danger">{{ "%.1f"|format(wd.avg_headwind_kph) }} km/h headwind</span>
                            {% endif %}
                        </div>
                        <div class="col-md-4">
                            <strong>Avg Crosswind:</strong> {{ "%.1f"|format(wd.avg_crosswind_kph) }} km/h
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-4">
                            <strong>Temperature:</strong> {{ "%.1f"|format(wd.temp_c) }}°C
                        </div>
                        <div class="col-md-4">
                            <strong>Time Impact:</strong>
                            {% if wd.time_penalty_pct < 0 %}
                                <span class="text-success">{{ "%.1f"|format(wd.time_penalty_pct|abs) }}% faster</span>
                            {% else %}
                                <span class="text-warning">{{ "%.1f"|format(wd.time_penalty_pct) }}% slower</span>
                            {% endif %}
                        </div>
                        <div class="col-md-4">
                            <strong>Humidity:</strong> {{ "%.0f"|format(wd.humidity) }}%
                        </div>
                    </div>
                </div>
                {% endif %}
            </div>
        </div>

        <div class="card">
            <div class="card-header"><h3>📊 Route Comparison & Map</h3></div>
            <div class="card-body">
                <div class="direction-filter">
                    <label class="me-2"><strong>Filter by Direction:</strong></label>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-outline-primary active" data-direction="all">All Routes</button>
                        <button type="button" class="btn btn-outline-primary" data-direction="home_to_work">🏠 → 🏢 To Work</button>
                        <button type="button" class="btn btn-outline-primary" data-direction="work_to_home">🏢 → 🏠 To Home</button>
                    </div>
                </div>
                <div class="comparison-section">
                    <div class="comparison-table">
                        <div class="pagination-controls">
                            <div>
                                <button class="btn btn-sm btn-outline-primary" id="prevPage" disabled>← Previous</button>
                                <button class="btn btn-sm btn-outline-primary" id="nextPage">Next →</button>
                            </div>
                            <div class="page-info">
                                <span id="pageInfo">Page 1 of <span id="totalPages">1</span></span>
                                <span class="ms-3">Showing <span id="showingCount">0</span> of {{ ranked_routes|length }} routes</span>
                            </div>
                        </div>
                        <table class="table table-hover" id="routesTable">
                            <thead>
                                <tr>
                                    <th>Rank</th><th>Route Name</th><th>Score</th><th>Duration</th><th>Distance</th><th>Uses</th><th>Wind</th><th>View on Strava</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for route in ranked_routes %}
                                <tr class="route-row"
                                    data-route-id="{{ route.group.id }}"
                                    data-direction="{{ route.group.direction }}"
                                    data-page="{{ ((loop.index - 1) // 10) + 1 }}"
                                    data-strava-url="{{ route.strava_url }}"
                                    {% if loop.index == 1 %}data-optimal="true"{% endif %}>
                                    <td>{{ loop.index }}</td>
                                    <td>
                                        <span class="route-color-indicator" style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: {{ route.color }}; margin-right: 8px; border: 1px solid #ddd;"></span>
                                        <strong class="route-name-link" style="cursor: pointer; color: #667eea;" title="Click to view on Strava">
                                            {{ route.name }}
                                        </strong>
                                    </td>
                                    <td>
                                        <span class="score-link"
                                              onclick="document.getElementById('howitworks').scrollIntoView({behavior: 'smooth'});"
                                              data-bs-toggle="tooltip"
                                              data-bs-placement="top"
                                              title="Time: {{ "%.1f"|format(route.breakdown['time']) }} | Distance: {{ "%.1f"|format(route.breakdown['distance']) }} | Safety: {{ "%.1f"|format(route.breakdown['safety']) }}">
                                            {{ "%.1f"|format(route.score) }}
                                        </span>
                                    </td>
                                    <td>{{ "%.1f"|format(route.metrics['avg_duration'] / 60) }} min</td>
                                    <td>{{ "%.2f"|format(route.metrics['avg_distance'] / 1000) }} km</td>
                                    <td>{{ route.group.frequency }}</td>
                                    <td>
                                        {% if route.breakdown.get('weather_details') %}
                                            {% set wd = route.breakdown.weather_details %}
                                            {% if wd.wind_favorability == 'favorable' %}
                                                <div style="background-color: #d4edda; padding: 6px 8px; border-radius: 4px; border-left: 3px solid #28a745;"
                                                     title="Favorable: Headwind {{ '%.1f'|format(wd.avg_headwind_kph) }} km/h, Crosswind {{ '%.1f'|format(wd.avg_crosswind_kph) }} km/h">
                                                    <span style="font-size: 16px;">🌬️</span>
                                                    <span style="color: #155724; font-weight: 600;">{{ "%.0f"|format(route.breakdown.weather) }}</span>
                                                    <span style="color: #155724; font-size: 11px;">✓ Tailwind</span>
                                                </div>
                                            {% elif wd.wind_favorability == 'unfavorable' %}
                                                <div style="background-color: #f8d7da; padding: 6px 8px; border-radius: 4px; border-left: 3px solid #dc3545;"
                                                     title="Unfavorable: Headwind {{ '%.1f'|format(wd.avg_headwind_kph) }} km/h, Crosswind {{ '%.1f'|format(wd.avg_crosswind_kph) }} km/h">
                                                    <span style="font-size: 16px;">💨</span>
                                                    <span style="color: #721c24; font-weight: 600;">{{ "%.0f"|format(route.breakdown.weather) }}</span>
                                                    <span style="color: #721c24; font-size: 11px;">⚠ Headwind</span>
                                                </div>
                                            {% else %}
                                                <div style="background-color: #e2e3e5; padding: 6px 8px; border-radius: 4px; border-left: 3px solid #6c757d;"
                                                     title="Neutral: Headwind {{ '%.1f'|format(wd.avg_headwind_kph) }} km/h, Crosswind {{ '%.1f'|format(wd.avg_crosswind_kph) }} km/h">
                                                    <span style="font-size: 16px;">🌫️</span>
                                                    <span style="color: #383d41; font-weight: 600;">{{ "%.0f"|format(route.breakdown.weather) }}</span>
                                                    <span style="color: #383d41; font-size: 11px;">~ Neutral</span>
                                                </div>
                                            {% endif %}
                                            {% if route.prevailing_wind %}
                                                <small class="text-muted" style="font-size: 10px; display: block; margin-top: 4px;" title="{{ route.prevailing_wind.description }}">
                                                    📅 {{ route.prevailing_wind.month }}: {{ route.prevailing_wind.direction_name }}
                                                </small>
                                            {% endif %}
                                        {% else %}
                                            <div style="background-color: #f8f9fa; padding: 6px 8px; border-radius: 4px; text-align: center;" title="No weather data available">
                                                <span class="text-muted">-</span>
                                            </div>
                                            {% if route.prevailing_wind %}
                                                <small class="text-muted" style="font-size: 10px; display: block; margin-top: 4px;" title="{{ route.prevailing_wind.description }}">
                                                    📅 {{ route.prevailing_wind.month }}: {{ route.prevailing_wind.direction_name }}
                                                </small>
                                            {% endif %}
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if route.strava_url %}
                                        <a href="{{ route.strava_url }}" target="_blank" class="btn btn-sm btn-outline-primary" title="View most recent activity on Strava">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                                <path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0zM5.5 7.5l2.5 5 2.5-5h-1.5l-1 2-1-2H5.5z"/>
                                            </svg>
                                            View
                                        </a>
                                        {% else %}
                                        <span class="text-muted">N/A</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        <p class="text-muted small">
                            <i class="bi bi-info-circle"></i> Hover over a route name to highlight it on the map.
                            Click to keep it highlighted.
                        </p>
                    </div>
                    <div class="map-pane">
                        <div class="map-container">{{ map_html | safe }}</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header"><h3>📈 Statistics</h3></div>
            <div class="card-body">
                <ul>
                    <li><strong>Total Activities:</strong> {{ statistics.total_activities }}</li>
                    <li><strong>Commute Activities:</strong> {{ statistics.commute_activities }}</li>
                    <li><strong>Route Variants:</strong> {{ statistics.route_variants }}</li>
                    <li><strong>Date Range:</strong> {{ statistics.date_range }}</li>
                </ul>
                <h5>Locations</h5>
                <div class="row">
                    <div class="col-md-6">
                        <h6>🏠 Home</h6>
                        <p>{{ "%.4f"|format(home.lat) }}, {{ "%.4f"|format(home.lon) }}</p>
                        <p>Activities: {{ home.activity_count }}</p>
                    </div>
                    <div class="col-md-6">
                        <h6>🏢 Work</h6>
                        <p>{{ "%.4f"|format(work.lat) }}, {{ "%.4f"|format(work.lon) }}</p>
                        <p>Activities: {{ work.activity_count }}</p>
                    </div>
                </div>
            </div>
        </div>

        {% if alternative %}
        <div class="card">
            <div class="card-header"><h3>💡 Alternative Route</h3></div>
            <div class="card-body">
                <p><strong>{{ route_names.get(alternative.id, alternative.id) }}</strong> - {{ alternative.direction.replace('_', ' ').title() }}</p>
                <p>{{ alternative.reason }}</p>
                <p>Duration: {{ "%.1f"|format(alternative.avg_duration_min) }} min |
                   Distance: {{ "%.2f"|format(alternative.avg_distance_km) }} km |
                   Score: {{ "%.1f"|format(alternative.score) }}</p>
            </div>
        </div>
        {% endif %}

        <div class="text-center text-muted mt-4">
            <p>Generated by Strava Commute Route Analyzer</p>
        </div>
    </div>

    <script>
        // Direction filter functionality
        (function() {
            let currentDirection = 'all';
            const directionButtons = document.querySelectorAll('.direction-filter button');
            const allRouteRows = document.querySelectorAll('.route-row');
            
            directionButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    // Prevent default scroll behavior
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Update active button
                    directionButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Get selected direction
                    currentDirection = this.getAttribute('data-direction');
                    
                    // Filter routes in table
                    filterRoutesInTable();
                    
                    // Filter routes in map iframe
                    try {
                        const mapIframe = document.querySelector('iframe');
                        if (mapIframe && mapIframe.contentWindow && typeof mapIframe.contentWindow.filterRoutes === 'function') {
                            mapIframe.contentWindow.filterRoutes(currentDirection);
                        }
                    } catch (err) {
                        console.error('Error calling map filterRoutes:', err);
                    }
                    
                    // Reset pagination to page 1 (without scrolling)
                    window.paginationController.resetToFirstPage();
                    
                    // Return false to prevent any default behavior
                    return false;
                });
            });
            
            function filterRoutesInTable() {
                allRouteRows.forEach(row => {
                    const rowDirection = row.getAttribute('data-direction');
                    
                    if (currentDirection === 'all' || rowDirection === currentDirection) {
                        row.classList.remove('direction-hidden');
                    } else {
                        row.classList.add('direction-hidden');
                    }
                });
                
                // Update pagination counts
                window.paginationController.updateCounts();
            }
            
            // Expose filter function globally
            window.directionFilter = {
                getCurrentDirection: () => currentDirection,
                filterRoutes: filterRoutesInTable
            };
        })();
        
        // Pagination functionality
        (function() {
            const ROUTES_PER_PAGE = 10;
            let currentPage = 1;
            const allRouteRows = document.querySelectorAll('.route-row');
            
            const prevButton = document.getElementById('prevPage');
            const nextButton = document.getElementById('nextPage');
            const pageInfo = document.getElementById('pageInfo');
            const totalPagesSpan = document.getElementById('totalPages');
            const showingCount = document.getElementById('showingCount');
            
            function getVisibleRoutes() {
                return Array.from(allRouteRows).filter(row =>
                    !row.classList.contains('direction-hidden')
                );
            }
            
            function showPage(page, shouldScroll = false) {
                const visibleRoutes = getVisibleRoutes();
                const totalRoutes = visibleRoutes.length;
                const totalPages = Math.ceil(totalRoutes / ROUTES_PER_PAGE);
                
                currentPage = Math.min(page, Math.max(1, totalPages));
                
                // Hide all rows first
                allRouteRows.forEach(row => {
                    row.classList.add('page-hidden');
                });
                
                // Show rows for current page (only visible ones)
                const startIndex = (currentPage - 1) * ROUTES_PER_PAGE;
                const endIndex = Math.min(startIndex + ROUTES_PER_PAGE, totalRoutes);
                
                for (let i = startIndex; i < endIndex; i++) {
                    visibleRoutes[i].classList.remove('page-hidden');
                }
                
                // Update pagination controls
                prevButton.disabled = (currentPage === 1);
                nextButton.disabled = (currentPage === totalPages || totalPages === 0);
                pageInfo.textContent = `Page ${currentPage} of `;
                totalPagesSpan.textContent = totalPages || 1;
                showingCount.textContent = totalRoutes > 0 ? `${startIndex + 1}-${endIndex}` : '0';
                
                // Only scroll if explicitly requested (e.g., pagination button clicks)
                if (shouldScroll) {
                    document.getElementById('routesTable').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }
            
            function updateCounts() {
                showPage(currentPage);
            }
            
            function resetToFirstPage() {
                showPage(1);
            }
            
            // Event listeners
            prevButton.addEventListener('click', () => {
                if (currentPage > 1) {
                    showPage(currentPage - 1, true);  // Scroll when using pagination buttons
                }
            });
            
            nextButton.addEventListener('click', () => {
                const visibleRoutes = getVisibleRoutes();
                const totalPages = Math.ceil(visibleRoutes.length / ROUTES_PER_PAGE);
                if (currentPage < totalPages) {
                    showPage(currentPage + 1, true);  // Scroll when using pagination buttons
                }
            });
            
            // Expose pagination controller globally
            window.paginationController = {
                showPage: showPage,
                updateCounts: updateCounts,
                resetToFirstPage: resetToFirstPage
            };
            
            // Initialize first page
            showPage(1);
        })();
        
        // Route name click to open Strava
        (function() {
            const routeRows = document.querySelectorAll('.route-row');
            
            routeRows.forEach(row => {
                const routeNameLink = row.querySelector('.route-name-link');
                const stravaUrl = row.getAttribute('data-strava-url');
                
                if (routeNameLink && stravaUrl && stravaUrl !== 'None') {
                    routeNameLink.addEventListener('click', function(e) {
                        e.stopPropagation(); // Prevent row click event
                        window.open(stravaUrl, '_blank');
                    });
                    
                    // Add hover effect
                    routeNameLink.addEventListener('mouseenter', function() {
                        this.style.textDecoration = 'underline';
                    });
                    
                    routeNameLink.addEventListener('mouseleave', function() {
                        this.style.textDecoration = 'none';
                    });
                }
            });
        })();
        
        // Interactive route highlighting functionality
        (function() {
            console.log('Route interaction script loaded');
            console.log('Found route rows:', document.querySelectorAll('.route-row').length);
            
            let selectedRouteId = null;
            const routeRows = document.querySelectorAll('.route-row');
            
            console.log('Setting up', routeRows.length, 'route row listeners');
            
            // Function to highlight route on map
            function highlightRoute(routeId, persist = false) {
                // Find all polylines in the map
                const mapContainer = document.querySelector('.map-container');
                if (!mapContainer) return;
                
                const iframe = mapContainer.querySelector('iframe');
                let mapDoc = iframe ? iframe.contentDocument : mapContainer;
                
                // Try to access Leaflet map through various methods
                try {
                    // Method 1: Direct SVG path manipulation
                    const paths = mapDoc.querySelectorAll('path.leaflet-interactive');
                    paths.forEach(path => {
                        const classes = path.getAttribute('class') || '';
                        
                        // Check if this path belongs to the route
                        if (classes.includes('route-' + routeId)) {
                            // Highlight this route
                            path.style.strokeWidth = '8';
                            path.style.strokeOpacity = '1';
                            path.style.zIndex = '1000';
                        } else if (!persist || routeId !== selectedRouteId) {
                            // Dim other routes
                            path.style.strokeWidth = '3';
                            path.style.strokeOpacity = '0.4';
                        }
                    });
                } catch (e) {
                    console.log('Could not access map elements:', e);
                }
            }
            
            // Function to reset all routes to normal
            function resetRoutes() {
                const mapContainer = document.querySelector('.map-container');
                if (!mapContainer) return;
                
                const iframe = mapContainer.querySelector('iframe');
                let mapDoc = iframe ? iframe.contentDocument : mapContainer;
                
                try {
                    const paths = mapDoc.querySelectorAll('path.leaflet-interactive');
                    paths.forEach(path => {
                        const classes = path.getAttribute('class') || '';
                        
                        // Reset to default styling
                        if (classes.includes('route-')) {
                            const isOptimal = path.getAttribute('data-optimal') === 'true';
                            path.style.strokeWidth = isOptimal ? '5' : '3';
                            path.style.strokeOpacity = isOptimal ? '0.9' : '0.6';
                            path.style.zIndex = isOptimal ? '500' : '100';
                        }
                    });
                } catch (e) {
                    console.log('Could not reset map elements:', e);
                }
            }
            
            // Add event listeners to route rows
            routeRows.forEach(row => {
                const routeId = row.getAttribute('data-route-id');
                
                // Hover effect
                row.addEventListener('mouseenter', function() {
                    if (selectedRouteId === null) {
                        this.classList.add('highlighted');
                        highlightRoute(routeId, false);
                    }
                });
                
                row.addEventListener('mouseleave', function() {
                    if (selectedRouteId === null) {
                        this.classList.remove('highlighted');
                        resetRoutes();
                    }
                });
                
                // Click to persist highlight
                row.addEventListener('click', function() {
                    // Remove previous selection
                    routeRows.forEach(r => r.classList.remove('selected'));
                    
                    if (selectedRouteId === routeId) {
                        // Unselect if clicking the same route
                        selectedRouteId = null;
                        this.classList.remove('selected');
                        resetRoutes();
                        
                        // Reset map zoom to show all routes
                        if (typeof window.resetMapView === 'function') {
                            window.resetMapView();
                        }
                    } else {
                        // Select new route
                        selectedRouteId = routeId;
                        this.classList.add('selected');
                        highlightRoute(routeId, true);
                        
                        // Zoom map to selected route - need to access iframe's contentWindow
                        console.log('Table row clicked, routeId:', routeId);
                        try {
                            const mapIframe = document.querySelector('iframe');
                            if (mapIframe && mapIframe.contentWindow) {
                                const iframeWindow = mapIframe.contentWindow;
                                console.log('Found iframe, checking for zoomToRouteById...');
                                console.log('iframe.contentWindow.zoomToRouteById exists?', typeof iframeWindow.zoomToRouteById);
                                
                                if (typeof iframeWindow.zoomToRouteById === 'function') {
                                    console.log('Calling iframe.contentWindow.zoomToRouteById with:', routeId);
                                    iframeWindow.zoomToRouteById(routeId);
                                } else {
                                    console.error('zoomToRouteById not found in iframe contentWindow');
                                }
                            } else {
                                console.error('Map iframe not found or no contentWindow');
                            }
                        } catch (err) {
                            console.error('Error accessing iframe:', err);
                        }
                    }
                });
            });
            
            // Wait for map to load before setting up interactions
            setTimeout(() => {
                const mapContainer = document.querySelector('.map-container');
                if (mapContainer) {
                    // Store original styles for routes
                    const iframe = mapContainer.querySelector('iframe');
                    let mapDoc = iframe ? iframe.contentDocument : mapContainer;
                    
                    try {
                        const paths = mapDoc.querySelectorAll('path.leaflet-interactive');
                        paths.forEach(path => {
                            const classes = path.getAttribute('class') || '';
                            if (classes.includes('route-')) {
                                // Store original styles as data attributes
                                path.setAttribute('data-original-width', path.style.strokeWidth || '3');
                                path.setAttribute('data-original-opacity', path.style.strokeOpacity || '0.6');
                            }
                        });
                    } catch (e) {
                        console.log('Map not fully loaded yet');
                    }
                }
            }, 1000);
        })();
        
        // Refresh report functionality
        function refreshReport() {
            const projectPath = window.location.pathname.includes('/commute/') ?
                window.location.pathname.split('/commute/')[0] + '/commute' :
                '.';
            
            const message = `To refresh the report with latest data:\\n\\n` +
                `1. Open Terminal\\n` +
                `2. Run: cd ${projectPath} && python3 main.py --analyze\\n` +
                `3. The new report will open automatically\\n\\n` +
                `Or press Ctrl+C in the running terminal and it will regenerate.`;
            
            if (confirm(message + '\\n\\nCopy command to clipboard?')) {
                // Copy command to clipboard
                const command = `cd ${projectPath} && python3 main.py --analyze`;
                navigator.clipboard.writeText(command).then(() => {
                    alert('Command copied to clipboard! Paste it in your terminal.');
                }).catch(() => {
                    // Fallback if clipboard API not available
                    prompt('Copy this command:', command);
                });
            }
        }
    </script>

    </div><!-- End Commute Routes Tab -->

    <!-- How It Works Tab -->
    <div class="tab-pane fade" id="howitworks" role="tabpanel" aria-labelledby="howitworks-tab">
        <div class="card">
            <div class="card-header"><h3>📊 How the Route Optimizer Works</h3></div>
            <div class="card-body">
                <p class="lead">The route optimizer uses a multi-criteria scoring system to recommend the best commute routes based on your historical riding data.</p>
                
                <h4 class="mt-4">🎯 Scoring Methodology</h4>
                <p>Each route is evaluated using three key factors, weighted to balance speed, efficiency, and safety:</p>
                
                <div class="row mt-4">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h2 style="color: #667eea;">⏱️</h2>
                                <h5>Time Score</h5>
                                <p class="text-muted">Weight: 40%</p>
                                <hr>
                                <p class="small text-start">
                                    <strong>What it measures:</strong> How fast you can complete the route<br><br>
                                    <strong>Calculation:</strong> Faster routes score higher. We also consider consistency - routes with less time variation score better.<br><br>
                                    <strong>Formula:</strong> Normalized average duration + consistency bonus
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h2 style="color: #667eea;">📏</h2>
                                <h5>Distance Score</h5>
                                <p class="text-muted">Weight: 30%</p>
                                <hr>
                                <p class="small text-start">
                                    <strong>What it measures:</strong> Route efficiency and directness<br><br>
                                    <strong>Calculation:</strong> Shorter routes generally score higher, but we balance this with time - sometimes a slightly longer route is faster.<br><br>
                                    <strong>Formula:</strong> Normalized distance (inverted - shorter is better)
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body text-center">
                                <h2 style="color: #667eea;">🛡️</h2>
                                <h5>Safety Score</h5>
                                <p class="text-muted">Weight: 30%</p>
                                <hr>
                                <p class="small text-start">
                                    <strong>What it measures:</strong> Route familiarity and predictability<br><br>
                                    <strong>Calculation:</strong> Routes you use more frequently score higher (more familiar = safer). Flatter routes with less elevation change also score better.<br><br>
                                    <strong>Formula:</strong> Usage frequency + elevation consistency
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <h4 class="mt-5">🧮 Final Score Calculation</h4>
                <div class="alert alert-info">
                    <p class="mb-2"><strong>Overall Score = (Time Score × 0.40) + (Distance Score × 0.30) + (Safety Score × 0.30)</strong></p>
                    <p class="mb-0 small">All scores are normalized to a 0-100 scale, then weighted and combined. Higher scores indicate better routes.</p>
                </div>
                
                <h4 class="mt-4">🔍 Route Grouping</h4>
                <p>Similar routes are automatically grouped together using the <strong>Fréchet distance algorithm</strong>, which measures how similar two paths are by considering:</p>
                <ul>
                    <li><strong>Path order:</strong> Routes must follow similar sequences of turns and streets</li>
                    <li><strong>Spatial proximity:</strong> GPS points should be close together along the entire route</li>
                    <li><strong>Direction consistency:</strong> Routes going the same direction are grouped separately</li>
                </ul>
                <p class="small text-muted">Routes with similarity above 85% are grouped together. The most frequently used route in each group becomes the representative route.</p>
                
                <h4 class="mt-4">🌦️ Weather Integration</h4>
                <p>Current weather conditions are fetched for each route's start and end points, including:</p>
                <ul>
                    <li><strong>Temperature:</strong> Helps you dress appropriately</li>
                    <li><strong>Wind speed & direction:</strong> Identifies headwinds and tailwinds</li>
                    <li><strong>Precipitation:</strong> Alerts you to rain or snow</li>
                </ul>
                <p class="small text-muted">Weather data is cached for 90 minutes to minimize API calls while keeping information current.</p>
                
                <h4 class="mt-4">💡 Tips for Best Results</h4>
                <div class="alert alert-success">
                    <ul class="mb-0">
                        <li>Record at least 5-10 commutes on each route for accurate analysis</li>
                        <li>Use consistent start/end points (within 500m of home/work)</li>
                        <li>Name your activities with keywords like "commute" or "to work" for better filtering</li>
                        <li>The more data you have, the more accurate the recommendations become</li>
                    </ul>
                </div>
                
                <h4 class="mt-4">🔧 Customization</h4>
                <p>You can adjust the scoring weights in <code>config/config.yaml</code> to match your priorities:</p>
                <pre class="bg-light p-3 rounded"><code>optimization:
  weights:
    time: 0.4      # Increase if speed is your priority
    distance: 0.3  # Increase if you want shorter routes
    safety: 0.3    # Increase if you prefer familiar routes</code></pre>
            </div>
        </div>
    </div><!-- End How It Works Tab -->

    <!-- Commute Forecast Tab -->
    <div class="tab-pane fade" id="forecast" role="tabpanel" aria-labelledby="forecast-tab">
        <div class="coming-soon">
            <h2>🌤️</h2>
            <h3>7-Day Commute Forecast</h3>
            <p>Coming Soon!</p>
            <p class="text-muted">This feature will show weather forecasts for your morning and evening commutes,<br>
            with optimal route recommendations based on wind conditions.</p>
        </div>
    </div>

    <!-- Long Rides Tab -->
    <div class="tab-pane fade" id="longrides" role="tabpanel" aria-labelledby="longrides-tab">
        <div class="card mb-4">
            <div class="card-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <h3 class="mb-0">🚵 Long Ride Recommendations</h3>
                <p class="mb-0 mt-2" style="font-size: 0.95em;">Find the best routes based on wind conditions - prioritizing tailwinds on the return journey</p>
            </div>
            <div class="card-body">
                <!-- User Input Section -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <label for="rideDateTime" class="form-label"><strong>📅 When do you plan to ride?</strong></label>
                        <input type="datetime-local" class="form-control" id="rideDateTime">
                        <small class="text-muted">We'll analyze wind conditions for this time</small>
                    </div>
                    <div class="col-md-6">
                        <label for="startLocation" class="form-label"><strong>📍 Starting Location</strong></label>
                        <div class="input-group">
                            <input type="text" class="form-control" id="startLocation" placeholder="City, State or ZIP code" value="Chicago, IL">
                            <button class="btn btn-outline-secondary" type="button" onclick="geocodeLocation()" title="Search location">
                                🔍
                            </button>
                        </div>
                        <small class="text-muted">Enter city name, ZIP code, or coordinates - or click on map</small>
                        <div id="geocodeStatus" class="mt-1"></div>
                    </div>
                </div>

                <button class="btn btn-primary btn-lg mb-4" onclick="loadAndAnalyzeRoutes()">
                    🔍 Get Recommendations
                </button>

                <!-- Info Box -->
                <div class="alert alert-info">
                    <h5>💡 How Wind Scoring Works</h5>
                    <p class="mb-2">
                        Our recommendation system analyzes wind conditions along each route and calculates a <strong>Wind Score (0-1)</strong>:
                    </p>
                    <ul class="mb-2">
                        <li><strong>70% weight on second half</strong> - Tailwinds when you're tired are more valuable</li>
                        <li><strong>30% weight on first half</strong> - Fighting headwinds when fresh is manageable</li>
                        <li><strong>10% bonus</strong> for routes with strong consistent tailwinds (>0.8 score) on return</li>
                    </ul>
                    <p class="mb-0">
                        <strong>Score Guide:</strong>
                        <span class="badge bg-success ms-2">0.80-1.00 = Excellent</span>
                        <span class="badge bg-primary ms-2">0.65-0.79 = Good</span>
                        <span class="badge bg-warning ms-2">0.50-0.64 = Fair</span>
                        <span class="badge bg-danger ms-2">0.00-0.49 = Poor</span>
                    </p>
                </div>

                <!-- Loading State -->
                <div id="loadingState" class="text-center py-5" style="display: none;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-3">Fetching weather data and analyzing routes...</p>
                </div>

                <!-- Recommendations Container -->
                <div id="recommendationsContainer">
                    <!-- Statistics Cards -->
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h5 class="card-title">Total Rides</h5>
                                    <p class="card-text display-6">{{ long_rides_stats.total_rides }}</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h5 class="card-title">Average Distance</h5>
                                    <p class="card-text display-6">{{ "%.1f"|format(long_rides_stats.avg_distance_km) }} km</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h5 class="card-title">Loop Rides</h5>
                                    <p class="card-text display-6">{{ "%.0f"|format(long_rides_stats.loop_percentage) }}%</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card text-center">
                                <div class="card-body">
                                    <h5 class="card-title">Point-to-Point</h5>
                                    <p class="card-text display-6">{{ "%.0f"|format(100 - long_rides_stats.loop_percentage) }}%</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Placeholder for recommendations -->
                    <div class="alert alert-secondary text-center">
                        <h5>👆 Set your ride time and starting location above to get personalized recommendations</h5>
                        <p class="mb-0">We'll analyze wind conditions and show you the best routes with detailed maps and wind analysis</p>
                    </div>
                </div>

                <!-- Map Container -->
                <div class="card mt-4" id="longRideMapCard" style="display: none;">
                    <div class="card-header">
                        <h5 class="mb-0">🗺️ Route Map</h5>
                    </div>
                    <div class="card-body p-0">
                        <div id="longRideMap" style="height: 600px; width: 100%;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    </div><!-- End Tab Content -->
    </div><!-- End Container -->

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Initialize Bootstrap tooltips
        document.addEventListener('DOMContentLoaded', function() {
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        });

        // Initialize distance distribution chart
        {% if long_rides_stats and long_rides_stats.distance_bins %}
        document.addEventListener('DOMContentLoaded', function() {
            const ctx = document.getElementById('distanceChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [
                        {% for bin in long_rides_stats.distance_bins %}
                        '{{ bin.label }}'{% if not loop.last %},{% endif %}
                        {% endfor %}
                    ],
                    datasets: [{
                        label: 'Number of Rides',
                        data: [
                            {% for bin in long_rides_stats.distance_bins %}
                            {{ bin.count }}{% if not loop.last %},{% endif %}
                            {% endfor %}
                        ],
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            },
                            title: {
                                display: true,
                                text: 'Number of Rides'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Distance Range (km)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.parsed.y + ' ride' + (context.parsed.y !== 1 ? 's' : '');
                                }
                            }
                        }
                    }
                }
            });
        });
        {% endif %}

        // Long Ride Recommendations JavaScript
        let longRideMap = null;
        let longRidePolylines = [];
        
        // Load long rides data from template context
        let cachedRoutes = [
            {% for ride in long_rides %}
            {
                activity_id: {{ ride.activity_id }},
                name: "{{ ride.name|replace('"', '\\"') }}",
                distance: {{ ride.distance }},
                elevation_gain: {{ ride.elevation_gain }},
                coordinates: {{ ride.coordinates|tojson }}
            }{% if not loop.last %},{% endif %}
            {% endfor %}
        ];
        
        function initializeLongRideMap() {
            if (!longRideMap) {
                longRideMap = L.map('longRideMap').setView([41.8781, -87.6298], 6);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(longRideMap);
                
                longRideMap.on('click', function(e) {
                    document.getElementById('startLocation').value = `${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`;
                    document.getElementById('geocodeStatus').innerHTML = '<small class="text-success">✓ Location set from map</small>';
                });
            }
        }
        
        async function geocodeLocation() {
            const location = document.getElementById('startLocation').value.trim();
            const statusDiv = document.getElementById('geocodeStatus');
            
            if (!location) {
                statusDiv.innerHTML = '<small class="text-danger">Please enter a location</small>';
                return;
            }
            
            statusDiv.innerHTML = '<small class="text-info">🔍 Searching...</small>';
            
            try {
                const response = await fetch(
                    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(location)}&limit=1`,
                    { headers: { 'User-Agent': 'StravaCommuteAnalyzer/1.0' } }
                );
                
                const data = await response.json();
                
                if (data && data.length > 0) {
                    const result = data[0];
                    const lat = parseFloat(result.lat);
                    const lon = parseFloat(result.lon);
                    
                    document.getElementById('startLocation').value = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
                    statusDiv.innerHTML = `<small class="text-success">✓ Found: ${result.display_name}</small>`;
                    
                    if (longRideMap) {
                        longRideMap.setView([lat, lon], 10);
                        const marker = L.marker([lat, lon]).addTo(longRideMap);
                        marker.bindPopup(`<strong>Starting Location</strong><br>${result.display_name}`).openPopup();
                        setTimeout(() => longRideMap.removeLayer(marker), 3000);
                    }
                } else {
                    statusDiv.innerHTML = '<small class="text-danger">❌ Location not found. Try a different search term.</small>';
                }
            } catch (error) {
                console.error('Geocoding error:', error);
                statusDiv.innerHTML = '<small class="text-danger">❌ Error searching location. Please try again.</small>';
            }
        }
        
        function loadAndAnalyzeRoutes() {
            const dateTime = document.getElementById('rideDateTime').value;
            const location = document.getElementById('startLocation').value;
            
            if (!dateTime || !location) {
                alert('Please enter both date/time and location');
                return;
            }
            
            if (cachedRoutes.length === 0) {
                alert('No long ride data available. Please ensure you have non-commute rides in your Strava data.');
                return;
            }
            
            document.getElementById('loadingState').style.display = 'block';
            document.getElementById('recommendationsContainer').style.display = 'none';
            
            // Simulate wind analysis (in real app, this would call weather API)
            // TODO: Integrate with actual weather API based on dateTime
            const windDirection = 180; // South wind
            const windSpeed = 20;
            
            setTimeout(() => {
                analyzeAndDisplayRoutes(cachedRoutes, windDirection, windSpeed);
            }, 500);
        }
        
        function analyzeAndDisplayRoutes(routes, windDirection, windSpeed) {
            const recommendations = routes.map(route => {
                const analysis = calculateWindScore(route.coordinates, windDirection, windSpeed);
                
                return {
                    activity_id: route.activity_id,
                    name: route.name,
                    distance: route.distance / 1000,
                    elevation: route.elevation_gain,
                    duration: (route.distance / 1000) / 25,
                    coordinates: route.coordinates,
                    windScore: analysis.score,
                    firstHalfScore: analysis.firstHalfScore,
                    secondHalfScore: analysis.secondHalfScore,
                    recommendation: analysis.recommendation,
                    segments: analysis.segments
                };
            });
            
            recommendations.sort((a, b) => b.windScore - a.windScore);
            displayRecommendations(recommendations, windDirection, windSpeed);
        }
        
        function calculateWindScore(coordinates, windDirection, windSpeed) {
            const numSegments = Math.min(8, Math.floor(coordinates.length / 100));
            const segmentSize = Math.floor(coordinates.length / numSegments);
            
            const segments = [];
            let firstHalfScores = [];
            let secondHalfScores = [];
            
            for (let i = 0; i < numSegments; i++) {
                const startIdx = i * segmentSize;
                const endIdx = Math.min((i + 1) * segmentSize, coordinates.length - 1);
                
                const bearing = calculateBearing(
                    coordinates[startIdx],
                    coordinates[endIdx]
                );
                
                const relativeAngle = ((windDirection - bearing + 180) % 360) - 180;
                const absAngle = Math.abs(relativeAngle);
                
                let windType, score;
                if (absAngle < 45) {
                    windType = 'headwind';
                    score = 0.3;
                } else if (absAngle > 135) {
                    windType = 'tailwind';
                    score = 1.0;
                } else if (absAngle < 90) {
                    windType = 'quartering_headwind';
                    score = 0.5;
                } else {
                    windType = 'quartering_tailwind';
                    score = 0.8;
                }
                
                segments.push({ type: windType, score: score });
                
                if (i < numSegments / 2) {
                    firstHalfScores.push(score);
                } else {
                    secondHalfScores.push(score);
                }
            }
            
            const firstHalfAvg = firstHalfScores.reduce((a, b) => a + b, 0) / firstHalfScores.length;
            const secondHalfAvg = secondHalfScores.reduce((a, b) => a + b, 0) / secondHalfScores.length;
            
            let combinedScore = 0.3 * firstHalfAvg + 0.7 * secondHalfAvg;
            
            if (secondHalfAvg > 0.8) {
                combinedScore = Math.min(1.0, combinedScore * 1.1);
            }
            
            let recommendation;
            if (windSpeed < 10) {
                recommendation = 'Light winds - minimal impact on ride';
            } else if (secondHalfAvg > 0.8) {
                if (firstHalfAvg < 0.5) {
                    recommendation = 'Excellent! Headwind out, strong tailwind back - perfect for a long ride';
                } else {
                    recommendation = 'Great tailwinds for the return journey';
                }
            } else if (secondHalfAvg > 0.6) {
                recommendation = 'Favorable winds on the way back';
            } else if (secondHalfAvg < 0.4) {
                recommendation = 'Challenging headwinds on return - consider shorter route or different day';
            } else {
                recommendation = 'Mixed wind conditions - manageable but not ideal';
            }
            
            return {
                score: combinedScore,
                firstHalfScore: firstHalfAvg,
                secondHalfScore: secondHalfAvg,
                segments: segments,
                recommendation: recommendation
            };
        }
        
        function calculateBearing(point1, point2) {
            const lat1 = point1[0] * Math.PI / 180;
            const lat2 = point2[0] * Math.PI / 180;
            const lon1 = point1[1] * Math.PI / 180;
            const lon2 = point2[1] * Math.PI / 180;
            
            const dlon = lon2 - lon1;
            const x = Math.sin(dlon) * Math.cos(lat2);
            const y = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dlon);
            
            let bearing = Math.atan2(x, y) * 180 / Math.PI;
            bearing = (bearing + 360) % 360;
            
            return bearing;
        }
        
        function displayRecommendations(recommendations, windDirection, windSpeed) {
            longRidePolylines.forEach(p => longRideMap && longRideMap.removeLayer(p));
            longRidePolylines = [];
            
            let html = `
                <div class="alert alert-primary mb-4">
                    <strong>🌬️ Current Wind Conditions:</strong> ${windSpeed} km/h from ${windDirection}°
                    (${getWindDirectionName(windDirection)})
                </div>
                <div class="row">
            `;
            
            recommendations.forEach((rec, index) => {
                const scoreClass = rec.windScore >= 0.8 ? 'success' : rec.windScore >= 0.65 ? 'primary' : rec.windScore >= 0.5 ? 'warning' : 'danger';
                const scoreLabel = rec.windScore >= 0.8 ? 'Excellent' : rec.windScore >= 0.65 ? 'Good' : rec.windScore >= 0.5 ? 'Fair' : 'Poor';
                
                html += `
                    <div class="col-md-6 mb-4">
                        <div class="card h-100 border-${scoreClass} route-card" onclick="showRouteOnMap(${index})" style="cursor: pointer; transition: all 0.2s;">
                            <div class="card-header bg-${scoreClass} text-white">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h5 class="mb-0">${index + 1}. ${rec.name}</h5>
                                    <span class="badge bg-light text-dark fs-4">${rec.windScore.toFixed(3)}</span>
                                </div>
                                <small>${scoreLabel} Wind Conditions</small>
                            </div>
                            <div class="card-body">
                                <div class="row mb-3">
                                    <div class="col-4 text-center">
                                        <strong class="fs-5">${rec.distance.toFixed(1)} km</strong><br>
                                        <small class="text-muted">Distance</small>
                                    </div>
                                    <div class="col-4 text-center">
                                        <strong class="fs-5">${rec.duration.toFixed(1)} h</strong><br>
                                        <small class="text-muted">Est. Duration</small>
                                    </div>
                                    <div class="col-4 text-center">
                                        <strong class="fs-5">${rec.elevation.toFixed(0)} m</strong><br>
                                        <small class="text-muted">Elevation</small>
                                    </div>
                                </div>
                                
                                <div class="alert alert-light mb-3">
                                    <h6 class="mb-2">🌬️ Wind Analysis</h6>
                                    <div class="row mb-2">
                                        <div class="col-6">
                                            <small><strong>First Half:</strong> ${rec.firstHalfScore.toFixed(3)}</small>
                                        </div>
                                        <div class="col-6">
                                            <small><strong>Second Half:</strong> ${rec.secondHalfScore.toFixed(3)}</small>
                                        </div>
                                    </div>
                                    <div class="progress mb-2" style="height: 30px;">
                                        <div class="progress-bar bg-warning" style="width: 30%">
                                            <strong>30%</strong>
                                        </div>
                                        <div class="progress-bar bg-success" style="width: 70%">
                                            <strong>70%</strong>
                                        </div>
                                    </div>
                                    <small class="text-muted">
                                        Tailwinds when tired are more valuable
                                    </small>
                                    
                                    <div class="mt-3">
                                        <strong>Segments:</strong><br>
                                        ${rec.segments.slice(0, 8).map((seg, i) => `
                                            <span class="badge ${seg.type.includes('tail') ? 'bg-success' : 'bg-danger'} me-1 mb-1">
                                                ${i+1}: ${seg.type.replace('_', ' ')} (${seg.score.toFixed(2)})
                                            </span>
                                        `).join('')}
                                    </div>
                                </div>
                                
                                <div class="alert alert-${scoreClass} mb-0">
                                    <strong>💨 ${rec.recommendation}</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Add polyline to map
                const colors = ['#28a745', '#dc3545', '#007bff', '#ffc107'];
                const polyline = L.polyline(rec.coordinates, {
                    color: colors[index % colors.length],
                    weight: 4,
                    opacity: 0.7
                }).addTo(longRideMap);
                
                polyline.bindPopup(`
                    <strong>${rec.name}</strong><br>
                    Distance: ${rec.distance.toFixed(1)} km<br>
                    Wind Score: ${rec.windScore.toFixed(3)}
                `);
                
                longRidePolylines.push(polyline);
            });
            
            html += '</div>';
            
            document.getElementById('recommendationsContainer').innerHTML = html;
            document.getElementById('recommendationsContainer').style.display = 'block';
            document.getElementById('loadingState').style.display = 'none';
            
            if (longRidePolylines.length > 0) {
                const group = L.featureGroup(longRidePolylines);
                longRideMap.fitBounds(group.getBounds().pad(0.1));
            }
        }
        
        function showRouteOnMap(index) {
            // Highlight selected route
            longRidePolylines.forEach((p, i) => {
                p.setStyle({
                    weight: i === index ? 6 : 4,
                    opacity: i === index ? 1.0 : 0.5
                });
            });
            
            // Zoom to route
            longRideMap.fitBounds(longRidePolylines[index].getBounds().pad(0.1));
        }
        
        function getWindDirectionName(degrees) {
            const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
            const index = Math.round(degrees / 45) % 8;
            return directions[index];
        }
        
        // Set default date/time and initialize
        document.addEventListener('DOMContentLoaded', function() {
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            document.getElementById('rideDateTime').value = now.toISOString().slice(0, 16);
            
            initializeLongRideMap();
            
            document.getElementById('startLocation').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    geocodeLocation();
                }
            });
        });
    </script>
    
    <!-- Leaflet CSS and JS for maps -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</body>
</html>'''

# Made with Bob
