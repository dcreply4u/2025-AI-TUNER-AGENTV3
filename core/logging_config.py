"""
Centralized Logging Configuration System

Provides robust, configurable logging with:
- Multiple log levels and handlers
- File rotation and retention
- Performance tracking
- Context-aware logging
- Structured logging support
- Remote logging capabilities
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import colorama
    from colorama import Fore, Style
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    console_enabled: bool = True
    file_enabled: bool = True
    file_path: Path = Path("logs/ai_tuner.log")
    max_file_size_mb: int = 10
    backup_count: int = 5
    enable_performance_logging: bool = True
    enable_structured_logging: bool = True
    enable_remote_logging: bool = False
    remote_endpoint: Optional[str] = None
    colorize_console: bool = True
    include_timestamp: bool = True
    include_module: bool = True
    include_thread: bool = False
    include_process: bool = False
    log_format: Optional[str] = None
    date_format: str = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    """Colored console formatter."""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }
    
    def __init__(self, *args, colorize: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.colorize = colorize and COLORAMA_AVAILABLE
        if self.colorize:
            colorama.init(autoreset=True)
    
    def format(self, record: logging.LogRecord) -> str:
        if self.colorize and record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """JSON structured formatter for log aggregation."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class PerformanceFilter(logging.Filter):
    """Filter for performance-related log messages."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        return hasattr(record, 'performance') and record.performance


class LoggingManager:
    """Centralized logging manager."""
    
    _instance: Optional[LoggingManager] = None
    _initialized = False
    
    def __new__(cls) -> LoggingManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if LoggingManager._initialized:
            return
        
        self.config = LoggingConfig()
        self.loggers: Dict[str, logging.Logger] = {}
        self.performance_logger: Optional[logging.Logger] = None
        self._setup_root_logger()
        LoggingManager._initialized = True
    
    def configure(self, config: LoggingConfig) -> None:
        """Configure logging system."""
        self.config = config
        self._setup_root_logger()
    
    def _setup_root_logger(self) -> None:
        """Set up root logger with handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level.value))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if self.config.console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.config.level.value))
            
            if self.config.colorize_console:
                formatter = ColoredFormatter(
                    self._get_format_string(),
                    datefmt=self.config.date_format,
                    colorize=True
                )
            else:
                formatter = logging.Formatter(
                    self._get_format_string(),
                    datefmt=self.config.date_format
                )
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if self.config.file_enabled:
            # Ensure log directory exists
            self.config.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                str(self.config.file_path),
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, self.config.level.value))
            
            if self.config.enable_structured_logging:
                formatter = StructuredFormatter()
            else:
                formatter = logging.Formatter(
                    self._get_format_string(),
                    datefmt=self.config.date_format
                )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # Performance logger (separate file)
        if self.config.enable_performance_logging:
            perf_log_path = self.config.file_path.parent / f"performance_{self.config.file_path.name}"
            perf_handler = logging.handlers.RotatingFileHandler(
                str(perf_log_path),
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            perf_handler.setLevel(logging.DEBUG)
            perf_handler.addFilter(PerformanceFilter())
            perf_handler.setFormatter(StructuredFormatter())
            
            self.performance_logger = logging.getLogger("performance")
            self.performance_logger.addHandler(perf_handler)
            self.performance_logger.setLevel(logging.DEBUG)
            self.performance_logger.propagate = False
    
    def _get_format_string(self) -> str:
        """Get format string based on configuration."""
        if self.config.log_format:
            return self.config.log_format
        
        parts = []
        if self.config.include_timestamp:
            parts.append("%(asctime)s")
        parts.append("[%(levelname)s]")
        if self.config.include_module:
            parts.append("[%(name)s]")
        if self.config.include_thread:
            parts.append("[%(threadName)s]")
        if self.config.include_process:
            parts.append("[%(process)d]")
        parts.append("- %(message)s")
        
        return " ".join(parts)
    
    def get_logger(self, name: str, level: Optional[LogLevel] = None) -> logging.Logger:
        """Get or create a logger for a module."""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        if level:
            logger.setLevel(getattr(logging, level.value))
        self.loggers[name] = logger
        return logger
    
    def log_performance(self, operation: str, duration: float, **kwargs: Any) -> None:
        """Log performance metrics."""
        if not self.performance_logger:
            return
        
        extra_data = {
            'operation': operation,
            'duration_ms': duration * 1000,
            **kwargs
        }
        
        self.performance_logger.debug(
            f"Performance: {operation} took {duration*1000:.2f}ms",
            extra={'performance': True, 'extra_data': extra_data}
        )
    
    def set_level(self, level: LogLevel) -> None:
        """Set global log level."""
        self.config.level = level
        logging.getLogger().setLevel(getattr(logging, level.value))
        for handler in logging.getLogger().handlers:
            handler.setLevel(getattr(logging, level.value))
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        stats = {
            'total_loggers': len(self.loggers),
            'log_file': str(self.config.file_path),
            'log_file_size_mb': self.config.file_path.stat().st_size / (1024 * 1024) if self.config.file_path.exists() else 0,
            'level': self.config.level.value,
            'handlers': len(logging.getLogger().handlers),
        }
        return stats


# Global instance
_logging_manager = LoggingManager()


def get_logger(name: str, level: Optional[LogLevel] = None) -> logging.Logger:
    """Get a logger instance."""
    return _logging_manager.get_logger(name, level)


def configure_logging(config: Optional[LoggingConfig] = None, **kwargs: Any) -> None:
    """Configure logging system."""
    if config is None:
        config = LoggingConfig(**kwargs)
    _logging_manager.configure(config)


def log_performance(operation: str, duration: float, **kwargs: Any) -> None:
    """Log performance metrics."""
    _logging_manager.log_performance(operation, duration, **kwargs)


def set_log_level(level: LogLevel) -> None:
    """Set global log level."""
    _logging_manager.set_level(level)


__all__ = [
    "LoggingConfig",
    "LogLevel",
    "LoggingManager",
    "get_logger",
    "configure_logging",
    "log_performance",
    "set_log_level",
]

