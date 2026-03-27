# Issue Prioritization

**Last Updated:** 2026-03-27 01:57 UTC

This file reflects the current state of GitHub issues by priority. Issues are managed via GitHub labels (P0-critical, P1-high, P2-medium, P3-low, P4-future).

## 🔴 P0 - CRITICAL (Drop Everything)
Issues that make the application unusable or cause data loss.

### Active P0 Issues

**None** ✅

## 🔴 P1 - HIGH (Current Sprint)
Issues that significantly impact core functionality or user experience.

### Active P1 Issues

- #58 - Show time-aware next commute recommendations (to work & to home)
- #71 - UI/UX Improvements for Route Comparison Table and Map (NEW - 2026-03-27)
- #41 - Create unit tests for core modules (moved from P3 - 2026-03-27)
- #42 - Write integration tests for full workflow (moved from P3 - 2026-03-27)
- #21 - Update TECHNICAL_SPEC.md with comprehensive implementation details (moved from P2 - 2026-03-27)

## 🟡 P2 - MEDIUM (Next Sprint)
Important improvements that enhance functionality but don't block core workflows.

**None**



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

- **Total Open Issues:** 29
- **P0 (Critical):** 0 ✅
- **P1 (High):** 5
- **P2 (Medium):** 0
- **P3 (Low):** 1
- **P4 (Future):** 6
- **Unprioritized:** 15

**Note:** Completed issues are documented in release notes (RELEASE_NOTES.md) and version-specific plans (plans/v2.x.0/).

## Recommended Next Actions

All recommended actions have been prioritized to P1-high:

1. **#71** - UI/UX Improvements for Route Comparison Table and Map (P1-high) ⭐ NEW
2. **#58** - Time-aware next commute recommendations (P1-high)
3. **#21** - Update TECHNICAL_SPEC.md with comprehensive implementation details (P1-high) ⬆️ Moved from P2
4. **#41** - Create unit tests for core modules (P1-high) ⬆️ Moved from P3
5. **#42** - Write integration tests for full workflow (P1-high) ⬆️ Moved from P3

### Additional Actions (Not Issues)
- **Test with real data** - Validate segment-based route naming with actual Strava routes
- **CI/CD Integration** - Set up GitHub Actions with the now-working test suite
- **Triage unprioritized issues** - Assign priority labels to remaining 15 issues
- **Prepare v2.3.0 release** - Route naming epic complete, ready for next release