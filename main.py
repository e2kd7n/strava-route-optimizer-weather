#!/usr/bin/env python3
"""
Strava Commute Route Analyzer - Main Entry Point

Analyzes Strava cycling activities to determine optimal commute routes
and recommend long recreational rides.

Copyright (c) 2024-2026 e2kd7n
Licensed under the MIT License - see LICENSE file for details.

This software requires valid Strava API credentials to function.
Unauthorized use, reproduction, or distribution is prohibited.
"""

import argparse
import logging
import subprocess
import sys
import webbrowser
import json
import os
import platform
import warnings
from pathlib import Path
from datetime import datetime
from collections import Counter

# Fix WeasyPrint library path on macOS
if platform.system() == 'Darwin':  # macOS
    homebrew_lib = '/opt/homebrew/lib'
    if os.path.exists(homebrew_lib):
        dyld_path = os.environ.get('DYLD_LIBRARY_PATH', '')
        if homebrew_lib not in dyld_path:
            os.environ['DYLD_LIBRARY_PATH'] = f"{homebrew_lib}:{dyld_path}"

from tqdm import tqdm

from src.config import load_config
# Use secure authentication module with enhanced security features
from src.auth_secure import SecureStravaAuthenticator, get_authenticated_client, validate_strava_credentials
from src.data_fetcher import StravaDataFetcher
from src.location_finder import LocationFinder
from src.route_analyzer import RouteAnalyzer
from src.optimizer import RouteOptimizer
from src.visualizer import RouteVisualizer
from src.report_generator import ReportGenerator
from src.long_ride_analyzer import LongRideAnalyzer

# Suppress stravalib refresh_token warning
warnings.filterwarnings('ignore', message='.*refresh_token.*auto.*', category=Warning)

# Configure logging - suppress timestamps for cleaner output during analysis
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors by default
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a separate logger for progress messages
progress_logger = logging.getLogger('progress')
progress_logger.setLevel(logging.INFO)
progress_handler = logging.StreamHandler()
progress_handler.setFormatter(logging.Formatter('%(message)s'))
progress_logger.addHandler(progress_handler)
progress_logger.propagate = False

# Create a file logger for debugging
debug_logger = logging.getLogger('debug')
debug_logger.setLevel(logging.DEBUG)
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
debug_handler = logging.FileHandler(log_dir / 'debug.log')
debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
debug_logger.addHandler(debug_handler)
debug_logger.propagate = False


def authenticate(config):
    """
    Perform Strava authentication.
    
    Args:
        config: Configuration object
    """
    logger.info("Starting authentication...")
    
    # Validate credentials before attempting authentication
    client_id = config.get('strava.client_id')
    client_secret = config.get('strava.client_secret')
    validate_strava_credentials(client_id, client_secret)
    
    authenticator = SecureStravaAuthenticator(
        client_id=client_id,
        client_secret=client_secret
    )
    
    tokens = authenticator.authenticate()
    logger.info("Authentication successful!")
    logger.info(f"Access token expires at: {tokens['expires_at']}")


def show_cache_stats():
    """
    Display statistics about cached activities.
    """
    cache_file = Path('data/cache/activities.json')
    
    if not cache_file.exists():
        print("❌ No cached activities found.")
        print("   Run: python main.py --fetch")
        return
    
    print("\n" + "="*70)
    print("📊 CACHED ACTIVITIES STATISTICS")
    print("="*70 + "\n")
    
    # Load cached data
    with open(cache_file, 'r') as f:
        data = json.load(f)
        activities = data.get('activities', [])
        cache_timestamp = data.get('timestamp', 'Unknown')
    
    # Summary table
    print("+---------------------------------------------------------------+")
    print(f"| Cache Updated: {cache_timestamp[:19]:<42} |")
    print(f"| Total Activities: {len(activities):<45} |")
    print("+---------------------------------------------------------------+")
    print()
    
    if not activities:
        print("No activities in cache.")
        return
    
    # Analyze activities
    activity_types = Counter()
    years = Counter()
    commute_keywords = ['commute', 'to work', 'from work', 'ride to work', 'ride home']
    commute_count = 0
    to_work_count = 0
    from_work_count = 0
    
    distances = []
    durations = []
    
    earliest_date = None
    latest_date = None
    
    for activity in activities:
        # Activity type
        activity_type = activity.get('type', 'Unknown')
        activity_types[activity_type] += 1
        
        # Date analysis
        start_date_str = activity.get('start_date', '')
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                year = start_date.year
                years[year] += 1
                
                if earliest_date is None or start_date < earliest_date:
                    earliest_date = start_date
                if latest_date is None or start_date > latest_date:
                    latest_date = start_date
            except:
                pass
        
        # Commute detection
        name = activity.get('name', '').lower()
        if any(keyword in name for keyword in commute_keywords):
            commute_count += 1
            if 'to work' in name or 'morning' in name:
                to_work_count += 1
            elif 'from work' in name or 'home' in name or 'evening' in name:
                from_work_count += 1
        
        # Distance and duration
        distance = activity.get('distance', 0)
        if distance > 0:
            distances.append(distance / 1000)  # Convert to km
        
        moving_time = activity.get('moving_time', 0)
        if moving_time > 0:
            durations.append(moving_time / 60)  # Convert to minutes
    
    # Date Range table
    if earliest_date and latest_date:
        days_span = (latest_date - earliest_date).days
        print("📅 DATE RANGE")
        print("+-------------+------------------------------------------------+")
        print(f"| Earliest    | {str(earliest_date.date()):<46} |")
        print(f"| Latest      | {str(latest_date.date()):<46} |")
        span_text = f"{days_span} days ({days_span/365.25:.1f} years)"
        print(f"| Span        | {span_text:<46} |")
        print("+-------------+------------------------------------------------+")
        print()
    
    # Activity Types table
    print("🚴 ACTIVITY TYPES")
    print("+-----------------------------+-----------+------------+")
    print("| Type                        | Count     | Percentage |")
    print("+-----------------------------+-----------+------------+")
    for activity_type, count in activity_types.most_common():
        percentage = (count / len(activities)) * 100
        print(f"| {activity_type:<27} | {count:>9} | {percentage:>9.1f}% |")
    print("+-----------------------------+-----------+------------+")
    print()
    
    # Activities by Year table
    if years:
        print("📆 ACTIVITIES BY YEAR")
        print("+----------+-----------+")
        print("| Year     | Count     |")
        print("+----------+-----------+")
        for year in sorted(years.keys()):
            print(f"| {year}   | {years[year]:>9} |")
        print("+----------+-----------+")
        print()
    
    # Commute Activities table
    commute_percentage = (commute_count / len(activities)) * 100 if activities else 0
    print("🏢 COMMUTE ACTIVITIES")
    print("+------------------+-----------+------------+")
    print("| Category         | Count     | Percentage |")
    print("+------------------+-----------+------------+")
    print(f"| Total Commutes   | {commute_count:>9} | {commute_percentage:>9.1f}% |")
    print(f"| To Work          | {to_work_count:>9} | {(to_work_count/len(activities)*100):>9.1f}% |")
    print(f"| From Work        | {from_work_count:>9} | {(from_work_count/len(activities)*100):>9.1f}% |")
    print("+------------------+-----------+------------+")
    print()
    
    # Distance Statistics table
    if distances:
        print("📏 DISTANCE STATISTICS")
        print("+--------------+--------------+")
        print("| Metric       | Value        |")
        print("+--------------+--------------+")
        print(f"| Total        | {sum(distances):>10.1f} km |")
        print(f"| Average      | {sum(distances)/len(distances):>10.2f} km |")
        print(f"| Min          | {min(distances):>10.2f} km |")
        print(f"| Max          | {max(distances):>10.2f} km |")
        print("+--------------+--------------+")
        print()
    
    # Duration Statistics table
    if durations:
        print("⏱️  DURATION STATISTICS")
        print("+--------------+------------------+")
        print("| Metric       | Value            |")
        print("+--------------+------------------+")
        print(f"| Total        | {sum(durations)/60:>12.1f} hours |")
        print(f"| Average      | {sum(durations)/len(durations):>12.1f} min   |")
        print(f"| Min          | {min(durations):>12.1f} min   |")
        print(f"| Max          | {max(durations):>12.1f} min   |")
        print("+--------------+------------------+")
        print()
    
    print("="*70 + "\n")


def fetch_activities(config, after_date=None, before_date=None, limit=None, replace_cache=False):
    """
    Fetch activities from Strava API.
    
    Args:
        config: Configuration object
        after_date: Optional datetime to fetch activities after this date
        before_date: Optional datetime to fetch activities before this date
        limit: Optional maximum number of activities to fetch
        replace_cache: If True, replace cache instead of merging
    """
    if after_date and before_date:
        logger.info(f"Fetching activities from {after_date.date()} to {before_date.date()}...")
    elif after_date:
        logger.info(f"Fetching activities from Strava (after {after_date.date()})...")
    elif before_date:
        logger.info(f"Fetching activities from Strava (before {before_date.date()})...")
    else:
        logger.info("Fetching activities from Strava...")
    
    # Validate credentials before fetching
    client_id = config.get('strava.client_id')
    client_secret = config.get('strava.client_secret')
    validate_strava_credentials(client_id, client_secret)
    
    try:
        client = get_authenticated_client(config)
        fetcher = StravaDataFetcher(client, config)
        
        # Fetch activities
        activities = fetcher.fetch_activities(after=after_date, before=before_date, limit=limit)
        
        # Cache activities (merge by default, replace if requested)
        cache_stats = fetcher.cache_activities(activities, merge=not replace_cache)
        
        # Log summary
        if replace_cache:
            logger.info(f"Successfully fetched and replaced cache with {cache_stats['total']} activities")
        else:
            logger.info(f"Successfully fetched and merged: {cache_stats['new']} new, "
                       f"{cache_stats['updated']} updated, {cache_stats['total']} total")
        
    except Exception as e:
        logger.error(f"Failed to fetch activities: {e}")
        raise


def _load_and_filter_activities(fetcher, config):
    """
    Load cached activities and filter for commutes.
    
    Args:
        fetcher: StravaDataFetcher instance
        config: Configuration object
        
    Returns:
        tuple: (all_activities, commute_activities)
        
    Raises:
        SystemExit: If no cached activities or insufficient commute activities
    """
    logger.info("Loading activities from cache...")
    all_activities = fetcher.load_cached_activities()
    
    if not all_activities:
        logger.error("No cached activities found. Run with --fetch first.")
        return None, None
    
    logger.info(f"Loaded {len(all_activities)} activities from cache")
    
    # Filter commute activities
    logger.info("Filtering commute activities...")
    commute_activities = fetcher.filter_commute_activities(all_activities)
    
    if len(commute_activities) < 10:
        logger.error(f"Insufficient commute activities: {len(commute_activities)} found, need at least 10")
        logger.info("Try adjusting distance filters in config/config.yaml")
        return None, None
    
    logger.info(f"Found {len(commute_activities)} potential commute activities")
    return all_activities, commute_activities


def _identify_locations(commute_activities, config):
    """
    Identify home and work locations from commute activities.
    
    Args:
        commute_activities: List of commute activities
        config: Configuration object
        
    Returns:
        tuple: (home, work) Location objects
        
    Raises:
        ValueError: If locations cannot be identified
    """
    logger.info("Identifying home and work locations...")
    finder = LocationFinder(commute_activities, config)
    
    try:
        home, work = finder.identify_home_work()
    except ValueError as e:
        logger.error(f"Failed to identify locations: {e}")
        logger.info("Try adjusting clustering parameters in config/config.yaml")
        raise
    
    logger.info(f"Home: ({home.lat:.4f}, {home.lon:.4f}) - {home.activity_count} activities")
    logger.info(f"Work: ({work.lat:.4f}, {work.lon:.4f}) - {work.activity_count} activities")
    
    return home, work


def _log_route_summary(route_groups):
    """
    Log summary of route groups.
    
    Args:
        route_groups: List of RouteGroup objects
    """
    logger.info(f"Found {len(route_groups)} commute route variants")
    for group in route_groups:
        logger.info(f"  - {group.id}: {group.frequency} uses")


def _analyze_long_rides(all_activities, commute_activities, config):
    """
    Analyze long recreational rides if enabled.
    
    Args:
        all_activities: List of all activities
        commute_activities: List of commute activities
        config: Configuration object
        
    Returns:
        tuple: (long_rides, long_ride_analyzer)
    """
    long_rides = []
    long_ride_analyzer = None
    
    # Check if long rides analysis is enabled
    long_rides_config = config.get('long_rides', {})
    if isinstance(long_rides_config, dict):
        enabled = long_rides_config.get('enabled', True)
    else:
        enabled = config.get('long_rides.enabled', True)
    
    if not enabled:
        return long_rides, long_ride_analyzer
    
    logger.info("Analyzing long recreational rides...")
    long_ride_analyzer = LongRideAnalyzer(all_activities, config)
    
    # Classify activities
    _, long_ride_activities = long_ride_analyzer.classify_activities(commute_activities)
    logger.info(f"Found {len(long_ride_activities)} long ride activities")
    
    # Extract long rides
    if long_ride_activities:
        long_rides = long_ride_analyzer.extract_long_rides(long_ride_activities)
        logger.info(f"Extracted {len(long_rides)} long rides for analysis")
        
        # Show statistics
        if long_rides:
            distances = [r.distance_km for r in long_rides]
            logger.info(f"  Distance range: {min(distances):.1f} - {max(distances):.1f} km")
            logger.info(f"  Average distance: {sum(distances)/len(distances):.1f} km")
            loop_count = sum(1 for r in long_rides if r.is_loop)
            logger.info(f"  Loop rides: {loop_count} ({loop_count/len(long_rides)*100:.1f}%)")
    
    return long_rides, long_ride_analyzer


def _optimize_and_rank_routes(route_groups, config):
    """
    Optimize and rank routes.
    
    Args:
        route_groups: List of RouteGroup objects
        config: Configuration object
        
    Returns:
        dict: Optimization results with keys:
            - ranked_routes
            - optimal_route
            - optimal_score
            - optimal_breakdown
            - recommendations
            - optimizer
    """
    logger.info("Optimizing route selection...")
    optimizer = RouteOptimizer(route_groups, config)
    ranked_routes = optimizer.rank_routes()
    optimal_route, optimal_score, optimal_breakdown = optimizer.get_optimal_route()
    recommendations = optimizer.get_route_recommendations()
    
    logger.info(f"Optimal route: {optimal_route.id}")
    logger.info(f"  Score: {optimal_score:.2f}")
    logger.info(f"  Time: {optimal_breakdown['time']:.1f}, Distance: {optimal_breakdown['distance']:.1f}, Safety: {optimal_breakdown['safety']:.1f}")
    
    return {
        'ranked_routes': ranked_routes,
        'optimal_route': optimal_route,
        'optimal_score': optimal_score,
        'optimal_breakdown': optimal_breakdown,
        'recommendations': recommendations,
        'optimizer': optimizer
    }


def _generate_visualization(route_groups, home, work, config, long_rides,
                           long_ride_analyzer, optimal_route, ranked_routes):
    """
    Generate interactive map visualization.
    
    Args:
        route_groups: List of RouteGroup objects
        home: Home Location object
        work: Work Location object
        config: Configuration object
        long_rides: List of long ride objects
        long_ride_analyzer: LongRideAnalyzer instance
        optimal_route: Optimal RouteGroup object
        ranked_routes: List of ranked routes
        
    Returns:
        str: HTML content for the map
    """
    logger.info("Generating interactive map...")
    visualizer = RouteVisualizer(
        route_groups, home, work, config,
        long_rides=long_rides,
        long_ride_analyzer=long_ride_analyzer
    )
    map_html = visualizer.generate_map(
        optimal_route=optimal_route,
        ranked_routes=ranked_routes
    )
    
    # Generate preview map for optimal route
    logger.info("Generating optimal route preview map...")
    preview_map_html = visualizer.generate_preview_map(optimal_route)
    
    return map_html, preview_map_html, visualizer


def _save_report(analysis_results, output_dir, generate_pdf=False):
    """
    Generate and save HTML report with timestamp.
    
    Args:
        analysis_results: Dictionary of analysis results
        output_dir: Output directory path
        generate_pdf: Whether to generate PDF report (default: False)
        
    Returns:
        Path: Path to the saved report file
    """
    logger.info("Generating HTML report...")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = output_path / f'commute_analysis_{timestamp}.html'
    
    generator = ReportGenerator(analysis_results)
    generator.generate_report(str(report_path), generate_pdf=generate_pdf)
    
    logger.info(f"✅ Analysis complete!")
    logger.info(f"📄 Report saved to: {report_path}")
    if generate_pdf:
        pdf_path = str(report_path).replace('.html', '.pdf')
        logger.info(f"📄 PDF saved to: {pdf_path}")
    logger.info(f"🚴 Optimal route: {analysis_results['optimal_route'].id} (score: {analysis_results['optimal_score']:.2f})")
    
    return report_path


def _open_report_in_browser(report_path):
    """
    Open report in browser without blocking (non-blocking subprocess).
    
    This significantly improves performance by not waiting for the browser to launch.
    
    Args:
        report_path: Path to the report file
    """
    try:
        # Convert to absolute path
        abs_path = report_path.resolve()
        
        # Use platform-specific non-blocking commands
        if sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', str(abs_path)])
            logger.info("🌐 Opening report in default browser...")
        elif sys.platform == 'win32':  # Windows
            subprocess.Popen(['start', str(abs_path)], shell=True)
            logger.info("🌐 Opening report in default browser...")
        else:  # Linux
            subprocess.Popen(['xdg-open', str(abs_path)])
            logger.info("🌐 Opening report in default browser...")
        
        # Return immediately without waiting for browser to launch
    except Exception as e:
        logger.warning(f"Could not automatically open report: {e}")
        logger.info(f"Please open manually: {report_path}")


def _log_runtime(runtime_seconds: float, num_activities: int, num_route_groups: int):
    """
    Log analysis runtime to file for performance tracking.
    
    Args:
        runtime_seconds: Total runtime in seconds
        num_activities: Number of activities analyzed
        num_route_groups: Number of route groups created
    """
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'performance.log'
    
    timestamp = datetime.now().isoformat()
    log_entry = {
        'timestamp': timestamp,
        'runtime_seconds': round(runtime_seconds, 2),
        'runtime_minutes': round(runtime_seconds / 60, 2),
        'num_activities': num_activities,
        'num_route_groups': num_route_groups,
        'activities_per_second': round(num_activities / runtime_seconds, 2) if runtime_seconds > 0 else 0
    }
    
    # Append to log file
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def analyze_routes(config, output_dir, n_workers=2, generate_pdf=False, force_reanalysis=False):
    """
    Analyze routes and generate report.
    
    Args:
        config: Configuration object
        output_dir: Output directory for reports
        n_workers: Number of parallel workers for route analysis
        generate_pdf: Whether to generate PDF report (default: False)
        force_reanalysis: Whether to clear cache and reprocess all routes (default: False)
    """
    import time
    from tqdm import tqdm as tqdm_module
    
    # Start timing
    start_time = time.time()
    
    tqdm_module.write("\n" + "="*60)
    tqdm_module.write("🚴  STRAVA COMMUTE ROUTE ANALYZER")
    tqdm_module.write("="*60)
    if n_workers > 1:
        tqdm_module.write(f"⚡  Parallel: {n_workers} workers")
    tqdm_module.write("")
    
    # Log start of analysis
    debug_logger.info("="*60)
    debug_logger.info("Starting route analysis")
    debug_logger.info(f"Workers: {n_workers}, PDF: {generate_pdf}, Force reanalysis: {force_reanalysis}")
    debug_logger.info("="*60)
    
    # Validate credentials before analysis
    try:
        debug_logger.info("Validating Strava credentials...")
        client_id = config.get('strava.client_id')
        client_secret = config.get('strava.client_secret')
        validate_strava_credentials(client_id, client_secret)
        debug_logger.info("Credentials validated successfully")
    except Exception as e:
        debug_logger.error(f"Credential validation failed: {e}", exc_info=True)
        tqdm_module.write(f"\n❌ ERROR: Credential validation failed: {e}")
        raise
    
    try:
        # Progress tracking
        total_steps = 8
        
        with tqdm(total=total_steps, desc="Progress", unit="step", ncols=80,
                 bar_format='{desc}: {percentage:3.0f}%|{bar}|', leave=True) as pbar:
            # Step 1: Get authenticated client
            step_start = time.time()
            pbar.set_description("🔐 Authenticating")
            debug_logger.info("Step 1: Getting authenticated client...")
            try:
                client = get_authenticated_client(config)
                fetcher = StravaDataFetcher(client, config)
                debug_logger.info(f"Step 1 completed in {time.time() - step_start:.2f}s")
                pbar.update(1)
                pbar.refresh()
                print()  # New line after this phase
            except Exception as e:
                debug_logger.error(f"Step 1 failed: {e}", exc_info=True)
                tqdm_module.write(f"\n❌ ERROR at Step 1 (Authentication): {e}")
                raise
            
            # Step 2: Load and filter activities
            step_start = time.time()
            pbar.set_description("📥 Loading activities")
            debug_logger.info("Step 2: Loading and filtering activities...")
            try:
                all_activities, commute_activities = _load_and_filter_activities(fetcher, config)
                if not all_activities or not commute_activities:
                    debug_logger.error("No activities found or insufficient commute activities")
                    tqdm_module.write("\n❌ ERROR: No activities found or insufficient commute activities")
                    return
                debug_logger.info(f"Step 2 completed in {time.time() - step_start:.2f}s")
                debug_logger.info(f"Loaded {len(all_activities)} total, {len(commute_activities)} commute activities")
                pbar.update(1)
                pbar.refresh()
                print()  # New line after this phase
            except Exception as e:
                debug_logger.error(f"Step 2 failed: {e}", exc_info=True)
                tqdm_module.write(f"\n❌ ERROR at Step 2 (Loading activities): {e}")
                raise
            
            # Step 3: Identify locations
            step_start = time.time()
            pbar.set_description("📍 Identifying locations")
            debug_logger.info("Step 3: Identifying home and work locations...")
            try:
                home, work = _identify_locations(commute_activities, config)
                debug_logger.info(f"Step 3 completed in {time.time() - step_start:.2f}s")
                debug_logger.info(f"Home: ({home.lat:.4f}, {home.lon:.4f}), Work: ({work.lat:.4f}, {work.lon:.4f})")
                pbar.update(1)
                pbar.refresh()
                print()  # New line after this phase
            except ValueError as e:
                debug_logger.error(f"Step 3 failed: {e}", exc_info=True)
                tqdm_module.write(f"\n❌ ERROR at Step 3 (Identifying locations): {e}")
                return
            except Exception as e:
                debug_logger.error(f"Step 3 failed with unexpected error: {e}", exc_info=True)
                tqdm_module.write(f"\n❌ ERROR at Step 3 (Identifying locations): {e}")
                raise
            
            # Step 4: Analyze commute routes
            step_start = time.time()
            pbar.set_description("🗺️  Analyzing commute routes")
            debug_logger.info("Step 4: Analyzing commute routes...")
            debug_logger.info(f"Creating RouteAnalyzer with {n_workers} workers, force_reanalysis={force_reanalysis}")
            try:
                analyzer = RouteAnalyzer(commute_activities, home, work, config,
                                        n_workers=n_workers, force_reanalysis=force_reanalysis)
                debug_logger.info("RouteAnalyzer created, starting route grouping...")
                route_groups = analyzer.group_similar_routes()
                
                if not route_groups:
                    debug_logger.error("No route groups found")
                    tqdm_module.write("\n❌ ERROR: No route groups found")
                    return
                
                debug_logger.info(f"Step 4 completed in {time.time() - step_start:.2f}s")
                debug_logger.info(f"Found {len(route_groups)} route groups")
                _log_route_summary(route_groups)
                pbar.update(1)
                pbar.refresh()
                print()  # New line after this phase
            except Exception as e:
                debug_logger.error(f"Step 4 failed: {e}", exc_info=True)
                tqdm_module.write(f"\n❌ ERROR at Step 4 (Analyzing routes): {e}")
                tqdm_module.write(f"   This step took {time.time() - step_start:.1f}s before failing")
                raise
            
            # Step 5: Analyze long rides (optional)
            step_start = time.time()
            pbar.set_description("🚵 Analyzing long rides")
            debug_logger.info("Step 5: Analyzing long rides...")
            try:
                long_rides, long_ride_analyzer = _analyze_long_rides(
                    all_activities, commute_activities, config
                )
                debug_logger.info(f"Step 5 completed in {time.time() - step_start:.2f}s")
                debug_logger.info(f"Found {len(long_rides)} long rides")
                pbar.update(1)
                pbar.refresh()
                print()  # New line after this phase
            except Exception as e:
                debug_logger.error(f"Step 5 failed: {e}", exc_info=True)
                tqdm_module.write(f"\n❌ ERROR at Step 5 (Analyzing long rides): {e}")
                raise
            
            # Step 6: Optimize routes
            step_start = time.time()
            pbar.set_description("⚡ Optimizing routes")
            debug_logger.info("Step 6: Optimizing routes...")
            try:
                optimization_results = _optimize_and_rank_routes(route_groups, config)
                debug_logger.info(f"Step 6 completed in {time.time() - step_start:.2f}s")
                pbar.update(1)
                pbar.refresh()
                print()  # New line after this phase
            except Exception as e:
                debug_logger.error(f"Step 6 failed: {e}", exc_info=True)
                tqdm_module.write(f"\n❌ ERROR at Step 6 (Optimizing routes): {e}")
                raise
            
            # Step 6.5: Generate next commute recommendations
            step_start = time.time()
            pbar.set_description("🕐 Next commute recommendations")
            debug_logger.info("Step 6.5: Generating next commute recommendations...")
            try:
                from src.next_commute_recommender import NextCommuteRecommender
                next_commute_recommender = NextCommuteRecommender(
                    route_groups, config, (home.lat, home.lon), (work.lat, work.lon)
                )
                next_commutes = next_commute_recommender.get_next_commute_recommendations()
                debug_logger.info(f"Step 6.5 completed in {time.time() - step_start:.2f}s")
                debug_logger.info(f"Generated recommendations for {len(next_commutes)} next commutes")
                logger.info(f"Generated recommendations for {len(next_commutes)} next commutes")
                pbar.refresh()
                print()  # New line after this phase
            except Exception as e:
                debug_logger.error(f"Step 6.5 failed: {e}", exc_info=True)
                tqdm_module.write(f"\n❌ ERROR at Step 6.5 (Next commute recommendations): {e}")
                raise
            
            # Step 7: Generate visualization
            step_start = time.time()
            pbar.set_description("🗺️  Generating map")
            debug_logger.info("Step 7: Generating visualization...")
            try:
                map_html, preview_map_html, visualizer = _generate_visualization(
                    route_groups, home, work, config,
                    long_rides, long_ride_analyzer,
                    optimization_results['optimal_route'],
                    optimization_results['ranked_routes']
                )
                debug_logger.info(f"Step 7 completed in {time.time() - step_start:.2f}s")
                pbar.update(1)
                pbar.refresh()
                print()  # New line after this phase
            except Exception as e:
                debug_logger.error(f"Step 7 failed: {e}", exc_info=True)
                tqdm_module.write(f"\n❌ ERROR at Step 7 (Generating map): {e}")
                raise
            
            # Step 8: Save report
            step_start = time.time()
            pbar.set_description("💾 Saving report")
            debug_logger.info("Step 8: Saving report...")
            try:
                # Build complete analysis results
                analysis_results = {
                    **optimization_results,
                    'route_groups': route_groups,
                    'home': home,
                    'work': work,
                    'map_html': map_html,
                    'preview_map_html': preview_map_html,
                    'all_activities': all_activities,
                    'commute_activities': commute_activities,
                    'visualizer': visualizer,
                    'long_rides': long_rides,
                    'long_ride_analyzer': long_ride_analyzer,
                    'config': config,
                    'next_commutes': next_commutes
                }
                
                # Save and open report
                report_path = _save_report(analysis_results, output_dir, generate_pdf)
                debug_logger.info(f"Step 8 completed in {time.time() - step_start:.2f}s")
                pbar.update(1)
                pbar.refresh()
            except Exception as e:
                debug_logger.error(f"Step 8 failed: {e}", exc_info=True)
                tqdm_module.write(f"\n❌ ERROR at Step 8 (Saving report): {e}")
                raise
        
        # Calculate runtime
        end_time = time.time()
        runtime_seconds = end_time - start_time
        minutes = int(runtime_seconds // 60)
        seconds = runtime_seconds % 60
        runtime_display = f"{minutes}m{seconds:.1f}s"
        
        # Print completion message
        tqdm_module.write("\n" + "="*60)
        tqdm_module.write("✅  ANALYSIS COMPLETE!")
        tqdm_module.write("="*60)
        tqdm_module.write(f"📄  Report: {report_path.name}")
        tqdm_module.write(f"🚴  Route: {analysis_results['optimal_route'].name}")
        tqdm_module.write(f"⭐  Score: {analysis_results['optimal_score']:.1f}/100")
        tqdm_module.write(f"⏱️   Runtime: {runtime_display}")
        tqdm_module.write("="*60 + "\n")
        
        # Log runtime to file for performance tracking
        _log_runtime(runtime_seconds, len(commute_activities), len(route_groups))
        
        _open_report_in_browser(report_path)
        
        debug_logger.info("="*60)
        debug_logger.info("Analysis completed successfully")
        debug_logger.info("="*60)
        
    except KeyboardInterrupt:
        debug_logger.warning("Analysis interrupted by user (Ctrl+C)")
        tqdm_module.write("\n\n⚠️  Analysis interrupted by user")
        tqdm_module.write("Check logs/debug.log for details on where the script stopped")
        raise
    except Exception as e:
        debug_logger.error(f"Analysis failed: {e}", exc_info=True)
        tqdm_module.write(f"\n\n❌ ANALYSIS FAILED")
        tqdm_module.write(f"Error: {e}")
        tqdm_module.write(f"\n📋 Check logs/debug.log for detailed error information")
        tqdm_module.write(f"   Last successful step information is logged there")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze Strava commute routes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # First time setup
  python main.py --auth
  python main.py --fetch --analyze
  
  # Show cached activity statistics
  python main.py --stats
  
  # Fetch most recent 100 activities and analyze
  python main.py --fetch --limit 100 --analyze
  
  # Fetch activities from a specific date onwards
  python main.py --fetch --from-date 2023-01-01 --analyze
  
  # Fetch activities within a date range
  python main.py --fetch --from-date 2023-01-01 --to-date 2023-12-31 --analyze
  
  # Replace cache completely (WARNING: loses existing data)
  python main.py --fetch --replace-cache --analyze
  
  # Re-analyze with cached data
  python main.py --analyze
  
  # Force full reanalysis (auto-enables --analyze)
  python main.py --force-reanalysis
  
  # Use parallel processing (auto-enables --analyze)
  python main.py --parallel 4
  
  # Generate PDF report (auto-enables --analyze)
  python main.py --pdf
  
  # Combine options
  python main.py --force-reanalysis --parallel 4 --pdf
        """
    )
    
    parser.add_argument('--auth', action='store_true',
                       help='Authenticate with Strava (first time only)')
    parser.add_argument('--fetch', action='store_true',
                       help='Fetch new activities from Strava')
    parser.add_argument('--from-date', type=str,
                       help='Fetch activities from this date (YYYY-MM-DD), e.g., 2023-01-01')
    parser.add_argument('--to-date', type=str,
                       help='Fetch activities up to this date (YYYY-MM-DD), e.g., 2024-12-31')
    parser.add_argument('--limit', type=int,
                       help='Maximum number of activities to fetch (default: 500)')
    parser.add_argument('--replace-cache', action='store_true',
                       help='Replace cache instead of merging (use with --fetch)')
    parser.add_argument('--stats', action='store_true',
                       help='Show statistics about cached activities')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze routes and generate report')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Path to configuration file (default: config/config.yaml)')
    parser.add_argument('--output', type=str, default='output/reports',
                       help='Output directory for reports (default: output/reports)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--parallel', type=int, default=2, choices=range(1, 9),
                       help='Number of parallel workers for route analysis (1-8, default: 2)')
    parser.add_argument('--pdf', action='store_true',
                       help='Generate PDF report (slower, adds ~30s)')
    parser.add_argument('--force-reanalysis', action='store_true',
                       help='Clear route grouping cache and reprocess all routes')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Auto-enable --analyze if analysis-specific flags are used
    if args.force_reanalysis or args.pdf or (args.parallel != 2):
        if not args.analyze:
            args.analyze = True
            logger.info("Auto-enabling --analyze due to analysis-specific flags")
    
    # Show help if no arguments
    if not (args.auth or args.fetch or args.stats or args.analyze):
        parser.print_help()
        sys.exit(0)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = load_config(args.config)
        
        # Validate Strava credentials at startup
        logger.info("Validating Strava API credentials...")
        client_id = config.get('strava.client_id')
        client_secret = config.get('strava.client_secret')
        validate_strava_credentials(client_id, client_secret)
        
        # Execute requested operations
        if args.auth:
            authenticate(config)
        
        if args.stats:
            show_cache_stats()
            return  # Exit after showing stats
        
        if args.fetch:
            after_date = None
            before_date = None
            limit = args.limit
            
            if args.from_date:
                try:
                    after_date = datetime.strptime(args.from_date, '%Y-%m-%d')
                except ValueError:
                    print(f"❌ Invalid from-date format: {args.from_date}. Use YYYY-MM-DD")
                    return
            
            if args.to_date:
                try:
                    before_date = datetime.strptime(args.to_date, '%Y-%m-%d')
                except ValueError:
                    print(f"❌ Invalid to-date format: {args.to_date}. Use YYYY-MM-DD")
                    return
            
            # Validate date range
            if after_date and before_date and after_date >= before_date:
                print(f"❌ Invalid date range: from-date must be before to-date")
                return
            
            # If both from and to dates specified, fetch ALL activities in range (no limit)
            if after_date and before_date:
                if limit:
                    print(f"ℹ️  Note: --limit ignored when date range is specified")
                limit = 2000  # Set reasonable limit to get all activities in range
                print(f"📅 Fetching ALL activities from {after_date.date()} to {before_date.date()}")
            
            if args.replace_cache:
                print("⚠️  Cache will be REPLACED (not merged)")
            
            fetch_activities(config, after_date, before_date, limit, args.replace_cache)
        
        if args.analyze:
            analyze_routes(config, args.output, n_workers=args.parallel,
                          generate_pdf=args.pdf, force_reanalysis=args.force_reanalysis)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

# Made with Bob
