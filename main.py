#!/usr/bin/env python3
"""
Strava Commute Route Analyzer - Main Entry Point

Analyzes Strava cycling activities to determine optimal commute routes
and recommend long recreational rides.
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

from src.config import load_config
from src.auth import StravaAuthenticator, get_authenticated_client
from src.data_fetcher import StravaDataFetcher
from src.location_finder import LocationFinder
from src.route_analyzer import RouteAnalyzer
from src.optimizer import RouteOptimizer
from src.visualizer import RouteVisualizer
from src.report_generator import ReportGenerator
from src.long_ride_analyzer import LongRideAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def authenticate(config):
    """
    Perform Strava authentication.
    
    Args:
        config: Configuration object
    """
    logger.info("Starting authentication...")
    
    authenticator = StravaAuthenticator(
        client_id=config.get('strava.client_id'),
        client_secret=config.get('strava.client_secret')
    )
    
    tokens = authenticator.authenticate()
    logger.info("Authentication successful!")
    logger.info(f"Access token expires at: {tokens['expires_at']}")


def fetch_activities(config):
    """
    Fetch activities from Strava API.
    
    Args:
        config: Configuration object
    """
    logger.info("Fetching activities from Strava...")
    
    try:
        client = get_authenticated_client(config)
        fetcher = StravaDataFetcher(client, config)
        
        # Fetch activities
        activities = fetcher.fetch_activities()
        
        # Cache activities
        fetcher.cache_activities(activities)
        
        logger.info(f"Successfully fetched and cached {len(activities)} activities")
        
    except Exception as e:
        logger.error(f"Failed to fetch activities: {e}")
        raise


def analyze_routes(config, output_dir):
    """
    Analyze routes and generate report.
    
    Args:
        config: Configuration object
        output_dir: Output directory for reports
    """
    logger.info("Starting route analysis...")
    
    try:
        # Get authenticated client
        client = get_authenticated_client(config)
        fetcher = StravaDataFetcher(client, config)
        
        # Load cached activities
        logger.info("Loading activities from cache...")
        all_activities = fetcher.load_cached_activities()
        
        if not all_activities:
            logger.error("No cached activities found. Run with --fetch first.")
            return
        
        logger.info(f"Loaded {len(all_activities)} activities from cache")
        
        # Filter commute activities
        logger.info("Filtering commute activities...")
        commute_activities = fetcher.filter_commute_activities(all_activities)
        
        if len(commute_activities) < 10:
            logger.error(f"Insufficient commute activities: {len(commute_activities)} found, need at least 10")
            logger.info("Try adjusting distance filters in config/config.yaml")
            return
        
        logger.info(f"Found {len(commute_activities)} potential commute activities")
        
        # Identify home and work locations
        logger.info("Identifying home and work locations...")
        finder = LocationFinder(commute_activities, config)
        
        try:
            home, work = finder.identify_home_work()
        except ValueError as e:
            logger.error(f"Failed to identify locations: {e}")
            logger.info("Try adjusting clustering parameters in config/config.yaml")
            return
        
        logger.info(f"Home: ({home.lat:.4f}, {home.lon:.4f}) - {home.activity_count} activities")
        logger.info(f"Work: ({work.lat:.4f}, {work.lon:.4f}) - {work.activity_count} activities")
        
        # Analyze commute routes
        logger.info("Analyzing routes between home and work...")
        analyzer = RouteAnalyzer(commute_activities, home, work, config)
        route_groups = analyzer.group_similar_routes()
        
        if not route_groups:
            logger.error("No route groups found")
            return
        
        logger.info(f"Found {len(route_groups)} commute route variants")
        for group in route_groups:
            logger.info(f"  - {group.id}: {group.frequency} uses")
        
        # Analyze long rides (if enabled)
        long_rides = []
        long_ride_analyzer = None
        if config.get('long_rides.enabled', True):
            logger.info("Analyzing long recreational rides...")
            long_ride_analyzer = LongRideAnalyzer(all_activities, config)
            
            # Classify activities
            _, long_ride_activities = long_ride_analyzer.classify_activities(commute_activities)
            logger.info(f"Found {len(long_ride_activities)} long ride activities")
            
            # Extract long rides
            if long_ride_activities:
                long_rides = long_ride_analyzer.extract_long_rides(long_ride_activities)
                logger.info(f"Extracted {len(long_rides)} long rides for analysis")
                
                # Show some statistics
                if long_rides:
                    distances = [r.distance_km for r in long_rides]
                    logger.info(f"  Distance range: {min(distances):.1f} - {max(distances):.1f} km")
                    logger.info(f"  Average distance: {sum(distances)/len(distances):.1f} km")
                    loop_count = sum(1 for r in long_rides if r.is_loop)
                    logger.info(f"  Loop rides: {loop_count} ({loop_count/len(long_rides)*100:.1f}%)")
        
        # Optimize routes
        logger.info("Optimizing route selection...")
        optimizer = RouteOptimizer(route_groups, config)
        ranked_routes = optimizer.rank_routes()
        optimal_route, optimal_score, optimal_breakdown = optimizer.get_optimal_route()
        recommendations = optimizer.get_route_recommendations()
        
        logger.info(f"Optimal route: {optimal_route.id}")
        logger.info(f"  Score: {optimal_score:.2f}")
        logger.info(f"  Time: {optimal_breakdown['time']:.1f}, Distance: {optimal_breakdown['distance']:.1f}, Safety: {optimal_breakdown['safety']:.1f}")
        
        # Generate map with long rides support
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
        
        # Generate report with timestamp
        logger.info("Generating HTML report...")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'commute_analysis_{timestamp}.html'
        report_path = output_path / report_filename
        
        analysis_results = {
            'optimal_route': optimal_route,
            'ranked_routes': ranked_routes,
            'recommendations': recommendations,
            'route_groups': route_groups,
            'home': home,
            'work': work,
            'map_html': map_html,
            'all_activities': all_activities,
            'commute_activities': commute_activities,
            'optimizer': optimizer,
            'visualizer': visualizer,
            'long_rides': long_rides,
            'long_ride_analyzer': long_ride_analyzer
        }
        
        generator = ReportGenerator(analysis_results)
        generator.generate_report(str(report_path))
        
        logger.info(f"✅ Analysis complete!")
        logger.info(f"📄 Report saved to: {report_path}")
        logger.info(f"🚴 Optimal route: {optimal_route.id} (score: {optimal_score:.2f})")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
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
  
  # Update and re-analyze
  python main.py --fetch --analyze
  
  # Re-analyze with cached data
  python main.py --analyze
        """
    )
    
    parser.add_argument('--auth', action='store_true',
                       help='Authenticate with Strava (first time only)')
    parser.add_argument('--fetch', action='store_true',
                       help='Fetch new activities from Strava')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze routes and generate report')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Path to configuration file (default: config/config.yaml)')
    parser.add_argument('--output', type=str, default='output/reports',
                       help='Output directory for reports (default: output/reports)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Show help if no arguments
    if not (args.auth or args.fetch or args.analyze):
        parser.print_help()
        sys.exit(0)
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = load_config(args.config)
        
        # Execute requested operations
        if args.auth:
            authenticate(config)
        
        if args.fetch:
            fetch_activities(config)
        
        if args.analyze:
            analyze_routes(config, args.output)
        
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
