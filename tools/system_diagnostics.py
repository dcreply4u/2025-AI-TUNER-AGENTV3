"""
System Diagnostics Utility

Provides comprehensive system health checks and diagnostics for the AI Tuner Agent.
"""

from __future__ import annotations

import json
import logging
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import psutil
except ImportError:
    psutil = None

LOGGER = logging.getLogger(__name__)


class SystemDiagnostics:
    """System diagnostics and health monitoring."""

    def __init__(self) -> None:
        """Initialize diagnostics."""
        self.results: Dict[str, Any] = {}

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all diagnostic checks."""
        self.results = {
            "platform": self.check_platform(),
            "python": self.check_python(),
            "dependencies": self.check_dependencies(),
            "hardware": self.check_hardware(),
            "network": self.check_network(),
            "storage": self.check_storage(),
            "can_bus": self.check_can_bus(),
            "usb_devices": self.check_usb_devices(),
            "system_resources": self.check_system_resources(),
        }
        return self.results

    def check_platform(self) -> Dict[str, Any]:
        """Check platform information."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "platform": platform.platform(),
        }

    def check_python(self) -> Dict[str, Any]:
        """Check Python version and environment."""
        return {
            "version": sys.version,
            "version_info": list(sys.version_info),
            "executable": sys.executable,
            "path": sys.path[:5],  # First 5 entries
        }

    def check_dependencies(self) -> Dict[str, Any]:
        """Check if required dependencies are installed."""
        dependencies = {
            "pyside6": False,
            "pyqtgraph": False,
            "numpy": False,
            "pandas": False,
            "scikit-learn": False,
            "opencv-python": False,
            "pyserial": False,
            "pynmea2": False,
            "python-OBD": False,
            "psutil": False,
        }

        for dep in dependencies:
            try:
                __import__(dep.replace("-", "_"))
                dependencies[dep] = True
            except ImportError:
                pass

        return dependencies

    def check_hardware(self) -> Dict[str, Any]:
        """Check hardware platform and capabilities."""
        try:
            from core import get_hardware_config

            config = get_hardware_config()
            return {
                "platform": config.platform_name,
                "can_channels": config.can_channels,
                "can_bitrate": config.can_bitrate,
                "has_touchscreen": config.has_touchscreen,
                "has_lte": config.has_lte,
                "has_wifi": config.has_wifi,
                "has_bluetooth": config.has_bluetooth,
                "display_size": config.display_size_inches,
            }
        except Exception as e:
            return {"error": str(e)}

    def check_network(self) -> Dict[str, Any]:
        """Check network interfaces."""
        interfaces = {}
        try:
            if psutil:
                net_if_addrs = psutil.net_if_addrs()
                for interface, addrs in net_if_addrs.items():
                    interfaces[interface] = [
                        {
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                        }
                        for addr in addrs
                    ]
        except Exception as e:
            interfaces["error"] = str(e)

        return {"interfaces": interfaces}

    def check_storage(self) -> Dict[str, Any]:
        """Check storage availability."""
        storage = {}
        try:
            if psutil:
                partitions = psutil.disk_usage("/")
                storage = {
                    "total_gb": partitions.total / (1024**3),
                    "used_gb": partitions.used / (1024**3),
                    "free_gb": partitions.free / (1024**3),
                    "percent": partitions.percent,
                }
        except Exception as e:
            storage["error"] = str(e)

        return storage

    def check_can_bus(self) -> Dict[str, Any]:
        """Check CAN bus interfaces."""
        can_status = {}
        try:
            result = subprocess.run(
                ["ip", "link", "show"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                output = result.stdout
                can_interfaces = [line for line in output.split("\n") if "can" in line.lower()]
                can_status["interfaces_found"] = len(can_interfaces)
                can_status["details"] = can_interfaces[:5]  # First 5 lines
            else:
                can_status["error"] = "ip command failed"
        except FileNotFoundError:
            can_status["error"] = "ip command not found"
        except Exception as e:
            can_status["error"] = str(e)

        return can_status

    def check_usb_devices(self) -> Dict[str, Any]:
        """Check USB devices."""
        usb_devices = {}
        try:
            if Path("/dev").exists():
                usb_devices_list = list(Path("/dev").glob("ttyUSB*"))
                usb_devices_list.extend(Path("/dev").glob("ttyACM*"))
                usb_devices["count"] = len(usb_devices_list)
                usb_devices["devices"] = [str(d) for d in usb_devices_list[:10]]
        except Exception as e:
            usb_devices["error"] = str(e)

        return usb_devices

    def check_system_resources(self) -> Dict[str, Any]:
        """Check CPU, memory, and system resources."""
        resources = {}
        try:
            if psutil:
                resources = {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                    "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                    "memory_percent": psutil.virtual_memory().percent,
                }
        except Exception as e:
            resources["error"] = str(e)

        return resources

    def print_report(self) -> None:
        """Print a formatted diagnostic report."""
        print("\n" + "=" * 60)
        print("AI Tuner Agent - System Diagnostics Report")
        print("=" * 60 + "\n")

        for category, data in self.results.items():
            print(f"[{category.upper()}]")
            print(json.dumps(data, indent=2))
            print()

    def save_report(self, filepath: str | Path) -> None:
        """Save diagnostic report to JSON file."""
        path = Path(filepath)
        path.write_text(json.dumps(self.results, indent=2))
        print(f"Diagnostic report saved to: {path}")


def main() -> None:
    """Run diagnostics and print report."""
    diagnostics = SystemDiagnostics()
    diagnostics.run_all_checks()
    diagnostics.print_report()

    # Optionally save to file
    report_file = Path("system_diagnostics_report.json")
    diagnostics.save_report(report_file)


if __name__ == "__main__":
    main()
