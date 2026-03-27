# UI/UX P1 Improvements

**Priority:** P1  
**Epic:** UI/UX Enhancements  
**Created:** 2026-03-27  
**Status:** Ready for Implementation

---

## Overview

This document tracks critical UI/UX improvements identified for the route comparison table and map visualization. These improvements will enhance usability, fix bugs, and ensure adherence to design principles.

---

## Issues to Address

### 1. Table Sorting Functionality
**Priority:** P1  
**Component:** Route Comparison Table  
**File:** `templates/report_template.html` (lines 515-600)

**Problem:**  
Table headers are not sortable. Users cannot sort routes by different criteria (score, duration, distance, uses).

**Requirements:**
- Add click handlers to table headers (`<th>` elements)
- Implement sorting for all columns:
  - Rank (numeric)
  - Route Name (alphabetic)
  - Score (numeric, descending default)
  - Duration (numeric)
  - Distance (numeric)
  - Uses/Frequency (numeric)
  - Wind (by favorability: favorable > neutral > unfavorable)
- Add visual indicators (↑↓ arrows) to show current sort column and direction
- Maintain pagination after sorting
- Preserve filter state when sorting

**Design Adherence:**
- Use semantic colors for sort indicators (primary color `#667eea`)
- Smooth transitions (0.2s) for visual feedback
- Touch-friendly click targets (44x44px minimum)

**Implementation Notes:**
- Add JavaScript sorting function in `<script>` section
- Store original data order for reset functionality
- Update pagination counts after sorting

---

### 2. Route Group Name Display Issue
**Priority:** P1  
**Component:** Route Naming System  
**Files:** 
- `src/route_analyzer.py` (RouteGroup dataclass, lines 52-61)
- `src/visualizer.py` (generate_map method, lines 302-308)
- `src/report_generator.py` (_prepare_context method, lines 350-374)

**Problem:**  
New route group names are not displaying correctly in the table. Investigation needed to determine why `route['name']` may be showing route IDs instead of human-readable names.

**Investigation Steps:**
1. Verify `RouteNamer.generate_simple_name()` is being called correctly
2. Check if `route_names` dictionary is properly populated in visualizer
3. Confirm names are passed through report generator context
4. Verify template is accessing the correct field (`route['name']`)

**Requirements:**
- Ensure all route groups have human-readable names
- Names should follow format: "Route 1", "Route 2", etc. (or custom names if configured)
- Verify names persist through cache serialization/deserialization
- Add logging to track name generation and assignment

**Files to Check:**
- `src/route_namer.py` - Name generation logic
- `src/route_analyzer.py` - RouteGroup.name field (line 59)
- `src/visualizer.py` - Name assignment (lines 302-308, 323-327)
- `src/report_generator.py` - Context preparation (lines 352, 369)
- `templates/report_template.html` - Name display (line 534)

---

### 3. Polyline Color Assignment Review
**Priority:** P1  
**Component:** Map Visualization  
**Files:**
- `src/visualizer.py` (lines 294-327)
- `plans/v2.1.0/DESIGN_PRINCIPLES.md` (lines 110-116)

**Problem:**  
Need to verify polyline colors follow design principles and are assigned consistently.

**Current Implementation:**
```python
# From visualizer.py lines 294-297
optimal_color = config.get('visualization.colors.optimal', '#FF0000')  # Red
alternative_colors = config.get('visualization.colors.alternative',
                                ['#00FF00', '#0000FF', '#FFA500', '#800080'])
```

**Design Principles Requirement (lines 110-116):**
- Route 1 (Primary): `#28a745` (green)
- Route 2: `#dc3545` (red)
- Route 3: `#007bff` (blue)
- Route 4: `#ffc107` (yellow)
- Unselected: `#808080` at 40% opacity

**Issues:**
1. Default optimal color is `#FF0000` (pure red) instead of semantic red `#dc3545`
2. Alternative colors don't match design principles (using pure green `#00FF00` instead of `#28a745`)
3. Color order doesn't follow semantic meaning (green should be optimal/first)

**Requirements:**
- Update default colors in config to match design principles
- Optimal route should use green (`#28a745`) as it represents "success/optimal"
- Alternative routes should use semantic colors in order: red, blue, yellow
- Ensure colors meet WCAG AA contrast requirements
- Add comments explaining color choices based on design principles

**Implementation:**
```python
# Proposed fix
optimal_color = config.get('visualization.colors.optimal', '#28a745')  # Green (success)
alternative_colors = config.get('visualization.colors.alternative',
                                ['#dc3545', '#007bff', '#ffc107', '#6c757d'])  # Red, Blue, Yellow, Grey
```

---

### 4. Remove "View on Strava" Button, Use Route Name as Link
**Priority:** P1  
**Component:** Route Comparison Table  
**File:** `templates/report_template.html` (lines 531-596)

**Problem:**  
Table has a separate "View on Strava" button column. Design should use the route name itself as a clickable link to Strava.

**Current Implementation:**
- Line 533-535: Route name with click handler
- Lines 585-596: Separate "View on Strava" button column

**Requirements:**
- Remove entire "View on Strava" column (lines 585-596)
- Remove `<th>View on Strava</th>` from header (line 518)
- Keep route name as clickable link (already implemented at line 533)
- Add visual indicator that name is clickable (underline on hover, external link icon)
- Maintain Strava icon/branding in the link styling

**Design Adherence:**
- Use primary color (`#667eea`) for link
- Add hover state with darker shade (`#764ba2`)
- Include external link icon (↗) or Strava icon next to name
- Ensure touch-friendly click target (44x44px)

**Implementation:**
```html
<!-- Proposed change for route name cell -->
<td>
    <span class="route-color-indicator" style="..."></span>
    {% if route['strava_url'] %}
    <a href="{{ route['strava_url'] }}" target="_blank" class="route-name-link" 
       style="color: #667eea; text-decoration: none; font-weight: 600;"
       title="View on Strava">
        {{ route['name'] }}
        <svg style="width: 14px; height: 14px; margin-left: 4px; vertical-align: middle;">
            <!-- External link icon -->
        </svg>
    </a>
    {% else %}
    <strong>{{ route['name'] }}</strong>
    {% endif %}
    <!-- Plus badge remains -->
</td>
```

---

### 5. Clickable "Uses" Column to Show Matched Routes
**Priority:** P1  
**Component:** Route Comparison Table  
**File:** `templates/report_template.html` (line 553)

**Problem:**  
"Uses" column shows frequency count but doesn't allow users to see which specific activities matched this route.

**Requirements:**
- Make "Uses" count clickable
- On click, show modal/popover with list of matched activities
- Display for each matched activity:
  - Date
  - Duration
  - Distance
  - Link to Strava activity
- Sort activities by date (most recent first)
- Add visual indicator that count is clickable (underline, cursor pointer)

**Design Adherence:**
- Use primary color for clickable count
- Modal should follow existing modal patterns (centered, backdrop, close button)
- Use card styling for activity list items
- Ensure mobile-friendly (scrollable list, touch targets)

**Implementation:**
```html
<!-- In table cell -->
<td>
    <span class="uses-count" 
          style="cursor: pointer; color: #667eea; text-decoration: underline;"
          onclick="showMatchedRoutes('{{ route['group'].id }}')"
          title="Click to view matched activities">
        {{ route['group'].frequency }}
    </span>
</td>

<!-- Modal template -->
<div id="matchedRoutesModal" class="modal">
    <div class="modal-content">
        <h4>Matched Activities for <span id="routeNameDisplay"></span></h4>
        <div id="matchedRoutesList">
            <!-- Populated by JavaScript -->
        </div>
    </div>
</div>
```

**Data Requirements:**
- Pass route group activities to template context
- Include activity metadata: id, date, duration, distance, strava_url
- Store in data attribute or JavaScript variable for access

---

### 6. Fix Page Counter Display
**Priority:** P1  
**Component:** Pagination Controls  
**File:** `templates/report_template.html` (line 511)

**Problem:**  
Page counter shows "Page 1 of _" with underscore instead of total page count.

**Current Code:**
```html
<span id="pageInfo">Page 1 of <span id="totalPages">1</span></span>
```

**Investigation:**
- Check JavaScript pagination controller (lines 906-950)
- Verify `totalPages` calculation and DOM update
- Check if filters affect page count calculation

**Requirements:**
- Display correct total page count on load
- Update total pages when filters are applied
- Format: "Page X of Y" (e.g., "Page 1 of 3")
- Ensure count updates when routes are filtered

**Implementation Check:**
- Line 908: `const totalPages = Math.ceil(visibleRows.length / rowsPerPage);`
- Line 911: `document.getElementById('totalPages').textContent = totalPages;`
- Verify this code is executing on page load and after filter changes

---

### 7. Simplify Route Counter Display
**Priority:** P1  
**Component:** Pagination Controls  
**File:** `templates/report_template.html` (line 512)

**Problem:**  
Route counter shows "Showing 1-10 of X routes" which is redundant with pagination.

**Current Code:**
```html
<span class="ms-3">Showing <span id="showingCount">0</span> of <span id="totalCount">{{ ranked_routes|length }}</span> routes</span>
```

**Requirements:**
- Simplify to show only total count: "X routes"
- Remove "Showing 1-10 of" portion
- Keep count dynamic (updates with filters)
- Format: "24 routes" or "1 route" (singular/plural)

**Proposed Change:**
```html
<span class="ms-3">
    <span id="totalCount">{{ ranked_routes|length }}</span> 
    <span id="routeLabel">route{{ 's' if ranked_routes|length != 1 else '' }}</span>
</span>
```

**JavaScript Update:**
- Update `updateCounts()` function to handle singular/plural
- Remove `showingCount` updates
- Keep `totalCount` updates for filter changes

---

## Implementation Plan

### Phase 1: Bug Fixes (Immediate)
1. Fix page counter display (#6)
2. Investigate and fix route name display (#2)
3. Simplify route counter (#7)

### Phase 2: Color System Alignment (High Priority)
4. Review and update polyline colors (#3)
5. Update config defaults to match design principles

### Phase 3: Feature Enhancements (Medium Priority)
6. Add table sorting functionality (#1)
7. Remove "View on Strava" button, enhance route name link (#4)
8. Add clickable "Uses" column with matched routes modal (#5)

---

## Testing Requirements

### Functional Testing
- [ ] Table sorting works for all columns
- [ ] Sort direction toggles correctly
- [ ] Pagination persists after sorting
- [ ] Filters work with sorting
- [ ] Route names display correctly
- [ ] Colors match design principles
- [ ] Route name links to Strava
- [ ] Uses count shows matched activities
- [ ] Page counter shows correct total
- [ ] Route counter shows correct format

### Visual Testing
- [ ] Colors meet WCAG AA contrast requirements
- [ ] Touch targets are 44x44px minimum
- [ ] Hover states work correctly
- [ ] Transitions are smooth (0.2s)
- [ ] Mobile layout works correctly
- [ ] Modal displays properly on all screen sizes

### Cross-Browser Testing
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (macOS/iOS)
- [ ] Mobile browsers (iOS Safari, Chrome Android)

---

## Design Principle Compliance

All changes must adhere to:
- **Mobile-First Approach** (Design Principles §1)
- **Semantic Color System** (Design Principles §4)
- **Touch-Optimized Interactions** (Design Principles §5)
- **Map Clarity & Readability** (Design Principles §6)
- **Consistent Patterns** (Design Principles §10)

Reference: `plans/v2.1.0/DESIGN_PRINCIPLES.md`

---

## Related Files

### Templates
- `templates/report_template.html` - Main report template

### Source Code
- `src/visualizer.py` - Map generation and color assignment
- `src/route_analyzer.py` - Route grouping and naming
- `src/report_generator.py` - Report context preparation
- `src/route_namer.py` - Route name generation

### Configuration
- `config/config.yaml` - Visualization color settings

### Documentation
- `plans/v2.1.0/DESIGN_PRINCIPLES.md` - Design system reference

---

## Success Criteria

- [ ] All 7 issues resolved
- [ ] All tests passing
- [ ] Design principles compliance verified
- [ ] User testing completed with positive feedback
- [ ] Documentation updated
- [ ] No regressions in existing functionality

---

## Notes

- Consider adding keyboard shortcuts for table sorting (e.g., Shift+Click for multi-column sort)
- Future enhancement: Save user's preferred sort order in localStorage
- Consider adding export functionality for sorted/filtered table data
- May want to add route comparison feature (select multiple routes to compare side-by-side)

---

*Last Updated: 2026-03-27*