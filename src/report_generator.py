"""
Report generation module.

Creates comprehensive HTML reports with embedded maps and statistics.
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
        .map-container { height: 600px; border-radius: 10px; overflow: hidden; position: sticky; top: 20px; }
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
                                            <div title="Current: Headwind {{ '%.1f'|format(wd.avg_headwind_kph) }} km/h, Crosswind {{ '%.1f'|format(wd.avg_crosswind_kph) }} km/h">
                                                {% if wd.wind_favorability == 'favorable' %}
                                                    <span style="color: green;">✅ {{ "%.0f"|format(route.breakdown.weather) }}</span>
                                                {% elif wd.wind_favorability == 'unfavorable' %}
                                                    <span style="color: red;">⚠️ {{ "%.0f"|format(route.breakdown.weather) }}</span>
                                                {% else %}
                                                    <span style="color: gray;">➖ {{ "%.0f"|format(route.breakdown.weather) }}</span>
                                                {% endif %}
                                            </div>
                                            {% if route.prevailing_wind %}
                                                <small class="text-muted" title="{{ route.prevailing_wind.description }}">
                                                    {{ route.prevailing_wind.month }}: {{ route.prevailing_wind.direction_name }}
                                                </small>
                                            {% endif %}
                                        {% else %}
                                            <span class="text-muted" title="No weather data">-</span>
                                            {% if route.prevailing_wind %}
                                                <br><small class="text-muted" title="{{ route.prevailing_wind.description }}">
                                                    {{ route.prevailing_wind.month }}: {{ route.prevailing_wind.direction_name }}
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
            let selectedRouteId = null;
            const routeRows = document.querySelectorAll('.route-row');
            
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
                        
                        // Zoom map to selected route
                        if (typeof window.zoomToRouteById === 'function') {
                            window.zoomToRouteById(routeId);
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
                '/Users/erik/commute';
            
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
        <h3>Long Rides Analysis</h3>
        
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

        <!-- Distance Distribution Chart -->
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">Distance Distribution</h5>
            </div>
            <div class="card-body">
                <canvas id="distanceChart" style="max-height: 400px;"></canvas>
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
    </script>
</body>
</html>'''

# Made with Bob
