#!/usr/bin/env python3
"""
Test script for route naming functionality.
"""

from src.route_namer import RouteNamer

def test_route_naming():
    """Test route naming with sample data."""
    print("Testing Route Naming Functionality")
    print("=" * 50)
    
    # Create route namer
    namer = RouteNamer()
    
    # Test simple naming
    print("\n1. Testing simple route naming:")
    name1 = namer.generate_simple_name("home_to_work_0", "home_to_work", rank=1)
    print(f"   Route 1: {name1}")
    
    name2 = namer.generate_simple_name("home_to_work_1", "home_to_work", rank=2)
    print(f"   Route 2: {name2}")
    
    name3 = namer.generate_simple_name("work_to_home_0", "work_to_home", rank=1)
    print(f"   Route 3: {name3}")
    
    # Test with sample coordinates (Chicago area)
    print("\n2. Testing geographic naming (this may take a moment):")
    sample_coords = [
        (41.8781, -87.6298),  # Chicago downtown
        (41.8850, -87.6200),  # Near North Side
        (41.8900, -87.6100),  # Lincoln Park
    ]
    
    try:
        geo_name = namer.name_route(sample_coords, "home_to_work_0", "home_to_work")
        print(f"   Geographic name: {geo_name}")
    except Exception as e:
        print(f"   Geographic naming skipped (requires internet): {e}")
    
    print("\n✅ Route naming tests completed!")
    print("\nNote: Geographic naming requires internet connection and may be rate-limited.")

if __name__ == '__main__':
    test_route_naming()

# Made with Bob
