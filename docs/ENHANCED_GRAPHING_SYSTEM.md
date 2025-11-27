# Enhanced Graphing System

## Overview

The Enhanced Telemetry Panel is a cutting-edge graphing interface designed for professional tuners. It provides dynamic sensor selection, advanced configuration options, and professional-grade features.

## Key Features

### 1. Dynamic Sensor Selection
- **Add/Remove Sensors**: Click "➕ Add Sensor" to open the sensor selection dialog
- **Organized by Category**: Sensors are organized into categories:
  - Powertrain (RPM, Speed, Throttle, Boost, etc.)
  - Thermal (Coolant, Oil, EGT, Intake Temp, etc.)
  - Forced Induction (Turbo RPM, Wastegate, Intercooler Temp)
  - Nitrous (Bottle Pressure, Solenoid State, Flow Rate, Temperature)
  - Methanol/Water Injection (Duty Cycle, Tank Level, Flow Rate, Pressure)
  - Fuel System (Flex Fuel %, Fuel Pressure, Injector Duty)
  - Transmission (Trans Brake, Gear, Clutch Position, Temp)
  - Suspension (All four corners)
  - G-Forces & Motion (Lateral, Longitudinal, Gyro, Accel)
  - GPS (Speed, Heading, Altitude, Latitude, Longitude)
  - Electrical (Battery Voltage, Alternator, Current Draw)
  - Braking (Brake Pressure, Brake Temperatures)
  - Other (Knock Count, Density Altitude, Weather)

### 2. Click-to-Configure
- **Click any sensor curve** in the graph to open its settings dialog
- **Right-click** on the graph for context menu (Add Sensor, Reset View, Export)

### 3. Sensor Settings Dialog
Each sensor can be configured with:
- **Basic Settings**:
  - Enable/Disable
  - Color (with color picker)
  - Line Width (1-10px)
  - Line Style (Solid, Dashed, Dotted)
  
- **Scale & Display**:
  - Scale Factor (multiply values)
  - Offset (add/subtract from values)
  - Unit (custom unit label)
  - Y-Axis Index (for multi-axis plotting)
  
- **Value Range**:
  - Min Value (auto or custom)
  - Max Value (auto or custom)
  
- **Alerts & Thresholds**:
  - Alert Below (minimum threshold)
  - Alert Above (maximum threshold)
  - Visual indicators shown as dashed lines
  
- **Data Processing**:
  - Smoothing Level (0-10, moving average)

### 4. Advanced Features

#### Zoom & Pan
- **Zoom Mode**: Click "🔍 Zoom" button, then use mouse wheel to zoom
- **Pan Mode**: Click "✋ Pan" button, then drag to pan
- **Reset View**: Click "↺ Reset View" to return to auto-range

#### Time Range Selection
- **All**: Display all collected data
- **Last 100/500/1000**: Display only recent samples
- **Custom**: (Future: custom time range dialog)

#### Export Data
- **CSV Export**: Export all sensor data as CSV file
- **JSON Export**: Export data with configuration as JSON
- Click "💾 Export" button

#### Legend Panel
- **Sensor List**: Shows all active sensors on the right side
- **Enable/Disable**: Checkbox to toggle sensor visibility
- **Settings Button**: Quick access to sensor configuration (⚙ icon)
- **Color Indicator**: Visual color swatch for each sensor

### 5. Multi-Axis Support
- Assign sensors to different Y-axes (0-3)
- Useful for sensors with different scales (e.g., RPM vs. Temperature)

### 6. Visual Thresholds
- **Min/Max Lines**: Dashed red lines showing value limits
- **Alert Lines**: Dash-dot red lines showing alert thresholds
- Automatically displayed when configured

### 7. Data Smoothing
- Moving average smoothing (0-10 levels)
- Helps reduce noise in sensor readings
- Applied in real-time

## Usage

### Adding Sensors
1. Click "➕ Add Sensor" button
2. Select sensors from the organized categories
3. Use "Quick Add Categories" buttons for common sensor groups
4. Click "OK" to add selected sensors

### Configuring a Sensor
1. **Method 1**: Click directly on the sensor's curve in the graph
2. **Method 2**: Click the ⚙ button next to the sensor in the legend
3. Adjust settings in the dialog
4. Click "Apply" to see changes immediately, or "OK" to apply and close

### Managing Sensors
- **Enable/Disable**: Use checkbox in legend
- **Remove**: Remove from selection in sensor selection dialog
- **Reorder**: (Future: drag-and-drop in legend)

### Exporting Data
1. Click "💾 Export" button
2. Choose file location and format (CSV or JSON)
3. Data is exported with all sensor values and configurations

## Configuration Persistence

- Sensor selections and configurations are automatically saved to `~/.aituner/telemetry_config.json`
- Settings persist between application sessions
- Can be manually edited if needed

## Technical Details

### Sensor Aliases
The system supports extensive sensor name aliases for compatibility:
- Handles different naming conventions (CamelCase, snake_case, etc.)
- Supports common abbreviations (RPM, TPS, EGT, IAT, etc.)
- Case-insensitive matching

### Performance
- Efficient deque-based data storage (configurable max length, default 1000)
- Smooth real-time updates
- Optimized rendering with pyqtgraph

### Integration
- Drop-in replacement for basic TelemetryPanel
- Compatible with existing DataStreamController
- Automatically detects available sensors from telemetry data

## Future Enhancements

Potential additions:
- Drag-and-drop sensor reordering
- Custom calculated channels (formulas)
- Run/lap comparison overlay
- Statistical analysis (min/max/avg/std dev)
- Data replay from logs
- Custom time range dialog
- Multiple graph tabs
- Graph templates/presets
- Real-time alerts/notifications
- Data correlation analysis

## Troubleshooting

### Sensors Not Appearing
- Ensure sensor data is being generated (check data stream)
- Sensor names must match available telemetry keys
- Check sensor selection dialog for available sensors

### Click Not Working
- Ensure pyqtgraph is installed: `pip install pyqtgraph`
- Try clicking directly on the curve line
- Use the ⚙ button in legend as alternative

### Performance Issues
- Reduce time range (Last 100 instead of All)
- Disable unused sensors
- Reduce smoothing level
- Lower max data length if needed

