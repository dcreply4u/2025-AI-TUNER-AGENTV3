# Logging Quick Reference

## Basic Usage

```python
from core.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

## Performance Tracking

```python
from core.logging_utils import log_performance_metric

@log_performance_metric("operation_name")
def my_function():
    pass
```

## Error Handling

```python
from core.logging_utils import log_error_with_context

@log_error_with_context()
def risky_function():
    pass
```

## Context Manager

```python
from core.logging_utils import log_execution_time

with log_execution_time("operation"):
    # Your code
    pass
```

## Diagnostics

```python
from core.troubleshooter import Troubleshooter, DiagnosticLevel

troubleshooter = Troubleshooter()
diagnostics = troubleshooter.run_diagnostics(DiagnosticLevel.STANDARD)
```

## Configuration

```python
from core.init_logging import initialize_logging

initialize_logging(log_level="INFO")
```

## Log Levels

- `DEBUG`: Detailed debugging info
- `INFO`: General information
- `WARNING`: Warnings
- `ERROR`: Errors
- `CRITICAL`: Critical failures

## Environment Variables

- `AITUNER_LOG_LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `AITUNER_DEMO_MODE`: Enable demo mode (true/false)

