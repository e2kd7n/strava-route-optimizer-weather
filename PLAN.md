# Strava Commute Route Analyzer - Project Plan

## Overview
A Python application that analyzes Strava cycling activities to determine optimal commute routes between home and work, considering time, distance, and safety factors.

## Project Goals
1. Automatically identify home and work locations from Strava activity data
2. Extract and analyze all routes between these locations
3. Determine optimal routes based on multiple criteria (time, distance, safety)
4. Generate interactive HTML reports with map visualizations

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Strava Route Analyzer                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Authentication  │      │  Data Fetcher    │            │
│  │    Module        │─────▶│    Module        │            │
│  └──────────────────┘      └──────────────────┘            │
│           │                         │                        │
│           │                         ▼                        │
│           │                ┌──────────────────┐            │
│           │                │  Location        │            │
│           │                │  Clustering      │            │
│           │                └──────────────────┘            │
│           │                         │                        │
│           │                         ▼                        │
│           │                ┌──────────────────┐            │
│           │                │  Route           │            │
│           │                │  Analyzer        │            │
│           │                └──────────────────┘            │
│           │                         │                        │
│           │                         ▼                        │
│           │                ┌──────────────────┐            │
│           │                │  Optimization    │            │
│           │                │  Engine          │            │
│           │                └──────────────────┘            │
│           │                         │                        │
│           │                         ▼                        │
│           │                ┌──────────────────┐            │
│           └───────────────▶│  Report          │            │
│                            │  Generator       │            │
│                            └──────────────────┘            │
│                                     │                        │
│                                     ▼                        │
│                            ┌──────────────────┐            │
│                            │  HTML Output     │            │
│                            │  with Maps       │            │
│                            └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Technical Approach

### 1. Project Structure
```
commute/
├── src/
│   ├── __init__.py
│   ├── auth.py              # Strava OAuth authentication
│   ├── data_fetcher.py      # Fetch activities from Strava API
│   ├── location_finder.py   # Identify home/work locations
│   ├── route_analyzer.py    # Analyze and compare routes
│   ├── optimizer.py         # Multi-criteria route optimization
│   ├── visualizer.py        # Generate maps and visualizations
│   └── report_generator.py  # Create HTML reports
├── config/
│   ├── config.yaml          # User configuration
│   └── credentials.json     # API credentials (gitignored)
├── data/
│   └── cache/               # Cached activity data
├── output/
│   └── reports/             # Generated HTML reports
├── tests/
│   └── test_*.py            # Unit tests
├── requirements.txt
├── README.md
├── .env.example
└── main.py                  # Entry point
```

### 2. Key Technologies

**Core Libraries:**
- `stravalib` - Strava API client
- `pandas` - Data manipulation and analysis
- `numpy` - Numerical computations
- `scikit-learn` - Clustering algorithms (DBSCAN for location identification)
- `geopy` - Geographic calculations
- `folium` - Interactive map generation
- `jinja2` - HTML template rendering

**Additional Tools:**
- `python-dotenv` - Environment variable management
- `pyyaml` - Configuration file parsing
- `requests` - HTTP requests
- `polyline` - Decode Strava polylines

### 3. Location Identification Algorithm

**Approach: DBSCAN Clustering**
- Collect start/end points from all activities
- Apply DBSCAN clustering to identify frequent locations
- Identify the two most frequent clusters as home and work
- Use time-of-day heuristics to distinguish home from work:
  - Morning departures (6-10 AM) likely from home
  - Evening arrivals (4-8 PM) likely at home

### 4. Route Analysis Strategy

**Route Extraction:**
1. Filter activities between identified home/work locations
2. Decode polyline data to get GPS coordinates
3. Group similar routes using path similarity algorithms
4. Calculate statistics for each route variant

**Metrics to Calculate:**
- Average duration
- Average distance
- Speed consistency (standard deviation)
- Elevation gain/loss
- Time of day patterns
- Weather conditions (if available)
- Route frequency (how often used)

### 5. Multi-Criteria Optimization

**Scoring System:**
```python
score = w1 * time_score + w2 * distance_score + w3 * safety_score
```

**Time Score (40% weight):**
- Faster routes score higher
- Consider consistency (lower variance = higher score)

**Distance Score (30% weight):**
- Shorter routes score higher
- Balance with time (sometimes longer but faster is better)

**Safety Score (30% weight):**
- Route frequency (more used = more familiar = safer)
- Road type inference from GPS patterns:
  - Straight segments at high speed = main roads
  - Winding paths at lower speed = residential/bike paths
- Elevation changes (flatter = safer for commuting)

### 6. Visualization Features

**Interactive Map Elements:**
- All route variants displayed with different colors
- Optimal route highlighted prominently
- Home and work markers
- Clickable route segments showing statistics
- Heatmap overlay showing most-used paths
- Legend with route comparison table

**Report Sections:**
1. Executive Summary
   - Recommended optimal route
   - Key statistics comparison
   - Time/distance savings

2. Route Comparison Table
   - All identified routes
   - Metrics for each route
   - Pros/cons analysis

3. Interactive Map
   - Visual route comparison
   - Zoom and pan capabilities

4. Detailed Analytics
   - Time-of-day patterns
   - Seasonal variations (if data available)
   - Performance trends

5. Recommendations
   - Primary route suggestion
   - Alternative routes for variety
   - Weather-dependent suggestions

## Implementation Phases

### Phase 1: Foundation
- Set up project structure
- Implement Strava authentication
- Create basic data fetching functionality

### Phase 2: Data Analysis
- Implement location clustering
- Build route extraction logic
- Calculate basic route metrics

### Phase 3: Optimization
- Develop multi-criteria scoring system
- Implement route comparison algorithm
- Add safety factor calculations

### Phase 4: Visualization
- Create interactive maps with Folium
- Build HTML report templates
- Add statistical visualizations

### Phase 5: Polish
- Add configuration file support
- Implement caching for API calls
- Create comprehensive documentation
- Add error handling and validation

## Configuration Options

**User-Configurable Parameters:**
```yaml
optimization:
  weights:
    time: 0.4
    distance: 0.3
    safety: 0.3
  
location_detection:
  min_activities: 5
  cluster_radius_meters: 200
  
filtering:
  max_distance_km: 30
  min_distance_km: 2
  activity_types:
    - Ride
    - EBikeRide
  
output:
  map_zoom: 13
  route_colors:
    - "#FF0000"
    - "#00FF00"
    - "#0000FF"
```

## API Considerations

**Strava API Limits:**
- 100 requests per 15 minutes
- 1000 requests per day
- Implement caching to minimize API calls
- Store processed data locally

**Required OAuth Scopes:**
- `activity:read_all` - Read all activity data
- `profile:read_all` - Read profile information

## Success Criteria

1. Successfully authenticates with Strava API
2. Accurately identifies home and work locations (>90% accuracy)
3. Extracts and analyzes all commute routes
4. Generates clear, actionable recommendations
5. Creates visually appealing, interactive HTML reports
6. Runs efficiently with minimal API calls
7. Handles edge cases gracefully

## Future Enhancements

- Weather data integration
- Traffic pattern analysis
- Carbon footprint calculations
- Integration with other fitness platforms
- Mobile app version
- Real-time route suggestions
- Social features (compare with other commuters)

## Security Considerations

- Store API credentials securely (environment variables)
- Never commit credentials to version control
- Implement token refresh mechanism
- Validate all user inputs
- Sanitize data before display in HTML

## Testing Strategy

- Unit tests for each module
- Integration tests for API interactions
- Mock Strava API responses for testing
- Test with various data scenarios:
  - Few activities
  - Many activities
  - Multiple potential home/work locations
  - Irregular commute patterns