# Performance Optimization Guide

## Overview

The AI Tuner Agent now includes comprehensive performance optimizations to ensure:
- **Snappy UI** - No lag when switching screens/menus
- **Low Memory Usage** - Automatic cleanup and memory management
- **Low Disk Usage** - Automatic compression and cleanup of old files
- **Fast Database** - Optimized queries and indexing

## Quick Integration

### 1. Initialize Resource Optimizer in Main Window

```python
from core import ResourceOptimizer

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # Initialize resource optimizer
        self.resource_optimizer = ResourceOptimizer(parent=self)
        
        # Connect signals for notifications
        self.resource_optimizer.memory_warning.connect(self._on_memory_warning)
        self.resource_optimizer.disk_warning.connect(self._on_disk_warning)
        
        # Optimize this window
        self.resource_optimizer.optimize_ui_widget(self)
```

### 2. Use Lazy Loading for Heavy Widgets

```python
from core import UIOptimizer

# Register widgets for lazy loading
self.resource_optimizer.register_lazy_widget(
    "camera_view",
    CameraView,
    parent=self
)

# Load only when needed
def show_camera_view(self):
    widget = self.resource_optimizer.get_lazy_widget("camera_view")
    if widget:
        # Add to layout or show
        pass
```

### 3. Use Debounce/Throttle for Expensive Operations

```python
from core import debounce, throttle

@throttle(0.1)  # Max once per 100ms
def update_telemetry_display(self, data):
    # Expensive UI update
    pass

@debounce(0.5)  # Wait 500ms after last call
def search_function(self, query):
    # Expensive search operation
    pass
```

### 4. Optimize Data Loading

```python
from core import EfficientDataModel

class TelemetryModel(EfficientDataModel):
    def _load_page(self, page):
        # Load only one page at a time
        offset = page * self.page_size
        return self.db.query_telemetry(limit=self.page_size, offset=offset)
```

## Automatic Optimizations

The system automatically:
- **Cleans memory** every 30 seconds if usage > 80%
- **Cleans disk** every 5 minutes if usage > 90%
- **Compresses old logs** after 7 days
- **Deletes old files** after 30 days (configurable)
- **Optimizes database** periodically
- **Unloads unused widgets** automatically

## Manual Optimization

```python
# Force immediate cleanup
results = self.resource_optimizer.force_cleanup()

# Get statistics
memory_stats = self.resource_optimizer.get_memory_stats()
disk_stats = self.resource_optimizer.get_disk_stats()
perf_stats = self.resource_optimizer.get_performance_stats()
```

## Best Practices

1. **Use lazy loading** for screens that aren't always visible
2. **Debounce/throttle** expensive operations (search, filtering)
3. **Paginate data** instead of loading everything at once
4. **Clean up** event handlers and timers in `closeEvent`
5. **Use weak references** for callbacks to prevent memory leaks

## Configuration

Adjust thresholds in `ResourceOptimizer`:
- `max_memory_mb`: Maximum memory (default: 512 MB)
- `cleanup_threshold`: Cleanup trigger (default: 80%)
- `retention_days`: Keep data for N days (default: 30)

## Monitoring

Check resource usage:
```python
# Memory
stats = resource_optimizer.get_memory_stats()
print(f"Memory: {stats['rss_mb']:.1f} MB ({stats['percent']:.1f}%)")

# Disk
stats = resource_optimizer.get_disk_stats()
print(f"Disk: {stats['used_gb']:.1f} GB / {stats['total_gb']:.1f} GB")
```
