"""
Error Monitoring Service

A robust, lightweight service for continuous runtime error monitoring in the racing tuner app.
Provides real-time error detection, detailed diagnostics, resource monitoring, and analysis.

Features:
- Real-time error detection and alerting
- Detailed error diagnostics (stack traces, context)
- Contextual information (breadcrumbs)
- Error prioritization and impact analysis
- Resource monitoring (CPU, memory)
- User session tracking
- Terminal output with progress indicators
- Lightweight and non-intrusive
"""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
import threading
import time
import traceback
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from queue import Queue
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

try:
    import psutil
    PSUtil_AVAILABLE = True
except ImportError:
    PSUtil_AVAILABLE = False
    psutil = None

from core.error_handler import ErrorContext, ErrorSeverity, get_error_handler

LOGGER = logging.getLogger(__name__)


class ErrorPriority(Enum):
    """Error priority levels for impact analysis."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Breadcrumb:
    """Breadcrumb for tracking user actions leading to error."""
    timestamp: float
    action: str
    component: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceSnapshot:
    """System resource snapshot at time of error."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    process_count: int = 0
    thread_count: int = 0


@dataclass
class ErrorReport:
    """Comprehensive error report with all diagnostic information."""
    # Error identification
    error_id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    priority: ErrorPriority
    
    # Timing
    timestamp: float
    first_occurrence: float
    occurrence_count: int
    
    # Location
    component: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    
    # Diagnostics
    stack_trace: str = ""
    traceback_lines: List[str] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)
    
    # Context
    breadcrumbs: List[Breadcrumb] = field(default_factory=list)
    resource_snapshot: Optional[ResourceSnapshot] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Impact
    affected_users: int = 1
    frequency_per_hour: float = 0.0
    
    # Recovery
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionInfo:
    """User session information."""
    session_id: str
    start_time: float
    user_id: Optional[str] = None
    platform: str = field(default_factory=lambda: platform.platform())
    python_version: str = field(default_factory=lambda: sys.version)
    app_version: Optional[str] = None
    errors: List[str] = field(default_factory=list)  # Error IDs
    breadcrumbs: Deque[Breadcrumb] = field(default_factory=lambda: deque(maxlen=100))


class ErrorMonitoringService:
    """
    Continuous error monitoring service for runtime error detection and analysis.
    
    This service runs in the background, monitoring for errors, capturing diagnostics,
    and providing real-time feedback through terminal output.
    """
    
    def __init__(
        self,
        enable_terminal_output: bool = True,
        enable_resource_monitoring: bool = True,
        enable_breadcrumbs: bool = True,
        max_breadcrumbs: int = 100,
        resource_check_interval: float = 1.0,
        error_buffer_size: int = 1000,
        session_timeout: float = 3600.0,  # 1 hour
    ):
        """
        Initialize error monitoring service.
        
        Args:
            enable_terminal_output: Enable real-time terminal output
            enable_resource_monitoring: Monitor system resources
            enable_breadcrumbs: Track user actions (breadcrumbs)
            max_breadcrumbs: Maximum breadcrumbs per session
            resource_check_interval: Interval for resource monitoring (seconds)
            error_buffer_size: Maximum errors to keep in memory
            session_timeout: Session timeout in seconds
        """
        self.enable_terminal_output = enable_terminal_output
        self.enable_resource_monitoring = enable_resource_monitoring and PSUtil_AVAILABLE
        self.enable_breadcrumbs = enable_breadcrumbs
        self.max_breadcrumbs = max_breadcrumbs
        self.resource_check_interval = resource_check_interval
        self.error_buffer_size = error_buffer_size
        self.session_timeout = session_timeout
        
        # Error tracking
        self.error_reports: Dict[str, ErrorReport] = {}
        self.error_history: Deque[ErrorReport] = deque(maxlen=error_buffer_size)
        self.error_queue: Queue[ErrorContext] = Queue()
        
        # Session tracking
        self.current_session: Optional[SessionInfo] = None
        self.sessions: Dict[str, SessionInfo] = {}
        
        # Statistics
        self.stats = {
            "total_errors": 0,
            "errors_by_severity": defaultdict(int),
            "errors_by_component": defaultdict(int),
            "errors_by_type": defaultdict(int),
            "recovery_success_rate": 0.0,
            "average_errors_per_hour": 0.0,
        }
        
        # Resource monitoring
        self.resource_history: Deque[ResourceSnapshot] = deque(maxlen=100)
        self.last_resource_check = 0.0
        self.process = None
        if self.enable_resource_monitoring:
            try:
                self.process = psutil.Process(os.getpid())
            except Exception:
                self.enable_resource_monitoring = False
                LOGGER.warning("Failed to initialize process monitoring")
        
        # Threading
        self.monitoring_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.Lock()
        
        # Terminal output
        self.terminal_output_enabled = enable_terminal_output and sys.stdout.isatty()
        self.last_terminal_update = 0.0
        self.terminal_update_interval = 0.5  # Update terminal every 0.5 seconds
        
        # Integration with existing error handler
        self.error_handler = get_error_handler()
        self.error_handler.register_error_callback(self._on_error_detected)
        
        # Callbacks
        self.error_callbacks: List[Callable[[ErrorReport], None]] = []
        self.alert_callbacks: List[Callable[[ErrorReport], None]] = []
        
        LOGGER.info("Error Monitoring Service initialized")
        LOGGER.info(f"  Terminal output: {self.terminal_output_enabled}")
        LOGGER.info(f"  Resource monitoring: {self.enable_resource_monitoring}")
        LOGGER.info(f"  Breadcrumbs: {self.enable_breadcrumbs}")
    
    def start(self) -> None:
        """Start the error monitoring service."""
        if self.running:
            LOGGER.warning("Error monitoring service is already running")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="ErrorMonitor"
        )
        self.monitoring_thread.start()
        
        # Start new session
        self._start_session()
        
        if self.terminal_output_enabled:
            self._print_startup_message()
        
        LOGGER.info("Error monitoring service started")
    
    def stop(self) -> None:
        """Stop the error monitoring service."""
        if not self.running:
            return
        
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        
        if self.terminal_output_enabled:
            self._print_shutdown_message()
        
        LOGGER.info("Error monitoring service stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        while self.running:
            try:
                # Process error queue
                self._process_error_queue()
                
                # Update resource monitoring
                if self.enable_resource_monitoring:
                    self._update_resource_monitoring()
                
                # Update terminal output
                if self.terminal_output_enabled:
                    self._update_terminal_output()
                
                # Cleanup old sessions
                self._cleanup_sessions()
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.1)
                
            except Exception as e:
                LOGGER.error("Error in monitoring loop: %s", e, exc_info=True)
                time.sleep(1.0)
    
    def _process_error_queue(self) -> None:
        """Process errors from the queue."""
        while not self.error_queue.empty():
            try:
                error_context = self.error_queue.get_nowait()
                self._create_error_report(error_context)
            except Exception as e:
                LOGGER.error("Error processing error queue: %s", e)
    
    def _on_error_detected(self, error_context: ErrorContext) -> None:
        """Callback when error is detected by error handler."""
        self.error_queue.put(error_context)
    
    def _create_error_report(self, error_context: ErrorContext) -> None:
        """Create comprehensive error report from error context."""
        try:
            # Generate error ID
            error_id = self._generate_error_id(error_context)
            
            # Check if this is a duplicate error
            if error_id in self.error_reports:
                report = self.error_reports[error_id]
                report.occurrence_count += 1
                report.timestamp = time.time()
            else:
                # Create new error report
                report = self._build_error_report(error_context, error_id)
                self.error_reports[error_id] = report
                self.error_history.append(report)
            
            # Update statistics
            self._update_statistics(report)
            
            # Capture resource snapshot
            if self.enable_resource_monitoring:
                report.resource_snapshot = self._capture_resource_snapshot()
            
            # Add breadcrumbs
            if self.enable_breadcrumbs and self.current_session:
                report.breadcrumbs = list(self.current_session.breadcrumbs)
                report.session_id = self.current_session.session_id
                self.current_session.errors.append(error_id)
            
            # Notify callbacks
            for callback in self.error_callbacks:
                try:
                    callback(report)
                except Exception as e:
                    LOGGER.error("Error in error callback: %s", e)
            
            # Alert for high priority errors
            if report.priority in [ErrorPriority.HIGH, ErrorPriority.CRITICAL]:
                for callback in self.alert_callbacks:
                    try:
                        callback(report)
                    except Exception as e:
                        LOGGER.error("Error in alert callback: %s", e)
            
            # Terminal output
            if self.terminal_output_enabled:
                self._print_error_notification(report)
            
        except Exception as e:
            LOGGER.error("Error creating error report: %s", e, exc_info=True)
    
    def _build_error_report(
        self,
        error_context: ErrorContext,
        error_id: str
    ) -> ErrorReport:
        """Build comprehensive error report from error context."""
        # Parse stack trace
        stack_trace = error_context.traceback or ""
        traceback_lines = stack_trace.split("\n") if stack_trace else []
        
        # Extract file path, line number, function name
        file_path = None
        line_number = None
        function_name = None
        
        for line in traceback_lines:
            if "File" in line and ".py" in line:
                # Extract file path and line number
                parts = line.strip().split('"')
                if len(parts) >= 2:
                    file_path = parts[1]
                if "line" in line:
                    try:
                        line_number = int(line.split("line")[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
            elif "def " in line or "class " in line:
                # Extract function/class name
                if "def " in line:
                    function_name = line.split("def ")[1].split("(")[0].strip()
                elif "class " in line:
                    function_name = line.split("class ")[1].split("(")[0].strip()
        
        # Determine priority
        priority = self._determine_priority(error_context)
        
        # Build environment info
        environment = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "working_directory": os.getcwd(),
            "pid": os.getpid(),
        }
        
        # Create report
        report = ErrorReport(
            error_id=error_id,
            error_type=error_context.error_type,
            error_message=error_context.message,
            severity=error_context.severity,
            priority=priority,
            timestamp=time.time(),
            first_occurrence=time.time(),
            occurrence_count=1,
            component=error_context.component,
            file_path=file_path,
            line_number=line_number,
            function_name=function_name,
            stack_trace=stack_trace,
            traceback_lines=traceback_lines,
            environment=environment,
            recovery_attempted=error_context.recovery_attempted,
            recovery_successful=error_context.recovery_successful,
            metadata={},
        )
        
        return report
    
    def _generate_error_id(self, error_context: ErrorContext) -> str:
        """Generate unique error ID based on error characteristics."""
        # Use error type, component, and message hash for ID
        import hashlib
        key = f"{error_context.error_type}:{error_context.component}:{error_context.message}"
        hash_obj = hashlib.md5(key.encode())
        return hash_obj.hexdigest()[:12]
    
    def _determine_priority(self, error_context: ErrorContext) -> ErrorPriority:
        """Determine error priority based on severity and context."""
        if error_context.severity == ErrorSeverity.CRITICAL:
            return ErrorPriority.CRITICAL
        elif error_context.severity == ErrorSeverity.HIGH:
            return ErrorPriority.HIGH
        elif error_context.severity == ErrorSeverity.MEDIUM:
            return ErrorPriority.MEDIUM
        else:
            return ErrorPriority.LOW
    
    def _capture_resource_snapshot(self) -> ResourceSnapshot:
        """Capture current system resource snapshot."""
        if not self.enable_resource_monitoring or not self.process:
            return None
        
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # System-wide metrics
            system_memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()
            
            snapshot = ResourceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_info.rss / (1024 * 1024),
                memory_available_mb=system_memory.available / (1024 * 1024),
                disk_io_read_mb=disk_io.read_bytes / (1024 * 1024) if disk_io else 0.0,
                disk_io_write_mb=disk_io.write_bytes / (1024 * 1024) if disk_io else 0.0,
                network_sent_mb=network_io.bytes_sent / (1024 * 1024) if network_io else 0.0,
                network_recv_mb=network_io.bytes_recv / (1024 * 1024) if network_io else 0.0,
                process_count=len(psutil.pids()),
                thread_count=threading.active_count(),
            )
            
            self.resource_history.append(snapshot)
            return snapshot
            
        except Exception as e:
            LOGGER.warning("Failed to capture resource snapshot: %s", e)
            return None
    
    def _update_resource_monitoring(self) -> None:
        """Update resource monitoring periodically."""
        current_time = time.time()
        if current_time - self.last_resource_check >= self.resource_check_interval:
            self._capture_resource_snapshot()
            self.last_resource_check = current_time
    
    def _update_statistics(self, report: ErrorReport) -> None:
        """Update error statistics."""
        with self.lock:
            self.stats["total_errors"] += 1
            self.stats["errors_by_severity"][report.severity.value] += 1
            self.stats["errors_by_component"][report.component] += 1
            self.stats["errors_by_type"][report.error_type] += 1
            
            # Calculate recovery success rate
            total_recovery_attempts = sum(
                1 for r in self.error_history if r.recovery_attempted
            )
            successful_recoveries = sum(
                1 for r in self.error_history if r.recovery_successful
            )
            if total_recovery_attempts > 0:
                self.stats["recovery_success_rate"] = (
                    successful_recoveries / total_recovery_attempts
                )
            
            # Calculate average errors per hour
            if len(self.error_history) > 1:
                time_span = (
                    self.error_history[-1].timestamp - self.error_history[0].timestamp
                )
                if time_span > 0:
                    self.stats["average_errors_per_hour"] = (
                        len(self.error_history) / (time_span / 3600.0)
                    )
    
    def _start_session(self, user_id: Optional[str] = None) -> None:
        """Start a new user session."""
        session_id = f"session_{int(time.time())}_{os.getpid()}"
        self.current_session = SessionInfo(
            session_id=session_id,
            start_time=time.time(),
            user_id=user_id,
            app_version=self._get_app_version(),
        )
        self.sessions[session_id] = self.current_session
        LOGGER.info(f"Started new session: {session_id}")
    
    def _cleanup_sessions(self) -> None:
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if current_time - session.start_time > self.session_timeout
        ]
        for sid in expired_sessions:
            del self.sessions[sid]
    
    def add_breadcrumb(self, action: str, component: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Add a breadcrumb to track user actions."""
        if not self.enable_breadcrumbs or not self.current_session:
            return
        
        breadcrumb = Breadcrumb(
            timestamp=time.time(),
            action=action,
            component=component,
            data=data or {},
        )
        self.current_session.breadcrumbs.append(breadcrumb)
    
    def _get_app_version(self) -> Optional[str]:
        """Get application version if available."""
        # Try to get version from various sources
        try:
            import __main__
            if hasattr(__main__, "__version__"):
                return __main__.__version__
        except Exception:
            pass
        return None
    
    # Terminal output methods
    def _print_startup_message(self) -> None:
        """Print startup message to terminal."""
        print("\n" + "=" * 70)
        print("  ERROR MONITORING SERVICE - ACTIVE")
        print("=" * 70)
        print(f"  Session ID: {self.current_session.session_id if self.current_session else 'N/A'}")
        print(f"  Resource Monitoring: {'✓' if self.enable_resource_monitoring else '✗'}")
        print(f"  Breadcrumbs: {'✓' if self.enable_breadcrumbs else '✗'}")
        print("=" * 70 + "\n")
    
    def _print_shutdown_message(self) -> None:
        """Print shutdown message to terminal."""
        print("\n" + "=" * 70)
        print("  ERROR MONITORING SERVICE - STOPPED")
        print("=" * 70)
        print(f"  Total Errors Monitored: {self.stats['total_errors']}")
        print("=" * 70 + "\n")
    
    def _print_error_notification(self, report: ErrorReport) -> None:
        """Print error notification to terminal."""
        severity_colors = {
            ErrorSeverity.CRITICAL: "\033[91m",  # Red
            ErrorSeverity.HIGH: "\033[93m",       # Yellow
            ErrorSeverity.MEDIUM: "\033[94m",     # Blue
            ErrorSeverity.LOW: "\033[92m",        # Green
        }
        reset_color = "\033[0m"
        
        color = severity_colors.get(report.severity, "")
        timestamp = datetime.fromtimestamp(report.timestamp).strftime("%H:%M:%S")
        
        print(f"\n{color}⚠ ERROR DETECTED [{timestamp}]{reset_color}")
        print(f"  Type: {report.error_type}")
        print(f"  Component: {report.component}")
        print(f"  Message: {report.error_message[:100]}")
        if report.file_path:
            print(f"  Location: {report.file_path}:{report.line_number or '?'}")
        if report.occurrence_count > 1:
            print(f"  Occurrences: {report.occurrence_count}")
        print()
    
    def _update_terminal_output(self) -> None:
        """Update terminal output with current status."""
        current_time = time.time()
        if current_time - self.last_terminal_update < self.terminal_update_interval:
            return
        
        self.last_terminal_update = current_time
        
        # This would be called periodically to update status
        # For now, we'll keep it simple and only show on errors
        pass
    
    # Public API methods
    def get_error_report(self, error_id: str) -> Optional[ErrorReport]:
        """Get error report by ID."""
        return self.error_reports.get(error_id)
    
    def get_recent_errors(self, limit: int = 10) -> List[ErrorReport]:
        """Get recent errors."""
        return list(self.error_history)[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        with self.lock:
            return self.stats.copy()
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """Get comprehensive error analysis."""
        with self.lock:
            # Top errors by frequency
            error_frequencies = {}
            for report in self.error_reports.values():
                error_frequencies[report.error_id] = report.occurrence_count
            
            top_errors = sorted(
                error_frequencies.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                "statistics": self.stats.copy(),
                "top_errors": [
                    {
                        "error_id": error_id,
                        "occurrence_count": count,
                        "report": asdict(self.error_reports[error_id])
                    }
                    for error_id, count in top_errors
                ],
                "total_unique_errors": len(self.error_reports),
                "session_count": len(self.sessions),
            }
    
    def register_error_callback(self, callback: Callable[[ErrorReport], None]) -> None:
        """Register callback for error notifications."""
        self.error_callbacks.append(callback)
    
    def register_alert_callback(self, callback: Callable[[ErrorReport], None]) -> None:
        """Register callback for high-priority error alerts."""
        self.alert_callbacks.append(callback)
    
    def export_error_report(self, error_id: str, file_path: Path) -> bool:
        """Export error report to JSON file."""
        report = self.error_reports.get(error_id)
        if not report:
            return False
        
        try:
            report_dict = asdict(report)
            # Convert enums to strings
            report_dict["severity"] = report.severity.value
            report_dict["priority"] = report.priority.value
            
            with open(file_path, "w") as f:
                json.dump(report_dict, f, indent=2, default=str)
            
            return True
        except Exception as e:
            LOGGER.error("Failed to export error report: %s", e)
            return False


# Global instance
_global_error_monitor: Optional[ErrorMonitoringService] = None


def get_error_monitor() -> ErrorMonitoringService:
    """Get or create global error monitoring service."""
    global _global_error_monitor
    if _global_error_monitor is None:
        _global_error_monitor = ErrorMonitoringService()
    return _global_error_monitor


__all__ = [
    "ErrorMonitoringService",
    "ErrorReport",
    "ErrorPriority",
    "Breadcrumb",
    "ResourceSnapshot",
    "SessionInfo",
    "get_error_monitor",
]

