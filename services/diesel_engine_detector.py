"""
Diesel Engine Auto-Detection System
Automatically detects diesel engines and their characteristics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class DieselEngineType(Enum):
    """Diesel engine types."""
    COMMON_RAIL = "common_rail"
    UNIT_INJECTOR = "unit_injector"
    HEUI = "heui"  # Hydraulic Electronic Unit Injector
    PIEZO = "piezo"
    MECHANICAL = "mechanical"
    UNKNOWN = "unknown"


class DieselSystem(Enum):
    """Diesel systems."""
    EGR = "egr"  # Exhaust Gas Recirculation
    DPF = "dpf"  # Diesel Particulate Filter
    SCR = "scr"  # Selective Catalytic Reduction
    VGT = "vgt"  # Variable Geometry Turbo
    WASTEGATE = "wastegate"
    INTERCOOLER = "intercooler"
    WATER_METH = "water_meth"
    NITROUS = "nitrous"


@dataclass
class DieselEngineProfile:
    """Diesel engine profile."""
    engine_id: str
    make: str
    model: str
    year: int
    engine_type: DieselEngineType
    displacement: float  # Liters
    cylinders: int
    injection_system: str
    turbo_type: str
    systems: List[DieselSystem] = field(default_factory=list)
    max_injection_pressure: float = 0.0  # PSI
    max_boost_pressure: float = 0.0  # PSI
    stock_power: float = 0.0  # HP
    stock_torque: float = 0.0  # lb-ft
    modifications: List[str] = field(default_factory=list)


@dataclass
class DieselDetectionResult:
    """Diesel engine detection result."""
    is_diesel: bool
    confidence: float  # 0.0 - 1.0
    engine_profile: Optional[DieselEngineProfile] = None
    detected_systems: List[DieselSystem] = field(default_factory=list)
    reasoning: str = ""


class DieselEngineDetector:
    """
    Diesel engine auto-detection system.
    
    Detects:
    - Diesel vs gasoline engine
    - Engine type (common rail, unit injector, etc.)
    - Injection system
    - Turbo system
    - Emissions systems (EGR, DPF, SCR)
    - Modifications
    """
    
    def __init__(self):
        """Initialize diesel engine detector."""
        self.known_diesel_engines: Dict[str, DieselEngineProfile] = {}
        self._load_known_engines()
    
    def detect_engine(
        self,
        telemetry_data: Dict[str, Any],
        vehicle_info: Optional[Dict[str, Any]] = None,
    ) -> DieselDetectionResult:
        """
        Detect diesel engine from telemetry and vehicle info.
        
        Args:
            telemetry_data: Current telemetry data
            vehicle_info: Optional vehicle information
        
        Returns:
            DieselDetectionResult
        """
        # Check vehicle info first
        if vehicle_info:
            profile = self._detect_from_vehicle_info(vehicle_info)
            if profile:
                return DieselDetectionResult(
                    is_diesel=True,
                    confidence=0.95,
                    engine_profile=profile,
                    reasoning="Detected from vehicle information",
                )
        
        # Detect from telemetry
        is_diesel, confidence = self._detect_from_telemetry(telemetry_data)
        
        if not is_diesel:
            return DieselDetectionResult(
                is_diesel=False,
                confidence=confidence,
                reasoning="No diesel characteristics detected",
            )
        
        # Identify engine type
        engine_type = self._identify_engine_type(telemetry_data)
        
        # Detect systems
        systems = self._detect_systems(telemetry_data)
        
        # Create profile
        profile = DieselEngineProfile(
            engine_id="detected_diesel",
            make=vehicle_info.get("make", "Unknown") if vehicle_info else "Unknown",
            model=vehicle_info.get("model", "Unknown") if vehicle_info else "Unknown",
            year=vehicle_info.get("year", 0) if vehicle_info else 0,
            engine_type=engine_type,
            displacement=0.0,
            cylinders=0,
            injection_system="Unknown",
            turbo_type="Unknown",
            systems=systems,
        )
        
        return DieselDetectionResult(
            is_diesel=True,
            confidence=confidence,
            engine_profile=profile,
            detected_systems=systems,
            reasoning="Detected from telemetry characteristics",
        )
    
    def _detect_from_vehicle_info(self, vehicle_info: Dict[str, Any]) -> Optional[DieselEngineProfile]:
        """Detect engine from vehicle information."""
        make = vehicle_info.get("make", "").lower()
        model = vehicle_info.get("model", "").lower()
        year = vehicle_info.get("year", 0)
        
        # Check known engines
        key = f"{make}_{model}_{year}"
        if key in self.known_diesel_engines:
            return self.known_diesel_engines[key]
        
        # Check by make/model patterns
        for engine_id, profile in self.known_diesel_engines.items():
            if make in profile.make.lower() and model in profile.model.lower():
                if year == 0 or abs(year - profile.year) <= 2:
                    return profile
        
        return None
    
    def _detect_from_telemetry(self, telemetry_data: Dict[str, Any]) -> tuple[bool, float]:
        """
        Detect diesel from telemetry characteristics.
        
        Returns:
            Tuple of (is_diesel, confidence)
        """
        diesel_indicators = 0
        total_checks = 0
        
        # Check for diesel-specific parameters
        diesel_params = [
            "injection_pressure",
            "rail_pressure",
            "fuel_pressure",
            "egr_position",
            "dpf_pressure",
            "scr_temperature",
            "boost_pressure",
            "turbo_boost",
        ]
        
        for param in diesel_params:
            if param in telemetry_data:
                diesel_indicators += 1
            total_checks += 1
        
        # Check RPM range (diesels typically lower)
        rpm = telemetry_data.get("rpm", 0)
        if 0 < rpm < 4000:  # Diesel typical range
            diesel_indicators += 1
        total_checks += 1
        
        # Check for high boost (diesels often have higher boost)
        boost = telemetry_data.get("boost_pressure", telemetry_data.get("boost_psi", 0))
        if boost > 20:  # High boost suggests diesel
            diesel_indicators += 1
        total_checks += 1
        
        # Check for injection timing
        if "injection_timing" in telemetry_data or "timing_advance" in telemetry_data:
            diesel_indicators += 1
        total_checks += 1
        
        confidence = diesel_indicators / total_checks if total_checks > 0 else 0.0
        is_diesel = confidence >= 0.5
        
        return is_diesel, confidence
    
    def _identify_engine_type(self, telemetry_data: Dict[str, Any]) -> DieselEngineType:
        """Identify diesel engine type."""
        # Check for common rail indicators
        if "rail_pressure" in telemetry_data:
            pressure = telemetry_data["rail_pressure"]
            if pressure > 10000:  # PSI - common rail typically high pressure
                return DieselEngineType.COMMON_RAIL
        
        # Check for unit injector
        if "injection_pressure" in telemetry_data:
            return DieselEngineType.UNIT_INJECTOR
        
        # Check for HEUI
        if "heui_pressure" in telemetry_data or "oil_pressure" in telemetry_data:
            oil_pressure = telemetry_data.get("oil_pressure", 0)
            if oil_pressure > 50:  # HEUI uses high oil pressure
                return DieselEngineType.HEUI
        
        # Default to common rail (most common modern diesel)
        return DieselEngineType.COMMON_RAIL
    
    def _detect_systems(self, telemetry_data: Dict[str, Any]) -> List[DieselSystem]:
        """Detect installed diesel systems."""
        systems = []
        
        # EGR
        if "egr_position" in telemetry_data or "egr_valve" in telemetry_data:
            systems.append(DieselSystem.EGR)
        
        # DPF
        if "dpf_pressure" in telemetry_data or "dpf_temperature" in telemetry_data:
            systems.append(DieselSystem.DPF)
        
        # SCR
        if "scr_temperature" in telemetry_data or "def_level" in telemetry_data:
            systems.append(DieselSystem.SCR)
        
        # VGT
        if "vgt_position" in telemetry_data or "turbo_vane" in telemetry_data:
            systems.append(DieselSystem.VGT)
        
        # Wastegate
        if "wastegate_position" in telemetry_data:
            systems.append(DieselSystem.WASTEGATE)
        
        # Intercooler
        if "iat" in telemetry_data and "coolant_temp" in telemetry_data:
            # Check if IAT is significantly lower (intercooled)
            iat = telemetry_data.get("iat", 0)
            if iat < 100:  # Fahrenheit - intercooled
                systems.append(DieselSystem.INTERCOOLER)
        
        # Water/Meth
        if "water_meth_flow" in telemetry_data or "meth_injection" in telemetry_data:
            systems.append(DieselSystem.WATER_METH)
        
        # Nitrous
        if "nitrous_pressure" in telemetry_data or "nitrous_solenoid" in telemetry_data:
            systems.append(DieselSystem.NITROUS)
        
        return systems
    
    def _load_known_engines(self) -> None:
        """Load known diesel engine profiles."""
        # Common diesel engines
        engines = [
            # Cummins
            DieselEngineProfile(
                engine_id="cummins_6.7_ram",
                make="Ram",
                model="2500/3500",
                year=2007,
                engine_type=DieselEngineType.COMMON_RAIL,
                displacement=6.7,
                cylinders=6,
                injection_system="Common Rail",
                turbo_type="VGT",
                systems=[DieselSystem.EGR, DieselSystem.DPF, DieselSystem.SCR, DieselSystem.VGT],
                max_injection_pressure=26000,
                max_boost_pressure=35,
                stock_power=350,
                stock_torque=650,
            ),
            # Duramax
            DieselEngineProfile(
                engine_id="duramax_l5p",
                make="Chevrolet",
                model="Silverado 2500/3500",
                year=2017,
                engine_type=DieselEngineType.COMMON_RAIL,
                displacement=6.6,
                cylinders=8,
                injection_system="Common Rail",
                turbo_type="VGT",
                systems=[DieselSystem.EGR, DieselSystem.DPF, DieselSystem.SCR, DieselSystem.VGT],
                max_injection_pressure=29000,
                max_boost_pressure=32,
                stock_power=445,
                stock_torque=910,
            ),
            # Powerstroke
            DieselEngineProfile(
                engine_id="powerstroke_6.7",
                make="Ford",
                model="F-250/F-350",
                year=2011,
                engine_type=DieselEngineType.COMMON_RAIL,
                displacement=6.7,
                cylinders=8,
                injection_system="Common Rail",
                turbo_type="VGT",
                systems=[DieselSystem.EGR, DieselSystem.DPF, DieselSystem.SCR, DieselSystem.VGT],
                max_injection_pressure=30000,
                max_boost_pressure=35,
                stock_power=400,
                stock_torque=800,
            ),
        ]
        
        for engine in engines:
            key = f"{engine.make.lower()}_{engine.model.lower()}_{engine.year}"
            self.known_diesel_engines[key] = engine
        
        LOGGER.info("Loaded %d known diesel engines", len(self.known_diesel_engines))


