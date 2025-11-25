"""
Fleet Management Service
Manage multiple vehicles, compare performance, optimize fleet.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class VehicleStatus(Enum):
    """Vehicle status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


@dataclass
class Vehicle:
    """Fleet vehicle."""
    vehicle_id: str
    name: str
    make: str
    model: str
    year: int
    status: VehicleStatus
    current_driver: Optional[str] = None
    last_seen: float = field(default_factory=time.time)
    total_runs: int = 0
    total_distance: float = 0.0
    best_time: Optional[float] = None
    best_speed: Optional[float] = None
    configuration: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


@dataclass
class FleetPerformance:
    """Fleet performance metrics."""
    total_vehicles: int
    active_vehicles: int
    total_runs: int
    total_distance: float
    average_best_time: Optional[float] = None
    average_best_speed: Optional[float] = None
    top_performer: Optional[str] = None
    maintenance_required: List[str] = field(default_factory=list)


@dataclass
class PerformanceComparison:
    """Performance comparison between vehicles."""
    vehicle1_id: str
    vehicle2_id: str
    metric: str  # time, speed, power, etc.
    vehicle1_value: float
    vehicle2_value: float
    difference: float
    difference_percent: float
    winner: str


class FleetManagement:
    """
    Fleet management service.
    
    Features:
    - Manage multiple vehicles
    - Compare performance
    - Track metrics
    - Optimize fleet
    - Share best practices
    """
    
    def __init__(self):
        """Initialize fleet management."""
        self.vehicles: Dict[str, Vehicle] = {}
        self.data_dir = Path("data/fleet")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_fleet()
    
    def add_vehicle(
        self,
        vehicle_id: str,
        name: str,
        make: str,
        model: str,
        year: int,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> Vehicle:
        """
        Add vehicle to fleet.
        
        Args:
            vehicle_id: Vehicle ID
            name: Vehicle name
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            configuration: Vehicle configuration
        
        Returns:
            Created Vehicle
        """
        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            name=name,
            make=make,
            model=model,
            year=year,
            status=VehicleStatus.ACTIVE,
            configuration=configuration or {},
        )
        
        self.vehicles[vehicle_id] = vehicle
        self._save_fleet()
        
        LOGGER.info("Vehicle added to fleet: %s", name)
        return vehicle
    
    def remove_vehicle(self, vehicle_id: str) -> bool:
        """Remove vehicle from fleet."""
        if vehicle_id not in self.vehicles:
            return False
        
        del self.vehicles[vehicle_id]
        self._save_fleet()
        
        LOGGER.info("Vehicle removed from fleet: %s", vehicle_id)
        return True
    
    def update_vehicle_status(
        self,
        vehicle_id: str,
        status: VehicleStatus,
    ) -> bool:
        """Update vehicle status."""
        if vehicle_id not in self.vehicles:
            return False
        
        self.vehicles[vehicle_id].status = status
        self._save_fleet()
        return True
    
    def record_run(
        self,
        vehicle_id: str,
        time_seconds: Optional[float] = None,
        speed: Optional[float] = None,
        distance: Optional[float] = None,
    ) -> bool:
        """
        Record a run for a vehicle.
        
        Args:
            vehicle_id: Vehicle ID
            time_seconds: Run time
            speed: Top speed
            distance: Distance traveled
        
        Returns:
            True if recorded successfully
        """
        if vehicle_id not in self.vehicles:
            return False
        
        vehicle = self.vehicles[vehicle_id]
        vehicle.last_seen = time.time()
        vehicle.total_runs += 1
        
        if time_seconds is not None:
            if vehicle.best_time is None or time_seconds < vehicle.best_time:
                vehicle.best_time = time_seconds
        
        if speed is not None:
            if vehicle.best_speed is None or speed > vehicle.best_speed:
                vehicle.best_speed = speed
        
        if distance is not None:
            vehicle.total_distance += distance
        
        self._save_fleet()
        return True
    
    def get_fleet_performance(self) -> FleetPerformance:
        """Get overall fleet performance metrics."""
        total_vehicles = len(self.vehicles)
        active_vehicles = sum(1 for v in self.vehicles.values() 
                             if v.status == VehicleStatus.ACTIVE)
        total_runs = sum(v.total_runs for v in self.vehicles.values())
        total_distance = sum(v.total_distance for v in self.vehicles.values())
        
        # Calculate averages
        best_times = [v.best_time for v in self.vehicles.values() if v.best_time]
        average_best_time = sum(best_times) / len(best_times) if best_times else None
        
        best_speeds = [v.best_speed for v in self.vehicles.values() if v.best_speed]
        average_best_speed = sum(best_speeds) / len(best_speeds) if best_speeds else None
        
        # Find top performer
        top_performer = None
        if best_times:
            top_vehicle = min(self.vehicles.values(), 
                            key=lambda v: v.best_time if v.best_time else float('inf'))
            top_performer = top_vehicle.vehicle_id
        
        # Check for maintenance
        maintenance_required = [
            v.vehicle_id for v in self.vehicles.values()
            if v.status == VehicleStatus.MAINTENANCE
        ]
        
        return FleetPerformance(
            total_vehicles=total_vehicles,
            active_vehicles=active_vehicles,
            total_runs=total_runs,
            total_distance=total_distance,
            average_best_time=average_best_time,
            average_best_speed=average_best_speed,
            top_performer=top_performer,
            maintenance_required=maintenance_required,
        )
    
    def compare_vehicles(
        self,
        vehicle1_id: str,
        vehicle2_id: str,
        metric: str = "time",
    ) -> Optional[PerformanceComparison]:
        """
        Compare performance between two vehicles.
        
        Args:
            vehicle1_id: First vehicle ID
            vehicle2_id: Second vehicle ID
            metric: Metric to compare (time, speed, power, etc.)
        
        Returns:
            PerformanceComparison if both vehicles found
        """
        if vehicle1_id not in self.vehicles or vehicle2_id not in self.vehicles:
            return None
        
        v1 = self.vehicles[vehicle1_id]
        v2 = self.vehicles[vehicle2_id]
        
        if metric == "time":
            v1_value = v1.best_time or float('inf')
            v2_value = v2.best_time or float('inf')
            # Lower is better for time
            if v1_value < v2_value:
                winner = vehicle1_id
                difference = v2_value - v1_value
            else:
                winner = vehicle2_id
                difference = v1_value - v2_value
            difference_percent = (difference / max(v1_value, v2_value)) * 100 if max(v1_value, v2_value) > 0 else 0
        elif metric == "speed":
            v1_value = v1.best_speed or 0.0
            v2_value = v2.best_speed or 0.0
            # Higher is better for speed
            if v1_value > v2_value:
                winner = vehicle1_id
                difference = v1_value - v2_value
            else:
                winner = vehicle2_id
                difference = v2_value - v1_value
            difference_percent = (difference / max(v1_value, v2_value)) * 100 if max(v1_value, v2_value) > 0 else 0
        else:
            # Default to time
            v1_value = v1.best_time or float('inf')
            v2_value = v2.best_time or float('inf')
            if v1_value < v2_value:
                winner = vehicle1_id
                difference = v2_value - v1_value
            else:
                winner = vehicle2_id
                difference = v1_value - v2_value
            difference_percent = (difference / max(v1_value, v2_value)) * 100 if max(v1_value, v2_value) > 0 else 0
        
        return PerformanceComparison(
            vehicle1_id=vehicle1_id,
            vehicle2_id=vehicle2_id,
            metric=metric,
            vehicle1_value=v1_value,
            vehicle2_value=v2_value,
            difference=difference,
            difference_percent=difference_percent,
            winner=winner,
        )
    
    def get_best_practices(self) -> Dict[str, Any]:
        """
        Extract best practices from top performers.
        
        Returns:
            Dictionary of best practices
        """
        if not self.vehicles:
            return {}
        
        # Find top performers
        top_vehicles = sorted(
            [v for v in self.vehicles.values() if v.best_time],
            key=lambda v: v.best_time,
        )[:3]  # Top 3
        
        if not top_vehicles:
            return {}
        
        # Extract common configurations
        best_practices = {
            "top_performers": [v.vehicle_id for v in top_vehicles],
            "common_configurations": {},
            "average_best_time": sum(v.best_time for v in top_vehicles) / len(top_vehicles),
        }
        
        # Analyze configurations (simplified)
        # In real implementation, would analyze tuning maps, setups, etc.
        
        return best_practices
    
    def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        """Get vehicle by ID."""
        return self.vehicles.get(vehicle_id)
    
    def get_all_vehicles(self) -> List[Vehicle]:
        """Get all vehicles in fleet."""
        return list(self.vehicles.values())
    
    def _save_fleet(self) -> None:
        """Save fleet data to disk."""
        try:
            fleet_file = self.data_dir / "fleet.json"
            with open(fleet_file, 'w') as f:
                json.dump({
                    vehicle_id: {
                        "vehicle_id": v.vehicle_id,
                        "name": v.name,
                        "make": v.make,
                        "model": v.model,
                        "year": v.year,
                        "status": v.status.value,
                        "current_driver": v.current_driver,
                        "last_seen": v.last_seen,
                        "total_runs": v.total_runs,
                        "total_distance": v.total_distance,
                        "best_time": v.best_time,
                        "best_speed": v.best_speed,
                        "configuration": v.configuration,
                        "notes": v.notes,
                    }
                    for vehicle_id, v in self.vehicles.items()
                }, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save fleet: %s", e)
    
    def _load_fleet(self) -> None:
        """Load fleet data from disk."""
        try:
            fleet_file = self.data_dir / "fleet.json"
            if not fleet_file.exists():
                return
            
            with open(fleet_file, 'r') as f:
                data = json.load(f)
            
            for vehicle_id, vehicle_data in data.items():
                self.vehicles[vehicle_id] = Vehicle(
                    vehicle_id=vehicle_data["vehicle_id"],
                    name=vehicle_data["name"],
                    make=vehicle_data["make"],
                    model=vehicle_data["model"],
                    year=vehicle_data["year"],
                    status=VehicleStatus(vehicle_data["status"]),
                    current_driver=vehicle_data.get("current_driver"),
                    last_seen=vehicle_data.get("last_seen", time.time()),
                    total_runs=vehicle_data.get("total_runs", 0),
                    total_distance=vehicle_data.get("total_distance", 0.0),
                    best_time=vehicle_data.get("best_time"),
                    best_speed=vehicle_data.get("best_speed"),
                    configuration=vehicle_data.get("configuration", {}),
                    notes=vehicle_data.get("notes", ""),
                )
        except Exception as e:
            LOGGER.error("Failed to load fleet: %s", e)
