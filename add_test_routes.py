#!/usr/bin/env python3
"""Add test routes from saved coordinate files to visualizer and report generator."""

import json

# Load the coordinate files
with open('test_route_9458631701_coords.json', 'r') as f:
    route1 = json.load(f)

with open('test_route_11551867398_coords.json', 'r') as f:
    route2 = json.load(f)

# Sample coordinates to reduce size (every 10th point)
route1_sampled = route1['coordinates'][::10]
route2_sampled = route2['coordinates'][::10]

print("Route 1 (Four States Ferry):")
print(f"  Original points: {len(route1['coordinates'])}")
print(f"  Sampled points: {len(route1_sampled)}")
print(f"  Distance: {route1['distance']/1000:.1f} km")
print(f"  Elevation: {route1['elevation_gain']:.0f} m")
print()

print("Route 2 (Unbound 200):")
print(f"  Original points: {len(route2['coordinates'])}")
print(f"  Sampled points: {len(route2_sampled)}")
print(f"  Distance: {route2['distance']/1000:.1f} km")
print(f"  Elevation: {route2['elevation_gain']:.0f} m")
print()

# Generate Python code for visualizer.py
print("=" * 60)
print("Add this to visualizer.py (replace test_nyc and test_sf):")
print("=" * 60)
print()
print(f"        # Real Strava test routes for zoom testing")
print(f"        route_data['route-test_ferry'] = {{")
print(f"            'bounds': {route1_sampled},")
print(f"            'name': 'TEST: Four States Ferry (267km)',")
print(f"            'direction': 'test'")
print(f"        }}")
print(f"        route_data['route-test_unbound'] = {{")
print(f"            'bounds': {route2_sampled},")
print(f"            'name': 'TEST: Unbound 200 (327km)',")
print(f"            'direction': 'test'")
print(f"        }}")
print()

# Generate Python code for report_generator.py
print("=" * 60)
print("Add this to report_generator.py (replace test_nyc and test_sf):")
print("=" * 60)
print()
print(f"        # Real Strava test routes")
print(f"        test_routes = [")
print(f"            {{")
print(f"                'route_id': 'test_ferry',")
print(f"                'name': 'TEST: Four States Ferry (267km)',")
print(f"                'direction': 'test',")
print(f"                'frequency': 1,")
print(f"                'avg_distance': {route1['distance']},")
print(f"                'avg_speed': 8.1,")
print(f"                'avg_moving_time': {route1['distance'] / 8.1},")
print(f"                'avg_elevation': {route1['elevation_gain']},")
print(f"                'consistency_score': 1.0,")
print(f"                'score': 50.0")
print(f"            }},")
print(f"            {{")
print(f"                'route_id': 'test_unbound',")
print(f"                'name': 'TEST: Unbound 200 (327km)',")
print(f"                'direction': 'test',")
print(f"                'frequency': 1,")
print(f"                'avg_distance': {route2['distance']},")
print(f"                'avg_speed': 7.1,")
print(f"                'avg_moving_time': {route2['distance'] / 7.1},")
print(f"                'avg_elevation': {route2['elevation_gain']},")
print(f"                'consistency_score': 1.0,")
print(f"                'score': 50.0")
print(f"            }}")
print(f"        ]")

# Made with Bob
