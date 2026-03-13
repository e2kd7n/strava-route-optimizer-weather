#!/usr/bin/env python3
"""
Analyze the GPS point resolution in route polylines.
"""

import json
import polyline
from pathlib import Path
from geopy.distance import geodesic

# Load cached activities
cache_file = Path('data/cache/activities.json')
with open(cache_file, 'r') as f:
    cache_data = json.load(f)

activities = cache_data['activities']

# Find activities with polylines
activities_with_polylines = [a for a in activities if a.get('polyline')]

print(f"Found {len(activities_with_polylines)} activities with polylines")
print("\n" + "="*70)

# Analyze first few activities
for i, activity in enumerate(activities_with_polylines[:3]):
    print(f"\n--- Activity {i+1}: {activity['name']} ---")
    print(f"Distance: {activity['distance']:.0f} meters")
    print(f"Duration: {activity['moving_time']} seconds")
    
    # Decode polyline
    try:
        coords = polyline.decode(activity['polyline'])
        print(f"Number of GPS points: {len(coords)}")
        
        # Calculate distances between consecutive points
        distances = []
        for j in range(len(coords) - 1):
            dist = geodesic(coords[j], coords[j+1]).meters
            distances.append(dist)
        
        if distances:
            avg_dist = sum(distances) / len(distances)
            min_dist = min(distances)
            max_dist = max(distances)
            
            print(f"\nPoint-to-point distances:")
            print(f"  Average: {avg_dist:.1f} meters")
            print(f"  Min: {min_dist:.1f} meters")
            print(f"  Max: {max_dist:.1f} meters")
            
            # Calculate time resolution
            time_per_point = activity['moving_time'] / len(coords)
            print(f"\nEstimated time per point: {time_per_point:.1f} seconds")
            
            # Show first 10 points
            print(f"\nFirst 10 GPS points:")
            for k in range(min(10, len(coords))):
                if k > 0:
                    dist_from_prev = geodesic(coords[k-1], coords[k]).meters
                    print(f"  {k}: {coords[k]} (Δ {dist_from_prev:.1f}m)")
                else:
                    print(f"  {k}: {coords[k]}")
    
    except Exception as e:
        print(f"Error decoding polyline: {e}")
    
    print("="*70)

# Overall statistics
print("\n\n=== OVERALL STATISTICS ===")
all_point_counts = []
all_avg_distances = []

for activity in activities_with_polylines[:20]:  # Sample 20 activities
    try:
        coords = polyline.decode(activity['polyline'])
        all_point_counts.append(len(coords))
        
        distances = []
        for j in range(len(coords) - 1):
            dist = geodesic(coords[j], coords[j+1]).meters
            distances.append(dist)
        
        if distances:
            all_avg_distances.append(sum(distances) / len(distances))
    except:
        pass

if all_point_counts:
    print(f"\nPoints per route (sample of {len(all_point_counts)} routes):")
    print(f"  Average: {sum(all_point_counts)/len(all_point_counts):.0f} points")
    print(f"  Min: {min(all_point_counts)} points")
    print(f"  Max: {max(all_point_counts)} points")

if all_avg_distances:
    print(f"\nAverage point-to-point distance:")
    print(f"  Overall average: {sum(all_avg_distances)/len(all_avg_distances):.1f} meters")
    print(f"  Min average: {min(all_avg_distances):.1f} meters")
    print(f"  Max average: {max(all_avg_distances):.1f} meters")

print("\n" + "="*70)

# Made with Bob
