"""
Advanced Crash Logging System

Provides detailed crash logging with context, stack traces, and recovery attempts.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.crash_detector import CrashReport, get_crash_detector

LOGGER = logging.getLogger(__name__)


class CrashLogger:
    """Advanced crash logging system with structured output."""

    def __init__(self, log_dir: Optional[Path] = None) -> None:
        """Initialize crash logger."""
        self.log_dir = log_dir or Path("logs/crashes")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON log file for structured logging
        self.json_log_file = self.log_dir / "crashes.json"
        self._init_json_log()
        
        LOGGER.info("Crash logger initialized (log dir: %s)", self.log_dir)

    def _init_json_log(self) -> None:
        """Initialize JSON log file if it doesn't exist."""
        if not self.json_log_file.exists():
            with open(self.json_log_file, "w", encoding="utf-8") as f:
                json.dump({"crashes": []}, f, indent=2)

    def log_crash(self, crash: CrashReport) -> None:
        """Log crash in multiple formats."""
        # Log to structured JSON
        self._log_json(crash)
        
        # Log to human-readable text
        self._log_text(crash)
        
        # Log to console
        self._log_console(crash)

    def _log_json(self, crash: CrashReport) -> None:
        """Log crash to JSON file."""
        try:
            # Read existing crashes
            with open(self.json_log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Add new crash
            crash_data = {
                "crash_id": crash.crash_id,
                "timestamp": crash.timestamp,
                "datetime": datetime.fromtimestamp(crash.timestamp).isoformat(),
                "exception_type": crash.exception_type,
                "exception_message": crash.exception_message,
                "component": crash.component,
                "thread_name": crash.thread_name,
                "stack_trace": crash.stack_trace,
                "system_info": crash.system_info,
                "memory_info": crash.memory_info,
                "recovery_attempted": crash.recovery_attempted,
                "recovery_successful": crash.recovery_successful,
                "recent_errors": [
                    {
                        "timestamp": e.timestamp,
                        "component": e.component,
                        "severity": e.severity.value,
                        "message": e.message,
                    }
                    for e in crash.recent_errors
                ],
            }
            
            data["crashes"].append(crash_data)
            
            # Keep only last 100 crashes
            if len(data["crashes"]) > 100:
                data["crashes"] = data["crashes"][-100:]
            
            # Write back
            with open(self.json_log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            LOGGER.debug("Crash logged to JSON: %s", crash.crash_id)
        except Exception as e:
            LOGGER.error("Failed to log crash to JSON: %s", e)

    def _log_text(self, crash: CrashReport) -> None:
        """Log crash to human-readable text file."""
        crash_file = self.log_dir / f"{crash.crash_id}.txt"
        
        try:
            with open(crash_file, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write(f"CRASH REPORT: {crash.crash_id}\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Timestamp: {datetime.fromtimestamp(crash.timestamp)}\n")
                f.write(f"Exception Type: {crash.exception_type}\n")
                f.write(f"Exception Message: {crash.exception_message}\n")
                f.write(f"Component: {crash.component}\n")
                f.write(f"Thread: {crash.thread_name}\n")
                f.write(f"Recovery Attempted: {crash.recovery_attempted}\n")
                f.write(f"Recovery Successful: {crash.recovery_successful}\n\n")
                
                f.write("STACK TRACE:\n")
                f.write("-" * 80 + "\n")
                for i, frame in enumerate(crash.stack_trace, 1):
                    f.write(f"{i:3d}. {frame}\n")
                f.write("\n")
                
                f.write("FULL TRACEBACK:\n")
                f.write("-" * 80 + "\n")
                f.write(crash.traceback)
                f.write("\n\n")
                
                f.write("SYSTEM INFORMATION:\n")
                f.write("-" * 80 + "\n")
                for key, value in crash.system_info.items():
                    f.write(f"  {key:20s}: {value}\n")
                f.write("\n")
                
                f.write("MEMORY INFORMATION:\n")
                f.write("-" * 80 + "\n")
                for key, value in crash.memory_info.items():
                    f.write(f"  {key:20s}: {value}\n")
                f.write("\n")
                
                if crash.recent_errors:
                    f.write("RECENT ERRORS (Last 5):\n")
                    f.write("-" * 80 + "\n")
                    for error in crash.recent_errors[-5:]:
                        f.write(f"  [{datetime.fromtimestamp(error.timestamp)}] ")
                        f.write(f"{error.component}: {error.message}\n")
                    f.write("\n")
                
                f.write("=" * 80 + "\n")
            
            LOGGER.debug("Crash logged to text file: %s", crash_file)
        except Exception as e:
            LOGGER.error("Failed to log crash to text file: %s", e)

    def _log_console(self, crash: CrashReport) -> None:
        """Log crash to console with color coding."""
        # Use different log levels based on recovery success
        if crash.recovery_successful:
            LOGGER.warning(
                "CRASH [%s] in %s - RECOVERED: %s",
                crash.crash_id,
                crash.component,
                crash.exception_message,
            )
        else:
            LOGGER.critical(
                "CRASH [%s] in %s - NOT RECOVERED: %s",
                crash.crash_id,
                crash.component,
                crash.exception_message,
            )
        
        # Log stack trace
        if crash.stack_trace:
            LOGGER.debug("Stack trace (top 5 frames):")
            for frame in crash.stack_trace[:5]:
                LOGGER.debug("  %s", frame)

    def get_crash_summary(self, crash_id: str) -> Optional[dict[str, Any]]:
        """Get summary of a specific crash."""
        try:
            with open(self.json_log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for crash in data["crashes"]:
                if crash["crash_id"] == crash_id:
                    return crash
            return None
        except Exception as e:
            LOGGER.error("Failed to get crash summary: %s", e)
            return None

    def get_recent_crashes(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent crashes."""
        try:
            with open(self.json_log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            crashes = data.get("crashes", [])
            return crashes[-limit:]
        except Exception as e:
            LOGGER.error("Failed to get recent crashes: %s", e)
            return []

    def get_crash_statistics(self) -> dict[str, Any]:
        """Get crash statistics."""
        try:
            with open(self.json_log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            crashes = data.get("crashes", [])
            
            if not crashes:
                return {
                    "total": 0,
                    "by_component": {},
                    "by_exception": {},
                    "recovery_rate": 0.0,
                }
            
            by_component = {}
            by_exception = {}
            recovered = 0
            
            for crash in crashes:
                component = crash.get("component", "Unknown")
                exception = crash.get("exception_type", "Unknown")
                by_component[component] = by_component.get(component, 0) + 1
                by_exception[exception] = by_exception.get(exception, 0) + 1
                if crash.get("recovery_successful", False):
                    recovered += 1
            
            return {
                "total": len(crashes),
                "by_component": by_component,
                "by_exception": by_exception,
                "recovery_rate": recovered / len(crashes) if crashes else 0.0,
            }
        except Exception as e:
            LOGGER.error("Failed to get crash statistics: %s", e)
            return {"error": str(e)}


# Global crash logger instance
_global_crash_logger: Optional[CrashLogger] = None


def get_crash_logger(log_dir: Optional[Path] = None) -> CrashLogger:
    """Get or create global crash logger."""
    global _global_crash_logger
    if _global_crash_logger is None:
        _global_crash_logger = CrashLogger(log_dir=log_dir)
    return _global_crash_logger


__all__ = ["CrashLogger", "get_crash_logger"]





