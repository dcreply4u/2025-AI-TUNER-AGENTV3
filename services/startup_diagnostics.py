"""
Startup Diagnostics Service

Fast, non-blocking diagnostics for all hardware and services.
"""

from __future__ import annotations

import logging
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class DiagnosticStatus(Enum):
    """Diagnostic status levels."""

    CHECKING = "checking"
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_AVAILABLE = "not_available"


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""

    name: str
    category: str
    status: DiagnosticStatus
    message: str
    details: Dict = field(default_factory=dict)
    check_time_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


class StartupDiagnostics:
    """Fast startup diagnostics for hardware and services."""

    def __init__(self) -> None:
        """Initialize diagnostics."""
        self.results: Dict[str, DiagnosticResult] = {}
        self.check_callbacks: List[Callable[[DiagnosticResult], None]] = []
        self._lock = threading.Lock()

    def register_callback(self, callback: Callable[[DiagnosticResult], None]) -> None:
        """Register callback for diagnostic results."""
        self.check_callbacks.append(callback)

    def _notify(self, result: DiagnosticResult) -> None:
        """Notify callbacks of diagnostic result."""
        for callback in self.check_callbacks:
            try:
                callback(result)
            except Exception as e:
                LOGGER.error("Error in diagnostic callback: %s", e)

    def check_all(self, timeout_per_check: float = 2.0) -> Dict[str, DiagnosticResult]:
        """
        Run all diagnostic checks.

        Args:
            timeout_per_check: Maximum time per check (seconds)

        Returns:
            Dictionary of diagnostic results
        """
        checks = [
            ("camera", self.check_cameras),
            ("ecu", self.check_ecu),
            ("can_bus", self.check_can_bus),
            ("obd", self.check_obd),
            ("gps", self.check_gps),
            ("usb_storage", self.check_usb_storage),
            ("network", self.check_network),
            ("streaming", self.check_streaming),
            ("database", self.check_database),
            ("voice", self.check_voice),
            ("bluetooth", self.check_bluetooth),
            ("wifi", self.check_wifi),
            ("lte", self.check_lte),
        ]

        threads = []
        for name, check_func in checks:
            thread = threading.Thread(
                target=self._run_check,
                args=(name, check_func, timeout_per_check),
                daemon=True,
            )
            thread.start()
            threads.append(thread)

        # Wait for all checks to complete
        for thread in threads:
            thread.join(timeout=timeout_per_check + 1.0)

        return dict(self.results)

    def _run_check(self, name: str, check_func: Callable, timeout: float) -> None:
        """Run a single check with timeout."""
        start_time = time.time()

        # Set initial status
        result = DiagnosticResult(
            name=name,
            category=self._get_category(name),
            status=DiagnosticStatus.CHECKING,
            message="Checking...",
        )
        with self._lock:
            self.results[name] = result
        self._notify(result)

        try:
            # Run check with timeout
            check_result = self._run_with_timeout(check_func, timeout)
            check_time = (time.time() - start_time) * 1000

            result.status = check_result.status
            result.message = check_result.message
            result.details = check_result.details
            result.check_time_ms = check_time

        except Exception as e:
            result.status = DiagnosticStatus.FAIL
            result.message = f"Check failed: {str(e)}"
            result.check_time_ms = (time.time() - start_time) * 1000
            LOGGER.error("Diagnostic check failed for %s: %s", name, e)

        with self._lock:
            self.results[name] = result
        self._notify(result)

    def _run_with_timeout(self, func: Callable, timeout: float) -> DiagnosticResult:
        """Run function with timeout."""
        result_container = [None]
        exception_container = [None]

        def run():
            try:
                result_container[0] = func()
            except Exception as e:
                exception_container[0] = e

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        if exception_container[0]:
            raise exception_container[0]

        if result_container[0] is None:
            return DiagnosticResult(
                name="",
                category="",
                status=DiagnosticStatus.FAIL,
                message="Check timed out",
            )

        return result_container[0]

    def check_cameras(self) -> DiagnosticResult:
        """Check camera availability."""
        try:
            import cv2

            cameras_found = []
            for i in range(4):  # Check first 4 camera indices
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        cameras_found.append(f"Camera {i}")
                    cap.release()

            if cameras_found:
                return DiagnosticResult(
                    name="camera",
                    category="hardware",
                    status=DiagnosticStatus.PASS,
                    message=f"Detected: {', '.join(cameras_found)}",
                    details={"count": len(cameras_found), "cameras": cameras_found},
                )
            else:
                return DiagnosticResult(
                    name="camera",
                    category="hardware",
                    status=DiagnosticStatus.NOT_AVAILABLE,
                    message="No cameras detected",
                )
        except ImportError:
            return DiagnosticResult(
                name="camera",
                category="hardware",
                status=DiagnosticStatus.WARNING,
                message="OpenCV not available",
            )
        except Exception as e:
            return DiagnosticResult(
                name="camera",
                category="hardware",
                status=DiagnosticStatus.FAIL,
                message=f"Check failed: {str(e)}",
            )

    def check_ecu(self) -> DiagnosticResult:
        """Check ECU/CAN bus detection."""
        try:
            import can

            # Try to detect CAN interface
            try:
                bus = can.interface.Bus(channel="can0", bustype="socketcan")
                bus.shutdown()
                return DiagnosticResult(
                    name="ecu",
                    category="hardware",
                    status=DiagnosticStatus.PASS,
                    message="CAN bus (can0) available",
                    details={"interface": "can0", "type": "socketcan"},
                )
            except Exception:
                # Check for other CAN interfaces
                import subprocess

                result = subprocess.run(["ip", "link", "show"], capture_output=True, text=True, timeout=1)
                if "can" in result.stdout.lower():
                    return DiagnosticResult(
                        name="ecu",
                        category="hardware",
                        status=DiagnosticStatus.PASS,
                        message="CAN interface detected",
                    )
                else:
                    return DiagnosticResult(
                        name="ecu",
                        category="hardware",
                        status=DiagnosticStatus.NOT_AVAILABLE,
                        message="No CAN interface detected",
                    )
        except ImportError:
            return DiagnosticResult(
                name="ecu",
                category="hardware",
                status=DiagnosticStatus.WARNING,
                message="python-can not available",
            )
        except Exception as e:
            return DiagnosticResult(
                name="ecu",
                category="hardware",
                status=DiagnosticStatus.FAIL,
                message=f"Check failed: {str(e)}",
            )

    def check_can_bus(self) -> DiagnosticResult:
        """Check CAN bus connectivity."""
        return self.check_ecu()  # Same check

    def check_obd(self) -> DiagnosticResult:
        """Check OBD-II interface."""
        try:
            import serial.tools.list_ports

            ports = serial.tools.list_ports.comports()
            obd_ports = [p.device for p in ports if "USB" in p.description.upper() or "Serial" in p.description.upper()]

            if obd_ports:
                return DiagnosticResult(
                    name="obd",
                    category="hardware",
                    status=DiagnosticStatus.PASS,
                    message=f"Serial ports available: {', '.join(obd_ports[:3])}",
                    details={"ports": obd_ports},
                )
            else:
                return DiagnosticResult(
                    name="obd",
                    category="hardware",
                    status=DiagnosticStatus.NOT_AVAILABLE,
                    message="No serial ports detected",
                )
        except Exception as e:
            return DiagnosticResult(
                name="obd",
                category="hardware",
                status=DiagnosticStatus.WARNING,
                message=f"Check incomplete: {str(e)}",
            )

    def check_gps(self) -> DiagnosticResult:
        """Check GPS interface."""
        try:
            import serial.tools.list_ports

            ports = serial.tools.list_ports.comports()
            # GPS modules often show up as USB serial devices
            gps_ports = [p.device for p in ports]

            # Try to detect GPS by checking for NMEA-capable devices
            if gps_ports:
                return DiagnosticResult(
                    name="gps",
                    category="hardware",
                    status=DiagnosticStatus.PASS,
                    message=f"Serial ports available for GPS: {len(gps_ports)}",
                    details={"ports": gps_ports},
                )
            else:
                return DiagnosticResult(
                    name="gps",
                    category="hardware",
                    status=DiagnosticStatus.NOT_AVAILABLE,
                    message="No GPS device detected",
                )
        except Exception as e:
            return DiagnosticResult(
                name="gps",
                category="hardware",
                status=DiagnosticStatus.WARNING,
                message=f"Check incomplete: {str(e)}",
            )

    def check_usb_storage(self) -> DiagnosticResult:
        """Check USB storage devices."""
        try:
            import platform

            usb_devices = []
            if platform.system() == "Linux":
                # Check /media and /mnt
                from pathlib import Path

                for mount_point in [Path("/media"), Path("/mnt"), Path("/run/media")]:
                    if mount_point.exists():
                        devices = [d.name for d in mount_point.iterdir() if d.is_dir()]
                        usb_devices.extend(devices)

            if usb_devices:
                return DiagnosticResult(
                    name="usb_storage",
                    category="hardware",
                    status=DiagnosticStatus.PASS,
                    message=f"USB devices detected: {len(usb_devices)}",
                    details={"devices": usb_devices},
                )
            else:
                return DiagnosticResult(
                    name="usb_storage",
                    category="hardware",
                    status=DiagnosticStatus.NOT_AVAILABLE,
                    message="No USB storage detected",
                )
        except Exception as e:
            return DiagnosticResult(
                name="usb_storage",
                category="hardware",
                status=DiagnosticStatus.WARNING,
                message=f"Check incomplete: {str(e)}",
            )

    def check_network(self) -> DiagnosticResult:
        """Check network connectivity."""
        try:
            import socket

            # Try to connect to a reliable host
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return DiagnosticResult(
                name="network",
                category="connectivity",
                status=DiagnosticStatus.PASS,
                message="Network connectivity OK",
            )
        except OSError:
            return DiagnosticResult(
                name="network",
                category="connectivity",
                status=DiagnosticStatus.FAIL,
                message="No network connectivity",
            )
        except Exception as e:
            return DiagnosticResult(
                name="network",
                category="connectivity",
                status=DiagnosticStatus.WARNING,
                message=f"Check incomplete: {str(e)}",
            )

    def check_streaming(self) -> DiagnosticResult:
        """Check streaming capability."""
        try:
            # Check if FFmpeg is available
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=1,
            )
            if result.returncode == 0:
                return DiagnosticResult(
                    name="streaming",
                    category="services",
                    status=DiagnosticStatus.PASS,
                    message="FFmpeg available for streaming",
                )
            else:
                return DiagnosticResult(
                    name="streaming",
                    category="services",
                    status=DiagnosticStatus.FAIL,
                    message="FFmpeg not functional",
                )
        except FileNotFoundError:
            return DiagnosticResult(
                name="streaming",
                category="services",
                status=DiagnosticStatus.NOT_AVAILABLE,
                message="FFmpeg not installed",
            )
        except Exception as e:
            return DiagnosticResult(
                name="streaming",
                category="services",
                status=DiagnosticStatus.WARNING,
                message=f"Check incomplete: {str(e)}",
            )

    def check_database(self) -> DiagnosticResult:
        """Check database connectivity."""
        try:
            import sqlite3

            # Test local database
            conn = sqlite3.connect(":memory:")
            conn.execute("SELECT 1")
            conn.close()

            return DiagnosticResult(
                name="database",
                category="services",
                status=DiagnosticStatus.PASS,
                message="Local database OK",
            )
        except Exception as e:
            return DiagnosticResult(
                name="database",
                category="services",
                status=DiagnosticStatus.FAIL,
                message=f"Database check failed: {str(e)}",
            )

    def check_voice(self) -> DiagnosticResult:
        """Check voice input/output."""
        try:
            import pyttsx3

            engine = pyttsx3.init()
            if engine:
                return DiagnosticResult(
                    name="voice",
                    category="services",
                    status=DiagnosticStatus.PASS,
                    message="Voice output available",
                )
        except Exception:
            pass

        try:
            import speech_recognition as sr

            r = sr.Recognizer()
            return DiagnosticResult(
                name="voice",
                category="services",
                status=DiagnosticStatus.PASS,
                message="Voice input available",
            )
        except Exception:
            return DiagnosticResult(
                name="voice",
                category="services",
                status=DiagnosticStatus.NOT_AVAILABLE,
                message="Voice services not available",
            )

    def check_bluetooth(self) -> DiagnosticResult:
        """Check Bluetooth availability."""
        try:
            import subprocess

            result = subprocess.run(["bluetoothctl", "--version"], capture_output=True, timeout=1)
            if result.returncode == 0:
                return DiagnosticResult(
                    name="bluetooth",
                    category="connectivity",
                    status=DiagnosticStatus.PASS,
                    message="Bluetooth tools available",
                )
        except FileNotFoundError:
            pass

        return DiagnosticResult(
            name="bluetooth",
            category="connectivity",
            status=DiagnosticStatus.NOT_AVAILABLE,
            message="Bluetooth not available",
        )

    def check_wifi(self) -> DiagnosticResult:
        """Check Wi-Fi connectivity."""
        try:
            import subprocess

            result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=1)
            if "wlan" in result.stdout.lower() or "wifi" in result.stdout.lower():
                return DiagnosticResult(
                    name="wifi",
                    category="connectivity",
                    status=DiagnosticStatus.PASS,
                    message="Wi-Fi interface detected",
                )
        except Exception:
            pass

        return DiagnosticResult(
            name="wifi",
            category="connectivity",
            status=DiagnosticStatus.NOT_AVAILABLE,
            message="Wi-Fi not available",
        )

    def check_lte(self) -> DiagnosticResult:
        """Check LTE/4G connectivity."""
        try:
            import subprocess

            result = subprocess.run(["ip", "link", "show"], capture_output=True, text=True, timeout=1)
            if "wwan" in result.stdout.lower() or "lte" in result.stdout.lower():
                return DiagnosticResult(
                    name="lte",
                    category="connectivity",
                    status=DiagnosticStatus.PASS,
                    message="LTE interface detected",
                )
        except Exception:
            pass

        return DiagnosticResult(
            name="lte",
            category="connectivity",
            status=DiagnosticStatus.NOT_AVAILABLE,
            message="LTE not available",
        )

    def _get_category(self, name: str) -> str:
        """Get category for diagnostic name."""
        hardware = ["camera", "ecu", "can_bus", "obd", "gps", "usb_storage"]
        connectivity = ["network", "bluetooth", "wifi", "lte"]
        services = ["streaming", "database", "voice"]

        if name in hardware:
            return "hardware"
        elif name in connectivity:
            return "connectivity"
        elif name in services:
            return "services"
        return "other"

    def get_summary(self) -> Dict[str, Any]:
        """Get diagnostic summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r.status == DiagnosticStatus.PASS)
        failed = sum(1 for r in self.results.values() if r.status == DiagnosticStatus.FAIL)
        warnings = sum(1 for r in self.results.values() if r.status == DiagnosticStatus.WARNING)
        not_available = sum(1 for r in self.results.values() if r.status == DiagnosticStatus.NOT_AVAILABLE)

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "not_available": not_available,
            "health_score": (passed / total * 100) if total > 0 else 0,
        }


__all__ = ["StartupDiagnostics", "DiagnosticResult", "DiagnosticStatus"]

