"""
Fuel Efficiency Tracking Service

Advanced fuel efficiency monitoring, MPG calculation, cost tracking,
and route optimization for fleet management and personal use.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


@dataclass
class FuelReading:
    """Fuel level reading."""

    timestamp: float
    fuel_level: float  # 0-100 (percent)
    fuel_consumed: float = 0.0  # gallons
    distance: float = 0.0  # miles
    mpg: Optional[float] = None


@dataclass
class FuelEfficiencyMetrics:
    """Fuel efficiency metrics for a trip/session."""

    trip_id: str
    start_time: float
    end_time: Optional[float] = None
    distance_miles: float = 0.0
    fuel_consumed_gallons: float = 0.0
    mpg: Optional[float] = None
    fuel_cost: float = 0.0
    cost_per_mile: float = 0.0
    idle_fuel_waste: float = 0.0  # gallons wasted idling
    efficiency_score: float = 0.0  # 0-100
    route_optimization_savings: Optional[float] = None  # potential savings
    comparison_to_average: Optional[float] = None  # % vs fleet average


class FuelEfficiencyTracker:
    """
    Advanced fuel efficiency tracking and optimization.

    Features:
    - Real-time MPG calculation
    - Fuel cost tracking
    - Idle fuel waste detection
    - Route efficiency analysis
    - Comparison to fleet averages
    - Optimization recommendations
    """

    # Constants
    IDLE_FUEL_RATE = 0.5  # gallons per hour idling (typical for trucks)
    PERSONAL_IDLE_FUEL_RATE = 0.2  # gallons per hour idling (typical for cars)
    DEFAULT_FUEL_PRICE = 3.50  # dollars per gallon

    def __init__(
        self,
        fuel_tank_capacity: float = 20.0,  # gallons
        fuel_price: float = DEFAULT_FUEL_PRICE,
        vehicle_type: str = "truck",
    ) -> None:
        """
        Initialize fuel efficiency tracker.

        Args:
            fuel_tank_capacity: Fuel tank capacity in gallons
            fuel_price: Current fuel price per gallon
            vehicle_type: Vehicle type (affects idle fuel rate)
        """
        self.fuel_tank_capacity = fuel_tank_capacity
        self.fuel_price = fuel_price
        self.vehicle_type = vehicle_type
        self.idle_fuel_rate = (
            self.IDLE_FUEL_RATE if vehicle_type in ["truck", "commercial"] else self.PERSONAL_IDLE_FUEL_RATE
        )

        # Current trip tracking
        self.current_trip: Optional[FuelEfficiencyMetrics] = None
        self.trip_history: List[FuelEfficiencyMetrics] = []

        # Fuel level tracking
        self.fuel_readings: Deque[FuelReading] = deque(maxlen=1000)
        self.last_fuel_level: Optional[float] = None
        self.last_fuel_timestamp: Optional[float] = None

        # Distance tracking
        self.last_location: Optional[Tuple[float, float]] = None
        self.total_distance: float = 0.0

        # Idle tracking
        self.idle_start_time: Optional[float] = None
        self.total_idle_time: float = 0.0

        # Fleet comparison data
        self.fleet_average_mpg: Optional[float] = None
        self.fleet_average_cost_per_mile: Optional[float] = None

    def start_trip(self, trip_id: Optional[str] = None) -> FuelEfficiencyMetrics:
        """
        Start a new trip.

        Args:
            trip_id: Trip identifier (auto-generated if None)

        Returns:
            Fuel efficiency metrics for new trip
        """
        if trip_id is None:
            trip_id = f"trip_{int(time.time())}"

        self.current_trip = FuelEfficiencyMetrics(
            trip_id=trip_id,
            start_time=time.time(),
        )

        # Reset tracking
        self.total_distance = 0.0
        self.total_idle_time = 0.0
        self.last_location = None
        self.last_fuel_level = None
        self.last_fuel_timestamp = None

        LOGGER.info("Started fuel efficiency tracking for trip: %s", trip_id)
        return self.current_trip

    def update(
        self,
        fuel_level: Optional[float] = None,  # 0-100 (percent)
        location: Optional[Tuple[float, float]] = None,  # (lat, lon)
        speed: Optional[float] = None,  # mph
        is_idle: bool = False,
        timestamp: Optional[float] = None,
    ) -> Optional[FuelEfficiencyMetrics]:
        """
        Update fuel efficiency tracking.

        Args:
            fuel_level: Current fuel level (0-100%)
            location: GPS location (lat, lon)
            speed: Current speed (mph)
            is_idle: Whether vehicle is idling
            timestamp: Timestamp (defaults to current time)

        Returns:
            Updated trip metrics if trip ended, None otherwise
        """
        if timestamp is None:
            timestamp = time.time()

        if self.current_trip is None:
            self.start_trip()

        # Update distance if location provided
        if location and self.last_location:
            distance = self._calculate_distance(self.last_location, location)
            self.total_distance += distance
            if self.current_trip:
                self.current_trip.distance_miles += distance

        if location:
            self.last_location = location

        # Update fuel consumption
        if fuel_level is not None:
            if self.last_fuel_level is not None and self.last_fuel_timestamp is not None:
                # Calculate fuel consumed
                fuel_change = (self.last_fuel_level - fuel_level) / 100.0 * self.fuel_tank_capacity
                if fuel_change > 0:  # Fuel consumed (not refueled)
                    if self.current_trip:
                        self.current_trip.fuel_consumed_gallons += fuel_change

                    # Record fuel reading
                    reading = FuelReading(
                        timestamp=timestamp,
                        fuel_level=fuel_level,
                        fuel_consumed=fuel_change,
                        distance=self.total_distance - (self.fuel_readings[-1].distance if self.fuel_readings else 0.0),
                    )
                    if reading.distance > 0:
                        reading.mpg = reading.distance / reading.fuel_consumed if reading.fuel_consumed > 0 else None
                    self.fuel_readings.append(reading)

            self.last_fuel_level = fuel_level
            self.last_fuel_timestamp = timestamp

        # Update idle time and fuel waste
        if is_idle:
            if self.idle_start_time is None:
                self.idle_start_time = timestamp
        else:
            if self.idle_start_time is not None:
                idle_duration = timestamp - self.idle_start_time
                self.total_idle_time += idle_duration
                if self.current_trip:
                    idle_fuel_waste = (idle_duration / 3600.0) * self.idle_fuel_rate
                    self.current_trip.idle_fuel_waste += idle_fuel_waste
                self.idle_start_time = None

        # Update current trip metrics
        if self.current_trip:
            self.current_trip.distance_miles = self.total_distance
            if self.current_trip.fuel_consumed_gallons > 0:
                self.current_trip.mpg = (
                    self.current_trip.distance_miles / self.current_trip.fuel_consumed_gallons
                )
                self.current_trip.fuel_cost = self.current_trip.fuel_consumed_gallons * self.fuel_price
                if self.current_trip.distance_miles > 0:
                    self.current_trip.cost_per_mile = (
                        self.current_trip.fuel_cost / self.current_trip.distance_miles
                    )

            # Calculate efficiency score
            self._calculate_efficiency_score(self.current_trip)

        return None

    def end_trip(self) -> Optional[FuelEfficiencyMetrics]:
        """
        End current trip.

        Returns:
            Completed trip metrics
        """
        if self.current_trip is None:
            return None

        self.current_trip.end_time = time.time()

        # Final calculations
        if self.current_trip.fuel_consumed_gallons > 0:
            self.current_trip.mpg = (
                self.current_trip.distance_miles / self.current_trip.fuel_consumed_gallons
            )
            self.current_trip.fuel_cost = self.current_trip.fuel_consumed_gallons * self.fuel_price
            if self.current_trip.distance_miles > 0:
                self.current_trip.cost_per_mile = (
                    self.current_trip.fuel_cost / self.current_trip.distance_miles
                )

        # Compare to fleet average
        if self.fleet_average_mpg:
            if self.current_trip.mpg:
                self.current_trip.comparison_to_average = (
                    (self.current_trip.mpg - self.fleet_average_mpg) / self.fleet_average_mpg * 100.0
                )

        # Calculate final efficiency score
        self._calculate_efficiency_score(self.current_trip)

        # Store trip
        completed_trip = self.current_trip
        self.trip_history.append(completed_trip)
        self.current_trip = None

        LOGGER.info(
            "Trip ended: %.2f miles, %.2f MPG, $%.2f cost",
            completed_trip.distance_miles,
            completed_trip.mpg or 0.0,
            completed_trip.fuel_cost,
        )

        return completed_trip

    def _calculate_efficiency_score(self, trip: FuelEfficiencyMetrics) -> None:
        """Calculate efficiency score (0-100) for a trip."""
        score = 100.0

        # Penalize for low MPG (if we have fleet average)
        if self.fleet_average_mpg and trip.mpg:
            if trip.mpg < self.fleet_average_mpg:
                penalty = ((self.fleet_average_mpg - trip.mpg) / self.fleet_average_mpg) * 30.0
                score -= penalty

        # Penalize for idle fuel waste
        if trip.distance_miles > 0:
            idle_waste_percent = (trip.idle_fuel_waste / trip.fuel_consumed_gallons) * 100.0 if trip.fuel_consumed_gallons > 0 else 0.0
            score -= min(idle_waste_percent * 2.0, 40.0)  # Max 40 point penalty

        # Bonus for high MPG
        if trip.mpg and self.fleet_average_mpg:
            if trip.mpg > self.fleet_average_mpg:
                bonus = ((trip.mpg - self.fleet_average_mpg) / self.fleet_average_mpg) * 20.0
                score += min(bonus, 20.0)  # Max 20 point bonus

        trip.efficiency_score = max(0.0, min(100.0, score))

    def _calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """
        Calculate distance between two GPS coordinates (Haversine formula).

        Args:
            loc1: (lat, lon) of first point
            loc2: (lat, lon) of second point

        Returns:
            Distance in miles
        """
        import math

        R = 3959.0  # Earth radius in miles

        lat1, lon1 = math.radians(loc1[0]), math.radians(loc1[1])
        lat2, lon2 = math.radians(loc2[0]), math.radians(loc2[1])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def get_current_mpg(self) -> Optional[float]:
        """Get current trip MPG."""
        if self.current_trip and self.current_trip.mpg:
            return self.current_trip.mpg
        return None

    def get_average_mpg(self, days: Optional[int] = None) -> Optional[float]:
        """
        Get average MPG over time period.

        Args:
            days: Number of days to look back (None = all time)

        Returns:
            Average MPG
        """
        if not self.trip_history:
            return None

        cutoff_time = time.time() - (days * 24 * 3600) if days else 0

        trips = [t for t in self.trip_history if t.end_time and t.end_time >= cutoff_time]
        if not trips:
            return None

        total_distance = sum(t.distance_miles for t in trips)
        total_fuel = sum(t.fuel_consumed_gallons for t in trips)

        if total_fuel > 0:
            return total_distance / total_fuel
        return None

    def get_fuel_cost_summary(self, days: Optional[int] = None) -> Dict[str, float]:
        """
        Get fuel cost summary.

        Args:
            days: Number of days to look back (None = all time)

        Returns:
            Dictionary with cost metrics
        """
        cutoff_time = time.time() - (days * 24 * 3600) if days else 0

        trips = [t for t in self.trip_history if t.end_time and t.end_time >= cutoff_time]
        if not trips:
            return {
                "total_cost": 0.0,
                "total_fuel": 0.0,
                "total_distance": 0.0,
                "cost_per_mile": 0.0,
                "idle_waste_cost": 0.0,
            }

        total_cost = sum(t.fuel_cost for t in trips)
        total_fuel = sum(t.fuel_consumed_gallons for t in trips)
        total_distance = sum(t.distance_miles for t in trips)
        idle_waste_cost = sum(t.idle_fuel_waste * self.fuel_price for t in trips)

        return {
            "total_cost": total_cost,
            "total_fuel": total_fuel,
            "total_distance": total_distance,
            "cost_per_mile": total_cost / total_distance if total_distance > 0 else 0.0,
            "idle_waste_cost": idle_waste_cost,
        }

    def set_fleet_averages(self, average_mpg: float, average_cost_per_mile: float) -> None:
        """
        Set fleet average metrics for comparison.

        Args:
            average_mpg: Fleet average MPG
            average_cost_per_mile: Fleet average cost per mile
        """
        self.fleet_average_mpg = average_mpg
        self.fleet_average_cost_per_mile = average_cost_per_mile

    def get_optimization_recommendations(self) -> List[str]:
        """
        Get fuel efficiency optimization recommendations.

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not self.current_trip:
            return recommendations

        # Check idle time
        if self.current_trip.idle_fuel_waste > 0.5:  # More than 0.5 gallons wasted
            recommendations.append(
                f"Reduce idle time to save ${self.current_trip.idle_fuel_waste * self.fuel_price:.2f} per trip"
            )

        # Check MPG vs fleet average
        if self.fleet_average_mpg and self.current_trip.mpg:
            if self.current_trip.mpg < self.fleet_average_mpg * 0.9:  # 10% below average
                recommendations.append(
                    f"MPG is {((self.fleet_average_mpg - self.current_trip.mpg) / self.fleet_average_mpg * 100):.1f}% below fleet average. "
                    "Consider smoother acceleration and reduced idling."
                )

        # Check cost per mile
        if self.fleet_average_cost_per_mile and self.current_trip.cost_per_mile:
            if self.current_trip.cost_per_mile > self.fleet_average_cost_per_mile * 1.1:  # 10% above average
                recommendations.append(
                    f"Cost per mile is ${self.current_trip.cost_per_mile - self.fleet_average_cost_per_mile:.2f} above average. "
                    "Review driving habits and route efficiency."
                )

        return recommendations


__all__ = [
    "FuelReading",
    "FuelEfficiencyMetrics",
    "FuelEfficiencyTracker",
]









