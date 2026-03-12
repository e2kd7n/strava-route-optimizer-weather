"""Debug script to inspect commute activities."""
import json
from pathlib import Path

# Load cached activities
cache_file = Path('data/cache/activities.json')
with open(cache_file, 'r') as f:
    cache_data = json.load(f)

activities = cache_data['activities']

# Filter commute activities
commute_keywords = ['work', 'commute', 'to work', 'from work', 'home from work']
commute_activities = []

for activity in activities:
    activity_name_lower = activity['name'].lower()
    is_commute_name = any(keyword in activity_name_lower for keyword in commute_keywords)
    if is_commute_name:
        commute_activities.append(activity)

print(f"Found {len(commute_activities)} commute activities")
print("\nFirst 5 commute activities:")
for i, activity in enumerate(commute_activities[:5]):
    print(f"\n--- Activity {i+1} ---")
    print(f"Name: {activity['name']}")
    print(f"Type: {activity['type']}")
    print(f"Date: {activity['start_date']}")
    print(f"Distance: {activity['distance']} meters")
    print(f"Start LatLng: {activity['start_latlng']}")
    print(f"End LatLng: {activity['end_latlng']}")
    print(f"Has Polyline: {activity['polyline'] is not None}")
    if activity['polyline']:
        print(f"Polyline length: {len(activity['polyline'])}")

# Check how many have GPS data
with_start = sum(1 for a in commute_activities if a['start_latlng'])
with_end = sum(1 for a in commute_activities if a['end_latlng'])
with_polyline = sum(1 for a in commute_activities if a['polyline'])

print(f"\n--- GPS Data Summary ---")
print(f"Activities with start_latlng: {with_start}/{len(commute_activities)}")
print(f"Activities with end_latlng: {with_end}/{len(commute_activities)}")
print(f"Activities with polyline: {with_polyline}/{len(commute_activities)}")

# Made with Bob
