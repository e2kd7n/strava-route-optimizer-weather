# GitHub Issues for Strava Commute Route Analyzer

This document contains GitHub issues for outstanding tasks and improvements.

---

## Issue #15: Implement Unit System Toggle (Metric/Imperial)

**Labels:** `enhancement`, `feature`, `priority: P1`

**Title:** Add user preference for metric vs imperial units with consistent usage

**Description:**

Allow users to toggle between metric (km, km/h, meters) and imperial (miles, mph, feet) units throughout the application. Ensure consistency - never mix unit systems in the same report.

### Current Problem:

- Application uses metric units by default
- No option to switch to imperial units
- Users in US/UK may prefer miles and mph
- Inconsistent unit usage in some places

### Requirements:

1. **Configuration Option**
   ```yaml
   units:
     system: metric  # or 'imperial'
     distance: km    # or 'miles'
     speed: kmh      # or 'mph'
     elevation: m    # or 'ft'
   ```

2. **Consistent Conversion Throughout**
   - Distance: km ↔ miles (1 km = 0.621371 miles)
   - Speed: km/h ↔ mph (1 km/h = 0.621371 mph)
   - Elevation: meters ↔ feet (1 m = 3.28084 ft)
   - Temperature: Celsius ↔ Fahrenheit (if weather shown)

3. **Update All Display Locations**
   - Route comparison table
   - Map popups
   - Executive summary
   - Recommendations
   - Long ride analysis
   - Weather information

### Implementation:

```python
class UnitConverter:
    """Handle unit conversions between metric and imperial."""
    
    def __init__(self, system: str = 'metric'):
        self.system = system
        
    def distance(self, meters: float) -> tuple[float, str]:
        """Convert distance to preferred units."""
        if self.system == 'imperial':
            miles = meters / 1609.344
            return miles, 'mi'
        else:
            km = meters / 1000
            return km, 'km'
    
    def speed(self, meters_per_sec: float) -> tuple[float, str]:
        """Convert speed to preferred units."""
        if self.system == 'imperial':
            mph = meters_per_sec * 2.23694
            return mph, 'mph'
        else:
            kmh = meters_per_sec * 3.6
            return kmh, 'km/h'
    
    def elevation(self, meters: float) -> tuple[float, str]:
        """Convert elevation to preferred units."""
        if self.system == 'imperial':
            feet = meters * 3.28084
            return feet, 'ft'
        else:
            return meters, 'm'
    
    def format_distance(self, meters: float) -> str:
        """Format distance with appropriate units."""
        value, unit = self.distance(meters)
        return f"{value:.1f} {unit}"
```

### Validation Rules:

- **Never mix units** in the same report
- All conversions must be accurate
- Unit labels must be clear and consistent
- Rounding should be appropriate for each unit

### Acceptance Criteria:

- [ ] Configuration option for unit system
- [ ] UnitConverter class implemented
- [ ] All distance values converted consistently
- [ ] All speed values converted consistently
- [ ] All elevation values converted consistently
- [ ] No mixed units in any report
- [ ] Unit labels displayed correctly
- [ ] Documentation updated with examples

---

## Issue #16: Add Optimal Route Map Preview

**Labels:** `enhancement`, `ui/ux`, `priority: P1`

**Title:** Show map trace of recommended optimal route at top of page

**Description:**

Add a prominent map visualization of the optimal route at the top of the report page, before the detailed comparison table, so users can immediately see the recommended route.

### Current Problem:

- Optimal route is only shown in the main map with all other routes
- Users have to scroll and search to find the recommended route
- No quick visual preview of the optimal route

### Proposed Solution:

1. **Add Optimal Route Preview Section**
   - Place immediately after executive summary
   - Show only the optimal route (no other routes)
   - Larger, more prominent display
   - Include home/work markers

2. **Make It Interactive**
   - Click to zoom to full map
   - Show route statistics on hover
   - Link to detailed metrics below

3. **Visual Design**
   ```html
   <div class="optimal-route-preview">
       <h3>🏆 Recommended Optimal Route</h3>
       <div class="row">
           <div class="col-md-8">
               <div id="optimal-route-map" style="height: 400px;"></div>
           </div>
           <div class="col-md-4">
               <div class="route-stats">
                   <h5>Route Statistics</h5>
                   <p><strong>Distance:</strong> 12.5 km</p>
                   <p><strong>Duration:</strong> 35 min</p>
                   <p><strong>Score:</strong> 85.2</p>
                   <button onclick="scrollToFullMap()">
                       View on Full Map ↓
                   </button>
               </div>
           </div>
       </div>
   </div>
   ```

### Implementation:

```python
def create_optimal_route_preview_map(self, optimal_route: RouteGroup) -> str:
    """Create a focused map showing only the optimal route."""
    # Create smaller map centered on route
    preview_map = folium.Map(
        location=self._get_route_center(optimal_route),
        zoom_start=13,
        tiles='CartoDB Positron',
        height='400px'
    )
    
    # Add only the optimal route
    self.add_route_layer(
        optimal_route,
        color='#dc3545',  # Red for optimal
        weight=5,
        is_optimal=True
    )
    
    # Add home/work markers
    self.add_location_markers(preview_map)
    
    return preview_map._repr_html_()
```

### Acceptance Criteria:

- [ ] Preview map shows only optimal route
- [ ] Positioned at top of page after summary
- [ ] Clickable to scroll to full map
- [ ] Shows key statistics alongside map
- [ ] Mobile responsive
- [ ] Loads quickly

---

## Issue #17: Significantly Improve Route Naming

**Labels:** `enhancement`, `feature`, `priority: P1`

**Title:** Overhaul route naming to clearly indicate actual route paths

**Description:**

Current route names are generic and unhelpful (e.g., "Route 1 to Work"). Implement intelligent route naming that clearly indicates where the route actually goes using street names, landmarks, or geographic features.

### Current Problems:

- Names like "home_to_work_0" are meaningless
- No indication of actual route path
- Difficult to distinguish between similar routes
- Geocoding not fully implemented

### Proposed Solutions:

1. **Multi-Strategy Naming Approach**
   
   **Strategy 1: Major Street Names**
   - Sample 3-5 key points along route
   - Get street names via reverse geocoding
   - Prioritize major streets (arterials, highways)
   - Format: "Via Michigan Ave → Lake Shore Dr"
   
   **Strategy 2: Neighborhood/District Names**
   - Identify neighborhoods route passes through
   - Format: "Loop → Lincoln Park Route"
   
   **Strategy 3: Landmark-Based**
   - Identify major landmarks near route
   - Format: "Navy Pier → Millennium Park Route"
   
   **Strategy 4: Geographic Features**
   - Rivers, parks, lakefront paths
   - Format: "Lakefront Path Route"

2. **Intelligent Selection Algorithm**
   ```python
   def generate_route_name(self, route: Route) -> str:
       """Generate descriptive route name using multiple strategies."""
       
       # Sample strategic points (start, 1/3, 2/3, end)
       sample_points = self._get_strategic_points(route.coordinates)
       
       # Try strategies in order of preference
       strategies = [
           self._name_by_major_streets,
           self._name_by_neighborhoods,
           self._name_by_landmarks,
           self._name_by_geographic_features
       ]
       
       for strategy in strategies:
           name = strategy(sample_points)
           if name and self._is_descriptive(name):
               return name
       
       # Fallback to simple naming
       return self._simple_name(route)
   
   def _name_by_major_streets(self, points: List[Tuple]) -> str:
       """Name route by major streets it uses."""
       streets = []
       for lat, lon in points:
           street = self._get_street_name(lat, lon)
           if street and self._is_major_street(street):
               if street not in streets:
                   streets.append(street)
       
       if len(streets) >= 2:
           return f"Via {' → '.join(streets[:3])}"
       return None
   
   def _is_major_street(self, street: str) -> bool:
       """Determine if street is a major arterial."""
       major_indicators = [
           'Avenue', 'Boulevard', 'Parkway', 'Highway',
           'Drive', 'Expressway', 'Road'
       ]
       return any(ind in street for ind in major_indicators)
   ```

3. **Caching Strategy**
   - Cache geocoding results by coordinate
   - Cache street classifications
   - Persist cache between runs
   - Respect rate limits (1 request/second)

4. **Differentiation for Similar Routes**
   - If two routes have similar names, add distinguishing features
   - Example: "Via Michigan Ave (North)" vs "Via Michigan Ave (South)"
   - Use distance, duration, or unique street as differentiator

### Example Outputs:

**Good Names:**
- "Via Michigan Ave → Lake Shore Dr"
- "Lakefront Path Route"
- "Clark St → Division St → Halsted"
- "Loop → Lincoln Park via LaSalle"
- "River North → Gold Coast Route"

**Bad Names (Current):**
- "home_to_work_0"
- "Route 1 to Work"
- "Primary Route"

### Acceptance Criteria:

- [ ] Route names clearly indicate path
- [ ] Major streets identified and used
- [ ] Geocoding fully implemented with caching
- [ ] Rate limiting respected
- [ ] Similar routes have distinguishing names
- [ ] Fallback naming for geocoding failures
- [ ] Names are concise (< 50 characters)
- [ ] Documentation with examples

---

## Issue #18: Remove Test Routes from Production

**Labels:** `cleanup`, `priority: P1`

**Title:** Remove hardcoded test routes (Four States Ferry, Unbound 200)

**Description:**

Remove the hardcoded test routes "Four States and a Ferry" and "Unbound 200" from the production code. These were useful for testing zoom functionality but should not be in production.

### Current Problem:

- Test routes hardcoded in `src/visualizer.py` (lines 584-593)
- Add unnecessary data to every report
- Confuse users who see test routes in their reports
- Increase file size and memory usage

### Location:

File: `src/visualizer.py`
Method: `_add_route_interaction_javascript()`
Lines: 584-593

```python
# Real Strava test routes for zoom testing
route_data['route-test_ferry'] = {
    'bounds': [[41.98637, -87.66266], ...],
    'name': 'TEST: Four States Ferry (267km)',
    'direction': 'test'
}
route_data['route-test_unbound'] = {
    'bounds': [[38.41551, -96.17802], ...],
    'name': 'TEST: Unbound 200 (327km)',
    'direction': 'test'
}
```

### Solution:

1. **Remove Test Routes**
   - Delete lines 584-593 in `src/visualizer.py`
   - Remove test route data from JavaScript

2. **Add Development Mode (Optional)**
   ```python
   if config.get('development.enable_test_routes', False):
       # Add test routes only in dev mode
       route_data['route-test_ferry'] = {...}
   ```

3. **Update Tests**
   - If tests depend on these routes, update them
   - Use proper test fixtures instead

### Acceptance Criteria:

- [ ] Test routes removed from production code
- [ ] No test routes appear in generated reports
- [ ] All tests still pass
- [ ] Optional: Dev mode flag for test routes
- [ ] Code is cleaner and more maintainable

---

## Issue #19: Code Cleanup and Performance Optimization

**Labels:** `cleanup`, `performance`, `priority: P1`

**Title:** Remove dead code and optimize for performance

**Description:**

Perform comprehensive code cleanup to remove dead code, unused imports, abandoned routes, and optimize performance to minimize compute and memory load.

### Audit Areas:

1. **Dead Code Detection**
   - Unused functions and methods
   - Unreachable code paths
   - Commented-out code blocks
   - Unused imports

2. **Abandoned Routes**
   - Deprecated API endpoints
   - Old authentication methods
   - Legacy data structures
   - Unused configuration options

3. **Performance Optimization**
   - Inefficient loops
   - Redundant calculations
   - Memory leaks
   - Unnecessary data copies

### Tools to Use:

```bash
# Find unused code
pip install vulture
vulture src/ --min-confidence 80

# Find unused imports
pip install autoflake
autoflake --remove-all-unused-imports --recursive src/

# Profile performance
python -m cProfile -o profile.stats main.py --analyze
python -m pstats profile.stats

# Memory profiling
pip install memory_profiler
python -m memory_profiler main.py --analyze
```

### Specific Areas to Check:

1. **src/auth.py vs src/auth_secure.py**
   - Determine which is active
   - Remove deprecated version
   - Consolidate authentication logic

2. **Route Analyzer**
   - Check for redundant similarity calculations
   - Optimize coordinate sampling
   - Cache expensive operations

3. **Data Fetcher**
   - Remove unused activity fields
   - Optimize cache loading
   - Reduce memory footprint

4. **Report Generator**
   - Minimize template size
   - Remove unused JavaScript
   - Optimize CSS

5. **Visualizer**
   - Reduce map complexity
   - Optimize polyline rendering
   - Remove unused map layers

### Performance Targets:

- **Startup time:** < 2 seconds
- **Analysis time:** < 30 seconds for 200 activities
- **Memory usage:** < 500 MB peak
- **Report generation:** < 5 seconds
- **Report file size:** < 2 MB

### Implementation Checklist:

- [ ] Run vulture to find dead code
- [ ] Remove unused imports with autoflake
- [ ] Profile CPU usage and optimize hotspots
- [ ] Profile memory usage and fix leaks
- [ ] Remove deprecated auth module
- [ ] Optimize route similarity calculations
- [ ] Reduce cache file sizes
- [ ] Minimize report template
- [ ] Remove test routes (Issue #18)
- [ ] Document performance improvements

### Acceptance Criteria:

- [ ] No dead code remaining
- [ ] All imports are used
- [ ] Performance targets met
- [ ] Memory usage optimized
- [ ] Code coverage > 80%
- [ ] All tests pass
- [ ] Documentation updated

---

## Issue #10: Extract HTML Template to External File

**Labels:** `enhancement`, `refactoring`, `priority: P1`

**Title:** Extract inline HTML template from report_generator.py to external file

**Description:**

The `report_generator.py` file contains a 1,720-line inline HTML template (lines 239-1720) that should be extracted to an external template file for better maintainability and separation of concerns.

### Current Problem:

- HTML template is embedded as a Python string in `_get_inline_template()` method
- Makes the Python file extremely large and hard to maintain
- Mixing presentation logic with business logic
- Difficult to edit HTML without Python syntax errors
- No syntax highlighting for HTML in Python strings

### Proposed Solution:

1. **Create External Template**
   - Move HTML to `templates/report.html`
   - Use Jinja2 template engine (already imported)
   - Keep template variables and logic

2. **Update report_generator.py**
   ```python
   def _render_template(self, context: Dict[str, Any]) -> str:
       """Render template from external file."""
       template_path = self.template_dir / 'report.html'
       
       if not template_path.exists():
           # Fallback to inline template for backward compatibility
           return self._get_inline_template()
       
       with open(template_path, 'r', encoding='utf-8') as f:
           template_str = f.read()
       
       template = Template(template_str)
       return template.render(**context)
   ```

3. **Benefits**
   - Cleaner Python code
   - Easier HTML editing with proper syntax highlighting
   - Better separation of concerns
   - Easier to customize reports
   - Reduced file size for report_generator.py

### Implementation Steps:

1. Create `templates/report.html` with current inline template content
2. Update `_render_template()` to load from file
3. Keep `_get_inline_template()` as fallback for backward compatibility
4. Test report generation with external template
5. Update documentation

### Acceptance Criteria:

- [ ] HTML template extracted to `templates/report.html`
- [ ] Report generation works with external template
- [ ] Fallback to inline template if file not found
- [ ] All template variables render correctly
- [ ] JavaScript and CSS work as before
- [ ] Documentation updated

---

## Issue #11: Add QR Code Generation for Mobile Transfer

**Labels:** `enhancement`, `feature`, `mobile`, `priority: P1`

**Title:** Generate QR code for easy mobile transfer of reports

**Description:**

Add QR code generation to enable instant transfer of HTML reports to mobile devices without manual file transfer methods.

### Use Case:

User generates report on desktop → Scan QR code with phone → Report opens on mobile device instantly

### Implementation:

1. **Add QR Code Library**
   ```bash
   pip install qrcode[pil]
   ```

2. **Generate QR Code in Report**
   ```python
   import qrcode
   from pathlib import Path
   
   def generate_qr_code(report_path: Path) -> str:
       """Generate QR code for report access."""
       # Get local network IP
       import socket
       hostname = socket.gethostname()
       local_ip = socket.gethostbyname(hostname)
       
       # Create local URL
       port = 8000
       url = f"http://{local_ip}:{port}/{report_path.name}"
       
       # Generate QR code
       qr = qrcode.QRCode(version=1, box_size=10, border=5)
       qr.add_data(url)
       qr.make(fit=True)
       
       # Save as image
       img = qr.make_image(fill_color="black", back_color="white")
       qr_path = report_path.parent / f"{report_path.stem}_qr.png"
       img.save(qr_path)
       
       return str(qr_path)
   ```

3. **Add Simple HTTP Server**
   ```python
   def serve_report(report_path: Path, port: int = 8000):
       """Serve report on local network."""
       import http.server
       import socketserver
       
       os.chdir(report_path.parent)
       handler = http.server.SimpleHTTPRequestHandler
       
       with socketserver.TCPServer(("", port), handler) as httpd:
           print(f"Serving at http://localhost:{port}")
           print(f"Scan QR code to open on mobile")
           httpd.serve_forever()
   ```

4. **Update main.py**
   ```python
   parser.add_argument('--serve', action='store_true',
                      help='Serve report on local network with QR code')
   
   if args.serve:
       qr_path = generate_qr_code(report_path)
       print(f"QR Code saved to: {qr_path}")
       serve_report(report_path)
   ```

### Features:

- Generate QR code pointing to local network URL
- Start simple HTTP server to serve report
- Display QR code in terminal (optional: using qrcode-terminal)
- Save QR code as PNG for sharing
- Auto-detect local IP address

### Acceptance Criteria:

- [ ] QR code generation implemented
- [ ] Simple HTTP server for local network access
- [ ] QR code displays in terminal
- [ ] QR code saved as PNG file
- [ ] Works on local network (WiFi)
- [ ] Documentation includes usage instructions
- [ ] Command line flag `--serve` added

---

## Issue #12: Add PDF Export Option

**Labels:** `enhancement`, `feature`, `export`, `priority: P1`

**Title:** Implement PDF export for printable reports

**Description:**

Add ability to export reports as PDF for printing, archiving, or sharing with non-technical users.

### Implementation:

1. **Add PDF Library**
   ```bash
   pip install weasyprint
   # or
   pip install pdfkit  # requires wkhtmltopdf
   ```

2. **Create PDF Export Function**
   ```python
   from weasyprint import HTML, CSS
   
   def export_to_pdf(html_path: Path, pdf_path: Path = None):
       """Export HTML report to PDF."""
       if pdf_path is None:
           pdf_path = html_path.with_suffix('.pdf')
       
       # Custom CSS for print
       print_css = CSS(string='''
           @page {
               size: A4;
               margin: 2cm;
           }
           .no-print {
               display: none;
           }
           .map-container {
               page-break-inside: avoid;
           }
       ''')
       
       # Generate PDF
       HTML(filename=str(html_path)).write_pdf(
           pdf_path,
           stylesheets=[print_css]
       )
       
       return pdf_path
   ```

3. **Update main.py**
   ```python
   parser.add_argument('--export-pdf', action='store_true',
                      help='Export report as PDF')
   
   if args.export_pdf:
       pdf_path = export_to_pdf(report_path)
       print(f"PDF exported to: {pdf_path}")
   ```

4. **Optimize HTML for PDF**
   - Add print-specific CSS
   - Hide interactive elements in print
   - Ensure maps render as static images
   - Add page breaks appropriately
   - Include table of contents

### Features:

- Export HTML report to PDF
- Print-optimized layout
- Static map images (not interactive)
- Table of contents
- Page numbers
- Professional formatting

### Acceptance Criteria:

- [ ] PDF export implemented
- [ ] Maps render as static images in PDF
- [ ] Layout optimized for printing
- [ ] All data visible in PDF
- [ ] Command line flag `--export-pdf` added
- [ ] Documentation updated
- [ ] PDF quality is high (300 DPI)

---

## Issue #13: Add Route Comparison Feature

**Labels:** `enhancement`, `feature`, `ui/ux`, `priority: P1`

**Title:** Implement side-by-side route comparison in JavaScript

**Description:**

Add interactive feature to compare two or more routes side-by-side with detailed metrics comparison.

### Features:

1. **Route Selection**
   - Checkboxes to select routes for comparison
   - Support 2-4 routes at once
   - "Compare Selected" button

2. **Comparison View**
   - Side-by-side metrics table
   - Highlight differences (better/worse)
   - Visual indicators (arrows, colors)
   - Percentage differences

3. **Map Comparison**
   - Show selected routes on map simultaneously
   - Different colors for each route
   - Toggle individual routes on/off
   - Zoom to fit all selected routes

### Implementation:

```javascript
function compareRoutes(routeIds) {
    const comparisonData = routeIds.map(id => {
        const route = routeData[id];
        return {
            id: id,
            name: route.name,
            distance: route.distance,
            duration: route.duration,
            elevation: route.elevation,
            speed: route.speed,
            score: route.score
        };
    });
    
    // Create comparison table
    const html = `
        <div class="comparison-modal">
            <h3>Route Comparison</h3>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Metric</th>
                        ${comparisonData.map(r => `<th>${r.name}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Distance</td>
                        ${comparisonData.map(r => `<td>${r.distance} km</td>`).join('')}
                    </tr>
                    <!-- More metrics -->
                </tbody>
            </table>
        </div>
    `;
    
    // Display modal
    showModal(html);
}
```

### UI Elements:

- Comparison button in toolbar
- Modal dialog for comparison view
- Checkboxes on each route row
- "Select All" / "Clear All" buttons
- Export comparison as CSV

### Acceptance Criteria:

- [ ] Route selection with checkboxes
- [ ] Comparison modal displays correctly
- [ ] All metrics compared side-by-side
- [ ] Visual indicators for differences
- [ ] Map shows selected routes
- [ ] Export comparison data
- [ ] Mobile responsive

---

## Issue #14: Implement Data Export Formats

**Labels:** `enhancement`, `feature`, `export`, `priority: P1`

**Title:** Add multiple export formats (JSON, GPX, CSV)

**Description:**

Enable users to export their route data in various formats for use in other applications, GPS devices, or data analysis tools.

### Export Formats:

1. **JSON Export**
   - Complete route data with all metrics
   - Structured format for programmatic access
   - Include coordinates, timestamps, metadata

2. **GPX Export**
   - GPS Exchange Format for GPS devices
   - Compatible with Garmin, Wahoo, etc.
   - Include waypoints, tracks, routes

3. **CSV Export**
   - Tabular data for spreadsheet analysis
   - Route summary metrics
   - Activity-level data

### Implementation:

```python
class DataExporter:
    """Export route data in various formats."""
    
    def export_json(self, route_groups: List[RouteGroup], output_path: Path):
        """Export complete route data as JSON."""
        data = {
            'generated_at': datetime.now().isoformat(),
            'routes': [
                {
                    'id': group.id,
                    'direction': group.direction,
                    'frequency': group.frequency,
                    'avg_distance_km': group.avg_distance / 1000,
                    'avg_duration_min': group.avg_duration / 60,
                    'coordinates': group.representative_route.coordinates,
                    'activities': [
                        {
                            'id': route.activity_id,
                            'timestamp': route.timestamp.isoformat(),
                            'distance': route.distance,
                            'duration': route.duration
                        }
                        for route in group.routes
                    ]
                }
                for group in route_groups
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_gpx(self, route_group: RouteGroup, output_path: Path):
        """Export route as GPX file."""
        gpx = gpxpy.gpx.GPX()
        
        # Create track
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx_track.name = route_group.id
        gpx.tracks.append(gpx_track)
        
        # Create segment
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        
        # Add points
        for lat, lon in route_group.representative_route.coordinates:
            gpx_segment.points.append(
                gpxpy.gpx.GPXTrackPoint(lat, lon)
            )
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(gpx.to_xml())
    
    def export_csv(self, route_groups: List[RouteGroup], output_path: Path):
        """Export route summary as CSV."""
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Route ID', 'Direction', 'Frequency', 
                'Avg Distance (km)', 'Avg Duration (min)',
                'Avg Speed (km/h)', 'Elevation Gain (m)'
            ])
            
            for group in route_groups:
                writer.writerow([
                    group.id,
                    group.direction,
                    group.frequency,
                    f"{group.avg_distance / 1000:.2f}",
                    f"{group.avg_duration / 60:.1f}",
                    f"{group.avg_speed * 3.6:.1f}",
                    f"{group.avg_elevation:.0f}"
                ])
```

### Command Line Interface:

```python
parser.add_argument('--export-json', type=str,
                   help='Export route data as JSON')
parser.add_argument('--export-gpx', type=str,
                   help='Export routes as GPX files')
parser.add_argument('--export-csv', type=str,
                   help='Export route summary as CSV')
```

### Acceptance Criteria:

- [ ] JSON export with complete data
- [ ] GPX export for GPS devices
- [ ] CSV export for spreadsheet analysis
- [ ] Command line flags for each format
- [ ] Export all routes or selected routes
- [ ] Proper file naming conventions
- [ ] Documentation with examples
- [ ] Validation of exported data

---

## Issue #6: ✅ RESOLVED - Fix Logger Reference Before Definition

**Labels:** `bug`, `priority: critical`, `resolved`

**Title:** Logger referenced before definition in route_analyzer.py

**Description:**

VSCode identified a critical bug where the `logger` variable was being referenced in an exception handler before it was defined, which would cause a `NameError` at runtime if the `similaritymeasures` package was not installed.

### Problem:

In `src/route_analyzer.py`, the code attempted to use `logger.warning()` in the `except ImportError` block (line 24) before `logger` was initialized (line 30):

```python
try:
    import similaritymeasures
    FRECHET_AVAILABLE = True
except ImportError:
    FRECHET_AVAILABLE = False
    logger.warning("...")  # ❌ NameError: logger not defined yet
    
logger = logging.getLogger(__name__)  # Defined here
```

### Solution:

Moved the logger initialization before the try-except block to ensure it's available when needed:

```python
logger = logging.getLogger(__name__)  # ✅ Define first

try:
    import similaritymeasures
    FRECHET_AVAILABLE = True
except ImportError:
    FRECHET_AVAILABLE = False
    logger.warning("...")  # ✅ Now works correctly
```

### Resolution:

- **Fixed in commit:** `7423f0d`
- **Files changed:** `src/route_analyzer.py`
- **Documentation:** `VSCODE_PROBLEMS_RESOLUTION.md`
- **Status:** ✅ RESOLVED

### Validation:

- ✅ All Python files pass syntax validation
- ✅ AST parsing successful for all modules
- ✅ No runtime errors when similaritymeasures is missing
- ✅ Logger properly initialized before use

**Closed:** 2026-03-13

---

## Issue #1: Test Interactive Route Highlighting Features

**Labels:** `testing`, `enhancement`, `priority: high`

**Title:** Test and validate interactive route highlighting in HTML report

**Description:**

The interactive route highlighting features have been implemented but need comprehensive testing to ensure they work correctly across different browsers and scenarios.

### Features to Test:

1. **Hover Highlighting**
   - Hover over route names in the comparison table
   - Verify route is highlighted on the map
   - Verify other routes are dimmed
   - Test that highlighting resets when mouse leaves

2. **Click to Persist**
   - Click on a route name to keep it highlighted
   - Verify route stays highlighted when mouse moves away
   - Click again to deselect
   - Verify routes return to normal state

3. **Map Interaction**
   - Verify map displays correctly in right pane
   - Test sticky positioning of map during scroll
   - Verify route colors match between table and map
   - Test popup information on route click

4. **Cross-browser Testing**
   - Chrome/Edge
   - Firefox
   - Safari
   - Mobile browsers

### Testing Steps:

1. Run the analyzer with real Strava data:
   ```bash
   cd commute
   python3 main.py --analyze
   ```

2. Open the generated report in `output/reports/commute_analysis.html`

3. Test each feature listed above

4. Document any issues found

### Acceptance Criteria:

- [ ] Hover highlighting works smoothly without lag
- [ ] Click to persist works correctly
- [ ] Routes can be selected and deselected
- [ ] Map displays correctly in right pane
- [ ] No JavaScript errors in browser console
- [ ] Works in major browsers (Chrome, Firefox, Safari)
- [ ] Mobile responsive design works

### Notes:

The JavaScript implementation uses direct DOM manipulation to highlight routes. If the Folium map structure changes, the selectors may need updating.

---

## Issue #2: Enhance Route Naming with Real Geocoding

**Labels:** `enhancement`, `feature`, `priority: medium`

**Title:** Implement full geocoding for route names based on streets

**Description:**

Currently, route names use simple naming (e.g., "Primary Route to Work"). The `RouteNamer` class has been created with geocoding support, but it needs to be fully integrated and tested.

### Current State:

- `RouteNamer` class exists in `src/route_namer.py`
- Has methods for reverse geocoding using Nominatim
- Currently using simple naming as fallback
- Geocoding is rate-limited and requires internet

### Tasks:

1. **Enable Geocoding by Default**
   - Add configuration option to enable/disable geocoding
   - Implement proper error handling for offline scenarios
   - Add caching for geocoded street names

2. **Improve Street Name Selection**
   - Sample more strategic points along routes
   - Prioritize major streets over minor ones
   - Handle cases where street names aren't available

3. **Add Configuration Options**
   ```yaml
   route_naming:
     enable_geocoding: true
     cache_geocoding: true
     max_retries: 3
     timeout_seconds: 5
     sample_points: 3
   ```

4. **Testing**
   - Test with various route types
   - Test offline behavior
   - Test rate limiting handling
   - Verify cache works correctly

### Example Output:

Instead of "Route 1 to Work", generate names like:
- "Via Michigan Ave → Lake Shore Dr"
- "Clark St → Division St Route"
- "Lakeshore Path Route"

### Acceptance Criteria:

- [ ] Geocoding can be enabled via config
- [ ] Street names are cached to avoid repeated API calls
- [ ] Graceful fallback to simple names when geocoding fails
- [ ] Rate limiting is handled properly
- [ ] Works offline with cached data
- [ ] Documentation updated with examples

---

## Issue #3: Improve Map-Table Synchronization

**Labels:** `enhancement`, `bug`, `priority: medium`

**Title:** Enhance JavaScript for better map-table interaction

**Description:**

The current JavaScript implementation for highlighting routes may not work perfectly with all Folium map configurations. Need to improve the synchronization between table interactions and map highlighting.

### Known Issues:

1. **Folium Map Access**
   - Current implementation tries to access map elements directly
   - May not work if Folium changes its HTML structure
   - Need more robust way to identify and highlight routes

2. **Route Identification**
   - Routes need unique identifiers that persist in both table and map
   - Current className approach may not be reliable

### Proposed Solutions:

1. **Add Data Attributes to Folium Routes**
   - Modify `visualizer.py` to add custom data attributes
   - Use these for reliable route identification
   - Example: `data-route-id="home_to_work_0"`

2. **Improve JavaScript Selectors**
   - Use more specific selectors
   - Add fallback methods for route identification
   - Better error handling

3. **Add Visual Feedback**
   - Show loading state while map initializes
   - Add tooltips explaining interaction
   - Highlight selected route in table with icon

### Implementation:

```python
# In visualizer.py, when creating polylines:
folium.PolyLine(
    coords,
    color=color,
    weight=weight,
    opacity=opacity,
    popup=popup_html,
    tooltip=route_name,
    className=f"route-line route-{route_group.id}",
    # Add custom attributes
    **{'data-route-id': route_group.id}
).add_to(self.map)
```

### Acceptance Criteria:

- [ ] Routes can be reliably identified in map
- [ ] Highlighting works consistently
- [ ] No console errors
- [ ] Visual feedback for user interactions
- [ ] Works with different Folium versions

---

## Issue #4: Add Route Comparison Metrics Visualization

**Labels:** `enhancement`, `feature`, `priority: low`

**Title:** Add charts and graphs for route comparison

**Description:**

Enhance the report with visual comparisons of routes using charts.

### Proposed Features:

1. **Bar Charts**
   - Compare duration across routes
   - Compare distance across routes
   - Compare elevation gain

2. **Radar Chart**
   - Show multi-dimensional comparison
   - Include time, distance, safety, consistency

3. **Time Series**
   - Show route usage over time
   - Identify seasonal patterns

### Implementation:

- Use Chart.js or similar library
- Add charts below route comparison table
- Make charts interactive (click to highlight route)

### Acceptance Criteria:

- [ ] Charts display correctly
- [ ] Charts are interactive
- [ ] Charts are responsive
- [ ] Data is accurate

---

## Issue #5: Mobile Responsive Design Improvements

**Labels:** `enhancement`, `ui/ux`, `priority: medium`

**Title:** Improve mobile experience for HTML report

**Description:**

The current report layout with side-by-side comparison and map may not work well on mobile devices.

### Tasks:

1. **Responsive Layout**
   - Stack table and map vertically on mobile
   - Adjust map height for mobile
   - Make table scrollable horizontally if needed

2. **Touch Interactions**
   - Ensure hover effects work with touch
   - Add tap-to-highlight for mobile
   - Improve button sizes for touch

3. **Performance**
   - Lazy load map on mobile
   - Optimize JavaScript for mobile browsers

### Acceptance Criteria:

- [ ] Report is usable on mobile devices
- [ ] All interactions work with touch
- [ ] Layout adapts to screen size
- [ ] Performance is acceptable on mobile

## Issue #7: Containerize Application with Podman Support

**Labels:** `enhancement`, `feature`, `infrastructure`, `priority: high`

**Title:** Add containerization support for Podman/Docker deployment

**Description:**

Containerize the application to enable easy deployment, consistent environments, and better portability. Support both Docker and Podman (rootless container runtime).

### Requirements:

1. **Dockerfile Creation**
   - Base image: Python 3.11+ slim
   - Install all dependencies from requirements.txt
   - Set up proper working directory
   - Configure environment variables
   - Expose necessary ports (if web interface added later)

2. **Podman Compatibility**
   - Ensure Dockerfile works with both Docker and Podman
   - Test rootless Podman deployment
   - Document Podman-specific commands

3. **Volume Mounts**
   - `/app/cache` - For geocoding and weather cache
   - `/app/data` - For activity data storage
   - `/app/output` - For generated reports
   - `/app/config` - For configuration files
   - `/app/.env` - For environment variables (secrets)

4. **Docker Compose / Podman Compose**
   - Create compose file for easy deployment
   - Configure volume mounts
   - Set environment variables
   - Add health checks

### Implementation:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p cache data output config

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python3", "main.py", "--analyze"]
```

```yaml
# docker-compose.yml / podman-compose.yml
version: '3.8'

services:
  strava-analyzer:
    build: .
    container_name: strava-route-analyzer
    volumes:
      - ./cache:/app/cache
      - ./data:/app/data
      - ./output:/app/output
      - ./config:/app/config
      - ./.env:/app/.env:ro
    environment:
      - STRAVA_CLIENT_ID=${STRAVA_CLIENT_ID}
      - STRAVA_CLIENT_SECRET=${STRAVA_CLIENT_SECRET}
    restart: unless-stopped
```

### Testing:

```bash
# Docker
docker build -t strava-analyzer .
docker run -v $(pwd)/cache:/app/cache -v $(pwd)/.env:/app/.env strava-analyzer

# Podman
podman build -t strava-analyzer .
podman run -v $(pwd)/cache:/app/cache:Z -v $(pwd)/.env:/app/.env:ro,Z strava-analyzer
```

### Acceptance Criteria:

- [ ] Dockerfile builds successfully
- [ ] Works with both Docker and Podman
- [ ] All dependencies installed correctly
- [ ] Volume mounts work properly
- [ ] Environment variables passed correctly
- [ ] Cache persists between runs
- [ ] Documentation includes container usage
- [ ] Compose file provided for easy deployment

---

## Issue #8: Add Multi-User Support with Strava OAuth

**Labels:** `enhancement`, `feature`, `security`, `priority: high`

**Title:** Implement multi-user system with individual Strava authentication

**Description:**

Transform the single-user CLI application into a multi-user system where each user can authenticate with their own Strava account and view their personal cycling data.

### Architecture Changes:

1. **User Management System**
   - User registration/login system
   - Store user credentials securely (hashed passwords)
   - User session management
   - User profile management

2. **Per-User Strava Authentication**
   - Each user authenticates with their own Strava account
   - Store OAuth tokens per user (encrypted)
   - Handle token refresh per user
   - Support multiple Strava accounts per user (optional)

3. **Data Isolation**
   - Separate data storage per user
   - User-specific cache directories
   - User-specific output directories
   - Prevent cross-user data access

4. **Web Interface** (Required for multi-user)
   - Flask or FastAPI web framework
   - Login/logout functionality
   - Dashboard showing user's routes
   - Interactive report viewing
   - Settings page for user preferences

### Database Schema:

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Strava tokens table
CREATE TABLE strava_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    access_token TEXT NOT NULL,  -- Encrypted
    refresh_token TEXT NOT NULL,  -- Encrypted
    expires_at TIMESTAMP NOT NULL,
    athlete_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User settings table
CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY,
    home_lat REAL,
    home_lon REAL,
    work_lat REAL,
    work_lon REAL,
    config_yaml TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Directory Structure:

```
/app/
  /users/
    /user_123/
      /cache/
      /data/
      /output/
      /config/
```

### Security Requirements:

- Password hashing with bcrypt or argon2
- OAuth tokens encrypted at rest
- HTTPS required for production
- CSRF protection
- Rate limiting on API endpoints
- Session timeout
- Secure cookie handling

### Acceptance Criteria:

- [ ] User registration and login system
- [ ] Per-user Strava OAuth flow
- [ ] Data isolation between users
- [ ] Web interface for user interaction
- [ ] Secure token storage (encrypted)
- [ ] Session management
- [ ] User can only access their own data
- [ ] Admin interface for user management (optional)

---

## Issue #9: Implement Security and Access Control

**Labels:** `security`, `priority: critical`

**Title:** Ensure robust security and user access control

**Description:**

Implement comprehensive security measures to protect user data and ensure proper access control in the multi-user system.

### Security Requirements:

1. **Authentication Security**
   - Strong password requirements (min 12 chars, complexity)
   - Password hashing with bcrypt (cost factor 12+)
   - Account lockout after failed login attempts
   - Two-factor authentication (optional, future)
   - Secure password reset flow

2. **Authorization & Access Control**
   - Role-based access control (RBAC)
   - User can only access their own data
   - Admin role for system management
   - API endpoint authorization checks
   - File system permission checks

3. **Data Protection**
   - Encrypt sensitive data at rest (OAuth tokens, API keys)
   - Use environment variables for secrets
   - Secure key management (consider HashiCorp Vault)
   - Regular security audits
   - Data retention policies

4. **Network Security**
   - HTTPS/TLS required in production
   - Secure headers (HSTS, CSP, X-Frame-Options)
   - CORS configuration
   - Rate limiting to prevent abuse
   - DDoS protection considerations

5. **Input Validation**
   - Sanitize all user inputs
   - Validate file uploads
   - Prevent SQL injection (use parameterized queries)
   - Prevent XSS attacks
   - Validate OAuth callbacks

6. **Audit Logging**
   - Log all authentication attempts
   - Log data access events
   - Log configuration changes
   - Log failed authorization attempts
   - Secure log storage

### Implementation:

```python
# Example: User data access control
def get_user_data(user_id: int, requested_user_id: int):
    """Ensure user can only access their own data."""
    if user_id != requested_user_id:
        raise PermissionError("Access denied: Cannot access other user's data")
    
    # Proceed with data retrieval
    return fetch_data(requested_user_id)

# Example: File system isolation
def get_user_directory(user_id: int) -> Path:
    """Get user-specific directory with proper permissions."""
    user_dir = Path(f"/app/users/user_{user_id}")
    user_dir.mkdir(mode=0o700, exist_ok=True)  # Owner only
    return user_dir
```

### Security Checklist:

- [ ] Password hashing implemented (bcrypt/argon2)
- [ ] OAuth tokens encrypted at rest
- [ ] HTTPS enforced in production
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output escaping)
- [ ] Secure session management
- [ ] File system permissions properly set
- [ ] Audit logging implemented
- [ ] Security headers configured
- [ ] Secrets stored in environment variables
- [ ] Regular dependency updates (security patches)
- [ ] Security testing performed

### Compliance Considerations:

- GDPR compliance (if serving EU users)
- Data export functionality
- Data deletion functionality
- Privacy policy
- Terms of service

### Acceptance Criteria:

- [ ] All security measures implemented
- [ ] Security audit passed
- [ ] Penetration testing completed
- [ ] Documentation includes security best practices
- [ ] Incident response plan documented

---

## Priority Summary

**P1 Priority (Immediate Improvements):**
- Issue #10: Extract HTML Template to External File
- Issue #11: Add QR Code Generation for Mobile Transfer
- Issue #12: Add PDF Export Option
- Issue #13: Add Route Comparison Feature
- Issue #14: Implement Data Export Formats (JSON, GPX, CSV)
- Issue #15: Implement Unit System Toggle (Metric/Imperial)
- Issue #16: Add Optimal Route Map Preview
- Issue #17: Significantly Improve Route Naming
- Issue #18: Remove Test Routes from Production
- Issue #19: Code Cleanup and Performance Optimization

**Critical Priority:**
- Issue #9: Implement Security and Access Control

**High Priority:**
- Issue #1: Test Interactive Features
- Issue #7: Containerize Application with Podman Support
- Issue #8: Add Multi-User Support with Strava OAuth

**Medium Priority:**
- Issue #2: Enhance Route Naming (superseded by Issue #17)
- Issue #3: Improve Map-Table Sync
- Issue #5: Mobile Responsive Design

**Low Priority:**
- Issue #4: Add Charts/Graphs

**Resolved:**
- Issue #6: ✅ Fix Logger Reference Before Definition (Commit: 7423f0d)

---

## How to Create These Issues on GitHub

1. Go to your repository on GitHub
2. Click on "Issues" tab
3. Click "New Issue"
4. Copy the title and description from each issue above
5. Add the appropriate labels
6. Assign to yourself or team members
7. Add to project board if using one

---

*Last Updated: 2026-03-24*