# Virtual Dyno Enhancements Summary

## Overview
Integrated all advanced enhancements from the provided Virtual Dyno Logger code into our existing Virtual Dyno system.

## ✅ Completed Enhancements

### 1. **Enhanced Air Density Calculation**
- **Location**: `services/virtual_dyno.py` - `EnvironmentalConditions.air_density_kg_m3()`
- **Improvement**: Upgraded from simplified formula to full barometric equation with proper humidity correction
- **Formula**:
  - Barometric pressure: `P = P0 * (1 - 2.25577e-5 * h)^5.25588`
  - Saturation pressure: `P_sat = 6.1078 * 10^((7.5*T)/(T+237.3)) * 100`
  - Vapor pressure: `P_v = humidity * P_sat`
  - Dry air pressure: `P_dry = P - P_v`
  - Air density: `ρ = P_dry/(R_dry*T) + P_v/(R_vapor*T)`
- **Benefits**: More accurate HP calculations across different altitudes, temperatures, and humidity levels

### 2. **Torque Estimation**
- **Location**: `services/virtual_dyno.py` - `calculate_horsepower()`
- **Improvement**: Always calculates torque when RPM is available
- **Formula**: `Torque = (HP × 5252) / RPM`
- **Benefits**: Provides complete power curve data (both HP and torque) for analysis

### 3. **Session Management**
- **Location**: `services/virtual_dyno.py`
- **New Features**:
  - `session_runs`: List of all runs in current session
  - `run_counter`: Tracks run numbers
  - `get_session_runs()`: Get all runs including current
  - `clear_session()`: Clear all session data
  - `export_session()`: Export all runs to single CSV file
- **Benefits**: Track multiple dyno runs, compare before/after, export complete session data

### 4. **Run Metadata**
- **Location**: `services/virtual_dyno.py` - `DynoCurve` dataclass
- **New Fields**:
  - `run_name`: Optional name for each run (e.g., "Run_1", "Run_2")
  - `run_timestamp`: When the run was created
- **Benefits**: Better organization and tracking of multiple runs

### 5. **Enhanced Export Functionality**
- **Location**: `ui/dyno_tab.py`
- **New Features**:
  - **Export Data**: Export current run to CSV
  - **Export Session**: Export all runs in session to single CSV file
  - Both exports include: time, RPM, speed, acceleration, wheel HP, engine HP, torque, confidence, method
- **Benefits**: Easy data analysis, sharing, and comparison

### 6. **Run Summary Dialog**
- **Location**: `ui/dyno_tab.py` - `_show_run_summary()`
- **Features**:
  - Displays peak HP and RPM
  - Displays peak torque and RPM
  - Shows run name and data point count
  - Professional dialog window matching UI theme
- **Benefits**: Quick reference for run results without checking graph

### 7. **Improved Peak Value Tracking**
- **Location**: `services/virtual_dyno.py` - `calculate_horsepower()`
- **Improvement**: Always updates peak HP wheel value and ensures torque peaks are properly tracked
- **Benefits**: More accurate peak value reporting

## Integration Details

### Air Density Calculation
The new air density formula is more accurate for:
- High altitude locations
- Extreme temperatures (hot/cold)
- High humidity conditions
- Different barometric pressures

### Torque Display
- Torque curves are already displayed in `dyno_view.py` alongside HP curves
- Torque is calculated automatically when RPM data is available
- Both HP and torque curves are shown in separate plots with proper scaling

### Session Export Format
The exported CSV includes:
- `run_name`: Name of the run
- `run_timestamp`: When the run started
- `time_s`: Relative time from run start
- `rpm`: Engine RPM
- `speed_mph`, `speed_mps`: Vehicle speed
- `acceleration_mps2`: Calculated acceleration
- `wheel_hp`: Wheel horsepower
- `engine_hp`: Crank horsepower
- `torque_ftlb`: Calculated torque
- `confidence`: Calculation confidence (0-1)
- `method`: Calculation method used

## Usage

### Starting a Logging Session
1. Click "Start Logging" button
2. Data is collected in real-time
3. Click "Stop Logging" when done
4. Data is automatically processed using improved batch calculation
5. Summary dialog appears with peak values

### Exporting Data
- **Export Data**: Exports only the current run
- **Export Session**: Exports all runs in the current session to a single CSV file

### Viewing Results
- HP and torque curves are displayed in the dyno view
- Summary dialog shows peak values after each run
- Multiple runs can be compared using the comparison feature

## Technical Notes

### Air Density Formula
The new formula uses:
- Separate gas constants for dry air (R_dry = 287.058 J/(kg·K)) and water vapor (R_vapor = 461.495 J/(kg·K))
- Proper barometric equation for altitude correction
- Magnus formula for saturation vapor pressure
- Combined density calculation: ρ = ρ_dry + ρ_vapor

### Torque Calculation
Torque is calculated using the standard automotive formula:
```
Torque (ft-lb) = (Horsepower × 5252) / RPM
```

This is the inverse of the power formula:
```
Horsepower = (Torque × RPM) / 5252
```

### Batch Processing
The `calculate_horsepower_from_timeseries()` method uses:
- `np.gradient()` for accurate acceleration calculation (central differences)
- Savitzky-Golay filter for noise reduction
- Proper handling of time series data

## Future Enhancements (Optional)

1. **Live Graph Updates**: Real-time graph updates during logging (currently updates after processing)
2. **Multi-Run Overlay**: Display multiple runs on same graph with different colors
3. **Statistical Analysis**: Calculate power band, area under curve, etc.
4. **Export Formats**: Support JSON, Excel, and other formats
5. **Run Comparison**: Side-by-side comparison of multiple runs

## Files Modified

1. `services/virtual_dyno.py`:
   - Enhanced `air_density_kg_m3()` method
   - Added session management methods
   - Improved torque calculation
   - Added run metadata to `DynoCurve`

2. `ui/dyno_tab.py`:
   - Added "Export Session" button
   - Implemented `_export_data()` for single run export
   - Implemented `_export_session()` for session export
   - Added `_show_run_summary()` dialog

## Testing Recommendations

1. Test air density calculation at different altitudes/temperatures
2. Verify torque calculation matches expected values
3. Test session export with multiple runs
4. Verify summary dialog displays correct peak values
5. Test export functionality with various data sets











