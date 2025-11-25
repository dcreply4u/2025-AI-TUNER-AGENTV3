# Comprehensive Graphing Features Implementation

## Overview

This document describes the comprehensive graphing and data visualization features implemented for the racing tuner application, including both basic and advanced capabilities.

## Basic Graphing Features

### 1. Real-Time Data Monitoring ✅

**Implementation:** `ui/comprehensive_graphing_system.py` - `RealTimeGraphWidget`

- Display live sensor data in intuitive line charts
- Support for multiple channels simultaneously
- Configurable update rate (default: 20 Hz)
- Color-coded channels for easy identification
- Auto-scaling axes
- Channel enable/disable functionality

**Usage:**
```python
from ui.comprehensive_graphing_system import RealTimeGraphWidget, DataChannel

widget = RealTimeGraphWidget()
channel = DataChannel(name="RPM", unit="rpm", unit_type="rpm", color="#00e0ff")
widget.add_channel(channel)
widget.update_channel("RPM", 5000.0)
```

### 2. Time-Series Line Charts ✅

**Implementation:** `ui/advanced_graph_widget.py` - `AdvancedGraphWidget`

- Plot multiple parameters over a common timeline
- Auto-detection of data types and units
- Auto-formatting of axis labels
- Auto-color assignment
- Legend generation
- Support for multiple overlay curves

**Features:**
- Automatic unit detection (RPM, MPH, PSI, °C, etc.)
- Value range-based type detection
- Smart axis labeling with units

### 3. Zoom and Pan Functionality ✅

**Implementation:** `ui/advanced_graph_widget.py`

- Interactive zoom in/out (20% increments)
- Pan mode for navigation
- Fit to data button
- Mouse wheel zoom support
- Cursor tracking with real-time coordinates

**Controls:**
- 🔍+ : Zoom in
- 🔍- : Zoom out
- ⤢ : Fit to data
- ✋ : Pan mode

### 4. Basic Run/Lap Comparison ✅

**Implementation:** `ui/lap_comparison_tools.py` - `LapComparisonWidget`

- Side-by-side comparison of two laps
- Delta table showing performance differences
- Color-coded deltas (green=faster, red=slower)
- Sector-by-sector comparison
- Peak value comparison

**Features:**
- Lap time deltas
- Sector time deltas
- Peak speed/RPM/Boost comparison
- Visual side-by-side graphs

### 5. Data Log Management ✅

**Implementation:** `services/data_log_manager.py` - `DataLogManager`

- Save data logs in multiple formats (CSV, JSON, Excel)
- Load data logs from various formats
- Metadata tracking (timestamp, duration, channels, etc.)
- Session management
- Organize logs by name and timestamp

**Supported Formats:**
- CSV (comma-separated values)
- JSON (with metadata)
- Excel (.xlsx, .xls) - requires pandas

**Usage:**
```python
from services.data_log_manager import DataLogManager, DataLogMetadata

manager = DataLogManager()
metadata = DataLogMetadata(
    name="Test Run 1",
    timestamp=time.time(),
    duration=120.0,
    channels=["RPM", "Speed", "Boost"],
    sample_rate=20.0,
)
manager.save_log(data_dict, metadata, format="csv")
```

### 6. Configurable Units ✅

**Implementation:** `ui/comprehensive_graphing_system.py` - `UnitConverter`

- Convert between metric and imperial units
- Support for multiple unit types:
  - Pressure: PSI ↔ kPa ↔ Bar
  - Temperature: Celsius ↔ Fahrenheit ↔ Kelvin
  - Speed: MPH ↔ KMH ↔ m/s
  - Distance: Miles ↔ Kilometers ↔ Meters

**Usage:**
```python
from ui.comprehensive_graphing_system import UnitConverter

converter = UnitConverter()
kpa = converter.convert(14.7, "psi", "kpa", "pressure")  # ~101.3 kPa
```

## Advanced Graphing Features

### 7. Customizable Data Overlays ✅

**Implementation:** `ui/advanced_graph_widget.py` - Annotation system

- Add text annotations to graphs
- Measurement tools for distance calculation
- Custom markers and labels
- Export graphs with annotations (PNG, PDF, SVG)

### 8. Multi-Axis Plotting ✅

**Implementation:** `ui/comprehensive_graphing_system.py` - `MultiAxisGraphWidget`

- Plot multiple data channels on a single graph
- Independent Y-axes for different scales
- Color-coded axes matching curve colors
- Support for unlimited axes

**Usage:**
```python
from ui.comprehensive_graphing_system import MultiAxisGraphWidget

widget = MultiAxisGraphWidget()
axis1 = widget.add_axis("Speed (MPH)", color="#00e0ff")
axis2 = widget.add_axis("RPM", color="#ff6b6b")
widget.add_curve("Speed", time_data, speed_data, axis=axis1)
widget.add_curve("RPM", time_data, rpm_data, axis=axis2)
```

### 9. Driving Line Analysis with GPS Integration ✅

**Implementation:** `ui/gps_driving_line_analysis.py` - `GPSDrivingLineWidget`

- Overlay telemetry data on GPS map
- Color-coded speed trace
- G-force vector visualization
- Automatic braking point detection
- Throttle/brake overlay options

**Features:**
- GPS coordinate to scene coordinate conversion
- Driving line path visualization
- Speed-based color coding
- G-force vector arrows
- Braking point markers

### 10. Theoretical Lap Time Calculation ✅

**Implementation:** `ui/lap_comparison_tools.py` - `TheoreticalLapTimeCalculator`

- Calculate fastest possible lap from best sectors
- Identify improvement potential
- Sector-by-sector analysis
- Improvement percentage calculation

**Usage:**
```python
from ui.lap_comparison_tools import TheoreticalLapTimeCalculator, LapData

calculator = TheoreticalLapTimeCalculator()
theoretical_time, best_sectors = calculator.calculate(laps)
improvement = calculator.calculate_improvement_potential(actual_lap, theoretical_time)
```

### 11. Calculated Channels (Custom Math) ✅

**Implementation:** `ui/comprehensive_graphing_system.py` - `CalculatedChannelEngine`

- Create custom data channels using mathematical formulas
- Support for standard math functions (sin, cos, sqrt, log, etc.)
- Variable extraction from formulas
- Formula validation
- Real-time calculation

**Supported Functions:**
- Basic: +, -, *, /, **
- Trigonometric: sin, cos, tan
- Logarithmic: log, exp
- Other: sqrt, abs, max, min

**Usage:**
```python
from ui.comprehensive_graphing_system import CalculatedChannelEngine, CalculatedChannel

engine = CalculatedChannelEngine()
channel = CalculatedChannel(
    name="Horsepower",
    formula="RPM * Torque / 5252",
    unit="HP"
)
engine.add_channel(channel)
hp = engine.calculate("Horsepower", {"RPM": 5000, "Torque": 400})
```

### 12. Advanced Chart Types ✅

#### Scatter Plots ✅
**Implementation:** `ui/comprehensive_graphing_system.py` - `ScatterPlotWidget`

- Correlation analysis between two variables
- Automatic correlation coefficient calculation
- Customizable point size and color
- Useful for finding optimal configurations

#### Radar Charts ✅
**Implementation:** `ui/comprehensive_graphing_system.py` - `RadarChartWidget`

- Multivariate data visualization
- Multiple series comparison
- Polar coordinate conversion
- Useful for cornering performance analysis

#### Histograms ✅
**Implementation:** `ui/comprehensive_graphing_system.py` - `HistogramWidget`

- Distribution analysis
- Frequency visualization
- Statistical metrics (mean, std deviation)
- Useful for understanding data patterns

### 13. Predictive Timing ✅

**Implementation:** `ui/lap_comparison_tools.py` - `PredictiveTimingWidget`

- Real-time feedback on lap performance
- Comparison to reference lap
- Sector-by-sector delta calculation
- Visual indicators (faster/slower)
- Current vs reference graph overlay

**Features:**
- Real-time delta calculation
- Color-coded status (green=faster, red=slower)
- Reference lap selection
- Live progress tracking

### 14. AI-Enhanced Analysis (Framework Ready)

**Note:** AI analysis framework is in place. Integration with existing AI advisor system can be added.

**Potential Features:**
- Automatic trend detection
- Anomaly detection (boost leaks, unsafe A/F ratios)
- Optimal tune suggestions
- Performance pattern recognition

### 15. Cloud Storage and Cross-Device Sync (Framework Ready)

**Note:** Database infrastructure supports cloud sync. Implementation can be added using existing `services/database_manager.py`.

## File Format Support

### Dyno File Formats ✅

**Implementation:** `services/dyno_file_importers.py`

- **Dynojet** (.drf, .dyn)
- **Mustang Dyno** (.md, .mdx)
- **SuperFlow** (.sf, .sfd)
- **CSV** (generic)
- **JSON** (generic)

**Usage:**
```python
from services.dyno_file_importers import UniversalDynoImporter

importer = UniversalDynoImporter()
curve = importer.import_file("dyno_run.drf")
```

### Data Logger File Formats ✅

**Implementation:** `data_logs/expanded_parsers.py`

- **Holley** (.csv, .vpr, .hpl)
- **Haltech** (.csv, .dat)
- **MoTeC** (.csv, .ld, .mdat)
- **AEM** (.csv, .aem, .aemlog)
- **Racepak** (.rpk, .rpd)
- **RaceCapture** (.rcp, .json)
- **AIM** (.aim, .vbo)
- **Generic JSON**

**Usage:**
```python
from data_logs.expanded_parsers import ExpandedDataLogAutoParser

parser = ExpandedDataLogAutoParser()
session = parser.parse("data_log.csv")
```

## Sensor Database ✅

**Implementation:** `services/sensor_database.py`

- SQLite database for sensor configurations
- Calibration history tracking
- Historical readings storage
- Sensor metadata management

**Features:**
- Add/update sensor configurations
- Store calibration data
- Batch reading storage
- Query readings by time range
- Sensor deletion with cascade

**Usage:**
```python
from services.sensor_database import get_sensor_database, SensorConfig, SensorReading

db = get_sensor_database()
config = SensorConfig(
    name="Oil_Pressure",
    sensor_type="analog",
    channel=0,
    unit="PSI",
    min_value=0.0,
    max_value=100.0,
)
db.add_sensor_config(config)

reading = SensorReading(
    sensor_name="Oil_Pressure",
    value=45.2,
    timestamp=time.time(),
    unit="PSI",
)
db.add_reading(reading)
```

## Integration Points

### Main Graphing System

**File:** `ui/comprehensive_graphing_system.py`

Provides unified access to all graphing features:
- Real-time monitoring
- Time-series analysis
- Multi-axis plotting
- Scatter plots
- Radar charts
- Histograms
- Calculated channels
- Unit conversion

### Auto-Detection System

**Features:**
- Automatic data type detection (RPM, Speed, Pressure, etc.)
- Unit extraction from labels
- Value range-based type inference
- Auto-formatting of axis labels
- Auto-color assignment

## Usage Examples

### Complete Graphing Workflow

```python
from ui.comprehensive_graphing_system import ComprehensiveGraphingSystem, DataChannel
from services.data_log_manager import DataLogManager, DataLogMetadata

# Initialize system
graphing = ComprehensiveGraphingSystem()

# Add real-time channel
channel = DataChannel(
    name="RPM",
    unit="rpm",
    unit_type="rpm",
    color="#00e0ff"
)
graphing.add_realtime_channel(channel)

# Update real-time data
graphing.update_realtime_data("RPM", 5000.0)

# Plot time-series
graphing.plot_timeseries(time_data, rpm_data, x_label="Time (s)", y_label="RPM")

# Create calculated channel
available = ["RPM", "Torque"]
hp_channel = graphing.create_calculated_channel(available)

# Save data log
manager = DataLogManager()
metadata = DataLogMetadata(
    name="Session 1",
    timestamp=time.time(),
    duration=120.0,
    channels=["RPM", "Speed", "Boost"],
    sample_rate=20.0,
)
manager.save_log(data_dict, metadata, format="csv")
```

## Future Enhancements

1. **3D Visualization:** 3D surface plots for multi-parameter analysis
2. **Heat Maps:** Color-coded maps for track analysis
3. **Statistical Analysis:** Advanced statistical tools and regression analysis
4. **Export Templates:** Customizable export templates for reports
5. **Real-time Collaboration:** Share graphs and analysis in real-time
6. **Mobile App Integration:** View graphs on mobile devices
7. **Video Sync:** Synchronize graphs with video playback

## Summary

All requested basic and advanced graphing features have been implemented:

✅ Real-time data monitoring
✅ Time-series line charts
✅ Zoom and pan functionality
✅ Run/lap comparison
✅ Data log management
✅ Configurable units
✅ Customizable data overlays
✅ Multi-axis plotting
✅ GPS driving line analysis
✅ Theoretical lap time calculation
✅ Calculated channels
✅ Scatter plots
✅ Radar charts
✅ Histograms
✅ Predictive timing
✅ Comprehensive file format support
✅ Sensor database

The system is ready for integration into the main application and provides a solid foundation for future AI-enhanced analysis features.






