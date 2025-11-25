"""
Diesel Engine Tuner Module

Comprehensive diesel engine support for:
- Cummins (5.9L, 6.7L)
- Duramax (LB7, LLY, LBZ, LMM, LML, L5P)
- Powerstroke (6.0L, 6.4L, 6.7L)
- BMW (various models)
- And other diesel platforms

DIESEL IS VERY DIFFERENT FROM GASOLINE:
- Compression ignition (no spark plugs)
- Fuel injection timing (not ignition timing)
- Rail pressure (high pressure fuel system)
- EGT (Exhaust Gas Temperature) - critical
- Boost pressure (most are turbocharged)
- EGR (Exhaust Gas Recirculation)
- DPF (Diesel Particulate Filter)
- DEF/AdBlue (Diesel Exhaust Fluid)
- Torque-based tuning (not RPM-based)
- Fuel quantity (injection quantity, not AFR)
- Pilot injection (multiple injection events)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from services.voice_feedback import FeedbackPriority, VoiceFeedback

LOGGER = logging.getLogger(__name__)


class DieselEngineType(Enum):
    """Supported diesel engine platforms."""

    # Cummins
    CUMMINS_59L = "cummins_5.9l"  # ISB 5.9L
    CUMMINS_67L = "cummins_6.7l"  # ISB 6.7L
    CUMMINS_68L = "cummins_6.8l"  # ISB 6.8L

    # Duramax
    DURAMAX_LB7 = "duramax_lb7"  # 2001-2004
    DURAMAX_LLY = "duramax_lly"  # 2004-2005
    DURAMAX_LBZ = "duramax_lbz"  # 2006-2007
    DURAMAX_LMM = "duramax_lmm"  # 2007-2010
    DURAMAX_LML = "duramax_lml"  # 2011-2016
    DURAMAX_L5P = "duramax_l5p"  # 2017+

    # Powerstroke
    POWERSTROKE_60L = "powerstroke_6.0l"  # 2003-2007
    POWERSTROKE_64L = "powerstroke_6.4l"  # 2008-2010
    POWERSTROKE_67L = "powerstroke_6.7l"  # 2011+

    # BMW
    BMW_M57 = "bmw_m57"  # 3.0L I6
    BMW_N57 = "bmw_n57"  # 3.0L I6 (newer)
    BMW_M67 = "bmw_m67"  # V8
    BMW_N67 = "bmw_n67"  # V8 (newer)

    # Other
    CATERPILLAR = "caterpillar"
    DETROIT_DIESEL = "detroit_diesel"
    VOLVO = "volvo"
    MERCEDES = "mercedes"
    VW_TDI = "vw_tdi"
    GENERIC = "generic_diesel"


class DieselParameter(Enum):
    """Diesel-specific tuning parameters."""

    # Fuel System
    FUEL_RAIL_PRESSURE = "fuel_rail_pressure"  # PSI (common rail)
    INJECTION_TIMING = "injection_timing"  # Degrees BTDC
    INJECTION_QUANTITY = "injection_quantity"  # mm³
    PILOT_INJECTION_QUANTITY = "pilot_injection_quantity"  # mm³
    POST_INJECTION_QUANTITY = "post_injection_quantity"  # mm³
    FUEL_PRESSURE_REGULATOR = "fuel_pressure_regulator"  # %

    # Turbo/Boost
    BOOST_PRESSURE = "boost_pressure"  # PSI
    VGT_POSITION = "vgt_position"  # % (Variable Geometry Turbo)
    WASTEGATE_POSITION = "wastegate_position"  # %
    TURBO_BOOST_TARGET = "turbo_boost_target"  # PSI

    # Temperature
    EGT = "egt"  # Exhaust Gas Temperature (°F)
    EGT_PRE_TURBO = "egt_pre_turbo"  # Pre-turbo EGT
    EGT_POST_TURBO = "egt_post_turbo"  # Post-turbo EGT
    COOLANT_TEMP = "coolant_temp"  # °F
    OIL_TEMP = "oil_temp"  # °F
    INTAKE_AIR_TEMP = "intake_air_temp"  # °F

    # Emissions
    EGR_POSITION = "egr_position"  # % (Exhaust Gas Recirculation)
    EGR_FLOW = "egr_flow"  # g/s
    DPF_PRESSURE = "dpf_pressure"  # PSI (Diesel Particulate Filter)
    DPF_REGEN_STATUS = "dpf_regen_status"  # 0=off, 1=active
    DEF_LEVEL = "def_level"  # % (Diesel Exhaust Fluid/AdBlue)
    NOX_SENSOR = "nox_sensor"  # PPM

    # Performance
    TORQUE = "torque"  # lb-ft
    TORQUE_LIMIT = "torque_limit"  # lb-ft
    HORSEPOWER = "horsepower"  # HP
    RPM = "rpm"  # RPM
    SPEED = "speed"  # MPH

    # Safety
    RAIL_PRESSURE_LIMIT = "rail_pressure_limit"  # PSI
    EGT_LIMIT = "egt_limit"  # °F
    BOOST_LIMIT = "boost_limit"  # PSI


@dataclass
class DieselTuningRecommendation:
    """Diesel tuning recommendation."""

    parameter: DieselParameter
    current_value: float
    recommended_value: float
    reason: str
    priority: FeedbackPriority
    confidence: float  # 0-1
    auto_apply: bool = False
    safety_critical: bool = False


@dataclass
class DieselEngineProfile:
    """Diesel engine platform profile with limits and characteristics."""

    engine_type: DieselEngineType
    name: str
    displacement: str
    year_range: str

    # Fuel System Limits
    max_rail_pressure: float  # PSI
    min_rail_pressure: float  # PSI
    max_injection_quantity: float  # mm³
    injection_timing_range: Tuple[float, float]  # (min, max) degrees BTDC

    # Boost Limits
    max_boost: float  # PSI
    max_egt: float  # °F (critical!)
    safe_egt: float  # °F (safe operating)

    # Torque Limits
    max_torque: float  # lb-ft
    max_horsepower: float  # HP

    # Emissions
    has_egr: bool = True
    has_dpf: bool = False
    has_def: bool = False

    # Characteristics
    is_common_rail: bool = True
    has_vgt: bool = True
    has_pilot_injection: bool = True


class DieselTuner:
    """
    Comprehensive Diesel Engine Tuner.

    Handles all diesel-specific parameters and tuning for various platforms.
    """

    # Engine profiles with platform-specific limits
    ENGINE_PROFILES: Dict[DieselEngineType, DieselEngineProfile] = {
        # Cummins 5.9L
        DieselEngineType.CUMMINS_59L: DieselEngineProfile(
            engine_type=DieselEngineType.CUMMINS_59L,
            name="Cummins 5.9L ISB",
            displacement="5.9L",
            year_range="1998-2007",
            max_rail_pressure=24000,  # PSI
            min_rail_pressure=5000,
            max_injection_quantity=200,  # mm³
            injection_timing_range=(-5.0, 25.0),
            max_boost=45.0,  # PSI
            max_egt=1650,  # °F
            safe_egt=1400,  # °F
            max_torque=600,  # lb-ft
            max_horsepower=325,
            has_egr=True,
            has_dpf=False,
            has_def=False,
            is_common_rail=True,
            has_vgt=True,
            has_pilot_injection=True,
        ),
        # Cummins 6.7L
        DieselEngineType.CUMMINS_67L: DieselEngineProfile(
            engine_type=DieselEngineType.CUMMINS_67L,
            name="Cummins 6.7L ISB",
            displacement="6.7L",
            year_range="2007+",
            max_rail_pressure=26000,  # PSI
            min_rail_pressure=5000,
            max_injection_quantity=220,  # mm³
            injection_timing_range=(-5.0, 30.0),
            max_boost=50.0,  # PSI
            max_egt=1650,  # °F
            safe_egt=1400,  # °F
            max_torque=800,  # lb-ft
            max_horsepower=400,
            has_egr=True,
            has_dpf=True,
            has_def=True,
            is_common_rail=True,
            has_vgt=True,
            has_pilot_injection=True,
        ),
        # Duramax LB7
        DieselEngineType.DURAMAX_LB7: DieselEngineProfile(
            engine_type=DieselEngineType.DURAMAX_LB7,
            name="Duramax LB7",
            displacement="6.6L",
            year_range="2001-2004",
            max_rail_pressure=23000,  # PSI
            min_rail_pressure=5000,
            max_injection_quantity=180,  # mm³
            injection_timing_range=(-3.0, 22.0),
            max_boost=35.0,  # PSI
            max_egt=1600,  # °F
            safe_egt=1350,  # °F
            max_torque=520,  # lb-ft
            max_horsepower=300,
            has_egr=True,
            has_dpf=False,
            has_def=False,
            is_common_rail=True,
            has_vgt=True,
            has_pilot_injection=True,
        ),
        # Duramax L5P (newest)
        DieselEngineType.DURAMAX_L5P: DieselEngineProfile(
            engine_type=DieselEngineType.DURAMAX_L5P,
            name="Duramax L5P",
            displacement="6.6L",
            year_range="2017+",
            max_rail_pressure=29000,  # PSI
            min_rail_pressure=5000,
            max_injection_quantity=250,  # mm³
            injection_timing_range=(-5.0, 35.0),
            max_boost=55.0,  # PSI
            max_egt=1700,  # °F
            safe_egt=1450,  # °F
            max_torque=910,  # lb-ft
            max_horsepower=445,
            has_egr=True,
            has_dpf=True,
            has_def=True,
            is_common_rail=True,
            has_vgt=True,
            has_pilot_injection=True,
        ),
        # Powerstroke 6.7L
        DieselEngineType.POWERSTROKE_67L: DieselEngineProfile(
            engine_type=DieselEngineType.POWERSTROKE_67L,
            name="Powerstroke 6.7L",
            displacement="6.7L",
            year_range="2011+",
            max_rail_pressure=28000,  # PSI
            min_rail_pressure=5000,
            max_injection_quantity=240,  # mm³
            injection_timing_range=(-5.0, 32.0),
            max_boost=52.0,  # PSI
            max_egt=1650,  # °F
            safe_egt=1400,  # °F
            max_torque=925,  # lb-ft
            max_horsepower=450,
            has_egr=True,
            has_dpf=True,
            has_def=True,
            is_common_rail=True,
            has_vgt=True,
            has_pilot_injection=True,
        ),
        # BMW M57
        DieselEngineType.BMW_M57: DieselEngineProfile(
            engine_type=DieselEngineType.BMW_M57,
            name="BMW M57",
            displacement="3.0L",
            year_range="1998-2013",
            max_rail_pressure=18000,  # PSI
            min_rail_pressure=3000,
            max_injection_quantity=120,  # mm³
            injection_timing_range=(-2.0, 18.0),
            max_boost=28.0,  # PSI
            max_egt=1550,  # °F
            safe_egt=1300,  # °F
            max_torque=428,  # lb-ft
            max_horsepower=286,
            has_egr=True,
            has_dpf=True,
            has_def=True,
            is_common_rail=True,
            has_vgt=True,
            has_pilot_injection=True,
        ),
        # BMW N57
        DieselEngineType.BMW_N57: DieselEngineProfile(
            engine_type=DieselEngineType.BMW_N57,
            name="BMW N57",
            displacement="3.0L",
            year_range="2008+",
            max_rail_pressure=22000,  # PSI
            min_rail_pressure=3000,
            max_injection_quantity=140,  # mm³
            injection_timing_range=(-3.0, 22.0),
            max_boost=32.0,  # PSI
            max_egt=1600,  # °F
            safe_egt=1350,  # °F
            max_torque=560,  # lb-ft
            max_horsepower=381,
            has_egr=True,
            has_dpf=True,
            has_def=True,
            is_common_rail=True,
            has_vgt=True,
            has_pilot_injection=True,
        ),
    }

    def __init__(
        self,
        engine_type: Optional[DieselEngineType] = None,
        voice_feedback: Optional[VoiceFeedback] = None,
        auto_apply: bool = False,
    ) -> None:
        """
        Initialize diesel tuner.

        Args:
            engine_type: Specific diesel engine platform
            voice_feedback: Voice feedback for announcements
            auto_apply: Automatically apply safe recommendations
        """
        self.engine_type = engine_type or DieselEngineType.GENERIC
        self.voice_feedback = voice_feedback
        self.auto_apply = auto_apply

        # Get engine profile
        self.profile = self.ENGINE_PROFILES.get(self.engine_type)
        if not self.profile:
            LOGGER.warning(f"No profile for {self.engine_type}, using generic limits")
            self.profile = self._create_generic_profile()

        # Current telemetry
        self.current_telemetry: Dict[str, float] = {}
        self.tuning_history: List[DieselTuningRecommendation] = []

        # Safety monitoring
        self.egt_warning_threshold = self.profile.safe_egt
        self.egt_critical_threshold = self.profile.max_egt - 50  # 50°F buffer

        LOGGER.info(f"Initialized Diesel Tuner for {self.profile.name}")

    def _create_generic_profile(self) -> DieselEngineProfile:
        """Create generic diesel profile for unknown engines."""
        return DieselEngineProfile(
            engine_type=DieselEngineType.GENERIC,
            name="Generic Diesel",
            displacement="Unknown",
            year_range="Unknown",
            max_rail_pressure=25000,  # PSI
            min_rail_pressure=5000,
            max_injection_quantity=200,  # mm³
            injection_timing_range=(-5.0, 25.0),
            max_boost=45.0,  # PSI
            max_egt=1650,  # °F
            safe_egt=1400,  # °F
            max_torque=600,  # lb-ft
            max_horsepower=350,
            has_egr=True,
            has_dpf=False,
            has_def=False,
            is_common_rail=True,
            has_vgt=True,
            has_pilot_injection=True,
        )

    def update_telemetry(self, telemetry: Dict[str, float]) -> None:
        """Update current telemetry data."""
        self.current_telemetry = telemetry.copy()

        # Monitor critical parameters
        self._monitor_egt()
        self._monitor_rail_pressure()
        self._monitor_boost()

    def analyze_and_recommend(self) -> List[DieselTuningRecommendation]:
        """
        Analyze current diesel parameters and provide tuning recommendations.

        Returns:
            List of tuning recommendations
        """
        recommendations = []

        # Analyze EGT (most critical for diesel)
        egt_rec = self._analyze_egt()
        if egt_rec:
            recommendations.append(egt_rec)

        # Analyze rail pressure
        rail_rec = self._analyze_rail_pressure()
        if rail_rec:
            recommendations.append(rail_rec)

        # Analyze injection timing
        timing_rec = self._analyze_injection_timing()
        if timing_rec:
            recommendations.append(timing_rec)

        # Analyze boost pressure
        boost_rec = self._analyze_boost()
        if boost_rec:
            recommendations.append(boost_rec)

        # Analyze injection quantity
        quantity_rec = self._analyze_injection_quantity()
        if quantity_rec:
            recommendations.append(quantity_rec)

        # Analyze emissions systems
        emissions_recs = self._analyze_emissions()
        recommendations.extend(emissions_recs)

        # Store in history
        self.tuning_history.extend(recommendations)

        return recommendations

    def _analyze_egt(self) -> Optional[DieselTuningRecommendation]:
        """Analyze Exhaust Gas Temperature (critical for diesel)."""
        egt = self.current_telemetry.get("EGT", self.current_telemetry.get("ExhaustGasTemp", 0))

        if egt <= 0:
            return None

        # Critical thresholds
        if egt >= self.egt_critical_threshold:
            return DieselTuningRecommendation(
                parameter=DieselParameter.EGT,
                current_value=egt,
                recommended_value=self.profile.safe_egt,
                reason=f"CRITICAL: EGT at {egt:.0f}°F exceeds safe limit! Reduce fuel or boost immediately.",
                priority=FeedbackPriority.CRITICAL,
                confidence=1.0,
                safety_critical=True,
            )

        if egt >= self.egt_warning_threshold:
            return DieselTuningRecommendation(
                parameter=DieselParameter.EGT,
                current_value=egt,
                recommended_value=egt - 50,  # Reduce by 50°F
                reason=f"EGT at {egt:.0f}°F is approaching limit. Consider reducing fuel or boost.",
                priority=FeedbackPriority.HIGH,
                confidence=0.8,
                safety_critical=True,
            )

        # Optimization: EGT too low (inefficient)
        if egt < self.profile.safe_egt - 200:
            return DieselTuningRecommendation(
                parameter=DieselParameter.EGT,
                current_value=egt,
                recommended_value=self.profile.safe_egt - 100,
                reason=f"EGT at {egt:.0f}°F is low. Can increase fuel/timing for better efficiency.",
                priority=FeedbackPriority.LOW,
                confidence=0.6,
                safety_critical=False,
            )

        return None

    def _analyze_rail_pressure(self) -> Optional[DieselTuningRecommendation]:
        """Analyze fuel rail pressure."""
        rail_pressure = self.current_telemetry.get(
            "FuelRailPressure",
            self.current_telemetry.get("RailPressure", 0),
        )

        if rail_pressure <= 0:
            return None

        # Too high (dangerous)
        if rail_pressure >= self.profile.max_rail_pressure * 0.95:
            return DieselTuningRecommendation(
                parameter=DieselParameter.FUEL_RAIL_PRESSURE,
                current_value=rail_pressure,
                recommended_value=self.profile.max_rail_pressure * 0.90,
                reason=f"Rail pressure {rail_pressure:.0f} PSI near maximum. Reduce to prevent damage.",
                priority=FeedbackPriority.CRITICAL,
                confidence=1.0,
                safety_critical=True,
            )

        # Too low (poor performance)
        if rail_pressure < self.profile.min_rail_pressure * 1.2:
            return DieselTuningRecommendation(
                parameter=DieselParameter.FUEL_RAIL_PRESSURE,
                current_value=rail_pressure,
                recommended_value=self.profile.min_rail_pressure * 1.5,
                reason=f"Rail pressure {rail_pressure:.0f} PSI is low. Increase for better atomization.",
                priority=FeedbackPriority.MEDIUM,
                confidence=0.7,
                safety_critical=False,
            )

        return None

    def _analyze_injection_timing(self) -> Optional[DieselTuningRecommendation]:
        """Analyze injection timing (diesel equivalent of ignition timing)."""
        timing = self.current_telemetry.get(
            "InjectionTiming",
            self.current_telemetry.get("FuelTiming", 0),
        )

        if timing == 0 and "InjectionTiming" not in self.current_telemetry:
            return None

        min_timing, max_timing = self.profile.injection_timing_range

        # Out of range
        if timing < min_timing or timing > max_timing:
            return DieselTuningRecommendation(
                parameter=DieselParameter.INJECTION_TIMING,
                current_value=timing,
                recommended_value=(min_timing + max_timing) / 2,
                reason=f"Injection timing {timing:.1f}° is outside safe range ({min_timing} to {max_timing}°).",
                priority=FeedbackPriority.HIGH,
                confidence=0.9,
                safety_critical=True,
            )

        return None

    def _analyze_boost(self) -> Optional[DieselTuningRecommendation]:
        """Analyze boost pressure."""
        boost = self.current_telemetry.get(
            "BoostPressure",
            self.current_telemetry.get("ManifoldPressure", 0),
        )

        if boost <= 0:
            return None

        # Too high
        if boost >= self.profile.max_boost * 0.95:
            return DieselTuningRecommendation(
                parameter=DieselParameter.BOOST_PRESSURE,
                current_value=boost,
                recommended_value=self.profile.max_boost * 0.90,
                reason=f"Boost {boost:.1f} PSI near maximum. Reduce to prevent turbo damage.",
                priority=FeedbackPriority.HIGH,
                confidence=0.9,
                safety_critical=True,
            )

        return None

    def _analyze_injection_quantity(self) -> Optional[DieselTuningRecommendation]:
        """Analyze injection quantity."""
        quantity = self.current_telemetry.get("InjectionQuantity", 0)

        if quantity <= 0:
            return None

        # Too high
        if quantity >= self.profile.max_injection_quantity * 0.95:
            return DieselTuningRecommendation(
                parameter=DieselParameter.INJECTION_QUANTITY,
                current_value=quantity,
                recommended_value=self.profile.max_injection_quantity * 0.90,
                reason=f"Injection quantity {quantity:.1f} mm³ near maximum. Reduce to prevent over-fueling.",
                priority=FeedbackPriority.HIGH,
                confidence=0.8,
                safety_critical=True,
            )

        return None

    def _analyze_emissions(self) -> List[DieselTuningRecommendation]:
        """Analyze emissions systems (EGR, DPF, DEF)."""
        recommendations = []

        # DPF pressure (if equipped)
        if self.profile.has_dpf:
            dpf_pressure = self.current_telemetry.get("DPFPressure", 0)
            if dpf_pressure > 10.0:  # PSI - high pressure indicates clogging
                recommendations.append(
                    DieselTuningRecommendation(
                        parameter=DieselParameter.DPF_PRESSURE,
                        current_value=dpf_pressure,
                        recommended_value=5.0,
                        reason=f"DPF pressure {dpf_pressure:.1f} PSI is high. Regeneration may be needed.",
                        priority=FeedbackPriority.MEDIUM,
                        confidence=0.7,
                        safety_critical=False,
                    )
                )

        # DEF level (if equipped)
        if self.profile.has_def:
            def_level = self.current_telemetry.get("DEFLevel", self.current_telemetry.get("AdBlueLevel", 100))
            if def_level < 20:  # %
                recommendations.append(
                    DieselTuningRecommendation(
                        parameter=DieselParameter.DEF_LEVEL,
                        current_value=def_level,
                        recommended_value=50,
                        reason=f"DEF/AdBlue level at {def_level:.0f}%. Refill soon to avoid derate.",
                        priority=FeedbackPriority.MEDIUM,
                        confidence=0.9,
                        safety_critical=False,
                    )
                )

        return recommendations

    def _monitor_egt(self) -> None:
        """Monitor EGT and provide voice feedback if critical."""
        egt = self.current_telemetry.get("EGT", self.current_telemetry.get("ExhaustGasTemp", 0))

        if egt > 0 and self.voice_feedback:
            if egt >= self.egt_critical_threshold:
                self.voice_feedback.announce(
                    f"CRITICAL: EGT at {egt:.0f} degrees! Reduce fuel immediately!",
                    FeedbackPriority.CRITICAL,
                )
            elif egt >= self.egt_warning_threshold:
                self.voice_feedback.announce(
                    f"Warning: EGT at {egt:.0f} degrees, approaching limit.",
                    FeedbackPriority.HIGH,
                )

    def _monitor_rail_pressure(self) -> None:
        """Monitor rail pressure and provide voice feedback if critical."""
        rail_pressure = self.current_telemetry.get(
            "FuelRailPressure",
            self.current_telemetry.get("RailPressure", 0),
        )

        if rail_pressure > 0 and self.voice_feedback:
            if rail_pressure >= self.profile.max_rail_pressure * 0.95:
                self.voice_feedback.announce(
                    f"Warning: Rail pressure at {rail_pressure:.0f} PSI, near maximum.",
                    FeedbackPriority.HIGH,
                )

    def _monitor_boost(self) -> None:
        """Monitor boost pressure and provide voice feedback if critical."""
        boost = self.current_telemetry.get(
            "BoostPressure",
            self.current_telemetry.get("ManifoldPressure", 0),
        )

        if boost > 0 and self.voice_feedback:
            if boost >= self.profile.max_boost * 0.95:
                self.voice_feedback.announce(
                    f"Warning: Boost at {boost:.1f} PSI, near maximum.",
                    FeedbackPriority.HIGH,
                )

    def detect_engine_type(self, telemetry: Dict[str, float]) -> Optional[DieselEngineType]:
        """
        Attempt to detect diesel engine type from telemetry.

        Args:
            telemetry: Current telemetry data

        Returns:
            Detected engine type or None
        """
        # This would use CAN IDs, rail pressure characteristics, etc.
        # For now, return None (user must specify)
        return None

    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the current engine profile."""
        return {
            "engine_type": self.engine_type.value,
            "name": self.profile.name,
            "displacement": self.profile.displacement,
            "year_range": self.profile.year_range,
            "max_rail_pressure": self.profile.max_rail_pressure,
            "max_boost": self.profile.max_boost,
            "max_egt": self.profile.max_egt,
            "has_dpf": self.profile.has_dpf,
            "has_def": self.profile.has_def,
        }


__all__ = [
    "DieselEngineType",
    "DieselParameter",
    "DieselTuningRecommendation",
    "DieselEngineProfile",
    "DieselTuner",
]

