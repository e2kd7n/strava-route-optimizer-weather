# Strava Commute Analyzer - Workflow Diagram

## High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION (First Run)                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. User runs: python main.py --auth                        │ │
│  │ 2. Browser opens for Strava OAuth                          │ │
│  │ 3. User grants permissions                                 │ │
│  │ 4. Tokens saved to config/credentials.json                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA FETCHING PHASE                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Load cached activities (if exist)                       │ │
│  │ 2. Fetch new activities from Strava API                    │ │
│  │ 3. Filter by type (Ride, EBikeRide)                        │ │
│  │ 4. Filter by distance (2-30 km)                            │ │
│  │ 5. Decode polylines for GPS coordinates                    │ │
│  │ 6. Save to cache (data/cache/activities.json)              │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LOCATION IDENTIFICATION                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Extract start/end coordinates from all activities       │ │
│  │ 2. Apply DBSCAN clustering (eps=200m, min_samples=5)       │ │
│  │ 3. Identify top 2 clusters by frequency                    │ │
│  │ 4. Analyze time patterns:                                  │ │
│  │    - Morning departures (6-10 AM) → Home                   │ │
│  │    - Evening arrivals (4-8 PM) → Home                      │ │
│  │ 5. Assign Home and Work labels                             │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ROUTE EXTRACTION                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Filter activities between Home and Work                 │ │
│  │ 2. Separate by direction:                                  │ │
│  │    - Home → Work (morning commutes)                        │ │
│  │    - Work → Home (evening commutes)                        │ │
│  │ 3. Decode polylines to GPS coordinates                     │ │
│  │ 4. Extract route metadata (distance, time, elevation)      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ROUTE GROUPING                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Calculate pairwise route similarity                     │ │
│  │    - Use Hausdorff distance algorithm                      │ │
│  │    - Normalize by route length                             │ │
│  │ 2. Group routes with similarity > 85%                      │ │
│  │ 3. Select representative route for each group              │ │
│  │ 4. Calculate group statistics:                             │ │
│  │    - Average duration, distance, speed                     │ │
│  │    - Standard deviation (consistency)                      │ │
│  │    - Elevation gain/loss                                   │ │
│  │    - Usage frequency                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-CRITERIA SCORING                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ For each route group, calculate:                           │ │
│  │                                                             │ │
│  │ TIME SCORE (40% weight):                                   │ │
│  │   - Faster routes score higher                             │ │
│  │   - Bonus for consistency (low variance)                   │ │
│  │   - Formula: 100 * (1 - normalized_duration) + bonus       │ │
│  │                                                             │ │
│  │ DISTANCE SCORE (30% weight):                               │ │
│  │   - Shorter routes score higher                            │ │
│  │   - Formula: 100 * (1 - normalized_distance)               │ │
│  │                                                             │ │
│  │ SAFETY SCORE (30% weight):                                 │ │
│  │   - Frequency: More used = more familiar = safer           │ │
│  │   - Road type: Inferred from GPS patterns                  │ │
│  │   - Elevation: Flatter routes score higher                 │ │
│  │   - Formula: weighted_sum(frequency, road, elevation)      │ │
│  │                                                             │ │
│  │ COMPOSITE SCORE:                                           │ │
│  │   = time_score * 0.4 + dist_score * 0.3 + safety * 0.3    │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ROUTE RANKING                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Sort routes by composite score (highest first)          │ │
│  │ 2. Identify optimal route (highest score)                  │ │
│  │ 3. Identify alternative routes for variety                 │ │
│  │ 4. Generate recommendations based on:                      │ │
│  │    - Weather conditions (if available)                     │ │
│  │    - Time of day                                           │ │
│  │    - User preferences                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MAP VISUALIZATION                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Create Folium base map centered on midpoint             │ │
│  │ 2. Add route layers:                                       │ │
│  │    - Optimal route: thick red line (weight=5)              │ │
│  │    - Alternative routes: colored lines (weight=3)          │ │
│  │ 3. Add location markers:                                   │ │
│  │    - Home: green house icon                                │ │
│  │    - Work: blue building icon                              │ │
│  │ 4. Add interactive elements:                               │ │
│  │    - Click routes for statistics popup                     │ │
│  │    - Hover for route names                                 │ │
│  │    - Layer control to toggle routes                        │ │
│  │ 5. Add heatmap overlay (optional)                          │ │
│  │ 6. Generate HTML map file                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     REPORT GENERATION                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Compile analysis results                                │ │
│  │ 2. Generate HTML sections:                                 │ │
│  │    a) Executive Summary                                    │ │
│  │       - Recommended optimal route                          │ │
│  │       - Key statistics and savings                         │ │
│  │    b) Route Comparison Table                               │ │
│  │       - All routes with metrics                            │ │
│  │       - Sortable columns                                   │ │
│  │    c) Interactive Map                                      │ │
│  │       - Embedded Folium map                                │ │
│  │    d) Detailed Analytics                                   │ │
│  │       - Charts and graphs                                  │ │
│  │       - Time-of-day patterns                               │ │
│  │    e) Recommendations                                      │ │
│  │       - Primary and alternative routes                     │ │
│  │       - Usage suggestions                                  │ │
│  │ 3. Render using Jinja2 template                            │ │
│  │ 4. Save to output/reports/commute_analysis.html            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         OUTPUT                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Files Generated:                                            │ │
│  │ - output/reports/commute_analysis.html (main report)        │ │
│  │ - output/reports/route_map.html (standalone map)            │ │
│  │ - data/cache/activities.json (cached data)                  │ │
│  │                                                             │ │
│  │ Console Output:                                             │ │
│  │ - Summary of findings                                       │ │
│  │ - Optimal route recommendation                              │ │
│  │ - Path to generated report                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Module Interactions

```
┌──────────────┐
│   main.py    │
│  (Entry)     │
└──────┬───────┘
       │
       ├─────────────────────────────────────────────────────┐
       │                                                       │
       ▼                                                       ▼
┌──────────────┐                                      ┌──────────────┐
│   auth.py    │                                      │  config.py   │
│              │                                      │              │
│ - OAuth flow │                                      │ - Load YAML  │
│ - Token mgmt │                                      │ - Env vars   │
└──────┬───────┘                                      └──────┬───────┘
       │                                                       │
       │ provides authenticated client                        │
       │                                                       │
       ▼                                                       │
┌──────────────────┐                                          │
│ data_fetcher.py  │◄─────────────────────────────────────────┘
│                  │
│ - Fetch activities
│ - Cache management
│ - Filtering
└──────┬───────────┘
       │
       │ provides filtered activities
       │
       ▼
┌──────────────────┐
│location_finder.py│
│                  │
│ - DBSCAN cluster
│ - Time analysis
│ - Home/Work ID
└──────┬───────────┘
       │
       │ provides home & work locations
       │
       ▼
┌──────────────────┐
│route_analyzer.py │
│                  │
│ - Extract routes
│ - Similarity calc
│ - Route grouping
│ - Metrics
└──────┬───────────┘
       │
       │ provides route groups with metrics
       │
       ▼
┌──────────────────┐
│  optimizer.py    │
│                  │
│ - Score routes
│ - Rank routes
│ - Select optimal
└──────┬───────────┘
       │
       │ provides ranked routes
       │
       ├─────────────────────┬─────────────────────┐
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│visualizer.py │    │report_gen.py │    │   Output     │
│              │    │              │    │              │
│ - Folium map │───▶│ - HTML gen   │───▶│ - HTML files │
│ - Layers     │    │ - Templates  │    │ - Console    │
│ - Markers    │    │ - Statistics │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

## State Transitions

```
┌─────────────┐
│   Initial   │
│   State     │
└──────┬──────┘
       │
       │ python main.py --auth
       ▼
┌─────────────┐
│Authenticated│
└──────┬──────┘
       │
       │ python main.py --fetch
       ▼
┌─────────────┐
│Data Cached  │
└──────┬──────┘
       │
       │ python main.py --analyze
       ▼
┌─────────────┐
│  Analyzing  │
│             │
│ ┌─────────┐ │
│ │Location │ │
│ │Detection│ │
│ └────┬────┘ │
│      │      │
│      ▼      │
│ ┌─────────┐ │
│ │ Route   │ │
│ │Analysis │ │
│ └────┬────┘ │
│      │      │
│      ▼      │
│ ┌─────────┐ │
│ │Optimize │ │
│ └────┬────┘ │
│      │      │
│      ▼      │
│ ┌─────────┐ │
│ │Visualize│ │
│ └────┬────┘ │
└──────┼──────┘
       │
       ▼
┌─────────────┐
│   Report    │
│  Generated  │
└─────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Error Scenarios                       │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Auth Failure │  │ API Errors   │  │ Data Errors  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ - Retry auth │  │ - Use cache  │  │ - Validate   │
│ - Clear      │  │ - Backoff    │  │ - Skip bad   │
│   tokens     │  │ - Log error  │  │   records    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Graceful     │
                  │ Degradation  │
                  └──────────────┘
```

## Data Flow Example

### Example: Analyzing 50 Activities

```
Input: 50 Strava cycling activities
  │
  ├─ Filter by type (Ride, EBikeRide)
  │  → 45 activities remain
  │
  ├─ Filter by distance (2-30 km)
  │  → 30 activities remain
  │
  ├─ Extract endpoints
  │  → 60 coordinate pairs (start + end)
  │
  ├─ DBSCAN clustering
  │  → 3 clusters found
  │    - Cluster 1: 25 points (Home)
  │    - Cluster 2: 22 points (Work)
  │    - Cluster 3: 8 points (Other)
  │
  ├─ Filter commute activities
  │  → 20 activities between Home and Work
  │    - 10 Home → Work
  │    - 10 Work → Home
  │
  ├─ Group similar routes
  │  → Home → Work: 3 route variants
  │    - Route A: 6 activities (60%)
  │    - Route B: 3 activities (30%)
  │    - Route C: 1 activity (10%)
  │  → Work → Home: 2 route variants
  │    - Route D: 7 activities (70%)
  │    - Route E: 3 activities (30%)
  │
  ├─ Calculate metrics
  │  → Route A: 8.5 km, 22 min avg, 23.1 km/h
  │  → Route B: 9.2 km, 24 min avg, 23.0 km/h
  │  → Route C: 7.8 km, 25 min avg, 18.7 km/h
  │  → Route D: 8.3 km, 21 min avg, 23.7 km/h
  │  → Route E: 9.5 km, 23 min avg, 24.8 km/h
  │
  ├─ Score routes
  │  → Route A: 87.5 (time: 88, dist: 90, safety: 85)
  │  → Route B: 82.3 (time: 85, dist: 82, safety: 80)
  │  → Route C: 75.1 (time: 70, dist: 95, safety: 65)
  │  → Route D: 91.2 (time: 92, dist: 92, safety: 90) ← OPTIMAL
  │  → Route E: 85.7 (time: 87, dist: 80, safety: 90)
  │
  └─ Generate report
     → Recommendation: Use Route D (Work → Home)
     → Alternative: Route A (Home → Work)
     → Potential savings: 2 min/day vs Route B
```

## Performance Metrics

```
┌─────────────────────────────────────────────────────────┐
│              Expected Performance                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Authentication:           < 5 seconds                   │
│  Fetch 100 activities:     10-30 seconds                 │
│  Location clustering:      < 1 second                    │
│  Route similarity calc:    2-5 seconds                   │
│  Route grouping:           1-3 seconds                   │
│  Optimization:             < 1 second                    │
│  Map generation:           2-5 seconds                   │
│  Report generation:        1-2 seconds                   │
│                                                          │
│  Total (first run):        20-50 seconds                 │
│  Total (cached):           10-20 seconds                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Memory Usage

```
┌─────────────────────────────────────────────────────────┐
│              Memory Footprint                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  100 activities:           ~5 MB                         │
│  500 activities:           ~25 MB                        │
│  1000 activities:          ~50 MB                        │
│                                                          │
│  Peak usage (processing):  ~100 MB                       │
│  Cached data on disk:      ~10-50 MB                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## API Rate Limits

```
┌─────────────────────────────────────────────────────────┐
│           Strava API Rate Limits                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  15-minute limit:  100 requests                          │
│  Daily limit:      1000 requests                         │
│                                                          │
│  Typical usage:                                          │
│  - Initial fetch:  1-5 requests                          │
│  - With caching:   0-1 requests per run                  │
│                                                          │
│  Strategy:                                               │
│  - Cache aggressively                                    │
│  - Batch requests                                        │
│  - Respect rate limits                                   │
│                                                          │
└─────────────────────────────────────────────────────────┘