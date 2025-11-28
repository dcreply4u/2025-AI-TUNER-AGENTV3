# AI Tuner Project Context

**Last Updated:** December 2024  
**Purpose:** Context file for AI assistants to quickly understand the project state

---

## 🎯 Current Focus

**Active Development Areas:**
- CAN bus integration and decoding (cantools)
- CAN bus simulation for testing
- QA test suite development
- Enhanced CAN interface with DBC support
- Real-time CAN message decoding

**Recent Major Changes:**
- ✅ **Integrated cantools library** - DBC file parsing and CAN message decoding
- ✅ **Added CAN decoder service** - Real-time message decoding with signal extraction
- ✅ **Added CAN bus simulator** - Virtual CAN bus for testing without hardware
- ✅ **Enhanced CAN interface tab** - DBC loading, decoded messages view, DBC browser
- ✅ **Created QA test suite** - Comprehensive pytest-based testing framework
- ✅ **Added comprehensive documentation** - CANTOOLS_INTEGRATION.md, CAN_SIMULATOR_GUIDE.md

---

## 📁 Project Structure

```
C:\Users\DC\OneDrive\Desktop\AITUNER\
├── AI-TUNER-AGENT\              # Main development repo (v2 branch) - Legacy
├── 2025-AI-TUNER-AGENTV2\       # Secondary repo (main branch) - Legacy
├── 2025-AI-TUNER-AGENTV3\       # Latest V3 repo (main branch) ← WORK FROM HERE
└── v2\AI-TUNER-AGENT\           # Backup/reference
```

### Primary Working Directory
**Use `2025-AI-TUNER-AGENTV3` for new development work.**

### Repository Relationships
- **V3 (2025-AI-TUNER-AGENTV3)**: Primary active development, latest features
- **V2 (2025-AI-TUNER-AGENTV2)**: Previous version, kept for reference
- **AI-TUNER-AGENT**: Original repo on v2 branch, legacy codebase
- **v2/AI-TUNER-AGENT**: Backup copy

**Sync Strategy:** After major changes in V3, selectively copy critical files to other repos if needed.

---

## 🌐 GitHub Repositories

| Repo Name | Branch | URL |
|-----------|--------|-----|
| `ai-tuner-agent` | v2 | https://github.com/dcreply4u/ai-tuner-agent |
| `2025-AI-TUNER-AGENTV2` | main | https://github.com/dcreply4u/2025-AI-TUNER-AGENTV2 |
| `2025-AI-TUNER-AGENTV3` | main | https://github.com/dcreply4u/2025-AI-TUNER-AGENTV3 |

---

## 🍓 Raspberry Pi 5 Connection

```
IP Address: 192.168.1.214
Username: aituner
Password: aituner
Project Path: /home/aituner/AITUNER/2025-AI-TUNER-AGENTV3/
```

### SSH Commands (from Windows)
```powershell
# Run command on Pi
& "C:\Users\DC\OneDrive\Desktop\AITUNER\2025-AI-TUNER-AGENTV3\scripts\run_pi5_command.ps1" -Command "your command here"

# Copy file to Pi
$hostKey = "ssh-ed25519 255 SHA256:kYD1kP0J+ldb0WyphVRnikIRQgZJP1nnL6MzESnu2iw"
& "C:\Program Files\PuTTY\pscp.exe" -hostkey $hostKey -pw aituner "local\path" "aituner@192.168.1.214:/remote/path"

# Sync entire project to Pi (FIXED - now uses correct source path)
& "C:\Users\DC\OneDrive\Desktop\AITUNER\2025-AI-TUNER-AGENTV3\scripts\sync_to_pi5.ps1"
```

### ⚠️ Pi Sync Issue (FIXED)
**Problem:** Sync script was pointing to wrong source directory (`AI-TUNER-AGENT` instead of `2025-AI-TUNER-AGENTV3`)  
**Status:** ✅ Fixed in `scripts/sync_to_pi5.ps1`  
**If merge conflicts occur on Pi:** Use `fix_pi_merge.py` script on the Pi to resolve

---

## 🚀 Running the Demo

```powershell
cd C:\Users\DC\OneDrive\Desktop\AITUNER\2025-AI-TUNER-AGENTV3
python demo_safe.py
```

The demo uses `demo_safe.py` which:
1. Creates a minimal window first
2. Loads the MainWindow in background
3. Starts the DemoController with simulated data

---

## 🎨 UI Architecture

### Main Window (`ui/main.py`)
- **Platform-aware sizing:** Windows uses 70% width/65% height, Pi uses 85%
- **Two-column layout:**
  - Left: Telemetry, Health Score, AI Insights, Advice, Dragy Performance
  - Right: System Status, Camera & Streaming, Session Controls (with scroll)
- **Right column has vertical scrolling** (QScrollArea)

### Key UI Files
| File | Purpose |
|------|---------|
| `ui/main.py` | Main application window |
| `ui/main_container.py` | Full ECU interface with tabs |
| `ui/multi_row_tab_widget.py` | Custom tab widget with scrolling |
| `ui/telemetry_panel.py` | Live telemetry graphs |
| `ui/enhanced_widgets.py` | MetricCard, StatusIndicator, etc. |
| `ui/theme_manager.py` | 7 themes (Dark, Light, Racing, Modern, etc.) |
| `ui/can_interface_tab.py` | CAN bus monitor with DBC decoding and simulator |

### CAN Bus Features
| Component | Purpose |
|-----------|---------|
| `services/can_decoder.py` | DBC file parsing and CAN message decoding |
| `services/can_simulator.py` | Virtual CAN bus simulator for testing |
| `interfaces/can_interface.py` | Optimized CAN bus interface with monitoring |
| `interfaces/can_hardware_detector.py` | CAN hardware detection (Waveshare HAT) |
| `ui/can_interface_tab.py` | CAN interface UI with monitor, decoder, and simulator tabs |

### Multi-Row Tab Widget
- Tabs displayed in multiple rows (8 per row)
- Vertical scrolling when many tabs
- Auto-scrolls to selected tab

---

## 🔧 Recent Changes

### Latest Session (December 2024) - CAN Tools Integration
1. **Integrated cantools library** - Added DBC file parsing and CAN message decoding
2. **Created CAN decoder service** (`services/can_decoder.py`)
   - DBC file loading and management
   - Real-time message decoding with signal extraction
   - Support for multiple DBC databases
   - Signal value scaling and unit conversion
3. **Created CAN bus simulator** (`services/can_simulator.py`)
   - Virtual CAN bus using python-can's virtual interface
   - Periodic message transmission
   - DBC-based message generation
   - Dynamic signal value updates
4. **Enhanced CAN interface tab** (`ui/can_interface_tab.py`)
   - Added DBC file loading UI
   - Decoded Messages tab with real-time decoding
   - DBC Browser tab for browsing message definitions
   - Simulator tab with message configuration
5. **Created QA test suite** - Comprehensive pytest-based testing framework
   - File operations tests
   - Graphing tests
   - Data reading tests
   - AI advisor tests
   - Telemetry processing tests
   - Integration tests
6. **Added documentation**
   - `docs/CANTOOLS_INTEGRATION.md` - Complete DBC decoding guide
   - `docs/CAN_SIMULATOR_GUIDE.md` - Simulator usage guide

### Previous Session (Nov 26, 2025)
1. **Fixed Pi sync script** - Corrected source path to use `2025-AI-TUNER-AGENTV3`
2. **Updated PROJECT_CONTEXT.md** - Added current focus, troubleshooting, quick commands
3. **Documented merge conflict resolution** - Added scripts and procedures

### Previous Session (Nov 25, 2025)
1. **Platform-aware window sizing** - Windows uses 70%/65%, Pi uses 85%
2. **Vertical scroll for right column** - Controls can be scrolled
3. **Multi-row tab widget scrolling** - Tabs have vertical scroll (8 per row)
4. **QTimer import fix** - Removed shadowing in data_stream_controller.py
5. **Code quality improvements** - Fixed wildcard imports, split requirements, added input validation
6. **Created V3 repo** - Clean starting point for new development

### Code Review Fixes (Nov 25, 2025)
**All fixes completed and pushed to GitHub:**
- ✅ **Fixed wildcard imports** - Replaced `import *` with explicit imports using AST parsing
- ✅ **Split requirements** - Created `requirements-core.txt` and `requirements-optional.txt`
- ✅ **Input validation** - Added `InputValidator` class with comprehensive validation
- ✅ **Security improvements** - Added input sanitization, SQL injection protection
- ✅ **Error handling** - Improved exception handling and logging throughout
- ✅ **Documentation** - Enhanced docstrings and code comments
- ✅ **Merge conflict scripts** - Created `fix_pi_merge.py` for Pi conflict resolution

---

## 📝 Key Patterns & Conventions

### Imports
```python
# PySide6 with PyQt6 fallback
try:
    from PySide6.QtWidgets import ...
except ImportError:
    from PyQt6.QtWidgets import ...
```

### Size Policies
```python
# Expanding horizontally, shrink vertically
widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
```

### Scroll Areas
```python
scroll = QScrollArea()
scroll.setWidgetResizable(True)
scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
```

### Error Handling
```python
# Use logging for errors
import logging
LOGGER = logging.getLogger(__name__)

try:
    # operation
except Exception as e:
    LOGGER.error("Operation failed: %s", e, exc_info=True)
```

### Platform Detection
```python
import sys
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")
IS_PI = IS_LINUX and os.path.exists("/proc/device-tree/model")
```

### Input Validation
```python
from core.input_validator import InputValidator
validator = InputValidator()
if not validator.validate_rpm(value):
    raise ValueError("Invalid RPM value")
```

---

## ⚠️ Known Issues / Notes

1. **Camera errors in logs** - Normal when no camera connected (OpenCV probing)
2. **ECU detection fails** - Normal in demo mode (no hardware)
3. **Voice control** - Requires `SpeechRecognition` and `PyAudio` packages
4. **GitHub push protection** - Don't commit files with tokens (push_now.ps1)
5. **Pi merge conflicts** - If sync fails due to merge conflicts, use `fix_pi_merge.py` on Pi

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### Pi Sync Fails
**Symptom:** `sync_to_pi5.ps1` fails or syncs wrong files  
**Solution:** 
- Verify script uses correct source path: `2025-AI-TUNER-AGENTV3`
- Check PuTTY installation: `C:\Program Files\PuTTY\pscp.exe`
- Test SSH connection: `scripts/test_ssh_connection.ps1`

#### Merge Conflicts on Pi
**Symptom:** Git pull fails with merge conflicts  
**Solution:**
```bash
# On Pi, run:
cd ~/AITUNER/2025-AI-TUNER-AGENTV3
python3 fix_pi_merge.py
```

#### Demo Won't Start
**Symptom:** `demo_safe.py` crashes or window doesn't appear  
**Solution:**
- Check Python version: `python --version` (needs 3.9+)
- Install dependencies: `pip install -r requirements-core.txt`
- Check logs: `logs/ai_tuner.log`

#### Import Errors
**Symptom:** `ModuleNotFoundError` or import failures  
**Solution:**
- Install core deps: `pip install -r requirements-core.txt`
- Install optional deps if needed: `pip install -r requirements-optional.txt`
- Check virtual environment activation

#### Camera Not Detected
**Symptom:** Camera widget shows "No camera"  
**Solution:**
- This is normal if no camera connected
- Check USB camera: `lsusb` (Linux) or Device Manager (Windows)
- Test with: `python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"`

#### CAN Decoder Not Working
**Symptom:** DBC files won't load or messages not decoding  
**Solution:**
- Install cantools: `pip install cantools`
- Verify DBC file is valid: `python -m cantools dump your_file.dbc`
- Check CAN ID exists in DBC browser tab
- Ensure correct DBC database is active (use dropdown)

#### CAN Simulator Not Starting
**Symptom:** Simulator fails to start or messages not appearing  
**Solution:**
- Verify python-can is installed: `pip install python-can`
- On Linux, ensure vcan module loaded: `sudo modprobe vcan`
- Check that monitor is listening on same channel (e.g., vcan0)
- Verify message is enabled in simulator table

---

## ⚡ Quick Commands Cheat Sheet

### Development
```powershell
# Run demo
cd 2025-AI-TUNER-AGENTV3
python demo_safe.py

# Install dependencies
pip install -r requirements-core.txt
pip install -r requirements-optional.txt  # Optional features

# Run tests
python -m pytest tests/
```

### Git Operations
```powershell
# Commit and push
git add .
git commit -m "Description"
git push origin main

# Check status
git status
git log --oneline -10
```

### Pi Operations
```powershell
# Sync to Pi
.\scripts\sync_to_pi5.ps1

# Run command on Pi
.\scripts\run_pi5_command.ps1 -Command "python3 demo_safe.py"

# Test SSH connection
.\scripts\test_ssh_connection.ps1
```

### Testing
```powershell
# Test demo
python demo_safe.py

# Test minimal window
python test_minimal_window.py

# Test integration
python test_integration.py

# Run QA test suite
python tests/run_all_tests.py
# Or use pytest directly
pytest tests/
```

### CAN Bus Operations
```powershell
# Load DBC file (via UI)
# 1. Open CAN Bus Interface tab
# 2. Click "Load DBC File" button
# 3. Select your .dbc file

# Start CAN simulator (via UI)
# 1. Open CAN Bus Interface tab
# 2. Go to "Simulator" tab
# 3. Click "Start Simulator"
# 4. Add messages as needed

# Or use programmatically:
from services.can_decoder import CANDecoder
from services.can_simulator import CANSimulator

decoder = CANDecoder()
decoder.load_dbc("vehicle.dbc")

simulator = CANSimulator(channel="vcan0", dbc_decoder=decoder)
simulator.add_dbc_message("EngineData", {"RPM": 3000.0}, period=0.1)
simulator.start()
```

---

## 🔄 Sync Workflow

### Standard Development Flow
1. **Make changes** in `2025-AI-TUNER-AGENTV3`
2. **Test locally** with `python demo_safe.py`
3. **Commit and push** to GitHub:
   ```powershell
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```
4. **Sync to Pi** using fixed script:
   ```powershell
   .\scripts\sync_to_pi5.ps1
   ```
5. **Copy to other repos** only if needed (selective sync)

### Pi Sync Process
1. Run `sync_to_pi5.ps1` from V3 directory
2. Script creates directories on Pi if needed
3. Copies essential files first (requirements.txt, demo_safe.py, README.md)
4. Then copies directories (services, ui, controllers, etc.)
5. If merge conflicts occur on Pi, run `fix_pi_merge.py` on Pi

### Handling Merge Conflicts on Pi
If sync fails due to merge conflicts:
```bash
# SSH to Pi first, then:
cd ~/AITUNER/2025-AI-TUNER-AGENTV3
python3 fix_pi_merge.py
# Or use resolve_merge_simple.sh for automatic resolution
```

---

## 📦 Dependencies

Main packages:
- PySide6 (Qt GUI framework)
- pyqtgraph (graphing)
- opencv-python (camera)
- obd (OBD-II interface)
- python-can (CAN bus)
- **cantools** (DBC file parsing and CAN message decoding) ⭐ NEW
- scipy, numpy (calculations)
- pytest (testing framework) ⭐ NEW

Install on Pi:
```bash
pip3 install PySide6 pyqtgraph obd python-can cantools opencv-python scipy numpy pytest --break-system-packages
```

### CAN Bus Dependencies
- **python-can** - CAN bus interface library
- **cantools** - DBC file parsing and message encoding/decoding
- Both are included in `requirements.txt`

---

## 💡 Tips for Next AI

1. **Always work from V3 repo** (`2025-AI-TUNER-AGENTV3`) - This is the primary working directory
2. **Run demo_safe.py** to test changes (not demo.py) - Safe version handles errors gracefully
3. **Use sync_to_pi5.ps1** for Pi sync (now fixed with correct path)
4. **Check logs** in `logs/` directory for debugging
5. **Platform detection:** Use `IS_WINDOWS`, `IS_LINUX`, `IS_PI` constants for OS-specific code
6. **Input validation:** Use `InputValidator` class from `core/input_validator.py`
7. **Requirements:** Install `requirements-core.txt` first, then optional features
8. **Git workflow:** Commit frequently, push to GitHub, then sync to Pi
9. **Merge conflicts:** Use `fix_pi_merge.py` on Pi if conflicts occur
10. **Testing:** Run `python demo_safe.py` before committing major changes
11. **CAN Bus:** Use `CANDecoder` for DBC decoding, `CANSimulator` for testing ⭐ NEW
12. **DBC Files:** Load DBC files via CAN interface tab → "Load DBC File" button ⭐ NEW
13. **CAN Simulator:** Use Simulator tab in CAN interface to test without hardware ⭐ NEW
14. **QA Tests:** Run `python tests/run_all_tests.py` for comprehensive testing ⭐ NEW

---

*This file should be kept updated as the project evolves.*

