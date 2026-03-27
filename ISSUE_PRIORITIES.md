# Issue Prioritization

**Last Updated:** 2026-03-27 01:30 UTC

This file reflects the current state of GitHub issues by priority. Issues are managed via GitHub labels (P0-critical, P1-high, P2-medium, P3-low, P4-future).

## 🔴 P0 - CRITICAL (Drop Everything)
Issues that make the application unusable or cause data loss.

### Active P0 Issues

**None** - All critical issues resolved! ✅

### Recently Resolved P0 Issues

- **✅ Test Suite Failures (16/43 tests failing)** - RESOLVED 2026-03-27
  - All 43 tests now passing (100% pass rate)
  - Fixed type mismatches, mock configurations, and edge cases
  - Test suite ready for CI/CD integration

## 🔴 P1 - HIGH (Current Sprint)
Issues that significantly impact core functionality or user experience.

### Active P1 Issues

- #58 - Show time-aware next commute recommendations (to work & to home)

### Recently Completed P1 Issues

- **✅ EPIC: Segment-Based Route Naming** - COMPLETED 2026-03-27
  - ✅ Sub-issue 1: Increase route sampling density (10 points instead of 5)
  - ✅ Sub-issue 2: Implement route segment identification
  - ✅ Sub-issue 3: Implement segment-based name generation
  - ✅ Sub-issue 4: Update route analysis integration
  - ✅ Sub-issue 5: Add configuration options to config.yaml
  - ✅ Sub-issue 6: Clear cache and validate with real data
  - Route names now show: "Start St → Main St → End St"

## 🟡 P2 - MEDIUM (Next Sprint)
Important improvements that enhance functionality but don't block core workflows.

- #21 - Update TECHNICAL_SPEC.md with comprehensive implementation details



## 🟢 P3 - LOW (Backlog)
Nice-to-have improvements and minor UX enhancements.

- #41 - Create unit tests for core modules (in progress - tests created, need more coverage)
- #42 - Write integration tests for full workflow (in progress - tests created, need more coverage)
- #22 - Debug and fix Bootstrap tab switching functionality

### Recently Completed P3 Issues

- **✅ #61** - Code Quality: Improve exception handling - COMPLETED 2026-03-27
  - All bare `except:` statements replaced with specific exception types
  - Added debug logging for troubleshooting

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

- **Total Open Issues:** 28
- **P0 (Critical):** 0 ✅ (All resolved!)
- **P1 (High):** 1 (down from 7 - Route Naming Epic completed!)
- **P2 (Medium):** 1
- **P3 (Low):** 3 (includes new #70)
- **P4 (Future):** 6
- **Unprioritized:** 15

## Completed Issues (v2.2.0 - 2026-03-27)

### v2.1.0 Completed (2026-03-26)
1. **✅ #55** - Closed as superseded by #56 (Fréchet algorithm already working)
2. **✅ #53** - Code Cleanup and Performance Optimization
3. **✅ #52** - Remove Test Routes from Production Code
4. **✅ #51** - Significantly Improve Route Naming Mechanism
5. **✅ #50** - Show Optimal Route Map Preview at Top of Page
6. **✅ #43** - Add caching for Fréchet distance calculations

### v2.2.0 In Progress (2026-03-27)
1. **✅ Test Infrastructure** - Created pytest configuration, test runner, and documentation
2. **✅ Cache Separation Implementation** - Separated test and production cache files
   - Added `use_test_cache` parameter to StravaDataFetcher
   - Created `data/cache/activities_test.json` for test data
   - Protected production cache (`data/cache/activities.json`) from test overwrites
   - Created `tests/setup_test_data.py` for synthetic test data generation
   - Documented in `tests/TEST_DATA_README.md` and `CACHE_SEPARATION_IMPLEMENTATION.md`
   - Prevents data loss incidents (recovered from March 26 incident where 2,408 activities were overwritten)
3. **✅ Test Suite Remediation** - Fixed all 16 failing tests (100% pass rate achieved)
   - Fixed Activity dataclass 'commute' parameter issues (6 tests)
   - Fixed datetime vs string type mismatches (3 tests)
   - Fixed tuple vs Location object mismatches (5 tests)
   - Fixed mock configuration issues (2 tests)
   - Fixed edge case handling and assertions (2 tests)
   - Implemented all fixes from TEST_REMEDIATION_PLAN.md (Phases 1-3)
   - Test suite now fully operational: **43/43 tests passing** ✅
4. **✅ #61** - Code Quality: Improve exception handling (COMPLETED 2026-03-27)
   - Replaced all bare `except:` statements with specific exception types
   - Added debug logging for better troubleshooting
5. **✅ Route Naming Epic** - Segment-Based Route Naming (COMPLETED 2026-03-27)
   - Increased route sampling density from 5 to 10 points
   - Implemented route segment identification algorithm
   - Added segment-based name generation: "Start St → Main St → End St"
   - Integrated segments into route analysis workflow
   - Added configuration options to config.yaml
   - Cleared geocoding cache for fresh analysis
6. **✅ Security: Replace MD5 with SHA256** - (COMPLETED 2026-03-27)
   - Updated cache key generation in route_analyzer.py and weather_fetcher.py
   - Cleared route_similarity_cache.json for regeneration
7. **🔄 #41** - Unit tests for core modules (in progress - 4 test files created, need more coverage)
8. **🔄 #42** - Integration tests for full workflow (in progress - end-to-end tests created)
9. **🔄 #63** - Mobile-first responsive layout (in progress - part of #62 epic)
10. **🔄 #65** - Touch-optimized interactions (in progress - part of #62 epic)

## Recommended Next Actions

1. **#58** - Time-aware next commute recommendations (P1-high) - ONLY REMAINING P1 ISSUE
2. **#21** - Update TECHNICAL_SPEC.md with comprehensive implementation details (P2-medium)
3. **Test with real data** - Validate segment-based route naming with actual Strava routes
4. **CI/CD Integration** - Set up GitHub Actions with the now-working test suite
5. **Increase test coverage** - Expand #41 and #42 to cover more modules
6. **Triage unprioritized issues** - Assign priority labels to remaining 15 issues
7. **Prepare v2.3.0 release** - Route naming epic complete, ready for next release