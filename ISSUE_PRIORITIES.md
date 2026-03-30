# Issue Prioritization

**Last Updated:** 2026-03-30 02:23 UTC

This file reflects the current state of GitHub issues by priority. Issues are managed via GitHub labels (P0-critical, P1-high, P2-medium, P3-low, P4-future).

## 🔴 P0 - CRITICAL (Drop Everything)
Issues that make the application unusable or cause data loss.

### Active P0 Issues

**None** ✅

## 🔴 P1 - HIGH (v2.5.0 Sprint)
Issues that significantly impact core functionality or user experience.

### Active P1 Issues (v2.5.0)

**Testing & Quality Assurance** (Deferred from v2.4.0)
- #99 - Create Comprehensive Unit Tests for All Core Modules (8-10h)
  - Target: 80% code coverage (currently 30%)
  - Modules: long_ride_analyzer, auth_secure, carbon_calculator, traffic_analyzer, next_commute_recommender, visualizer, route_analyzer, weather_fetcher, report_generator, api/long_rides_api
  - Supersedes #41
  
- #100 - Create Comprehensive Integration Tests for All Workflows (8-10h)
  - Long Rides workflow
  - Route comparison workflow
  - Weather dashboard data flow
  - Commute analysis with all features
  - Supersedes #42

- #101 - Update Documentation for Long Rides Feature (3h)
  - Update README.md with v2.4.0 features
  - Document Long Rides API endpoints
  - Create user guide updates
  - Add screenshots and examples

**Major Features** (Deferred from v2.4.0)
- #47 - Add Side-by-Side Route Comparison Feature (12-16h)
  - Implementation plan: `/plans/v2.5.0/ROUTE_COMPARISON_IMPLEMENTATION_PLAN.md`
  - Select 2-3 routes for comparison
  - Side-by-side metrics display
  - Interactive map visualization
  - Decision support with recommendations
  
- #54 - Weather Dashboard Implementation (Epic) (16-20h)
  - Implementation plan: `/plans/v2.5.0/WEATHER_DASHBOARD_IMPLEMENTATION_PLAN.md`
  - Current conditions widget
  - 24-hour hourly forecast
  - 7-day daily forecast
  - Weather alerts and recommendations
  - Ride suitability scoring


## 🟡 P2 - MEDIUM (Next Sprint)
Important improvements that enhance functionality but don't block core workflows.

- #73 - Investigate why routes 78 and 62 aren't matching in route grouping
- #74 - Ensure selected polylines and tooltips appear on top of all map elements
- #62 - 🎨 EPIC: Mobile-First UI/UX Redesign & Accessibility
  - #63 - Mobile-First Responsive Layout (in progress)
  - #64 - Progressive Disclosure for Metrics
  - #65 - Touch-Optimized Interactions (in progress)
  - #66 - Feature Discovery & Onboarding
  - #67 - Mobile Navigation Patterns
  - #68 - Visual Hierarchy & Polish

### P2 Issues from Long Rides Feature (Polish & Optimization)
- #95 - Optimize Mobile Map Performance (3h)
- #96 - Add Form Validation Feedback (2h)
- #97 - Optimize Chart Responsiveness (2h)
- #98 - Add Animation Performance Optimizations (2h)





## 🟢 P3 - LOW (Backlog)
Nice-to-have improvements and minor UX enhancements.

- #22 - Debug and fix Bootstrap tab switching functionality

## 📋 P4 - FUTURE ENHANCEMENTS
Feature requests and enhancements for future releases.



## ⚠️ Unprioritized Issues
Issues without priority labels that need to be triaged.

- #49 - Implement Metric/Imperial Unit Toggle with Complete Consistency
- #48 - Implement Data Export in JSON, GPX, and CSV Formats
- #46 - Add PDF Export Option
- #45 - Add QR Code Generation for Mobile Transfer
- #44 - Extract HTML template to external file
- #39 - Evaluate Photon API as Nominatim alternative
- #38 - Add social features (compare with other commuters)
- #37 - Add real-time route suggestions
- #36 - Create mobile app version
- #35 - Add integration with other fitness platforms



## Priority Guidelines

### P0 - CRITICAL
- Application is down or unusable
- Data loss or corruption
- Security vulnerabilities
- **Action:** Drop everything and fix immediately

### P1 - HIGH
- Core features broken or severely degraded
- Significant user pain points
- Blocks important workflows
- **Action:** Fix in current sprint (1-2 weeks)

### P2 - MEDIUM
- Feature improvements
- Moderate user pain points
- Quality of life enhancements
- **Action:** Plan for next sprint (2-4 weeks)

### P3 - LOW
- Minor UX improvements
- Edge cases
- Nice-to-have features
- **Action:** Backlog, address when time permits

### P4 - FUTURE
- New features
- Major enhancements
- Long-term improvements
- **Action:** Plan for future releases

## How to Update Priorities

1. Use GitHub labels to set priority (P0-critical, P1-high, P2-medium, P3-low, P4-future)
2. Update this file manually or via script
3. Commit changes with descriptive message
4. Communicate priority changes to team

## Summary Statistics

- **Total Open Issues:** 14
- **P0 (Critical):** 0 ✅
- **P1 (High):** 5 (v2.5.0 sprint)
- **P2 (Medium):** 10 (includes 4 Long Rides polish issues)
- **P3 (Low):** 1
- **P4 (Future):** 0
- **Unprioritized:** 8
- **Recently Closed:** 18 issues from v2.4.0 Long Rides Epic (see "Recently Completed" section below)

### v2.4.0 Completion Summary
- **Long Rides Epic (#57):** ✅ COMPLETED (18/21 issues)
  - Core functionality: 100% complete
  - Backend improvements (#89, #90, #91): Deferred to v2.6.0+ (not needed for static reports)
  - All user-facing features production-ready
- **Code Cleanup:** ✅ COMPLETED
  - Removed 115 console.log statements (8KB saved)
  - Created technical debt documentation
- **Status:** Ready for release

### v2.5.0 Sprint Planning
- **Total P1 Issues:** 5
- **Estimated Total Effort:** 48-60 hours (6-8 weeks at 8-10 hours/week)
- **Focus Areas:**
  1. Testing & Quality (16-20h)
  2. Route Comparison Feature (12-16h)
  3. Weather Dashboard (16-20h)
  4. Documentation (3h)
- **Release Plan:** `/plans/v2.5.0/README.md`

**Note:** Completed issues are documented in release notes (RELEASE_NOTES.md) and version-specific plans (plans/v2.x.0/).

## Recommended Next Actions (v2.5.0)

Focus on P1 issues in this order:

1. **Testing Infrastructure First** (Weeks 1-2)
   - #99 - Comprehensive unit tests (8-10h)
   - #100 - Integration tests (8-10h)
   - #101 - Documentation updates (3h)
   - Rationale: Establish quality foundation before adding features

2. **Route Comparison Feature** (Weeks 3-4)
   - #47 - Side-by-side route comparison (12-16h)
   - See implementation plan: `/plans/v2.5.0/ROUTE_COMPARISON_IMPLEMENTATION_PLAN.md`

3. **Weather Dashboard** (Weeks 5-7)
   - #54 - Weather dashboard (16-20h)
   - See implementation plan: `/plans/v2.5.0/WEATHER_DASHBOARD_IMPLEMENTATION_PLAN.md`

### Additional Actions (Not Issues)
- **CI/CD Integration** - Set up GitHub Actions with expanded test suite
- **Performance Monitoring** - Establish baseline metrics

---

## 🎉 Recently Completed

### Completed 2026-03-29

- **#34 - Add carbon footprint calculations** (COMPLETED 2026-03-29)
  - Created comprehensive CarbonCalculator module for environmental impact analysis
  - Calculates CO2 emissions saved vs driving
  - Tracks gasoline saved and money saved on fuel
  - Calculates calories burned and health benefits
  - Provides tree equivalency and environmental impact statements
  - Supports time-based projections (daily/weekly/monthly/yearly)
  - Route-by-route carbon footprint breakdown
  - Added carbon configuration to config.yaml
  - Supports both metric and imperial units
  - Files: src/carbon_calculator.py, config/config.yaml
  - Commit: 56e83fc
  - Priority: P1-high

- **#33 - Add traffic pattern analysis** (COMPLETED 2026-03-29)
  - Created comprehensive TrafficAnalyzer module for analyzing commute patterns
  - Analyzes usage by hour of day and day of week
  - Identifies peak/off-peak times and rush hour penalties
  - Calculates optimal departure times based on historical data
  - Provides traffic scores for route comparison at specific times
  - Added traffic configuration to config.yaml
  - Supports configurable rush hour windows
  - Files: src/traffic_analyzer.py, config/config.yaml
  - Commit: 40e910f
  - Priority: P1-high

- **#77 - Add user preferences configuration for browser, units, and other toggleable settings** (COMPLETED 2026-03-29)
  - Implemented user preferences system with config file support
  - Added browser selection (Chrome, Firefox, Safari, Edge, Brave)
  - Added unit system toggle (metric/imperial)
  - Added auto-open browser preference
  - Files: src/config.py, config/config.yaml
  - Priority: P1-high

- **#70 - Implement wind-aware route selection in forecast generator** (COMPLETED 2026-03-29)
  - Enhanced forecast generator to consider wind conditions
  - Integrated wind speed and direction into route recommendations
  - Added wind favorability scoring
  - Files: src/forecast_generator.py
  - Priority: P1-high

- **#58 - Show time-aware next commute recommendations (to work & to home)** (COMPLETED 2026-03-29)
  - Implemented intelligent time-based recommendations
  - Separate "to work" and "to home" route suggestions
  - Forecast weather for specific time windows
  - Wind favorability assessment
  - See NEXT_COMMUTE_FEATURE.md for details
  - Priority: P1-high

- **#25 - Implement automatic token refresh for expired Strava tokens** (COMPLETED 2026-03-29)
  - Added automatic token refresh mechanism
  - Improved authentication flow
  - Better error handling for expired tokens
  - Files: src/auth_secure.py
  - Priority: P1-high

- **#42 - Write integration tests for full workflow** (COMPLETED 2026-03-29)
  - Created comprehensive integration test suite
  - Covers full workflow from data fetching to report generation
  - Includes edge cases and error scenarios
  - Files: tests/test_integration.py
  - Priority: P1-high
  - Note: Superseded by #100 for expanded coverage

- **#41 - Create unit tests for core modules** (COMPLETED 2026-03-29)
  - Implemented unit tests for core functionality
  - Covers route analyzer, data fetcher, and other modules
  - Improved code coverage
  - Files: tests/test_route_analyzer.py, tests/test_data_fetcher.py, tests/test_units.py
  - Priority: P1-high
  - Note: Superseded by #99 for expanded coverage

### Completed 2026-03-27

- **#72 - Test: Investigate why routes 78 and 62 aren't matching** (COMPLETED 2026-03-27)
  - Investigated route matching algorithm
  - Identified and resolved matching issues
  - Improved route grouping logic
  - Priority: P2-medium

- **#61 - Code Quality: Improve exception handling (remove bare except)** (COMPLETED 2026-03-27)
  - Removed bare except clauses
  - Added specific exception handling
  - Improved error messages and logging
  - Priority: P3-low

- **#60 - Security: Upgrade vulnerable dependencies (requests, tornado, pygments)** (COMPLETED 2026-03-27)
  - Updated vulnerable dependencies to secure versions
  - Resolved security vulnerabilities
  - Updated requirements.txt
  - Priority: P1-high, security

- **#59 - Security: Replace MD5 hash with SHA256 for cache keys** (COMPLETED 2026-03-27)
  - Migrated from MD5 to SHA256 for cache key generation
  - Improved security posture
  - Updated cache handling logic
  - Priority: P2-medium, security

- **#56 - Implement percentile-based route similarity to reduce over-clustering** (COMPLETED 2026-03-27)
  - Implemented percentile-based similarity algorithm
  - Reduced over-clustering of routes
  - Improved route grouping accuracy
  - Priority: P1-high

### UI/UX Improvements
- **#71 - UI/UX Improvements for Route Comparison Table and Map** (COMPLETED 2026-03-27)
  - All 7 improvements implemented
  - Table sorting functionality with visual indicators
  - Fixed route group name display (geographic names)
  - Updated polyline colors to semantic system (green=optimal)
  - Removed "View on Strava" button, made route name clickable
  - Made "Uses" column clickable to show matched activities modal
  - Fixed page counter display
  - Simplified route counter display
  - Files: templates/report_template.html, src/route_analyzer.py, config/config.yaml
  - Priority: P1-high

- **#69 - Map Direction Indicators** (COMPLETED 2026-03-27)
  - Implemented direction arrows on Next Commute map
  - Stacked card layout for "To Work" and "To Home" recommendations
  - Dense information display with 6 compact metrics per card
  - Interactive map with color-coded routes (green for "to work", blue for "to home")
  - Direction arrows using screen-space bearing calculation
  - Click handlers to highlight and zoom to specific routes
  - Responsive design with mobile breakpoints
  - Files: templates/report_template.html
  - Priority: P1-high

- **#75 - Add current weather conditions display to map** (COMPLETED 2026-03-27)
  - Shows real-time weather on interactive map
  - Temperature with unit conversion
  - Wind speed and direction (cardinal + degrees)
  - Precipitation amount
  - Integrates with WeatherFetcher and Open-Meteo API
  - Priority: P2-medium

- **#21 - Update TECHNICAL_SPEC.md** (COMPLETED 2026-03-27)
  - Updated 3 major sections with comprehensive implementation details
  - Route naming algorithm documentation
  - Security improvements (MD5 → SHA256)
  - Exception handling enhancements
  - Priority: P2-medium