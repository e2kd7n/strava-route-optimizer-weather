#!/usr/bin/env python3
"""
Test script to check if geocoding is working (IP not blocked).
"""

import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def test_single_geocoding():
    """Test geocoding a single coordinate to check if IP is blocked."""
    
    # Initialize geolocator
    geolocator = Nominatim(user_agent="strava_commute_analyzer", timeout=10)
    
    # Test coordinate (Chicago downtown area)
    test_point = (41.8781, -87.6298)  # Chicago, IL
    
    print("Testing geocoding with Nominatim (OpenStreetMap)...")
    print(f"Test coordinate: {test_point}")
    print("-" * 60)
    
    try:
        # Add rate limiting delay (Nominatim requires 1 second between requests)
        time.sleep(1.0)
        
        print("Attempting reverse geocoding...")
        location = geolocator.reverse(test_point, exactly_one=True, language='en', timeout=10)
        
        if location:
            print("✅ SUCCESS! Geocoding is working.")
            print(f"\nAddress: {location.address}")
            
            if location.raw.get('address'):
                address = location.raw['address']
                print("\nDetailed address components:")
                for key, value in address.items():
                    print(f"  {key}: {value}")
            
            print("\n✅ Your IP is NOT blocked!")
            return True
        else:
            print("⚠️  No location data returned (but no error)")
            return False
            
    except GeocoderTimedOut:
        print("❌ TIMEOUT: Request timed out")
        print("This might indicate network issues or rate limiting")
        return False
        
    except GeocoderServiceError as e:
        print(f"❌ SERVICE ERROR: {e}")
        print("This might indicate your IP is blocked or service is down")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GEOCODING IP BLOCK TEST")
    print("=" * 60)
    print()
    
    success = test_single_geocoding()
    
    print()
    print("=" * 60)
    if success:
        print("RESULT: Geocoding is working normally")
    else:
        print("RESULT: Geocoding failed - check errors above")
    print("=" * 60)

# Made with Bob
