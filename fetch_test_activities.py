#!/usr/bin/env python3
"""Fetch specific Strava activities for testing zoom functionality."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from auth import get_authenticated_client
from config import Config

def main():
    """Fetch two specific activities for zoom testing."""
    
    # Activity IDs to fetch
    activity_ids = [9458631701, 11551867398]
    
    print("Loading configuration...")
    config = Config('config/config_quick.yaml')
    
    print("Authenticating with Strava...")
    client = get_authenticated_client(config)
    
    print("\nFetching activities...")
    for activity_id in activity_ids:
        try:
            activity = client.get_activity(activity_id)
            
            print(f"\n{'='*60}")
            print(f"Activity ID: {activity_id}")
            print(f"Name: {activity.name}")
            print(f"Type: {activity.type}")
            print(f"Distance: {float(activity.distance)} meters")
            print(f"Moving Time: {activity.moving_time}")
            print(f"Total Elevation Gain: {float(activity.total_elevation_gain)} meters")
            print(f"Start Date: {activity.start_date_local}")
            
            # Get the polyline
            if hasattr(activity, 'map') and activity.map:
                polyline_str = activity.map.polyline
                if polyline_str:
                    import polyline
                    import json
                    coords = polyline.decode(polyline_str)
                    print(f"Coordinates: {len(coords)} points")
                    print(f"Start: {coords[0]}")
                    print(f"End: {coords[-1]}")
                    
                    # Calculate bounds
                    lats = [c[0] for c in coords]
                    lngs = [c[1] for c in coords]
                    print(f"Bounds: lat [{min(lats):.5f}, {max(lats):.5f}], lng [{min(lngs):.5f}, {max(lngs):.5f}]")
                    
                    # Save coordinates to file for adding to visualizer
                    output_file = f"test_route_{activity_id}_coords.json"
                    with open(output_file, 'w') as f:
                        json.dump({
                            'activity_id': activity_id,
                            'name': activity.name,
                            'distance': float(activity.distance),
                            'elevation_gain': float(activity.total_elevation_gain),
                            'coordinates': coords
                        }, f, indent=2)
                    print(f"Saved coordinates to {output_file}")
                else:
                    print("No polyline data available")
            else:
                print("No map data available")
                
        except Exception as e:
            print(f"Error fetching activity {activity_id}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()

# Made with Bob
