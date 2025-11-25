# AI Tuner Project Context

**Last Updated:** November 25, 2025  
**Purpose:** Context file for AI assistants to quickly understand the project state

---

## 📁 Project Structure

```
C:\Users\DC\OneDrive\Desktop\AITUNER\
├── AI-TUNER-AGENT\              # Main development repo (v2 branch)
├── 2025-AI-TUNER-AGENTV2\       # Secondary repo (main branch)
├── 2025-AI-TUNER-AGENTV3\       # Latest V3 repo (main branch) ← WORK FROM HERE
└── v2\AI-TUNER-AGENT\           # Backup/reference
```

### Primary Working Directory
**Use `2025-AI-TUNER-AGENTV3` for new development work.**

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
Project Path: /home/aituner/AITUNER/AI-TUNER-AGENT/
```

### SSH Commands (from Windows)
```powershell
# Run command on Pi
& "C:\Users\DC\OneDrive\Desktop\AITUNER\AI-TUNER-AGENT\scripts\run_pi5_command.ps1" -Command "your command here"

# Copy file to Pi
$hostKey = "ssh-ed25519 255 SHA256:kYD1kP0J+ldb0WyphVRnikIRQgZJP1nnL6MzESnu2iw"
& "C:\Program Files\PuTTY\pscp.exe" -hostkey $hostKey -pw aituner "local\path" "aituner@192.168.1.214:/remote/path"
```

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

### Multi-Row Tab Widget
- Tabs displayed in multiple rows (8 per row)
- Vertical scrolling when many tabs
- Auto-scrolls to selected tab

---

## 🔧 Recent Changes (This Session)

1. **Platform-aware window sizing** - Windows vs Pi/Linux different defaults
2. **Vertical scroll for right column** - Controls can be scrolled
3. **Multi-row tab widget scrolling** - Tabs have vertical scroll
4. **QTimer import fix** - Removed shadowing in data_stream_controller.py
5. **Created V3 repo** - Clean starting point

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

---

## ⚠️ Known Issues / Notes

1. **Camera errors in logs** - Normal when no camera connected (OpenCV probing)
2. **ECU detection fails** - Normal in demo mode (no hardware)
3. **Voice control** - Requires `SpeechRecognition` and `PyAudio` packages
4. **GitHub push protection** - Don't commit files with tokens (push_now.ps1)

---

## 🔄 Sync Workflow

When making changes:
1. Make changes in `2025-AI-TUNER-AGENTV3`
2. Test with `python demo_safe.py`
3. Commit and push to GitHub
4. Copy changed files to other repos if needed
5. Sync to Pi 5 using pscp

---

## 📦 Dependencies

Main packages:
- PySide6 (Qt GUI framework)
- pyqtgraph (graphing)
- opencv-python (camera)
- obd (OBD-II interface)
- python-can (CAN bus)
- scipy, numpy (calculations)

Install on Pi:
```bash
pip3 install PySide6 pyqtgraph obd python-can opencv-python scipy numpy --break-system-packages
```

---

## 💡 Tips for Next AI

1. **Always work from V3 repo** (`2025-AI-TUNER-AGENTV3`)
2. **Run demo_safe.py** to test changes (not demo.py)
3. **Use pscp with hostkey** for Pi file transfers
4. **Check terminal output** at `~/.cursor/projects/.../terminals/` 
5. **Platform detection:** Check `IS_WINDOWS` for OS-specific code
6. **Keep all 3 repos in sync** after major changes

---

*This file should be kept updated as the project evolves.*

