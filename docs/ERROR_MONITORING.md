# Error Monitoring Service

A robust, lightweight service for continuous runtime error monitoring in the racing tuner app. Provides real-time error detection, detailed diagnostics, resource monitoring, and comprehensive analysis.

## Features

### Core Capabilities

- **Real-Time Error Detection**: Automatically detects and captures all runtime errors
- **Detailed Diagnostics**: Full stack traces, file paths, line numbers, function names
- **Contextual Information**: Breadcrumbs track user actions leading to errors
- **Error Prioritization**: Automatic categorization by severity and impact
- **Resource Monitoring**: CPU, memory, disk I/O, network usage at time of error
- **Session Tracking**: Correlate errors with user sessions
- **Terminal Output**: Real-time feedback with progress indicators
- **Lightweight**: Minimal performance impact, runs in background thread

### Advanced Features

- **Error Deduplication**: Groups duplicate errors by signature
- **Impact Analysis**: Tracks frequency, affected users, recovery success rates
- **Export Capabilities**: Export error reports to JSON for analysis
- **Alert System**: Callbacks for high-priority error notifications
- **Statistics**: Comprehensive error statistics and trends

## Architecture

The error monitoring service is designed to be:

1. **Non-Intrusive**: Runs in a background daemon thread with minimal overhead
2. **Integrated**: Automatically hooks into the existing `ErrorHandler`
3. **Extensible**: Callback system for custom error handling
4. **Efficient**: Buffers errors in memory, processes asynchronously

## Usage

### Basic Usage

The error monitoring service automatically starts when imported and integrated:

```python
from services.error_monitoring_service import get_error_monitor

# Get the global error monitor instance
monitor = get_error_monitor()

# Start monitoring (if not already started)
monitor.start()

# The service will automatically capture errors from ErrorHandler
```

### Integration with Application

The service integrates automatically with the existing `ErrorHandler`:

```python
from core.error_handler import get_error_handler
from services.error_monitoring_service import get_error_monitor

# Error handler automatically notifies error monitor
error_handler = get_error_handler()
monitor = get_error_monitor()
monitor.start()

# Any errors handled by ErrorHandler will be automatically captured
```

### Adding Breadcrumbs

Track user actions leading to errors:

```python
from services.error_monitoring_service import get_error_monitor

monitor = get_error_monitor()

# Add breadcrumb when user performs action
monitor.add_breadcrumb(
    action="load_ecu_config",
    component="ECUControl",
    data={"config_file": "tune.json", "ecu_type": "Holley"}
)
```

### Custom Error Callbacks

Register callbacks for error notifications:

```python
from services.error_monitoring_service import ErrorReport, get_error_monitor

def on_error_detected(report: ErrorReport):
    print(f"Error detected: {report.error_type} in {report.component}")
    # Send to external service, log to database, etc.

monitor = get_error_monitor()
monitor.register_error_callback(on_error_detected)
monitor.start()
```

### Alert Callbacks

Register callbacks for high-priority errors:

```python
def on_critical_error(report: ErrorReport):
    if report.priority == ErrorPriority.CRITICAL:
        # Send alert, notify team, etc.
        send_alert_email(report)

monitor = get_error_monitor()
monitor.register_alert_callback(on_critical_error)
monitor.start()
```

## CLI Tool

### Real-Time Monitoring

Watch for errors in real-time with live updates:

```bash
# Watch mode (default)
python tools/monitor_errors.py

# With custom refresh interval
python tools/monitor_errors.py --watch --refresh 1.0

# Without rich terminal output
python tools/monitor_errors.py --no-rich
```

### Error Analysis

Analyze errors and display comprehensive report:

```bash
python tools/monitor_errors.py --analyze
```

### Export Errors

Export errors to JSON file for external analysis:

```bash
python tools/monitor_errors.py --export errors.json
```

## Error Report Structure

Each error report contains comprehensive diagnostic information:

```python
@dataclass
class ErrorReport:
    # Error identification
    error_id: str                    # Unique error ID (hash)
    error_type: str                  # Exception type name
    error_message: str               # Error message
    severity: ErrorSeverity          # LOW, MEDIUM, HIGH, CRITICAL
    priority: ErrorPriority         # LOW, MEDIUM, HIGH, CRITICAL
    
    # Timing
    timestamp: float                 # When error occurred
    first_occurrence: float          # First time this error occurred
    occurrence_count: int            # How many times this error occurred
    
    # Location
    component: str                   # Component where error occurred
    file_path: Optional[str]         # Source file path
    line_number: Optional[int]       # Line number
    function_name: Optional[str]    # Function/class name
    
    # Diagnostics
    stack_trace: str                 # Full stack trace
    traceback_lines: List[str]       # Stack trace as list
    environment: Dict[str, Any]      # Environment info (platform, Python version, etc.)
    
    # Context
    breadcrumbs: List[Breadcrumb]    # User actions leading to error
    resource_snapshot: Optional[ResourceSnapshot]  # System resources at time of error
    session_id: Optional[str]        # User session ID
    user_id: Optional[str]           # User ID (if available)
    
    # Impact
    affected_users: int              # Number of users affected
    frequency_per_hour: float         # Error frequency
    
    # Recovery
    recovery_attempted: bool         # Whether recovery was attempted
    recovery_successful: bool         # Whether recovery succeeded
    
    # Additional data
    metadata: Dict[str, Any]          # Custom metadata
```

## Resource Monitoring

The service captures system resource snapshots when errors occur:

```python
@dataclass
class ResourceSnapshot:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    process_count: int
    thread_count: int
```

## Statistics

Get comprehensive error statistics:

```python
monitor = get_error_monitor()
stats = monitor.get_statistics()

# Returns:
# {
#     "total_errors": 150,
#     "errors_by_severity": {
#         "critical": 5,
#         "high": 20,
#         "medium": 100,
#         "low": 25
#     },
#     "errors_by_component": {
#         "ECUControl": 50,
#         "CANInterface": 30,
#         ...
#     },
#     "errors_by_type": {
#         "ConnectionError": 10,
#         "ValueError": 5,
#         ...
#     },
#     "recovery_success_rate": 0.85,
#     "average_errors_per_hour": 12.5
# }
```

## Error Analysis

Get comprehensive error analysis:

```python
monitor = get_error_monitor()
analysis = monitor.get_error_analysis()

# Returns:
# {
#     "statistics": {...},
#     "top_errors": [
#         {
#             "error_id": "...",
#             "occurrence_count": 25,
#             "report": {...}
#         },
#         ...
#     ],
#     "total_unique_errors": 50,
#     "session_count": 3
# }
```

## Configuration

Configure the error monitoring service:

```python
from services.error_monitoring_service import ErrorMonitoringService

monitor = ErrorMonitoringService(
    enable_terminal_output=True,      # Show real-time terminal output
    enable_resource_monitoring=True,   # Monitor system resources (requires psutil)
    enable_breadcrumbs=True,          # Track user actions
    max_breadcrumbs=100,              # Maximum breadcrumbs per session
    resource_check_interval=1.0,       # Resource check interval (seconds)
    error_buffer_size=1000,            # Maximum errors to keep in memory
    session_timeout=3600.0,             # Session timeout (seconds)
)

monitor.start()
```

## Dependencies

### Required

- Python 3.9+
- `core.error_handler` (existing error handling system)

### Optional

- `psutil` - For resource monitoring (CPU, memory, disk, network)
- `rich` - For enhanced terminal output in CLI tool

Install optional dependencies:

```bash
pip install psutil rich
```

## Performance Considerations

The error monitoring service is designed to be lightweight:

- **Background Thread**: Runs in daemon thread, doesn't block main application
- **Asynchronous Processing**: Errors are queued and processed asynchronously
- **Memory Management**: Limits error history to prevent memory leaks
- **Minimal Overhead**: Resource monitoring uses minimal CPU (checks every 1 second by default)

## Best Practices

1. **Start Early**: Start the monitor at application startup
2. **Add Breadcrumbs**: Track important user actions
3. **Use Callbacks**: Register callbacks for critical errors
4. **Export Regularly**: Export error reports for analysis
5. **Monitor Resources**: Enable resource monitoring to identify performance issues

## Integration Example

Complete integration example:

```python
from core.init_logging import initialize_logging
from core.error_handler import get_error_handler
from services.error_monitoring_service import get_error_monitor

# Initialize logging
initialize_logging()

# Get error handler and monitor
error_handler = get_error_handler()
monitor = get_error_monitor()

# Configure monitor
monitor.enable_terminal_output = True
monitor.enable_resource_monitoring = True
monitor.enable_breadcrumbs = True

# Start monitoring
monitor.start()

# Add breadcrumb when user performs action
monitor.add_breadcrumb(
    action="start_tuning_session",
    component="MainWindow",
    data={"session_type": "dyno"}
)

# Application continues normally
# All errors will be automatically captured and monitored
```

## Troubleshooting

### Monitor Not Starting

If the monitor doesn't start:

```python
monitor = get_error_monitor()
if not monitor.running:
    monitor.start()
    print(f"Monitor started: {monitor.running}")
```

### No Errors Being Captured

Ensure the error handler is being used:

```python
from core.error_handler import get_error_handler, handle_errors

# Use error handler decorator
@handle_errors(component="MyComponent")
def my_function():
    # This will automatically be monitored
    pass

# Or manually handle errors
error_handler = get_error_handler()
try:
    # code
except Exception as e:
    error_handler.handle_error(e, component="MyComponent")
```

### Resource Monitoring Not Working

Install `psutil`:

```bash
pip install psutil
```

Or disable resource monitoring:

```python
monitor = get_error_monitor()
monitor.enable_resource_monitoring = False
```

## Future Enhancements

Potential future enhancements:

- Integration with external error tracking services (Sentry, Rollbar)
- Machine learning for error pattern detection
- Predictive error prevention
- Real-time dashboards
- Email/SMS alerts for critical errors
- Error correlation analysis
- Performance regression detection

---

**Last Updated**: December 2024

