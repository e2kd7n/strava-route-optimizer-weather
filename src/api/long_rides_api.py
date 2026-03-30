"""
Long Rides API Server

Provides REST API endpoints for long ride recommendations.
"""

import logging
from typing import List, Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from ..long_ride_analyzer import LongRideAnalyzer, LongRide
from ..weather_fetcher import WeatherFetcher
from ..config import Config

logger = logging.getLogger(__name__)


class LongRidesAPI:
    """Flask API server for long ride recommendations."""
    
    def __init__(self, long_rides: List[LongRide], config: Config):
        """
        Initialize API server.
        
        Args:
            long_rides: List of LongRide objects
            config: Configuration object
        """
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        
        self.long_rides = long_rides
        self.config = config
        self.weather_fetcher = WeatherFetcher()
        self.geocoder = Nominatim(user_agent="ride-optimizer")
        
        # Register routes
        self._register_routes()
        
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'total_rides': len(self.long_rides)
            })
        
        @self.app.route('/api/long-rides/recommendations', methods=['GET'])
        def get_recommendations():
            """
            Get long ride recommendations based on location and filters.
            
            Query Parameters:
                lat (float): Latitude
                lon (float): Longitude
                min_distance (float, optional): Minimum distance in km
                max_distance (float, optional): Maximum distance in km
                min_duration (float, optional): Minimum duration in hours
                max_duration (float, optional): Maximum duration in hours
                ride_type (str, optional): 'all', 'loops', or 'point-to-point'
            
            Returns:
                JSON with list of recommended rides
            """
            try:
                # Parse query parameters
                lat = float(request.args.get('lat', 0))
                lon = float(request.args.get('lon', 0))
                min_distance = float(request.args.get('min_distance', 0))
                max_distance = float(request.args.get('max_distance', 999))
                min_duration = float(request.args.get('min_duration', 0))
                max_duration = float(request.args.get('max_duration', 999))
                ride_type = request.args.get('ride_type', 'all')
                
                # Filter rides
                filtered_rides = []
                for ride in self.long_rides:
                    # Distance filter
                    if not (min_distance <= ride.distance_km <= max_distance):
                        continue
                    
                    # Duration filter
                    if not (min_duration <= ride.duration_hours <= max_duration):
                        continue
                    
                    # Ride type filter
                    if ride_type == 'loops' and not ride.is_loop:
                        continue
                    if ride_type == 'point-to-point' and ride.is_loop:
                        continue
                    
                    filtered_rides.append(ride)
                
                # Sort by distance from location
                from geopy.distance import geodesic
                for ride in filtered_rides:
                    ride.distance_to_location = geodesic(
                        (lat, lon),
                        ride.start_location
                    ).kilometers
                
                filtered_rides.sort(key=lambda r: r.distance_to_location)
                
                # Limit to top 20
                filtered_rides = filtered_rides[:20]
                
                # Format response
                recommendations = []
                for ride in filtered_rides:
                    recommendations.append({
                        'activity_id': ride.activity_id,
                        'name': ride.name,
                        'distance_km': ride.distance_km,
                        'duration_hours': ride.duration_hours,
                        'elevation_gain': ride.elevation_gain,
                        'average_speed': ride.average_speed,
                        'is_loop': ride.is_loop,
                        'start_location': ride.start_location,
                        'distance_to_location': ride.distance_to_location,
                        'coordinates': ride.coordinates,
                        'uses': ride.uses,
                        'activity_ids': ride.activity_ids or [ride.activity_id],
                        'activity_dates': ride.activity_dates or [ride.timestamp[:10] if ride.timestamp else "Unknown"]
                    })
                
                return jsonify({
                    'success': True,
                    'count': len(recommendations),
                    'recommendations': recommendations
                })
                
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid parameter: {str(e)}'
                }), 400
            except Exception as e:
                logger.error(f"Error getting recommendations: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Internal server error'
                }), 500
        
        @self.app.route('/api/long-rides/geocode', methods=['POST'])
        def geocode_location():
            """
            Geocode a location string to coordinates.
            
            Request Body:
                {
                    "location": "Chicago, IL"
                }
            
            Returns:
                JSON with lat/lon coordinates
            """
            try:
                data = request.get_json()
                location = data.get('location', '')
                
                if not location:
                    return jsonify({
                        'success': False,
                        'error': 'Location parameter required'
                    }), 400
                
                # Geocode location
                result = self.geocoder.geocode(location, timeout=10)
                
                if not result:
                    return jsonify({
                        'success': False,
                        'error': 'Location not found'
                    }), 404
                
                return jsonify({
                    'success': True,
                    'lat': result.latitude,
                    'lon': result.longitude,
                    'display_name': result.address
                })
                
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                logger.error(f"Geocoding error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Geocoding service unavailable'
                }), 503
            except Exception as e:
                logger.error(f"Error geocoding location: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Internal server error'
                }), 500
        
        @self.app.route('/api/long-rides/weather', methods=['GET'])
        def get_weather():
            """
            Get current weather for a location.
            
            Query Parameters:
                lat (float): Latitude
                lon (float): Longitude
            
            Returns:
                JSON with weather data
            """
            try:
                lat = float(request.args.get('lat', 0))
                lon = float(request.args.get('lon', 0))
                
                if lat == 0 or lon == 0:
                    return jsonify({
                        'success': False,
                        'error': 'Valid lat/lon required'
                    }), 400
                
                # Fetch weather
                weather = self.weather_fetcher.get_weather(lat, lon)
                
                if not weather:
                    return jsonify({
                        'success': False,
                        'error': 'Weather data unavailable'
                    }), 503
                
                return jsonify({
                    'success': True,
                    'weather': {
                        'temperature': weather.get('temperature'),
                        'wind_speed': weather.get('wind_speed'),
                        'wind_direction': weather.get('wind_direction'),
                        'precipitation': weather.get('precipitation', 0),
                        'conditions': weather.get('conditions', 'Unknown')
                    }
                })
                
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid parameter: {str(e)}'
                }), 400
            except Exception as e:
                logger.error(f"Error fetching weather: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Internal server error'
                }), 500
    
    def run(self, host='localhost', port=5000, debug=False):
        """
        Run the API server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        logger.info(f"Starting Long Rides API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_api(long_rides: List[LongRide], config: Config) -> LongRidesAPI:
    """
    Factory function to create API instance.
    
    Args:
        long_rides: List of LongRide objects
        config: Configuration object
    
    Returns:
        LongRidesAPI instance
    """
    return LongRidesAPI(long_rides, config)

# Made with Bob
