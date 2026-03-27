# Issue Prioritization

**Last Updated:** 2026-03-27 13:00 UTC

This file reflects the current state of GitHub issues by priority. Issues are managed via GitHub labels (P0-critical, P1-high, P2-medium, P3-low, P4-future).

## 🔴 P0 - CRITICAL (Drop Everything)
Issues that make the application unusable or cause data loss.

### Active P0 Issues

**None** ✅

## 🔴 P1 - HIGH (Current Sprint)
Issues that significantly impact core functionality or user experience.

### Active P1 Issues

- #71 - UI/UX Improvements for Route Comparison Table and Map (NEW - 2026-03-27)
- #41 - Create unit tests for core modules (moved from P3 - 2026-03-27)
- #42 - Write integration tests for full workflow (moved from P3 - 2026-03-27)

## 🟡 P2 - MEDIUM (Next Sprint)
Important improvements that enhance functionality but don't block core workflows.

- #73 - Investigate why routes 78 and 62 aren't matching in route grouping
- #74 - Ensure selected polylines and tooltips appear on top of all map elements



## 🟢 P3 - LOW (Backlog)
Nice-to-have improvements and minor UX enhancements.

- #22 - Debug and fix Bootstrap tab switching functionality

## 📋 P4 - FUTURE ENHANCEMENTS
Feature requests and enhancements for future releases.

- #70 - Implement wind-aware route selection in forecast generator
- #62 - 🎨 EPIC: Mobile-First UI/UX Redesign & Accessibility
  - #63 - Mobile-First Responsive Layout (in progress)
  - #64 - Progressive Disclosure for Metrics
  - #65 - Touch-Optimized Interactions (in progress)
  - #66 - Feature Discovery & Onboarding
  - #67 - Mobile Navigation Patterns
  - #68 - Visual Hierarchy & Polish
  - #69 - Map Direction Indicators
- #57 - 🎯 EPIC: Long Rides Analysis & Recommendations (consolidates #6, #7, #8, #9)
  - #6 - Add top 10 longest rides table with Strava links
  - #7 - Add monthly ride statistics breakdown
  - #8 - Add average speed and elevation gain metrics
  - #9 - Add interactive map showing all long ride routes
- #54 - Weather Dashboard Implementation (Epic)
- #33 - Add traffic pattern analysis

## ⚠️ Unprioritized Issues
Issues without priority labels that need to be triaged.

- #49 - Implement Metric/Imperial Unit Toggle with Complete Consistency
- #48 - Implement Data Export in JSON, GPX, and CSV Formats
- #47 - Add Side-by-Side Route Comparison Feature
- #46 - Add PDF Export Option
- #45 - Add QR Code Generation for Mobile Transfer
- #44 - Extract HTML template to external file
- #39 - Evaluate Photon API as Nominatim alternative
- #38 - Add social features (compare with other commuters)
- #37 - Add real-time route suggestions
- #36 - Create mobile app version
- #35 - Add integration with other fitness platforms
- #34 - Add carbon footprint calculations
- #25 - Implement automatic token refresh for expired Strava tokens


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

- **Total Open Issues:** 31
- **P0 (Critical):** 0 ✅
- **P1 (High):** 3
- **P2 (Medium):** 2
- **P3 (Low):** 1
- **P4 (Future):** 6
- **Unprioritized:** 15

**Note:** Completed issues are documented in release notes (RELEASE_NOTES.md) and version-specific plans (plans/v2.x.0/).

## Recommended Next Actions

All recommended actions have been prioritized to P1-high:

1. **#71** - UI/UX Improvements for Route Comparison Table and Map (P1-high) ⭐ NEW
2. **#41** - Create unit tests for core modules (P1-high) ⬆️ Moved from P3
3. **#42** - Write integration tests for full workflow (P1-high) ⬆️ Moved from P3

### Additional Actions (Not Issues)
- **Create GitHub issues** - Create 2 new P2 issues from `plans/v2.2.0/GITHUB_ISSUES_FROM_FUTURE_TODOS.md`
- **Test v2.2.0 fixes** - Verify JSON serialization fix and performance improvements
- **Run performance profiling** - Measure actual improvements from Phase 1 optimizations
- **Test with real data** - Validate segment-based route naming with actual Strava routes
- **CI/CD Integration** - Set up GitHub Actions with the now-working test suite
- **Triage unprioritized issues** - Assign priority labels to remaining 15 issues
- **Prepare v2.3.0 release** - Route naming epic complete, ready for next release

---

## 🎉 Recently Completed (2026-03-27)

### v2.3.0 Implementations
- **#75 - Add current weather conditions display to map** - Shows real-time weather on interactive map (COMPLETED 2026-03-27)
  - Temperature with unit conversion
  - Wind speed and direction (cardinal + degrees)
  - Precipitation amount
  - Integrates with WeatherFetcher and Open-Meteo API
  - Commit: 131a6fb

- **Progress Bar Improvements** - Enhanced terminal output visibility (COMPLETED 2026-03-27)
  - Updated bar format to show step counts (2/8 format)
  - Added user prompt for background geocoding approval
  - Documented in FUTURE_TODOS.md as RESOLVED
  - Commit: 131a6fb

- **#21 - Update TECHNICAL_SPEC.md** - Updated 3 major sections with comprehensive implementation details
  - Route naming algorithm documentation
  - Security improvements (MD5 → SHA256)
  - Exception handling enhancements

### v2.0.0 Implementations
- **#58 - Time-aware next commute recommendations** - Shows separate "to work" and "to home" recommendations
  - Intelligent time-based logic (morning/midday/evening)
  - Forecast weather for specific time windows
  - Wind favorability assessment
  - See NEXT_COMMUTE_FEATURE.md for details

### v2.2.0 Implementations
- **JSON Serialization Fix** - Fixed `TypeError: Object of type Route is not JSON serializable` in matched routes modal
  - Added `_route_to_dict()` helper method in ReportGenerator
  - Updated template to use serialized route data
  - Files: src/report_generator.py, templates/report_template.html

- **Performance Optimizations (Phase 1)** - Implemented quick-win optimizations for ~48% performance improvement
  - Non-blocking browser opening (saves ~6 seconds)
  - Wind analysis coordinate sampling with 10x reduction in calculations (saves ~2 seconds)
  - Files: main.py, src/weather_fetcher.py
  - Expected: 16.8s → 8.8s runtime