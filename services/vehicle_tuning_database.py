"""
Vehicle-Specific Tuning Database

Comprehensive, sortable database for different makes, models, and years,
detailing stock specifications and aftermarket modifications.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

LOGGER = logging.getLogger(__name__)


@dataclass
class VehicleSpecification:
    """Vehicle stock specifications."""
    make: str
    model: str
    year: int
    engine_code: Optional[str] = None
    displacement_liters: Optional[float] = None
    cylinders: Optional[int] = None
    forced_induction: Optional[str] = None  # "turbo", "supercharger", "na"
    fuel_type: str = "gasoline"
    stock_hp: Optional[int] = None
    stock_torque: Optional[int] = None
    compression_ratio: Optional[float] = None
    redline_rpm: Optional[int] = None
    ecu_type: Optional[str] = None
    notes: str = ""


@dataclass
class Modification:
    """Aftermarket modification details."""
    modification_id: str
    name: str
    category: str  # "turbo", "fuel", "intake", "exhaust", "ecu", etc.
    description: str
    compatible_vehicles: List[str] = field(default_factory=list)  # Vehicle IDs
    specifications: Dict[str, Any] = field(default_factory=dict)
    performance_gain_hp: Optional[int] = None
    performance_gain_torque: Optional[int] = None
    installation_difficulty: str = "medium"  # "easy", "medium", "hard"
    cost_estimate: Optional[float] = None
    tuning_required: bool = True
    notes: str = ""


@dataclass
class ComponentSpecification:
    """Component specifications (turbo, injectors, ECU, etc.)."""
    component_id: str
    name: str
    type: str  # "turbo", "injector", "ecu", "intercooler", etc.
    manufacturer: str
    model: str
    specifications: Dict[str, Any] = field(default_factory=dict)
    compatibility: List[str] = field(default_factory=list)  # Compatible vehicles
    performance_characteristics: Dict[str, Any] = field(default_factory=dict)
    price_range: Optional[Tuple[float, float]] = None
    notes: str = ""


class VehicleTuningDatabase:
    """
    Comprehensive vehicle tuning database.
    
    Features:
    - Vehicle specifications database
    - Modification database
    - Component specifications
    - Searchable and sortable
    - Community contributions
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize vehicle tuning database.
        
        Args:
            storage_path: Path to store database
        """
        self.storage_path = storage_path or Path("data/vehicle_tuning_db.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Databases
        self.vehicles: Dict[str, VehicleSpecification] = {}
        self.modifications: Dict[str, Modification] = {}
        self.components: Dict[str, ComponentSpecification] = {}
        
        # Load existing data
        self._load_database()
        
        # Initialize with common vehicles if empty
        if not self.vehicles:
            self._initialize_default_data()
    
    def add_vehicle(self, vehicle: VehicleSpecification) -> None:
        """Add vehicle to database."""
        vehicle_id = self._generate_vehicle_id(vehicle)
        self.vehicles[vehicle_id] = vehicle
        self._save_database()
        LOGGER.info("Added vehicle: %s %s %d", vehicle.make, vehicle.model, vehicle.year)
    
    def add_modification(self, modification: Modification) -> None:
        """Add modification to database."""
        self.modifications[modification.modification_id] = modification
        self._save_database()
        LOGGER.info("Added modification: %s", modification.name)
    
    def add_component(self, component: ComponentSpecification) -> None:
        """Add component to database."""
        self.components[component.component_id] = component
        self._save_database()
        LOGGER.info("Added component: %s", component.name)
    
    def search_vehicles(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        engine_code: Optional[str] = None
    ) -> List[VehicleSpecification]:
        """
        Search vehicles by criteria.
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            engine_code: Engine code
        
        Returns:
            List of matching vehicles
        """
        results = []
        for vehicle in self.vehicles.values():
            if make and vehicle.make.lower() != make.lower():
                continue
            if model and vehicle.model.lower() != model.lower():
                continue
            if year and vehicle.year != year:
                continue
            if engine_code and vehicle.engine_code and vehicle.engine_code.lower() != engine_code.lower():
                continue
            results.append(vehicle)
        
        return results
    
    def search_modifications(
        self,
        category: Optional[str] = None,
        compatible_vehicle_id: Optional[str] = None,
        min_hp_gain: Optional[int] = None
    ) -> List[Modification]:
        """
        Search modifications by criteria.
        
        Args:
            category: Modification category
            compatible_vehicle_id: Compatible vehicle ID
            min_hp_gain: Minimum HP gain
        
        Returns:
            List of matching modifications
        """
        results = []
        for modification in self.modifications.values():
            if category and modification.category.lower() != category.lower():
                continue
            if compatible_vehicle_id and compatible_vehicle_id not in modification.compatible_vehicles:
                continue
            if min_hp_gain and (not modification.performance_gain_hp or modification.performance_gain_hp < min_hp_gain):
                continue
            results.append(modification)
        
        return results
    
    def search_components(
        self,
        component_type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        compatible_vehicle_id: Optional[str] = None
    ) -> List[ComponentSpecification]:
        """
        Search components by criteria.
        
        Args:
            component_type: Component type
            manufacturer: Manufacturer name
            compatible_vehicle_id: Compatible vehicle ID
        
        Returns:
            List of matching components
        """
        results = []
        for component in self.components.values():
            if component_type and component.type.lower() != component_type.lower():
                continue
            if manufacturer and component.manufacturer.lower() != manufacturer.lower():
                continue
            if compatible_vehicle_id and compatible_vehicle_id not in component.compatibility:
                continue
            results.append(component)
        
        return results
    
    def get_vehicle_modifications(self, vehicle_id: str) -> List[Modification]:
        """Get modifications compatible with vehicle."""
        return [
            mod for mod in self.modifications.values()
            if vehicle_id in mod.compatible_vehicles
        ]
    
    def get_vehicle_components(self, vehicle_id: str) -> List[ComponentSpecification]:
        """Get components compatible with vehicle."""
        return [
            comp for comp in self.components.values()
            if vehicle_id in comp.compatibility
        ]
    
    def _generate_vehicle_id(self, vehicle: VehicleSpecification) -> str:
        """Generate unique vehicle ID."""
        return f"{vehicle.make}_{vehicle.model}_{vehicle.year}_{vehicle.engine_code or 'base'}"
    
    def _initialize_default_data(self) -> None:
        """Initialize with common vehicle data."""
        # Example vehicles
        common_vehicles = [
            VehicleSpecification(
                make="Honda",
                model="Civic",
                year=2020,
                engine_code="K20C1",
                displacement_liters=2.0,
                cylinders=4,
                forced_induction="turbo",
                fuel_type="gasoline",
                stock_hp=306,
                stock_torque=295,
                compression_ratio=9.8,
                redline_rpm=7000,
                ecu_type="Bosch",
            ),
            VehicleSpecification(
                make="Subaru",
                model="WRX",
                year=2021,
                engine_code="FA20",
                displacement_liters=2.0,
                cylinders=4,
                forced_induction="turbo",
                fuel_type="gasoline",
                stock_hp=268,
                stock_torque=258,
                compression_ratio=10.6,
                redline_rpm=6700,
                ecu_type="Denso",
            ),
        ]
        
        for vehicle in common_vehicles:
            vehicle_id = self._generate_vehicle_id(vehicle)
            self.vehicles[vehicle_id] = vehicle
        
        # Example modifications
        common_modifications = [
            Modification(
                modification_id="stage1_tune",
                name="Stage 1 ECU Tune",
                category="ecu",
                description="Basic ECU remap for stock vehicle",
                compatible_vehicles=list(self.vehicles.keys()),
                performance_gain_hp=30,
                performance_gain_torque=40,
                installation_difficulty="easy",
                cost_estimate=500.0,
                tuning_required=True,
            ),
            Modification(
                modification_id="cold_air_intake",
                name="Cold Air Intake",
                category="intake",
                description="Aftermarket cold air intake system",
                compatible_vehicles=list(self.vehicles.keys()),
                performance_gain_hp=10,
                installation_difficulty="easy",
                cost_estimate=300.0,
                tuning_required=False,
            ),
        ]
        
        for modification in common_modifications:
            self.modifications[modification.modification_id] = modification
        
        self._save_database()
    
    def _save_database(self) -> None:
        """Save database to disk."""
        try:
            data = {
                "vehicles": {
                    k: asdict(v) for k, v in self.vehicles.items()
                },
                "modifications": {
                    k: asdict(v) for k, v in self.modifications.items()
                },
                "components": {
                    k: asdict(v) for k, v in self.components.items()
                },
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save database: %s", e)
    
    def _load_database(self) -> None:
        """Load database from disk."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Load vehicles
            self.vehicles = {
                k: VehicleSpecification(**v)
                for k, v in data.get("vehicles", {}).items()
            }
            
            # Load modifications
            self.modifications = {
                k: Modification(**v)
                for k, v in data.get("modifications", {}).items()
            }
            
            # Load components
            self.components = {
                k: ComponentSpecification(**v)
                for k, v in data.get("components", {}).items()
            }
            
            LOGGER.info("Loaded database: %d vehicles, %d modifications, %d components",
                       len(self.vehicles), len(self.modifications), len(self.components))
        except Exception as e:
            LOGGER.error("Failed to load database: %s", e)


__all__ = [
    "VehicleTuningDatabase",
    "VehicleSpecification",
    "Modification",
    "ComponentSpecification",
]

