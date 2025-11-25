# Methanol Module – Feature Summary

## Overview
The Methanol tab is now a full-featured tuning workstation for water/meth injection and 100 % meth fuel systems. It combines real-time diagnostics, dynamic control tables, environmental compensation, and logging/failsafes so you can tune safely for street, race, or kill maps.

## Real-Time Monitoring
- Gauges for injection duty, tank level, flow rate, AFR/Lambda, fuel pressure, EGT, boost, and coolant.
- Diagnostics indicator + soft-failsafe banner on the top control bar.
- Individual-cylinder EGT graph plus VE, AFR, timing, and pressure graphs.

## Control Bar / Modes
- One-tap Street / Race / Kill switching adjusts base timing and fuel multipliers automatically.
- Failsafe status light with “Armed” / “Safe map active”.
- Buttons to clear fault codes and export session logs.

## Center Tabs
1. **VE / Base Fuel Map** – VETableWidget for methanol’s ~2.3× fuel requirement.
2. **Target AFR/Lambda** – high-resolution table (3.5–6.4:1 AFR) with color coding.
3. **Ignition Timing** – methanol-specific advance map (10–50° window).
4. **Injection Flow Map** – boost/EGT/TPS matrix for progressive duty control.
5. **Temperature Corrections** – coolant + air temp enrichment/retard tables.
6. **Dynamic Control** – RPM/load grid for live duty scheduling.
7. **Diagnostics** – fault-code table with timestamped entries.
8. **Environment** – ambient temp/humidity/baro inputs + density correction summary.
9. **Data Logging** – rolling session table (time, RPM, boost, AFR, duty, faults) with clear/export options.

## Safety & Failsafes
- Thresholds for tank level, fuel pressure, flow, coolant, and EGT.
- Automatic fault capture with detents in the Diagnostics tab and status indicator.
- “Failsafe: Safe map active” banner when thresholds are breached (if failsafe enabled).
- Emergency map switching supported through the base ModuleTab stack.

## Environmental Compensation
- Inputs for ambient temperature, humidity, barometric pressure, and density altitude.
- Live text summary suggests timing/fuel trims so you can pre-empt conditions that cause lean surging.

## Logging & Analysis
- Session log deque (240 entries) mirrored in the Data Logging tab.
- CSV export button on the control bar.
- Logs capture RPM, boost, AFR, duty, and any active fault string at each timestamp.

## Integration Hooks
- `update_telemetry()` handles sensor inputs (`meth_duty`, `MethInjectionDuty`, `methanol_level`, `Fuel_Pressure`, `AFR`, `EGT`, `Coolant_Temp`, `Boost_Pressure`, etc.).
- Failsafe logic respects UI thresholds and automatically records faults/log samples.
- Environment slider updates can be tied to backend compensation if you integrate a closed-loop table.

## Operator Tips
1. Run Street mode for commuting, Race for track days, Kill for dyno hero pulls only.
2. Watch the Diagnostics indicator—if it flips to orange/red, investigate before next pass.
3. Use the Dynamic Control tab to smooth duty vs RPM/load for spool-friendly injection.
4. Export logs after each session and attach them to tune revisions or customer builds.
5. Keep ambient inputs updated on race day for accurate density trim suggestions.

This module now meets the requested requirements: real-time vitals, diagnostics, dynamic methanol control, failsafes, custom map editing, logging, environmental adjustments, mode switching, per-cylinder data, and boost-integrated behavior.











