"""
Diesel Tune Map Database
Comprehensive database for diesel tuning maps.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.diesel_engine_detector import DieselEngineProfile, DieselEngineType
from services.diesel_tuner_integration import DieselTunerIntegration

LOGGER = logging.getLogger(__name__)


class TuneCategory(Enum):
    """Tune categories."""
    BASE = "base"
    ECONOMY = "economy"
    PERFORMANCE = "performance"
    TOWING = "towing"
    RACING = "racing"
    EMISSIONS = "emissions"
    DELETE = "delete"  # Emissions delete tunes


class TuneSource(Enum):
    """Tune source."""
    STOCK = "stock"
    CUSTOM = "custom"
    COMMUNITY = "community"
    PROFESSIONAL = "professional"
    EFI_LIVE = "efi_live"
    HP_TUNERS = "hp_tuners"
    SCT = "sct"
    BULLY_DOG = "bully_dog"
    EDGE = "edge"


@dataclass
class DieselTuneMap:
    """Diesel tuning map."""
    tune_id: str
    name: str
    category: TuneCategory
    source: TuneSource
    engine_profile: DieselEngineProfile
    description: str = ""
    version: str = "1.0"
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    
    # Tuning parameters
    injection_timing_map: Dict[str, Any] = field(default_factory=dict)
    injection_pressure_map: Dict[str, Any] = field(default_factory=dict)
    fuel_quantity_map: Dict[str, Any] = field(default_factory=dict)
    boost_map: Dict[str, Any] = field(default_factory=dict)
    egr_map: Optional[Dict[str, Any]] = None
    dpf_map: Optional[Dict[str, Any]] = None
    scr_map: Optional[Dict[str, Any]] = None
    
    # Performance data
    power_hp: Optional[float] = None
    torque_lbft: Optional[float] = None
    efficiency_mpg: Optional[float] = None
    
    # Requirements
    required_modifications: List[str] = field(default_factory=list)
    required_fuel: Optional[str] = None  # e.g., "Diesel #2", "Biodiesel"
    
    # Safety
    max_egt: float = 1650.0  # Fahrenheit
    max_boost: float = 50.0  # PSI
    max_cylinder_pressure: float = 3000.0  # PSI
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    verified: bool = False
    download_count: int = 0
    rating: float = 0.0
    rating_count: int = 0


class DieselTuneDatabase:
    """
    Diesel tune map database.
    
    Features:
    - Store and retrieve diesel tunes
    - Search by vehicle, category, source
    - Import from other tuners
    - Community sharing
    - Version management
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize diesel tune database."""
        self.data_dir = data_dir or Path("data/diesel_tunes")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.tunes: Dict[str, DieselTuneMap] = {}
        self.tuner_integration = DieselTunerIntegration()
        self._load_tunes()
    
    def add_tune(self, tune: DieselTuneMap) -> bool:
        """
        Add tune to database.
        
        Args:
            tune: Tune map to add
        
        Returns:
            True if added successfully
        """
        self.tunes[tune.tune_id] = tune
        self._save_tune(tune)
        
        LOGGER.info("Added diesel tune: %s", tune.name)
        return True
    
    def get_tune(self, tune_id: str) -> Optional[DieselTuneMap]:
        """Get tune by ID."""
        return self.tunes.get(tune_id)
    
    def search_tunes(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        category: Optional[TuneCategory] = None,
        source: Optional[TuneSource] = None,
        min_power: Optional[float] = None,
        max_power: Optional[float] = None,
    ) -> List[DieselTuneMap]:
        """
        Search tunes.
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            category: Tune category
            source: Tune source
            min_power: Minimum power
            max_power: Maximum power
        
        Returns:
            List of matching tunes
        """
        results = list(self.tunes.values())
        
        if make:
            results = [t for t in results if make.lower() in t.engine_profile.make.lower()]
        
        if model:
            results = [t for t in results if model.lower() in t.engine_profile.model.lower()]
        
        if year:
            results = [t for t in results if abs(t.engine_profile.year - year) <= 2]
        
        if category:
            results = [t for t in results if t.category == category]
        
        if source:
            results = [t for t in results if t.source == source]
        
        if min_power:
            results = [t for t in results if t.power_hp and t.power_hp >= min_power]
        
        if max_power:
            results = [t for t in results if t.power_hp and t.power_hp <= max_power]
        
        return sorted(results, key=lambda t: t.rating, reverse=True)
    
    def import_from_efi_live(self, file_path: str) -> Optional[DieselTuneMap]:
        """
        Import tune from EFI Live format.
        
        Args:
            file_path: Path to EFI Live file
        
        Returns:
            Imported tune or None
        """
        tune = self.tuner_integration.import_tune(file_path)
        if tune:
            self.add_tune(tune)
        return tune
    
    def import_from_hp_tuners(self, file_path: str) -> Optional[DieselTuneMap]:
        """
        Import tune from HPTuners format.
        
        Args:
            file_path: Path to HPTuners file
        
        Returns:
            Imported tune or None
        """
        tune = self.tuner_integration.import_tune(file_path)
        if tune:
            self.add_tune(tune)
        return tune
    
    def import_from_sct(self, file_path: str) -> Optional[DieselTuneMap]:
        """
        Import tune from SCT format.
        
        Args:
            file_path: Path to SCT file
        
        Returns:
            Imported tune or None
        """
        tune = self.tuner_integration.import_tune(file_path)
        if tune:
            self.add_tune(tune)
        return tune
    
    def import_from_file(self, file_path: str) -> Optional[DieselTuneMap]:
        """
        Import tune from any supported format (auto-detect).
        
        Args:
            file_path: Path to tune file
        
        Returns:
            Imported tune or None
        """
        tune = self.tuner_integration.import_tune(file_path)
        if tune:
            self.add_tune(tune)
        return tune
    
    def convert_tune(
        self,
        tune_id: str,
        output_path: str,
        target_format: str,
    ) -> bool:
        """
        Convert tune to another format.
        
        Args:
            tune_id: ID of tune to convert
            output_path: Output file path
            target_format: Target format (e.g., "edge_csv", "efi_live_ctz")
        
        Returns:
            True if successful
        """
        tune = self.get_tune(tune_id)
        if not tune:
            return False
        
        from services.diesel_tuner_integration import TunerFormat
        try:
            target = TunerFormat(target_format)
        except ValueError:
            LOGGER.error("Unknown target format: %s", target_format)
            return False
        
        return self.tuner_integration.export_tune(tune, output_path, target)
    
    def _save_tune(self, tune: DieselTuneMap) -> None:
        """Save tune to disk."""
        try:
            tune_file = self.data_dir / f"{tune.tune_id}.json"
            with open(tune_file, 'w') as f:
                json.dump({
                    "tune_id": tune.tune_id,
                    "name": tune.name,
                    "category": tune.category.value,
                    "source": tune.source.value,
                    "engine_profile": {
                        "engine_id": tune.engine_profile.engine_id,
                        "make": tune.engine_profile.make,
                        "model": tune.engine_profile.model,
                        "year": tune.engine_profile.year,
                        "engine_type": tune.engine_profile.engine_type.value,
                        "displacement": tune.engine_profile.displacement,
                        "cylinders": tune.engine_profile.cylinders,
                        "injection_system": tune.engine_profile.injection_system,
                        "turbo_type": tune.engine_profile.turbo_type,
                    },
                    "description": tune.description,
                    "version": tune.version,
                    "created_at": tune.created_at,
                    "modified_at": tune.modified_at,
                    "injection_timing_map": tune.injection_timing_map,
                    "injection_pressure_map": tune.injection_pressure_map,
                    "fuel_quantity_map": tune.fuel_quantity_map,
                    "boost_map": tune.boost_map,
                    "power_hp": tune.power_hp,
                    "torque_lbft": tune.torque_lbft,
                    "efficiency_mpg": tune.efficiency_mpg,
                    "required_modifications": tune.required_modifications,
                    "required_fuel": tune.required_fuel,
                    "max_egt": tune.max_egt,
                    "max_boost": tune.max_boost,
                    "max_cylinder_pressure": tune.max_cylinder_pressure,
                    "tags": tune.tags,
                    "notes": tune.notes,
                    "verified": tune.verified,
                    "download_count": tune.download_count,
                    "rating": tune.rating,
                    "rating_count": tune.rating_count,
                }, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save tune: %s", e)
    
    def _load_tunes(self) -> None:
        """Load tunes from disk."""
        try:
            for tune_file in self.data_dir.glob("*.json"):
                with open(tune_file, 'r') as f:
                    data = json.load(f)
                    
                    engine_data = data["engine_profile"]
                    engine_profile = DieselEngineProfile(
                        engine_id=engine_data["engine_id"],
                        make=engine_data["make"],
                        model=engine_data["model"],
                        year=engine_data["year"],
                        engine_type=DieselEngineType(engine_data["engine_type"]),
                        displacement=engine_data["displacement"],
                        cylinders=engine_data["cylinders"],
                        injection_system=engine_data["injection_system"],
                        turbo_type=engine_data["turbo_type"],
                    )
                    
                    tune = DieselTuneMap(
                        tune_id=data["tune_id"],
                        name=data["name"],
                        category=TuneCategory(data["category"]),
                        source=TuneSource(data["source"]),
                        engine_profile=engine_profile,
                        description=data.get("description", ""),
                        version=data.get("version", "1.0"),
                        created_at=data.get("created_at", time.time()),
                        modified_at=data.get("modified_at", time.time()),
                        injection_timing_map=data.get("injection_timing_map", {}),
                        injection_pressure_map=data.get("injection_pressure_map", {}),
                        fuel_quantity_map=data.get("fuel_quantity_map", {}),
                        boost_map=data.get("boost_map", {}),
                        power_hp=data.get("power_hp"),
                        torque_lbft=data.get("torque_lbft"),
                        efficiency_mpg=data.get("efficiency_mpg"),
                        required_modifications=data.get("required_modifications", []),
                        required_fuel=data.get("required_fuel"),
                        max_egt=data.get("max_egt", 1650.0),
                        max_boost=data.get("max_boost", 50.0),
                        max_cylinder_pressure=data.get("max_cylinder_pressure", 3000.0),
                        tags=data.get("tags", []),
                        notes=data.get("notes", ""),
                        verified=data.get("verified", False),
                        download_count=data.get("download_count", 0),
                        rating=data.get("rating", 0.0),
                        rating_count=data.get("rating_count", 0),
                    )
                    
                    self.tunes[tune.tune_id] = tune
            
            LOGGER.info("Loaded %d diesel tunes", len(self.tunes))
        except Exception as e:
            LOGGER.error("Failed to load tunes: %s", e)


