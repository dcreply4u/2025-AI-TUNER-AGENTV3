"""Core platform and hardware abstraction modules."""

from .config_manager import AppConfig, ConfigManager, VehicleProfile
from .config_validator import ConfigValidator, ConfigValidationError
from .data_validator import DataValidator, MetricDefinition, ValidationLevel, ValidationResult
from .error_handler import ErrorContext, ErrorHandler, ErrorSeverity, get_error_handler, handle_errors
from .crash_detector import CrashDetector, CrashReport, get_crash_detector
from .crash_logger import CrashLogger, get_crash_logger
from .hardware_platform import HardwareConfig, HardwareDetector, get_hardware_config
from .disk_manager import DiskManager
from .memory_manager import CircularBuffer, MemoryManager
from .performance_manager import PerformanceManager, PerformanceMetrics, ResourceType, ResourceUsage, ThreadPoolManager
from .reterminal_optimizations import ReTerminalOptimizer, optimize_for_reterminal
from .resource_optimizer import ResourceOptimizer
from .security_manager import SecurityManager
from .ui_optimizer import EfficientDataModel, LazyWidget, UIOptimizer, debounce, throttle
from .logging_config import LoggingConfig, LoggingManager, LogLevel, configure_logging, get_logger, log_performance, set_log_level
from .logging_utils import log_execution_time, log_function_call, log_performance_metric, log_resource_usage, log_error_with_context
from .troubleshooter import CheckStatus, DiagnosticLevel, DiagnosticResult, SystemDiagnostics, Troubleshooter
from .app_context import AppContext
from .performance_optimizer import (
    CircularBuffer,
    LazyLoader,
    PerformanceMonitor,
    Throttle,
    UpdateBatcher,
    defer_to_background,
    enable_performance_monitoring,
    get_performance_monitor,
    measure_time,
    throttle,
)

try:
    from .error_recovery import (
        ErrorRecoveryManager,
        ErrorState,
        ErrorType,
        RecoveryAction,
        get_recovery_manager,
    )
except ImportError:
    # Fallback to new error_recovery module
    from .error_recovery import (
        CircuitBreaker,
        ConnectionManager,
        RetryConfig,
        retry_with_backoff,
    )
    ErrorRecoveryManager = None  # type: ignore
    ErrorState = None  # type: ignore
    ErrorType = None  # type: ignore
    RecoveryAction = None  # type: ignore
    get_recovery_manager = None  # type: ignore

__all__ = [
    "AppConfig",
    "ConfigManager",
    "VehicleProfile",
    "ConfigValidator",
    "ConfigValidationError",
    "DataValidator",
    "MetricDefinition",
    "ValidationLevel",
    "ValidationResult",
    "ErrorContext",
    "ErrorHandler",
    "ErrorSeverity",
    "get_error_handler",
    "handle_errors",
    "CrashDetector",
    "CrashReport",
    "get_crash_detector",
    "CrashLogger",
    "get_crash_logger",
    "HardwareConfig",
    "HardwareDetector",
    "get_hardware_config",
    "PerformanceManager",
    "PerformanceMetrics",
    "ResourceType",
    "ResourceUsage",
    "ThreadPoolManager",
    "ReTerminalOptimizer",
    "optimize_for_reterminal",
    "ResourceOptimizer",
    "SecurityManager",
    "MemoryManager",
    "CircularBuffer",
    "DiskManager",
    "UIOptimizer",
    "LazyWidget",
    "debounce",
    "throttle",
    "EfficientDataModel",
    "LoggingConfig",
    "LoggingManager",
    "LogLevel",
    "configure_logging",
    "get_logger",
    "log_performance",
    "set_log_level",
    "log_execution_time",
    "log_function_call",
    "log_performance_metric",
    "log_resource_usage",
    "log_error_with_context",
    "Troubleshooter",
    "DiagnosticLevel",
    "CheckStatus",
    "DiagnosticResult",
    "SystemDiagnostics",
    "AppContext",
    "LazyLoader",
    "UpdateBatcher",
    "CircularBuffer",
    "Throttle",
    "PerformanceMonitor",
    "throttle",
    "measure_time",
    "defer_to_background",
    "get_performance_monitor",
    "enable_performance_monitoring",
]

# Add error recovery exports if available
if ErrorRecoveryManager is not None:
    __all__.extend([
        "ErrorRecoveryManager",
        "ErrorState",
        "ErrorType",
        "RecoveryAction",
        "get_recovery_manager",
    ])
else:
    __all__.extend([
        "CircuitBreaker",
        "ConnectionManager",
        "RetryConfig",
        "retry_with_backoff",
    ])

