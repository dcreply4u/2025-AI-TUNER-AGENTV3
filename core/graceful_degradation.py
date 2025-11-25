"""
Graceful Degradation Utilities

Provides decorators and utilities for features that should gracefully
disable themselves if dependencies are missing.
"""

from __future__ import annotations

import functools
import logging
from typing import Callable, Optional, TypeVar

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class FeatureUnavailable(Exception):
    """Exception raised when a feature is unavailable."""

    pass


def optional_feature(
    feature_name: str,
    required_module: Optional[str] = None,
    required_driver: Optional[str] = None,
    notification_callback: Optional[Callable[[str, str], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    Decorator for optional features that should gracefully degrade.

    Args:
        feature_name: Name of the feature
        required_module: Required Python module name
        required_driver: Required driver/system component
        notification_callback: Callback to show notification (message, level)

    Returns:
        Decorated function that returns None if feature unavailable
    """

    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            # Check module availability
            if required_module:
                try:
                    __import__(required_module)
                except ImportError:
                    msg = f"{feature_name} unavailable: {required_module} not installed"
                    LOGGER.warning(msg)
                    if notification_callback:
                        notification_callback(msg, "warning")
                    return None

            # Check driver availability (placeholder - can be extended)
            if required_driver:
                # This could check for system drivers, hardware, etc.
                pass

            try:
                return func(*args, **kwargs)
            except Exception as e:
                msg = f"{feature_name} error: {str(e)}"
                LOGGER.error(msg, exc_info=True)
                if notification_callback:
                    notification_callback(msg, "error")
                return None

        return wrapper

    return decorator


def safe_import(module_name: str, fallback: Optional[T] = None) -> Optional[T]:
    """
    Safely import a module, returning fallback if unavailable.

    Args:
        module_name: Module to import
        fallback: Value to return if import fails

    Returns:
        Imported module or fallback
    """
    try:
        return __import__(module_name)
    except ImportError:
        LOGGER.debug("Module %s not available, using fallback", module_name)
        return fallback


def check_dependency(dependency_name: str, check_func: Callable[[], bool], notification_callback: Optional[Callable[[str, str], None]] = None) -> bool:
    """
    Check if a dependency is available.

    Args:
        dependency_name: Name of dependency
        check_func: Function that returns True if available
        notification_callback: Callback to show notification

    Returns:
        True if dependency available
    """
    try:
        available = check_func()
        if not available:
            msg = f"{dependency_name} not available - feature disabled"
            LOGGER.warning(msg)
            if notification_callback:
                notification_callback(msg, "warning")
        return available
    except Exception as e:
        msg = f"{dependency_name} check failed: {str(e)} - feature disabled"
        LOGGER.warning(msg)
        if notification_callback:
            notification_callback(msg, "warning")
        return False


__all__ = ["optional_feature", "safe_import", "check_dependency", "FeatureUnavailable"]

