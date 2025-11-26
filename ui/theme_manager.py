"""
Theme Manager

Manages UI themes, colors, and styling with support for custom backgrounds.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

LOGGER = logging.getLogger(__name__)


class ThemeStyle(Enum):
    """Predefined theme styles."""

    DARK = "dark"
    LIGHT = "light"
    RACING = "racing"
    MODERN = "modern"
    CLASSIC = "classic"
    NEON = "neon"
    MINIMAL = "minimal"


@dataclass
class ThemeColors:
    """Color palette for a theme - CSS-like semantic color system.
    
    Change colors here to update globally across all widgets.
    """

    # Primary colors
    primary: str = "#00e0ff"
    primary_dark: str = "#00a8c5"
    primary_light: str = "#33e8ff"

    # Background colors
    background: str = "#0a0e27"
    background_secondary: str = "#141b2d"
    background_tertiary: str = "#1e2839"

    # Text colors
    text_primary: str = "#ffffff"
    text_secondary: str = "#b0b8c4"
    text_disabled: str = "#6b7280"

    # Accent colors
    accent: str = "#00ff88"
    accent_dark: str = "#00cc6a"
    warning: str = "#ffaa00"
    error: str = "#ff4444"
    success: str = "#00ff88"
    info: str = "#00a8ff"

    # Border colors
    border: str = "#2d3748"
    border_light: str = "#4a5568"

    # Widget colors
    widget_background: str = "#1a1f35"
    widget_border: str = "#2d3748"
    widget_hover: str = "#252b42"

    # Chart/Graph colors
    chart_line: str = "#00e0ff"
    chart_grid: str = "#1e2839"
    chart_background: str = "#0a0e27"
    
    # ============================================================
    # SEMANTIC COLOR NAMES - Change these to update globally
    # ============================================================
    
    # Title colors (for panel titles, section headers)
    title: str = "#ff2a2a"  # Red - main panel titles like "LIVE GAUGES"
    title_secondary: str = "#ff6b00"  # Orange - gauge titles, metric labels
    title_tertiary: str = "#3498db"  # Blue - secondary headers
    
    # Scrollbar colors
    scrollbar: str = "#3498db"  # Blue - scrollbar handle color
    scrollbar_background: str = "#e0e0e0"  # Light gray - scrollbar track
    
    # Gauge-specific colors
    gauge_title: str = "#ff6b00"  # Orange - individual gauge titles (e.g., "BOOST PSI")
    gauge_value: str = "#ffffff"  # White - digital gauge values
    gauge_border: str = "#ff2a2a"  # Red - gauge value box border
    gauge_needle: str = "#ff4444"  # Red - gauge needle color
    
    # Drag Mode colors (for consistency)
    drag_mode_title: str = "#ff2a2a"  # Red - Drag Mode panel title
    drag_mode_metric: str = "#ff6b00"  # Orange - Drag Mode metric titles
    drag_mode_value: str = "#ffffff"  # White - Drag Mode values
    
    # Button/Interactive colors
    button_primary: str = "#3498db"  # Blue - primary buttons
    button_hover: str = "#2980b9"  # Darker blue - button hover state
    
    # Status colors
    status_optimal: str = "#27ae60"  # Green
    status_warning: str = "#f39c12"  # Orange
    status_danger: str = "#e74c3c"  # Red


@dataclass
class Theme:
    """Complete theme definition."""

    name: str
    style: ThemeStyle
    colors: ThemeColors
    background_image: Optional[str] = None  # Path to background image
    background_opacity: float = 0.3  # 0.0 to 1.0
    font_family: str = "Segoe UI, Arial, sans-serif"
    font_size_base: int = 14
    border_radius: int = 8
    shadow_enabled: bool = True


class ThemeManager:
    """Manages UI themes and styling."""

    # Predefined themes
    THEMES: Dict[ThemeStyle, Theme] = {
        ThemeStyle.DARK: Theme(
            name="Dark",
            style=ThemeStyle.DARK,
            colors=ThemeColors(
                primary="#00e0ff",
                background="#0a0e27",
                background_secondary="#141b2d",
                text_primary="#ffffff",
            ),
        ),
        ThemeStyle.LIGHT: Theme(
            name="Light",
            style=ThemeStyle.LIGHT,
            colors=ThemeColors(
                primary="#0066cc",
                background="#f5f7fa",
                background_secondary="#ffffff",
                background_tertiary="#e8ecf1",
                text_primary="#1a202c",
                text_secondary="#4a5568",
                widget_background="#ffffff",
                widget_border="#e2e8f0",
            ),
        ),
        ThemeStyle.RACING: Theme(
            name="Racing",
            style=ThemeStyle.RACING,
            colors=ThemeColors(
                primary="#ff0000",
                primary_dark="#cc0000",
                accent="#ffff00",
                background="#000000",
                background_secondary="#1a0000",
                background_tertiary="#330000",
                text_primary="#ffffff",
                warning="#ffaa00",
                success="#00ff00",
            ),
            background_opacity=0.2,
        ),
        ThemeStyle.MODERN: Theme(
            name="Modern",
            style=ThemeStyle.MODERN,
            colors=ThemeColors(
                primary="#6366f1",
                primary_dark="#4f46e5",
                primary_light="#818cf8",
                background="#0f172a",
                background_secondary="#1e293b",
                background_tertiary="#334155",
                text_primary="#f1f5f9",
                accent="#10b981",
            ),
            border_radius=12,
        ),
        ThemeStyle.CLASSIC: Theme(
            name="Classic",
            style=ThemeStyle.CLASSIC,
            colors=ThemeColors(
                primary="#00ff00",
                background="#000000",
                background_secondary="#1a1a1a",
                text_primary="#00ff00",
                widget_background="#0a0a0a",
                border="#00ff00",
            ),
            font_family="Courier New, monospace",
        ),
        ThemeStyle.NEON: Theme(
            name="Neon",
            style=ThemeStyle.NEON,
            colors=ThemeColors(
                primary="#ff00ff",
                primary_dark="#cc00cc",
                accent="#00ffff",
                background="#0a0a1a",
                background_secondary="#1a0a2a",
                text_primary="#ffffff",
                warning="#ffff00",
                success="#00ff00",
            ),
            shadow_enabled=True,
        ),
        ThemeStyle.MINIMAL: Theme(
            name="Minimal",
            style=ThemeStyle.MINIMAL,
            colors=ThemeColors(
                primary="#2563eb",
                background="#ffffff",
                background_secondary="#f9fafb",
                text_primary="#111827",
                text_secondary="#6b7280",
                widget_background="#ffffff",
                widget_border="#e5e7eb",
            ),
            border_radius=4,
            shadow_enabled=False,
        ),
    }

    def __init__(self, config_file: str | Path = "config/theme.json") -> None:
        """
        Initialize theme manager.

        Args:
            config_file: Path to theme configuration file
        """
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.current_theme: Theme = self.THEMES[ThemeStyle.DARK]
        self.custom_themes: Dict[str, Theme] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load theme configuration from file."""
        if not self.config_file.exists():
            self._save_config()
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            theme_name = data.get("current_theme", "Dark")
            style_value = data.get("style", "dark")

            try:
                style = ThemeStyle(style_value)
            except ValueError:
                style = ThemeStyle.DARK

            if style in self.THEMES:
                self.current_theme = self.THEMES[style]
            elif theme_name in self.custom_themes:
                self.current_theme = self.custom_themes[theme_name]

            # Load custom background if specified
            if "background_image" in data:
                self.current_theme.background_image = data["background_image"]
            if "background_opacity" in data:
                self.current_theme.background_opacity = data["background_opacity"]

            LOGGER.info("Theme configuration loaded: %s", theme_name)
        except Exception as exc:  # pragma: no cover - config errors non-fatal
            LOGGER.error("Failed to load theme config: %s", exc)

    def _save_config(self) -> None:
        """Save theme configuration to file."""
        try:
            data = {
                "current_theme": self.current_theme.name,
                "style": self.current_theme.style.value,
                "background_image": self.current_theme.background_image,
                "background_opacity": self.current_theme.background_opacity,
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:  # pragma: no cover - config errors non-fatal
            LOGGER.error("Failed to save theme config: %s", exc)

    def set_theme(self, theme_style: ThemeStyle | str) -> None:
        """
        Set current theme.

        Args:
            theme_style: Theme style enum or name
        """
        if isinstance(theme_style, str):
            # Try to find by name
            for style, theme in self.THEMES.items():
                if theme.name.lower() == theme_style.lower():
                    self.current_theme = theme
                    self._save_config()
                    return
            # Try custom themes
            if theme_style in self.custom_themes:
                self.current_theme = self.custom_themes[theme_style]
                self._save_config()
                return
        else:
            if theme_style in self.THEMES:
                self.current_theme = self.THEMES[theme_style]
                self._save_config()

    def set_background_image(self, image_path: str | Path, opacity: float = 0.3) -> None:
        """
        Set custom background image.

        Args:
            image_path: Path to background image
            opacity: Background opacity (0.0 to 1.0)
        """
        self.current_theme.background_image = str(image_path)
        self.current_theme.background_opacity = max(0.0, min(1.0, opacity))
        self._save_config()

    def clear_background_image(self) -> None:
        """Clear custom background image."""
        self.current_theme.background_image = None
        self._save_config()

    def get_stylesheet(self) -> str:
        """
        Get QSS stylesheet for current theme.

        Returns:
            QSS stylesheet string
        """
        c = self.current_theme.colors
        theme = self.current_theme

        stylesheet = f"""
        /* Main Window */
        QWidget {{
            font-family: '{theme.font_family}';
            font-size: {theme.font_size_base}px;
            color: {c.text_primary};
        }}

        QMainWindow {{
            background-color: {c.background};
        }}

        /* Buttons */
        QPushButton {{
            background-color: {c.primary};
            color: {c.background};
            border: none;
            border-radius: {theme.border_radius}px;
            padding: 8px 16px;
            font-weight: 600;
            min-height: 32px;
        }}

        QPushButton:hover {{
            background-color: {c.primary_light};
        }}

        QPushButton:pressed {{
            background-color: {c.primary_dark};
        }}

        QPushButton:disabled {{
            background-color: {c.background_tertiary};
            color: {c.text_disabled};
        }}

        /* Secondary Button */
        QPushButton[class="secondary"] {{
            background-color: {c.widget_background};
            color: {c.text_primary};
            border: 2px solid {c.border};
        }}

        QPushButton[class="secondary"]:hover {{
            background-color: {c.widget_hover};
            border-color: {c.primary};
        }}

        /* Labels */
        QLabel {{
            color: {c.text_primary};
        }}

        QLabel[class="heading"] {{
            font-size: {theme.font_size_base + 4}px;
            font-weight: 700;
            color: {c.primary};
        }}

        QLabel[class="subheading"] {{
            font-size: {theme.font_size_base + 2}px;
            font-weight: 600;
            color: {c.text_secondary};
        }}

        /* Line Edits */
        QLineEdit {{
            background-color: {c.widget_background};
            border: 2px solid {c.border};
            border-radius: {theme.border_radius}px;
            padding: 6px 12px;
            color: {c.text_primary};
        }}

        QLineEdit:focus {{
            border-color: {c.primary};
        }}

        /* Combo Boxes */
        QComboBox {{
            background-color: {c.widget_background};
            border: 2px solid {c.border};
            border-radius: {theme.border_radius}px;
            padding: 6px 12px;
            color: {c.text_primary};
            min-height: 32px;
        }}

        QComboBox:hover {{
            border-color: {c.primary};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {c.widget_background};
            border: 2px solid {c.border};
            selection-background-color: {c.primary};
            selection-color: {c.background};
        }}

        /* Checkboxes */
        QCheckBox {{
            color: {c.text_primary};
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {c.border};
            border-radius: 4px;
            background-color: {c.widget_background};
        }}

        QCheckBox::indicator:checked {{
            background-color: {c.primary};
            border-color: {c.primary};
        }}

        /* Spin Boxes */
        QSpinBox, QDoubleSpinBox {{
            background-color: {c.widget_background};
            border: 2px solid {c.border};
            border-radius: {theme.border_radius}px;
            padding: 6px 12px;
            color: {c.text_primary};
        }}

        /* Scroll Bars */
        QScrollBar:vertical {{
            background: {c.background_secondary};
            width: 12px;
            border: none;
        }}

        QScrollBar::handle:vertical {{
            background: {c.border};
            border-radius: 6px;
            min-height: 30px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {c.primary};
        }}

        /* Group Boxes */
        QGroupBox {{
            border: 2px solid {c.border};
            border-radius: {theme.border_radius}px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: 600;
            color: {c.primary};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
        }}

        /* Tab Widget */
        QTabWidget::pane {{
            border: 2px solid {c.border};
            border-radius: {theme.border_radius}px;
            background-color: {c.background_secondary};
        }}

        QTabBar::tab {{
            background-color: {c.widget_background};
            color: {c.text_secondary};
            border: 2px solid {c.border};
            border-bottom: none;
            padding: 8px 16px;
            border-top-left-radius: {theme.border_radius}px;
            border-top-right-radius: {theme.border_radius}px;
        }}

        QTabBar::tab:selected {{
            background-color: {c.primary};
            color: {c.background};
        }}

        /* Status Indicators */
        QLabel[class="status-ok"] {{
            color: {c.success};
        }}

        QLabel[class="status-warning"] {{
            color: {c.warning};
        }}

        QLabel[class="status-error"] {{
            color: {c.error};
        }}

        /* Custom Widgets */
        QFrame[class="metric-tile"] {{
            background-color: {c.widget_background};
            border: 2px solid {c.border};
            border-radius: {theme.border_radius}px;
            padding: 12px;
        }}

        QFrame[class="metric-tile"]:hover {{
            border-color: {c.primary};
        }}

        /* Progress Bars */
        QProgressBar {{
            background-color: {c.widget_background};
            border: 2px solid {c.border};
            border-radius: {theme.border_radius}px;
            text-align: center;
            color: {c.text_primary};
            height: 24px;
        }}

        QProgressBar::chunk {{
            background-color: {c.primary};
            border-radius: {theme.border_radius - 2}px;
        }}
        """

        return stylesheet

    def get_background_stylesheet(self) -> Optional[str]:
        """
        Get background image stylesheet if configured.

        Returns:
            QSS stylesheet for background or None
        """
        if not self.current_theme.background_image:
            return None

        image_path = Path(self.current_theme.background_image)
        if not image_path.exists():
            return None

        opacity = self.current_theme.background_opacity
        return f"""
        QMainWindow {{
            background-image: url({image_path.absolute()});
            background-repeat: no-repeat;
            background-position: center;
            background-attachment: fixed;
        }}

        QMainWindow::before {{
            background-color: rgba(10, 14, 39, {1.0 - opacity});
        }}
        """

    def list_themes(self) -> list[str]:
        """List all available theme names."""
        themes = [theme.name for theme in self.THEMES.values()]
        themes.extend(self.custom_themes.keys())
        return themes

    def create_custom_theme(
        self,
        name: str,
        base_style: ThemeStyle,
        **overrides,
    ) -> Theme:
        """
        Create a custom theme based on an existing one.

        Args:
            name: Theme name
            base_style: Base theme style
            **overrides: Theme property overrides

        Returns:
            Created theme
        """
        base_theme = self.THEMES[base_style]
        custom_theme = Theme(
            name=name,
            style=base_style,
            colors=ThemeColors(
                **{**asdict(base_theme.colors), **overrides.get("colors", {})}
            ),
            **{k: v for k, v in overrides.items() if k != "colors"},
        )

        self.custom_themes[name] = custom_theme
        return custom_theme


# ============================================================
# Global Style Accessor - CSS-like semantic color system
# ============================================================
# Usage: from ui.theme_manager import Style
#        color = Style.title  # Gets current theme's title color
#        Change colors in ThemeColors above to update globally
# ============================================================

class Style:
    """
    Global style accessor - provides CSS-like semantic color access.
    
    Change colors in ThemeColors class above to update globally.
    All widgets should use this instead of hardcoded colors.
    
    Example:
        from ui.theme_manager import Style
        painter.setPen(QColor(Style.title))  # Uses current theme's title color
    """
    
    _theme_manager: Optional[ThemeManager] = None
    
    @classmethod
    def _get_colors(cls) -> ThemeColors:
        """Get current theme colors."""
        if cls._theme_manager is None:
            # Initialize default theme manager if not set
            cls._theme_manager = ThemeManager()
        return cls._theme_manager.current_theme.colors
    
    @classmethod
    def set_theme_manager(cls, manager: ThemeManager) -> None:
        """Set the theme manager instance (called by main app)."""
        cls._theme_manager = manager
    
    # Primary colors
    @classmethod
    def primary(cls) -> str:
        return cls._get_colors().primary
    
    @classmethod
    def primary_dark(cls) -> str:
        return cls._get_colors().primary_dark
    
    @classmethod
    def primary_light(cls) -> str:
        return cls._get_colors().primary_light
    
    # Text colors
    @classmethod
    def text_primary(cls) -> str:
        return cls._get_colors().text_primary
    
    @classmethod
    def text_secondary(cls) -> str:
        return cls._get_colors().text_secondary
    
    # Semantic color names - change in ThemeColors to update globally
    @classmethod
    def title(cls) -> str:
        """Main panel titles (e.g., 'LIVE GAUGES') - Red by default."""
        return cls._get_colors().title
    
    @classmethod
    def title_secondary(cls) -> str:
        """Secondary titles (e.g., gauge titles, metric labels) - Orange by default."""
        return cls._get_colors().title_secondary
    
    @classmethod
    def title_tertiary(cls) -> str:
        """Tertiary titles - Blue by default."""
        return cls._get_colors().title_tertiary
    
    @classmethod
    def scrollbar(cls) -> str:
        """Scrollbar handle color - Blue by default."""
        return cls._get_colors().scrollbar
    
    @classmethod
    def scrollbar_background(cls) -> str:
        """Scrollbar track color."""
        return cls._get_colors().scrollbar_background
    
    @classmethod
    def gauge_title(cls) -> str:
        """Individual gauge titles (e.g., 'BOOST PSI') - Orange by default."""
        return cls._get_colors().gauge_title
    
    @classmethod
    def gauge_value(cls) -> str:
        """Digital gauge values - White by default."""
        return cls._get_colors().gauge_value
    
    @classmethod
    def gauge_border(cls) -> str:
        """Gauge value box border - Red by default."""
        return cls._get_colors().gauge_border
    
    @classmethod
    def gauge_needle(cls) -> str:
        """Gauge needle color - Red by default."""
        return cls._get_colors().gauge_needle
    
    @classmethod
    def drag_mode_title(cls) -> str:
        """Drag Mode panel title - Red by default."""
        return cls._get_colors().drag_mode_title
    
    @classmethod
    def drag_mode_metric(cls) -> str:
        """Drag Mode metric titles - Orange by default."""
        return cls._get_colors().drag_mode_metric
    
    @classmethod
    def drag_mode_value(cls) -> str:
        """Drag Mode values - White by default."""
        return cls._get_colors().drag_mode_value
    
    @classmethod
    def button_primary(cls) -> str:
        """Primary button color - Blue by default."""
        return cls._get_colors().button_primary
    
    @classmethod
    def button_hover(cls) -> str:
        """Button hover color - Darker blue by default."""
        return cls._get_colors().button_hover
    
    @classmethod
    def status_optimal(cls) -> str:
        """Optimal status color - Green by default."""
        return cls._get_colors().status_optimal
    
    @classmethod
    def status_warning(cls) -> str:
        """Warning status color - Orange by default."""
        return cls._get_colors().status_warning
    
    @classmethod
    def status_danger(cls) -> str:
        """Danger status color - Red by default."""
        return cls._get_colors().status_danger


__all__ = ["ThemeManager", "Theme", "ThemeColors", "ThemeStyle", "Style"]
