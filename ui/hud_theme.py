"""
Futuristic HUD Theme
High-tech, holographic interface with electric blue grid pattern
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HUDColors:
    """Color palette for HUD theme - Minimalist Neo-Cyberpunk."""
    
    # Background
    background_dark: str = "#000000"  # Deep near-pure black
    background_charcoal: str = "#0a0a0a"  # Dark charcoal
    grid_blue: str = "#00ffff"  # Electric cyan for grid
    grid_blue_dim: str = "#001a1a"  # Very subtle dark-blue grid
    
    # Primary accents (high-contrast neon)
    electric_cyan: str = "#00ffff"  # Electric Cyan (active/primary data)
    vibrant_traffic_orange: str = "#ff6600"  # Vibrant Traffic Orange (alerts/secondary)
    
    # Secondary colors
    lime_green: str = "#00ff00"  # Lime green (battery/power)
    red_alert: str = "#ff4444"  # Red for warnings
    
    # Text
    text_primary: str = "#ffffff"  # White (sharp, thin)
    text_cyan: str = "#00ffff"  # Cyan text
    text_dim: str = "#666666"  # Dimmed text
    
    # Panel backgrounds (semi-transparent)
    panel_bg: str = "rgba(10, 10, 10, 200)"  # Semi-transparent dark
    panel_border: str = "#00ffff"  # Cyan border
    
    # Status colors
    status_good: str = "#00ff00"  # Green
    status_warning: str = "#ff6600"  # Traffic Orange
    status_error: str = "#ff4444"  # Red


@dataclass
class HUDTheme:
    """HUD theme configuration."""
    
    name: str = "Futuristic HUD"
    colors: HUDColors = HUDColors()
    font_family: str = "Consolas, 'Courier New', monospace"
    font_size_title: int = 16
    font_size_normal: int = 12
    font_size_small: int = 10
    grid_spacing: int = 20  # Grid pattern spacing
    glow_intensity: float = 0.8  # Glow effect intensity


