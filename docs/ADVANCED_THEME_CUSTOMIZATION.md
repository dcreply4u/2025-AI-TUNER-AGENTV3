# Advanced Theme Customization System

**Date:** 2024  
**Status:** ✅ Implemented  
**Features:** System-wide dark mode, accent colors, gauge customization, OLED optimization, accessibility validation

---

## Executive Summary

The Advanced Theme Customization System provides comprehensive UI theme customization for the racing tuning app, prioritizing user comfort, accessibility, and battery efficiency. The system includes automatic system theme detection, manual overrides, accent color selection, gauge customization, OLED optimization, and real-time contrast validation.

---

## Features

### 1. System-Wide Dark Mode Support

**Automatic Detection:**
- Detects operating system theme preference (Windows, macOS, Linux)
- Automatically applies matching theme on startup
- Follows platform conventions

**Manual Override:**
- Users can force dark mode regardless of system setting
- Users can force light mode for bright daylight use
- Changes apply instantly without restart

**Implementation:**
```python
from ui.advanced_theme_customizer import SystemThemeDetector, SystemThemeMode

# Detect system theme
detected = SystemThemeDetector.detect_system_theme()
# Returns: SystemThemeMode.DARK or SystemThemeMode.LIGHT

# Set theme mode
customizer.customization.system_theme_mode = SystemThemeMode.AUTO  # Follow system
customizer.customization.system_theme_mode = SystemThemeMode.DARK   # Force dark
customizer.customization.system_theme_mode = SystemThemeMode.LIGHT  # Force light
```

---

### 2. Accent Color Chooser

**Features:**
- Full color picker with hex input
- Preset colors (Electric Blue, Racing Green, Safety Orange, etc.)
- Real-time preview
- Accessibility validation

**Preset Colors:**
- Electric Blue: `#00e0ff`
- Racing Green: `#00ff88`
- Safety Orange: `#ff8000`
- Vibrant Red: `#ff4444`
- Bright Yellow: `#ffff00`
- Neon Purple: `#ff00ff`

**Usage:**
```python
# Set accent color
customizer.customization.accent_color = "#00e0ff"

# Apply to theme
customizer._apply_theme()
```

---

### 3. Customizable Gauges

**Customizable Elements:**
- Needle color
- Background color
- Scale color
- Text color
- Warning zone color
- Critical zone color

**Implementation:**
```python
from ui.advanced_theme_customizer import GaugeCustomization

gauge_customization = GaugeCustomization(
    needle_color="#00e0ff",
    background_color="#1a1f35",
    scale_color="#ffffff",
    text_color="#ffffff",
    warning_zone_color="#ffaa00",
    critical_zone_color="#ff4444",
)

# Apply to gauges
for gauge in dashboard.gauges.values():
    gauge.set_customization(
        needle_color=gauge_customization.needle_color,
        background_color=gauge_customization.background_color,
        scale_color=gauge_customization.scale_color,
        text_color=gauge_customization.text_color,
        warning_zone_color=gauge_customization.warning_zone_color,
        critical_zone_color=gauge_customization.critical_zone_color,
    )
```

---

### 4. True Black OLED Optimization

**Features:**
- True black background (`#000000`) for OLED displays
- Saves battery life on OLED/AMOLED screens
- Maximum contrast for visibility
- Optional setting (can be disabled)

**Usage:**
```python
# Enable OLED optimization
customizer.customization.oled_optimized = True
customizer.customization.true_black_background = True

# Apply theme
customizer._apply_theme()
```

**Benefits:**
- **Battery Savings:** Up to 30% battery savings on OLED displays
- **Contrast:** Maximum contrast ratio for visibility
- **Eye Strain:** Reduced eye strain in low-light conditions

---

### 5. Instant Preview

**Features:**
- Real-time preview of theme changes
- No restart required
- Updates all widgets instantly
- Preview tab in customization dialog

**Implementation:**
- Uses Qt signal/slot mechanism for instant updates
- Debounced updates to prevent performance issues
- Applies to all widgets simultaneously

---

### 6. Readability & Contrast Validation

**WCAG Compliance:**
- Validates contrast ratios against WCAG standards
- AA Level: 4.5:1 minimum contrast ratio
- AAA Level: 7:1 enhanced contrast ratio

**Auto-Fix:**
- Automatically suggests accessible colors
- Fixes contrast issues with one click
- Validates all color combinations

**Implementation:**
```python
from ui.advanced_theme_customizer import ContrastValidator

# Check contrast
is_accessible, ratio = ContrastValidator.is_accessible(
    text_color="#ffffff",
    background_color="#000000",
    level="AA"
)

# Get contrast ratio
ratio = ContrastValidator.get_contrast_ratio("#ffffff", "#000000")
# Returns: 21.0 (maximum contrast)

# Suggest accessible color
suggested = ContrastValidator.suggest_accessible_color(
    text_color="#888888",  # Too low contrast
    background_color="#000000"
)
# Returns: "#ffffff" (high contrast)
```

---

## Usage Guide

### Opening Theme Customizer

1. Click "Theme Settings" button in the main UI
2. Or use voice command: "Open theme settings"
3. Dialog opens with 5 tabs:
   - **General:** System theme, OLED optimization, font scaling
   - **Colors:** Accent color selection, contrast validation
   - **Gauges:** Gauge color customization
   - **Accessibility:** Contrast information and validation
   - **Preview:** Real-time theme preview

### Customizing Theme

1. **Select System Theme Mode:**
   - Choose "Follow System" for automatic detection
   - Choose "Force Dark" or "Force Light" for manual override

2. **Choose Accent Color:**
   - Click "Choose Color..." to open color picker
   - Or click preset color buttons
   - Preview updates instantly

3. **Customize Gauges:**
   - Select each gauge element (needle, background, scale, etc.)
   - Choose colors from color picker
   - Preview updates in real-time

4. **Enable OLED Optimization:**
   - Check "Enable OLED Optimization"
   - Check "Use True Black Background"
   - Saves battery on OLED displays

5. **Validate Accessibility:**
   - Check contrast ratios in "Accessibility" tab
   - Click "Auto-Fix Contrast Issues" if needed
   - System ensures all colors meet WCAG standards

6. **Apply Changes:**
   - Click "OK" to apply and save
   - Or click "Cancel" to discard changes
   - Changes apply instantly without restart

---

## Integration

### With Existing Theme System

The advanced theme customizer integrates seamlessly with the existing `ThemeManager`:

```python
from ui.theme_manager import ThemeManager
from ui.advanced_theme_customizer import AdvancedThemeCustomizer

# Initialize theme manager
theme_manager = ThemeManager()

# Open customizer
customizer = AdvancedThemeCustomizer(theme_manager, parent_widget)
customizer.theme_changed.connect(on_theme_changed)
customizer.exec()
```

### With Gauge Widgets

Gauge widgets support customization:

```python
from ui.gauge_widget import CircularGauge

# Create gauge with custom colors
gauge = CircularGauge(
    "RPM",
    min_value=0,
    max_value=8000,
    needle_color="#00e0ff",
    background_color="#1a1f35",
    scale_color="#ffffff",
)

# Or update existing gauge
gauge.set_customization(
    needle_color="#ff0000",
    background_color="#000000",
)
```

---

## Configuration Storage

Theme customizations are saved to `config/theme_customization.json`:

```json
{
  "system_theme_mode": "auto",
  "accent_color": "#00e0ff",
  "oled_optimized": false,
  "true_black_background": false,
  "high_contrast": true,
  "font_size_scale": 1.0,
  "gauge_customization": {
    "needle_color": "#00e0ff",
    "background_color": "#1a1f35",
    "scale_color": "#ffffff",
    "text_color": "#ffffff",
    "warning_zone_color": "#ffaa00",
    "critical_zone_color": "#ff4444"
  }
}
```

---

## Best Practices

1. **Accessibility First:**
   - Always validate contrast ratios
   - Use auto-fix if contrast is too low
   - Test with different lighting conditions

2. **OLED Optimization:**
   - Enable for OLED/AMOLED displays
   - Disable for LCD displays (no benefit)
   - True black provides maximum contrast

3. **System Theme:**
   - Use "Follow System" for best user experience
   - Allow manual override for specific use cases
   - Respect user preferences

4. **Gauge Customization:**
   - Ensure warning/critical colors are distinct
   - Maintain high contrast for readability
   - Test in various lighting conditions

5. **Performance:**
   - Instant preview is debounced for performance
   - Changes apply to all widgets simultaneously
   - No restart required

---

## Technical Details

### System Theme Detection

**Windows:**
- Reads `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize\AppsUseLightTheme`
- Returns `SystemThemeMode.LIGHT` if `1`, `SystemThemeMode.DARK` if `0`

**macOS:**
- Runs `defaults read -g AppleInterfaceStyle`
- Returns `SystemThemeMode.DARK` if "Dark" in output

**Linux:**
- Uses `gsettings get org.gnome.desktop.interface gtk-theme`
- Checks for "dark" in theme name

### Contrast Calculation

Uses WCAG 2.1 relative luminance formula:

```
L = 0.2126 * R + 0.7152 * G + 0.0722 * B
```

Contrast ratio:
```
(L1 + 0.05) / (L2 + 0.05)
```

Where L1 is the lighter color and L2 is the darker color.

---

## Conclusion

The Advanced Theme Customization System provides:

- ✅ **System-wide dark mode** with automatic detection
- ✅ **Manual dark/light toggle** for user preference
- ✅ **Accent color chooser** with presets and validation
- ✅ **Customizable gauges** (needle, background, scale, text, zones)
- ✅ **True black OLED optimization** for battery savings
- ✅ **Instant preview** without restart
- ✅ **WCAG-compliant contrast validation** for accessibility

The system is production-ready and fully integrated with the existing theme system.



