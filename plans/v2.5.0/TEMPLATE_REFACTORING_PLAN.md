# Report Template Refactoring Plan

## Problem Statement

The `templates/report_template.html` file has grown to **3,293 lines** (168KB), with **~2,252 lines of JavaScript** (68% of the file). This creates several issues:

1. **Maintainability**: Hard to navigate and modify
2. **Performance**: Large inline scripts slow initial page load
3. **Code Organization**: JavaScript logic mixed with HTML structure
4. **Testing**: Inline JavaScript is difficult to unit test
5. **Caching**: Browser can't cache JavaScript separately from HTML
6. **IDE Performance**: Large files slow down editor features

## Current Structure

The template contains 3 major script blocks:

1. **Lines 356-840**: Chart.js initialization for monthly statistics (~485 lines)
2. **Lines 841-2107**: Commute routes map and filtering logic (~1,267 lines)
3. **Lines 2108-3293**: Long Rides recommendations feature (~1,185 lines)

## Proposed Solution

### Phase 1: Extract JavaScript to Separate Files

Create a new `templates/static/js/` directory with modular JavaScript files:

```
templates/static/js/
├── chart-utils.js          # Chart.js initialization and utilities
├── map-utils.js            # Leaflet map initialization helpers
├── commute-routes.js       # Commute routes filtering and display
├── long-rides.js           # Long Rides recommendations feature
└── main.js                 # Initialization and coordination
```

### Phase 2: Update Template Structure

Modify `report_template.html` to:
1. Include external JavaScript files at end of body
2. Pass data via `<script type="application/json">` blocks
3. Keep only minimal inline initialization code

### Phase 3: Add Build Process (Optional)

Consider adding a simple build step to:
- Minify JavaScript for production
- Bundle related modules
- Generate source maps for debugging

## Benefits

1. **Better Organization**: Each feature in its own file
2. **Easier Testing**: Can unit test JavaScript modules
3. **Improved Performance**: Browser caching of static JS files
4. **Better IDE Support**: Smaller files, better autocomplete
5. **Easier Collaboration**: Clearer separation of concerns

## Implementation Priority

**Priority:** P2 (Technical Debt)
**Estimated Effort:** 4-6 hours
**Risk:** Medium (requires careful testing of all interactive features)

## Related Issues

- Template size makes it difficult to add new features
- JavaScript errors are harder to debug in inline scripts
- No way to reuse code between different report sections

## Notes

- This refactoring should not change any user-facing functionality
- All existing features must continue to work identically
- Consider this for v2.7.0 or later when time permits
- Could be done incrementally (one script block at a time)