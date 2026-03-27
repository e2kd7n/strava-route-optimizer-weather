# v2.4.0 Planning Documents

## ⛔ STATUS: BLOCKED

**This release is currently BLOCKED and cannot proceed.**

See **BLOCKED_UNTIL_GEOCODING_COMPLETE.md** for full details.

---

## Release Scope: P1 Sprint

This release addresses all P1 (high priority) issues from ISSUE_PRIORITIES.md:

### Testing & Quality Assurance
- #41 - Create unit tests for core modules (31% → 80% coverage)
- #42 - Write integration tests for full workflow

### Long Rides Feature (Epic #57)
- #6 - Add top 10 longest rides table with Strava links
- #7 - Add monthly ride statistics breakdown
- #8 - Add average speed and elevation gain metrics
- #9 - Add interactive map showing all long ride routes

### Core Features
- #70 - Implement wind-aware route selection in forecast generator
- #54 - Weather Dashboard Implementation (Epic)
- #33 - Add traffic pattern analysis
- #34 - Add carbon footprint calculations
- #25 - Implement automatic token refresh for expired Strava tokens
- #47 - Add Side-by-Side Route Comparison Feature

---

## Documents in This Directory

- **BLOCKED_UNTIL_GEOCODING_COMPLETE.md** - Release blocker documentation with verification steps and complete sprint scope
- **README.md** - This file (quick reference)

---

## Quick Status Check

Run this command to check if geocoding is complete:

```bash
cat cache/geocoding_progress.txt
```

Look for: `✅ GEOCODING COMPLETE!`

---

## What Happens When Unblocked

Once geocoding completes:

1. Update blocker document status to UNBLOCKED
2. Update GitHub draft release to remove blocker
3. Begin v2.4.0 sprint work on all P1 issues
4. Create additional planning documents as needed (feature specs, implementation plans)
5. Track progress in ISSUE_PRIORITIES.md

---

## Related Documentation

- **GitHub Release:** https://github.com/e2kd7n/ride-optimizer/releases (v2.4.0 Draft)
- **Issue Tracking:** /ISSUE_PRIORITIES.md
- **Geocoding Implementation:** /BACKGROUND_GEOCODING_IMPLEMENTATION.md

---

*Created: 2026-03-27*
*Updated: 2026-03-27 (Added complete P1 scope)*