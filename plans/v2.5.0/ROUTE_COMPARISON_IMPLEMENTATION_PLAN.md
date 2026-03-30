# Route Comparison Feature Implementation Plan

**Issue:** #47 - Add Side-by-Side Route Comparison Feature  
**Priority:** P1-high  
**Estimated Effort:** 12-16 hours  
**Target Release:** v2.4.0

---

## Overview

Enable users to select and compare 2-3 routes side-by-side to make informed decisions about which route to take based on multiple factors (distance, duration, elevation, weather, traffic patterns, etc.).

## User Stories

1. **As a commuter**, I want to compare my usual route with alternative routes to see which is better for today's conditions
2. **As a cyclist**, I want to see visual differences between routes on a map with highlighted segments
3. **As a data-driven user**, I want to see detailed metrics comparison in a table format
4. **As a mobile user**, I want the comparison view to work well on small screens

## Requirements

### Functional Requirements

1. **Route Selection**
   - Allow selecting 2-3 routes from the route list
   - Checkbox or button-based selection UI
   - Clear visual indication of selected routes
   - "Compare" button appears when 2+ routes selected

2. **Comparison View**
   - Side-by-side layout for desktop (responsive for mobile)
   - Each route displayed in its own column
   - Synchronized scrolling for metric sections
   - Clear route identification (name, color-coding)

3. **Metrics to Compare**
   - **Basic Metrics:**
     - Distance (with difference %)
     - Duration (with difference %)
     - Average speed
     - Elevation gain/loss
     - Number of uses
   - **Advanced Metrics:**
     - Weather favorability score
     - Wind impact analysis
     - Traffic pattern score
     - Carbon savings
     - Calories burned
   - **Route Characteristics:**
     - Direction (to work / to home)
     - Is Plus route
     - Route type (direct, scenic, etc.)

4. **Visual Comparison**
   - Map showing all selected routes simultaneously
   - Different colors for each route
   - Ability to toggle routes on/off
   - Highlight differences (diverging segments)
   - Show common segments in neutral color

5. **Decision Support**
   - "Winner" badge for best route based on selected criteria
   - Recommendation engine considering:
     - Current weather conditions
     - Time of day (traffic patterns)
     - User preferences
   - Pros/cons list for each route

### Non-Functional Requirements

1. **Performance**
   - Comparison view loads in <1 second
   - Map rendering smooth with 3 routes
   - No lag when toggling routes

2. **Usability**
   - Intuitive selection mechanism
   - Clear visual hierarchy
   - Easy to understand metrics
   - Mobile-friendly layout

3. **Accessibility**
   - Keyboard navigation for route selection
   - Screen reader support for comparison table
   - High contrast colors for route differentiation
   - ARIA labels for all interactive elements

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Report Template                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Route List (Commute Routes Tab)                       │ │
│  │  - Checkbox for each route                             │ │
│  │  - "Compare Selected" button (appears when 2+ selected)│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Comparison Modal/Section                              │ │
│  │  ┌──────────┬──────────┬──────────┐                   │ │
│  │  │ Route 1  │ Route 2  │ Route 3  │                   │ │
│  │  ├──────────┼──────────┼──────────┤                   │ │
│  │  │ Metrics  │ Metrics  │ Metrics  │                   │ │
│  │  │ Map      │ Map      │ Map      │                   │ │
│  │  │ Analysis │ Analysis │ Analysis │                   │ │
│  │  └──────────┴──────────┴──────────┘                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Structures

```python
# In report_template.html JavaScript
const comparisonState = {
    selectedRoutes: [],  // Array of route IDs
    maxRoutes: 3,
    comparisonData: {},  // Cached comparison data
    activeView: 'table' | 'map' | 'analysis'
};

const routeComparison = {
    routes: [
        {
            id: 'route_123',
            name: 'Main Street Route',
            metrics: {
                distance: 5.2,
                duration: 18.5,
                elevation: 45,
                // ... more metrics
            },
            scores: {
                weather: 0.85,
                traffic: 0.72,
                overall: 0.78
            },
            pros: ['Shortest distance', 'Good bike lanes'],
            cons: ['Busy intersection at Main & 5th']
        },
        // ... more routes
    ],
    recommendation: {
        winnerId: 'route_123',
        reason: 'Best overall score considering weather and traffic'
    }
};
```

### Components

#### 1. Route Selection UI (HTML/CSS/JS)

**Location:** `templates/report_template.html`

```html
<!-- Add to each route row -->
<td class="route-select-cell">
    <input type="checkbox" 
           class="route-compare-checkbox" 
           data-route-id="{{ route.id }}"
           aria-label="Select {{ route.name }} for comparison">
</td>

<!-- Floating compare button -->
<div id="compareButton" class="compare-fab" style="display: none;">
    <button class="btn btn-primary" onclick="showComparison()">
        <i class="bi bi-bar-chart-line"></i>
        Compare <span id="compareCount">0</span> Routes
    </button>
</div>
```

#### 2. Comparison Modal

```html
<div id="comparisonModal" class="modal fade" tabindex="-1">
    <div class="modal-dialog modal-xl modal-fullscreen-lg-down">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Route Comparison</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <!-- Tab navigation -->
                <ul class="nav nav-tabs" role="tablist">
                    <li class="nav-item">
                        <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#comparisonTable">
                            Metrics
                        </button>
                    </li>
                    <li class="nav-item">
                        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#comparisonMap">
                            Map View
                        </button>
                    </li>
                    <li class="nav-item">
                        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#comparisonAnalysis">
                            Analysis
                        </button>
                    </li>
                </ul>
                
                <!-- Tab content -->
                <div class="tab-content">
                    <div class="tab-pane fade show active" id="comparisonTable">
                        <!-- Metrics comparison table -->
                    </div>
                    <div class="tab-pane fade" id="comparisonMap">
                        <!-- Leaflet map with all routes -->
                    </div>
                    <div class="tab-pane fade" id="comparisonAnalysis">
                        <!-- Recommendation and analysis -->
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

#### 3. JavaScript Functions

```javascript
// Route selection management
function toggleRouteSelection(routeId) {
    const index = comparisonState.selectedRoutes.indexOf(routeId);
    if (index > -1) {
        comparisonState.selectedRoutes.splice(index, 1);
    } else if (comparisonState.selectedRoutes.length < comparisonState.maxRoutes) {
        comparisonState.selectedRoutes.push(routeId);
    } else {
        showError(`Maximum ${comparisonState.maxRoutes} routes can be compared`);
        return false;
    }
    updateCompareButton();
    return true;
}

// Show/hide compare button
function updateCompareButton() {
    const count = comparisonState.selectedRoutes.length;
    const button = document.getElementById('compareButton');
    const countSpan = document.getElementById('compareCount');
    
    if (count >= 2) {
        button.style.display = 'block';
        countSpan.textContent = count;
    } else {
        button.style.display = 'none';
    }
}

// Load comparison data
function showComparison() {
    if (comparisonState.selectedRoutes.length < 2) {
        showError('Please select at least 2 routes to compare');
        return;
    }
    
    // Gather route data
    const routes = comparisonState.selectedRoutes.map(id => getRouteData(id));
    
    // Build comparison
    buildComparisonTable(routes);
    buildComparisonMap(routes);
    buildComparisonAnalysis(routes);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('comparisonModal'));
    modal.show();
}

// Build comparison table
function buildComparisonTable(routes) {
    const metrics = [
        { key: 'distance', label: 'Distance', format: formatDistance },
        { key: 'duration', label: 'Duration', format: formatDuration },
        { key: 'elevation', label: 'Elevation Gain', format: formatElevation },
        { key: 'avgSpeed', label: 'Avg Speed', format: formatSpeed },
        { key: 'uses', label: 'Times Used', format: (v) => v },
        // ... more metrics
    ];
    
    let html = '<table class="table table-striped comparison-table">';
    html += '<thead><tr><th>Metric</th>';
    routes.forEach(route => {
        html += `<th>${route.name}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    metrics.forEach(metric => {
        html += `<tr><td><strong>${metric.label}</strong></td>`;
        const values = routes.map(r => r[metric.key]);
        const best = findBestValue(metric.key, values);
        
        routes.forEach((route, idx) => {
            const value = route[metric.key];
            const formatted = metric.format(value);
            const isBest = value === best;
            const className = isBest ? 'best-value' : '';
            html += `<td class="${className}">${formatted}${isBest ? ' 🏆' : ''}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    document.getElementById('comparisonTable').innerHTML = html;
}

// Build comparison map
function buildComparisonMap(routes) {
    const mapContainer = document.getElementById('comparisonMap');
    mapContainer.innerHTML = '<div id="comparisonMapLeaflet" style="height: 500px;"></div>';
    
    const map = L.map('comparisonMapLeaflet');
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    
    const colors = ['#2E7D32', '#1976D2', '#D32F2F'];  // Green, Blue, Red
    const allBounds = [];
    
    routes.forEach((route, idx) => {
        const color = colors[idx % colors.length];
        const polyline = L.polyline(route.coordinates, {
            color: color,
            weight: 4,
            opacity: 0.7
        }).addTo(map);
        
        polyline.bindPopup(`<strong>${route.name}</strong><br>${formatDistance(route.distance)}`);
        allBounds.push(...route.coordinates);
    });
    
    // Fit map to show all routes
    if (allBounds.length > 0) {
        map.fitBounds(allBounds);
    }
}

// Build analysis and recommendation
function buildComparisonAnalysis(routes) {
    // Calculate scores
    const scored = routes.map(route => ({
        ...route,
        score: calculateOverallScore(route)
    }));
    
    // Find winner
    scored.sort((a, b) => b.score - a.score);
    const winner = scored[0];
    
    let html = `
        <div class="recommendation-card">
            <h4>🏆 Recommended Route</h4>
            <h5>${winner.name}</h5>
            <p class="lead">Overall Score: ${(winner.score * 100).toFixed(0)}%</p>
            <p>${generateRecommendationReason(winner, scored)}</p>
        </div>
        
        <div class="row mt-4">
    `;
    
    scored.forEach(route => {
        html += `
            <div class="col-md-${12 / scored.length}">
                <div class="card">
                    <div class="card-header">
                        <h6>${route.name}</h6>
                    </div>
                    <div class="card-body">
                        <h6>Pros:</h6>
                        <ul>${route.pros.map(p => `<li>${p}</li>`).join('')}</ul>
                        <h6>Cons:</h6>
                        <ul>${route.cons.map(c => `<li>${c}</li>`).join('')}</ul>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    document.getElementById('comparisonAnalysis').innerHTML = html;
}

// Helper functions
function calculateOverallScore(route) {
    // Weighted scoring algorithm
    const weights = {
        distance: 0.25,
        duration: 0.25,
        weather: 0.20,
        traffic: 0.15,
        elevation: 0.10,
        safety: 0.05
    };
    
    // Normalize and weight each factor
    let score = 0;
    Object.keys(weights).forEach(key => {
        score += normalizeMetric(key, route[key]) * weights[key];
    });
    
    return score;
}

function generateRecommendationReason(winner, allRoutes) {
    const reasons = [];
    
    if (winner.distance === Math.min(...allRoutes.map(r => r.distance))) {
        reasons.push('shortest distance');
    }
    if (winner.duration === Math.min(...allRoutes.map(r => r.duration))) {
        reasons.push('fastest time');
    }
    if (winner.weatherScore > 0.8) {
        reasons.push('best weather conditions');
    }
    
    return `This route is recommended because it has the ${reasons.join(', ')}.`;
}
```

---

## Implementation Phases

### Phase 1: Basic Selection UI (2-3 hours)
- Add checkboxes to route table
- Implement selection state management
- Add floating "Compare" button
- Handle max 3 routes limit

### Phase 2: Comparison Modal Structure (2-3 hours)
- Create modal HTML structure
- Add tab navigation (Metrics, Map, Analysis)
- Implement responsive layout
- Add close/cancel functionality

### Phase 3: Metrics Comparison (3-4 hours)
- Build comparison table with all metrics
- Implement "best value" highlighting
- Add percentage differences
- Format units properly (metric/imperial)
- Add tooltips for metric explanations

### Phase 4: Map Visualization (3-4 hours)
- Initialize Leaflet map in modal
- Render all selected routes with different colors
- Add route toggle controls
- Implement zoom to fit all routes
- Add popups with route details

### Phase 5: Analysis & Recommendation (2-3 hours)
- Implement scoring algorithm
- Generate pros/cons for each route
- Display recommendation with reasoning
- Add decision support UI

### Phase 6: Polish & Testing (2-3 hours)
- Mobile responsive design
- Accessibility improvements
- Error handling
- Performance optimization
- User testing and refinements

---

## Testing Strategy

### Unit Tests
- Selection state management
- Scoring algorithm
- Metric calculations
- Data formatting functions

### Integration Tests
- Full comparison workflow
- Modal interactions
- Map rendering
- Data accuracy

### Manual Testing
- Test with 2 routes
- Test with 3 routes
- Test on mobile devices
- Test with different route types
- Test accessibility with screen reader

---

## Success Criteria

1. ✅ Users can select 2-3 routes from the list
2. ✅ Comparison modal displays all metrics side-by-side
3. ✅ Map shows all routes with clear differentiation
4. ✅ Recommendation engine provides actionable advice
5. ✅ Works smoothly on mobile devices
6. ✅ Meets WCAG 2.1 AA accessibility standards
7. ✅ No performance degradation with 3 routes

---

## Future Enhancements (Post-v2.4.0)

1. **Export Comparison** - Save comparison as PDF or image
2. **Historical Comparison** - Compare current conditions vs historical averages
3. **Custom Weights** - Let users adjust scoring weights
4. **Share Comparison** - Generate shareable link
5. **Comparison Presets** - Save favorite comparisons
6. **More Routes** - Support comparing 4-5 routes
7. **Advanced Filters** - Filter routes before comparison

---

## Dependencies

- Bootstrap 5 (already included)
- Leaflet.js (already included)
- Existing route data structure
- Weather and traffic data (already available)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance with 3 routes on map | Medium | Optimize polyline rendering, use clustering |
| Mobile UX complexity | High | Simplify mobile layout, use accordion for metrics |
| Scoring algorithm accuracy | Medium | Gather user feedback, iterate on weights |
| Data availability | Low | Gracefully handle missing metrics |

---

*Created: 2026-03-30*  
*Status: Ready for implementation*  
*Estimated Completion: 12-16 hours*