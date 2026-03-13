#!/bin/bash

# Create all GitHub issues for outstanding todos

echo "Creating GitHub issues..."

# Issue 2: Monthly statistics
gh issue create --title "Add monthly ride statistics breakdown" --body "Add monthly statistics showing:
- Rides per month
- Total distance per month
- Average distance per month
- Chart showing monthly trends

**Acceptance Criteria:**
- [ ] Monthly breakdown table or cards
- [ ] Line chart showing monthly trends
- [ ] Year-over-year comparison if data available"

# Issue 3: Speed and elevation
gh issue create --title "Add average speed and elevation gain metrics" --body "Enhance long rides analysis with:
- Average speed statistics
- Total elevation gain
- Elevation gain per ride
- Speed distribution chart

**Acceptance Criteria:**
- [ ] Display average speed for all long rides
- [ ] Show total and average elevation gain
- [ ] Add speed distribution histogram
- [ ] Include elevation profile visualization"

# Issue 4: Long rides map
gh issue create --title "Add interactive map showing all long ride routes" --body "Create an interactive map similar to commute routes map but for long rides:
- Display all long ride routes
- Color-code by distance or date
- Click to view ride details
- Filter by date range or distance

**Acceptance Criteria:**
- [ ] Interactive Folium map with all long rides
- [ ] Color coding system
- [ ] Click handlers for ride details
- [ ] Filter controls for date and distance"

# Issue 5: Forecast integration
gh issue create --title "Integrate forecast generator into main.py workflow" --body "Add the forecast generator to the main analysis workflow:
- Generate 7-day weather forecast
- Integrate with existing weather fetcher
- Add to HTML report

**Acceptance Criteria:**
- [ ] Forecast generator called in main.py
- [ ] 7-day forecast data available
- [ ] Integrated with weather cache system"

# Issue 6: Forecast UI
gh issue create --title "Design 7-day forecast card layout" --body "Create visual design for forecast display:
- 7-day forecast cards
- Morning (7-9 AM) and evening (3-6 PM) windows
- Weather icons and conditions
- Temperature, wind, precipitation

**Acceptance Criteria:**
- [ ] Responsive card layout for 7 days
- [ ] Morning and evening time windows
- [ ] Weather icons for conditions
- [ ] Clear display of key metrics"

# Issue 7: Morning window
gh issue create --title "Add morning commute window (7-9 AM) weather display" --body "Display weather conditions for morning commute window:
- Temperature range
- Wind speed and direction
- Precipitation probability
- Optimal route recommendation

**Acceptance Criteria:**
- [ ] Morning window (7-9 AM) clearly labeled
- [ ] All weather metrics displayed
- [ ] Route recommendation based on conditions"

# Issue 8: Evening window
gh issue create --title "Add evening commute window (3-6 PM) weather display" --body "Display weather conditions for evening commute window:
- Temperature range
- Wind speed and direction
- Precipitation probability
- Optimal route recommendation

**Acceptance Criteria:**
- [ ] Evening window (3-6 PM) clearly labeled
- [ ] All weather metrics displayed
- [ ] Route recommendation based on conditions"

# Issue 9: Weather severity
gh issue create --title "Add weather severity indicators (good/fair/poor/miserable icons)" --body "Add visual indicators for weather conditions:
- Good: ☀️ (sunny, light wind)
- Fair: ⛅ (partly cloudy, moderate wind)
- Poor: 🌧️ (rain, strong wind)
- Miserable: ⛈️ (heavy rain, very strong wind)

**Acceptance Criteria:**
- [ ] Icon system for 4 severity levels
- [ ] Clear criteria for each level
- [ ] Displayed prominently in forecast"

# Issue 10: Route recommendations
gh issue create --title "Show optimal route recommendations based on wind" --body "Provide route recommendations based on forecast:
- Best route for each day
- Wind impact analysis
- Alternative routes if conditions are poor

**Acceptance Criteria:**
- [ ] Daily route recommendation
- [ ] Wind impact explanation
- [ ] Alternative routes suggested"

# Issue 11: Transit recommendations
gh issue create --title "Add transit recommendations when conditions are poor" --body "Suggest public transit when weather is too severe:
- Threshold for 'too severe' conditions
- Transit alternatives
- Link to transit planner

**Acceptance Criteria:**
- [ ] Severity threshold defined
- [ ] Transit suggestion displayed
- [ ] Optional link to transit planner"

# Issue 12: Optimal departure time
gh issue create --title "Display optimal departure time suggestions" --body "Suggest best departure times based on weather:
- Analyze weather throughout commute windows
- Recommend specific departure time
- Show weather progression

**Acceptance Criteria:**
- [ ] Optimal time calculated
- [ ] Reasoning displayed
- [ ] Weather progression shown"

# Issue 13: Visual weather icons
gh issue create --title "Add visual weather icons and color coding" --body "Enhance forecast with visual elements:
- Weather condition icons
- Color-coded temperature ranges
- Wind direction arrows
- Precipitation indicators

**Acceptance Criteria:**
- [ ] Icon library integrated
- [ ] Color coding system implemented
- [ ] Wind direction visualization
- [ ] Precipitation display"

# Issue 14: Map auto zoom
gh issue create --title "Fix map zoom to show start and finish when route is selected" --body "When a route is clicked, automatically zoom the map to show the entire route from start to finish.

**Acceptance Criteria:**
- [ ] Map zooms when route selected
- [ ] Entire route visible
- [ ] Smooth zoom animation"

# Issue 15: Re-enable geocoding
gh issue create --title "Re-enable geocoding after rate limit expires" --body "Nominatim geocoding was temporarily disabled due to rate limits. Re-enable this weekend (March 15-16).

**Acceptance Criteria:**
- [ ] Geocoding re-enabled in code
- [ ] Rate limiting properly implemented
- [ ] Cache working correctly
- [ ] Route names display properly"

# Issue 16: Documentation
gh issue create --title "Update TECHNICAL_SPEC.md with comprehensive implementation details" --body "Document all recent implementations:
- Long rides analysis
- Weather caching
- Chart.js integration
- Bootstrap tooltips
- Interactive UI features

**Acceptance Criteria:**
- [ ] All new features documented
- [ ] Code examples included
- [ ] Architecture diagrams updated
- [ ] API documentation complete"

# Issue 17: Bootstrap tabs (low priority)
gh issue create --title "[LOW PRIORITY] Debug and fix Bootstrap tab switching functionality" --body "Bootstrap tabs are not switching content properly. Attempted fix with aria attributes but issue persists.

**Acceptance Criteria:**
- [ ] Tabs switch content correctly
- [ ] No JavaScript errors
- [ ] Smooth transitions"

# Issue 18: Route colors (low priority)
gh issue create --title "[LOW PRIORITY] Color code route names to match map line colors" --body "Make route names in the table match the colors of their lines on the map for easier identification.

**Acceptance Criteria:**
- [ ] Route names colored
- [ ] Colors match map lines
- [ ] Accessible color contrast"

# Issue 19: Grey out routes (low priority)
gh issue create --title "[LOW PRIORITY] Grey out unselected routes on map when route is clicked" --body "When a route is selected, fade out other routes to focus attention on the selected route.

**Acceptance Criteria:**
- [ ] Unselected routes fade to grey
- [ ] Selected route remains vibrant
- [ ] Smooth transition animation
- [ ] Click again to restore all routes"

echo "All issues created successfully!"

# Made with Bob
