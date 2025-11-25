"""
Advanced Crash Detection and Logging System

Detects crashes, logs detailed information, and attempts recovery.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

try:
    from PySide6.QtCore import QObject, QTimer, Signal
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    # Create dummy classes for when Qt is not available
    class QObject:
        def __init__(self, parent=None):
            pass
    class QTimer:
        def __init__(self):
            pass
        def start(self, *args):
            pass
        def timeout(self):
            pass
    def Signal(*args):
        return None

from core.error_handler import ErrorContext, ErrorSeverity, get_error_handler

LOGGER = logging.getLogger(__name__)


@dataclass
class CrashReport:
    """Detailed crash report with context."""

    timestamp: float = field(default_factory=time.time)
    exception_type: str = ""
    exception_message: str = ""
    traceback: str = ""
    component: str = ""
    thread_name: str = ""
    stack_trace: list[str] = field(default_factory=list)
    system_info: dict[str, Any] = field(default_factory=dict)
    memory_info: dict[str, Any] = field(default_factory=dict)
    recent_errors: list[ErrorContext] = field(default_factory=list)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    crash_id: str = ""


class CrashDetector(QObject if QT_AVAILABLE else object):
    """Advanced crash detection and logging system."""

    if QT_AVAILABLE:
        crash_detected = Signal(CrashReport)  # Qt signal for crash notifications
    else:
        crash_detected = None  # Signal not available without Qt

    def __init__(self, log_dir: Optional[Path] = None) -> None:
        """Initialize crash detector."""
        if QT_AVAILABLE:
            try:
                super().__init__()
            except Exception:
                # If Qt initialization fails, continue without Qt
                pass
        
        self.log_dir = log_dir or Path("logs/crashes")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.crash_count = 0
        self.crash_history: list[CrashReport] = []
        self.max_history = 50
        
        # Recovery strategies
        self.recovery_strategies: list[Callable[[CrashReport], bool]] = []
        
        # Install exception handlers
        self._install_exception_handlers()
        
        # Monitor thread health
        self._monitor_threads = True
        self._thread_monitor_timer: Optional[QTimer] = None
        
        LOGGER.info("Crash detector initialized (log dir: %s)", self.log_dir)

    def _install_exception_handlers(self) -> None:
        """Install global exception handlers."""
        # Store original handlers
        self._original_excepthook = sys.excepthook
        self._original_thread_excepthook = threading.excepthook
        
        # Install custom handlers
        sys.excepthook = self._handle_exception
        threading.excepthook = self._handle_thread_exception

    def _handle_exception(self, exc_type, exc_value, exc_traceback) -> None:
        """Handle unhandled exceptions in main thread."""
        if exc_type is KeyboardInterrupt:
            # Allow normal keyboard interrupt handling
            if self._original_excepthook:
                self._original_excepthook(exc_type, exc_value, exc_traceback)
            return
        
        # Create crash report
        crash_report = self._create_crash_report(exc_type, exc_value, exc_traceback, "MainThread")
        
        # Log crash
        self._log_crash(crash_report)
        
        # Attempt recovery
        crash_report.recovery_attempted = True
        crash_report.recovery_successful = self._attempt_crash_recovery(crash_report)
        
        # Emit signal (if Qt is available)
        if QT_AVAILABLE and self.crash_detected:
            try:
                self.crash_detected.emit(crash_report)
            except Exception as e:
                LOGGER.warning("Could not emit crash signal: %s", e)
        
        # Call original handler if recovery failed
        if not crash_report.recovery_successful:
            if self._original_excepthook:
                self._original_excepthook(exc_type, exc_value, exc_traceback)
            else:
                # Fallback: print to stderr
                import sys
                print(f"Unhandled exception: {exc_type.__name__}: {exc_value}", file=sys.stderr)
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)

    def _handle_thread_exception(self, args) -> None:
        """Handle unhandled exceptions in threads."""
        exc_type, exc_value, exc_traceback, thread = args
        
        if exc_type is KeyboardInterrupt:
            if self._original_thread_excepthook:
                self._original_thread_excepthook(args)
            return
        
        # Create crash report
        thread_name = thread.name if thread else "UnknownThread"
        crash_report = self._create_crash_report(exc_type, exc_value, exc_traceback, thread_name)
        
        # Log crash
        self._log_crash(crash_report)
        
        # Attempt recovery
        crash_report.recovery_attempted = True
        crash_report.recovery_successful = self._attempt_crash_recovery(crash_report)
        
        # Emit signal (if Qt is available)
        if QT_AVAILABLE and self.crash_detected:
            try:
                self.crash_detected.emit(crash_report)
            except Exception as e:
                LOGGER.warning("Could not emit crash signal: %s", e)
        
        # Call original handler
        if self._original_thread_excepthook:
            self._original_thread_excepthook(args)

    def _create_crash_report(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: Any,
        thread_name: str,
    ) -> CrashReport:
        """Create detailed crash report."""
        crash_id = f"CRASH_{int(time.time())}_{self.crash_count}"
        self.crash_count += 1
        
        # Get traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = "".join(tb_lines)
        
        # Get stack trace
        stack_trace = []
        if exc_traceback:
            frame = exc_traceback
            while frame:
                filename = frame.tb_frame.f_code.co_filename
                lineno = frame.tb_lineno
                func_name = frame.tb_frame.f_code.co_name
                stack_trace.append(f"{filename}:{lineno} in {func_name}")
                frame = frame.tb_next
        
        # Get system info
        system_info = self._get_system_info()
        
        # Get memory info
        memory_info = self._get_memory_info()
        
        # Get recent errors
        error_handler = get_error_handler()
        recent_errors = error_handler.get_recent_errors(limit=10) if error_handler else []
        
        # Determine component from stack trace
        component = "Unknown"
        if stack_trace:
            # Try to extract component from file path
            top_frame = stack_trace[0]
            if "ui/" in top_frame:
                component = "UI"
            elif "controllers/" in top_frame:
                component = "Controller"
            elif "services/" in top_frame:
                component = "Service"
            elif "interfaces/" in top_frame:
                component = "Interface"
            elif "core/" in top_frame:
                component = "Core"
        
        return CrashReport(
            crash_id=crash_id,
            timestamp=time.time(),
            exception_type=exc_type.__name__,
            exception_message=str(exc_value),
            traceback=tb_text,
            component=component,
            thread_name=thread_name,
            stack_trace=stack_trace,
            system_info=system_info,
            memory_info=memory_info,
            recent_errors=recent_errors,
        )

    def _get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        import platform
        
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "cwd": os.getcwd(),
            "pid": os.getpid(),
        }

    def _get_memory_info(self) -> dict[str, Any]:
        """Get memory information."""
        try:
            import psutil
            
            process = psutil.Process()
            mem_info = process.memory_info()
            return {
                "rss_mb": mem_info.rss / 1024 / 1024,
                "vms_mb": mem_info.vms / 1024 / 1024,
                "percent": process.memory_percent(),
                "available_mb": psutil.virtual_memory().available / 1024 / 1024,
                "total_mb": psutil.virtual_memory().total / 1024 / 1024,
            }
        except ImportError:
            return {"error": "psutil not available"}

    def _log_crash(self, crash: CrashReport) -> None:
        """Log crash to file and console."""
        # Add to history
        self.crash_history.append(crash)
        if len(self.crash_history) > self.max_history:
            self.crash_history.pop(0)
        
        # Log to console
        LOGGER.critical(
            "CRASH DETECTED [%s] in %s (%s): %s",
            crash.crash_id,
            crash.component,
            crash.thread_name,
            crash.exception_message,
        )
        LOGGER.critical("Traceback:\n%s", crash.traceback)
        
        # Log to file
        crash_file = self.log_dir / f"{crash.crash_id}.log"
        try:
            with open(crash_file, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write(f"CRASH REPORT: {crash.crash_id}\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Timestamp: {datetime.fromtimestamp(crash.timestamp)}\n")
                f.write(f"Exception: {crash.exception_type}\n")
                f.write(f"Message: {crash.exception_message}\n")
                f.write(f"Component: {crash.component}\n")
                f.write(f"Thread: {crash.thread_name}\n\n")
                
                f.write("STACK TRACE:\n")
                f.write("-" * 80 + "\n")
                for frame in crash.stack_trace:
                    f.write(f"  {frame}\n")
                f.write("\n")
                
                f.write("FULL TRACEBACK:\n")
                f.write("-" * 80 + "\n")
                f.write(crash.traceback)
                f.write("\n\n")
                
                f.write("SYSTEM INFO:\n")
                f.write("-" * 80 + "\n")
                for key, value in crash.system_info.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
                
                f.write("MEMORY INFO:\n")
                f.write("-" * 80 + "\n")
                for key, value in crash.memory_info.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
                
                if crash.recent_errors:
                    f.write("RECENT ERRORS:\n")
                    f.write("-" * 80 + "\n")
                    for error in crash.recent_errors[-5:]:
                        f.write(f"  [{error.timestamp}] {error.component}: {error.message}\n")
                    f.write("\n")
                
                f.write("=" * 80 + "\n")
            
            LOGGER.info("Crash report saved to: %s", crash_file)
        except Exception as e:
            LOGGER.error("Failed to save crash report: %s", e)

    def _attempt_crash_recovery(self, crash: CrashReport) -> bool:
        """Attempt to recover from crash."""
        LOGGER.info("Attempting crash recovery for %s", crash.crash_id)
        
        # Try registered recovery strategies
        for strategy in self.recovery_strategies:
            try:
                if strategy(crash):
                    LOGGER.info("Recovery strategy succeeded for %s", crash.crash_id)
                    return True
            except Exception as e:
                LOGGER.error("Recovery strategy failed: %s", e)
        
        # Default recovery strategies
        if self._recover_ui_crash(crash):
            return True
        if self._recover_memory_crash(crash):
            return True
        
        LOGGER.warning("No recovery strategy succeeded for %s", crash.crash_id)
        return False

    def _recover_ui_crash(self, crash: CrashReport) -> bool:
        """Attempt to recover from UI crashes."""
        if crash.component != "UI":
            return False
        
        LOGGER.info("Attempting UI crash recovery")
        # UI recovery would need access to the main window
        # This is handled by the main window's crash handler
        return False

    def _recover_memory_crash(self, crash: CrashReport) -> bool:
        """Attempt to recover from memory-related crashes."""
        memory_info = crash.memory_info
        if "percent" in memory_info and memory_info["percent"] > 90:
            LOGGER.warning("High memory usage detected, attempting cleanup")
            # Trigger garbage collection
            import gc
            gc.collect()
            return True
        return False

    def register_recovery_strategy(self, strategy: Callable[[CrashReport], bool]) -> None:
        """Register a custom recovery strategy."""
        self.recovery_strategies.append(strategy)

    def get_crash_stats(self) -> dict[str, Any]:
        """Get crash statistics."""
        total = len(self.crash_history)
        by_component = {}
        by_exception = {}
        
        for crash in self.crash_history:
            by_component[crash.component] = by_component.get(crash.component, 0) + 1
            by_exception[crash.exception_type] = by_exception.get(crash.exception_type, 0) + 1
        
        return {
            "total_crashes": total,
            "by_component": by_component,
            "by_exception": by_exception,
            "recovery_success_rate": sum(1 for c in self.crash_history if c.recovery_successful) / total if total > 0 else 0,
        }

    def start_thread_monitoring(self) -> None:
        """Start monitoring thread health."""
        if self._thread_monitor_timer:
            return
        
        # Check if QApplication exists before using Qt features
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if not app:
                LOGGER.warning("QApplication not available, skipping thread monitoring")
                return
        except Exception as e:
            LOGGER.warning("Could not check QApplication: %s", e)
            return
        
        try:
            self._thread_monitor_timer = QTimer()
            self._thread_monitor_timer.timeout.connect(self._check_thread_health)
            self._thread_monitor_timer.start(5000)  # Check every 5 seconds
            LOGGER.info("Thread monitoring started")
        except Exception as e:
            LOGGER.error("Failed to start thread monitoring: %s", e)

    def _check_thread_health(self) -> None:
        """Check health of all threads."""
        try:
            for thread in threading.enumerate():
                if thread.is_alive():
                    continue
                
                # Thread died unexpectedly
                LOGGER.warning("Thread %s is not alive", thread.name)
        except Exception as e:
            LOGGER.error("Error checking thread health: %s", e)

    def restore_exception_handlers(self) -> None:
        """Restore original exception handlers."""
        if self._original_excepthook:
            sys.excepthook = self._original_excepthook
        if self._original_thread_excepthook:
            threading.excepthook = self._original_thread_excepthook


# Global crash detector instance
_global_crash_detector: Optional[CrashDetector] = None


def get_crash_detector(log_dir: Optional[Path] = None) -> CrashDetector:
    """Get or create global crash detector."""
    global _global_crash_detector
    if _global_crash_detector is None:
        _global_crash_detector = CrashDetector(log_dir=log_dir)
    return _global_crash_detector


__all__ = ["CrashDetector", "CrashReport", "get_crash_detector"]

