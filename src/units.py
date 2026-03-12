"""
Unit conversion utilities.

Handles conversion between metric and imperial units.
"""

from typing import Literal

UnitSystem = Literal['metric', 'imperial']


class UnitConverter:
    """Handles unit conversions and formatting."""
    
    def __init__(self, system: UnitSystem = 'metric'):
        """
        Initialize unit converter.
        
        Args:
            system: Unit system to use ('metric' or 'imperial')
        """
        self.system = system
    
    def distance(self, meters: float, precision: int = 2) -> str:
        """
        Convert distance to appropriate unit.
        
        Args:
            meters: Distance in meters
            precision: Decimal places for formatting
            
        Returns:
            Formatted string with unit
        """
        if self.system == 'imperial':
            miles = meters / 1609.34
            return f"{miles:.{precision}f} mi"
        else:
            km = meters / 1000
            return f"{km:.{precision}f} km"
    
    def distance_value(self, meters: float) -> float:
        """
        Convert distance to appropriate unit (value only).
        
        Args:
            meters: Distance in meters
            
        Returns:
            Distance in target unit
        """
        if self.system == 'imperial':
            return meters / 1609.34  # miles
        else:
            return meters / 1000  # km
    
    def distance_unit(self) -> str:
        """Get distance unit label."""
        return 'mi' if self.system == 'imperial' else 'km'
    
    def speed(self, meters_per_second: float, precision: int = 1) -> str:
        """
        Convert speed to appropriate unit.
        
        Args:
            meters_per_second: Speed in m/s
            precision: Decimal places for formatting
            
        Returns:
            Formatted string with unit
        """
        if self.system == 'imperial':
            mph = meters_per_second * 2.23694
            return f"{mph:.{precision}f} mph"
        else:
            kmh = meters_per_second * 3.6
            return f"{kmh:.{precision}f} km/h"
    
    def speed_value(self, meters_per_second: float) -> float:
        """
        Convert speed to appropriate unit (value only).
        
        Args:
            meters_per_second: Speed in m/s
            
        Returns:
            Speed in target unit
        """
        if self.system == 'imperial':
            return meters_per_second * 2.23694  # mph
        else:
            return meters_per_second * 3.6  # km/h
    
    def speed_unit(self) -> str:
        """Get speed unit label."""
        return 'mph' if self.system == 'imperial' else 'km/h'
    
    def wind_speed(self, meters_per_second: float, precision: int = 1) -> str:
        """
        Convert wind speed to appropriate unit.
        
        Args:
            meters_per_second: Wind speed in m/s
            precision: Decimal places for formatting
            
        Returns:
            Formatted string with unit
        """
        if self.system == 'imperial':
            mph = meters_per_second * 2.23694
            return f"{mph:.{precision}f} mph"
        else:
            # Keep m/s for metric (common in weather)
            return f"{meters_per_second:.{precision}f} m/s"
    
    def wind_speed_value(self, meters_per_second: float) -> float:
        """
        Convert wind speed to appropriate unit (value only).
        
        Args:
            meters_per_second: Wind speed in m/s
            
        Returns:
            Wind speed in target unit
        """
        if self.system == 'imperial':
            return meters_per_second * 2.23694  # mph
        else:
            return meters_per_second  # m/s
    
    def wind_speed_unit(self) -> str:
        """Get wind speed unit label."""
        return 'mph' if self.system == 'imperial' else 'm/s'
    
    def temperature(self, celsius: float, precision: int = 1) -> str:
        """
        Convert temperature to appropriate unit.
        
        Args:
            celsius: Temperature in Celsius
            precision: Decimal places for formatting
            
        Returns:
            Formatted string with unit
        """
        if self.system == 'imperial':
            fahrenheit = (celsius * 9/5) + 32
            return f"{fahrenheit:.{precision}f}°F"
        else:
            return f"{celsius:.{precision}f}°C"
    
    def temperature_value(self, celsius: float) -> float:
        """
        Convert temperature to appropriate unit (value only).
        
        Args:
            celsius: Temperature in Celsius
            
        Returns:
            Temperature in target unit
        """
        if self.system == 'imperial':
            return (celsius * 9/5) + 32  # Fahrenheit
        else:
            return celsius  # Celsius
    
    def temperature_unit(self) -> str:
        """Get temperature unit label."""
        return '°F' if self.system == 'imperial' else '°C'
    
    def elevation(self, meters: float, precision: int = 0) -> str:
        """
        Convert elevation to appropriate unit.
        
        Args:
            meters: Elevation in meters
            precision: Decimal places for formatting
            
        Returns:
            Formatted string with unit
        """
        if self.system == 'imperial':
            feet = meters * 3.28084
            return f"{feet:.{precision}f} ft"
        else:
            return f"{meters:.{precision}f} m"
    
    def elevation_value(self, meters: float) -> float:
        """
        Convert elevation to appropriate unit (value only).
        
        Args:
            meters: Elevation in meters
            
        Returns:
            Elevation in target unit
        """
        if self.system == 'imperial':
            return meters * 3.28084  # feet
        else:
            return meters  # meters
    
    def elevation_unit(self) -> str:
        """Get elevation unit label."""
        return 'ft' if self.system == 'imperial' else 'm'

# Made with Bob
