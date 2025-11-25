# Quick Start - Windows

## ✅ Yes! It Works on Windows!

The demo runs perfectly on Windows. Here's how:

## Step 1: Install Python

If you don't have Python installed:
1. Download from [python.org](https://www.python.org/downloads/)
2. Make sure to check "Add Python to PATH" during installation
3. Verify installation:
   ```cmd
   python --version
   ```

## Step 2: Install Dependencies

Open PowerShell or Command Prompt in the project folder:

```cmd
cd C:\Users\DC\OneDrive\Desktop\AITUNER\AI-TUNER-AGENT
pip install -r requirements.txt
```

**Note:** Some dependencies are optional for the demo:
- `python-can` - Only needed for real CAN bus (not demo)
- `psycopg2-binary` - Only needed for cloud database (not demo)
- `PyAudio` - Only needed for voice input (not demo)

If any fail to install, the demo will still work!

## Step 3: Run the Demo

```cmd
python demo.py
```

That's it! The GUI window will open.

## Windows-Specific Notes

### Voice Output
Windows has built-in TTS, so voice output should work automatically. If you get errors:
```cmd
python demo.py --no-voice
```

### Display Issues
If the window doesn't appear:
- Make sure you're not running in WSL without X11
- Try running from a regular Command Prompt (not WSL)

### Missing DLL Errors
If you get DLL errors for PySide6:
```cmd
pip install --upgrade pyside6
```

## Alternative: Use Python Virtual Environment

For a clean setup:

```cmd
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run demo
python demo.py
```

## What You'll See

A window will open showing:
- ✅ Real-time telemetry dashboard
- ✅ Health monitoring
- ✅ AI insights
- ✅ Performance tracking
- ✅ All UI components working

## Troubleshooting

### "python is not recognized"
- Make sure Python is in your PATH
- Try `py` instead of `python`:
  ```cmd
  py demo.py
  ```

### "No module named PySide6"
```cmd
pip install pyside6 pyqtgraph
```

### Window appears but is blank
- Wait a few seconds for data to start flowing
- Check the console for error messages

## Production Use

For production on Windows:
- OBD-II adapters work via USB (COM ports)
- CAN bus requires USB-to-CAN adapter
- GPS modules work via USB/Serial

The demo works identically on Windows, Linux, and macOS! 🎉

