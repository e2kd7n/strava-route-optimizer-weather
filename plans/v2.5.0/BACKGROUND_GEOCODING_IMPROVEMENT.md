# Background Geocoding with Progressive Report Updates

## Issue
Currently, geocoding runs synchronously during analysis, which means users must wait for all geocoding to complete before viewing their report. This can take 3-4 minutes for 200+ routes.

## Proposed Solution
Implement a hybrid approach that provides immediate results while geocoding continues in the background:

### Phase 1: Immediate Report Generation
1. Generate initial report using cached geocoded names where available
2. Use temporary names (e.g., "Route 1 to Work") for routes not yet geocoded
3. Add a banner/notice to the report indicating geocoding is in progress
4. Display estimated completion time based on remaining routes

### Phase 2: Background Geocoding
1. Start background thread to geocode remaining routes
2. Respect 1.1 second rate limit to prevent Nominatim blocking
3. Update route groups cache as geocoding progresses
4. Log progress to a file that can be monitored

### Phase 3: Report Regeneration
1. When background geocoding completes, automatically regenerate the report
2. Replace temporary names with geocoded names
3. Remove the "geocoding in progress" banner
4. Optionally notify user (desktop notification or terminal message)

## Benefits
- **Immediate feedback**: Users can view their report within seconds
- **No waiting**: Geocoding happens in the background
- **Progressive enhancement**: Report improves as geocoding completes
- **Better UX**: Users aren't blocked by a 3-4 minute wait

## Implementation Details

### Report Banner
Add to HTML template when geocoding is active:
```html
<div class="geocoding-notice">
  ⏳ Route names are being geocoded in the background...
  <br>
  Progress: X/Y routes (estimated Z minutes remaining)
  <br>
  This report will be automatically updated when geocoding completes.
</div>
```

### Cache Strategy
1. Save route groups cache immediately with whatever names are available
2. Background thread updates cache as it geocodes
3. Use file locking to prevent race conditions
4. Atomic writes to prevent corruption

### Progress Tracking
- Maintain `geocoding_status.json` with:
  - Total routes to geocode
  - Routes completed
  - Estimated time remaining
  - Start time
  - Status (in_progress, completed, failed)

### Report Regeneration
- After geocoding completes, call report generator again
- Use same data but with updated route names
- Overwrite the original report file
- Log completion message

## Technical Considerations

### Thread Safety
- Use locks when updating shared route group objects
- Atomic file writes for cache updates
- Handle race conditions between main thread and geocoding thread

### Error Handling
- If geocoding fails, keep temporary names
- Log errors but don't crash the background thread
- Implement retry logic with exponential backoff
- Create rate limit block file if Nominatim blocks IP

### Rate Limiting
- Maintain 1.1 second delay between API requests
- Track API call timestamps
- Implement circuit breaker if too many failures

### User Experience
- Show progress in terminal if user is still watching
- Desktop notification when geocoding completes (optional)
- Clear messaging about what's happening
- Don't regenerate report if user has closed terminal

## Priority
**P2** - Enhancement for better UX, but current synchronous approach works

## Estimated Effort
- 4-6 hours implementation
- 2 hours testing
- 1 hour documentation

## Related Files
- `src/route_analyzer.py` - Main analysis logic
- `src/route_namer.py` - Geocoding implementation
- `src/report_generator.py` - HTML report generation
- `templates/report_template.html` - Report template

## Success Criteria
1. Users can view report within 10 seconds of running `--analyze`
2. Background geocoding completes without user intervention
3. Report is automatically updated with geocoded names
4. No race conditions or cache corruption
5. Rate limiting prevents IP blocks
6. Clear progress indication for users

## Notes
- Current synchronous approach was implemented to fix cache persistence issue
- Background geocoding was previously implemented but didn't save names to cache
- This enhancement would restore background geocoding with proper cache updates
- Consider making this behavior configurable (sync vs async geocoding)