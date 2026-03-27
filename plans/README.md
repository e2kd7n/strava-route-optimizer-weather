# Planning Documents - Organized by Release

This directory contains all planning documents organized by the release version where the work was completed.

---

## Directory Structure

```
plans/
├── v0.1.0/          # Initial Release (March 11-12, 2026)
├── v1.0.0/          # Long Rides & Security (March 12-13, 2026)
├── v2.0.0/          # Feature Complete (March 24, 2026)
├── v2.1.0/          # Code Quality & Design System (March 26, 2026)
├── v2.2.0/          # Test Suite & Cache (March 26, 2026)
├── v2.3.0/          # Segment-Based Route Naming (March 26, 2026)
├── v2.4.0/          # ⛔ BLOCKED - Awaiting Geocoding Completion
└── README.md        # This file
```

---

## Release v0.1.0 - Initial Release

**Date:** March 11-12, 2026  
**Tag:** v0.1.0  
**Commit:** d0b1ecd

### Planning Documents
- **PLAN.md** - Original project plan and feature roadmap
- **WORKFLOW.md** - Development workflow and processes

### Key Features
- Strava OAuth integration
- Route analysis and similarity matching
- Weather integration with wind impact
- Interactive HTML reports
- Geocoding support

---

## Release v1.0.0 - Long Rides & Security

**Date:** March 12-13, 2026  
**Tag:** v1.0.0  
**Commit:** 7731a69

### Planning Documents
- **LONG_RIDE_RECOMMENDATIONS.md** - Long rides feature specification
- **ROUTE_SIMILARITY_OUTLIER_TOLERANCE.md** - Route matching algorithm details
- **ROUTE_MATCHING_EXPLANATION.md** - Fréchet distance implementation

### Key Features
- Long rides recommendation system with wind-optimized scoring
- Fréchet distance for route matching
- Comprehensive security enhancements
- Interactive UI features
- Anti-piracy protection

---

## Release v2.0.0 - Feature Complete

**Date:** March 24, 2026  
**Tag:** v2.0.0  
**Commit:** efbcc1c

### Planning Documents
- *(No specific planning documents - rapid feature development)*

### Key Features
- QR codes and PDF export
- Route comparison features
- Data export capabilities
- Multi-select support
- Parallel processing
- Plus route detection
- Historical data fetching

---

## Release v2.1.0 - Code Quality & Design System

**Date:** March 26, 2026  
**Tag:** v2.1.0  
**Commit:** 34033a4

### Planning Documents
- **DESIGN_PRINCIPLES.md** - Comprehensive design system (10 core principles)
- **P1_ISSUES_IMPLEMENTATION_PLAN.md** - P1 issues implementation details
- **UIUX_IMPROVEMENTS_EPIC.md** - Mobile-first UI/UX redesign specifications

### Key Features
- Improved exception handling
- SHA256 security migration
- Design system establishment
- UI/UX redesign roadmap (Epic #62 with 7 sub-issues)

---

## Release v2.2.0 - Test Suite & Cache

**Date:** March 26, 2026  
**Tag:** v2.2.0  
**Commit:** 3df3bd8

### Planning Documents
- **TEST_REMEDIATION_PLAN.md** - Test suite remediation strategy
- **CACHE_SEPARATION_IMPLEMENTATION.md** - Cache separation architecture

### Key Features
- All test suite failures resolved
- Cache separation implementation
- Repository renamed to ride-optimizer
- P1 features added

---

## Release v2.3.0 - Segment-Based Route Naming

**Date:** March 26, 2026  
**Tag:** v2.3.0  
**Commit:** 1fdbc5c

### Planning Documents
- **ROUTE_NAMING_EPIC.md** - Segment-based route naming specification
- **INCREMENTAL_ANALYSIS_GUIDE.md** - Incremental analysis implementation

### Key Features
- Segment-based route naming system
- Repository organization (scripts and plans folders)
- Technical documentation updates
- Issue tracking improvements

---

## Release v2.4.0 - P1 Sprint: Testing, Long Rides & Core Features

**Date:** TBD (⛔ BLOCKED - Awaiting Geocoding Completion)
**Tag:** v2.4.0 (Draft)
**Status:** 🔴 BLOCKED

### Planning Documents
- **BLOCKED_UNTIL_GEOCODING_COMPLETE.md** - Release blocker documentation
- **README.md** - Quick reference guide

### Blocker Details
This release is **BLOCKED** until background geocoding completes. Background geocoding (implemented 2026-03-27) must finish populating the geocoding cache before v2.4.0 work can begin.

**Reason:** Route naming affects test data, test scenarios, and integration tests.

**How to Check:** Run `cat cache/geocoding_progress.txt` and look for "✅ GEOCODING COMPLETE!"

### Planned Features (When Unblocked)

#### Testing & Quality Assurance
- Issue #41: Create unit tests for core modules (31% → 80% coverage)
- Issue #42: Write integration tests for full workflow (expand scenarios)

#### Long Rides Feature (Epic #57)
- Issue #6: Add top 10 longest rides table with Strava links
- Issue #7: Add monthly ride statistics breakdown
- Issue #8: Add average speed and elevation gain metrics
- Issue #9: Add interactive map showing all long ride routes

#### Core Features
- Issue #70: Implement wind-aware route selection in forecast generator
- Issue #54: Weather Dashboard Implementation (Epic)
- Issue #33: Add traffic pattern analysis
- Issue #34: Add carbon footprint calculations
- Issue #25: Implement automatic token refresh for expired Strava tokens
- Issue #47: Add Side-by-Side Route Comparison Feature

---

## Document Index by Type

### Architecture & Design
- v2.1.0/DESIGN_PRINCIPLES.md - Design system
- v2.2.0/CACHE_SEPARATION_IMPLEMENTATION.md - Cache architecture

### Feature Specifications
- v1.0.0/LONG_RIDE_RECOMMENDATIONS.md - Long rides feature
- v2.1.0/UIUX_IMPROVEMENTS_EPIC.md - UI/UX redesign
- v2.3.0/ROUTE_NAMING_EPIC.md - Route naming system

### Implementation Plans
- v2.1.0/P1_ISSUES_IMPLEMENTATION_PLAN.md - P1 issues
- v2.2.0/TEST_REMEDIATION_PLAN.md - Test suite fixes

### Technical Documentation
- v1.0.0/ROUTE_MATCHING_EXPLANATION.md - Fréchet distance
- v1.0.0/ROUTE_SIMILARITY_OUTLIER_TOLERANCE.md - Route matching
- v2.3.0/INCREMENTAL_ANALYSIS_GUIDE.md - Incremental analysis

### Project Management
- v0.1.0/PLAN.md - Original project plan
- v0.1.0/WORKFLOW.md - Development workflow
- v2.4.0/BLOCKED_UNTIL_GEOCODING_COMPLETE.md - Release blocker documentation

---

## Usage Guidelines

### For Developers
1. **Starting New Work**: Check the latest release folder for current planning documents
2. **Creating New Plans**: Place in the appropriate release folder based on target version
3. **Referencing Old Plans**: Use the release version to find historical context

### For Documentation
1. **Release Notes**: See `/HISTORICAL_RELEASES.md` for comprehensive release history
2. **Time Tracking**: See `/TIME_TRACKING_v*.md` files for development time analysis
3. **Technical Specs**: See `/TECHNICAL_SPEC.md` for current system architecture

---

## Release Timeline

| Version | Date | Type | Planning Docs | Key Focus |
|---------|------|------|---------------|-----------|
| v0.1.0 | Mar 11-12 | Initial | 2 docs | Foundation & Core Features |
| v1.0.0 | Mar 12-13 | Major | 3 docs | Long Rides & Security |
| v2.0.0 | Mar 24 | Major | 0 docs | Rapid Feature Development |
| v2.1.0 | Mar 26 | Minor | 3 docs | Code Quality & Design |
| v2.2.0 | Mar 26 | Minor | 2 docs | Testing & Architecture |
| v2.3.0 | Mar 26 | Minor | 2 docs | Route Naming & Organization |
| v2.4.0 | TBD | Minor | 2 docs | ⛔ BLOCKED - P1 Sprint (Testing, Long Rides, Core Features) |

**Total Planning Documents:** 13 documents across 7 releases

---

## Related Documentation

- **HISTORICAL_RELEASES.md** - Comprehensive release notes for all versions
- **RELEASE_NOTES.md** - Current release notes
- **TIME_TRACKING.md** - Development time analysis
- **TECHNICAL_SPEC.md** - System architecture and specifications
- **ISSUE_PRIORITIES.md** - Current issue priorities and roadmap

---

*Last Updated: March 27, 2026*
*Organization Structure: Release-based planning document archive*