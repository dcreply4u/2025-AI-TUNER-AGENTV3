"""
Global Auto-Detection System
Comprehensive auto-detection for all detectable components and settings
"""

from __future__ import annotations

import logging
import re
import time
import serial.tools.list_ports
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

try:
    import can
    CAN_AVAILABLE = True
except ImportError:
    CAN_AVAILABLE = False
    can = None  # type: ignore

try:
    from services.multi_ecu_detector import MultiECUDetector, DetectedECU, ECUType, ECUConflictType
    MULTI_ECU_AVAILABLE = True
except ImportError:
    MULTI_ECU_AVAILABLE = False
    MultiECUDetector = None  # type: ignore
    DetectedECU = None  # type: ignore
    ECUType = None  # type: ignore
    ECUConflictType = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class EngineType(Enum):
    """Engine type enumeration."""
    UNKNOWN = "unknown"
    I4 = "inline_4"
    I6 = "inline_6"
    V6 = "v6"
    V8 = "v8"
    V10 = "v10"
    V12 = "v12"
    ROTARY = "rotary"
    BOXER = "boxer"


class ForcedInductionType(Enum):
    """Forced induction type."""
    NONE = "naturally_aspirated"
    TURBO = "turbocharged"
    SUPERCHARGER = "supercharged"
    TWIN_TURBO = "twin_turbo"
    TWIN_SCROLL = "twin_scroll"


class TransmissionType(Enum):
    """Transmission type."""
    UNKNOWN = "unknown"
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    DCT = "dct"
    CVT = "cvt"
    SEQUENTIAL = "sequential"


class FuelType(Enum):
    """Fuel type."""
    GASOLINE = "gasoline"
    E85 = "e85"
    METHANOL = "methanol"
    NITROMETHANE = "nitromethane"
    DIESEL = "diesel"


@dataclass
class DetectedSensor:
    """Detected sensor information."""
    name: str
    sensor_type: str
    channel: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: Optional[str] = None
    calibration_factor: float = 1.0
    offset: float = 0.0
    detected: bool = False
    confidence: float = 0.0  # 0-1


@dataclass
class DetectedEngine:
    """Detected engine information."""
    engine_type: EngineType = EngineType.UNKNOWN
    cylinder_count: int = 0
    displacement: float = 0.0  # Liters
    forced_induction: ForcedInductionType = ForcedInductionType.NONE
    max_rpm: int = 8000
    redline: int = 7000
    confidence: float = 0.0


@dataclass
class DetectedTransmission:
    """Detected transmission information."""
    transmission_type: TransmissionType = TransmissionType.UNKNOWN
    gear_count: int = 0
    gear_ratios: List[float] = field(default_factory=list)
    final_drive: float = 0.0
    confidence: float = 0.0


@dataclass
class DetectedCommunication:
    """Detected communication interface."""
    interface_type: str  # "CAN", "Serial", "USB", "Ethernet"
    port: Optional[str] = None
    baudrate: Optional[int] = None
    can_speed: Optional[int] = None
    device_id: Optional[str] = None
    description: str = ""
    detected: bool = False


@dataclass
class DetectedECUParameters:
    """Detected ECU parameters."""
    available_parameters: List[str] = field(default_factory=list)
    parameter_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    default_values: Dict[str, float] = field(default_factory=dict)
    parameter_count: int = 0


@dataclass
class AutoDetectionResults:
    """Complete auto-detection results."""
    sensors: List[DetectedSensor] = field(default_factory=list)
    engine: DetectedEngine = field(default_factory=DetectedEngine)
    transmission: DetectedTransmission = field(default_factory=DetectedTransmission)
    communication: List[DetectedCommunication] = field(default_factory=list)
    ecu_parameters: DetectedECUParameters = field(default_factory=DetectedECUParameters)
    fuel_system: Dict[str, any] = field(default_factory=dict)
    ignition_system: Dict[str, any] = field(default_factory=dict)
    detected_ecus: List = field(default_factory=list)  # List of DetectedECU
    piggyback_systems: List = field(default_factory=list)
    ecu_conflicts: Dict[str, any] = field(default_factory=dict)
    detected_at: float = field(default_factory=time.time)


class GlobalAutoDetector:
    """
    Global auto-detection system for all detectable components.
    
    Features:
    - Sensor auto-detection (CAN, analog, digital)
    - Engine/vehicle auto-detection
    - Communication port auto-detection
    - ECU parameter auto-detection
    - Configuration auto-detection
    """
    
    def __init__(self):
        """Initialize global auto-detector."""
        self.results = AutoDetectionResults()
        self.multi_ecu_detector: Optional[MultiECUDetector] = None
        if MULTI_ECU_AVAILABLE and MultiECUDetector:
            try:
                self.multi_ecu_detector = MultiECUDetector()
            except Exception as e:
                LOGGER.warning("Could not initialize multi-ECU detector: %s", e)
    
    def detect_all(self, telemetry_data: Optional[Dict[str, float]] = None) -> AutoDetectionResults:
        """
        Run comprehensive auto-detection for all components.
        
        Args:
            telemetry_data: Optional telemetry data to aid detection
            
        Returns:
            Complete auto-detection results
        """
        LOGGER.info("Starting comprehensive auto-detection...")
        
        # Detect communication interfaces
        self.results.communication = self.detect_communication_interfaces()
        
        # Detect sensors
        self.results.sensors = self.detect_sensors(telemetry_data)
        
        # Detect engine
        self.results.engine = self.detect_engine(telemetry_data)
        
        # Detect transmission
        self.results.transmission = self.detect_transmission(telemetry_data)
        
        # Detect ECU parameters
        self.results.ecu_parameters = self.detect_ecu_parameters(telemetry_data)
        
        # Detect fuel system
        self.results.fuel_system = self.detect_fuel_system(telemetry_data)
        
        # Detect ignition system
        self.results.ignition_system = self.detect_ignition_system(telemetry_data)
        
        # Detect multiple ECUs, piggyback systems, and conflicts
        if self.multi_ecu_detector:
            try:
                detected_ecus = self.multi_ecu_detector.detect_all_ecus(sample_time=10.0)
                self.results.detected_ecus = detected_ecus
                self.results.piggyback_systems = self.multi_ecu_detector.piggyback_systems
                self.results.ecu_conflicts = self.multi_ecu_detector.get_conflict_summary()
            except Exception as e:
                LOGGER.warning("Multi-ECU detection failed: %s", e)
            finally:
                # Cleanup CAN bus connection
                try:
                    self.multi_ecu_detector.shutdown()
                except Exception:
                    pass
        
        LOGGER.info("Auto-detection complete: %d sensors, %d communication interfaces, %d ECUs",
                   len(self.results.sensors), len(self.results.communication), len(self.results.detected_ecus))
        
        return self.results
    
    def detect_communication_interfaces(self) -> List[DetectedCommunication]:
        """Detect all available communication interfaces."""
        interfaces = []
        
        # Detect CAN interfaces
        if CAN_AVAILABLE:
            try:
                can_interfaces = can.detect_available_configs()
                for interface in can_interfaces:
                    interfaces.append(DetectedCommunication(
                        interface_type="CAN",
                        port=interface.get("interface"),
                        can_speed=interface.get("bitrate", 500000),
                        description=f"CAN {interface.get('interface', 'unknown')}",
                        detected=True
                    ))
            except Exception as e:
                LOGGER.warning("Could not detect CAN interfaces: %s", e)
        
        # Detect serial ports
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                interfaces.append(DetectedCommunication(
                    interface_type="Serial",
                    port=port.device,
                    baudrate=115200,  # Default
                    description=port.description,
                    device_id=port.hwid,
                    detected=True
                ))
        except Exception as e:
            LOGGER.warning("Could not detect serial ports: %s", e)
        
        # Detect USB devices (basic)
        try:
            import usb.core
            usb_devices = usb.core.find(find_all=True)
            for device in usb_devices:
                interfaces.append(DetectedCommunication(
                    interface_type="USB",
                    device_id=f"{device.idVendor:04x}:{device.idProduct:04x}",
                    description=f"USB Device {device.idVendor:04x}:{device.idProduct:04x}",
                    detected=True
                ))
        except ImportError:
            LOGGER.debug("pyusb not available for USB detection")
        except Exception as e:
            LOGGER.warning("Could not detect USB devices: %s", e)
        
        return interfaces
    
    def detect_sensors(self, telemetry_data: Optional[Dict[str, float]] = None) -> List[DetectedSensor]:
        """Detect available sensors from telemetry data."""
        sensors = []
        
        if not telemetry_data:
            return sensors
        
        # Common sensor patterns
        sensor_patterns = {
            "RPM": ("RPM", "Engine_RPM", "rpm", "engine_rpm"),
            "Throttle": ("Throttle_Position", "TPS", "throttle", "tps"),
            "Boost": ("Boost_Pressure", "boost_psi", "boost", "MAP"),
            "AFR": ("AFR", "Lambda", "lambda_value", "air_fuel_ratio"),
            "Coolant_Temp": ("Coolant_Temp", "ECT", "coolant", "engine_temp"),
            "Oil_Pressure": ("Oil_Pressure", "oil_pressure", "oil_p"),
            "Oil_Temp": ("Oil_Temp", "oil_temp", "oil_t"),
            "Fuel_Pressure": ("Fuel_Pressure", "fuel_pressure", "fuel_p"),
            "EGT": ("EGT", "Exhaust_Gas_Temp", "exhaust_temp"),
            "IAT": ("IAT", "Intake_Air_Temp", "intake_temp"),
            "Knock": ("Knock_Count", "knock", "knock_count"),
            "Speed": ("Speed", "Vehicle_Speed", "speed", "vehicle_speed"),
            "Gear": ("Gear", "Current_Gear", "gear", "current_gear"),
        }
        
        for sensor_name, patterns in sensor_patterns.items():
            for pattern in patterns:
                if pattern in telemetry_data:
                    value = telemetry_data[pattern]
                    
                    # Determine sensor type and ranges
                    sensor_type, min_val, max_val, unit = self._infer_sensor_properties(sensor_name, value)
                    
                    sensors.append(DetectedSensor(
                        name=sensor_name,
                        sensor_type=sensor_type,
                        min_value=min_val,
                        max_value=max_val,
                        unit=unit,
                        detected=True,
                        confidence=0.8 if isinstance(value, (int, float)) and value > 0 else 0.5
                    ))
                    break  # Found, move to next sensor
        
        return sensors
    
    def _infer_sensor_properties(self, sensor_name: str, value: float) -> Tuple[str, Optional[float], Optional[float], Optional[str]]:
        """Infer sensor properties from name and value."""
        sensor_ranges = {
            "RPM": ("RPM", 0, 10000, "RPM"),
            "Throttle": ("TPS", 0, 100, "%"),
            "Boost": ("Pressure", -5, 50, "psi"),
            "AFR": ("AFR", 10, 20, "AFR"),
            "Coolant_Temp": ("Temperature", -40, 150, "°C"),
            "Oil_Pressure": ("Pressure", 0, 100, "psi"),
            "Oil_Temp": ("Temperature", 0, 200, "°C"),
            "Fuel_Pressure": ("Pressure", 0, 100, "psi"),
            "EGT": ("Temperature", 0, 2000, "°C"),
            "IAT": ("Temperature", -40, 150, "°C"),
            "Knock": ("Count", 0, 100, "count"),
            "Speed": ("Speed", 0, 300, "mph"),
            "Gear": ("Gear", 0, 6, "gear"),
        }
        
        return sensor_ranges.get(sensor_name, ("Unknown", None, None, None))
    
    def detect_engine(self, telemetry_data: Optional[Dict[str, float]] = None) -> DetectedEngine:
        """Detect engine type and characteristics."""
        engine = DetectedEngine()
        
        if not telemetry_data:
            return engine
        
        # Detect from RPM patterns
        rpm = telemetry_data.get("RPM", telemetry_data.get("Engine_RPM", 0))
        if rpm > 0:
            # Infer max RPM from observed values
            if rpm > 8000:
                engine.max_rpm = 10000
                engine.redline = 9000
            elif rpm > 6000:
                engine.max_rpm = 8000
                engine.redline = 7000
            else:
                engine.max_rpm = 6000
                engine.redline = 5500
            
            engine.confidence = 0.6
        
        # Detect forced induction from boost
        boost = telemetry_data.get("Boost_Pressure", telemetry_data.get("boost_psi", 0))
        if boost > 0:
            if boost > 20:
                engine.forced_induction = ForcedInductionType.TWIN_TURBO
            elif boost > 10:
                engine.forced_induction = ForcedInductionType.TURBO
            else:
                engine.forced_induction = ForcedInductionType.TURBO
            engine.confidence = max(engine.confidence, 0.7)
        else:
            engine.forced_induction = ForcedInductionType.NONE
        
        # Try to detect cylinder count from RPM patterns (advanced)
        # This would require more sophisticated analysis
        
        return engine
    
    def detect_transmission(self, telemetry_data: Optional[Dict[str, float]] = None) -> DetectedTransmission:
        """Detect transmission type and characteristics."""
        transmission = DetectedTransmission()
        
        if not telemetry_data:
            return transmission
        
        # Detect gear from telemetry
        gear = telemetry_data.get("Gear", telemetry_data.get("Current_Gear", 0))
        if gear > 0:
            if gear <= 6:
                transmission.transmission_type = TransmissionType.MANUAL
                transmission.gear_count = int(gear)
            else:
                transmission.transmission_type = TransmissionType.AUTOMATIC
                transmission.gear_count = 8  # Common modern auto
            transmission.confidence = 0.6
        
        # Detect from speed/RPM ratio patterns (would need historical data)
        
        return transmission
    
    def detect_ecu_parameters(self, telemetry_data: Optional[Dict[str, float]] = None) -> DetectedECUParameters:
        """Detect available ECU parameters."""
        params = DetectedECUParameters()
        
        if not telemetry_data:
            return params
        
        # Extract all available parameters from telemetry
        params.available_parameters = list(telemetry_data.keys())
        params.parameter_count = len(params.available_parameters)
        
        # Infer ranges from current values
        for key, value in telemetry_data.items():
            if isinstance(value, (int, float)):
                # Estimate range (current value ± 50% or known ranges)
                if "RPM" in key.upper():
                    params.parameter_ranges[key] = (0, 10000)
                elif "Temp" in key or "temp" in key:
                    params.parameter_ranges[key] = (-40, 200)
                elif "Pressure" in key or "pressure" in key:
                    params.parameter_ranges[key] = (0, 100)
                elif "AFR" in key.upper() or "Lambda" in key:
                    params.parameter_ranges[key] = (10, 20)
                else:
                    # Generic range
                    params.parameter_ranges[key] = (value * 0.5, value * 2.0)
                
                params.default_values[key] = value
        
        return params
    
    def detect_fuel_system(self, telemetry_data: Optional[Dict[str, float]] = None) -> Dict[str, any]:
        """Detect fuel system characteristics."""
        fuel_system = {
            "injector_size": None,
            "fuel_pump_type": "unknown",
            "fuel_type": FuelType.GASOLINE.value,
            "injector_count": 0,
        }
        
        if not telemetry_data:
            return fuel_system
        
        # Detect fuel type from AFR patterns
        afr = telemetry_data.get("AFR", telemetry_data.get("Lambda", 14.7))
        if afr < 10:
            fuel_system["fuel_type"] = FuelType.NITROMETHANE.value
        elif afr < 12:
            fuel_system["fuel_type"] = FuelType.METHANOL.value
        elif afr > 14:
            fuel_system["fuel_type"] = FuelType.E85.value
        
        # Detect from fuel pressure
        fuel_pressure = telemetry_data.get("Fuel_Pressure", 0)
        if fuel_pressure > 50:
            fuel_system["fuel_pump_type"] = "high_pressure"
        elif fuel_pressure > 30:
            fuel_system["fuel_pump_type"] = "standard"
        else:
            fuel_system["fuel_pump_type"] = "low_pressure"
        
        return fuel_system
    
    def detect_ignition_system(self, telemetry_data: Optional[Dict[str, float]] = None) -> Dict[str, any]:
        """Detect ignition system characteristics."""
        ignition_system = {
            "coil_type": "unknown",
            "spark_plug_type": "unknown",
            "ignition_timing_range": (0, 50),
        }
        
        if not telemetry_data:
            return ignition_system
        
        # Detect from knock patterns
        knock = telemetry_data.get("Knock_Count", 0)
        if knock > 5:
            ignition_system["spark_plug_type"] = "cold_plug"  # More knock = need colder plugs
        
        return ignition_system
    
    def get_recommended_settings(self) -> Dict[str, any]:
        """Get recommended settings based on detected components."""
        recommendations = {}
        
        # Engine-based recommendations
        if self.results.engine.forced_induction == ForcedInductionType.TURBO:
            recommendations["boost_control"] = {
                "enabled": True,
                "max_boost": 20.0,
                "wastegate_duty_cycle": 80.0,
            }
        
        # Sensor-based recommendations
        detected_sensor_names = [s.name for s in self.results.sensors if s.detected]
        if "EGT" in detected_sensor_names:
            recommendations["egt_protection"] = {
                "enabled": True,
                "max_egt": 1600.0,
            }
        
        # Fuel system recommendations
        if self.results.fuel_system.get("fuel_type") == FuelType.E85.value:
            recommendations["flex_fuel"] = {
                "enabled": True,
                "ethanol_content": 85.0,
            }
        
        return recommendations

