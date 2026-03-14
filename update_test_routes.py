#!/usr/bin/env python3
"""Update visualizer.py and report_generator.py with real Strava test routes."""

import json
import re
from pathlib import Path

# Security: Define allowed directory and whitelist of files to prevent path traversal
ALLOWED_DIR = Path(__file__).parent.resolve()
ALLOWED_FILES = [
    'test_route_9458631701_coords.json',
    'test_route_11551867398_coords.json'
]

def safe_open(filename, mode='r'):
    """
    Safely open a file with path validation to prevent code injection (CWE-94).
    
    Args:
        filename: Name of the file to open (must be in whitelist)
        mode: File open mode (default: 'r')
    
    Returns:
        File object
    
    Raises:
        ValueError: If file is outside allowed directory or not in whitelist
    """
    # Resolve the full path
    file_path = (ALLOWED_DIR / filename).resolve()
    
    # Check if file is in allowed directory (prevents path traversal)
    if not str(file_path).startswith(str(ALLOWED_DIR)):
        raise ValueError(f"Security: Access denied - {filename} is outside allowed directory")
    
    # Check if filename is in whitelist (defense in depth)
    if filename not in ALLOWED_FILES:
        raise ValueError(f"Security: Access denied - {filename} is not in allowed files list")
    
    return open(file_path, mode)

# Load the coordinate files using secure file opening
with safe_open('test_route_9458631701_coords.json', 'r') as f:
    route1 = json.load(f)

with safe_open('test_route_11551867398_coords.json', 'r') as f:
    route2 = json.load(f)

# Sample coordinates to reduce size (every 10th point)
route1_sampled = route1['coordinates'][::10]
route2_sampled = route2['coordinates'][::10]

print(f"Updating visualizer.py...")

# Read visualizer.py (using standard open for source files in src/ directory)
# Note: These are trusted source files, not user-provided data files
with open('src/visualizer.py', 'r') as f:
    visualizer_content = f.read()

# Create the new test routes code for visualizer
new_test_routes = f"""        # Real Strava test routes for zoom testing
        route_data['route-test_ferry'] = {{
            'bounds': {route1_sampled},
            'name': 'TEST: Four States Ferry (267km)',
            'direction': 'test'
        }}
        route_data['route-test_unbound'] = {{
            'bounds': {route2_sampled},
            'name': 'TEST: Unbound 200 (327km)',
            'direction': 'test'
        }}"""

# Replace the old test routes in visualizer.py
pattern = r"        # Add test routes with different locations to verify zoom functionality\s+route_data\['route-test_nyc'\] = \{[^}]+\}\s+route_data\['route-test_sf'\] = \{[^}]+\}"
visualizer_content = re.sub(pattern, new_test_routes, visualizer_content, flags=re.DOTALL)

# Write back (trusted source file)
with open('src/visualizer.py', 'w') as f:
    f.write(visualizer_content)

print(f"✓ Updated visualizer.py with {len(route1_sampled)} and {len(route2_sampled)} coordinate points")

print(f"\nUpdating report_generator.py...")

# Read report_generator.py (trusted source file)
with open('src/report_generator.py', 'r') as f:
    report_content = f.read()

# Create the new test routes code for report generator
new_report_routes = f"""        # Real Strava test routes
        test_routes = [
            {{
                'route_id': 'test_ferry',
                'name': 'TEST: Four States Ferry (267km)',
                'direction': 'test',
                'frequency': 1,
                'avg_distance': {route1['distance']},
                'avg_speed': 8.1,
                'avg_moving_time': {route1['distance'] / 8.1},
                'avg_elevation': {route1['elevation_gain']},
                'consistency_score': 1.0,
                'score': 50.0
            }},
            {{
                'route_id': 'test_unbound',
                'name': 'TEST: Unbound 200 (327km)',
                'direction': 'test',
                'frequency': 1,
                'avg_distance': {route2['distance']},
                'avg_speed': 7.1,
                'avg_moving_time': {route2['distance'] / 7.1},
                'avg_elevation': {route2['elevation_gain']},
                'consistency_score': 1.0,
                'score': 50.0
            }}
        ]"""

# Replace the old test routes in report_generator.py
pattern = r"        # Add test routes.*?'score': 50\.0\s+\}\s+\]"
report_content = re.sub(pattern, new_report_routes, report_content, flags=re.DOTALL)

# Write back (trusted source file)
with open('src/report_generator.py', 'w') as f:
    f.write(report_content)

print(f"✓ Updated report_generator.py with test route metadata")
print(f"\nDone! Run 'python3 main.py --analyze' to regenerate the report.")

# Made with Bob
