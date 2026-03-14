#!/usr/bin/env python3
"""
Test script for long ride recommendations with enhanced wind scoring.

Tests the new wind analysis that prioritizes tailwinds in the second half of routes.
"""

import sys
from datetime import datetime
from typing import List, Tuple

# Mock classes for testing
class MockActivity:
    def __init__(self, activity_id, name, polyline, distance, moving_time, 
                 elevation_gain, start_date, average_speed, start_latlng, end_latlng):
        self.id = activity_id
        self.name = name
        self.type = "Ride"
        self.polyline = polyline
        self.distance = distance
        self.moving_time = moving_time
        self.total_elevation_gain = elevation_gain
        self.start_date = start_date
        self.average_speed = average_speed
        self.start_latlng = start_latlng
        self.end_latlng = end_latlng


class MockConfig:
    def __init__(self):
        self.data = {
            'long_rides.min_distance_km': 15,
            'geocoding.enabled': False
        }
    
    def get(self, key, default=None):
        return self.data.get(key, default)


def create_test_route(start_lat: float, start_lon: float, 
                      direction: str = "north") -> str:
    """
    Create a simple test route polyline.
    
    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        direction: "north", "south", "east", or "west"
    
    Returns:
        Encoded polyline string
    """
    import polyline
    
    # Create a route with ~20 points
    coords = [(start_lat, start_lon)]
    
    if direction == "north":
        # Go north, then return south
        for i in range(1, 11):
            coords.append((start_lat + i * 0.01, start_lon))
        for i in range(10, 0, -1):
            coords.append((start_lat + i * 0.01, start_lon + 0.005))
    elif direction == "south":
        # Go south, then return north
        for i in range(1, 11):
            coords.append((start_lat - i * 0.01, start_lon))
        for i in range(10, 0, -1):
            coords.append((start_lat - i * 0.01, start_lon + 0.005))
    elif direction == "east":
        # Go east, then return west
        for i in range(1, 11):
            coords.append((start_lat, start_lon + i * 0.01))
        for i in range(10, 0, -1):
            coords.append((start_lat + 0.005, start_lon + i * 0.01))
    else:  # west
        # Go west, then return east
        for i in range(1, 11):
            coords.append((start_lat, start_lon - i * 0.01))
        for i in range(10, 0, -1):
            coords.append((start_lat + 0.005, start_lon - i * 0.01))
    
    return polyline.encode(coords)


def test_wind_scoring():
    """Test the enhanced wind scoring with different wind conditions."""
    from src.long_ride_analyzer import LongRideAnalyzer
    
    print("=" * 80)
    print("Testing Long Ride Wind Scoring (Tailwind Preference)")
    print("=" * 80)
    
    # Chicago area coordinates
    chicago_lat, chicago_lon = 41.8781, -87.6298
    
    # Create test activities
    activities = [
        MockActivity(
            activity_id=1,
            name="North Loop Ride",
            polyline=create_test_route(chicago_lat, chicago_lon, "north"),
            distance=25000,  # 25km
            moving_time=3600,  # 1 hour
            elevation_gain=100,
            start_date=datetime.now().isoformat(),
            average_speed=6.94,  # ~25 km/h
            start_latlng=(chicago_lat, chicago_lon),
            end_latlng=(chicago_lat + 0.001, chicago_lon + 0.005)
        ),
        MockActivity(
            activity_id=2,
            name="South Loop Ride",
            polyline=create_test_route(chicago_lat, chicago_lon, "south"),
            distance=30000,  # 30km
            moving_time=4200,  # 1.17 hours
            elevation_gain=120,
            start_date=datetime.now().isoformat(),
            average_speed=7.14,
            start_latlng=(chicago_lat, chicago_lon),
            end_latlng=(chicago_lat - 0.001, chicago_lon + 0.005)
        ),
        MockActivity(
            activity_id=3,
            name="East Loop Ride",
            polyline=create_test_route(chicago_lat, chicago_lon, "east"),
            distance=28000,  # 28km
            moving_time=3900,
            elevation_gain=80,
            start_date=datetime.now().isoformat(),
            average_speed=7.18,
            start_latlng=(chicago_lat, chicago_lon),
            end_latlng=(chicago_lat + 0.005, chicago_lon + 0.001)
        )
    ]
    
    config = MockConfig()
    analyzer = LongRideAnalyzer(activities, config)
    
    # Extract long rides
    long_rides = analyzer.extract_long_rides(activities)
    print(f"\n✓ Extracted {len(long_rides)} long rides")
    
    # Test different wind conditions
    wind_scenarios = [
        {"name": "North Wind (Ideal for North Route)", "wind_direction_deg": 0, "wind_speed_kph": 20},
        {"name": "South Wind (Ideal for South Route)", "wind_direction_deg": 180, "wind_speed_kph": 20},
        {"name": "East Wind (Ideal for East Route)", "wind_direction_deg": 90, "wind_speed_kph": 20},
        {"name": "West Wind", "wind_direction_deg": 270, "wind_speed_kph": 20},
        {"name": "Light Winds", "wind_direction_deg": 180, "wind_speed_kph": 8},
    ]
    
    for scenario in wind_scenarios:
        print(f"\n{'=' * 80}")
        print(f"Scenario: {scenario['name']}")
        print(f"Wind: {scenario['wind_speed_kph']} km/h from {scenario['wind_direction_deg']}°")
        print(f"{'=' * 80}")
        
        for ride in long_rides:
            score, analysis = analyzer.calculate_wind_score(ride, scenario)
            
            print(f"\n{ride.name}:")
            print(f"  Distance: {ride.distance_km:.1f}km")
            print(f"  Wind Score: {score:.3f}")
            print(f"  First Half Score: {analysis['first_half_score']:.3f}")
            print(f"  Second Half Score: {analysis['second_half_score']:.3f}")
            print(f"  Recommendation: {analysis['recommendation']}")
            
            # Show segment details
            segments = analysis.get('segments', [])
            if segments:
                print(f"  Segments:")
                for seg in segments[:4]:  # Show first 4 segments
                    print(f"    Seg {seg['segment']}: {seg['wind_type']} (score: {seg['score']:.2f})")
    
    print(f"\n{'=' * 80}")
    print("Testing Complete!")
    print(f"{'=' * 80}")
    
    # Test recommendations
    print("\n\nTesting Ride Recommendations:")
    print("=" * 80)
    
    # Simulate clicking near Chicago
    clicked_lat, clicked_lon = chicago_lat + 0.05, chicago_lon
    
    # Test with south wind (should favor north route with tailwind return)
    weather_data = {
        "wind_direction_deg": 180,  # South wind
        "wind_speed_kph": 25,
        "precipitation_mm": 0
    }
    
    print(f"\nClicked location: ({clicked_lat:.4f}, {clicked_lon:.4f})")
    print(f"Weather: {weather_data['wind_speed_kph']} km/h from {weather_data['wind_direction_deg']}°")
    
    # Mock the weather fetcher to return our test data
    class MockWeatherFetcher:
        def get_current_conditions(self, lat, lon):
            return weather_data
    
    analyzer.weather_fetcher = MockWeatherFetcher()
    
    recommendations = analyzer.get_ride_recommendations(
        long_rides, clicked_lat, clicked_lon
    )
    
    print(f"\nFound {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"\n{i}. {rec.ride.name}")
        print(f"   {rec.route_description}")
        print(f"   Weather Score: {rec.weather_score:.3f}")
        print(f"   Precipitation Risk: {rec.precipitation_risk}")
        if rec.wind_analysis:
            print(f"   Wind Analysis:")
            print(f"     {analyzer.format_wind_analysis(rec.wind_analysis)}")


if __name__ == "__main__":
    try:
        test_wind_scoring()
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
