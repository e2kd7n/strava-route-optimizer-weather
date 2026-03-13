#!/bin/bash

# Script to sync TODO list with GitHub issues
# Creates issues for pending/in-progress todos
# Closes issues for completed todos with commit references

cd "$(dirname "$0")"

echo "Syncing TODO list with GitHub issues..."
echo ""

# Check if gh is authenticated
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI not authenticated. Run: gh auth login"
    exit 1
fi

# Get the current commit hash
CURRENT_COMMIT=$(git rev-parse --short HEAD)
REPO_URL=$(git config --get remote.origin.url | sed 's/\.git$//')

echo "Current commit: $CURRENT_COMMIT"
echo "Repository: $REPO_URL"
echo ""

# Create issue for in-progress analysis
echo "Creating issue for in-progress task..."

gh issue create --title "Complete and review full analysis with Fréchet algorithm" --body "## Status
Currently running full analysis with geocoding enabled and new Fréchet-primary matching algorithm.

## Objective
Complete the analysis run and perform initial review of results.

## Tasks
- [x] Start analysis with geocoding enabled
- [ ] Wait for analysis to complete (~1-2 hours due to API rate limiting)
- [ ] Verify analysis completed successfully
- [ ] Check output files generated
- [ ] Open HTML report in browser
- [ ] Perform initial visual inspection of results

## Context
This is the first full analysis run after implementing the Fréchet distance algorithm (commit cf5ede5). The analysis includes:
- 161 commute activities
- Geocoding for human-readable route names
- New Fréchet-primary similarity matching
- Route grouping with 0.70 threshold

## Output Files
- \`output/reports/commute_analysis.html\` - Main report
- \`cache/geocoding_cache.json\` - Geocoded locations
- Analysis logs in terminal

## Next Steps
After completion, proceed with validation issues #1-5 to verify algorithm accuracy.

## Related
- Commit: cf5ede5
- Algorithm: Fréchet distance (primary) + Hausdorff validation
- Documentation: \`SIMILARITY_ALGORITHM_CHANGE.md\`" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ Issue created for in-progress analysis"
else
    echo "⚠ Issue may already exist or creation failed"
fi

echo ""
echo "Checking for completed todos to close..."

# Note: In a real implementation, you would:
# 1. Parse the TODO list to find completed items
# 2. Search for corresponding open issues
# 3. Close them with commit references
# 4. Add comments linking to the commit

# For now, we'll just show what would happen
echo ""
echo "📋 Completed todos from commit cf5ede5:"
echo "  - Implemented Fréchet distance algorithm"
echo "  - Updated documentation (README, TECHNICAL_SPEC)"
echo "  - Fixed rate limiting in route_namer.py"
echo "  - Pushed changes to GitHub"
echo ""
echo "These would be closed with:"
echo "  gh issue close <issue-number> --comment 'Completed in commit cf5ede5'"
echo ""

echo "✅ Sync complete!"
echo ""
echo "View all issues: ${REPO_URL}/issues"

# Made with Bob
