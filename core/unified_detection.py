"""
Unified Detection Interface

Integrates intelligent detection engine with all existing detectors:
- Hardware detection
- ECU detection
- Sensor detection
- Adapter detection
- Camera detection
- Global auto-detection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.adaptive_learning import AdaptiveLearner
from core.intelligent_detector import (
    DetectionContext,
    DetectionMethod,
    DetectionResult,
    DetectionSignature,
    IntelligentDetector,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class UnifiedDetectionResult:
    """Unified detection result combining all detectors."""

    hardware_platform: Optional[str] = None
    detected_ecus: List[Dict[str, Any]] = field(default_factory=list)
    detected_sensors: List[Dict[str, Any]] = field(default_factory=list)
    detected_adapters: List[Dict[str, Any]] = field(default_factory=list)
    detected_cameras: List[Dict[str, Any]] = field(default_factory=list)
    overall_confidence: float = 0.0
    detection_method: str = "ensemble"
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedDetector:
    """Unified detection interface for all detection modules."""

    def __init__(self, learning_enabled: bool = True):
        """
        Initialize unified detector.

        Args:
            learning_enabled: Enable adaptive learning
        """
        self.learning_enabled = learning_enabled

        # Intelligent detector
        self.intelligent_detector = IntelligentDetector(learning_enabled=learning_enabled)

        # Adaptive learner
        self.learner = AdaptiveLearner() if learning_enabled else None

        # Detection modules (lazy import)
        self._hardware_detector = None
        self._ecu_detector = None
        self._sensor_detector = None
        self._adapter_detector = None
        self._camera_detector = None
        self._global_detector = None

    def detect_all(
        self,
        include_hardware: bool = True,
        include_ecu: bool = True,
        include_sensors: bool = True,
        include_adapters: bool = True,
        include_cameras: bool = False,
        use_intelligent: bool = True,
    ) -> UnifiedDetectionResult:
        """
        Perform comprehensive detection of all components.

        Args:
            include_hardware: Detect hardware platform
            include_ecu: Detect ECUs
            include_sensors: Detect sensors
            include_adapters: Detect adapters
            include_cameras: Detect cameras
            use_intelligent: Use intelligent detection engine

        Returns:
            Unified detection results
        """
        result = UnifiedDetectionResult()

        # Detect hardware platform
        if include_hardware:
            try:
                from core.hardware_platform import HardwareDetector

                if self._hardware_detector is None:
                    self._hardware_detector = HardwareDetector

                config = self._hardware_detector.detect()
                result.hardware_platform = config.platform_name
                result.metadata["hardware_config"] = {
                    "platform": config.platform_name,
                    "can_channels": config.can_channels,
                    "gpio_available": config.gpio_available,
                }
            except Exception as e:
                LOGGER.warning("Hardware detection failed: %s", e)

        # Detect ECUs
        if include_ecu:
            try:
                ecu_results = self._detect_ecus(use_intelligent)
                result.detected_ecus = ecu_results
            except Exception as e:
                LOGGER.warning("ECU detection failed: %s", e)

        # Detect sensors
        if include_sensors:
            try:
                sensor_results = self._detect_sensors(use_intelligent)
                result.detected_sensors = sensor_results
            except Exception as e:
                LOGGER.warning("Sensor detection failed: %s", e)

        # Detect adapters
        if include_adapters:
            try:
                adapter_results = self._detect_adapters(use_intelligent)
                result.detected_adapters = adapter_results
            except Exception as e:
                LOGGER.warning("Adapter detection failed: %s", e)

        # Detect cameras
        if include_cameras:
            try:
                camera_results = self._detect_cameras()
                result.detected_cameras = camera_results
            except Exception as e:
                LOGGER.warning("Camera detection failed: %s", e)

        # Calculate overall confidence
        all_confidences = []
        for ecu in result.detected_ecus:
            if "confidence" in ecu:
                all_confidences.append(ecu["confidence"])
        for sensor in result.detected_sensors:
            if "confidence" in sensor:
                all_confidences.append(sensor["confidence"])
        for adapter in result.detected_adapters:
            if "confidence" in adapter:
                all_confidences.append(adapter["confidence"])

        result.overall_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        return result

    def _detect_ecus(self, use_intelligent: bool) -> List[Dict[str, Any]]:
        """Detect ECUs using intelligent detection if enabled."""
        results = []

        try:
            from services.can_vendor_detector import CANVendorDetector
            from services.multi_ecu_detector import MultiECUDetector

            # Use multi-ECU detector
            if self._ecu_detector is None:
                self._ecu_detector = MultiECUDetector()

            detected_ecus = self._ecu_detector.detect_all_ecus(sample_time=5.0)

            for ecu in detected_ecus:
                result = {
                    "name": ecu.vendor.value if hasattr(ecu.vendor, "value") else str(ecu.vendor),
                    "type": ecu.ecu_type.value if hasattr(ecu.ecu_type, "value") else str(ecu.ecu_type),
                    "confidence": ecu.confidence,
                    "can_ids": list(ecu.can_ids),
                    "is_primary": ecu.is_primary,
                    "metadata": ecu.metadata,
                }
                results.append(result)

                # Register with intelligent detector if enabled
                if use_intelligent:
                    signature = DetectionSignature(
                        name=result["name"],
                        signature_type="CAN_ID",
                        primary_signals={"can_ids": list(ecu.can_ids)},
                        metadata={"ecu_type": result["type"]},
                    )
                    self.intelligent_detector.register_signature(signature)

        except ImportError:
            LOGGER.warning("ECU detection modules not available")
        except Exception as e:
            LOGGER.error("ECU detection error: %s", e, exc_info=True)

        return results

    def _detect_sensors(self, use_intelligent: bool) -> List[Dict[str, Any]]:
        """Detect sensors."""
        results = []

        try:
            from services.global_auto_detection import GlobalAutoDetector

            if self._sensor_detector is None:
                self._sensor_detector = GlobalAutoDetector()

            detection_results = self._sensor_detector.detect_all()

            for sensor in detection_results.sensors:
                result = {
                    "name": sensor.name,
                    "type": sensor.sensor_type,
                    "channel": sensor.channel,
                    "confidence": sensor.confidence,
                    "detected": sensor.detected,
                }
                results.append(result)

        except ImportError:
            LOGGER.warning("Sensor detection modules not available")
        except Exception as e:
            LOGGER.error("Sensor detection error: %s", e, exc_info=True)

        return results

    def _detect_adapters(self, use_intelligent: bool) -> List[Dict[str, Any]]:
        """Detect adapters."""
        results = []

        try:
            from interfaces.obd2_adapter_detector import OBD2AdapterDetector
            from interfaces.serial_adapter_detector import SerialAdapterDetector

            # Detect OBD2 adapters
            obd2_detector = OBD2AdapterDetector()
            obd2_adapters = obd2_detector.detect_all()

            for adapter in obd2_adapters:
                result = {
                    "name": adapter.name,
                    "type": "OBD2",
                    "connection": adapter.connection_type.value if hasattr(adapter.connection_type, "value") else str(adapter.connection_type),
                    "port": adapter.port,
                    "confidence": 0.8,  # Default confidence for detected adapters
                }
                results.append(result)

            # Detect serial adapters
            serial_detector = SerialAdapterDetector()
            serial_adapters = serial_detector.detect_all()

            for adapter in serial_adapters:
                result = {
                    "name": adapter.name,
                    "type": "Serial",
                    "connection": adapter.connection_type.value if hasattr(adapter.connection_type, "value") else str(adapter.connection_type),
                    "port": adapter.port,
                    "confidence": 0.8,
                }
                results.append(result)

        except ImportError:
            LOGGER.warning("Adapter detection modules not available")
        except Exception as e:
            LOGGER.error("Adapter detection error: %s", e, exc_info=True)

        return results

    def _detect_cameras(self) -> List[Dict[str, Any]]:
        """Detect cameras."""
        results = []

        try:
            from interfaces.camera_interface import CameraAutoDetector

            if self._camera_detector is None:
                self._camera_detector = CameraAutoDetector

            cameras = self._camera_detector.detect_all_cameras(include_network=False)

            for camera in cameras:
                result = {
                    "name": camera.name,
                    "type": camera.camera_type,
                    "index": camera.index,
                    "resolution": camera.resolution,
                    "fps": camera.fps,
                }
                results.append(result)

        except ImportError:
            LOGGER.warning("Camera detection modules not available")
        except Exception as e:
            LOGGER.error("Camera detection error: %s", e, exc_info=True)

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        stats = {
            "intelligent_detector": self.intelligent_detector.get_stats(),
        }

        if self.learner:
            stats["adaptive_learner"] = self.learner.get_statistics()

        return stats


__all__ = ["UnifiedDetector", "UnifiedDetectionResult"]



