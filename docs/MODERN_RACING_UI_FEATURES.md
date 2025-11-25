# Modern Racing UI Features Documentation

## Overview

The Modern Racing UI enhancements provide a professional, high-contrast interface designed for clarity, safety, and efficiency in performance environments. The design minimizes distraction while maximizing critical information visibility.

## Core Components

### 1. Modern Racing Dashboard

**Location:** `ui/modern_racing_dashboard.py`

**Purpose:** Customizable cockpit view showing essential real-time data with digital gauges and warning indicators.

**Features:**
- **Digital Gauges:** RPM, Speed, Boost, Coolant Temp, AFR, Knock
- **Warning Indicators:** Color-coded with flashing capability
  - Overheat (yellow warning, red critical)
  - Knock (yellow warning, red critical)
  - Lean AFR (yellow warning, red critical)
  - Overboost (yellow warning, red critical)
- **Quick Access Buttons:**
  - Start/Stop Data Logging
  - AI Advisor (opens chat overlay)
- **Connection Status Indicator:** Visual indicator (green connected, red disconnected)
- **Panic Button:** Emergency safe stock map flash

**Usage:**
```python
from ui.modern_racing_dashboard import ModernRacingDashboard

def get_telemetry():
    return {"RPM": 5000, "Boost": 15.0, "CoolantTemp": 95.0, ...}

def panic_callback():
    # Flash safe stock map to ECU
    pass

def ai_advisor_callback():
    # Open AI advisor chat
    pass

dashboard = ModernRacingDashboard(
    telemetry_provider=get_telemetry,
    panic_callback=panic_callback,
    ai_advisor_callback=ai_advisor_callback
)
```

**Integration:** Automatically added as the first tab in `MainContainerWindow`.

### 2. Floating AI Advisor

**Location:** `ui/floating_ai_advisor.py`

**Purpose:** Persistent floating icon with chat overlay that's always accessible from any screen.

**Components:**
- **FloatingAIIcon:** Draggable floating icon (bottom-right by default)
- **AIChatOverlay:** Chat window that overlays current screen
- **FloatingAIAdvisorManager:** Manages icon and overlay lifecycle

**Features:**
- Always-on-top floating icon
- Draggable positioning
- Chat overlay with actionable suggestions
- Navigation buttons for AI recommendations
- Integrates with existing `AIAdvisorWidget`

**Usage:**
```python
from ui.floating_ai_advisor import FloatingAIAdvisorManager

# In main window initialization
self.ai_advisor_manager = FloatingAIAdvisorManager(self)
```

**Voice Commands:**
- "AI Advisor" - Opens chat
- "Q" - Opens chat
- "Ask..." - Opens chat with question

### 3. Voice Command Handler

**Location:** `ui/voice_command_handler.py`

**Purpose:** Hands-free voice input for AI advisor and navigation.

**Features:**
- Speech recognition (requires `speech_recognition` library)
- Background listening in separate thread
- Command routing to appropriate handlers

**Supported Commands:**
- "AI Advisor" / "Q" / "Ask..." - Open AI advisor
- "Dashboard" - Navigate to dashboard tab
- "Telemetry" - Navigate to telemetry tab
- "Diagnostics" - Navigate to diagnostics tab
- "Panic" / "Safe Map" - Activate panic button

**Usage:**
```python
from ui.voice_command_handler import VoiceCommandHandler

voice_handler = VoiceCommandHandler()
if voice_handler.is_available():
    voice_handler.command_received.connect(handle_command)
    voice_handler.start_listening()
```

**Dependencies:**
```bash
pip install SpeechRecognition
```

### 4. Map Comparison View

**Location:** `ui/map_comparison_view.py`

**Purpose:** Side-by-side or overlay comparison of tuning maps with color-coded differences.

**Features:**
- **Side-by-Side Mode:** Current map vs base map
- **Overlay Mode:** Color-coded differences
  - Green: Higher values
  - Red: Lower values
  - Transparent: Same values
- **Difference Highlighting:** Toggle to show/hide differences
- **Cell-by-Cell Comparison:** Visual comparison of individual cells

**Usage:**
```python
from ui.map_comparison_view import MapComparisonDialog

current_map = [[...], [...]]  # 2D array of values
base_map = [[...], [...]]     # 2D array of values

dialog = MapComparisonDialog(current_map, base_map, parent=self)
dialog.exec()
```

### 5. Haptic Feedback

**Location:** `ui/haptic_feedback.py`

**Purpose:** Tactile feedback for button presses and critical warnings.

**Features:**
- Button press feedback
- Warning alerts (double pulse)
- Critical alerts (triple pulse)
- Success feedback (single pulse)

**Usage:**
```python
from ui.haptic_feedback import get_haptic_feedback

haptic = get_haptic_feedback()
haptic.button_press()    # Single pulse
haptic.warning()         # Double pulse
haptic.critical()        # Triple pulse
haptic.success()         # Single short pulse
```

**Platform Support:**
- Windows: Basic support (placeholder for future implementation)
- Linux: Basic support
- Mobile: Would require platform-specific APIs

## Design Principles

### Dark Mode & High Contrast

- **Background:** Very dark (#0a0e27) to reduce eye strain
- **Primary Color:** Electric blue (#00e0ff) for high contrast
- **Accent Colors:**
  - Green (#00ff88) for success/normal
  - Orange (#ffaa00) for warnings
  - Red (#ff4444) for errors/critical
- **Text:** Pure white (#ffffff) for maximum legibility

### Minimalist & Focused

- Clean layouts with plenty of dark space
- Prioritize critical data
- Avoid unnecessary visual flair
- Large, clear fonts for quick reading

### Safety Features

- **Panic Button:** Prominent, easy-to-reach emergency button
- **Warning Indicators:** Flashing animations for critical alerts
- **Connection Status:** Clear visual feedback for hardware connection

## Integration Points

### Main Container Integration

All components are integrated into `MainContainerWindow`:

1. **Dashboard:** Added as first tab
2. **Floating AI Advisor:** Initialized on startup
3. **Voice Handler:** Initialized on startup (if available)
4. **Haptic Feedback:** Available globally via `get_haptic_feedback()`
5. **Connection Status:** Updated in real-time via `update_telemetry()`

### Theme Integration

Components use the enhanced dark theme from `ThemeManager`:
- High contrast colors
- Consistent styling
- Responsive scaling via `UIScaler`

### Telemetry Integration

Dashboard receives real-time telemetry updates:
- Automatic updates every 100ms
- Warning thresholds configured per sensor
- Visual feedback for all critical parameters

## Configuration

### Dashboard Customization

Gauges can be customized by modifying `ModernRacingDashboard.setup_ui()`:
```python
gauge_configs = [
    ("RPM", 0, 8000, "rpm", 0, 0),
    ("Speed", 0, 200, "mph", 0, 1),
    # Add more gauges...
]
```

### Warning Thresholds

Warning thresholds are configured in `_update_data()`:
```python
# Overheat warning
if coolant > 110:
    self.warning_indicators["overheat"].set_warning("critical")
elif coolant > 100:
    self.warning_indicators["overheat"].set_warning("warning")
```

### Voice Command Customization

Add new commands in `MainContainerWindow._handle_voice_command()`:
```python
elif "your command" in text_lower:
    # Handle command
```

## Troubleshooting

### Dashboard Not Showing Data

1. Check `telemetry_provider` is returning data
2. Verify telemetry keys match gauge names
3. Check update timer is running

### Floating AI Icon Not Visible

1. Check `FloatingAIAdvisorManager` is initialized
2. Verify window flags are set correctly
3. Check icon position (may be off-screen)

### Voice Commands Not Working

1. Install `speech_recognition`: `pip install SpeechRecognition`
2. Check microphone permissions
3. Verify `VoiceCommandHandler.is_available()` returns `True`

### Haptic Feedback Not Working

1. Check platform support
2. Verify `get_haptic_feedback().is_available()` returns `True`
3. Ensure haptic is enabled: `haptic.enable()`

## Best Practices

1. **Always provide telemetry provider** to dashboard for real-time updates
2. **Initialize floating AI advisor** early in application lifecycle
3. **Handle voice commands gracefully** - they're optional
4. **Use haptic feedback sparingly** - too much can be distracting
5. **Test warning indicators** with actual threshold values
6. **Keep dashboard minimal** - only show critical data

## Future Enhancements

- Touch gesture support for map editing
- Customizable gauge layouts
- Additional voice commands
- Platform-specific haptic implementations
- Dashboard widget customization UI
- Multi-screen support for dashboard

## Related Documentation

- `AI_ADVISOR_ULTRA_ENHANCED_IMPLEMENTATION.md` - AI advisor features
- `THEME_MANAGER.md` - Theme system documentation
- `UI_SCALING.md` - UI scaling system
- `ARCHITECTURE.md` - Overall architecture



