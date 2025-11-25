# Diesel Engine Support

## Overview

The AI Tuner Agent now includes **comprehensive diesel engine support** for all major diesel platforms. Diesel engines are fundamentally different from gasoline engines and require specialized tuning parameters and monitoring.

## Supported Engines

### Cummins
- **5.9L ISB** (1998-2007)
- **6.7L ISB** (2007+)
- **6.8L ISB** (newest)

### Duramax
- **LB7** (2001-2004)
- **LLY** (2004-2005)
- **LBZ** (2006-2007)
- **LMM** (2007-2010)
- **LML** (2011-2016)
- **L5P** (2017+) - Latest generation

### Powerstroke
- **6.0L** (2003-2007)
- **6.4L** (2008-2010)
- **6.7L** (2011+)

### BMW
- **M57** (3.0L I6, 1998-2013)
- **N57** (3.0L I6, 2008+)
- **M67** (V8)
- **N67** (V8, newer)

### Other Platforms
- Caterpillar
- Detroit Diesel
- Volvo
- Mercedes
- VW TDI
- Generic diesel (for unknown engines)

## Key Differences: Diesel vs Gasoline

### 1. **Ignition System**
- **Gasoline**: Spark plugs, ignition timing
- **Diesel**: Compression ignition, **NO spark plugs**
- **Tuning Focus**: Injection timing (when fuel is injected), not ignition timing

### 2. **Fuel System**
- **Gasoline**: Low pressure (30-60 PSI), port or direct injection
- **Diesel**: **High pressure common rail** (5,000-29,000 PSI!)
- **Critical Parameter**: Rail pressure - must be monitored closely

### 3. **Temperature Monitoring**
- **Gasoline**: Coolant temp, oil temp
- **Diesel**: **EGT (Exhaust Gas Temperature) is CRITICAL**
  - Pre-turbo EGT: Most important
  - Post-turbo EGT: Also monitored
  - Exceeding EGT limits = engine damage!

### 4. **Boost Pressure**
- **Gasoline**: Optional, typically 10-30 PSI
- **Diesel**: **Standard**, typically 20-55 PSI
- Most diesels are turbocharged
- VGT (Variable Geometry Turbo) common

### 5. **Emissions Systems**
- **EGR** (Exhaust Gas Recirculation): Common on both
- **DPF** (Diesel Particulate Filter): Diesel-specific
- **DEF/AdBlue** (Diesel Exhaust Fluid): Diesel-specific (SCR system)
- **NOX Sensors**: Diesel-specific

### 6. **Tuning Philosophy**
- **Gasoline**: RPM-based, air/fuel ratio (AFR/Lambda)
- **Diesel**: **Torque-based**, injection quantity (mm³)
- **No AFR** - diesel runs lean, air is always in excess

## Diesel-Specific Parameters

### Fuel System
- **Fuel Rail Pressure**: 5,000-29,000 PSI (platform-dependent)
- **Injection Timing**: Degrees BTDC (Before Top Dead Center)
- **Injection Quantity**: mm³ per injection
- **Pilot Injection**: Small pre-injection for smoother combustion
- **Post Injection**: For DPF regeneration

### Turbo/Boost
- **Boost Pressure**: PSI (higher than gasoline)
- **VGT Position**: % (Variable Geometry Turbo)
- **Wastegate Position**: % (if equipped)

### Temperature
- **EGT (Exhaust Gas Temperature)**: **CRITICAL** - typically 1,300-1,650°F
- **Pre-Turbo EGT**: Most important
- **Post-Turbo EGT**: Also monitored
- **Coolant Temp**: Standard
- **Oil Temp**: Standard
- **Intake Air Temp**: Important for density calculations

### Emissions
- **EGR Position**: % (Exhaust Gas Recirculation)
- **EGR Flow**: g/s
- **DPF Pressure**: PSI (indicates clogging)
- **DPF Regen Status**: Active/Inactive
- **DEF Level**: % (Diesel Exhaust Fluid/AdBlue)
- **NOX Sensor**: PPM

## Safety Limits by Platform

### Cummins 6.7L
- Max Rail Pressure: 26,000 PSI
- Max Boost: 50 PSI
- Max EGT: 1,650°F
- Safe EGT: 1,400°F
- Max Torque: 800 lb-ft

### Duramax L5P (Latest)
- Max Rail Pressure: 29,000 PSI
- Max Boost: 55 PSI
- Max EGT: 1,700°F
- Safe EGT: 1,450°F
- Max Torque: 910 lb-ft

### Powerstroke 6.7L
- Max Rail Pressure: 28,000 PSI
- Max Boost: 52 PSI
- Max EGT: 1,650°F
- Safe EGT: 1,400°F
- Max Torque: 925 lb-ft

## Usage

### Basic Usage

```python
from services.diesel_tuner import DieselTuner, DieselEngineType

# Initialize for specific engine
tuner = DieselTuner(
    engine_type=DieselEngineType.DURAMAX_L5P,
    voice_feedback=voice_feedback,
    auto_apply=False
)

# Update telemetry
telemetry = {
    "EGT": 1450,  # Exhaust Gas Temperature
    "FuelRailPressure": 25000,  # PSI
    "BoostPressure": 45.0,  # PSI
    "InjectionTiming": 12.5,  # Degrees BTDC
    "InjectionQuantity": 180,  # mm³
}

tuner.update_telemetry(telemetry)

# Get recommendations
recommendations = tuner.analyze_and_recommend()

for rec in recommendations:
    print(f"{rec.parameter.value}: {rec.reason}")
    print(f"  Current: {rec.current_value}")
    print(f"  Recommended: {rec.recommended_value}")
```

### Auto-Detection

The tuner can attempt to detect engine type from telemetry:

```python
detected_type = tuner.detect_engine_type(telemetry)
if detected_type:
    tuner.engine_type = detected_type
```

### Voice Feedback

Critical diesel parameters trigger voice warnings:

- **EGT Critical**: "CRITICAL: EGT at X degrees! Reduce fuel immediately!"
- **Rail Pressure High**: "Warning: Rail pressure at X PSI, near maximum."
- **Boost High**: "Warning: Boost at X PSI, near maximum."

## Integration

The diesel tuner integrates with:

- **Data Stream Controller**: Automatically monitors diesel parameters
- **Tuning Advisor**: Provides diesel-specific advice
- **Voice Feedback**: Critical alerts for EGT, rail pressure, etc.
- **ECU Control**: Can adjust diesel-specific parameters
- **Health Scoring**: Includes diesel-specific health metrics

## Critical Warnings

### EGT (Exhaust Gas Temperature)
- **Most critical parameter for diesel**
- Exceeding limits causes:
  - Turbo failure
  - Piston damage
  - Head gasket failure
  - Engine destruction
- **Always monitor EGT!**

### Rail Pressure
- Extremely high pressure (20,000+ PSI)
- Exceeding limits causes:
  - Injector failure
  - Rail damage
  - Fuel system failure

### Boost Pressure
- Higher than gasoline (40-55 PSI common)
- Exceeding limits causes:
  - Turbo failure
  - Intercooler failure
  - Engine damage

## Best Practices

1. **Always monitor EGT** - Set up alerts
2. **Know your platform limits** - Each engine has different limits
3. **Start conservative** - Increase gradually
4. **Monitor rail pressure** - Critical for fuel system health
5. **Watch emissions systems** - DPF, DEF, EGR can cause derates
6. **Use platform-specific profiles** - Don't use generic limits

## Future Enhancements

- Automatic engine type detection from CAN IDs
- Platform-specific tuning maps
- DPF regeneration optimization
- DEF consumption tracking
- EGR optimization for performance
- Multi-stage injection timing optimization

---

**Diesel tuning is different - use the right tools!** 🔧

