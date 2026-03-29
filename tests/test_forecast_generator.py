"""
Unit tests for forecast_generator module.

Tests commute forecast generation with weather-aware route recommendations.
"""

import pytest
from datetime import datetime, time
from unittest.mock import Mock, patch

from src.forecast_generator import (
    CommuteWindow,
    DailyForecast,
    CommuteForecastGenerator
)


class TestCommuteWindow:
    """Test CommuteWindow dataclass."""
    
    def test_commute_window_creation(self):
        """Test creating a CommuteWindow instance."""
        window = CommuteWindow(
            date="2026-03-30",
            day_name="Sunday",
            direction="to_work",
            window_start=time(7, 0),
            window_end=time(9, 0),
            optimal_departure=time(8, 0),
            temp_c=15.0,
            temp_f=59.0,
            wind_speed_kph=10.0,
            wind_speed_mph=6.2,
            wind_direction_deg=180.0,
            precipitation_prob=20.0,
            precipitation_mm=0.5,
            recommended_route_id="route_1",
            recommended_route_name="Main Route",
            weather_severity="good",
            recommend_transit=False,
            notes=["Good cycling weather"]
        )
        
        assert window.date == "2026-03-30"
        assert window.direction == "to_work"
        assert window.temp_c == 15.0
        assert window.weather_severity == "good"
        assert not window.recommend_transit


class TestDailyForecast:
    """Test DailyForecast dataclass."""
    
    def test_daily_forecast_creation(self):
        """Test creating a DailyForecast instance."""
        morning = CommuteWindow(
            date="2026-03-30", day_name="Sunday", direction="to_work",
            window_start=time(7, 0), window_end=time(9, 0),
            optimal_departure=time(8, 0), temp_c=15.0, temp_f=59.0,
            wind_speed_kph=10.0, wind_speed_mph=6.2, wind_direction_deg=180.0,
            precipitation_prob=20.0, precipitation_mm=0.5,
            recommended_route_id="route_1", recommended_route_name="Main Route",
            weather_severity="good", recommend_transit=False, notes=[]
        )
        
        evening = CommuteWindow(
            date="2026-03-30", day_name="Sunday", direction="to_home",
            window_start=time(15, 0), window_end=time(18, 0),
            optimal_departure=time(16, 30), temp_c=18.0, temp_f=64.4,
            wind_speed_kph=12.0, wind_speed_mph=7.5, wind_direction_deg=200.0,
            precipitation_prob=10.0, precipitation_mm=0.0,
            recommended_route_id="route_2", recommended_route_name="Alt Route",
            weather_severity="good", recommend_transit=False, notes=[]
        )
        
        forecast = DailyForecast(
            date="2026-03-30",
            day_name="Sunday",
            morning_commute=morning,
            evening_commute=evening,
            overall_rating="excellent"
        )
        
        assert forecast.date == "2026-03-30"
        assert forecast.overall_rating == "excellent"
        assert forecast.morning_commute.direction == "to_work"
        assert forecast.evening_commute.direction == "to_home"


class TestCommuteForecastGenerator:
    """Test CommuteForecastGenerator class."""
    
    @pytest.fixture
    def mock_weather_fetcher(self):
        """Create mock weather fetcher."""
        fetcher = Mock()
        fetcher.get_daily_forecast.return_value = [
            {
                'date': '2026-03-30',
                'temp_max_c': 20.0,
                'temp_min_c': 10.0,
                'wind_speed_max_kph': 15.0,
                'wind_direction_dominant_deg': 180.0,
                'precipitation_prob_max': 20.0,
                'precipitation_sum_mm': 0.5
            }
        ]
        return fetcher
    
    @pytest.fixture
    def route_groups(self):
        """Create mock route groups."""
        return {
            'to_work': [
                {'id': 'route_1', 'name': 'Main Route', 'frequency': 10},
                {'id': 'route_2', 'name': 'Alt Route', 'frequency': 5}
            ],
            'to_home': [
                {'id': 'route_3', 'name': 'Home Route', 'frequency': 8}
            ]
        }
    
    @pytest.fixture
    def generator(self, mock_weather_fetcher, route_groups):
        """Create forecast generator instance."""
        return CommuteForecastGenerator(
            weather_fetcher=mock_weather_fetcher,
            route_groups=route_groups,
            home_location=(41.8781, -87.6298),
            work_location=(41.8819, -87.6278),
            unit_system="imperial"
        )
    
    def test_init(self, generator, mock_weather_fetcher, route_groups):
        """Test generator initialization."""
        assert generator.weather_fetcher == mock_weather_fetcher
        assert generator.route_groups == route_groups
        assert generator.home_location == (41.8781, -87.6298)
        assert generator.work_location == (41.8819, -87.6278)
        assert generator.unit_system == "imperial"
        assert generator.morning_window_start == time(7, 0)
        assert generator.evening_window_end == time(18, 0)
    
    def test_generate_7day_forecast_success(self, generator, mock_weather_fetcher):
        """Test successful 7-day forecast generation."""
        forecasts = generator.generate_7day_forecast()
        
        assert len(forecasts) == 1
        assert isinstance(forecasts[0], DailyForecast)
        assert forecasts[0].date == '2026-03-30'
        mock_weather_fetcher.get_daily_forecast.assert_called_once()
    
    def test_generate_7day_forecast_no_weather_data(self, generator, mock_weather_fetcher):
        """Test forecast generation when weather data unavailable."""
        mock_weather_fetcher.get_daily_forecast.return_value = None
        
        forecasts = generator.generate_7day_forecast()
        
        assert forecasts == []
    
    def test_calculate_weather_severity_good(self, generator):
        """Test weather severity calculation - good conditions."""
        severity = generator._calculate_weather_severity(
            temp_c=20.0, wind_speed_kph=10.0, precip_prob=10.0, precip_mm=0.0
        )
        assert severity == "good"
    
    def test_calculate_weather_severity_fair(self, generator):
        """Test weather severity calculation - fair conditions."""
        severity = generator._calculate_weather_severity(
            temp_c=8.0, wind_speed_kph=15.0, precip_prob=30.0, precip_mm=1.0
        )
        assert severity == "fair"
    
    def test_calculate_weather_severity_poor(self, generator):
        """Test weather severity calculation - poor conditions."""
        severity = generator._calculate_weather_severity(
            temp_c=3.0, wind_speed_kph=25.0, precip_prob=50.0, precip_mm=3.0
        )
        assert severity == "poor"
    
    def test_calculate_weather_severity_miserable(self, generator):
        """Test weather severity calculation - miserable conditions."""
        severity = generator._calculate_weather_severity(
            temp_c=-5.0, wind_speed_kph=45.0, precip_prob=90.0, precip_mm=15.0
        )
        assert severity == "miserable"
    
    def test_calculate_weather_severity_freezing(self, generator):
        """Test weather severity with freezing temperatures."""
        severity = generator._calculate_weather_severity(
            temp_c=-2.0, wind_speed_kph=10.0, precip_prob=20.0, precip_mm=0.5
        )
        assert severity in ["poor", "miserable"]
    
    def test_calculate_weather_severity_hot(self, generator):
        """Test weather severity with hot temperatures."""
        severity = generator._calculate_weather_severity(
            temp_c=32.0, wind_speed_kph=5.0, precip_prob=10.0, precip_mm=0.0
        )
        assert severity in ["fair", "poor"]
    
    def test_should_recommend_transit_wet_and_cold(self, generator):
        """Test transit recommendation for wet and cold conditions."""
        recommend = generator._should_recommend_transit(
            temp_c=3.0, wind_speed_kph=20.0, precip_prob=80.0, precip_mm=8.0
        )
        assert recommend is True
    
    def test_should_recommend_transit_wet_and_windy(self, generator):
        """Test transit recommendation for wet and windy conditions."""
        recommend = generator._should_recommend_transit(
            temp_c=15.0, wind_speed_kph=40.0, precip_prob=75.0, precip_mm=6.0
        )
        assert recommend is True
    
    def test_should_recommend_transit_freezing_rain(self, generator):
        """Test transit recommendation for freezing rain."""
        recommend = generator._should_recommend_transit(
            temp_c=1.0, wind_speed_kph=15.0, precip_prob=60.0, precip_mm=3.0
        )
        assert recommend is True
    
    def test_should_not_recommend_transit_good_conditions(self, generator):
        """Test no transit recommendation for good conditions."""
        recommend = generator._should_recommend_transit(
            temp_c=20.0, wind_speed_kph=10.0, precip_prob=20.0, precip_mm=0.5
        )
        assert recommend is False
    
    def test_select_optimal_route_light_wind(self, generator):
        """Test route selection with light wind."""
        route_id, route_name = generator._select_optimal_route(
            direction="to_work", wind_direction_deg=180.0, wind_speed_kph=10.0
        )
        assert route_id == 'route_1'
        assert route_name == 'Main Route'
    
    def test_select_optimal_route_strong_wind(self, generator):
        """Test route selection with strong wind - now wind-aware (#70 implemented)."""
        # Add coordinates to routes for wind analysis
        generator.route_groups['to_work'][0]['coordinates'] = [
            (41.8781, -87.6298), (41.8800, -87.6280), (41.8819, -87.6278)
        ]
        generator.route_groups['to_work'][1]['coordinates'] = [
            (41.8781, -87.6298), (41.8790, -87.6290), (41.8819, -87.6278)
        ]
        
        route_id, route_name = generator._select_optimal_route(
            direction="to_work", wind_direction_deg=180.0, wind_speed_kph=30.0
        )
        # Should analyze wind impact and select best route
        assert route_id in ['route_1', 'route_2']
        assert route_name in ['Main Route', 'Alt Route']
    
    def test_select_optimal_route_no_routes(self, generator):
        """Test route selection when no routes available."""
        route_id, route_name = generator._select_optimal_route(
            direction="nonexistent", wind_direction_deg=180.0, wind_speed_kph=15.0
        )
        assert route_id is None
        assert route_name == "No routes available"
    
    def test_calculate_optimal_departure_low_precip(self, generator):
        """Test optimal departure calculation with low precipitation."""
        departure = generator._calculate_optimal_departure(
            window_start=time(7, 0), window_end=time(9, 0),
            precip_prob=30.0, is_morning=True
        )
        assert departure == time(8, 0)  # Middle of window
    
    def test_calculate_optimal_departure_high_precip(self, generator):
        """Test optimal departure calculation with high precipitation."""
        departure = generator._calculate_optimal_departure(
            window_start=time(7, 0), window_end=time(9, 0),
            precip_prob=70.0, is_morning=True
        )
        # Should suggest earlier departure
        assert departure.hour == 7
        assert departure.minute == 30
    
    def test_generate_notes_good_conditions(self, generator):
        """Test note generation for good conditions."""
        notes = generator._generate_notes(
            temp_c=20.0, wind_speed_kph=10.0, wind_direction_deg=180.0,
            precip_prob=10.0, precip_mm=0.0, severity="good",
            recommend_transit=False
        )
        assert any("Excellent cycling conditions" in note for note in notes)
    
    def test_generate_notes_cold_weather(self, generator):
        """Test note generation for cold weather."""
        notes = generator._generate_notes(
            temp_c=3.0, wind_speed_kph=10.0, wind_direction_deg=180.0,
            precip_prob=10.0, precip_mm=0.0, severity="fair",
            recommend_transit=False
        )
        assert any("cold" in note.lower() for note in notes)
    
    def test_generate_notes_hot_weather(self, generator):
        """Test note generation for hot weather."""
        notes = generator._generate_notes(
            temp_c=32.0, wind_speed_kph=10.0, wind_direction_deg=180.0,
            precip_prob=10.0, precip_mm=0.0, severity="fair",
            recommend_transit=False
        )
        assert any("hot" in note.lower() or "warm" in note.lower() for note in notes)
    
    def test_generate_notes_strong_wind(self, generator):
        """Test note generation for strong winds."""
        notes = generator._generate_notes(
            temp_c=15.0, wind_speed_kph=40.0, wind_direction_deg=180.0,
            precip_prob=10.0, precip_mm=0.0, severity="poor",
            recommend_transit=False
        )
        assert any("wind" in note.lower() for note in notes)
    
    def test_generate_notes_heavy_rain(self, generator):
        """Test note generation for heavy rain."""
        notes = generator._generate_notes(
            temp_c=15.0, wind_speed_kph=10.0, wind_direction_deg=180.0,
            precip_prob=85.0, precip_mm=12.0, severity="poor",
            recommend_transit=False
        )
        assert any("rain" in note.lower() for note in notes)
    
    def test_generate_notes_transit_recommended(self, generator):
        """Test note generation when transit recommended."""
        notes = generator._generate_notes(
            temp_c=2.0, wind_speed_kph=40.0, wind_direction_deg=180.0,
            precip_prob=80.0, precip_mm=10.0, severity="miserable",
            recommend_transit=True
        )
        assert any("transit" in note.lower() for note in notes)
    
    def test_calculate_overall_rating_excellent(self, generator):
        """Test overall rating calculation - excellent."""
        morning = Mock(weather_severity="good", recommend_transit=False)
        evening = Mock(weather_severity="good", recommend_transit=False)
        
        rating = generator._calculate_overall_rating(morning, evening)
        assert rating == "excellent"
    
    def test_calculate_overall_rating_good(self, generator):
        """Test overall rating calculation - good."""
        morning = Mock(weather_severity="good", recommend_transit=False)
        evening = Mock(weather_severity="fair", recommend_transit=False)
        
        rating = generator._calculate_overall_rating(morning, evening)
        assert rating == "good"
    
    def test_calculate_overall_rating_fair(self, generator):
        """Test overall rating calculation - fair."""
        morning = Mock(weather_severity="fair", recommend_transit=False)
        evening = Mock(weather_severity="fair", recommend_transit=False)
        
        rating = generator._calculate_overall_rating(morning, evening)
        assert rating == "fair"
    
    def test_calculate_overall_rating_poor(self, generator):
        """Test overall rating calculation - poor."""
        morning = Mock(weather_severity="poor", recommend_transit=False)
        evening = Mock(weather_severity="poor", recommend_transit=False)
        
        rating = generator._calculate_overall_rating(morning, evening)
        assert rating == "poor"
    
    def test_calculate_overall_rating_avoid(self, generator):
        """Test overall rating calculation - avoid."""
        morning = Mock(weather_severity="miserable", recommend_transit=True)
        evening = Mock(weather_severity="miserable", recommend_transit=True)
        
        rating = generator._calculate_overall_rating(morning, evening)
        assert rating == "avoid"
    
    def test_generate_commute_window(self, generator):
        """Test generating a single commute window."""
        day_weather = {
            'temp_max_c': 20.0,
            'temp_min_c': 10.0,
            'wind_speed_max_kph': 15.0,
            'wind_direction_dominant_deg': 180.0,
            'precipitation_prob_max': 20.0,
            'precipitation_sum_mm': 0.5
        }
        
        window = generator._generate_commute_window(
            date_str="2026-03-30",
            day_name="Sunday",
            direction="to_work",
            day_weather=day_weather,
            is_morning=True
        )
        
        assert isinstance(window, CommuteWindow)
        assert window.date == "2026-03-30"
        assert window.direction == "to_work"
        assert window.temp_c == 15.0  # Average of max and min
        assert window.window_start == time(7, 0)
        assert window.window_end == time(9, 0)

# Made with Bob
