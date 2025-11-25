#!/usr/bin/env python3
"""
AI Tuner Agent Startup Script

Main entry point for the AI Tuner Agent application.
Handles initialization, validation, and error recovery.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Initialize comprehensive logging system
from core.init_logging import initialize_logging
from core.logging_config import get_logger

initialize_logging(
    log_level="INFO",
    log_file=Path("logs/ai_tuner.log"),
    enable_performance=True,
    enable_structured=True,
    colorize=True,
)

LOGGER = get_logger(__name__)


def validate_environment() -> bool:
    """Validate environment and configuration."""
    try:
        from core.config_validator import ConfigValidator

        LOGGER.info("Validating configuration...")
        results = ConfigValidator.validate_all()

        if not results["valid"]:
            LOGGER.error("Configuration validation failed:")
            for error in results["errors"]:
                LOGGER.error("  ✗ %s", error)
            return False

        if results["warnings"]:
            LOGGER.warning("Configuration warnings:")
            for warning in results["warnings"]:
                LOGGER.warning("  ⚠ %s", warning)

        return True
    except Exception as e:
        LOGGER.error("Error during validation: %s", e)
        return False


def run_diagnostics() -> None:
    """Run system diagnostics."""
    try:
        from tools.system_diagnostics import SystemDiagnostics

        LOGGER.info("Running system diagnostics...")
        diagnostics = SystemDiagnostics()
        diagnostics.run_all_checks()
        diagnostics.save_report("startup_diagnostics.json")
    except Exception as e:
        LOGGER.warning("Could not run diagnostics: %s", e)


def main() -> None:
    """Main entry point."""
    LOGGER.info("=" * 60)
    LOGGER.info("AI Tuner Agent - Starting")
    LOGGER.info("=" * 60)

    # Code protection and YubiKey verification
    try:
        from core.code_protection import CodeProtection
        
        # Check if YubiKey required
        require_yubikey = os.environ.get("AI_TUNER_REQUIRE_YUBIKEY", "false").lower() == "true"
        yubikey_serial = os.environ.get("AI_TUNER_YUBIKEY_SERIAL")
        
        protection = CodeProtection(
            require_yubikey=require_yubikey,
            yubikey_serial=yubikey_serial,
        )
        
        # Enforce protection
        if not protection.enforce_protection():
            LOGGER.critical("Code protection checks failed - application cannot start!")
            sys.exit(1)
        
        LOGGER.info("Code protection verified")
    except Exception as e:
        LOGGER.warning("Code protection check failed (non-critical): %s", e)
    
    # Check license status
    try:
        from core.license_manager import get_license_manager
        license_manager = get_license_manager()
        if license_manager.is_demo_mode():
            LOGGER.info("Running in DEMO MODE - Limited features available")
            LOGGER.info("Enter license key in Settings to unlock full features")
        else:
            license_type = license_manager.get_license_type().value.upper()
            LOGGER.info(f"License active: {license_type}")
    except Exception as e:
        LOGGER.warning("License check failed (non-critical): %s", e)

    # Validate environment
    if not validate_environment():
        LOGGER.error("Environment validation failed. Please fix configuration errors.")
        sys.exit(1)

    # Run diagnostics (optional, can be disabled)
    if "--diagnostics" in sys.argv:
        run_diagnostics()

    # Import and run UI
    try:
        from PySide6.QtWidgets import QApplication
        from ui.main import MainWindow

        LOGGER.info("Initializing Qt application...")
        app = QApplication(sys.argv)
        app.setApplicationName("AI Tuner Agent")

        LOGGER.info("Creating main window...")
        window = MainWindow()
        window.show()

        LOGGER.info("Starting event loop...")
        sys.exit(app.exec())

    except KeyboardInterrupt:
        LOGGER.info("Shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        LOGGER.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

