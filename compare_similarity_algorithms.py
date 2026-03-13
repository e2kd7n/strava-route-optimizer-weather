#!/usr/bin/env python3
"""
Compare Hausdorff-only vs Hausdorff+Fréchet similarity algorithms.
"""

import json
import numpy as np
import polyline
from pathlib import Path
from scipy.spatial.distance import directed_hausdorff
from geopy.distance import geodesic

try:
    import similaritymeasures
    FRECHET_AVAILABLE = True
except ImportError:
    FRECHET_AVAILABLE = False
    print("WARNING: similaritymeasures not available")

def calculate_hausdorff_similarity(coords1, coords2):
    """Calculate similarity using Hausdorff distance only."""
    dist_forward = directed_hausdorff(coords1, coords2)[0]
    dist_backward = directed_hausdorff(coords2, coords1)[0]
    max_dist = max(dist_forward, dist_backward)
    normalized_dist = max_dist * 111000  # degrees to meters
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
        print(f"Fréchet calculation failed: {e}")
        return None, None

def calculate_combined_similarity(coords1, coords2):
    """Calculate combined similarity using both metrics."""
    hausdorff_sim, hausdorff_dist = calculate_hausdorff_similarity(coords1, coords2)
    frechet_sim, frechet_dist = calculate_frechet_similarity(coords1, coords2)
    
    if frechet_sim is not None:
        combined = np.sqrt(hausdorff_sim * frechet_sim)
        return combined, hausdorff_sim, frechet_sim, hausdorff_dist, frechet_dist
    else:
        return hausdorff_sim, hausdorff_sim, None, hausdorff_dist, None

# Load cached activities
cache_file = Path('data/cache/activities.json')
with open(cache_file, 'r') as f:
    cache_data = json.load(f)

activities = cache_data['activities']

# Get activities with polylines
activities_with_polylines = [a for a in activities if a.get('polyline')]
print(f"Found {len(activities_with_polylines)} activities with polylines")

# Compare first 10 pairs of routes
print("\n" + "="*80)
print("SIMILARITY COMPARISON: Hausdorff vs Hausdorff+Fréchet")
print("="*80)

comparison_count = 0
max_comparisons = 10

for i in range(len(activities_with_polylines)):
    if comparison_count >= max_comparisons:
        break
    
    for j in range(i+1, len(activities_with_polylines)):
        if comparison_count >= max_comparisons:
            break
        
        act1 = activities_with_polylines[i]
        act2 = activities_with_polylines[j]
        
        # Only compare similar distance routes (within 20%)
        dist_ratio = min(act1['distance'], act2['distance']) / max(act1['distance'], act2['distance'])
        if dist_ratio < 0.8:
            continue
        
        try:
            coords1 = np.array(polyline.decode(act1['polyline']))
            coords2 = np.array(polyline.decode(act2['polyline']))
            
            combined, hausdorff_sim, frechet_sim, h_dist, f_dist = calculate_combined_similarity(coords1, coords2)
            
            print(f"\n--- Comparison {comparison_count + 1} ---")
            print(f"Route 1: {act1['name'][:50]} ({act1['distance']:.0f}m)")
            print(f"         ID: {act1['id']} - https://www.strava.com/activities/{act1['id']}")
            print(f"         Date: {act1['start_date'][:10]}")
            print(f"Route 2: {act2['name'][:50]} ({act2['distance']:.0f}m)")
            print(f"         ID: {act2['id']} - https://www.strava.com/activities/{act2['id']}")
            print(f"         Date: {act2['start_date'][:10]}")
            print(f"\nHausdorff:")
            print(f"  Similarity: {hausdorff_sim:.4f}")
            print(f"  Distance:   {h_dist:.1f}m")
            print(f"  Would group (≥0.70)? {'YES' if hausdorff_sim >= 0.70 else 'NO'}")
            
            if frechet_sim is not None:
                print(f"\nFréchet:")
                print(f"  Similarity: {frechet_sim:.4f}")
                print(f"  Distance:   {f_dist:.1f}m")
                print(f"  Would group (≥0.70)? {'YES' if frechet_sim >= 0.70 else 'NO'}")
                
                print(f"\nCombined (geometric mean):")
                print(f"  Similarity: {combined:.4f}")
                print(f"  Would group (≥0.70)? {'YES' if combined >= 0.70 else 'NO'}")
                
                # Show if algorithms disagree
                h_group = hausdorff_sim >= 0.70
                f_group = frechet_sim >= 0.70
                c_group = combined >= 0.70
                
                if h_group != c_group:
                    print(f"\n  ⚠️  ALGORITHMS DISAGREE!")
                    if h_group and not c_group:
                        print(f"     Hausdorff says YES, Combined says NO")
                        print(f"     → Fréchet caught a path difference")
                    else:
                        print(f"     Hausdorff says NO, Combined says YES")
                        print(f"     → Unlikely with geometric mean")
            
            comparison_count += 1
            
        except Exception as e:
            print(f"Error comparing routes: {e}")
            continue

print("\n" + "="*80)
print(f"Compared {comparison_count} route pairs")
print("="*80)

if FRECHET_AVAILABLE:
    print("\n✅ Fréchet distance is available and working")
else:
    print("\n❌ Fréchet distance not available - install similaritymeasures")

# Made with Bob
