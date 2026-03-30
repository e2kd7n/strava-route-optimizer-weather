# Clickable "uses" Field Implementation Status

## Completed ✅

### Backend Changes
1. **`src/long_ride_analyzer.py`**
   - ✅ Added `activity_ids` field to `LongRide` dataclass
   - ✅ Added `activity_dates` field to `LongRide` dataclass
   - ✅ Updated `consolidate_named_groups()` to populate these fields with all activities
   - ✅ Hardware-aware parallel processing (2-6 workers)

2. **`src/api/long_rides_api.py`**
   - ✅ Added `activity_ids` and `activity_dates` to API response

3. **Testing**
   - ✅ Verified with "Old School" routes showing 40 activities with IDs and dates

## Still Needed 🔨

### Frontend Changes (templates/report_template.html)

The template already has infrastructure for clickable elements and modals (lines 2080-2100), but needs to be adapted for long rides:

1. **Add "Uses" column to consolidated routes display**
   - Need to find where consolidated routes are displayed (not the "Top 10" table)
   - Add a "Uses" column with clickable count
   - Style it to indicate it's clickable (cursor: pointer, underline on hover)

2. **Create modal function for activity list**
   - Similar to existing `showMatchedRoutes()` function
   - Display list of activities with:
     - Activity ID (link to Strava)
     - Date
     - Distance
     - Duration
   - Sort by date (most recent first)

3. **Wire up click handlers**
   - Attach click handler to uses count
   - Pass `activity_ids` and `activity_dates` to modal function
   - Fetch additional details if needed

## Where to Find Things

### Consolidated Routes Display
The consolidated routes with `uses` counts are likely in:
- Long Rides recommendations section (around line 3727)
- Uses `long_rides_geojson` variable
- Need to add table/list view showing consolidated routes

### Existing Modal Infrastructure
- Lines 2080-2100: Click handlers for uses-count
- Lines 2000-2050: Modal creation example
- Function `showMatchedRoutes()` exists but may need adaptation

## Implementation Plan

1. **Find/Create consolidated routes table**
   - Search for where `long_rides_geojson` is displayed in a table
   - If no table exists, create one showing consolidated routes
   - Add "Uses" column

2. **Make uses count clickable**
   ```html
   <td>
       <span class="uses-count clickable" 
             data-activity-ids="{{ ride.activity_ids|tojson }}"
             data-activity-dates="{{ ride.activity_dates|tojson }}"
             data-route-name="{{ ride.name }}">
           {{ ride.uses }}
       </span>
   </td>
   ```

3. **Add JavaScript modal function**
   ```javascript
   function showLongRideActivities(routeName, activityIds, activityDates) {
       // Create modal with list of activities
       // Link each to Strava: https://strava.com/activities/{id}
       // Show date, allow sorting
   }
   ```

4. **Add CSS for clickable style**
   ```css
   .uses-count.clickable {
       cursor: pointer;
       color: #667eea;
       text-decoration: underline;
       font-weight: bold;
   }
   .uses-count.clickable:hover {
       color: #764ba2;
   }
   ```

## Data Flow

```
Backend:
LongRideAnalyzer.consolidate_named_groups()
  → Creates LongRide with activity_ids=[...] and activity_dates=[...]
  → Passed to report_generator
  → Rendered in template as long_rides_geojson

Frontend:
User clicks on "uses: 21"
  → JavaScript reads data-activity-ids and data-activity-dates
  → Calls showLongRideActivities()
  → Creates modal with table of all 21 activities
  → Each activity links to Strava
```

## Next Steps

1. Search template for consolidated routes table
2. If not found, create one in the Long Rides tab
3. Add clickable uses column
4. Implement modal function
5. Test with real data

## Notes

- The backend is complete and working
- All data is available in the template
- Just needs frontend UI implementation
- Can reuse existing modal patterns from commute routes