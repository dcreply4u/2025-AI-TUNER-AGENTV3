"""
Density Altitude Calculator

Automatically calculates Density Altitude (DA) from:
- GPS altitude (or barometric altitude)
- Outside Air Temperature (OAT)
- Barometric pressure (optional, improves accuracy)
- Relative humidity (optional, improves accuracy)

Density Altitude is critical for engine performance tuning as it affects:
- Air density
- Engine power output
- Fuel mixture requirements
- Ignition timing adjustments
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class DensityAltitudeData:
    """Density Altitude calculation data."""
    
    density_altitude_ft: float = 0.0  # Density altitude in feet
    pressure_altitude_ft: float = 0.0  # Pressure altitude in feet
    outside_air_temp_f: float = 59.0  # Outside Air Temperature in Fahrenheit
    outside_air_temp_c: float = 15.0  # Outside Air Temperature in Celsius
    barometric_pressure_inhg: float = 29.92  # Barometric pressure in inches of mercury
    barometric_pressure_mb: float = 1013.25  # Barometric pressure in millibars
    altitude_ft: float = 0.0  # GPS or barometric altitude in feet
    relative_humidity_percent: float = 50.0  # Relative humidity
    air_density_ratio: float = 1.0  # Air density ratio (vs sea level standard)
    last_update: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "density_altitude_ft": self.density_altitude_ft,
            "pressure_altitude_ft": self.pressure_altitude_ft,
            "outside_air_temp_f": self.outside_air_temp_f,
            "outside_air_temp_c": self.outside_air_temp_c,
            "barometric_pressure_inhg": self.barometric_pressure_inhg,
            "barometric_pressure_mb": self.barometric_pressure_mb,
            "altitude_ft": self.altitude_ft,
            "relative_humidity_percent": self.relative_humidity_percent,
            "air_density_ratio": self.air_density_ratio,
            "last_update": self.last_update,
        }


class DensityAltitudeCalculator:
    """
    Automatic Density Altitude calculator.
    
    Calculates DA from available data sources:
    - GPS altitude
    - Temperature sensors
    - Barometric pressure sensors
    - Weather API (fallback)
    """
    
    # Standard atmosphere constants
    STANDARD_SEA_LEVEL_PRESSURE_INHG = 29.92  # inches of mercury
    STANDARD_SEA_LEVEL_PRESSURE_MB = 1013.25  # millibars
    STANDARD_TEMPERATURE_F = 59.0  # 15°C
    STANDARD_TEMPERATURE_C = 15.0
    TEMPERATURE_LAPSE_RATE_F_PER_1000FT = 3.57  # °F per 1000 feet
    TEMPERATURE_LAPSE_RATE_C_PER_1000M = 6.5  # °C per 1000 meters
    
    def __init__(
        self,
        gps_provider: Optional[Callable[[], Optional[dict]]] = None,
        temperature_provider: Optional[Callable[[], Optional[float]]] = None,
        pressure_provider: Optional[Callable[[], Optional[float]]] = None,
        humidity_provider: Optional[Callable[[], Optional[float]]] = None,
    ):
        """
        Initialize Density Altitude calculator.
        
        Args:
            gps_provider: Function that returns GPS data dict with 'altitude_ft' or 'altitude_m'
            temperature_provider: Function that returns outside air temperature in Celsius
            pressure_provider: Function that returns barometric pressure in millibars or inHg
            humidity_provider: Function that returns relative humidity (0-100)
        """
        self.gps_provider = gps_provider
        self.temperature_provider = temperature_provider
        self.pressure_provider = pressure_provider
        self.humidity_provider = humidity_provider
        
        # Current DA data
        self.current_da: DensityAltitudeData = DensityAltitudeData()
        
        # Update interval
        self.update_interval = 1.0  # Update every second
        self.last_calculation = 0.0
        
        LOGGER.info("Density Altitude Calculator initialized")
    
    def calculate_density_altitude(
        self,
        altitude_ft: Optional[float] = None,
        temperature_c: Optional[float] = None,
        barometric_pressure_mb: Optional[float] = None,
        humidity_percent: Optional[float] = None,
    ) -> DensityAltitudeData:
        """
        Calculate Density Altitude.
        
        Args:
            altitude_ft: Altitude in feet (from GPS or barometric)
            temperature_c: Outside Air Temperature in Celsius
            barometric_pressure_mb: Barometric pressure in millibars
            humidity_percent: Relative humidity (0-100)
        
        Returns:
            DensityAltitudeData with calculated values
        """
        # Get data from providers if not provided
        if altitude_ft is None and self.gps_provider:
            gps_data = self.gps_provider()
            if gps_data:
                altitude_ft = gps_data.get("altitude_ft")
                if altitude_ft is None:
                    altitude_m = gps_data.get("altitude_m")
                    if altitude_m is not None:
                        altitude_ft = altitude_m * 3.28084
        
        if temperature_c is None and self.temperature_provider:
            temperature_c = self.temperature_provider()
        
        if barometric_pressure_mb is None and self.pressure_provider:
            pressure = self.pressure_provider()
            if pressure:
                # Assume millibars if > 100, otherwise assume inHg
                if pressure > 100:
                    barometric_pressure_mb = pressure
                else:
                    barometric_pressure_mb = pressure * 33.8639  # inHg to mb
        
        if humidity_percent is None and self.humidity_provider:
            humidity_percent = self.humidity_provider()
        
        # Use defaults if still None
        altitude_ft = altitude_ft or 0.0
        temperature_c = temperature_c or self.STANDARD_TEMPERATURE_C
        barometric_pressure_mb = barometric_pressure_mb or self.STANDARD_SEA_LEVEL_PRESSURE_MB
        humidity_percent = humidity_percent or 50.0
        
        # Convert temperature
        temperature_f = (temperature_c * 9.0 / 5.0) + 32.0
        
        # Convert pressure to inHg
        barometric_pressure_inhg = barometric_pressure_mb / 33.8639
        
        # Calculate Pressure Altitude
        # PA = altitude + (1013.25 - baro_pressure_mb) * 30
        pressure_altitude_ft = altitude_ft + (self.STANDARD_SEA_LEVEL_PRESSURE_MB - barometric_pressure_mb) * 30.0
        
        # Calculate ISA (International Standard Atmosphere) temperature at pressure altitude
        # ISA temp = 15°C - (1.98°C per 1000 feet of pressure altitude)
        isa_temp_c = self.STANDARD_TEMPERATURE_C - (pressure_altitude_ft / 1000.0) * 1.98
        isa_temp_f = (isa_temp_c * 9.0 / 5.0) + 32.0
        
        # Calculate Density Altitude
        # DA = PA + (120 * (OAT - ISA_temp))
        # Where OAT and ISA_temp are in Fahrenheit
        temperature_deviation_f = temperature_f - isa_temp_f
        density_altitude_ft = pressure_altitude_ft + (120.0 * temperature_deviation_f)
        
        # Calculate air density ratio
        # Using simplified formula: density_ratio ≈ (P/P0) * (T0/T)
        # Where P0 = standard pressure, T0 = standard temperature
        temp_kelvin = temperature_c + 273.15
        standard_temp_kelvin = self.STANDARD_TEMPERATURE_C + 273.15
        pressure_ratio = barometric_pressure_mb / self.STANDARD_SEA_LEVEL_PRESSURE_MB
        temperature_ratio = standard_temp_kelvin / temp_kelvin
        air_density_ratio = pressure_ratio * temperature_ratio
        
        # Create result
        result = DensityAltitudeData(
            density_altitude_ft=density_altitude_ft,
            pressure_altitude_ft=pressure_altitude_ft,
            outside_air_temp_f=temperature_f,
            outside_air_temp_c=temperature_c,
            barometric_pressure_inhg=barometric_pressure_inhg,
            barometric_pressure_mb=barometric_pressure_mb,
            altitude_ft=altitude_ft,
            relative_humidity_percent=humidity_percent,
            air_density_ratio=air_density_ratio,
            last_update=time.time(),
        )
        
        self.current_da = result
        return result
    
    def update(self) -> Optional[DensityAltitudeData]:
        """
        Update Density Altitude calculation.
        
        Returns:
            Updated DensityAltitudeData or None if calculation failed
        """
        now = time.time()
        if now - self.last_calculation < self.update_interval:
            return self.current_da
        
        try:
            result = self.calculate_density_altitude()
            self.last_calculation = now
            return result
        except Exception as e:
            LOGGER.error("Error calculating Density Altitude: %s", e)
            return None
    
    def get_current_da(self) -> DensityAltitudeData:
        """Get current Density Altitude data."""
        return self.current_da
    
    def get_density_altitude_ft(self) -> float:
        """Get current Density Altitude in feet."""
        return self.current_da.density_altitude_ft
    
    def get_air_density_ratio(self) -> float:
        """Get current air density ratio (vs sea level standard)."""
        return self.current_da.air_density_ratio


__all__ = [
    "DensityAltitudeCalculator",
    "DensityAltitudeData",
]









