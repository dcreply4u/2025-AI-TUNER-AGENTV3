"""
Initialize Logging System

This module should be imported early to set up logging for all modules.
Call initialize_logging() at application startup.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from core.logging_config import LoggingConfig, configure_logging, get_logger, LogLevel


def initialize_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_performance: bool = True,
    enable_structured: bool = True,
    colorize: bool = True,
) -> None:
    """
    Initialize the logging system for the entire application.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (defaults to logs/ai_tuner.log)
        enable_performance: Enable performance logging
        enable_structured: Enable structured JSON logging
        colorize: Enable colored console output
    """
    # Determine log level
    try:
        level = LogLevel[log_level.upper()]
    except KeyError:
        level = LogLevel.INFO
    
    # Determine log file path
    if log_file is None:
        log_file = Path("logs/ai_tuner.log")
    
    # Check for environment variable overrides
    env_level = os.environ.get("AITUNER_LOG_LEVEL", "").upper()
    if env_level:
        try:
            level = LogLevel[env_level]
        except KeyError:
            pass
    
    # Create configuration
    config = LoggingConfig(
        level=level,
        console_enabled=True,
        file_enabled=True,
        file_path=log_file,
        max_file_size_mb=10,
        backup_count=5,
        enable_performance_logging=enable_performance,
        enable_structured_logging=enable_structured,
        colorize_console=colorize and sys.stdout.isatty(),
        include_timestamp=True,
        include_module=True,
    )
    
    # Configure logging
    configure_logging(config)
    
    # Get logger and log initialization
    logger = get_logger(__name__)
    logger.info("=" * 60)
    logger.info("AI Tuner - Logging System Initialized")
    logger.info(f"Log Level: {level.value}")
    logger.info(f"Log File: {log_file}")
    logger.info(f"Performance Logging: {enable_performance}")
    logger.info(f"Structured Logging: {enable_structured}")
    logger.info("=" * 60)


# Auto-initialize if this module is imported directly
if __name__ != "__main__":
    # Only auto-initialize if logging hasn't been configured yet
    import logging
    if not logging.getLogger().handlers:
        initialize_logging()


__all__ = ["initialize_logging"]

