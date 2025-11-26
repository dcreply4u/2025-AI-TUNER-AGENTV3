# CSS-Like Style System

## Overview

The application now uses a centralized, CSS-like style system where you can change colors in one place (`ThemeColors` class) and they update globally across all widgets.

## How It Works

### 1. Define Colors in `ThemeColors` (ui/theme_manager.py)

All semantic colors are defined in the `ThemeColors` dataclass:

```python
@dataclass
class ThemeColors:
    # Semantic color names - change these to update globally
    title: str = "#ff2a2a"  # Main panel titles
    title_secondary: str = "#ff6b00"  # Gauge titles, metric labels
    gauge_title: str = "#ff6b00"  # Individual gauge titles
    gauge_value: str = "#ffffff"  # Digital gauge values
    scrollbar: str = "#3498db"  # Scrollbar handle color
    # ... etc
```

**To change a color globally, just modify it here!**

### 2. Use `Style` Class in Widgets

Instead of hardcoded colors, widgets use the `Style` class:

```python
from ui.theme_manager import Style

# In your widget code:
painter.setPen(QColor(Style.title()))  # Gets current theme's title color
painter.setPen(QColor(Style.gauge_title()))  # Gets gauge title color
```

### 3. Example: Updating Gauge Widget

**Before (hardcoded):**
```python
painter.setPen(QColor("#ff6b00"))  # Hardcoded orange
```

**After (centralized):**
```python
from ui.theme_manager import Style
painter.setPen(QColor(Style.gauge_title()))  # Uses centralized color
```

## Available Style Properties

### Title Colors
- `Style.title()` - Main panel titles (e.g., "LIVE GAUGES")
- `Style.title_secondary()` - Secondary titles (e.g., gauge titles)
- `Style.title_tertiary()` - Tertiary titles

### Gauge Colors
- `Style.gauge_title()` - Individual gauge titles
- `Style.gauge_value()` - Digital gauge values
- `Style.gauge_border()` - Gauge value box border
- `Style.gauge_needle()` - Gauge needle color

### Scrollbar Colors
- `Style.scrollbar()` - Scrollbar handle color
- `Style.scrollbar_background()` - Scrollbar track color

### Drag Mode Colors
- `Style.drag_mode_title()` - Drag Mode panel title
- `Style.drag_mode_metric()` - Drag Mode metric titles
- `Style.drag_mode_value()` - Drag Mode values

### Button Colors
- `Style.button_primary()` - Primary button color
- `Style.button_hover()` - Button hover color

### Status Colors
- `Style.status_optimal()` - Optimal status (green)
- `Style.status_warning()` - Warning status (orange)
- `Style.status_danger()` - Danger status (red)

## Benefits

1. **Single Source of Truth**: Change colors in one place (`ThemeColors`)
2. **Global Updates**: All widgets using `Style` automatically get the new colors
3. **Easy Maintenance**: No need to search and replace across multiple files
4. **Consistency**: Ensures all widgets use the same color scheme
5. **Theme Support**: Can easily switch themes by changing the `ThemeManager` theme

## Migration Guide

To migrate existing widgets:

1. Import `Style`:
   ```python
   from ui.theme_manager import Style
   ```

2. Replace hardcoded colors:
   ```python
   # Old
   color = "#ff6b00"
   
   # New
   color = Style.gauge_title()
   ```

3. For stylesheets, use f-strings:
   ```python
   # Old
   stylesheet = "color: #ff6b00;"
   
   # New
   stylesheet = f"color: {Style.gauge_title()};"
   ```

## Adding New Semantic Colors

1. Add the color to `ThemeColors` in `ui/theme_manager.py`:
   ```python
   my_new_color: str = "#ff0000"  # Red
   ```

2. Add a method to the `Style` class:
   ```python
   @classmethod
   def my_new_color(cls) -> str:
       """Description of what this color is for."""
       return cls._get_colors().my_new_color
   ```

3. Use it in widgets:
   ```python
   painter.setPen(QColor(Style.my_new_color()))
   ```

## Notes

- The `Style` class is initialized automatically in `main.py`
- Colors are accessed via class methods (e.g., `Style.title()`)
- All colors are strings in hex format (e.g., `"#ff2a2a"`)
- The system supports theme switching - colors update when theme changes

