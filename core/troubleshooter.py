"""
Troubleshooting and Diagnostic System

Provides comprehensive diagnostic tools for:
- System health checks
- Component status verification
- Performance analysis
- Error pattern detection
- Configuration validation
- Network diagnostics
- Hardware detection
"""

from __future__ import annotations

import importlib
import logging
import os
import platform
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from core.logging_config import get_logger

LOGGER = get_logger(__name__)


class DiagnosticLevel(Enum):
    """Diagnostic check levels."""
    QUICK = "quick"  # Fast checks only
    STANDARD = "standard"  # Standard checks
    COMPREHENSIVE = "comprehensive"  # All checks including slow ones


class CheckStatus(Enum):
    """Status of a diagnostic check."""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    SKIPPED = "skipped"


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""
    name: str
    status: CheckStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class SystemDiagnostics:
    """Complete system diagnostics."""
    timestamp: float = field(default_factory=time.time)
    platform: Dict[str, str] = field(default_factory=dict)
    python_version: str = ""
    checks: List[DiagnosticResult] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)


class Troubleshooter:
    """Troubleshooting and diagnostic system."""
    
    def __init__(self) -> None:
        """Initialize troubleshooter."""
        self.logger = get_logger(__name__)
        self.results: List[DiagnosticResult] = []
    
    def run_diagnostics(self, level: DiagnosticLevel = DiagnosticLevel.STANDARD) -> SystemDiagnostics:
        """
        Run comprehensive system diagnostics.
        
        Args:
            level: Diagnostic level to run
            
        Returns:
            SystemDiagnostics with all results
        """
        self.logger.info(f"Running diagnostics (level: {level.value})...")
        start_time = time.time()
        
        diagnostics = SystemDiagnostics()
        diagnostics.platform = self._get_platform_info()
        diagnostics.python_version = sys.version
        
        # Run checks
        checks = [
            self._check_python_version,
            self._check_dependencies,
            self._check_file_permissions,
            self._check_disk_space,
            self._check_memory,
            self._check_cpu,
            self._check_network,
            self._check_configuration,
            self._check_log_files,
        ]
        
        if level == DiagnosticLevel.COMPREHENSIVE:
            checks.extend([
                self._check_hardware_interfaces,
                self._check_database_connectivity,
                self._check_camera_availability,
            ])
        
        for check_func in checks:
            try:
                result = check_func()
                if result:
                    diagnostics.checks.append(result)
            except Exception as e:
                self.logger.error(f"Diagnostic check failed: {check_func.__name__}: {e}")
                diagnostics.checks.append(DiagnosticResult(
                    name=check_func.__name__,
                    status=CheckStatus.FAIL,
                    message=f"Check failed: {e}",
                ))
        
        # Calculate summary
        diagnostics.summary = {
            'total': len(diagnostics.checks),
            'passed': sum(1 for c in diagnostics.checks if c.status == CheckStatus.PASS),
            'warnings': sum(1 for c in diagnostics.checks if c.status == CheckStatus.WARNING),
            'failed': sum(1 for c in diagnostics.checks if c.status == CheckStatus.FAIL),
            'skipped': sum(1 for c in diagnostics.checks if c.status == CheckStatus.SKIPPED),
        }
        
        elapsed = (time.time() - start_time) * 1000
        self.logger.info(f"Diagnostics complete in {elapsed:.2f}ms: {diagnostics.summary}")
        
        return diagnostics
    
    def _get_platform_info(self) -> Dict[str, str]:
        """Get platform information."""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture()[0],
        }
    
    def _check_python_version(self) -> DiagnosticResult:
        """Check Python version."""
        start = time.time()
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            status = CheckStatus.FAIL
            message = f"Python {version.major}.{version.minor} is too old. Requires Python 3.8+"
        elif version.major == 3 and version.minor < 10:
            status = CheckStatus.WARNING
            message = f"Python {version.major}.{version.minor} is supported but 3.10+ is recommended"
        else:
            status = CheckStatus.PASS
            message = f"Python {version.major}.{version.minor}.{version.micro} is compatible"
        
        return DiagnosticResult(
            name="python_version",
            status=status,
            message=message,
            details={'version': f"{version.major}.{version.minor}.{version.micro}"},
            duration_ms=(time.time() - start) * 1000,
        )
    
    def _check_dependencies(self) -> DiagnosticResult:
        """Check critical dependencies."""
        start = time.time()
        required = {
            'PySide6': 'PySide6',
            'numpy': 'numpy',
            'pandas': 'pandas',
        }
        optional = {
            'cv2': 'opencv-python',
            'psutil': 'psutil',
            'pyserial': 'pyserial',
        }
        
        missing_required = []
        missing_optional = []
        
        for module_name, package_name in required.items():
            try:
                importlib.import_module(module_name)
            except ImportError:
                missing_required.append(package_name)
        
        for module_name, package_name in optional.items():
            try:
                importlib.import_module(module_name)
            except ImportError:
                missing_optional.append(package_name)
        
        if missing_required:
            status = CheckStatus.FAIL
            message = f"Missing required dependencies: {', '.join(missing_required)}"
        elif missing_optional:
            status = CheckStatus.WARNING
            message = f"Missing optional dependencies: {', '.join(missing_optional)}"
        else:
            status = CheckStatus.PASS
            message = "All dependencies available"
        
        return DiagnosticResult(
            name="dependencies",
            status=status,
            message=message,
            details={
                'missing_required': missing_required,
                'missing_optional': missing_optional,
            },
            duration_ms=(time.time() - start) * 1000,
        )
    
    def _check_file_permissions(self) -> DiagnosticResult:
        """Check file permissions for log and data directories."""
        start = time.time()
        directories = [
            Path("logs"),
            Path("data"),
            Path("config"),
        ]
        
        issues = []
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                test_file = directory / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                issues.append(f"{directory}: {e}")
        
        if issues:
            status = CheckStatus.FAIL
            message = f"File permission issues: {', '.join(issues)}"
        else:
            status = CheckStatus.PASS
            message = "File permissions OK"
        
        return DiagnosticResult(
            name="file_permissions",
            status=status,
            message=message,
            details={'issues': issues},
            duration_ms=(time.time() - start) * 1000,
        )
    
    def _check_disk_space(self) -> DiagnosticResult:
        """Check available disk space."""
        start = time.time()
        
        if not PSUTIL_AVAILABLE:
            return DiagnosticResult(
                name="disk_space",
                status=CheckStatus.SKIPPED,
                message="psutil not available",
                duration_ms=(time.time() - start) * 1000,
            )
        
        try:
            disk = psutil.disk_usage('.')
            free_gb = disk.free / (1024 ** 3)
            total_gb = disk.total / (1024 ** 3)
            percent_free = (disk.free / disk.total) * 100
            
            if percent_free < 5:
                status = CheckStatus.FAIL
                message = f"Critical: Only {free_gb:.1f}GB free ({percent_free:.1f}%)"
            elif percent_free < 10:
                status = CheckStatus.WARNING
                message = f"Low disk space: {free_gb:.1f}GB free ({percent_free:.1f}%)"
            else:
                status = CheckStatus.PASS
                message = f"Disk space OK: {free_gb:.1f}GB free ({percent_free:.1f}%)"
            
            return DiagnosticResult(
                name="disk_space",
                status=status,
                message=message,
                details={
                    'free_gb': free_gb,
                    'total_gb': total_gb,
                    'percent_free': percent_free,
                },
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return DiagnosticResult(
                name="disk_space",
                status=CheckStatus.FAIL,
                message=f"Failed to check disk space: {e}",
                duration_ms=(time.time() - start) * 1000,
            )
    
    def _check_memory(self) -> DiagnosticResult:
        """Check available memory."""
        start = time.time()
        
        if not PSUTIL_AVAILABLE:
            return DiagnosticResult(
                name="memory",
                status=CheckStatus.SKIPPED,
                message="psutil not available",
                duration_ms=(time.time() - start) * 1000,
            )
        
        try:
            mem = psutil.virtual_memory()
            free_gb = mem.available / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            percent_free = (mem.available / mem.total) * 100
            
            if percent_free < 10:
                status = CheckStatus.WARNING
                message = f"Low memory: {free_gb:.1f}GB available ({percent_free:.1f}%)"
            else:
                status = CheckStatus.PASS
                message = f"Memory OK: {free_gb:.1f}GB available ({percent_free:.1f}%)"
            
            return DiagnosticResult(
                name="memory",
                status=status,
                message=message,
                details={
                    'free_gb': free_gb,
                    'total_gb': total_gb,
                    'percent_free': percent_free,
                },
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return DiagnosticResult(
                name="memory",
                status=CheckStatus.FAIL,
                message=f"Failed to check memory: {e}",
                duration_ms=(time.time() - start) * 1000,
            )
    
    def _check_cpu(self) -> DiagnosticResult:
        """Check CPU usage."""
        start = time.time()
        
        if not PSUTIL_AVAILABLE:
            return DiagnosticResult(
                name="cpu",
                status=CheckStatus.SKIPPED,
                message="psutil not available",
                duration_ms=(time.time() - start) * 1000,
            )
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            
            if cpu_percent > 90:
                status = CheckStatus.WARNING
                message = f"High CPU usage: {cpu_percent:.1f}%"
            else:
                status = CheckStatus.PASS
                message = f"CPU usage: {cpu_percent:.1f}% ({cpu_count} cores)"
            
            return DiagnosticResult(
                name="cpu",
                status=status,
                message=message,
                details={
                    'cpu_percent': cpu_percent,
                    'cpu_count': cpu_count,
                },
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return DiagnosticResult(
                name="cpu",
                status=CheckStatus.FAIL,
                message=f"Failed to check CPU: {e}",
                duration_ms=(time.time() - start) * 1000,
            )
    
    def _check_network(self) -> DiagnosticResult:
        """Check network connectivity."""
        start = time.time()
        
        try:
            import socket
            # Try to resolve a common hostname
            socket.gethostbyname('google.com')
            status = CheckStatus.PASS
            message = "Network connectivity OK"
        except Exception:
            status = CheckStatus.WARNING
            message = "Network connectivity check failed (may be offline)"
        
        return DiagnosticResult(
            name="network",
            status=status,
            message=message,
            duration_ms=(time.time() - start) * 1000,
        )
    
    def _check_configuration(self) -> DiagnosticResult:
        """Check configuration files."""
        start = time.time()
        config_files = [
            Path("config/app_config.json"),
        ]
        
        missing = []
        invalid = []
        
        for config_file in config_files:
            if not config_file.exists():
                missing.append(str(config_file))
            else:
                try:
                    import json
                    with open(config_file) as f:
                        json.load(f)
                except Exception as e:
                    invalid.append(f"{config_file}: {e}")
        
        if missing:
            status = CheckStatus.WARNING
            message = f"Missing config files: {', '.join(missing)}"
        elif invalid:
            status = CheckStatus.FAIL
            message = f"Invalid config files: {', '.join(invalid)}"
        else:
            status = CheckStatus.PASS
            message = "Configuration files OK"
        
        return DiagnosticResult(
            name="configuration",
            status=status,
            message=message,
            details={'missing': missing, 'invalid': invalid},
            duration_ms=(time.time() - start) * 1000,
        )
    
    def _check_log_files(self) -> DiagnosticResult:
        """Check log file accessibility."""
        start = time.time()
        log_dir = Path("logs")
        
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            test_log = log_dir / ".test_log"
            with open(test_log, 'w') as f:
                f.write("test")
            test_log.unlink()
            status = CheckStatus.PASS
            message = "Log files accessible"
        except Exception as e:
            status = CheckStatus.FAIL
            message = f"Log file access failed: {e}"
        
        return DiagnosticResult(
            name="log_files",
            status=status,
            message=message,
            duration_ms=(time.time() - start) * 1000,
        )
    
    def _check_hardware_interfaces(self) -> DiagnosticResult:
        """Check hardware interface availability."""
        start = time.time()
        available = []
        unavailable = []
        
        # Check serial ports
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            if ports:
                available.append(f"{len(ports)} serial port(s)")
            else:
                unavailable.append("serial ports")
        except Exception:
            unavailable.append("serial ports (pyserial not available)")
        
        # Check cameras
        try:
            import cv2
            camera_count = 0
            for i in range(5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    camera_count += 1
                    cap.release()
            if camera_count > 0:
                available.append(f"{camera_count} camera(s)")
            else:
                unavailable.append("cameras")
        except Exception:
            unavailable.append("cameras (opencv not available)")
        
        if unavailable and not available:
            status = CheckStatus.WARNING
            message = f"No hardware interfaces detected: {', '.join(unavailable)}"
        elif unavailable:
            status = CheckStatus.WARNING
            message = f"Some interfaces unavailable: {', '.join(unavailable)}"
        else:
            status = CheckStatus.PASS
            message = f"Hardware interfaces: {', '.join(available)}"
        
        return DiagnosticResult(
            name="hardware_interfaces",
            status=status,
            message=message,
            details={'available': available, 'unavailable': unavailable},
            duration_ms=(time.time() - start) * 1000,
        )
    
    def _check_database_connectivity(self) -> DiagnosticResult:
        """Check database connectivity."""
        start = time.time()
        
        # Check SQLite
        try:
            import sqlite3
            test_db = Path("test.db")
            conn = sqlite3.connect(str(test_db))
            conn.close()
            test_db.unlink()
            sqlite_ok = True
        except Exception as e:
            sqlite_ok = False
            sqlite_error = str(e)
        
        # Check PostgreSQL (optional)
        postgres_ok = None
        try:
            import psycopg2
            # Don't actually connect, just check if module is available
            postgres_ok = True
        except ImportError:
            postgres_ok = False
        
        if not sqlite_ok:
            status = CheckStatus.FAIL
            message = f"SQLite unavailable: {sqlite_error}"
        elif postgres_ok is False:
            status = CheckStatus.WARNING
            message = "SQLite OK, PostgreSQL not available"
        else:
            status = CheckStatus.PASS
            message = "Database connectivity OK"
        
        return DiagnosticResult(
            name="database_connectivity",
            status=status,
            message=message,
            details={'sqlite': sqlite_ok, 'postgres': postgres_ok},
            duration_ms=(time.time() - start) * 1000,
        )
    
    def _check_camera_availability(self) -> DiagnosticResult:
        """Check camera availability."""
        start = time.time()
        
        try:
            import cv2
            camera_count = 0
            for i in range(5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    camera_count += 1
                    cap.release()
            
            if camera_count == 0:
                status = CheckStatus.WARNING
                message = "No cameras detected"
            else:
                status = CheckStatus.PASS
                message = f"{camera_count} camera(s) detected"
            
            return DiagnosticResult(
                name="camera_availability",
                status=status,
                message=message,
                details={'camera_count': camera_count},
                duration_ms=(time.time() - start) * 1000,
            )
        except ImportError:
            return DiagnosticResult(
                name="camera_availability",
                status=CheckStatus.SKIPPED,
                message="OpenCV not available",
                duration_ms=(time.time() - start) * 1000,
            )


__all__ = [
    "Troubleshooter",
    "DiagnosticLevel",
    "CheckStatus",
    "DiagnosticResult",
    "SystemDiagnostics",
]

