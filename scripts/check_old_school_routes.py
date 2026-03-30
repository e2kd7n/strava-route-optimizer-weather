#!/usr/bin/env python3
"""
Check how "Old School" routes are being grouped.
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetcher import StravaDataFetcher, Activity
from src.config import Config
from src.long_ride_analyzer import LongRideAnalyzer


def main():
    print("=" * 70)
    print("Checking 'Old School' Route Grouping")
    print("=" * 70)
    
    # Load config
    config = Config()
    
    # Create fetcher and load activities
    fetcher = StravaDataFetcher(None, config)
    all_activities = fetcher.load_cached_activities()
    
    if not all_activities:
        print("❌ No cached activities found")
        return
    
    print(f"\n📊 Loaded {len(all_activities)} total activities")
    
    # Filter for "Old School" activities
    old_school_activities = [a for a in all_activities if 'Old School' in a.name]
    
    print(f"Found {len(old_school_activities)} activities with 'Old School' in the name")
    
    if not old_school_activities:
        print("\n⚠️  No 'Old School' activities found in cache")
        return
    
    # Group by exact name
    by_name = defaultdict(list)
    for act in old_school_activities:
        by_name[act.name].append(act)
    
    print(f"\n📋 Grouped into {len(by_name)} unique names:")
    print("-" * 70)
    
    for name, acts in sorted(by_name.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{len(acts):2}x | {name}")
        for act in acts[:5]:  # Show first 5 of each
            print(f"      ID: {act.id:12} | Distance: {act.distance/1000:6.1f}km | Date: {act.start_date[:10]}")
        if len(acts) > 5:
            print(f"      ... and {len(acts)-5} more")
    
    print("\n" + "=" * 70)
    print("Testing Long Ride Analyzer Grouping")
    print("=" * 70)
    
    # Filter for long rides (>15km by default)
    min_distance = config.get('long_rides.min_distance_km', 15) * 1000
    long_old_school = [a for a in old_school_activities if a.distance >= min_distance]
    
    print(f"\n{len(long_old_school)} 'Old School' activities meet long ride criteria (>{min_distance/1000}km)")
    
    if long_old_school:
        # Create analyzer
        analyzer = LongRideAnalyzer(all_activities, config)
        
        # Group by name
        name_groups, unnamed = analyzer.group_rides_by_name(long_old_school)
        
        print(f"\n📊 LongRideAnalyzer grouped into {len(name_groups)} named groups:")
        print("-" * 70)
        
        for name, acts in sorted(name_groups.items(), key=lambda x: len(x[1]), reverse=True):
            if 'Old School' in name:
                print(f"\n{len(acts):2}x | {name}")
                for act in acts[:3]:
                    print(f"      ID: {act.id:12} | Distance: {act.distance/1000:6.1f}km")
        
        # Consolidate similar named groups
        print("\n" + "=" * 70)
        print("Consolidating Similar Named Groups (Route Similarity)")
        print("=" * 70)
        
        merged_groups = analyzer.consolidate_similar_named_groups(name_groups)
        
        print(f"\n📊 After similarity consolidation: {len(merged_groups)} groups")
        print("-" * 70)
        
        for name, acts in sorted(merged_groups.items(), key=lambda x: len(x[1]), reverse=True):
            if 'Old School' in name:
                print(f"\n{len(acts):2}x | {name}")
                for act in acts[:3]:
                    print(f"      ID: {act.id:12} | Distance: {act.distance/1000:6.1f}km")
        
        # Consolidate
        consolidated = analyzer.consolidate_named_groups(merged_groups)
        
        print(f"\n🔄 Final consolidated 'Old School' routes:")
        print("-" * 70)
        
        for ride in sorted(consolidated, key=lambda r: r.uses, reverse=True):
            if 'Old School' in ride.name:
                print(f"✅ {ride.name}: uses={ride.uses}, distance={ride.distance_km:.1f}km")
                if ride.activity_ids and len(ride.activity_ids) > 1:
                    print(f"   Activity IDs: {ride.activity_ids[:5]}")
                    if len(ride.activity_ids) > 5:
                        print(f"   ... and {len(ride.activity_ids) - 5} more")
                    print(f"   Dates: {ride.activity_dates[:3]}")
                    if len(ride.activity_dates) > 3:
                        print(f"   ... to {ride.activity_dates[-1]}")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
