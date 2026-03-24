# Issue Prioritization

**Last Updated:** 2026-03-24

This file reflects the current state of GitHub issues by priority. Issues are managed via GitHub labels (P0-critical, P1-high, P2-medium, P3-low, P4-future).

## 🔴 P0 - CRITICAL (Drop Everything)
Issues that make the application unusable or cause data loss.

**No P0 issues currently open** ✅

## 🔴 P1 - HIGH (Current Sprint)
Issues that significantly impact core functionality or user experience.

- #44 - Extract HTML Template to External File
- #45 - Add QR Code Generation for Mobile Transfer
- #46 - Add PDF Export Option
- #47 - Add Side-by-Side Route Comparison Feature
- #48 - Implement Data Export in JSON, GPX, and CSV Formats
- #49 - Implement Metric/Imperial Unit Toggle with Complete Consistency
- #50 - Show Optimal Route Map Preview at Top of Page
- #51 - Significantly Improve Route Naming Mechanism
- #52 - Remove Test Routes from Production Code
- #53 - Code Cleanup and Performance Optimization

## 🟡 P2 - MEDIUM (Next Sprint)
Important improvements that enhance functionality but don't block core workflows.

- #19 - Fix map zoom to show start and finish when route is selected
- #20 - Re-enable geocoding after rate limit expires
- #21 - Update TECHNICAL_SPEC.md with comprehensive implementation details
- #24 - Grey out unselected routes on map when route is clicked

## 🟢 P3 - LOW (Backlog)
Nice-to-have improvements and minor UX enhancements.

- #22 - Debug and fix Bootstrap tab switching functionality
- #40 - Complete and review full analysis with Fréchet algorithm
- #41 - Create unit tests for core modules
- #42 - Write integration tests for full workflow

## 📋 P4 - FUTURE ENHANCEMENTS
Feature requests and enhancements for future releases.

### Long Rides Features
- #6 - Add top 10 longest rides table with Strava links
- #7 - Add monthly ride statistics breakdown
- #8 - Add average speed and elevation gain metrics
- #9 - Add interactive map showing all long ride routes

### Weather Integration
- #54 - Weather Dashboard Implementation (Epic)

### Infrastructure & Integrations
- #25 - Implement automatic token refresh for expired Strava tokens
- #33 - Add traffic pattern analysis
- #34 - Add carbon footprint calculations
- #35 - Add integration with other fitness platforms
- #39 - Evaluate Photon API as Nominatim alternative

### Advanced Features
- #36 - Create mobile app version
- #37 - Add real-time route suggestions
- #38 - Add social features (compare with other commuters)

## ⚠️ Unprioritized Issues
Issues without priority labels that need to be triaged.

**No unprioritized issues currently open** ✅

## Priority Guidelines

### P0 - CRITICAL
- Application is down or unusable
- Data loss or corruption
- Security vulnerabilities
- Strava API authentication failures
- **Action:** Drop everything and fix immediately

### P1 - HIGH
- Core features broken or severely degraded
- Significant user pain points
- Blocks important workflows
- Route matching failures
- Weather data integration issues
- **Action:** Fix in current sprint (1-2 weeks)

### P2 - MEDIUM
- Feature improvements
- Moderate user pain points
- Quality of life enhancements
- Report visualization improvements
- **Action:** Plan for next sprint (2-4 weeks)

### P3 - LOW
- Minor UX improvements
- Edge cases
- Nice-to-have features
- Documentation updates
- **Action:** Backlog, address when time permits

### P4 - FUTURE
- New features
- Major enhancements
- Long-term improvements
- Mobile app development
- Real-time tracking integration
- **Action:** Plan for future releases

## How to Update Priorities

1. Use GitHub labels to set priority (P0-critical, P1-high, P2-medium, P3-low, P4-future)
2. Manually update this file to reflect current state
3. Commit changes with descriptive message
4. Communicate priority changes to team

## Issue Lifecycle

```
New Issue → Triaged (Priority Assigned) → In Progress → Testing → Closed
```

### Status Labels
- `needs-triage` - New issue, priority not yet assigned
- `in-progress` - Actively being worked on
- `blocked` - Waiting on external dependency
- `needs-testing` - Implementation complete, needs verification
- `ready-for-review` - Code complete, awaiting review

## Sprint Planning

### Current Sprint Focus (Week of 2026-03-24)
**Theme:** Report Enhancement & Code Quality

**Goals:**
1. Extract HTML template for maintainability (#44)
2. Add mobile transfer capability (#45)
3. Improve route naming (#51)
4. Clean up test code (#52)

**Stretch Goals:**
- PDF export (#46)
- Unit system consistency (#49)

### Next Sprint (Week of 2026-03-31)
**Theme:** Data Export & Visualization

**Planned:**
- Side-by-side route comparison (#47)
- Multiple export formats (#48)
- Optimal route preview map (#50)
- Map zoom fixes (#19)
- Re-enable geocoding (#20)

## Issue Statistics

**Total Open Issues:** 30 (down from 52 after deduplication)
- P0 (Critical): 0
- P1 (High): 10
- P2 (Medium): 4
- P3 (Low): 4
- P4 (Future): 12

**Recently Closed:** 23 issues
- #1-5: Fréchet algorithm validation (completed)
- #10-18, #26-32: Weather features (consolidated into #54)
- #23: Route naming color coding (duplicate of #51)
- #43: Fréchet caching (completed)

**Average Time to Close:** TBD (tracking starts 2026-03-24)

## Deduplication Summary

**Date:** 2026-03-24

### Actions Taken:
1. ✅ Closed #1-5 (Fréchet validation - completed)
2. ✅ Closed #10-18, #26-32 (Weather - consolidated into #54)
3. ✅ Closed #23 (Duplicate of #51)
4. ✅ Created #54 (Weather Dashboard Epic)
5. ✅ Reprioritized remaining 30 issues

### Result:
- **Before:** 52 open issues (many duplicates/obsolete)
- **After:** 30 open issues (clean, prioritized)
- **Improvement:** 42% reduction in issue count

## Related Documentation

- [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md) - Development workflow and processes
- [GITHUB_ISSUES.md](./GITHUB_ISSUES.md) - Detailed issue descriptions
- [WEEKLY_MAINTENANCE.md](./WEEKLY_MAINTENANCE.md) - Maintenance procedures