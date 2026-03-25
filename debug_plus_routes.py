#!/usr/bin/env python3
"""Debug script to analyze plus route detection."""

import json
import numpy as np
from pathlib import Path

# Load cached activities
cache_file = Path('data/cache/activities.json')
if not cache_file.exists():
    print("No activities cache found. Run: python3 main.py --fetch")
    exit(1)

with open(cache_file, 'r') as f:
    data = json.load(f)
    activities = data.get('activities', [])

print(f"Total activities: {len(activities)}")

# Filter commute activities
commute_keywords = ['commute', 'to work', 'from work', 'ride to work', 'ride home']
commutes = []
for activity in activities:
    name = activity.get('name', '').lower()
    if any(keyword in name for keyword in commute_keywords):
        commutes.append(activity)

print(f"Commute activities: {len(commutes)}")

# Separate by direction (simple heuristic based on name)
to_work = []
from_work = []

for activity in commutes:
    name = activity.get('name', '').lower()
    distance = activity.get('distance', 0) / 1000  # Convert to km
    
    if 'to work' in name or 'morning' in name:
        to_work.append({
            'id': activity.get('id'),
            'name': activity.get('name'),
            'distance': distance
        })
    elif 'from work' in name or 'home' in name or 'evening' in name:
        from_work.append({
            'id': activity.get('id'),
            'name': activity.get('name'),
            'distance': distance
        })

print(f"\nTo work activities: {len(to_work)}")
print(f"From work activities: {len(from_work)}")

# Analyze to work
if to_work:
    distances = [a['distance'] for a in to_work]
    median = np.median(distances)
    threshold = median * 1.15
    
    print(f"\n=== TO WORK ===")
    print(f"Median distance: {median:.2f}km")
    print(f"Plus route threshold (15%): {threshold:.2f}km")
    print(f"Min: {min(distances):.2f}km, Max: {max(distances):.2f}km")
    
    plus_routes = [a for a in to_work if a['distance'] > threshold]
    print(f"\nPlus routes: {len(plus_routes)}/{len(to_work)}")
    if plus_routes:
        print("\nPlus route examples:")
        for route in sorted(plus_routes, key=lambda x: x['distance'], reverse=True)[:5]:
            print(f"  {route['distance']:.2f}km - {route['name']}")

# Analyze from work
if from_work:
    distances = [a['distance'] for a in from_work]
    median = np.median(distances)
    threshold = median * 1.15
    
    print(f"\n=== FROM WORK ===")
    print(f"Median distance: {median:.2f}km")
    print(f"Plus route threshold (15%): {threshold:.2f}km")
    print(f"Min: {min(distances):.2f}km, Max: {max(distances):.2f}km")
    
    plus_routes = [a for a in from_work if a['distance'] > threshold]
    print(f"\nPlus routes: {len(plus_routes)}/{len(from_work)}")
    if plus_routes:
        print("\nPlus route examples:")
        for route in sorted(plus_routes, key=lambda x: x['distance'], reverse=True)[:5]:
            print(f"  {route['distance']:.2f}km - {route['name']}")
    
    # Show all from work routes sorted by distance
    print("\nAll from work routes (sorted by distance):")
    for route in sorted(from_work, key=lambda x: x['distance'], reverse=True):
        is_plus = "PLUS" if route['distance'] > threshold else ""
        print(f"  {route['distance']:.2f}km - {route['name']} {is_plus}")

# Made with Bob
