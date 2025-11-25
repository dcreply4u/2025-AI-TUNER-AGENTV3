# Logging and Troubleshooting Guide

## Overview

The AI Tuner application includes a comprehensive logging and troubleshooting system designed to help diagnose issues, monitor performance, and track application behavior across all modules.

## Features

### Logging System

- **Centralized Configuration**: Single configuration point for all logging
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **File Rotation**: Automatic log file rotation with configurable size limits
- **Colored Console Output**: Color-coded log levels for easy reading
- **Structured Logging**: JSON-formatted logs for log aggregation tools
- **Performance Logging**: Separate performance metrics logging
- **Context-Aware**: Automatic module and function name tracking

### Troubleshooting System

- **System Diagnostics**: Comprehensive health checks
- **Component Status**: Verify all system components
- **Performance Analysis**: Monitor resource usage
- **Error Pattern Detection**: Identify recurring issues
- **Configuration Validation**: Verify settings and dependencies
- **Hardware Detection**: Check available hardware interfaces

## Quick Start

### Initialize Logging

```python
from core.init_logging import initialize_logging

# Initialize at application startup
initialize_logging(
    log_level="INFO",
    log_file=Path("logs/ai_tuner.log"),
    enable_performance=True,
    enable_structured=True,
    colorize=True
)
```

### Using Loggers in Your Modules

```python
from core.logging_config import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Use it
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")
```

### Performance Logging

```python
from core.logging_utils import log_performance_metric, log_execution_time

# Decorator approach
@log_performance_metric("database_query")
def query_database():
    # Your code here
    pass

# Context manager approach
with log_execution_time("data_processing"):
    # Your code here
    process_data()
```

### Error Logging with Context

```python
from core.logging_utils import log_error_with_context

@log_error_with_context(reraise=True, include_traceback=True)
def risky_operation():
    # Your code here
    pass
```

## Advanced Usage

### Custom Log Configuration

```python
from core.logging_config import LoggingConfig, configure_logging, LogLevel

config = LoggingConfig(
    level=LogLevel.DEBUG,
    console_enabled=True,
    file_enabled=True,
    file_path=Path("logs/custom.log"),
    max_file_size_mb=50,
    backup_count=10,
    enable_performance_logging=True,
    enable_structured_logging=True,
    colorize_console=True,
    include_timestamp=True,
    include_module=True,
    include_thread=True,
)

configure_logging(config)
```

### Running Diagnostics

```python
from core.troubleshooter import Troubleshooter, DiagnosticLevel

troubleshooter = Troubleshooter()
diagnostics = troubleshooter.run_diagnostics(DiagnosticLevel.STANDARD)

# Check results
for check in diagnostics.checks:
    print(f"{check.name}: {check.status.value} - {check.message}")
    if check.details:
        print(f"  Details: {check.details}")
```

### Using the Log Viewer UI

```python
from ui.log_viewer import LogViewer

# Create log viewer widget
log_viewer = LogViewer()
log_viewer.set_log_file(Path("logs/ai_tuner.log"))

# Add to your UI
layout.addWidget(log_viewer)
```

### Using the Diagnostics Dialog

```python
from ui.diagnostics_dialog import DiagnosticsDialog

# Create and show diagnostics dialog
dialog = DiagnosticsDialog(parent=self)
dialog.exec()
```

## Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors that may cause system failure

## Log Files

### Main Log File
- Location: `logs/ai_tuner.log`
- Contains: All log messages
- Rotation: 10MB per file, 5 backups

### Performance Log File
- Location: `logs/performance_ai_tuner.log`
- Contains: Performance metrics only
- Format: JSON structured logs

## Environment Variables

You can configure logging via environment variables:

```bash
# Set log level
export AITUNER_LOG_LEVEL=DEBUG

# Enable demo mode (disables network camera scanning)
export AITUNER_DEMO_MODE=true
```

## Best Practices

### 1. Use Appropriate Log Levels

```python
# Good
logger.debug("Processing item %d", item_id)  # Detailed debugging
logger.info("User logged in: %s", username)  # Important events
logger.warning("Low disk space: %d%%", percent)  # Potential issues
logger.error("Failed to connect: %s", error)  # Errors
logger.critical("Database connection lost")  # Critical failures
```

### 2. Include Context

```python
# Good - includes context
logger.error("Failed to save data", extra={
    'user_id': user_id,
    'file_path': file_path,
    'error_code': error_code
})

# Bad - no context
logger.error("Failed to save")
```

### 3. Use Performance Logging for Slow Operations

```python
# Good - track performance
@log_performance_metric("heavy_computation")
def process_large_dataset():
    # Your code
    pass
```

### 4. Log Errors with Full Context

```python
# Good - includes traceback
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True)
```

## Troubleshooting Common Issues

### Issue: Logs not appearing

**Solution**: Check that logging is initialized:
```python
from core.init_logging import initialize_logging
initialize_logging()
```

### Issue: Too many log messages

**Solution**: Adjust log level:
```python
from core.logging_config import set_log_level, LogLevel
set_log_level(LogLevel.WARNING)  # Only warnings and errors
```

### Issue: Log file too large

**Solution**: Adjust rotation settings:
```python
config = LoggingConfig(
    max_file_size_mb=5,  # Smaller files
    backup_count=3,  # Fewer backups
)
```

### Issue: Performance logging not working

**Solution**: Ensure performance logging is enabled:
```python
config = LoggingConfig(enable_performance_logging=True)
configure_logging(config)
```

## Integration Examples

### Adding Logging to a New Module

```python
"""
My New Module

Provides functionality for...
"""

from core.logging_config import get_logger
from core.logging_utils import log_function_call, log_error_with_context

logger = get_logger(__name__)

class MyModule:
    def __init__(self):
        logger.info("Initializing MyModule")
        # Your initialization code
    
    @log_function_call(log_args=False, log_result=False)
    def my_function(self, param1, param2):
        logger.debug("Processing with param1=%s, param2=%s", param1, param2)
        try:
            result = self._do_work(param1, param2)
            logger.info("Function completed successfully")
            return result
        except Exception as e:
            logger.error("Function failed: %s", e, exc_info=True)
            raise
    
    @log_error_with_context()
    def risky_operation(self):
        # This will automatically log errors with context
        pass
```

## Diagnostic Checks

The troubleshooting system performs the following checks:

1. **Python Version**: Verifies Python 3.8+
2. **Dependencies**: Checks required and optional dependencies
3. **File Permissions**: Verifies write access to log/data directories
4. **Disk Space**: Checks available disk space
5. **Memory**: Checks available system memory
6. **CPU**: Monitors CPU usage
7. **Network**: Tests network connectivity
8. **Configuration**: Validates configuration files
9. **Log Files**: Checks log file accessibility
10. **Hardware Interfaces** (comprehensive): Checks serial ports, cameras
11. **Database Connectivity** (comprehensive): Tests SQLite and PostgreSQL
12. **Camera Availability** (comprehensive): Detects available cameras

## Performance Monitoring

The system automatically tracks:

- Function execution times
- Resource usage (memory, CPU)
- Operation durations
- Error rates
- Component health

View performance logs:
```python
from core.logging_config import LoggingManager

manager = LoggingManager()
stats = manager.get_log_statistics()
print(f"Log file size: {stats['log_file_size_mb']:.2f}MB")
```

## Support

For issues or questions about logging and troubleshooting:

1. Check the log files in `logs/`
2. Run diagnostics: `DiagnosticsDialog`
3. Review this documentation
4. Check error messages in the console

