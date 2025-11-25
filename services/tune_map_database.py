"""
Tune/Map Database Service

Comprehensive database for storing and managing ECU tuning maps and base configurations.
Provides vehicle-specific categorization, map sharing, and integration with ECU control.

Features:
- Base maps and performance tunes
- Vehicle-specific categorization (make, model, year, engine)
- Map information (hardware requirements, performance gains)
- All tuning map types (fuel, ignition, boost, etc.)
- Map sharing and community contributions
- Safety validation and warnings
"""

from __future__ import annotations

import json
import logging
import hashlib
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

LOGGER = logging.getLogger(__name__)


class TuneType(Enum):
    """Type of tune/map."""
    BASE_MAP = "base_map"  # Safe starting point
    PERFORMANCE = "performance"  # Performance-oriented tune
    ECONOMY = "economy"  # Fuel economy focused
    RACE = "race"  # Race/competition tune
    CUSTOM = "custom"  # User custom tune
    COMMUNITY = "community"  # Shared by community


class MapCategory(Enum):
    """Category of tuning map."""
    FUEL_MAP = "fuel_map"  # IAP/TPS fuel maps
    IGNITION_TIMING = "ignition_timing"
    RPM_LIMITER = "rpm_limiter"
    STP_OPENING = "stp_opening"  # Secondary throttle plate
    FAN_CONTROL = "fan_control"
    THROTTLE_RESPONSE = "throttle_response"
    BOOST_CONTROL = "boost_control"
    O2_LAMBDA_CONTROL = "o2_lambda_control"
    IDLE_CONTROL = "idle_control"
    LAUNCH_CONTROL = "launch_control"
    ANTI_LAG = "anti_lag"
    NITROUS_CONTROL = "nitrous_control"


@dataclass
class VehicleIdentifier:
    """Vehicle identification for tune matching."""
    make: str
    model: str
    year: int
    engine_code: Optional[str] = None
    engine_displacement: Optional[float] = None  # Liters
    fuel_type: str = "gasoline"  # gasoline, diesel, e85, methanol, etc.
    forced_induction: Optional[str] = None  # turbo, supercharger, na


@dataclass
class HardwareRequirement:
    """Hardware modification required for tune."""
    component: str  # e.g., "aftermarket exhaust", "larger turbo"
    description: str
    required: bool = True  # True if mandatory, False if recommended
    notes: str = ""


@dataclass
class PerformanceGains:
    """Expected performance gains from tune."""
    hp_gain: Optional[int] = None  # Horsepower increase
    torque_gain: Optional[int] = None  # Torque increase (lb-ft)
    hp_percent: Optional[float] = None  # Percentage increase
    torque_percent: Optional[float] = None
    notes: str = ""


@dataclass
class TuningMap:
    """Individual tuning map (fuel, ignition, etc.)."""
    category: MapCategory
    name: str
    description: str
    data: Dict[str, Any]  # Map data (tables, values, etc.)
    unit: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    safety_level: str = "safe"  # safe, caution, warning, dangerous


@dataclass
class TuneMap:
    """Complete tune/map configuration."""
    tune_id: str
    name: str
    description: str
    tune_type: TuneType
    vehicle: VehicleIdentifier
    ecu_type: str  # Holley, Haltech, AEM, etc.
    
    # Maps included in this tune
    maps: List[TuningMap] = field(default_factory=list)
    
    # Hardware requirements
    hardware_requirements: List[HardwareRequirement] = field(default_factory=list)
    
    # Performance information
    performance_gains: Optional[PerformanceGains] = None
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    created_by: str = "system"  # Username or "system" for official tunes
    version: str = "1.0.0"
    
    # Safety and validation
    validated: bool = False
    validation_notes: str = ""
    safety_warnings: List[str] = field(default_factory=list)
    
    # Sharing and community
    shared: bool = False
    share_id: Optional[str] = None  # Unique ID for sharing
    download_count: int = 0
    rating: Optional[float] = None  # 1.0-5.0
    rating_count: int = 0
    
    # Tags for searchability
    tags: List[str] = field(default_factory=list)
    
    # Notes and documentation
    tuning_notes: str = ""
    installation_notes: str = ""
    dyno_results: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['tune_type'] = self.tune_type.value
        data['vehicle'] = asdict(self.vehicle)
        data['maps'] = []
        for m in self.maps:
            map_dict = asdict(m)
            map_dict['category'] = m.category.value
            data['maps'].append(map_dict)
        if self.performance_gains:
            data['performance_gains'] = asdict(self.performance_gains)
        data['hardware_requirements'] = [asdict(h) for h in self.hardware_requirements]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TuneMap:
        """Create from dictionary."""
        # Convert enums
        tune_type = TuneType(data['tune_type'])
        vehicle = VehicleIdentifier(**data['vehicle'])
        
        maps = []
        for m_data in data.get('maps', []):
            map_cat = MapCategory(m_data['category'])
            maps.append(TuningMap(
                category=map_cat,
                name=m_data['name'],
                description=m_data.get('description', ''),
                data=m_data['data'],
                unit=m_data.get('unit', ''),
                min_value=m_data.get('min_value'),
                max_value=m_data.get('max_value'),
                safety_level=m_data.get('safety_level', 'safe'),
            ))
        
        hardware_reqs = [
            HardwareRequirement(**h) for h in data.get('hardware_requirements', [])
        ]
        
        perf_gains = None
        if data.get('performance_gains'):
            perf_gains = PerformanceGains(**data['performance_gains'])
        
        return cls(
            tune_id=data['tune_id'],
            name=data['name'],
            description=data['description'],
            tune_type=tune_type,
            vehicle=vehicle,
            ecu_type=data['ecu_type'],
            maps=maps,
            hardware_requirements=hardware_reqs,
            performance_gains=perf_gains,
            created_at=data.get('created_at', time.time()),
            updated_at=data.get('updated_at', time.time()),
            created_by=data.get('created_by', 'system'),
            version=data.get('version', '1.0.0'),
            validated=data.get('validated', False),
            validation_notes=data.get('validation_notes', ''),
            safety_warnings=data.get('safety_warnings', []),
            shared=data.get('shared', False),
            share_id=data.get('share_id'),
            download_count=data.get('download_count', 0),
            rating=data.get('rating'),
            rating_count=data.get('rating_count', 0),
            tags=data.get('tags', []),
            tuning_notes=data.get('tuning_notes', ''),
            installation_notes=data.get('installation_notes', ''),
            dyno_results=data.get('dyno_results'),
        )


class TuneMapDatabase:
    """
    Comprehensive tune/map database manager.
    
    Features:
    - Store and retrieve tunes by vehicle
    - Search and filter tunes
    - Map sharing functionality
    - Safety validation
    - Community contributions
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize tune/map database.
        
        Args:
            storage_path: Path to store database files
        """
        self.storage_path = storage_path or Path("data/tune_map_database")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.tunes_dir = self.storage_path / "tunes"
        self.tunes_dir.mkdir(exist_ok=True)
        
        self.shared_dir = self.storage_path / "shared"
        self.shared_dir.mkdir(exist_ok=True)
        
        # In-memory index for fast lookup
        self.tunes_index: Dict[str, TuneMap] = {}
        self.vehicle_index: Dict[str, List[str]] = {}  # vehicle_id -> [tune_ids]
        self.ecu_index: Dict[str, List[str]] = {}  # ecu_type -> [tune_ids]
        
        # Load existing tunes
        self._load_database()
        
        # Initialize with example base maps if empty
        if not self.tunes_index:
            self._initialize_default_tunes()
    
    def add_tune(self, tune: TuneMap) -> bool:
        """
        Add a tune to the database.
        
        Args:
            tune: Tune map to add
            
        Returns:
            True if added successfully
        """
        try:
            # Generate ID if not provided
            if not tune.tune_id:
                tune.tune_id = self._generate_tune_id(tune)
            
            # Update timestamp
            tune.updated_at = time.time()
            
            # Save to disk - validate tune_id to prevent path traversal
            if not tune.tune_id or not all(c.isalnum() or c in ('-', '_') for c in tune.tune_id):
                raise ValueError(f"Invalid tune_id: {tune.tune_id}")
            tune_file = self.tunes_dir / f"{tune.tune_id}.json"
            # Ensure path is within tunes_dir (prevent path traversal)
            tune_file = tune_file.resolve()
            if not str(tune_file).startswith(str(self.tunes_dir.resolve())):
                raise ValueError(f"Path traversal attempt detected: {tune.tune_id}")
            with open(tune_file, 'w', encoding='utf-8') as f:
                json.dump(tune.to_dict(), f, indent=2)
            
            # Update indexes
            self.tunes_index[tune.tune_id] = tune
            self._update_indexes(tune)
            
            LOGGER.info("Added tune: %s (ID: %s)", tune.name, tune.tune_id)
            return True
        except Exception as e:
            LOGGER.error("Failed to add tune: %s", e)
            return False
    
    def get_tune(self, tune_id: str) -> Optional[TuneMap]:
        """Get tune by ID."""
        return self.tunes_index.get(tune_id)
    
    def search_tunes(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        engine_code: Optional[str] = None,
        ecu_type: Optional[str] = None,
        tune_type: Optional[TuneType] = None,
        tag: Optional[str] = None,
        min_hp_gain: Optional[int] = None,
    ) -> List[TuneMap]:
        """
        Search tunes by criteria.
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            engine_code: Engine code
            ecu_type: ECU type
            tune_type: Type of tune
            tag: Tag to search for
            min_hp_gain: Minimum HP gain
            
        Returns:
            List of matching tunes
        """
        results = []
        
        for tune in self.tunes_index.values():
            # Vehicle matching
            if make and tune.vehicle.make.lower() != make.lower():
                continue
            if model and tune.vehicle.model.lower() != model.lower():
                continue
            if year and tune.vehicle.year != year:
                continue
            if engine_code and tune.vehicle.engine_code:
                if tune.vehicle.engine_code.lower() != engine_code.lower():
                    continue
            
            # ECU type
            if ecu_type and tune.ecu_type.lower() != ecu_type.lower():
                continue
            
            # Tune type
            if tune_type and tune.tune_type != tune_type:
                continue
            
            # Tag
            if tag and tag.lower() not in [t.lower() for t in tune.tags]:
                continue
            
            # Performance gain
            if min_hp_gain and tune.performance_gains:
                if not tune.performance_gains.hp_gain or tune.performance_gains.hp_gain < min_hp_gain:
                    continue
            
            results.append(tune)
        
        return results
    
    def get_base_maps(self, vehicle: VehicleIdentifier, ecu_type: str) -> List[TuneMap]:
        """
        Get base maps for a vehicle/ECU combination.
        
        Base maps are safe starting points for tuning.
        
        Args:
            vehicle: Vehicle identifier
            ecu_type: ECU type
            
        Returns:
            List of base map tunes
        """
        return self.search_tunes(
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            engine_code=vehicle.engine_code,
            ecu_type=ecu_type,
            tune_type=TuneType.BASE_MAP,
        )
    
    def apply_tune(self, tune_id: str, ecu_control) -> Tuple[bool, List[str]]:
        """
        Apply a tune to ECU.
        
        Args:
            tune_id: Tune ID to apply
            ecu_control: ECUControl instance
            
        Returns:
            Tuple of (success, warnings)
        """
        tune = self.get_tune(tune_id)
        if not tune:
            return False, [f"Tune not found: {tune_id}"]
        
        warnings = []
        success_count = 0
        
        # Apply each map in the tune
        for tuning_map in tune.maps:
            try:
                # Convert map data to ECU parameters
                params = self._map_to_parameters(tuning_map)
                
                for param_name, value in params.items():
                    success, param_warnings = ecu_control.set_parameter(param_name, value)
                    if success:
                        success_count += 1
                    warnings.extend(param_warnings)
            except Exception as e:
                warnings.append(f"Failed to apply map {tuning_map.name}: {e}")
        
        # Increment download/usage count
        tune.download_count += 1
        self.add_tune(tune)  # Save updated count
        
        return success_count > 0, warnings
    
    def share_tune(self, tune_id: str) -> Optional[str]:
        """
        Share a tune (make it available for download).
        
        Args:
            tune_id: Tune ID to share
            
        Returns:
            Share ID if successful, None otherwise
        """
        tune = self.get_tune(tune_id)
        if not tune:
            return None
        
        # Generate share ID
        if not tune.share_id:
            tune.share_id = self._generate_share_id(tune)
        
        tune.shared = True
        
        # Save shared version
        share_file = self.shared_dir / f"{tune.share_id}.json"
        with open(share_file, 'w') as f:
            json.dump(tune.to_dict(), f, indent=2)
        
        # Update in database
        self.add_tune(tune)
        
        LOGGER.info("Shared tune: %s (Share ID: %s)", tune.name, tune.share_id)
        return tune.share_id
    
    def download_shared_tune(self, share_id: str) -> Optional[TuneMap]:
        """
        Download a shared tune.
        
        Args:
            share_id: Share ID
            
        Returns:
            Tune map if found, None otherwise
        """
        # Sanitize share_id to prevent path traversal
        if not share_id or not all(c.isalnum() for c in share_id):
            LOGGER.warning("Invalid share_id format: %s", share_id)
            return None
        
        share_file = self.shared_dir / f"{share_id}.json"
        # Ensure path is within shared_dir (prevent path traversal)
        share_file = share_file.resolve()
        if not str(share_file).startswith(str(self.shared_dir.resolve())):
            LOGGER.warning("Path traversal attempt detected: %s", share_id)
            return None
        
        if not share_file.exists():
            return None
        
        try:
            with open(share_file, 'r') as f:
                data = json.load(f)
            tune = TuneMap.from_dict(data)
            
            # Add to local database
            tune.tune_id = self._generate_tune_id(tune)  # New local ID
            tune.share_id = share_id  # Keep original share ID
            tune.shared = False  # Not shared locally yet
            tune.created_by = "downloaded"
            
            self.add_tune(tune)
            return tune
        except Exception as e:
            LOGGER.error("Failed to download shared tune: %s", e)
            return None
    
    def create_tune_from_current_ecu(self, name: str, vehicle: VehicleIdentifier, 
                                      ecu_control, description: str = "") -> Optional[TuneMap]:
        """
        Create a tune from current ECU settings.
        
        Args:
            name: Tune name
            vehicle: Vehicle identifier
            ecu_control: ECUControl instance with current parameters
            description: Tune description
            
        Returns:
            Created tune map
        """
        try:
            # Get current parameters from ECU
            current_params = ecu_control.current_parameters
            
            # Convert parameters to maps
            maps = []
            for param_name, param in current_params.items():
                category = self._parameter_to_category(param.category)
                if category:
                    maps.append(TuningMap(
                        category=category,
                        name=param_name,
                        description=param.description,
                        data={"value": param.current_value},
                        unit=param.unit,
                        min_value=param.min_value,
                        max_value=param.max_value,
                        safety_level=param.safety_level.value,
                    ))
            
            tune = TuneMap(
                tune_id="",  # Will be generated
                name=name,
                description=description,
                tune_type=TuneType.CUSTOM,
                vehicle=vehicle,
                ecu_type=ecu_control.ecu_type or "unknown",
                maps=maps,
                created_by="user",
            )
            
            self.add_tune(tune)
            return tune
        except Exception as e:
            LOGGER.error("Failed to create tune from ECU: %s", e)
            return None
    
    def _map_to_parameters(self, tuning_map: TuningMap) -> Dict[str, Any]:
        """Convert tuning map to ECU parameters."""
        params = {}
        
        # Map category to parameter names
        category_map = {
            MapCategory.FUEL_MAP: "fuel_map",
            MapCategory.IGNITION_TIMING: "ignition_timing",
            MapCategory.RPM_LIMITER: "rev_limit",
            MapCategory.BOOST_CONTROL: "boost_target",
            MapCategory.THROTTLE_RESPONSE: "throttle_response",
            MapCategory.FAN_CONTROL: "fan_temperature",
            MapCategory.O2_LAMBDA_CONTROL: "lambda_target",
        }
        
        param_name = category_map.get(tuning_map.category, tuning_map.name)
        params[param_name] = tuning_map.data.get("value") or tuning_map.data
        
        return params
    
    def _parameter_to_category(self, category: str) -> Optional[MapCategory]:
        """Convert parameter category to MapCategory."""
        category_lower = category.lower()
        if "fuel" in category_lower:
            return MapCategory.FUEL_MAP
        elif "ignition" in category_lower or "timing" in category_lower:
            return MapCategory.IGNITION_TIMING
        elif "rev_limit" in category_lower or "rpm" in category_lower:
            return MapCategory.RPM_LIMITER
        elif "boost" in category_lower:
            return MapCategory.BOOST_CONTROL
        elif "throttle" in category_lower:
            return MapCategory.THROTTLE_RESPONSE
        elif "fan" in category_lower:
            return MapCategory.FAN_CONTROL
        elif "lambda" in category_lower or "o2" in category_lower:
            return MapCategory.O2_LAMBDA_CONTROL
        return None
    
    def _generate_tune_id(self, tune: TuneMap) -> str:
        """Generate unique tune ID."""
        base = f"{tune.vehicle.make}_{tune.vehicle.model}_{tune.vehicle.year}_{tune.name}"
        base = base.replace(" ", "_").lower()
        hash_str = hashlib.md5(f"{base}_{time.time()}".encode()).hexdigest()[:8]
        return f"{base}_{hash_str}"
    
    def _generate_share_id(self, tune: TuneMap) -> str:
        """Generate unique share ID."""
        base = f"{tune.tune_id}_{tune.created_at}"
        return hashlib.sha256(base.encode()).hexdigest()[:16]
    
    def _update_indexes(self, tune: TuneMap) -> None:
        """Update search indexes."""
        # Vehicle index
        vehicle_id = f"{tune.vehicle.make}_{tune.vehicle.model}_{tune.vehicle.year}"
        if vehicle_id not in self.vehicle_index:
            self.vehicle_index[vehicle_id] = []
        if tune.tune_id not in self.vehicle_index[vehicle_id]:
            self.vehicle_index[vehicle_id].append(tune.tune_id)
        
        # ECU index
        if tune.ecu_type not in self.ecu_index:
            self.ecu_index[tune.ecu_type] = []
        if tune.tune_id not in self.ecu_index[tune.ecu_type]:
            self.ecu_index[tune.ecu_type].append(tune.tune_id)
    
    def _load_database(self) -> None:
        """Load all tunes from disk."""
        for tune_file in self.tunes_dir.glob("*.json"):
            try:
                with open(tune_file, 'r') as f:
                    data = json.load(f)
                tune = TuneMap.from_dict(data)
                self.tunes_index[tune.tune_id] = tune
                self._update_indexes(tune)
            except Exception as e:
                LOGGER.error("Failed to load tune %s: %s", tune_file, e)
        
        LOGGER.info("Loaded %d tunes from database", len(self.tunes_index))
    
    def _initialize_default_tunes(self) -> None:
        """Initialize with example base maps."""
        # Example base map for Honda Civic Type R
        honda_civic_base = TuneMap(
            tune_id="",
            name="Honda Civic Type R - Base Map",
            description="Safe base map for stock Honda Civic Type R. Use for initial startup and leak checks.",
            tune_type=TuneType.BASE_MAP,
            vehicle=VehicleIdentifier(
                make="Honda",
                model="Civic Type R",
                year=2020,
                engine_code="K20C1",
                engine_displacement=2.0,
                fuel_type="gasoline",
                forced_induction="turbo",
            ),
            ecu_type="Bosch",
            maps=[
                TuningMap(
                    category=MapCategory.FUEL_MAP,
                    name="Base Fuel Map",
                    description="IAP/TPS fuel map - conservative AFR targets",
                    data={"afr_target": 14.7, "load_rpm_table": {}},
                    unit="AFR",
                    safety_level="safe",
                ),
                TuningMap(
                    category=MapCategory.IGNITION_TIMING,
                    name="Ignition Timing",
                    description="Conservative ignition timing map",
                    data={"timing_advance": 15.0},
                    unit="degrees",
                    safety_level="safe",
                ),
                TuningMap(
                    category=MapCategory.RPM_LIMITER,
                    name="RPM Limiter",
                    description="Stock RPM limit",
                    data={"rev_limit": 7000},
                    unit="RPM",
                    safety_level="safe",
                ),
            ],
            hardware_requirements=[],
            performance_gains=PerformanceGains(notes="Base map - no performance gains expected"),
            validated=True,
            tags=["base", "honda", "civic", "type-r", "stock"],
        )
        
        self.add_tune(honda_civic_base)
        LOGGER.info("Initialized default tunes")


__all__ = [
    "TuneMapDatabase",
    "TuneMap",
    "TuningMap",
    "VehicleIdentifier",
    "HardwareRequirement",
    "PerformanceGains",
    "TuneType",
    "MapCategory",
]

