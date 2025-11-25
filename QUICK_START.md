# Quick Start - Preview the GUI

## ✅ Works on Windows, Linux, and macOS!

## 🚀 Super Simple - Just Run This:

**Windows:**
```cmd
cd AI-TUNER-AGENT
python demo.py
```

**Linux/Mac:**
```bash
cd AI-TUNER-AGENT
python demo.py
```

That's it! The GUI will launch with simulated data.

## What You Need

1. **Python 3.8+** installed
2. **Dependencies** installed:
   ```bash
   pip install -r requirements.txt
   ```

## Demo Modes

### Default (Demo Mode)
Cycles through different scenarios automatically:
```bash
python demo.py
```

### Racing Mode
Full racing simulation:
```bash
python demo.py --mode racing
```

### Cruising Mode
Highway driving simulation:
```bash
python demo.py --mode cruising
```

### Idle Mode
Engine at idle:
```bash
python demo.py --mode idle
```

## What You'll See

✅ **Real-time telemetry panel** - Live sensor readings  
✅ **Health score widget** - Engine health monitoring  
✅ **AI insights panel** - Tuning recommendations  
✅ **Dragy performance view** - 0-60 times, lap times  
✅ **Status bar** - System status  
✅ **All UI components** - Fully functional with realistic data  

## Troubleshooting

### "ModuleNotFoundError: No module named 'PySide6'"
```bash
pip install pyside6
```

### Windows: "python is not recognized"
- Make sure Python is installed and in PATH
- Try `py` instead: `py demo.py`

### Linux: "No display"
Make sure X11 is running or use:
```bash
export DISPLAY=:0
python demo.py
```

### Voice output issues
Disable voice if you don't have TTS:
```bash
python demo.py --no-voice
```

### Windows: Missing DLL errors
```cmd
pip install --upgrade pyside6
```

## That's It!

The demo runs completely standalone - no hardware, no configuration needed. Just run it and explore the interface!

For production use with real hardware, see the main README.

