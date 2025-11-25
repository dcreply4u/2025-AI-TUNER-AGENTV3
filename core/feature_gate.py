"""
Feature Gate - Helper for checking license-based feature access.

Provides decorators and utilities for gating features based on license status.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Callable, Optional, TypeVar, Any

from core.license_manager import get_license_manager
from core.demo_restrictions import get_demo_restrictions

LOGGER = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


def require_feature(feature: str, show_message: bool = True) -> Callable[[F], F]:
    """
    Decorator to require a feature to be enabled.
    
    Args:
        feature: Feature name to check
        show_message: Show message to user if feature is disabled
        
    Example:
        @require_feature('ecu_tuning_write')
        def save_ecu_config(self):
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            license_manager = get_license_manager()
            
            # Check if feature is enabled
            if not license_manager.is_feature_enabled(feature):
                if license_manager.is_demo_mode():
                    # Check demo restrictions
                    demo_restrictions = get_demo_restrictions()
                    allowed, reason = demo_restrictions.can_use_feature(feature)
                    if not allowed:
                        if show_message:
                            _show_demo_message(reason)
                        return None
                
                if show_message:
                    _show_license_message(feature, license_manager.get_license_type().value)
                return None
            
            # Feature is enabled, proceed
            return func(*args, **kwargs)
        return wrapper  # type: ignore
    return decorator


def check_feature(feature: str) -> tuple[bool, Optional[str]]:
    """
    Check if a feature is enabled.
    
    Args:
        feature: Feature name to check
        
    Returns:
        (enabled, reason_message)
    """
    license_manager = get_license_manager()
    
    # Check if feature is enabled
    if not license_manager.is_feature_enabled(feature):
        if license_manager.is_demo_mode():
            # Check demo restrictions
            demo_restrictions = get_demo_restrictions()
            allowed, reason = demo_restrictions.can_use_feature(feature)
            if not allowed:
                return False, reason
        
        license_type = license_manager.get_license_type().value
        return False, f"Feature '{feature}' requires {license_type.upper()} license or higher"
    
    return True, None


def _show_demo_message(message: str) -> None:
    """Show demo mode message to user."""
    try:
        from PySide6.QtWidgets import QMessageBox, QApplication
        app = QApplication.instance()
        if app:
            QMessageBox.warning(
                None,
                "Demo Mode - Feature Restricted",
                f"{message}\n\n"
                "Enter a license key to unlock this feature.\n"
                "Go to Settings > License to activate."
            )
    except Exception:
        # Fallback to console if Qt not available
        print(f"[DEMO MODE] {message}")


def _show_license_message(feature: str, current_license: str) -> None:
    """Show license upgrade message to user."""
    try:
        from PySide6.QtWidgets import QMessageBox, QApplication
        app = QApplication.instance()
        if app:
            QMessageBox.information(
                None,
                "License Upgrade Required",
                f"Feature '{feature}' requires a higher license tier.\n\n"
                f"Current license: {current_license.upper()}\n"
                "Contact support to upgrade your license."
            )
    except Exception:
        # Fallback to console if Qt not available
        print(f"[LICENSE] Feature '{feature}' requires upgrade from {current_license}")


__all__ = [
    "require_feature",
    "check_feature",
]










