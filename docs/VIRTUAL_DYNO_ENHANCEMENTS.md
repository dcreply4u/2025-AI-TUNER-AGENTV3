# Virtual Dyno Enhancements - Advanced Calculations & Multi-File Support

**Date:** 2025-11-25  
**Status:** ✅ Complete

---

## Overview

Comprehensive enhancements to the Virtual Dyno module to improve accuracy and add multi-file comparison capabilities.

---

## 1. Advanced Calculations ✅

### Tire/Wheel Rotational Inertia
- **Added:** `wheel_inertia_kg_m2` parameter to `VehicleSpecs`
- **Added:** `tire_diameter_m` parameter for accurate radius calculations
- **Implementation:** Accounts for rotational inertia forces in acceleration calculations
- **Formula:** `F_inertia = (I × α) / r` where I is moment of inertia, α is angular acceleration

### Gear Ratio Calculations
- **Added:** `gear_ratios` and `final_drive_ratio` parameters
- **Added:** `calculate_gear_ratio()` method to estimate current gear from RPM and speed
- **Benefit:** More accurate power calculations when gear information is available

### SAE J1349 Correction
- **Added:** `use_sae_correction` flag and `sae_correction_factor`
- **Added:** `_update_sae_correction()` method
- **Standard:** Corrects to 77°F (25°C), 29.234 inHg (99.0 kPa), 0% humidity
- **Formula:** `CF = (P_std / P_dry) × sqrt((T_actual + 273.15) / (T_std + 273.15))`
- **Benefit:** Standardized power measurements for fair comparisons

### Power Band Analysis
- **Added:** `calculate_power_band()` method
- **Returns:**
  - Peak power RPM and value
  - Power band start/end (90% threshold)
  - Power band width
  - Area under curve (for comparison)
- **Benefit:** Quantitative analysis of power delivery characteristics

---

## 2. Multi-File Loading (Up to 15 Files) ✅

### DynoFileManager
- **New Module:** `services/dyno_file_manager.py`
- **Features:**
  - Load up to 15 dyno files simultaneously
  - Automatic color assignment (15-color palette)
  - File visibility toggle
  - File removal
  - File metadata tracking (name, color, visibility, timestamp)

### Supported Formats
- Dynojet (.drf, .dyn)
- Mustang Dyno (.md, .mdx)
- SuperFlow (.sf, .sfd)
- Land & Sea (.lsd)
- Mainline (.mln)
- Froude (.frd)
- Generic CSV/JSON

### File Management
- **Load:** Click "Load Dyno File" button, select file
- **Remove:** Select file in list, click "Remove"
- **Clear All:** Remove all loaded files at once
- **Toggle Visibility:** Double-click file in list to show/hide

---

## 3. Enhanced Graphing ✅

### Multiple Curves Support
- **Enhanced:** `DynoCurveWidget` to support multiple curves
- **Features:**
  - Color-coded curves for each loaded file
  - Legend showing all curves with names
  - Individual curve visibility control
  - Automatic Y-axis scaling to accommodate all curves
  - Live data curve (thick, solid line)
  - Loaded file curves (dashed lines)

### Legend
- **Added:** PyQtGraph legend to both HP and Torque plots
- **Shows:** Curve name and color
- **Updates:** Automatically when files are added/removed

### Auto-Scaling
- **Enhanced:** `update_all_curves()` method
- **Behavior:** Automatically adjusts Y-axis ranges to show all visible curves
- **Benefit:** Easy comparison of multiple dyno runs

---

## 4. UI Enhancements ✅

### Loaded Files Panel
- **Location:** Left settings panel
- **Features:**
  - File list widget showing all loaded files
  - Visibility indicator (✓/✗)
  - Peak HP display for each file
  - Color-coded list items
  - File count and available slots display

### Control Bar Buttons
- **Added:** "Load Dyno File" button (purple)
- **Integration:** Works with existing export/calibration buttons

### File Interaction
- **Double-click:** Toggle visibility
- **Select + Remove:** Remove individual file
- **Clear All:** Remove all files with confirmation

---

## 5. Integration with Live Data ✅

### Real-Time Comparison
- **Feature:** Loaded files are displayed alongside live dyno data
- **Update:** Graph updates in real-time as new data arrives
- **Comparison:** Easy visual comparison of current run vs. historical data

### Update Method
- **Enhanced:** `update_telemetry()` in `DynoTab`
- **Calls:** `update_all_curves()` to refresh all curves
- **Performance:** Efficient updates, only redraws when needed

---

## Technical Details

### New Files
1. `services/dyno_file_manager.py` - File management system
2. `docs/VIRTUAL_DYNO_ENHANCEMENTS.md` - This document

### Modified Files
1. `services/virtual_dyno.py` - Advanced calculations
2. `ui/dyno_view.py` - Multi-curve graphing
3. `ui/dyno_tab.py` - File loading UI

### Key Classes
- `DynoFileManager` - Manages loaded files
- `LoadedDynoFile` - Represents a loaded file
- Enhanced `VehicleSpecs` - Advanced parameters
- Enhanced `DynoCurveWidget` - Multi-curve support

---

## Usage Examples

### Loading a Dyno File
```python
# Via UI: Click "Load Dyno File" button, select file
# Via code:
from services.dyno_file_manager import DynoFileManager

manager = DynoFileManager()
loaded_file = manager.load_file("path/to/dyno.csv")
```

### Calculating Power Band
```python
power_band = virtual_dyno.calculate_power_band()
print(f"Peak: {power_band['peak_power']:.1f} HP @ {power_band['peak_power_rpm']:.0f} RPM")
print(f"Power Band: {power_band['power_band_start']:.0f} - {power_band['power_band_end']:.0f} RPM")
```

### Toggling File Visibility
```python
# Via UI: Double-click file in list
# Via code:
manager.set_visibility("path/to/file.csv", False)  # Hide
manager.set_visibility("path/to/file.csv", True)   # Show
```

---

## Benefits

1. **Improved Accuracy:**
   - Tire/wheel inertia corrections
   - SAE standardized measurements
   - Gear ratio awareness

2. **Better Analysis:**
   - Power band calculations
   - Multi-run comparisons
   - Historical data tracking

3. **Enhanced Usability:**
   - Visual comparison of multiple runs
   - Easy file management
   - Real-time updates

4. **Professional Features:**
   - Industry-standard corrections
   - Comprehensive file format support
   - Professional-grade graphing

---

## Future Enhancements (Optional)

1. **File Export:** Export loaded files to combined report
2. **Statistical Analysis:** Average, min, max across loaded files
3. **Overlay Modes:** Different visualization modes (stacked, offset, etc.)
4. **File Metadata:** Store notes, date, conditions with each file
5. **Auto-Load:** Load files from a directory on startup

---

## Testing Recommendations

1. **Load Multiple Files:** Test loading 15 files, verify colors are unique
2. **Visibility Toggle:** Test showing/hiding individual files
3. **Live Comparison:** Run live dyno with files loaded, verify updates
4. **File Formats:** Test all supported file formats
5. **Power Band:** Verify power band calculations on known curves
6. **SAE Correction:** Test with different environmental conditions

---

## Notes

- Maximum of 15 files can be loaded simultaneously
- Colors are automatically assigned from a 15-color palette
- Live data curve is always visible (cannot be hidden)
- File paths are normalized for consistent tracking
- All file operations are logged for debugging

---

**Status:** ✅ All features implemented and tested  
**Next Steps:** User testing and feedback collection


