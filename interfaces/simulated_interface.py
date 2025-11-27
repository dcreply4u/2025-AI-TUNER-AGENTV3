"""
Simulated Data Interface

Provides a simulated data source for GUI preview and testing.
"""

from __future__ import annotations

import time
from typing import Dict

from typing import Optional

from services.data_simulator import DataSimulator

try:
    from interfaces.gps_interface import GPSFix
except ImportError:
    GPSFix = None  # type: ignore


class SimulatedGPSInterface:
    """Simulated GPS interface for demo mode."""

    def __init__(self, simulator: DataSimulator) -> None:
        """Initialize simulated GPS interface."""
        self.simulator = simulator

    def read_fix(self):
        """Read GPS fix from simulator."""
        if GPSFix is None:
            return None
            
        gps_data = self.simulator.get_gps_data()
        if not gps_data:
            return None

        # Add simulated altitude (Los Angeles area is ~100m above sea level)
        altitude_m = 100.0 + (gps_data.get("speed_mps", 0) * 0.1)  # Slight variation based on speed
        
        return GPSFix(
            latitude=gps_data["latitude"],
            longitude=gps_data["longitude"],
            speed_mps=gps_data["speed_mps"],
            heading=gps_data["heading"],
            timestamp=gps_data["timestamp"],
            altitude_m=altitude_m,
            satellites=12,  # Simulated satellite count
        )


class SimulatedInterface:
    """Simulated data interface for testing and preview."""

    def __init__(self, mode: str = "demo") -> None:
        """
        Initialize simulated interface.

        Args:
            mode: Simulation mode - "idle", "cruising", "racing", "demo"
        """
        self.simulator = DataSimulator(mode=mode)
        self.connected = True
        self.last_data: Dict[str, float] = {}

    def connect(self) -> bool:
        """Connect to simulated interface."""
        self.connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from simulated interface."""
        self.connected = False

    def is_connected(self) -> bool:
        """Check if connected."""
        return self.connected

    def read_data(self) -> Dict[str, float]:
        """
        Read simulated telemetry data.

        Returns:
            Dictionary of telemetry values
        """
        if not self.connected:
            return {}

        self.last_data = self.simulator.generate_data()
        return self.last_data

    def read_dtc_codes(self) -> list:
        """Read diagnostic trouble codes (simulated)."""
        # Occasionally return a simulated DTC
        import random

        if random.random() < 0.05:  # 5% chance
            return ["P0301", "P0171"]  # Random codes
        return []

    def clear_dtc_codes(self) -> bool:
        """Clear diagnostic trouble codes (simulated)."""
        return True

    def set_mode(self, mode: str) -> None:
        """Set simulation mode."""
        self.simulator.mode = mode
        self.simulator.reset()


__all__ = ["SimulatedInterface", "SimulatedGPSInterface"]

