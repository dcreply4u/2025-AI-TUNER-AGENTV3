"""
Racing UI Theme System
Modern racing tuner app design system with high-tech aesthetic and safety-focused design
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from ui.ui_scaling import get_scaled_size, get_scaled_font_size


class RacingColor(Enum):
    """Racing UI color palette with vibrant, high-contrast colors."""
    
    # Background colors (dark theme)
    BG_PRIMARY = "#0a0a0a"  # Deep black
    BG_SECONDARY = "#1a1a1a"  # Dark charcoal
    BG_TERTIARY = "#2a2a2a"  # Medium dark
    BG_PANEL = "#1e1e1e"  # Panel background
    
    # Vibrant accent colors
    ACCENT_NEON_BLUE = "#00e0ff"  # Electric blue
    ACCENT_NEON_ORANGE = "#ff8000"  # Vibrant orange
    ACCENT_NEON_RED = "#ff0000"  # Vivid red
    ACCENT_NEON_GREEN = "#00ff00"  # Bright green
    ACCENT_NEON_YELLOW = "#ffff00"  # Bright yellow
    
    # Status colors
    STATUS_OPTIMAL = "#00ff00"  # Green - optimal
    STATUS_ADJUSTABLE = "#00e0ff"  # Electric blue - adjustable/target
    STATUS_CRITICAL = "#ff0000"  # Vivid red - critical/active
    STATUS_WARNING = "#ff8000"  # Orange - warning
    STATUS_CAUTION = "#ffff00"  # Yellow - caution
    
    # Text colors
    TEXT_PRIMARY = "#ffffff"  # White - primary text
    TEXT_SECONDARY = "#b0b0b0"  # Light grey - secondary text
    TEXT_DISABLED = "#606060"  # Grey - disabled text
    
    # Border colors
    BORDER_DEFAULT = "#404040"  # Medium grey
    BORDER_ACCENT = "#00e0ff"  # Electric blue
    BORDER_CRITICAL = "#ff0000"  # Red
    
    # Grid/Structure colors
    GRID_LINE = "#2a2a2a"  # Subtle grid lines
    DIVIDER = "#404040"  # Section dividers


class RacingFont(Enum):
    """Racing UI typography system."""
    
    # Font families (optimized for speed reading)
    FAMILY_PRIMARY = "Segoe UI, Arial, sans-serif"  # Modern sans-serif
    FAMILY_MONO = "'Courier New', 'Consolas', monospace"  # Monospace for data
    FAMILY_DIGITAL = "'Orbitron', 'Rajdhani', sans-serif"  # Digital/racing fonts
    
    # Font sizes (scaled)
    SIZE_XXL = 32  # Large displays (RPM, Speed)
    SIZE_XL = 24  # Major data
    SIZE_LG = 18  # Section headers
    SIZE_MD = 14  # Body text
    SIZE_SM = 12  # Secondary text
    SIZE_XS = 10  # Labels/captions
    
    # Font weights
    WEIGHT_BOLD = 700
    WEIGHT_SEMIBOLD = 600
    WEIGHT_NORMAL = 400
    WEIGHT_LIGHT = 300


@dataclass
class RacingTheme:
    """Complete racing UI theme configuration."""
    
    # Colors
    colors: Dict[str, str] = None  # type: ignore
    
    # Typography
    fonts: Dict[str, str] = None  # type: ignore
    
    # Spacing
    spacing_unit: int = 8  # Base spacing unit (8px grid)
    
    # Border radius
    radius_small: int = 2
    radius_medium: int = 4
    radius_large: int = 8
    
    # Shadows (for depth)
    shadow_small: str = "0 1px 2px rgba(0, 0, 0, 0.3)"
    shadow_medium: str = "0 2px 4px rgba(0, 0, 0, 0.4)"
    shadow_large: str = "0 4px 8px rgba(0, 0, 0, 0.5)"
    
    def __post_init__(self):
        """Initialize theme with default values."""
        if self.colors is None:
            self.colors = {color.name: color.value for color in RacingColor}
        if self.fonts is None:
            self.fonts = {font.name: font.value for font in RacingFont}


class RacingUIStyles:
    """
    Centralized styling system for racing tuner UI.
    Provides consistent, high-performance styling across all components.
    """
    
    _theme: Optional[RacingTheme] = None
    
    @classmethod
    def get_theme(cls) -> RacingTheme:
        """Get current theme."""
        if cls._theme is None:
            cls._theme = RacingTheme()
        return cls._theme
    
    @classmethod
    def get_stylesheet(cls, component_type: str, **kwargs) -> str:
        """
        Get stylesheet for component type.
        
        Args:
            component_type: Type of component ("button", "gauge", "table", etc.)
            **kwargs: Additional styling parameters
        """
        theme = cls.get_theme()
        colors = theme.colors
        fonts = theme.fonts
        
        if component_type == "main_window":
            return f"""
                QWidget {{
                    background-color: {colors['BG_PRIMARY']};
                    color: {colors['TEXT_PRIMARY']};
                    font-family: {fonts['FAMILY_PRIMARY']};
                    font-size: {get_scaled_font_size(int(fonts['SIZE_MD']))}px;
                }}
            """
        
        elif component_type == "button_primary":
            return f"""
                QPushButton {{
                    background-color: {colors['ACCENT_NEON_BLUE']};
                    color: {colors['BG_PRIMARY']};
                    font-weight: {fonts['WEIGHT_BOLD']};
                    font-size: {get_scaled_font_size(int(fonts['SIZE_MD']))}px;
                    padding: {get_scaled_size(8)}px {get_scaled_size(16)}px;
                    border: {get_scaled_size(2)}px solid {colors['ACCENT_NEON_BLUE']};
                    border-radius: {get_scaled_size(theme.radius_medium)}px;
                    min-height: {get_scaled_size(40)}px;
                }}
                QPushButton:hover {{
                    background-color: {colors['ACCENT_NEON_BLUE']}dd;
                    border-color: {colors['ACCENT_NEON_BLUE']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['ACCENT_NEON_BLUE']}aa;
                }}
            """
        
        elif component_type == "button_danger":
            return f"""
                QPushButton {{
                    background-color: {colors['ACCENT_NEON_RED']};
                    color: {colors['TEXT_PRIMARY']};
                    font-weight: {fonts['WEIGHT_BOLD']};
                    font-size: {get_scaled_font_size(int(fonts['SIZE_MD']))}px;
                    padding: {get_scaled_size(8)}px {get_scaled_size(16)}px;
                    border: {get_scaled_size(2)}px solid {colors['ACCENT_NEON_RED']};
                    border-radius: {get_scaled_size(theme.radius_medium)}px;
                    min-height: {get_scaled_size(40)}px;
                }}
                QPushButton:hover {{
                    background-color: {colors['ACCENT_NEON_RED']}dd;
                }}
            """
        
        elif component_type == "button_warning":
            return f"""
                QPushButton {{
                    background-color: {colors['ACCENT_NEON_ORANGE']};
                    color: {colors['BG_PRIMARY']};
                    font-weight: {fonts['WEIGHT_BOLD']};
                    font-size: {get_scaled_font_size(int(fonts['SIZE_MD']))}px;
                    padding: {get_scaled_size(8)}px {get_scaled_size(16)}px;
                    border: {get_scaled_size(2)}px solid {colors['ACCENT_NEON_ORANGE']};
                    border-radius: {get_scaled_size(theme.radius_medium)}px;
                    min-height: {get_scaled_size(40)}px;
                }}
            """
        
        elif component_type == "gauge":
            return f"""
                QWidget {{
                    background-color: {colors['BG_SECONDARY']};
                    border: {get_scaled_size(1)}px solid {colors['BORDER_DEFAULT']};
                    border-radius: {get_scaled_size(theme.radius_medium)}px;
                }}
            """
        
        elif component_type == "data_display_large":
            return f"""
                QLabel {{
                    color: {colors['ACCENT_NEON_BLUE']};
                    font-family: {fonts['FAMILY_DIGITAL']};
                    font-size: {get_scaled_font_size(int(fonts['SIZE_XXL']))}px;
                    font-weight: {fonts['WEIGHT_BOLD']};
                    background-color: {colors['BG_SECONDARY']};
                    padding: {get_scaled_size(10)}px;
                    border: {get_scaled_size(2)}px solid {colors['ACCENT_NEON_BLUE']};
                    border-radius: {get_scaled_size(theme.radius_medium)}px;
                }}
            """
        
        elif component_type == "alert_critical":
            return f"""
                QLabel {{
                    color: {colors['ACCENT_NEON_RED']};
                    font-family: {fonts['FAMILY_PRIMARY']};
                    font-size: {get_scaled_font_size(int(fonts['SIZE_LG']))}px;
                    font-weight: {fonts['WEIGHT_BOLD']};
                    background-color: {colors['BG_SECONDARY']};
                    padding: {get_scaled_size(12)}px;
                    border: {get_scaled_size(3)}px solid {colors['ACCENT_NEON_RED']};
                    border-radius: {get_scaled_size(theme.radius_medium)}px;
                }}
            """
        
        elif component_type == "alert_warning":
            return f"""
                QLabel {{
                    color: {colors['ACCENT_NEON_ORANGE']};
                    font-family: {fonts['FAMILY_PRIMARY']};
                    font-size: {get_scaled_font_size(int(fonts['SIZE_MD']))}px;
                    font-weight: {fonts['WEIGHT_SEMIBOLD']};
                    background-color: {colors['BG_SECONDARY']};
                    padding: {get_scaled_size(10)}px;
                    border: {get_scaled_size(2)}px solid {colors['ACCENT_NEON_ORANGE']};
                    border-radius: {get_scaled_size(theme.radius_medium)}px;
                }}
            """
        
        elif component_type == "table":
            return f"""
                QTableWidget {{
                    background-color: {colors['BG_PRIMARY']};
                    color: {colors['TEXT_PRIMARY']};
                    gridline-color: {colors['GRID_LINE']};
                    border: {get_scaled_size(1)}px solid {colors['BORDER_DEFAULT']};
                    border-radius: {get_scaled_size(theme.radius_small)}px;
                    font-size: {get_scaled_font_size(int(fonts['SIZE_SM']))}px;
                }}
                QHeaderView::section {{
                    background-color: {colors['BG_SECONDARY']};
                    color: {colors['TEXT_PRIMARY']};
                    font-weight: {fonts['WEIGHT_SEMIBOLD']};
                    padding: {get_scaled_size(8)}px;
                    border: {get_scaled_size(1)}px solid {colors['BORDER_DEFAULT']};
                }}
                QTableWidget::item {{
                    padding: {get_scaled_size(4)}px;
                }}
                QTableWidget::item:selected {{
                    background-color: {colors['ACCENT_NEON_BLUE']}33;
                    color: {colors['ACCENT_NEON_BLUE']};
                }}
            """
        
        elif component_type == "panel":
            return f"""
                QWidget {{
                    background-color: {colors['BG_SECONDARY']};
                    border: {get_scaled_size(1)}px solid {colors['BORDER_DEFAULT']};
                    border-radius: {get_scaled_size(theme.radius_medium)}px;
                    padding: {get_scaled_size(theme.spacing_unit)}px;
                }}
            """
        
        elif component_type == "group_box":
            return f"""
                QGroupBox {{
                    font-family: {fonts['FAMILY_PRIMARY']};
                    font-size: {get_scaled_font_size(int(fonts['SIZE_MD']))}px;
                    font-weight: {fonts['WEIGHT_BOLD']};
                    color: {colors['TEXT_PRIMARY']};
                    border: {get_scaled_size(1)}px solid {colors['BORDER_DEFAULT']};
                    border-radius: {get_scaled_size(theme.radius_medium)}px;
                    margin-top: {get_scaled_size(theme.spacing_unit * 2)}px;
                    padding-top: {get_scaled_size(theme.spacing_unit * 2)}px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: {get_scaled_size(4)}px {get_scaled_size(8)}px;
                    color: {colors['ACCENT_NEON_BLUE']};
                }}
            """
        
        elif component_type == "tab_widget":
            return f"""
                QTabWidget::pane {{
                    border: {get_scaled_size(1)}px solid {colors['BORDER_DEFAULT']};
                    background-color: {colors['BG_SECONDARY']};
                    border-radius: {get_scaled_size(theme.radius_medium)}px;
                }}
                QTabBar::tab {{
                    background-color: {colors['BG_TERTIARY']};
                    color: {colors['TEXT_SECONDARY']};
                    padding: {get_scaled_size(8)}px {get_scaled_size(16)}px;
                    margin-right: {get_scaled_size(2)}px;
                    border: {get_scaled_size(1)}px solid {colors['BORDER_DEFAULT']};
                    border-top-left-radius: {get_scaled_size(theme.radius_medium)}px;
                    border-top-right-radius: {get_scaled_size(theme.radius_medium)}px;
                    font-size: {get_scaled_font_size(int(fonts['SIZE_SM']))}px;
                    font-weight: {fonts['WEIGHT_SEMIBOLD']};
                    min-height: {get_scaled_size(32)}px;
                }}
                QTabBar::tab:selected {{
                    background-color: {colors['BG_SECONDARY']};
                    color: {colors['ACCENT_NEON_BLUE']};
                    border-bottom: {get_scaled_size(3)}px solid {colors['ACCENT_NEON_BLUE']};
                    font-weight: {fonts['WEIGHT_BOLD']};
                }}
                QTabBar::tab:hover {{
                    background-color: {colors['BG_SECONDARY']};
                    color: {colors['TEXT_PRIMARY']};
                }}
            """
        
        elif component_type == "input_field":
            return f"""
                QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                    background-color: {colors['BG_TERTIARY']};
                    color: {colors['TEXT_PRIMARY']};
                    border: {get_scaled_size(1)}px solid {colors['BORDER_DEFAULT']};
                    border-radius: {get_scaled_size(theme.radius_small)}px;
                    padding: {get_scaled_size(6)}px {get_scaled_size(10)}px;
                    font-size: {get_scaled_font_size(int(fonts['SIZE_MD']))}px;
                    min-height: {get_scaled_size(32)}px;
                }}
                QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                    border: {get_scaled_size(2)}px solid {colors['ACCENT_NEON_BLUE']};
                    background-color: {colors['BG_SECONDARY']};
                }}
            """
        
        elif component_type == "slider":
            return f"""
                QSlider::groove:horizontal {{
                    border: {get_scaled_size(1)}px solid {colors['BORDER_DEFAULT']};
                    height: {get_scaled_size(8)}px;
                    background-color: {colors['BG_TERTIARY']};
                    border-radius: {get_scaled_size(4)}px;
                }}
                QSlider::handle:horizontal {{
                    background-color: {colors['ACCENT_NEON_BLUE']};
                    border: {get_scaled_size(2)}px solid {colors['ACCENT_NEON_BLUE']};
                    width: {get_scaled_size(20)}px;
                    height: {get_scaled_size(20)}px;
                    margin: {get_scaled_size(-6)}px 0;
                    border-radius: {get_scaled_size(10)}px;
                }}
                QSlider::handle:horizontal:hover {{
                    background-color: {colors['ACCENT_NEON_BLUE']}dd;
                    width: {get_scaled_size(24)}px;
                    height: {get_scaled_size(24)}px;
                }}
                QSlider::sub-page:horizontal {{
                    background-color: {colors['ACCENT_NEON_BLUE']};
                    border-radius: {get_scaled_size(4)}px;
                }}
            """
        
        # Default fallback
        return ""


# Global theme instance
_global_theme: Optional[RacingTheme] = None


def get_racing_theme() -> RacingTheme:
    """Get global racing theme instance."""
    global _global_theme
    if _global_theme is None:
        _global_theme = RacingTheme()
    return _global_theme


def get_racing_stylesheet(component_type: str, **kwargs) -> str:
    """Get racing stylesheet for component type."""
    return RacingUIStyles.get_stylesheet(component_type, **kwargs)
















