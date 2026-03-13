#!/usr/bin/env python3
"""
Find routes that were matched using Hausdorff-only algorithm,
then compare with Hausdorff+Fréchet.
"""

import json
import numpy as np
import polyline
from pathlib import Path
from scipy.spatial.distance import directed_hausdorff

try:
    import similaritymeasures
    FRECHET_AVAILABLE = True
except ImportError:
    FRECHET_AVAILABLE = False

def calculate_hausdorff_similarity(coords1, coords2):
    """Calculate similarity using Hausdorff distance only."""
    dist_forward = directed_hausdorff(coords1, coords2)[0]
    dist_backward = directed_hausdorff(coords2, coords1)[0]
    max_dist = max(dist_forward, dist_backward)
    normalized_dist = max_dist * 111000
    distance_threshold = 200
    similarity = 1 / (1 + normalized_dist / distance_threshold)
    return similarity, normalized_dist

def calculate_frechet_similarity(coords1, coords2):
    """Calculate similarity using Fréchet distance."""
    if not FRECHET_AVAILABLE:
        return None, None
    try:
        frechet_dist = similaritymeasures.frechet_dist(coords1, coords2)
        normalized_dist = frechet_dist * 111000
        distance_threshold = 300
        similarity = 1 / (1 + normalized_dist / distance_threshold)
        return similarity, normalized_dist
    except Exception as e:
        return None, None

# Load cached activities
cache_file = Path('data/cache/activities.json')
with open(cache_file, 'r') as f:
    cache_data = json.load(f)

activities = cache_data['activities']

# Filter for commute activities with polylines
commute_keywords = ['work', 'commute', 'to work', 'from work']
commute_activities = []

for activity in activities:
    name_lower = activity['name'].lower()
    if any(keyword in name_lower for keyword in commute_keywords):
        if activity.get('polyline') and 10000 < activity['distance'] < 25000:
            commute_activities.append(activity)

print(f"Found {len(commute_activities)} commute activities")
print("\n" + "="*80)
print("FINDING ROUTES THAT MATCH WITH HAUSDORFF (≥0.70)")
print("="*80)

# Find pairs that match with Hausdorff
matched_pairs = []
comparison_count = 0

for i in range(len(commute_activities)):
    for j in range(i+1, len(commute_activities)):
        act1 = commute_activities[i]
        act2 = commute_activities[j]
        
        # Only compare similar distance routes
        dist_ratio = min(act1['distance'], act2['distance']) / max(act1['distance'], act2['distance'])
        if dist_ratio < 0.85:
            continue
        
        try:
            coords1 = np.array(polyline.decode(act1['polyline']))
            coords2 = np.array(polyline.decode(act2['polyline']))
            
            h_sim, h_dist = calculate_hausdorff_similarity(coords1, coords2)
            
            # If Hausdorff says they match (≥0.70)
            if h_sim >= 0.70:
                f_sim, f_dist = calculate_frechet_similarity(coords1, coords2)
                
                if f_sim is not None:
                    combined = np.sqrt(h_sim * f_sim)
                    
                    matched_pairs.append({
                        'act1': act1,
                        'act2': act2,
                        'h_sim': h_sim,
                        'h_dist': h_dist,
                        'f_sim': f_sim,
                        'f_dist': f_dist,
                        'combined': combined,
                        'coords1': coords1,
                        'coords2': coords2
                    })
            
            comparison_count += 1
            
        except Exception as e:
            continue

print(f"\nCompared {comparison_count} route pairs")
print(f"Found {len(matched_pairs)} pairs that match with Hausdorff (≥0.70)")
print("\n" + "="*80)

# Show the matched pairs
for idx, pair in enumerate(matched_pairs[:10]):  # Show first 10
    act1 = pair['act1']
    act2 = pair['act2']
    
    print(f"\n--- Matched Pair {idx + 1} ---")
    print(f"Route 1: {act1['name'][:60]}")
    print(f"         ID: {act1['id']} - https://www.strava.com/activities/{act1['id']}")
    print(f"         Date: {act1['start_date'][:10]} - {act1['distance']:.0f}m")
    print(f"Route 2: {act2['name'][:60]}")
    print(f"         ID: {act2['id']} - https://www.strava.com/activities/{act2['id']}")
    print(f"         Date: {act2['start_date'][:10]} - {act2['distance']:.0f}m")
    
    print(f"\nHausdorff:  {pair['h_sim']:.4f} (dist: {pair['h_dist']:.1f}m) → GROUP ✓")
    print(f"Fréchet:    {pair['f_sim']:.4f} (dist: {pair['f_dist']:.1f}m) → {'GROUP ✓' if pair['f_sim'] >= 0.70 else 'SEPARATE ✗'}")
    print(f"Combined:   {pair['combined']:.4f} → {'GROUP ✓' if pair['combined'] >= 0.70 else 'SEPARATE ✗'}")
    
    # Check for disagreement
    if pair['f_sim'] < 0.70 or pair['combined'] < 0.70:
        print(f"\n⚠️  DISAGREEMENT DETECTED!")
        if pair['f_sim'] < 0.70:
            print(f"   Hausdorff says GROUP, but Fréchet says SEPARATE")
            print(f"   → Fréchet detected a path difference (routes follow different paths)")
        if pair['combined'] < 0.70:
            print(f"   Combined metric says SEPARATE (geometric mean requires both to agree)")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

if matched_pairs:
    disagreements = sum(1 for p in matched_pairs if p['f_sim'] < 0.70 or p['combined'] < 0.70)
    print(f"Total Hausdorff matches: {len(matched_pairs)}")
    print(f"Disagreements with Fréchet/Combined: {disagreements}")
    print(f"Agreement rate: {(len(matched_pairs) - disagreements) / len(matched_pairs) * 100:.1f}%")
    
    if disagreements > 0:
        print(f"\n⚠️  {disagreements} route pairs that Hausdorff grouped would be separated by the combined algorithm")
        print("   This suggests the combined algorithm is more selective and may produce better groupings")
else:
    print("No routes matched with Hausdorff ≥0.70 threshold")
    print("This might mean:")
    print("  - Routes are genuinely different")
    print("  - Threshold is too strict")
    print("  - Need more commute data")

# Made with Bob
