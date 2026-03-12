# Implementation Guide - Step-by-Step

This guide provides a detailed walkthrough for implementing the Strava Commute Route Analyzer.

## Implementation Order

Follow these phases in sequence for optimal development flow:

---

## Phase 1: Foundation & Setup

### Step 1.1: Project Structure Setup

Create the directory structure:

```bash
mkdir -p src config data/cache output/reports tests
touch src/__init__.py
touch main.py
```

### Step 1.2: Dependencies

Create `requirements.txt`:

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

Install dependencies:
```bash
pip install -r requirements.txt
```

### Step 1.3: Configuration Files

Create `.env`:
```
STRAVA_CLIENT_ID=210778
STRAVA_CLIENT_SECRET=6ca357f46999a4ed14715c3de7fa2cfbbd0fee3e
```

Create `config/config.yaml` (see TECHNICAL_SPEC.md for full content)

Create `.gitignore`:
```
.env
config/credentials.json
data/cache/
output/
venv/
__pycache__/
*.pyc
.pytest_cache/
```

---

## Phase 2: Authentication Module

### Step 2.1: Create `src/auth.py`

**Key Components:**
1. `StravaAuthenticator` class
2. OAuth flow implementation
3. Token storage and refresh
4. Client initialization

**Testing:**
```python
# Test authentication
python -c "from src.auth import StravaAuthenticator; auth = StravaAuthenticator(); auth.authenticate()"
```

**Success Criteria:**
- Browser opens for OAuth
- Tokens saved to `config/credentials.json`
- Can create authenticated client

---

## Phase 3: Data Fetching

### Step 3.1: Create `src/data_fetcher.py`

**Key Components:**
1. `StravaDataFetcher` class
2. Activity fetching with pagination
3. Caching mechanism
4. Activity filtering

**Implementation Priority:**
1. Basic activity fetching
2. Caching to JSON
3. Filtering by type and distance
4. Stream data fetching (polylines)

**Testing:**
```python
# Test data fetching
from src.auth import get_authenticated_client
from src.data_fetcher import StravaDataFetcher

client = get_authenticated_client()
fetcher = StravaDataFetcher(client)
activities = fetcher.fetch_activities(limit=10)
print(f"Fetched {len(activities)} activities")
```

**Success Criteria:**
- Fetches activities from Strava
- Saves to cache
- Loads from cache on subsequent runs
- Filters correctly

---

## Phase 4: Location Detection

### Step 4.1: Create `src/location_finder.py`

**Key Components:**
1. `LocationFinder` class
2. Endpoint extraction
3. DBSCAN clustering
4. Home/work identification using time heuristics

**Implementation Steps:**

1. **Extract Endpoints:**
```python
def extract_endpoints(self):
    endpoints = []
    for activity in self.activities:
        if activity.start_latlng:
            endpoints.append({
                'lat': activity.start_latlng[0],
                'lon': activity.start_latlng[1],
                'time': activity.start_date.time(),
                'type': 'start'
            })
        if activity.end_latlng:
            endpoints.append({
                'lat': activity.end_latlng[0],
                'lon': activity.end_latlng[1],
                'time': activity.start_date.time() + activity.elapsed_time,
                'type': 'end'
            })
    return endpoints
```

2. **Apply DBSCAN:**
```python
from sklearn.cluster import DBSCAN

coords = np.array([[e['lat'], e['lon']] for e in endpoints])
clustering = DBSCAN(eps=0.002, min_samples=5).fit(coords)
```

3. **Identify Home/Work:**
- Calculate average departure/arrival times for each cluster
- Morning departures (6-10 AM) → likely home
- Evening arrivals (4-8 PM) → likely home

**Testing:**
```python
from src.location_finder import LocationFinder

finder = LocationFinder(activities)
home, work = finder.identify_home_work()
print(f"Home: {home.lat}, {home.lon}")
print(f"Work: {work.lat}, {work.lon}")
```

**Success Criteria:**
- Correctly identifies 2+ location clusters
- Distinguishes home from work
- Handles edge cases (irregular schedules)

---

## Phase 5: Route Analysis

### Step 5.1: Create `src/route_analyzer.py`

**Key Components:**
1. `RouteAnalyzer` class
2. Route extraction between locations
3. Polyline decoding
4. Route similarity calculation
5. Route grouping
6. Metrics calculation

**Implementation Steps:**

1. **Extract Routes:**
```python
def extract_routes(self, direction='home_to_work'):
    routes = []
    for activity in self.activities:
        if self._is_commute(activity, direction):
            route = self._create_route(activity)
            routes.append(route)
    return routes
```

2. **Decode Polylines:**
```python
import polyline

def decode_polyline(encoded):
    return polyline.decode(encoded)
```

3. **Calculate Similarity:**
```python
from scipy.spatial.distance import directed_hausdorff

def calculate_similarity(route1, route2):
    coords1 = np.array(route1.coordinates)
    coords2 = np.array(route2.coordinates)
    
    dist_forward = directed_hausdorff(coords1, coords2)[0]
    dist_backward = directed_hausdorff(coords2, coords1)[0]
    
    max_dist = max(dist_forward, dist_backward)
    similarity = 1 / (1 + max_dist * 100)  # Normalize
    return similarity
```

4. **Group Routes:**
```python
def group_similar_routes(self, threshold=0.85):
    groups = []
    ungrouped = self.routes.copy()
    
    while ungrouped:
        current = ungrouped.pop(0)
        group = [current]
        
        for route in ungrouped[:]:
            if self.calculate_similarity(current, route) > threshold:
                group.append(route)
                ungrouped.remove(route)
        
        groups.append(RouteGroup(routes=group))
    
    return groups
```

**Testing:**
```python
analyzer = RouteAnalyzer(activities, home, work)
route_groups = analyzer.group_similar_routes()
print(f"Found {len(route_groups)} route variants")
```

**Success Criteria:**
- Extracts routes between home and work
- Groups similar routes correctly
- Calculates accurate metrics

---

## Phase 6: Route Optimization

### Step 6.1: Create `src/optimizer.py`

**Key Components:**
1. `RouteOptimizer` class
2. Time scoring
3. Distance scoring
4. Safety scoring
5. Composite scoring
6. Route ranking

**Implementation Steps:**

1. **Time Score:**
```python
def calculate_time_score(self, metrics):
    # Normalize duration (faster = higher score)
    duration_score = 100 * (1 - (metrics.avg_duration - self.min_duration) / 
                           (self.max_duration - self.min_duration))
    
    # Bonus for consistency
    consistency_bonus = metrics.consistency_score * 10
    
    return min(100, duration_score + consistency_bonus)
```

2. **Safety Score:**
```python
def calculate_safety_score(self, route_group):
    # Frequency component
    freq_score = (route_group.frequency / self.max_frequency) * 100
    
    # Elevation component
    elev_penalty = min(50, route_group.metrics.avg_elevation / 10)
    elev_score = 100 - elev_penalty
    
    # Road type inference
    road_score = self._infer_road_safety(route_group)
    
    return (freq_score * 0.4 + road_score * 0.3 + elev_score * 0.3)
```

3. **Composite Score:**
```python
def calculate_composite_score(self, route_group):
    time_score = self.calculate_time_score(route_group.metrics)
    dist_score = self.calculate_distance_score(route_group.metrics)
    safety_score = self.calculate_safety_score(route_group)
    
    return (time_score * self.weights['time'] +
            dist_score * self.weights['distance'] +
            safety_score * self.weights['safety'])
```

**Testing:**
```python
optimizer = RouteOptimizer(route_groups, weights={'time': 0.4, 'distance': 0.3, 'safety': 0.3})
ranked_routes = optimizer.rank_routes()
optimal = optimizer.get_optimal_route()
print(f"Optimal route score: {optimal[1]:.2f}")
```

**Success Criteria:**
- Scores all routes
- Ranks correctly
- Identifies optimal route

---

## Phase 7: Visualization

### Step 7.1: Create `src/visualizer.py`

**Key Components:**
1. `RouteVisualizer` class
2. Folium map creation
3. Route layers
4. Markers and popups
5. Heatmap overlay

**Implementation Steps:**

1. **Create Base Map:**
```python
import folium

def create_base_map(self):
    center_lat = (self.home.lat + self.work.lat) / 2
    center_lon = (self.home.lon + self.work.lon) / 2
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    return m
```

2. **Add Route Layers:**
```python
def add_route_layer(self, route_group, color, weight):
    coords = route_group.representative_route.coordinates
    
    folium.PolyLine(
        coords,
        color=color,
        weight=weight,
        opacity=0.7,
        popup=self._create_popup(route_group)
    ).add_to(self.map)
```

3. **Add Markers:**
```python
def add_location_markers(self):
    folium.Marker(
        [self.home.lat, self.home.lon],
        popup='Home',
        icon=folium.Icon(color='green', icon='home')
    ).add_to(self.map)
    
    folium.Marker(
        [self.work.lat, self.work.lon],
        popup='Work',
        icon=folium.Icon(color='blue', icon='building')
    ).add_to(self.map)
```

**Testing:**
```python
visualizer = RouteVisualizer(route_groups, home, work)
visualizer.generate_map('output/test_map.html')
# Open in browser to verify
```

**Success Criteria:**
- Map displays correctly
- Routes are visible and distinguishable
- Markers show home and work
- Interactive elements work

---

## Phase 8: Report Generation

### Step 8.1: Create `src/report_generator.py`

**Key Components:**
1. `ReportGenerator` class
2. Jinja2 templates
3. Statistics calculation
4. HTML rendering

**Implementation Steps:**

1. **Create HTML Template:**
```html
<!-- templates/report.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Commute Analysis Report</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">
</head>
<body>
    <div class="container mt-5">
        <h1>Strava Commute Analysis</h1>
        
        <div class="alert alert-success">
            <h4>Recommended Route: {{ optimal_route.name }}</h4>
            <p>{{ optimal_route.description }}</p>
        </div>
        
        <!-- Comparison table -->
        <table class="table">
            {% for route in routes %}
            <tr>
                <td>{{ route.name }}</td>
                <td>{{ route.distance }} km</td>
                <td>{{ route.duration }} min</td>
                <td>{{ route.score }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <!-- Embedded map -->
        <div id="map">
            {{ map_html | safe }}
        </div>
    </div>
</body>
</html>
```

2. **Generate Report:**
```python
from jinja2 import Environment, FileSystemLoader

def generate_report(self, output_path):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('report.html')
    
    context = {
        'optimal_route': self.optimal_route,
        'routes': self.all_routes,
        'map_html': self.map_html,
        'statistics': self.statistics
    }
    
    html = template.render(context)
    
    with open(output_path, 'w') as f:
        f.write(html)
```

**Testing:**
```python
generator = ReportGenerator(analysis_results)
generator.save_report('output/reports/commute_analysis.html')
```

**Success Criteria:**
- HTML report generates successfully
- All sections display correctly
- Map is embedded properly
- Report is visually appealing

---

## Phase 9: Main Entry Point

### Step 9.1: Create `main.py`

**Implementation:**

```python
#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path

from src.auth import StravaAuthenticator, get_authenticated_client
from src.data_fetcher import StravaDataFetcher
from src.location_finder import LocationFinder
from src.route_analyzer import RouteAnalyzer
from src.optimizer import RouteOptimizer
from src.visualizer import RouteVisualizer
from src.report_generator import ReportGenerator
from src.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info("Starting authentication...")
        auth = StravaAuthenticator(config)
        auth.authenticate()
        logger.info("Authentication successful!")
        return
    
    # Get authenticated client
    client = get_authenticated_client(config)
    
    # Fetch activities
    if args.fetch:
        logger.info("Fetching activities...")
        fetcher = StravaDataFetcher(client, config)
        activities = fetcher.fetch_activities()
        fetcher.cache_activities(activities)
        logger.info(f"Fetched {len(activities)} activities")
    
    # Analyze routes
    if args.analyze:
        logger.info("Starting route analysis...")
        
        # Load activities
        fetcher = StravaDataFetcher(client, config)
        activities = fetcher.load_cached_activities()
        logger.info(f"Loaded {len(activities)} activities from cache")
        
        # Identify locations
        logger.info("Identifying home and work locations...")
        finder = LocationFinder(activities, config)
        home, work = finder.identify_home_work()
        logger.info(f"Home: ({home.lat:.4f}, {home.lon:.4f})")
        logger.info(f"Work: ({work.lat:.4f}, {work.lon:.4f})")
        
        # Analyze routes
        logger.info("Analyzing routes...")
        analyzer = RouteAnalyzer(activities, home, work, config)
        route_groups = analyzer.group_similar_routes()
        logger.info(f"Found {len(route_groups)} route variants")
        
        # Optimize
        logger.info("Optimizing route selection...")
        optimizer = RouteOptimizer(route_groups, config)
        ranked_routes = optimizer.rank_routes()
        optimal_route = optimizer.get_optimal_route()
        logger.info(f"Optimal route: {optimal_route[0].id} (score: {optimal_route[1]:.2f})")
        
        # Visualize
        logger.info("Generating map...")
        visualizer = RouteVisualizer(route_groups, home, work, config)
        map_html = visualizer.generate_map()
        
        # Generate report
        logger.info("Generating report...")
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generator = ReportGenerator({
            'optimal_route': optimal_route,
            'ranked_routes': ranked_routes,
            'home': home,
            'work': work,
            'map_html': map_html,
            'config': config
        })
        
        report_path = output_dir / 'commute_analysis.html'
        generator.save_report(report_path)
        
        logger.info(f"Report saved to: {report_path}")
        logger.info("Analysis complete!")

if __name__ == '__main__':
    main()
```

**Testing:**
```bash
# Full workflow test
python main.py --auth
python main.py --fetch --analyze
```

**Success Criteria:**
- All commands work
- Error handling is robust
- Output is clear and informative

---

## Phase 10: Testing & Documentation

### Step 10.1: Unit Tests

Create tests for each module:

```python
# tests/test_location_finder.py
import pytest
from src.location_finder import LocationFinder

def test_cluster_locations():
    # Test with mock data
    pass

def test_identify_home_work():
    # Test home/work identification
    pass
```

### Step 10.2: Integration Tests

Test the full workflow with mock data.

### Step 10.3: Documentation

Ensure all documentation is complete:
- README.md ✓
- PLAN.md ✓
- TECHNICAL_SPEC.md ✓
- IMPLEMENTATION_GUIDE.md ✓
- Code comments and docstrings

---

## Validation Checklist

Before considering the project complete:

- [ ] Authentication works
- [ ] Activities fetch successfully
- [ ] Caching works correctly
- [ ] Locations identified accurately
- [ ] Routes extracted and grouped
- [ ] Optimization produces sensible results
- [ ] Map displays correctly
- [ ] Report generates successfully
- [ ] Error handling is robust
- [ ] Documentation is complete
- [ ] Tests pass
- [ ] Code is clean and well-commented

---

## Common Issues & Solutions

### Issue: DBSCAN finds no clusters
**Solution:** Reduce `min_samples` or increase `eps`

### Issue: Routes not grouping correctly
**Solution:** Adjust similarity threshold or improve similarity algorithm

### Issue: Map doesn't display
**Solution:** Check that polylines are decoded correctly and coordinates are valid

### Issue: API rate limit
**Solution:** Implement better caching and reduce API calls

---

## Next Steps After Implementation

1. **Test with real data**: Run on your actual Strava activities
2. **Refine parameters**: Adjust weights and thresholds based on results
3. **Add features**: Consider weather integration, traffic data, etc.
4. **Optimize performance**: Profile and improve slow sections
5. **Share**: Consider open-sourcing or sharing with the cycling community

---

## Estimated Timeline

- **Phase 1-2 (Setup & Auth)**: 2-3 hours
- **Phase 3 (Data Fetching)**: 3-4 hours
- **Phase 4 (Location Detection)**: 4-5 hours
- **Phase 5 (Route Analysis)**: 6-8 hours
- **Phase 6 (Optimization)**: 3-4 hours
- **Phase 7 (Visualization)**: 4-5 hours
- **Phase 8 (Report Generation)**: 3-4 hours
- **Phase 9 (Main Entry)**: 2-3 hours
- **Phase 10 (Testing & Docs)**: 4-5 hours

**Total**: 30-45 hours of development time

---

## Resources

- Strava API Docs: https://developers.strava.com/
- stravalib Documentation: https://github.com/stravalib/stravalib
- Folium Documentation: https://python-visualization.github.io/folium/
- DBSCAN Algorithm: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html