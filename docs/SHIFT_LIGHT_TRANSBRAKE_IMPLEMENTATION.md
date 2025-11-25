# Advanced Shift Light & Transbrake Implementation

## Overview

This document details the implementation of advanced shift light and transbrake features for the racing tuner app.

## ✅ Features Implemented

### Advanced Shift Light Support

1. **Customizable RPM Thresholds**
   - Individual LED configuration with specific RPM thresholds
   - Different colors per LED (Green, Yellow, Orange, Red, Blue)
   - Configurable flash modes (Solid, Slow, Medium, Fast, Very Fast)
   - Brightness control per LED

2. **Gear-Dependent Settings**
   - Automatic adjustment of shift points based on current gear
   - Different optimal RPM, max RPM, start RPM, and peak RPM per gear
   - Configurable shift points for each gear (1-6+)

3. **Data Logging and Analysis**
   - Real-time logging of shift events
   - Reaction time measurement (time from peak shift light to actual shift)
   - Optimal shift detection (within 200 RPM of optimal)
   - Shift analysis statistics (average reaction time, optimal shift percentage)

4. **Predictive Lap Timing Integration**
   - Integration with lap timing system
   - Green LEDs for improving lap time
   - Red LEDs for falling behind
   - Configurable threshold for predictive timing

5. **External Hardware Connectivity**
   - CAN bus support for external shift light modules
   - Bluetooth support (framework ready)
   - Auto-detection of external hardware

### Advanced Transbrake Support

1. **Adjustable Launch Parameters**
   - Target RPM configuration
   - Boost pressure control (for turbo/supercharged)
   - Timing advance adjustment
   - Enable/disable boost and timing control

2. **Staging Control ("Bump" and "Creep")**
   - Manual, Bump, and Creep modes
   - Configurable duty cycle and frequency for bump mode
   - Configurable duty cycle and frequency for creep mode
   - Maximum staging time safety timeout

3. **Clutch Slip/Torque Converter Control**
   - Enable/disable slip control
   - Target slip RPM configuration
   - Slip table (time-based slip RPM)
   - Maximum slip time
   - Release threshold RPM

4. **Integrated Safety Features**
   - Coolant temperature limits
   - Transmission temperature limits
   - Maximum launch time
   - Minimum battery voltage
   - Automatic transbrake release on safety violation

5. **Data Analysis**
   - Launch event logging
   - G-force tracking (peak and 60-foot)
   - Wheel speed at 60-foot
   - 60-foot time measurement
   - Launch analysis statistics

## 📁 Files Created

### Core Services

1. **`services/shift_light_manager.py`**
   - `ShiftLightManager` - Main shift light manager
   - `ShiftLightConfig` - Configuration dataclass
   - `LEDConfig` - Individual LED configuration
   - `GearShiftPoint` - Gear-specific shift points
   - `ShiftEvent` - Shift event record
   - `ShiftLightColor` - Color enumeration
   - `FlashMode` - Flash mode enumeration

2. **`services/transbrake_manager.py`**
   - `TransbrakeManager` - Main transbrake manager
   - `TransbrakeConfig` - Configuration dataclass
   - `LaunchParameters` - Launch parameter configuration
   - `StagingConfig` - Staging control configuration
   - `ClutchSlipConfig` - Clutch slip configuration
   - `SafetyLimits` - Safety limits configuration
   - `LaunchEvent` - Launch event record
   - `TransbrakeState` - State enumeration
   - `StagingMode` - Staging mode enumeration

### UI Components

3. **`ui/shift_light_widget.py`**
   - `ShiftLightDisplay` - Visual LED display widget
   - `ShiftLightConfigWidget` - Configuration UI
   - `ShiftLightTab` - Main shift light tab

4. **`ui/transbrake_widget.py`**
   - `TransbrakeStatusWidget` - Status display widget
   - `TransbrakeConfigWidget` - Configuration UI
   - `TransbrakeTab` - Main transbrake tab

### Integration

5. **`ui/main_container.py`** (updated)
   - Added Shift Light tab
   - Added Transbrake tab
   - Integrated with main application

## 🚀 Usage

### Shift Light

```python
from services.shift_light_manager import ShiftLightManager, ShiftLightConfig, LEDConfig, GearShiftPoint

# Create manager
manager = ShiftLightManager()

# Update with current data
manager.update(rpm=6500, gear=3, lap_time=45.123)

# Set best lap time for predictive timing
manager.set_best_lap_time(44.567)

# Get shift analysis
analysis = manager.get_shift_analysis()
print(f"Average reaction time: {analysis['average_reaction_time_ms']:.1f}ms")
print(f"Optimal shifts: {analysis['optimal_shift_percentage']:.1f}%")
```

### Transbrake

```python
from services.transbrake_manager import TransbrakeManager, TransbrakeConfig

# Create manager
manager = TransbrakeManager()

# Arm transbrake
manager.arm()

# Engage transbrake
manager.engage()

# Update with sensor data
manager.update(
    rpm=4000,
    boost=15.0,
    timing=5.0,
    coolant_temp=180.0,
    trans_temp=200.0,
    battery_voltage=12.6,
    g_force=0.0,
    wheel_speed=0.0,
)

# Release transbrake
manager.release()

# Get launch analysis
analysis = manager.get_launch_analysis()
print(f"Best 60ft time: {analysis['best_60ft_time']:.3f}s")
```

## 🔧 Configuration

### Shift Light Configuration

```python
from services.shift_light_manager import ShiftLightConfig, LEDConfig, GearShiftPoint, ShiftLightColor, FlashMode

config = ShiftLightConfig(
    name="Custom Setup",
    led_configs=[
        LEDConfig(0, 5000, ShiftLightColor.GREEN, FlashMode.SOLID),
        LEDConfig(1, 5500, ShiftLightColor.YELLOW, FlashMode.SOLID),
        LEDConfig(2, 6000, ShiftLightColor.ORANGE, FlashMode.SLOW),
        LEDConfig(3, 6500, ShiftLightColor.RED, FlashMode.MEDIUM),
        LEDConfig(4, 7000, ShiftLightColor.RED, FlashMode.FAST),
    ],
    gear_shift_points={
        1: GearShiftPoint(1, 6500, 7500, 6000, 7000),
        2: GearShiftPoint(2, 6800, 7500, 6300, 7200),
        3: GearShiftPoint(3, 7000, 7500, 6500, 7300),
    },
    enable_gear_dependent=True,
    enable_predictive_timing=True,
    predictive_timing_threshold=0.1,
)

manager.update_config(config)
```

### Transbrake Configuration

```python
from services.transbrake_manager import (
    TransbrakeConfig,
    LaunchParameters,
    StagingConfig,
    SafetyLimits,
    StagingMode,
)

config = TransbrakeConfig(
    name="Drag Racing Setup",
    launch_params=LaunchParameters(
        target_rpm=4500.0,
        target_boost_psi=20.0,
        timing_advance=-2.0,
        enable_boost_control=True,
        enable_timing_control=True,
    ),
    staging_config=StagingConfig(
        mode=StagingMode.BUMP,
        bump_duty_cycle=0.5,
        bump_frequency_hz=2.0,
        creep_duty_cycle=0.3,
        creep_frequency_hz=1.0,
    ),
    safety_limits=SafetyLimits(
        max_coolant_temp_f=220.0,
        max_trans_temp_f=250.0,
        max_launch_time_seconds=5.0,
        min_battery_voltage=12.0,
        enable_safety_checks=True,
    ),
)

manager.update_config(config)
```

## 📊 Data Logging

Both systems automatically log events:

- **Shift Events**: Timestamp, gear before/after, RPM at shift, reaction time, optimal flag
- **Launch Events**: Timestamp, launch RPM/boost/timing, G-force, wheel speed, 60-foot time

Data is stored in memory and can be exported for analysis.

## 🔌 Hardware Integration

### Shift Light External Hardware

The system supports external shift light modules via:
- **CAN Bus**: Send LED states via CAN messages
- **Bluetooth**: Framework ready for Bluetooth modules

### Transbrake Hardware

The transbrake manager interfaces with:
- **ECU**: For RPM, boost, and timing control
- **Transbrake Solenoid**: For staging control (bump/creep)
- **Sensors**: Coolant temp, trans temp, battery voltage, G-force, wheel speed

## 🎯 Integration with Data Stream

To integrate with the main data stream controller:

```python
# In data_stream_controller.py
from services.shift_light_manager import ShiftLightManager
from services.transbrake_manager import TransbrakeManager

# Initialize managers
shift_light_manager = ShiftLightManager()
transbrake_manager = TransbrakeManager()

# In _on_poll method
def _on_poll(self):
    # Get current data
    rpm = self.current_data.get('rpm', 0)
    gear = self.current_data.get('gear', 1)
    lap_time = self.current_data.get('lap_time')
    
    # Update shift light
    shift_light_manager.update(rpm, gear, lap_time)
    
    # Update transbrake
    transbrake_manager.update(
        rpm=rpm,
        boost=self.current_data.get('boost', 0),
        timing=self.current_data.get('timing', 0),
        coolant_temp=self.current_data.get('coolant_temp', 0),
        trans_temp=self.current_data.get('trans_temp', 0),
        battery_voltage=self.current_data.get('battery_voltage', 12.6),
        g_force=self.current_data.get('g_force', 0),
        wheel_speed=self.current_data.get('wheel_speed', 0),
    )
```

## ✅ Status

All features have been implemented and are ready for use:

- ✅ Customizable RPM thresholds per LED
- ✅ Gear-dependent shift points
- ✅ Data logging and analysis
- ✅ Predictive lap timing integration
- ✅ External hardware connectivity (CAN/Bluetooth framework)
- ✅ Adjustable launch parameters
- ✅ Staging control (Bump/Creep)
- ✅ Clutch slip/torque converter control
- ✅ Integrated safety features
- ✅ Launch data analysis
- ✅ UI components
- ✅ Integration with main application

## 🔮 Future Enhancements

Potential future improvements:

1. **AI-Powered Shift Optimization**: ML model to suggest optimal shift points
2. **Advanced Slip Control**: PID control for clutch slip
3. **Track-Specific Configurations**: Save/load configs per track
4. **Real-Time Coaching**: Voice feedback for shift timing
5. **Advanced Analytics**: Heat maps, correlation analysis
6. **Cloud Sync**: Sync configurations across devices






