# Global Responsive UI Implementation

## Overview

This document describes the global responsive UI system implemented across the AI Tuner Agent application. The system ensures that all UI elements adapt gracefully to different window sizes, screen resolutions, and device types.

## Core Principles

### 1. Fluid Layouts
- Use relative units (scaled pixels) instead of fixed pixel values
- All spacing, margins, and sizes scale proportionally with window size
- Base reference size: 1280x720 pixels

### 2. Breakpoint-Based Design
The system uses six breakpoints for responsive behavior:

- **XS** (480px): Extra small - Mobile devices
- **SM** (768px): Small - Tablet portrait
- **MD** (1024px): Medium - Tablet landscape
- **LG** (1280px): Large - Desktop (default)
- **XL** (1920px): Extra large - Large desktop
- **XXL** (2560px): 2K/4K displays

### 3. Flexible Elements
- Graphs and plots automatically resize with their containers
- Images scale proportionally without distortion
- Text remains legible at all sizes

### 4. Content Prioritization
- Critical information remains visible at all breakpoints
- Secondary features may be hidden or simplified on smaller screens
- Layout adapts to available space

### 5. Consistency
- Visual hierarchy maintained across all screen sizes
- Interaction patterns remain familiar
- Platform conventions followed (Windows, macOS, Linux)

### 6. User Control
- Window size and position are saved and restored
- Users can manually resize windows
- Preferences persist across sessions

## Implementation

### ResponsiveLayoutManager

The `ResponsiveLayoutManager` class (`ui/responsive_layout_manager.py`) is the core of the responsive system:

```python
from ui.responsive_layout_manager import get_responsive_manager, scaled_size, scaled_font_size, scaled_spacing

# Get the global manager
manager = get_responsive_manager()

# Apply to a window
manager.apply_to_window(window)

# Use scaling functions
width = scaled_size(100)  # Scales based on window width
height = scaled_size(100, use_width=False)  # Scales based on window height
font_size = scaled_font_size(14)  # Scales font size
spacing = scaled_spacing(10)  # Scales spacing/margins
```

### Key Features

1. **Automatic Window State Management**
   - Saves window size and position on close
   - Restores window state on startup
   - Handles multi-monitor setups

2. **Dynamic Breakpoint Detection**
   - Automatically detects current breakpoint based on window width
   - Emits signals when breakpoint changes
   - Updates UI elements accordingly

3. **Scale Factor Calculation**
   - Calculates width and height scale factors
   - Computes font scale factor (average of width/height)
   - Applies breakpoint-specific adjustments

4. **Graph Responsive Configuration**
   - Automatically configures pyqtgraph plots for responsive behavior
   - Adjusts Y-axis width to prevent label overlap
   - Updates margins dynamically on resize

### Usage in Widgets

#### Basic Widget Setup

```python
from ui.responsive_layout_manager import scaled_size, scaled_font_size, scaled_spacing

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Use scaled spacing
        layout = QVBoxLayout(self)
        layout.setSpacing(scaled_spacing(10))
        layout.setContentsMargins(
            scaled_spacing(15), scaled_spacing(15),
            scaled_spacing(15), scaled_spacing(15)
        )
        
        # Use scaled font sizes
        label = QLabel("Title")
        font_size = scaled_font_size(18)
        label.setStyleSheet(f"font-size: {font_size}px;")
        
        # Use scaled sizes
        self.setMinimumSize(scaled_size(200), scaled_size(150))
```

#### Graph Widgets

```python
from ui.responsive_layout_manager import get_responsive_manager

# Create plot widget
plot = pg.PlotWidget()
plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

# Apply responsive configuration
get_responsive_manager().configure_graph_responsive(plot)
```

#### Main Window Integration

```python
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # Initialize responsive manager
        self.responsive_manager = get_responsive_manager()
        self.responsive_manager.apply_to_window(self)
        
        # Connect to breakpoint changes
        self.responsive_manager.breakpoint_changed.connect(self._on_breakpoint_changed)
        self.responsive_manager.window_resized.connect(self._on_window_resized)
    
    def _on_breakpoint_changed(self, breakpoint):
        # Update UI based on new breakpoint
        pass
    
    def _on_window_resized(self, size):
        # Update layouts when window is resized
        pass
    
    def closeEvent(self, event):
        # Save window state
        self.responsive_manager.save_window_state(self)
        super().closeEvent(event)
```

## Configuration

The responsive system can be configured via `config/responsive_ui.json`:

```json
{
  "save_window_state": true,
  "default_width": 1280,
  "default_height": 720,
  "min_width": 800,
  "min_height": 600,
  "font_scaling": true,
  "breakpoints": {
    "xs": {"font_scale": 0.8, "spacing_scale": 0.7},
    "sm": {"font_scale": 0.9, "spacing_scale": 0.8},
    "md": {"font_scale": 1.0, "spacing_scale": 0.9},
    "lg": {"font_scale": 1.0, "spacing_scale": 1.0},
    "xl": {"font_scale": 1.1, "spacing_scale": 1.1},
    "xxl": {"font_scale": 1.2, "spacing_scale": 1.2}
  },
  "graph_config": {
    "min_height": 200,
    "aspect_ratio": null,
    "y_axis_min_width": 60,
    "y_axis_max_width": 120
  }
}
```

## Graph-Specific Rules

### Responsiveness
- All graphs use `QSizePolicy.Policy.Expanding` for flexible resizing
- Minimum heights are enforced to maintain readability
- Aspect ratios can be maintained if critical for data integrity

### Legibility
- Y-axis labels automatically adjust width to prevent overlap
- Font sizes scale with window size
- SI prefixes (k, M, etc.) are used for large numbers
- Legend positioning adapts to available space

### Data Clarity
- Primary data channels remain visible at all sizes
- Secondary channels may be simplified on smaller screens
- Interactive elements (zoom, hover) remain functional

### Interactivity
- Touch-friendly on tablets and touchscreens
- Mouse interactions work on desktop
- Zoom and pan remain functional at all sizes

## Best Practices

1. **Always Use Scaled Functions**
   - Use `scaled_size()` instead of fixed pixel values
   - Use `scaled_font_size()` for all font sizes
   - Use `scaled_spacing()` for margins and spacing

2. **Use Expanding Size Policy**
   - Set `QSizePolicy.Policy.Expanding` for flexible widgets
   - Use `stretch` parameters in layouts

3. **Test at Multiple Sizes**
   - Test at each breakpoint
   - Verify text remains legible
   - Ensure no overlapping elements

4. **Handle Breakpoint Changes**
   - Connect to `breakpoint_changed` signal
   - Update layouts when breakpoint changes
   - Show/hide elements as needed

5. **Maintain Aspect Ratios When Critical**
   - Only for graphs where aspect ratio affects data interpretation
   - Use `aspect_ratio` in graph config if needed

## Migration Guide

To migrate existing widgets to use responsive sizing:

1. **Import responsive functions**
   ```python
   from ui.responsive_layout_manager import scaled_size, scaled_font_size, scaled_spacing
   ```

2. **Replace fixed values**
   - `setSpacing(10)` → `setSpacing(scaled_spacing(10))`
   - `setContentsMargins(15, 15, 15, 15)` → `setContentsMargins(scaled_spacing(15), ...)`
   - `font-size: 14px` → `font-size: {scaled_font_size(14)}px`
   - `resize(200, 150)` → `resize(scaled_size(200), scaled_size(150, use_width=False))`

3. **Update graph widgets**
   - Add `configure_graph_responsive()` call after creating plot widgets
   - Ensure `QSizePolicy.Policy.Expanding` is set

4. **Test thoroughly**
   - Resize window to different sizes
   - Verify no overlapping elements
   - Check text legibility

## Automated Migration

Use the `scripts/apply_responsive_globally.py` script to automatically apply responsive principles to widget files:

```bash
python scripts/apply_responsive_globally.py
```

This script will:
- Add responsive imports
- Replace fixed spacing/margins with scaled functions
- Add comments for manual updates needed
- Preserve existing functionality

## Troubleshooting

### Text Overlapping
- Increase spacing between elements
- Use `scaled_spacing()` for all margins
- Check legend positioning in graphs

### Graphs Not Resizing
- Ensure `QSizePolicy.Policy.Expanding` is set
- Call `configure_graph_responsive()` on plot widgets
- Check parent layout stretch factors

### Window State Not Saving
- Verify `save_window_state: true` in config
- Check QSettings permissions
- Ensure `closeEvent` calls `save_window_state()`

### Breakpoint Not Changing
- Verify window is resizable
- Check breakpoint thresholds in config
- Ensure `apply_to_window()` was called

## Future Enhancements

- [ ] Touch gesture support for mobile devices
- [ ] High DPI display optimization
- [ ] Dark mode responsive adjustments
- [ ] Accessibility features (font size preferences)
- [ ] Multi-monitor layout management
- [ ] Custom breakpoint definitions per user

## References

- [Qt Size Policy Documentation](https://doc.qt.io/qt-6/qsizepolicy.html)
- [PyQtGraph Responsive Plotting](https://pyqtgraph.readthedocs.io/)
- [Material Design Responsive Guidelines](https://material.io/design/layout/responsive-layout-grid.html)



