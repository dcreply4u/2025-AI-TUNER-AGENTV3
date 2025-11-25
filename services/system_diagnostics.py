"""
System Diagnostics Service

Comprehensive system health check for all components and connections.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class DiagnosticStatus(Enum):
    """Diagnostic status levels."""

    UNKNOWN = "unknown"
    CHECKING = "checking"
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    NOT_AVAILABLE = "not_available"


@dataclass
class ComponentDiagnostic:
    """Diagnostic result for a component."""

    name: str
    status: DiagnosticStatus
    message: str
    details: Dict = field(default_factory=dict)
    last_check: float = 0.0
    check_duration: float = 0.0


class SystemDiagnostics:
    """Comprehensive system diagnostics."""

    def __init__(self) -> None:
        """Initialize diagnostics service."""
        self.components: Dict[str, ComponentDiagnostic] = {}
        self.check_callbacks: Dict[str, Callable[[], ComponentDiagnostic]] = {}
        self.running = False

    def register_component(self, name: str, check_callback: Callable[[], ComponentDiagnostic]) -> None:
        """Register a component for diagnostics."""
        self.check_callbacks[name] = check_callback
        self.components[name] = ComponentDiagnostic(
            name=name,
            status=DiagnosticStatus.UNKNOWN,
            message="Not checked yet",
        )

    def check_all(self) -> Dict[str, ComponentDiagnostic]:
        """
        Check all registered components.

        Returns:
            Dictionary of component diagnostics
        """
        self.running = True
        results = {}

        for name, callback in self.check_callbacks.items():
            try:
                start_time = time.time()
                result = callback()
                result.check_duration = time.time() - start_time
                result.last_check = time.time()
                self.components[name] = result
                results[name] = result
            except Exception as e:
                LOGGER.error("Error checking component %s: %s", name, e)
                self.components[name] = ComponentDiagnostic(
                    name=name,
                    status=DiagnosticStatus.ERROR,
                    message=f"Check failed: {str(e)}",
                    last_check=time.time(),
                )
                results[name] = self.components[name]

        self.running = False
        return results

    def check_component(self, name: str) -> Optional[ComponentDiagnostic]:
        """Check a specific component."""
        if name not in self.check_callbacks:
            return None

        try:
            start_time = time.time()
            result = self.check_callbacks[name]()
            result.check_duration = time.time() - start_time
            result.last_check = time.time()
            self.components[name] = result
            return result
        except Exception as e:
            LOGGER.error("Error checking component %s: %s", name, e)
            result = ComponentDiagnostic(
                name=name,
                status=DiagnosticStatus.ERROR,
                message=f"Check failed: {str(e)}",
                last_check=time.time(),
            )
            self.components[name] = result
            return result

    def get_overall_status(self) -> DiagnosticStatus:
        """Get overall system status."""
        if not self.components:
            return DiagnosticStatus.UNKNOWN

        statuses = [comp.status for comp in self.components.values()]
        if DiagnosticStatus.ERROR in statuses:
            return DiagnosticStatus.ERROR
        if DiagnosticStatus.WARNING in statuses:
            return DiagnosticStatus.WARNING
        if all(s == DiagnosticStatus.OK for s in statuses):
            return DiagnosticStatus.OK
        return DiagnosticStatus.UNKNOWN

    def get_summary(self) -> Dict:
        """Get diagnostic summary."""
        total = len(self.components)
        ok = sum(1 for c in self.components.values() if c.status == DiagnosticStatus.OK)
        warning = sum(1 for c in self.components.values() if c.status == DiagnosticStatus.WARNING)
        error = sum(1 for c in self.components.values() if c.status == DiagnosticStatus.ERROR)
        not_available = sum(1 for c in self.components.values() if c.status == DiagnosticStatus.NOT_AVAILABLE)

        return {
            "total": total,
            "ok": ok,
            "warning": warning,
            "error": error,
            "not_available": not_available,
            "overall_status": self.get_overall_status().value,
        }


# Pre-defined check functions for common components

def check_can_bus() -> ComponentDiagnostic:
    """Check CAN bus connectivity."""
    try:
        import can

        # Try to connect to can0
        try:
            bus = can.interface.Bus(channel="can0", bustype="socketcan")
            bus.shutdown()
            return ComponentDiagnostic(
                name="CAN Bus",
                status=DiagnosticStatus.OK,
                message="CAN bus (can0) is available",
                details={"channel": "can0"},
            )
        except Exception:
            return ComponentDiagnostic(
                name="CAN Bus",
                status=DiagnosticStatus.NOT_AVAILABLE,
                message="CAN bus (can0) not available",
            )
    except ImportError:
        return ComponentDiagnostic(
            name="CAN Bus",
            status=DiagnosticStatus.NOT_AVAILABLE,
            message="python-can not installed",
        )


def check_gps() -> ComponentDiagnostic:
    """Check GPS interface."""
    try:
        from interfaces.gps_interface import GPSInterface

        try:
            gps = GPSInterface()
            fix = gps.read_fix()
            gps.close()
            if fix:
                return ComponentDiagnostic(
                    name="GPS",
                    status=DiagnosticStatus.OK,
                    message=f"GPS connected (lat: {fix.latitude:.4f}, lon: {fix.longitude:.4f})",
                    details={"latitude": fix.latitude, "longitude": fix.longitude},
                )
            return ComponentDiagnostic(
                name="GPS",
                status=DiagnosticStatus.WARNING,
                message="GPS connected but no fix",
            )
        except Exception as e:
            return ComponentDiagnostic(
                name="GPS",
                status=DiagnosticStatus.NOT_AVAILABLE,
                message=f"GPS not available: {str(e)}",
            )
    except ImportError:
        return ComponentDiagnostic(
            name="GPS",
            status=DiagnosticStatus.NOT_AVAILABLE,
            message="GPS interface not available",
        )


def check_cameras() -> ComponentDiagnostic:
    """Check camera availability."""
    try:
        import cv2

        available_cameras = []
        for i in range(4):  # Check first 4 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()

        if available_cameras:
            return ComponentDiagnostic(
                name="Cameras",
                status=DiagnosticStatus.OK,
                message=f"Found {len(available_cameras)} camera(s): {available_cameras}",
                details={"indices": available_cameras},
            )
        return ComponentDiagnostic(
            name="Cameras",
            status=DiagnosticStatus.NOT_AVAILABLE,
            message="No cameras detected",
        )
    except ImportError:
        return ComponentDiagnostic(
            name="Cameras",
            status=DiagnosticStatus.NOT_AVAILABLE,
            message="OpenCV not installed",
        )


def check_usb_storage() -> ComponentDiagnostic:
    """Check USB storage availability."""
    try:
        from services.usb_manager import USBManager

        usb_manager = USBManager()
        devices = usb_manager.scan_for_devices()

        if devices:
            active = usb_manager.active_device
            if active:
                return ComponentDiagnostic(
                    name="USB Storage",
                    status=DiagnosticStatus.OK,
                    message=f"USB device active: {active.label} ({active.size_gb:.1f} GB)",
                    details={"device": active.label, "size_gb": active.size_gb},
                )
            return ComponentDiagnostic(
                name="USB Storage",
                status=DiagnosticStatus.WARNING,
                message=f"{len(devices)} USB device(s) detected but not configured",
                details={"devices": len(devices)},
            )
        return ComponentDiagnostic(
            name="USB Storage",
            status=DiagnosticStatus.WARNING,
            message="No USB storage detected (using local disk)",
        )
    except Exception as e:
        return ComponentDiagnostic(
            name="USB Storage",
            status=DiagnosticStatus.WARNING,
            message=f"USB check failed: {str(e)}",
        )


def check_network() -> ComponentDiagnostic:
    """Check network connectivity."""
    try:
        import socket

        # Check internet connectivity
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return ComponentDiagnostic(
                name="Network",
                status=DiagnosticStatus.OK,
                message="Network connectivity OK",
            )
        except OSError:
            return ComponentDiagnostic(
                name="Network",
                status=DiagnosticStatus.WARNING,
                message="No internet connectivity",
            )
    except Exception as e:
        return ComponentDiagnostic(
            name="Network",
            status=DiagnosticStatus.ERROR,
            message=f"Network check failed: {str(e)}",
        )


def check_obd_interface() -> ComponentDiagnostic:
    """Check OBD interface."""
    try:
        from interfaces.obd_interface import OBDInterface

        obd = OBDInterface()
        # Try to connect (non-blocking check)
        return ComponentDiagnostic(
            name="OBD Interface",
            status=DiagnosticStatus.OK,
            message="OBD interface available",
        )
    except Exception as e:
        return ComponentDiagnostic(
            name="OBD Interface",
            status=DiagnosticStatus.NOT_AVAILABLE,
            message=f"OBD interface not available: {str(e)}",
        )


def check_voice_output() -> ComponentDiagnostic:
    """Check voice output."""
    try:
        from interfaces.voice_output import VoiceOutput

        voice = VoiceOutput()
        if voice.enabled:
            return ComponentDiagnostic(
                name="Voice Output",
                status=DiagnosticStatus.OK,
                message="Voice output available",
            )
        return ComponentDiagnostic(
            name="Voice Output",
            status=DiagnosticStatus.NOT_AVAILABLE,
            message="Voice output disabled",
        )
    except Exception as e:
        return ComponentDiagnostic(
            name="Voice Output",
            status=DiagnosticStatus.NOT_AVAILABLE,
            message=f"Voice output not available: {str(e)}",
        )


__all__ = [
    "SystemDiagnostics",
    "ComponentDiagnostic",
    "DiagnosticStatus",
    "check_can_bus",
    "check_gps",
    "check_cameras",
    "check_usb_storage",
    "check_network",
    "check_obd_interface",
    "check_voice_output",
]

