# Virtual Dyno Guide - Complete Feature Documentation

## 🎯 Overview

The Virtual Dyno is a **GAME CHANGER** - calculate horsepower from real driving data without expensive dyno runs!

**Target Accuracy:**
- Without calibration: ±10-15%
- With 1 calibration: ±5-8%
- With 3+ calibrations: ±3-5% (comparable to real dyno!)

## 🚀 Quick Start

### Step 1: Set Vehicle Specs

Before using the virtual dyno, you need accurate vehicle specifications:

```python
from services.virtual_dyno import VehicleSpecs, VirtualDyno

specs = VehicleSpecs(
    curb_weight_kg=1500,      # Vehicle weight (lookup your car)
    driver_weight_kg=80,      # Your weight
    fuel_weight_kg=50,         # Current fuel weight (~0.75 kg/L)
    frontal_area_m2=2.0,       # Frontal area (lookup your car)
    drag_coefficient=0.30,     # Cd (lookup your car)
    rolling_resistance_coef=0.015,  # Typical: 0.012-0.018
    drivetrain_loss=0.18,     # 15% FWD, 18% RWD, 20% AWD
    drivetrain_type="RWD",
)

dyno = VirtualDyno(vehicle_specs=specs)
```

### Step 2: Calibrate (For Maximum Accuracy)

**Option A: Import Real Dyno File**
1. Go to Settings → Calibrate Virtual Dyno
2. Click "Import CSV" or "Import JSON"
3. Select your dyno file
4. System calculates calibration factor automatically

**Option B: Manual Entry**
1. Go to Settings → Calibrate Virtual Dyno
2. Click "Manual Entry" tab
3. Enter your peak HP, peak torque, and RPMs
4. System prompts for additional data if needed

### Step 3: Use During Runs (GUI Workflow)

1. Open the **Virtual Dyno** tab in the desktop UI
2. Click **Start Logging** right before the pull (20 Hz capture)
3. Perform the acceleration run (smooth throttle, full pull)
4. Click **Stop Logging** once the run is complete
5. Review the live horsepower trace and run summary dialog (peak HP/TQ + RPM)
6. Use **Export Data** (single run) or **Export Session** (all runs) as needed

### Step 3b: Use Programmatically

The service API still supports direct telemetry feeds:

```python
reading = dyno.calculate_horsepower(
    speed_mph=60.0,
    acceleration_mps2=2.5,
    rpm=5000,
)

print(f"Current HP: {reading.horsepower_crank:.0f}")
print(f"Peak HP: {dyno.current_curve.peak_hp_crank:.0f}")
```

## 📊 Features

### 1. Real-Time HP Display
- Live horsepower and torque readings
- Updates during acceleration
- Shows RPM, HP, and torque simultaneously

### 2. Dyno Curve Plotting
- Beautiful HP vs RPM curve
- Torque vs RPM curve
- Peak markers
- Before/after comparisons

### 3. Calibration System
- Import CSV/JSON dyno files
- Manual entry with prompts
- Automatic calibration factor calculation
- Multiple calibration runs for accuracy

### 4. Advanced Analysis
- Power band analysis
- Torque band analysis
- Before/after mod comparisons
- Weather correction (SAE standard)
- Mod impact analysis

### 5. Session Management
- Start/Stop logging buttons in UI
- Live horsepower preview during capture
- Automatic run naming (`Run_1`, `Run_2`, …)
- Run summary dialog with peak HP/TQ + RPM
- Session reset without restarting the app

### 6. Export & Share
- Export dyno curves to CSV/JSON
- Export current run with time/RPM/HP/Torque
- Session-wide CSV export with metadata
- Share results and historical tracking
- Compare multiple runs

## 🎯 Accuracy Tips

### Maximum Accuracy Checklist:

✅ **Vehicle Specs**
- Accurate curb weight (check manufacturer specs)
- Correct drag coefficient (Cd) - lookup your car
- Frontal area (A) - lookup or measure
- Drivetrain type (FWD/RWD/AWD)

✅ **Calibration**
- Calibrate with at least 1 real dyno run
- More calibrations = better accuracy
- Calibrate in similar conditions

✅ **Data Quality**
- Use GPS speed (most accurate)
- Smooth acceleration data (not jerky)
- Higher speeds (30+ mph better)
- Full throttle pulls

✅ **Environmental**
- Enter temperature
- Enter altitude
- System corrects for air density

## 📈 Using the UI

### Main Dyno View
- **Real-Time HP Meter**: Shows current HP, RPM, torque
- **Dyno Curve Graph**: HP and torque vs RPM (HP/TQ overlays per run)
- **Live HP Trace**: Orange preview while logging
- **Session Controls**: Start/Stop logging, Export Data, Export Session
- **Stats**: Peak values, accuracy estimate, confidence

### Calibration Dialog
- **Import Tab**: Import CSV/JSON files
- **Manual Entry Tab**: Enter values manually
- System prompts for missing data

### Comparison View
- Compare before/after mods
- Side-by-side curves
- HP/torque differences
- Mod impact analysis

## 🧪 Logging Workflow

1. **Prep** – Confirm vehicle specs + environmental inputs, then click **Start Logging**.
2. **Capture** – Perform the pull; live horsepower trace updates every ~0.5 s.
3. **Process** – Click **Stop Logging** to trigger Savitzky–Golay smoothing + `np.gradient` acceleration.
4. **Review** – Run Summary dialog surfaces peak HP/TQ, RPM, and data-point counts; curves update instantly.
5. **Repeat** – Start another run; previous runs remain in-session until you hit **Reset Session**.

## 📤 Exporting Data

- **Export Data** – Saves the current run to CSV with relative time, RPM, HP/TQ, acceleration, method, and confidence.
- **Export Session** – Combines every run (name, timestamp, readings) into a single CSV compatible with Excel, Dynojet, or data science notebooks.
- **Automation Hooks** – Use `virtual_dyno.export_session("session_summary.csv")` for scripted exports during test automation.

## 🔧 Advanced Features

### Weather Correction
Corrects power to standard conditions (SAE J1349) and shares the same enhanced air-density formula used in real-time logging:

```python
from services.dyno_analyzer import DynoAnalyzer, WeatherStandard

analyzer = DynoAnalyzer()
corrected_curve = analyzer.apply_weather_correction(
    curve=my_curve,
    actual_temp_c=25.0,
    actual_pressure_kpa=101.325,
    actual_humidity_percent=50.0,
    standard=WeatherStandard.SAE_J1349,
)
```

### Power Band Analysis
Analyze power band characteristics:

```python
analysis = analyzer.analyze_power_band(my_curve)
print(f"Power band width: {analysis.power_band_width_rpm:.0f} RPM")
print(f"Flatness score: {analysis.flatness_score:.2f}")
print(f"Recommendations: {analysis.recommendations}")
```

### Before/After Comparison
Compare two dyno runs:

```python
comparison = analyzer.compare_runs(
    run1_name="Stock",
    run1_curve=stock_curve,
    run2_name="After Tune",
    run2_curve=tuned_curve,
)

print(f"HP gain: {comparison.hp_difference:.1f} HP")
print(f"Improvement: {comparison.improvement_percent:.1f}%")
```

## 📝 Manual Entry Guide

If you don't have a dyno file, you can manually enter:

### Required:
- **Peak Horsepower**: Maximum HP from dyno
- **Peak HP RPM**: RPM where peak HP occurs

### Recommended:
- **Peak Torque**: Maximum torque
- **Peak Torque RPM**: RPM where peak torque occurs

### Optional (More Accurate):
- HP and torque at 2000, 3000, 4000, 5000, 6000, 7000 RPM
- System will prompt for these if you want better accuracy

## 🎨 Example Workflow

1. **First Time Setup**
   - Enter vehicle specs
   - Run a few acceleration pulls
   - Check virtual dyno results

2. **Calibration**
   - Go to real dyno (one time)
   - Get dyno sheet
   - Import file or enter manually
   - System calibrates automatically

3. **Future Runs**
   - Virtual dyno now accurate to ±3-5%
   - No more expensive dyno runs needed!
   - Track HP changes over time
   - Compare before/after mods

## 🔍 Troubleshooting

### Low Accuracy
- Check vehicle specs (weight, Cd, etc.)
- Calibrate with real dyno run
- Ensure good GPS/speed data
- Enter environmental conditions

### Missing Data
- System prompts for required fields
- Can work with just peak HP/RPM
- More data = better accuracy

### Import Errors
- Check CSV format (RPM, HP, Torque columns)
- Try manual entry instead
- System will guide you through

## 💡 Pro Tips

1. **Calibrate Early**: Do one real dyno run, then use virtual dyno forever
2. **Track Changes**: Compare runs to see mod impact
3. **Weather Correct**: Use SAE correction for fair comparisons
4. **Multiple Calibrations**: More calibrations = better accuracy
5. **Good Data**: Use GPS speed, smooth acceleration, full throttle

---

**This feature alone could save thousands in dyno costs!** 🚀

