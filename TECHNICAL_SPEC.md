# Technical Specification - Strava Commute Route Analyzer

## 1. Authentication Module (`auth.py`)

### Purpose
Handle Strava OAuth 2.0 authentication flow and token management.

### Key Functions

```python
class StravaAuthenticator:
    def __init__(self, client_id: str, client_secret: str)
    def get_authorization_url(self) -> str
    def exchange_code_for_token(self, code: str) -> dict
    def refresh_access_token(self, refresh_token: str) -> dict
    def save_tokens(self, tokens: dict) -> None
    def load_tokens(self) -> dict
    def get_authenticated_client(self) -> stravalib.Client
```

### Implementation Details
- Use `stravalib.Client` for API interactions
- Store tokens in `config/credentials.json` (gitignored)
- Implement automatic token refresh when expired
- Handle OAuth callback with local server on port 8000

### Error Handling
- Invalid credentials
- Expired tokens
- Network errors during authentication
- Missing scope permissions

---

## 2. Data Fetcher Module (`data_fetcher.py`)

### Purpose
Retrieve and cache activity data from Strava API.

### Key Functions

```python
class StravaDataFetcher:
    def __init__(self, client: stravalib.Client)
    def fetch_activities(self, limit: int = None, after: datetime = None) -> List[Activity]
    def get_activity_details(self, activity_id: int) -> DetailedActivity
    def get_activity_streams(self, activity_id: int) -> dict
    def cache_activities(self, activities: List[Activity]) -> None
    def load_cached_activities(self) -> List[Activity]
    def filter_commute_activities(self, activities: List[Activity]) -> List[Activity]
```

### Data Structure

```python
@dataclass
class Activity:
    id: int
    name: str
    type: str
    start_date: datetime
    distance: float  # meters
    moving_time: int  # seconds
    elapsed_time: int  # seconds
    total_elevation_gain: float  # meters
    start_latlng: Tuple[float, float]
    end_latlng: Tuple[float, float]
    polyline: str  # encoded polyline
    average_speed: float  # m/s
    max_speed: float  # m/s
```

### Caching Strategy
- Save activities to `data/cache/activities.json`
- Include timestamp of last fetch
- Only fetch new activities on subsequent runs
- Compress polyline data for storage efficiency

### Filtering Criteria
- Activity type: Ride, EBikeRide
- Distance: 2-30 km (configurable)
- Has GPS data (polyline exists)
- Exclude virtual rides

---

## 3. Location Finder Module (`location_finder.py`)

### Purpose
Identify home and work locations using clustering algorithms.

### Key Functions

```python
class LocationFinder:
    def __init__(self, activities: List[Activity])
    def extract_endpoints(self) -> List[Tuple[float, float, datetime]]
    def cluster_locations(self, eps: float = 0.002) -> List[Cluster]
    def identify_home_work(self) -> Tuple[Location, Location]
    def get_location_statistics(self, location: Location) -> dict
```

### Algorithm: DBSCAN Clustering

**Parameters:**
- `eps`: 0.002 degrees (~200 meters at mid-latitudes)
- `min_samples`: 5 activities minimum

**Process:**
1. Extract all start and end coordinates with timestamps
2. Apply DBSCAN to find location clusters
3. Rank clusters by frequency
4. Use time-of-day heuristics to distinguish home from work:
   - Calculate average departure/arrival times for each cluster
   - Morning departures (6-10 AM) → likely home
   - Evening arrivals (4-8 PM) → likely home
   - Inverse patterns → likely work

### Data Structure

```python
@dataclass
class Location:
    lat: float
    lon: float
    name: str  # "Home" or "Work"
    activity_count: int
    avg_departure_time: time
    avg_arrival_time: time
    radius: float  # cluster radius in meters
```

### Edge Cases
- Multiple work locations (choose most frequent)
- Irregular schedules (use median times)
- Insufficient data (require minimum 10 activities)

---

## 4. Route Analyzer Module (`route_analyzer.py`)

### Purpose
Extract, group, and analyze route variants between home and work.

### Key Functions

```python
class RouteAnalyzer:
    def __init__(self, activities: List[Activity], home: Location, work: Location)
    def extract_routes(self, direction: str) -> List[Route]
    def decode_polylines(self, route: Route) -> List[Tuple[float, float]]
    def calculate_route_similarity(self, route1: Route, route2: Route) -> float
    def group_similar_routes(self, threshold: float = 0.85) -> List[RouteGroup]
    def calculate_route_metrics(self, route_group: RouteGroup) -> RouteMetrics
```

### Route Similarity Algorithm

**Hausdorff Distance Method:**
```python
def hausdorff_distance(route1_coords, route2_coords):
    # Calculate maximum minimum distance between point sets
    # Normalize by route length
    # Return similarity score (0-1)
```

**Grouping Threshold:**
- Similarity > 0.85 → same route variant
- Consider both forward and reverse directions

### Data Structures

```python
@dataclass
class Route:
    activity_id: int
    direction: str  # "home_to_work" or "work_to_home"
    coordinates: List[Tuple[float, float]]
    distance: float
    duration: int
    elevation_gain: float
    timestamp: datetime
    
@dataclass
class RouteGroup:
    id: str
    routes: List[Route]
    representative_route: Route  # median route
    frequency: int
    
@dataclass
class RouteMetrics:
    avg_duration: float
    std_duration: float
    avg_distance: float
    avg_speed: float
    avg_elevation: float
    consistency_score: float  # 1 - (std/mean)
    usage_frequency: int
```

### Metrics Calculation

**Duration Statistics:**
- Mean, median, std deviation
- Remove outliers (>2 std deviations)

**Speed Analysis:**
- Average speed
- Speed consistency
- Identify stop patterns (speed < 1 m/s)

**Elevation Profile:**
- Total gain/loss
- Maximum gradient
- Flat vs hilly classification

---

## 5. Optimizer Module (`optimizer.py`)

### Purpose
Score and rank routes based on multiple criteria.

### Key Functions

```python
class RouteOptimizer:
    def __init__(self, route_groups: List[RouteGroup], weights: dict)
    def calculate_time_score(self, metrics: RouteMetrics) -> float
    def calculate_distance_score(self, metrics: RouteMetrics) -> float
    def calculate_safety_score(self, route_group: RouteGroup) -> float
    def calculate_composite_score(self, route_group: RouteGroup) -> float
    def rank_routes(self) -> List[Tuple[RouteGroup, float]]
    def get_optimal_route(self) -> RouteGroup
```

### Scoring Formulas

**Time Score (0-100):**
```python
time_score = 100 * (1 - (duration - min_duration) / (max_duration - min_duration))
consistency_bonus = consistency_score * 10
final_time_score = time_score + consistency_bonus
```

**Distance Score (0-100):**
```python
distance_score = 100 * (1 - (distance - min_distance) / (max_distance - min_distance))
```

**Safety Score (0-100):**
```python
# Frequency component (40%)
frequency_score = min(100, (usage_count / max_usage_count) * 100)

# Road type inference (30%)
# Analyze speed patterns and GPS track smoothness
straightness_score = calculate_path_straightness()
speed_variance_score = 100 - (speed_std / speed_mean * 100)
road_score = (straightness_score + speed_variance_score) / 2

# Elevation component (30%)
elevation_penalty = min(50, elevation_gain / 10)  # -5 points per 100m
elevation_score = 100 - elevation_penalty

safety_score = (frequency_score * 0.4 + road_score * 0.3 + elevation_score * 0.3)
```

**Composite Score:**
```python
composite = (
    time_score * weights['time'] +
    distance_score * weights['distance'] +
    safety_score * weights['safety']
)
```

### Default Weights
- Time: 0.4 (40%)
- Distance: 0.3 (30%)
- Safety: 0.3 (30%)

---

## 6. Visualizer Module (`visualizer.py`)

### Purpose
Generate interactive maps using Folium.

### Key Functions

```python
class RouteVisualizer:
    def __init__(self, route_groups: List[RouteGroup], home: Location, work: Location)
    def create_base_map(self) -> folium.Map
    def add_route_layer(self, route_group: RouteGroup, color: str, weight: int) -> None
    def add_location_markers(self) -> None
    def add_heatmap_layer(self) -> None
    def add_route_statistics_popup(self, route_group: RouteGroup) -> str
    def generate_map(self, output_path: str) -> None
```

### Map Features

**Base Map:**
- Center on midpoint between home and work
- Zoom level: 13 (configurable)
- Tile layer: OpenStreetMap or CartoDB Positron

**Route Layers:**
- Each route group in different color
- Optimal route: thick red line (weight=5)
- Alternative routes: thinner lines (weight=3)
- Opacity: 0.7 for non-optimal routes

**Markers:**
- Home: green house icon
- Work: blue building icon
- Custom icons from Font Awesome

**Interactive Elements:**
- Click route for statistics popup
- Hover for route name
- Layer control to toggle routes
- Legend with route comparison

**Heatmap:**
- Show most frequently used paths
- Gradient: blue (low) → red (high)
- Radius: 15 pixels

---

## 7. Report Generator Module (`report_generator.py`)

### Purpose
Create comprehensive HTML reports with embedded maps and statistics.

### Key Functions

```python
class ReportGenerator:
    def __init__(self, analysis_results: dict)
    def generate_summary_section(self) -> str
    def generate_comparison_table(self) -> str
    def generate_statistics_section(self) -> str
    def generate_recommendations(self) -> str
    def render_template(self, template_name: str, context: dict) -> str
    def save_report(self, output_path: str) -> None
```

### Report Structure

**HTML Template (Jinja2):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Strava Commute Analysis Report</title>
    <style>/* Bootstrap + custom CSS */</style>
</head>
<body>
    <div class="container">
        <h1>Commute Route Analysis</h1>
        
        <!-- Executive Summary -->
        <section id="summary">
            <h2>Recommended Route</h2>
            <div class="alert alert-success">
                <strong>Route {{ optimal_route.id }}</strong>
                <p>{{ optimal_route.description }}</p>
            </div>
        </section>
        
        <!-- Comparison Table -->
        <section id="comparison">
            <h2>Route Comparison</h2>
            <table class="table">
                <!-- Route metrics table -->
            </table>
        </section>
        
        <!-- Interactive Map -->
        <section id="map">
            <h2>Route Visualization</h2>
            <div id="map-container">
                {{ map_html | safe }}
            </div>
        </section>
        
        <!-- Detailed Statistics -->
        <section id="statistics">
            <h2>Detailed Analysis</h2>
            <!-- Charts and graphs -->
        </section>
        
        <!-- Recommendations -->
        <section id="recommendations">
            <h2>Recommendations</h2>
            <ul>
                <li>Primary route: {{ primary_route }}</li>
                <li>Alternative for variety: {{ alternative_route }}</li>
                <li>Weather considerations: {{ weather_notes }}</li>
            </ul>
        </section>
    </div>
</body>
</html>
```

### Statistics to Include

**Summary Metrics:**
- Total activities analyzed
- Date range
- Total distance/time commuted
- Average commute time
- Potential time savings with optimal route

**Route Comparison:**
- Distance, duration, speed for each route
- Elevation profile
- Usage frequency
- Composite score

**Visualizations:**
- Bar chart: route comparison
- Line chart: commute time trends
- Pie chart: route usage distribution

---

## 8. Configuration System

### Configuration File (`config/config.yaml`)

```yaml
strava:
  client_id: ${STRAVA_CLIENT_ID}
  client_secret: ${STRAVA_CLIENT_SECRET}

data_fetching:
  cache_enabled: true
  cache_duration_days: 7
  max_activities: 500

location_detection:
  clustering:
    eps: 0.002  # ~200 meters
    min_samples: 5
  time_windows:
    morning_start: "06:00"
    morning_end: "10:00"
    evening_start: "16:00"
    evening_end: "20:00"

route_filtering:
  min_distance_km: 2
  max_distance_km: 30
  activity_types:
    - Ride
    - EBikeRide
  exclude_virtual: true

route_analysis:
  similarity_threshold: 0.85
  min_route_frequency: 2

optimization:
  weights:
    time: 0.4
    distance: 0.3
    safety: 0.3

visualization:
  map:
    zoom_level: 13
    tile_layer: "OpenStreetMap"
  colors:
    optimal: "#FF0000"
    alternative: ["#00FF00", "#0000FF", "#FFA500", "#800080"]
  route_weight:
    optimal: 5
    alternative: 3

output:
  report_directory: "output/reports"
  map_filename: "route_map.html"
  report_filename: "commute_analysis.html"
```

---

## 9. Main Entry Point (`main.py`)

### Command-Line Interface

```python
import argparse

def main():
    parser = argparse.ArgumentParser(description='Analyze Strava commute routes')
    parser.add_argument('--auth', action='store_true', help='Authenticate with Strava')
    parser.add_argument('--fetch', action='store_true', help='Fetch new activities')
    parser.add_argument('--analyze', action='store_true', help='Analyze routes')
    parser.add_argument('--config', type=str, default='config/config.yaml')
    parser.add_argument('--output', type=str, default='output/reports')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Authentication
    if args.auth:
        authenticate_strava(config)
        return
    
    # Main workflow
    client = get_authenticated_client(config)
    
    if args.fetch:
        fetch_activities(client, config)
    
    if args.analyze:
        analyze_and_generate_report(client, config, args.output)

if __name__ == '__main__':
    main()
```

### Workflow

1. **Authentication** (first run only)
   - Open browser for OAuth
   - Save tokens

2. **Data Fetching**
   - Load cached activities
   - Fetch new activities if needed
   - Update cache

3. **Location Identification**
   - Cluster endpoints
   - Identify home and work

4. **Route Analysis**
   - Extract routes between locations
   - Group similar routes
   - Calculate metrics

5. **Optimization**
   - Score all routes
   - Rank by composite score

6. **Visualization**
   - Generate interactive map
   - Create HTML report

7. **Output**
   - Save report to output directory
   - Print summary to console

---

## 10. Error Handling Strategy

### Exception Hierarchy

```python
class StravaAnalyzerError(Exception):
    """Base exception"""

class AuthenticationError(StravaAnalyzerError):
    """Authentication failed"""

class DataFetchError(StravaAnalyzerError):
    """Failed to fetch data"""

class InsufficientDataError(StravaAnalyzerError):
    """Not enough activities for analysis"""

class LocationDetectionError(StravaAnalyzerError):
    """Could not identify home/work locations"""
```

### Error Handling Patterns

```python
try:
    activities = fetch_activities(client)
except RateLimitExceeded:
    logger.warning("Rate limit exceeded, using cached data")
    activities = load_cached_activities()
except NetworkError as e:
    logger.error(f"Network error: {e}")
    raise DataFetchError("Could not fetch activities")

if len(activities) < 10:
    raise InsufficientDataError(
        f"Need at least 10 activities, found {len(activities)}"
    )
```

---

## 11. Testing Strategy

### Unit Tests

```python
# tests/test_location_finder.py
def test_cluster_locations():
    activities = create_mock_activities()
    finder = LocationFinder(activities)
    clusters = finder.cluster_locations()
    assert len(clusters) >= 2

def test_identify_home_work():
    activities = create_commute_activities()
    finder = LocationFinder(activities)
    home, work = finder.identify_home_work()
    assert home.name == "Home"
    assert work.name == "Work"
```

### Integration Tests

```python
# tests/test_integration.py
def test_full_workflow():
    # Mock Strava API
    with mock_strava_api():
        client = get_authenticated_client()
        activities = fetch_activities(client)
        home, work = identify_locations(activities)
        routes = analyze_routes(activities, home, work)
        optimal = optimize_routes(routes)
        assert optimal is not None
```

### Test Data

- Create synthetic activity data
- Mock Strava API responses
- Test edge cases:
  - No activities
  - Single location
  - Irregular patterns
  - Missing GPS data

---

## 12. Performance Considerations

### Optimization Strategies

1. **Caching**
   - Cache API responses
   - Store processed data
   - Avoid redundant calculations

2. **Batch Processing**
   - Fetch activities in batches
   - Process routes in parallel (if needed)

3. **Memory Management**
   - Stream large datasets
   - Clear unused data
   - Use generators for iteration

4. **API Rate Limiting**
   - Respect Strava limits
   - Implement exponential backoff
   - Use cached data when possible

### Expected Performance

- Authentication: < 5 seconds
- Fetch 100 activities: 10-30 seconds
- Location clustering: < 1 second
- Route analysis: 5-10 seconds
- Map generation: 2-5 seconds
- Total runtime: 30-60 seconds

---

## 13. Dependencies

### Core Requirements

```
stravalib>=0.10.0
pandas>=1.5.0
numpy>=1.23.0
scikit-learn>=1.1.0
geopy>=2.3.0
folium>=0.14.0
jinja2>=3.1.0
pyyaml>=6.0
python-dotenv>=0.21.0
polyline>=2.0.0
requests>=2.28.0
```

### Development Requirements

```
pytest>=7.2.0
pytest-cov>=4.0.0
black>=22.10.0
flake8>=5.0.0
mypy>=0.991