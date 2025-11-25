# Nitro Methane Module – Advanced Features

## Overview
The Nitro Methane tab in the ECU Tuning interface now mirrors professional nitro-burning crew chiefs tools.  It combines mixing calculators, AFR guidance, ignition/boost controls, and safety simulators so you can model nitro percentages, predict power changes, and monitor detonation risk in real time.

## Feature Highlights
### Fuel & AFR Management
- **Fuel Mixture Calculator** – precise nitro/methanol/oil blending by weight or volume with specific gravity readout.
- **AFR & Jetting Calculator** – accounts for displacement, blower size, overdrive, atmosphere, and nitro stoich (~1.7:1) to suggest jet and pill sizes.
- **Mix Simulator (Lean/Rich)** – slider + lean/rich nudge buttons simulate AFR adjustments; outputs recommended AFR, timing offset, and projected power gains.
- **Recommended Lambda** – live readout tied to current nitro percentage and telemetry.

### Ignition & Detonation Control
- **Ignition Timing Map** – high resolution RPM/load table tailored for nitro’s slower burn rate.
- **Detonation Predictor** – evaluates lambda, timing advance, boost, and EGT to warn about pre-ignition risk via color-coded indicator.
- **Timing Stages** – multi-stage timing tables vs boost/time to smooth the transition into heavy nitro loads.

### Boost & Power Simulation
- **Nitro Boost Gauge** – visual simulator for oxygen-release pressure; ties into audio cues (“idle hum”, “rising howl”, “siren”).
- **Power Predictor** – estimates hp gains from nitro %, lambda delta, and timing adjustments; surfaces inside Boost & Power panel and mix simulator.
- **Nitro Boost State Label** – textual summary for crew heads-up displays.

### Safety, Logging & Soft Limits
- **Soft Rev Limiter** – “Soft Limiting” status for nitro-specific rev control, with hard-cut detection.
- **Engine Stress Gauge** – cumulative damage model factoring detonation risk and lambda excursions.
- **Closed-loop safeguards** – configurable thresholds for EGT, CHT, fuel/oil pressure, peak cylinder pressure, knock-based retard, and emergency shutdown.
- **Detonation Warning Banner** – shows LOW / MODERATE / HIGH risk.
- **High-speed Datalogger** – 100–2000 Hz sampling with auto start/stop and analysis tools.

### User Interface Enhancements
- **Touchscreen-Friendly Controls** – large toggles and sliders sync with desktop settings.
- **Audio/Visual cues** – nitro boost states drive textual indicators for loudspeakers or HUD integration.
- **Mix simulator guidance** – contextual tips reminding that richer mixtures cool the engine but increase stress.

## Telemetry Integration
- `update_telemetry()` feeds: nitro %, lambda, timing, boost, fuel pressure, peak cylinder pressure, EGT/CHT, injector duty, horsepower, RPM, etc.
- Live data drives the mix simulator slider (when not manually dragged), recommended lambda, power prediction, soft rev status, detonation warnings, engine stress, and nitro boost cues.

## Files & Entry Points
- UI logic lives in `ui/ecu_tuning_main.py` inside `class NitroMethaneTab(ModuleTab)`.
- Mix calculator helpers: `_create_nitro_calculator()`, `_create_mix_simulator()`, `_update_mix_simulator()`.
- Safety helpers: `_recommended_lambda`, `_detonation_risk`, `_update_detonation_indicator`, `_update_engine_damage`, `_update_soft_rev_status`.

## Tips for Operators
1. Keep nitro percentage synced with physical mix using the Fuel Mixture tool.
2. Monitor the Detonation Risk widget before each pass; aim for “Low” or “Moderate”.
3. Use the Mix Simulator to preview lean-outs or rich-ups before altering mechanical jets.
4. Watch Engine Stress; sustained >80 % indicates you should richen the tune or reduce timing.
5. Enable high-speed logging for every run to correlate AFR, timing, and boost with ET changes.

With these enhancements the Nitro Methane module now provides AFR calculators, ignition-timing guidance, boost simulation, soft rev limiting, and visual/auditory cues exactly as requested.  Use this document as the primary reference when updating nitro-specific workflows or onboarding crew members.











