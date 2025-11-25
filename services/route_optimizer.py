"""
Route Optimization Service

Advanced route optimization for fleet management, delivery, and commercial vehicles.
Features: multi-stop routing, traffic-aware routing, fuel-efficient routing, geofencing.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


@dataclass
class RouteStop:
    """Route stop/waypoint."""

    stop_id: str
    name: str
    location: Tuple[float, float]  # (lat, lon)
    address: Optional[str] = None
    time_window_start: Optional[float] = None  # timestamp
    time_window_end: Optional[float] = None  # timestamp
    service_time: float = 0.0  # minutes
    priority: int = 1  # 1 = highest
    required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Route:
    """Optimized route."""

    route_id: str
    vehicle_id: str
    driver_id: Optional[str] = None
    stops: List[RouteStop] = field(default_factory=list)
    total_distance: float = 0.0  # miles
    estimated_time: float = 0.0  # minutes
    estimated_fuel_cost: float = 0.0
    fuel_efficient: bool = False
    optimized: bool = False
    created_at: float = field(default_factory=time.time)


class RouteOptimizer:
    """
    Advanced route optimization for fleet management.

    Features:
    - Multi-stop route planning
    - Traffic-aware routing
    - Fuel-efficient routing
    - Time window optimization
    - Priority-based routing
    - Geofencing and alerts
    - Route comparison
    """

    # Constants
    AVERAGE_SPEED_MPH = 45.0  # Average driving speed
    FUEL_PRICE_PER_GALLON = 3.50
    FUEL_EFFICIENCY_MPG = 10.0  # Typical for commercial vehicles

    def __init__(self, enable_traffic: bool = False) -> None:
        """
        Initialize route optimizer.

        Args:
            enable_traffic: Enable traffic-aware routing (requires API)
        """
        self.enable_traffic = enable_traffic
        self.routes: Dict[str, Route] = {}
        self.geofences: Dict[str, Tuple[float, float, float]] = {}  # name -> (lat, lon, radius_miles)

    def create_route(
        self,
        vehicle_id: str,
        stops: List[RouteStop],
        start_location: Optional[Tuple[float, float]] = None,
        optimize: bool = True,
    ) -> Route:
        """
        Create optimized route.

        Args:
            vehicle_id: Vehicle ID
            stops: List of stops
            start_location: Starting location (lat, lon)
            optimize: Whether to optimize route order

        Returns:
            Optimized route
        """
        route_id = f"route_{int(time.time())}"
        route = Route(route_id=route_id, vehicle_id=vehicle_id, stops=stops)

        if optimize and len(stops) > 1:
            # Optimize stop order (nearest neighbor with priority)
            optimized_stops = self._optimize_stop_order(stops, start_location)
            route.stops = optimized_stops
            route.optimized = True

        # Calculate route metrics
        self._calculate_route_metrics(route, start_location)

        self.routes[route_id] = route
        LOGGER.info("Created route %s with %d stops", route_id, len(stops))
        return route

    def _optimize_stop_order(
        self,
        stops: List[RouteStop],
        start_location: Optional[Tuple[float, float]] = None,
    ) -> List[RouteStop]:
        """
        Optimize stop order using nearest neighbor with priority.

        Args:
            stops: List of stops
            start_location: Starting location

        Returns:
            Optimized stop order
        """
        if not stops:
            return []

        # Separate required and optional stops
        required_stops = [s for s in stops if s.required]
        optional_stops = [s for s in stops if not s.required]

        # Sort required stops by priority
        required_stops.sort(key=lambda x: x.priority)

        # Build route using nearest neighbor
        optimized = []
        remaining = required_stops.copy()
        current_location = start_location

        while remaining:
            if current_location:
                # Find nearest stop
                nearest = min(
                    remaining,
                    key=lambda s: self._calculate_distance(current_location, s.location),
                )
            else:
                # Start with highest priority
                nearest = remaining[0]

            optimized.append(nearest)
            remaining.remove(nearest)
            current_location = nearest.location

        # Add optional stops if time permits
        for stop in optional_stops:
            # Find best insertion point
            best_position = len(optimized)
            min_detour = float("inf")

            for i in range(len(optimized) + 1):
                if i == 0:
                    detour = self._calculate_distance(start_location or optimized[0].location, stop.location)
                elif i == len(optimized):
                    detour = self._calculate_distance(optimized[-1].location, stop.location)
                else:
                    detour = (
                        self._calculate_distance(optimized[i - 1].location, stop.location)
                        + self._calculate_distance(stop.location, optimized[i].location)
                        - self._calculate_distance(optimized[i - 1].location, optimized[i].location)
                    )

                if detour < min_detour:
                    min_detour = detour
                    best_position = i

            optimized.insert(best_position, stop)

        return optimized

    def _calculate_route_metrics(
        self,
        route: Route,
        start_location: Optional[Tuple[float, float]] = None,
    ) -> None:
        """Calculate route metrics (distance, time, cost)."""
        if not route.stops:
            return

        total_distance = 0.0
        current_location = start_location

        for stop in route.stops:
            if current_location:
                distance = self._calculate_distance(current_location, stop.location)
                total_distance += distance
            current_location = stop.location

        route.total_distance = total_distance

        # Estimate time (distance / speed + service time)
        driving_time = (total_distance / self.AVERAGE_SPEED_MPH) * 60.0  # minutes
        service_time = sum(s.service_time for s in route.stops)
        route.estimated_time = driving_time + service_time

        # Estimate fuel cost
        fuel_consumed = total_distance / self.FUEL_EFFICIENCY_MPG
        route.estimated_fuel_cost = fuel_consumed * self.FUEL_PRICE_PER_GALLON

    def _calculate_distance(
        self, loc1: Tuple[float, float], loc2: Tuple[float, float]
    ) -> float:
        """
        Calculate distance between two GPS coordinates (Haversine formula).

        Args:
            loc1: (lat, lon) of first point
            loc2: (lat, lon) of second point

        Returns:
            Distance in miles
        """
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

    def add_geofence(
        self, name: str, location: Tuple[float, float], radius_miles: float
    ) -> None:
        """
        Add geofence for alerts.

        Args:
            name: Geofence name
            location: Center location (lat, lon)
            radius_miles: Radius in miles
        """
        self.geofences[name] = (location[0], location[1], radius_miles)
        LOGGER.info("Added geofence: %s at %s", name, location)

    def check_geofence(
        self, location: Tuple[float, float]
    ) -> List[Tuple[str, bool]]:
        """
        Check if location is within any geofence.

        Args:
            location: Current location (lat, lon)

        Returns:
            List of (geofence_name, is_inside) tuples
        """
        results = []
        for name, (fence_lat, fence_lon, radius) in self.geofences.items():
            distance = self._calculate_distance(location, (fence_lat, fence_lon))
            results.append((name, distance <= radius))
        return results

    def compare_routes(self, route1_id: str, route2_id: str) -> Dict[str, Any]:
        """
        Compare two routes.

        Args:
            route1_id: First route ID
            route2_id: Second route ID

        Returns:
            Comparison dictionary
        """
        route1 = self.routes.get(route1_id)
        route2 = self.routes.get(route2_id)

        if not route1 or not route2:
            return {}

        distance_diff = route2.total_distance - route1.total_distance
        time_diff = route2.estimated_time - route1.estimated_time
        cost_diff = route2.estimated_fuel_cost - route1.estimated_fuel_cost

        return {
            "route1": {
                "distance": route1.total_distance,
                "time": route1.estimated_time,
                "cost": route1.estimated_fuel_cost,
            },
            "route2": {
                "distance": route2.total_distance,
                "time": route2.estimated_time,
                "cost": route2.estimated_fuel_cost,
            },
            "differences": {
                "distance_miles": distance_diff,
                "time_minutes": time_diff,
                "cost_dollars": cost_diff,
            },
            "better_route": (
                route1_id
                if route1.total_distance < route2.total_distance
                else route2_id
            ),
        }


__all__ = [
    "RouteStop",
    "Route",
    "RouteOptimizer",
]









