# AI Tuner Agent - GUI Demo

Quick preview of the GUI without any hardware!

## Quick Start

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run the demo
python demo.py
```

## Demo Modes

### Demo Mode (Default)
Cycles through different scenarios:
- Idle (0-15s)
- Cruising (15-30s)
- Racing (30-45s)
- Back to idle (45-60s)

```bash
python demo.py --mode demo
```

### Racing Mode
Simulates a racing scenario with:
- Launch phase
- Acceleration
- Braking
- Cornering

```bash
python demo.py --mode racing
```

### Cruising Mode
Simulates normal highway driving at ~60 mph

```bash
python demo.py --mode cruising
```

### Idle Mode
Simulates engine at idle

```bash
python demo.py --mode idle
```

## Options

```bash
# Disable voice output (if you don't have TTS installed)
python demo.py --no-voice
```

## What You'll See

The demo will show:
- ✅ Real-time telemetry panel with simulated sensor data
- ✅ Health score widget with live updates
- ✅ AI insights panel with simulated recommendations
- ✅ Dragy-style performance view (if GPS simulation enabled)
- ✅ Status bar with connection status
- ✅ All UI components working with realistic data

## Features Demonstrated

- **Telemetry Display**: Real-time sensor readings
- **Health Monitoring**: Engine health scoring
- **AI Insights**: Simulated tuning recommendations
- **Performance Tracking**: Simulated 0-60 times, lap times
- **Voice Feedback**: Optional voice announcements
- **Data Logging**: All data is logged to CSV files

## Troubleshooting

### "No module named PySide6"
```bash
pip install pyside6
```

### "Voice output not working"
Use `--no-voice` flag or install `pyttsx3`:
```bash
pip install pyttsx3
```

### Window doesn't appear
Make sure you have a display (X11 on Linux, or run on Windows/Mac)

## Next Steps

Once you've previewed the GUI:
1. Connect real hardware (OBD-II, RaceCapture, CAN bus)
2. Configure your vehicle profile
3. Start logging real data!

Enjoy exploring the AI Tuner Agent! 🚗💨

