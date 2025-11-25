# RAM Requirements for AI Tuner Application

## Current RAM Requirements

### Minimum Requirements
- **Minimum RAM**: 512 MB
- **Recommended RAM**: 1 GB
- **Optimal RAM**: 2 GB or more

### Memory Usage Breakdown

#### Base Application Components
| Component | Estimated RAM Usage |
|-----------|-------------------|
| Python 3.8+ Runtime | 30-50 MB |
| PySide6 (Qt6 UI Framework) | 80-120 MB |
| PyQtGraph (Real-time Graphing) | 40-60 MB |
| NumPy/Pandas (Data Processing) | 50-80 MB |
| OpenCV (Video/Image Processing) | 40-60 MB |
| Scikit-learn (ML/AI Features) | 50-80 MB |
| Other Dependencies | 30-50 MB |
| **Subtotal (Base Libraries)** | **320-500 MB** |

#### Application Code & Data Structures
| Component | Estimated RAM Usage |
|-----------|-------------------|
| Application Code (Python modules) | 20-40 MB |
| UI Widgets & Rendering | 30-50 MB |
| Telemetry Data Buffers | 5-15 MB |
| Database (SQLite) | 10-30 MB |
| Logging System | 5-15 MB |
| Configuration & State | 5-10 MB |
| **Subtotal (Application)** | **75-175 MB** |

#### Runtime Data
| Component | Estimated RAM Usage |
|-----------|-------------------|
| Active Telemetry Data (400 points × 10 channels) | ~5 MB |
| Graph Rendering Buffers | 10-20 MB |
| Image/Video Buffers (if active) | 20-50 MB |
| AI Model Inference (if active) | 20-50 MB |
| **Subtotal (Runtime)** | **55-125 MB** |

### Total Memory Usage

#### Typical Operation (Idle/Demo Mode)
- **Base**: 320-500 MB
- **Application**: 75-175 MB
- **Runtime (Minimal)**: 55-75 MB
- **Total**: **450-750 MB**

#### Active Operation (Full Features)
- **Base**: 320-500 MB
- **Application**: 75-175 MB
- **Runtime (Full)**: 100-125 MB
- **Total**: **495-800 MB**

#### Peak Usage (All Features Active)
- **Base**: 320-500 MB
- **Application**: 75-175 MB
- **Runtime (Peak)**: 125-200 MB
- **Total**: **520-875 MB**

## Memory Management Features

### Automatic Memory Optimization
The application includes built-in memory management:

1. **Memory Manager** (Default: 512 MB max)
   - Automatic cleanup when usage exceeds 80%
   - Garbage collection every 30 seconds
   - Weak references for automatic cleanup

2. **Memory Optimizer** (Target: 200 MB)
   - Aggressive cleanup for lightweight operation
   - Cache size limits (100 items max)
   - Automatic object cleanup

3. **Circular Buffers**
   - Telemetry data: 400 points max per channel
   - Automatic old data removal
   - Fixed-size buffers prevent memory growth

4. **Resource Optimizer**
   - Monitors memory usage
   - Automatic cleanup at 80% threshold
   - Log compression after 7 days
   - Old file deletion after 30 days

### Buffer Sizes
- **Telemetry Panel**: 400 data points per channel (10 channels) = ~32 KB
- **Local Buffer**: 10,000 entries max (SQLite-based, disk-backed)
- **Graph Rendering**: Real-time, limited to visible window
- **Logging**: Rotating logs with size limits

## Platform-Specific Requirements

### Raspberry Pi 5
- **Minimum**: 1 GB RAM (512 MB may work but tight)
- **Recommended**: 2 GB RAM
- **Optimal**: 4 GB RAM or more

### Windows Desktop
- **Minimum**: 2 GB RAM
- **Recommended**: 4 GB RAM
- **Optimal**: 8 GB RAM or more

### Linux Desktop
- **Minimum**: 1 GB RAM
- **Recommended**: 2 GB RAM
- **Optimal**: 4 GB RAM or more

## Memory Optimization Tips

### For Low-RAM Systems (< 1 GB)
1. Disable video processing features
2. Reduce telemetry buffer size (change `max_len` from 400 to 200)
3. Disable AI/ML features if not needed
4. Use lighter UI theme
5. Close unused tabs/modules
6. Enable aggressive memory cleanup

### Configuration Adjustments
```python
# Reduce telemetry buffer size
TelemetryPanel(max_len=200)  # Instead of 400

# Reduce memory manager threshold
MemoryManager(max_memory_mb=256.0)  # Instead of 512 MB

# Enable aggressive cleanup
memory_optimizer.start()
```

## Monitoring Memory Usage

### Check Current Usage
```python
from core.memory_manager import MemoryManager

mm = MemoryManager()
usage = mm.get_memory_usage()
print(f"Memory: {usage['rss_mb']:.1f} MB ({usage['percent']:.1f}%)")
```

### Force Cleanup
```python
# Manual cleanup
result = mm.cleanup(aggressive=True)
print(f"Freed: {result['freed_mb']:.1f} MB")
```

## Recommendations

### For Production Use
- **Minimum**: 1 GB RAM
- **Recommended**: 2 GB RAM
- **With Video Processing**: 4 GB RAM
- **With Full AI Features**: 4-8 GB RAM

### For Development/Testing
- **Minimum**: 2 GB RAM
- **Recommended**: 4 GB RAM
- **Optimal**: 8 GB RAM or more

## Memory Leak Prevention

The application includes:
- Automatic garbage collection
- Weak references for callbacks
- Circular buffers (fixed size)
- Resource cleanup on widget close
- Memory monitoring and alerts
- Automatic cleanup when thresholds exceeded

## Summary

**Current RAM Requirements:**
- **Absolute Minimum**: 512 MB (may be tight)
- **Practical Minimum**: 1 GB (comfortable operation)
- **Recommended**: 2 GB (optimal performance)
- **With All Features**: 4 GB (video, AI, full features)

The application is designed to run efficiently on resource-constrained devices like Raspberry Pi 5 (1-2 GB RAM) while also scaling up for more powerful systems.



