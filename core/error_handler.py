"""
Error Handling and Recovery System

Provides graceful error handling, automatic recovery, and user-friendly error messages.
"""

from __future__ import annotations

import logging
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, Type

LOGGER = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"  # Informational, non-critical
    MEDIUM = "medium"  # Warning, may affect functionality
    HIGH = "high"  # Error, functionality degraded
    CRITICAL = "critical"  # System failure


@dataclass
class ErrorContext:
    """Context information for an error."""

    error_type: str
    severity: ErrorSeverity
    message: str
    component: str
    timestamp: float = field(default_factory=time.time)
    traceback: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    user_message: Optional[str] = None


class ErrorHandler:
    """Centralized error handling and recovery system."""

    def __init__(self) -> None:
        """Initialize error handler."""
        self.error_history: list[ErrorContext] = []
        self.max_history = 1000
        self.recovery_strategies: dict[Type[Exception], Callable] = {}
        self.error_callbacks: list[Callable[[ErrorContext], None]] = []

    def handle_error(
        self,
        error: Exception,
        component: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        attempt_recovery: bool = True,
    ) -> ErrorContext:
        """
        Handle an error with automatic recovery.

        Args:
            error: Exception that occurred
            component: Component where error occurred
            severity: Error severity
            user_message: User-friendly message
            attempt_recovery: Whether to attempt automatic recovery

        Returns:
            Error context with recovery status
        """
        context = ErrorContext(
            error_type=type(error).__name__,
            severity=severity,
            message=str(error),
            component=component,
            traceback=traceback.format_exc(),
            user_message=user_message or self._generate_user_message(error, component),
        )

        # Attempt recovery
        if attempt_recovery:
            context.recovery_attempted = True
            context.recovery_successful = self._attempt_recovery(error, context)

        # Log error
        self._log_error(context)

        # Store in history
        self.error_history.append(context)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

        # Notify callbacks
        for callback in self.error_callbacks:
            try:
                callback(context)
            except Exception as e:
                LOGGER.error("Error in error callback: %s", e)

        return context

    def _attempt_recovery(self, error: Exception, context: ErrorContext) -> bool:
        """Attempt automatic recovery for an error."""
        error_type = type(error)

        # Check for registered recovery strategy
        if error_type in self.recovery_strategies:
            try:
                return self.recovery_strategies[error_type](error, context)
            except Exception as e:
                LOGGER.error("Recovery strategy failed: %s", e)
                return False

        # Default recovery strategies
        if isinstance(error, ConnectionError):
            return self._recover_connection_error(error, context)
        elif isinstance(error, FileNotFoundError):
            return self._recover_file_error(error, context)
        elif isinstance(error, PermissionError):
            return self._recover_permission_error(error, context)
        elif isinstance(error, TimeoutError):
            return self._recover_timeout_error(error, context)

        return False

    def _recover_connection_error(self, error: ConnectionError, context: ErrorContext) -> bool:
        """Recover from connection errors."""
        LOGGER.info("Attempting to recover from connection error in %s", context.component)
        # Wait and retry logic would go here
        time.sleep(1)
        return False  # Recovery would need component-specific logic

    def _recover_file_error(self, error: FileNotFoundError, context: ErrorContext) -> bool:
        """Recover from file errors."""
        LOGGER.info("Attempting to recover from file error in %s", context.component)
        # Create missing directories or files
        return False

    def _recover_permission_error(self, error: PermissionError, context: ErrorContext) -> bool:
        """Recover from permission errors."""
        LOGGER.warning("Permission error in %s - may need elevated privileges", context.component)
        return False

    def _recover_timeout_error(self, error: TimeoutError, context: ErrorContext) -> bool:
        """Recover from timeout errors."""
        LOGGER.info("Timeout in %s - will retry with longer timeout", context.component)
        return False

    def _generate_user_message(self, error: Exception, component: str) -> str:
        """Generate user-friendly error message."""
        error_type = type(error).__name__

        if isinstance(error, ConnectionError):
            return f"Connection to {component} failed. Please check your connection and try again."
        elif isinstance(error, FileNotFoundError):
            return f"Required file not found in {component}. Please check your configuration."
        elif isinstance(error, PermissionError):
            return f"Permission denied in {component}. Please check file permissions."
        elif isinstance(error, TimeoutError):
            return f"{component} timed out. The system may be busy. Please try again."
        else:
            return f"An error occurred in {component}: {str(error)}"

    def _log_error(self, context: ErrorContext) -> None:
        """Log error with appropriate level."""
        log_message = f"[{context.component}] {context.message}"
        if context.traceback:
            log_message += f"\n{context.traceback}"

        if context.severity == ErrorSeverity.CRITICAL:
            LOGGER.critical(log_message)
        elif context.severity == ErrorSeverity.HIGH:
            LOGGER.error(log_message)
        elif context.severity == ErrorSeverity.MEDIUM:
            LOGGER.warning(log_message)
        else:
            LOGGER.info(log_message)

    def register_recovery_strategy(self, error_type: Type[Exception], strategy: Callable) -> None:
        """Register a custom recovery strategy for an error type."""
        self.recovery_strategies[error_type] = strategy

    def register_error_callback(self, callback: Callable[[ErrorContext], None]) -> None:
        """Register a callback to be notified of errors."""
        self.error_callbacks.append(callback)

    def get_recent_errors(self, component: Optional[str] = None, limit: int = 10) -> list[ErrorContext]:
        """Get recent errors, optionally filtered by component."""
        errors = self.error_history[-limit:]
        if component:
            errors = [e for e in errors if e.component == component]
        return errors

    def get_error_stats(self) -> dict[str, Any]:
        """Get error statistics."""
        total = len(self.error_history)
        by_severity = {}
        by_component = {}

        for error in self.error_history:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

            component = error.component
            by_component[component] = by_component.get(component, 0) + 1

        return {
            "total_errors": total,
            "by_severity": by_severity,
            "by_component": by_component,
            "recovery_success_rate": sum(1 for e in self.error_history if e.recovery_successful) / total if total > 0 else 0,
        }


def handle_errors(component: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, user_message: Optional[str] = None):
    """
    Decorator for automatic error handling.

    Args:
        component: Component name
        severity: Default error severity
        user_message: User-friendly error message template
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = getattr(args[0], "error_handler", None) if args else None
                if handler is None:
                    # Use global handler if available
                    handler = getattr(globals(), "_global_error_handler", None)

                if handler:
                    handler.handle_error(e, component, severity, user_message)
                else:
                    # Fallback to standard logging
                    LOGGER.exception("Unhandled error in %s", component)
                raise  # Re-raise for caller to handle if needed

        return wrapper

    return decorator


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get or create global error handler."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


__all__ = ["ErrorHandler", "ErrorContext", "ErrorSeverity", "handle_errors", "get_error_handler"]

