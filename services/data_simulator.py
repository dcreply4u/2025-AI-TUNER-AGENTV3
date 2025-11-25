"""
Data Simulator

Generates realistic telemetry data for GUI preview and testing.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class SimulatorState:
    """State of the simulator."""

    base_rpm: float = 800.0
    target_rpm: float = 3000.0
    throttle_position: float = 0.0
    vehicle_speed: float = 0.0
    coolant_temp: float = 85.0
    oil_pressure: float = 45.0
    boost_pressure: float = 0.0
    lambda_value: float = 1.0
    brake_pressure: float = 0.0
    battery_voltage: float = 13.8
    g_force_lat: float = 0.0
    g_force_long: float = 0.0
    suspension_travel_fl: float = 10.0
    suspension_travel_fr: float = 10.0
    suspension_travel_rl: float = 10.0
    suspension_travel_rr: float = 10.0
    session_time: float = 0.0
    lap_number: int = 0
    lap_time: float = 0.0


class DataSimulator:
    """Simulates realistic telemetry data for testing and preview."""

    def __init__(self, mode: str = "idle") -> None:
        """
        Initialize data simulator.

        Args:
            mode: Simulation mode - "idle", "cruising", "racing", "demo"
        """
        self.mode = mode
        self.state = SimulatorState()
        self.start_time = time.time()
        self.last_update = time.time()

    def generate_data(self) -> Dict[str, float]:
        """
        Generate a sample of telemetry data.

        Returns:
            Dictionary of telemetry values
        """
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now
        self.state.session_time = now - self.start_time

        # Update state based on mode
        self._update_state(elapsed)

        # Generate data based on current state
        data = {
            "Engine_RPM": self._clamp(self.state.base_rpm, 0, 8000),
            "Throttle_Position": self._clamp(self.state.throttle_position, 0, 100),
            "Vehicle_Speed": self._clamp(self.state.vehicle_speed, 0, 200),
            "Coolant_Temp": self._clamp(self.state.coolant_temp, 70, 120),
            "Oil_Pressure": self._clamp(self.state.oil_pressure, 20, 80),
            "Boost_Pressure": self._clamp(self.state.boost_pressure, -5, 30),
            "Lambda": self._clamp(self.state.lambda_value, 0.7, 1.3),
            "Brake_Pressure": self._clamp(self.state.brake_pressure, 0, 1500),
            "Battery_Voltage": self._clamp(self.state.battery_voltage, 11.5, 15.0),
            "GForce_Lateral": self._clamp(self.state.g_force_lat, -2.5, 2.5),
            "GForce_Longitudinal": self._clamp(self.state.g_force_long, -3.5, 3.5),
            "Suspension_FL": self._clamp(self.state.suspension_travel_fl, 0, 40),
            "Suspension_FR": self._clamp(self.state.suspension_travel_fr, 0, 40),
            "Fuel_Pressure": 45.0 + random.uniform(-2, 2),
            "Intake_Temp": self.state.coolant_temp - 20 + random.uniform(-5, 5),
            "Timing_Advance": 15.0 + random.uniform(-2, 2),
        }

        # Add racing-specific metrics if in racing mode
        if self.mode == "racing":
            data.update({
                "FlexFuelPercent": 85.0 + random.uniform(-5, 5),
                "MethInjectionDuty": 30.0 + random.uniform(-10, 10),
                "MethTankLevel": 75.0 + random.uniform(-5, 5),
                "NitrousBottlePressure": 900.0 + random.uniform(-50, 50),
                "NitrousSolenoidState": 1.0 if self.state.throttle_position > 80 else 0.0,
                "TransBrakeActive": 1.0 if self.state.vehicle_speed < 5 and self.state.throttle_position > 90 else 0.0,
            })

        # Add some realistic noise
        for key in data:
            if key not in ["NitrousSolenoidState", "TransBrakeActive"]:
                data[key] += random.uniform(-0.5, 0.5)

        return data

    def _update_state(self, elapsed: float) -> None:
        """Update simulator state based on mode and elapsed time."""
        if self.mode == "idle":
            self._update_idle(elapsed)
        elif self.mode == "cruising":
            self._update_cruising(elapsed)
        elif self.mode == "racing":
            self._update_racing(elapsed)
        elif self.mode == "demo":
            self._update_demo(elapsed)

    def _update_idle(self, elapsed: float) -> None:
        """Update state for idle mode."""
        # Idle RPM with slight variation
        self.state.base_rpm = 800 + math.sin(self.state.session_time * 0.5) * 50
        self.state.throttle_position = 0.0
        self.state.vehicle_speed = 0.0
        self.state.coolant_temp = 85.0 + math.sin(self.state.session_time * 0.1) * 2
        self.state.oil_pressure = 45.0
        self.state.boost_pressure = -1.0
        self.state.lambda_value = 1.0
        self.state.brake_pressure = 0.0
        self.state.g_force_lat = math.sin(self.state.session_time * 0.5) * 0.1
        self.state.g_force_long = math.cos(self.state.session_time * 0.3) * 0.1
        self.state.battery_voltage = 13.9 + math.sin(self.state.session_time * 0.1) * 0.05
        self._update_suspension_travel(0.5)

    def _update_cruising(self, elapsed: float) -> None:
        """Update state for cruising mode."""
        # Simulate cruising at 60 mph
        target_speed = 60.0
        self.state.vehicle_speed = self._approach(self.state.vehicle_speed, target_speed, elapsed * 10)
        self.state.base_rpm = 2500 + (self.state.vehicle_speed / 60) * 500
        self.state.throttle_position = 25.0 + math.sin(self.state.session_time * 0.3) * 5
        self.state.coolant_temp = 90.0 + math.sin(self.state.session_time * 0.1) * 3
        self.state.oil_pressure = 50.0
        self.state.boost_pressure = 2.0
        self.state.lambda_value = 1.0
        self.state.brake_pressure = 50.0 + math.sin(self.state.session_time * 0.4) * 10
        self.state.g_force_lat = math.sin(self.state.session_time * 0.6) * 0.5
        self.state.g_force_long = 0.2 + math.sin(self.state.session_time * 0.3) * 0.3
        self.state.battery_voltage = 13.7 + math.sin(self.state.session_time * 0.05) * 0.05
        self._update_suspension_travel(2.5)

    def _update_racing(self, elapsed: float) -> None:
        """Update state for racing mode."""
        # Simulate racing scenario
        cycle_time = self.state.session_time % 30.0  # 30 second cycle

        if cycle_time < 5:
            # Launch phase
            self.state.throttle_position = 100.0
            self.state.vehicle_speed = self._approach(self.state.vehicle_speed, 100, elapsed * 15)
            self.state.base_rpm = 4000 + (self.state.vehicle_speed / 100) * 3000
            self.state.boost_pressure = 20.0 + (cycle_time / 5) * 5
        elif cycle_time < 15:
            # Acceleration
            self.state.throttle_position = 95.0
            self.state.vehicle_speed = self._approach(self.state.vehicle_speed, 150, elapsed * 8)
            self.state.base_rpm = 6000 + math.sin(cycle_time * 0.5) * 500
            self.state.boost_pressure = 25.0
        elif cycle_time < 20:
            # Braking
            self.state.throttle_position = 0.0
            self.state.vehicle_speed = self._approach(self.state.vehicle_speed, 30, elapsed * 20)
            self.state.base_rpm = 2000 + (self.state.vehicle_speed / 150) * 2000
            self.state.boost_pressure = -2.0
        else:
            # Cornering
            self.state.throttle_position = 40.0
            self.state.vehicle_speed = 50.0 + math.sin((cycle_time - 20) * 0.5) * 10
            self.state.base_rpm = 3500 + math.sin((cycle_time - 20) * 0.5) * 500
            self.state.boost_pressure = 5.0
            self.state.g_force_lat = math.sin((cycle_time - 20) * 0.5) * 1.2
            self.state.g_force_long = math.cos((cycle_time - 20) * 0.5) * 0.6
            self.state.brake_pressure = 200.0 + abs(self.state.g_force_lat) * 100

        self.state.battery_voltage = 13.5 + math.sin(self.state.session_time * 0.2) * 0.2
        self._update_suspension_travel(4.0)

        self.state.coolant_temp = 95.0 + (cycle_time / 30) * 10
        self.state.oil_pressure = 55.0 + (cycle_time / 30) * 5
        self.state.lambda_value = 0.95 + (cycle_time / 30) * 0.1

        # Update lap time
        if cycle_time < 1:
            self.state.lap_number += 1
            self.state.lap_time = 25.0 + random.uniform(-1, 1)

    def _update_demo(self, elapsed: float) -> None:
        """Update state for demo mode (cycles through different scenarios)."""
        cycle_time = self.state.session_time % 60.0  # 60 second cycle

        if cycle_time < 15:
            # Idle
            self._update_idle(elapsed)
        elif cycle_time < 30:
            # Cruising
            self._update_cruising(elapsed)
        elif cycle_time < 45:
            # Racing
            self._update_racing(elapsed)
        else:
            # Back to idle
            self._update_idle(elapsed)

        # Blend in some smooth transitions for demo G-forces
        blend = math.sin(self.state.session_time * 0.2) * 0.2
        self.state.g_force_lat += blend
        self.state.g_force_long += blend * 0.5

    def _approach(self, current: float, target: float, rate: float) -> float:
        """Smoothly approach target value."""
        diff = target - current
        if abs(diff) < 0.1:
            return target
        return current + math.copysign(min(abs(diff), rate), diff)

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value between min and max."""
        return max(min_val, min(max_val, value))

    def _update_suspension_travel(self, amplitude: float) -> None:
        """Add subtle independent suspension motion for realism."""
        t = self.state.session_time
        self.state.suspension_travel_fl = 15 + math.sin(t * 1.1) * amplitude
        self.state.suspension_travel_fr = 15 + math.sin(t * 1.15 + 0.5) * amplitude
        self.state.suspension_travel_rl = 15 + math.sin(t * 1.05 + 1.0) * amplitude
        self.state.suspension_travel_rr = 15 + math.sin(t * 1.2 + 1.5) * amplitude

    def get_gps_data(self) -> Optional[Dict[str, float]]:
        """Generate GPS data."""
        # Simulate GPS coordinates (somewhere in California)
        base_lat = 34.0522
        base_lon = -118.2437

        # Move around based on speed
        lat_offset = (self.state.vehicle_speed / 111000) * math.sin(self.state.session_time * 0.1)
        lon_offset = (self.state.vehicle_speed / 111000) * math.cos(self.state.session_time * 0.1)

        return {
            "latitude": base_lat + lat_offset,
            "longitude": base_lon + lon_offset,
            "speed_mps": self.state.vehicle_speed * 0.44704,  # Convert mph to m/s
            "heading": (self.state.session_time * 10) % 360,
            "timestamp": time.time(),
        }

    def reset(self) -> None:
        """Reset simulator state."""
        self.state = SimulatorState()
        self.start_time = time.time()
        self.last_update = time.time()


__all__ = ["DataSimulator", "SimulatorState"]

