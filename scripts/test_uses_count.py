#!/usr/bin/env python3
"""
Test script to verify that the 'uses' field in long ride recommendations
properly shows values > 1 when routes are ridden multiple times.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.long_ride_analyzer import LongRideAnalyzer
from src.data_fetcher import Activity
from src.config import Config


def create_mock_activity(activity_id, name, distance=50000, polyline="test"):
    """Create a mock activity for testing."""
    return Activity(
        id=activity_id,
        name=name,
        type="Ride",
        sport_type="Ride",
        distance=distance,
        moving_time=7200,
        elapsed_time=7200,
        total_elevation_gain=500,
        start_date="2024-01-15T10:00:00Z",
        start_latlng=(41.8781, -87.6298),
        end_latlng=(41.8881, -87.6398),
        average_speed=6.94,
        max_speed=10.0,
        polyline=polyline
    )


def test_uses_count():
    """Test that uses count is properly calculated."""
    print("=" * 70)
    print("Testing 'uses' field in long ride recommendations")
    print("=" * 70)
    
    # Create mock activities with same name (should be grouped)
    # Using valid encoded polylines (simple 2-point routes)
    polyline1 = "ufp~FjvpuO?_@"  # Simple encoded polyline
    polyline2 = "wfp~FjvpuO?_@"  # Different polyline
    polyline3 = "xfp~FjvpuO?_@"  # Another different polyline
    
    activities = [
        create_mock_activity(1, "Lake Loop", 50000, polyline1),
        create_mock_activity(2, "Lake Loop", 51000, polyline1),  # Same route, slightly different distance
        create_mock_activity(3, "Lake Loop", 49500, polyline1),  # Same route
        create_mock_activity(4, "River Trail", 60000, polyline2),
        create_mock_activity(5, "River Trail", 60500, polyline2),  # Same route
        create_mock_activity(6, "Mountain Climb", 75000, polyline3),  # Only once
    ]
    
    # Create analyzer
    config = Config()
    analyzer = LongRideAnalyzer(activities, config)
    
    # Group rides by name
    print("\n📊 Grouping rides by name...")
    name_groups, unnamed_rides = analyzer.group_rides_by_name(activities)
    
    print(f"Found {len(name_groups)} named groups:")
    for name, acts in name_groups.items():
        print(f"  - '{name}': {len(acts)} activities")
    
    # Consolidate named groups
    print("\n🔄 Consolidating named groups...")
    long_rides = analyzer.consolidate_named_groups(name_groups)
    
    print(f"\nConsolidated into {len(long_rides)} unique routes:")
    print("-" * 70)
    
    # Check results
    all_passed = True
    for ride in long_rides:
        status = "✅" if ride.uses > 1 or ride.name == "Mountain Climb" else "❌"
        print(f"{status} {ride.name}: uses={ride.uses}, distance={ride.distance_km:.1f}km")
        
        # Verify expected values
        if ride.name == "Lake Loop" and ride.uses != 3:
            print(f"   ❌ FAILED: Expected uses=3, got uses={ride.uses}")
            all_passed = False
        elif ride.name == "River Trail" and ride.uses != 2:
            print(f"   ❌ FAILED: Expected uses=2, got uses={ride.uses}")
            all_passed = False
        elif ride.name == "Mountain Climb" and ride.uses != 1:
            print(f"   ❌ FAILED: Expected uses=1, got uses={ride.uses}")
            all_passed = False
    
    print("-" * 70)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        print("\nThe 'uses' field is now properly calculated and will show values > 1")
        print("when the same route has been ridden multiple times.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        return False


if __name__ == '__main__':
    try:
        success = test_uses_count()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
