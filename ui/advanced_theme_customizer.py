"""
Advanced Theme Customization System

Features:
- System-wide dark mode detection
- Manual dark/light toggle
- Accent color chooser with accessibility validation
- Customizable gauges (needle, background, scale colors)
- True black OLED optimization
- Instant preview
- Readability/contrast validation
"""

from __future__ import annotations

import json
import logging
import platform
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QMessageBox,
)

from ui.theme_manager import ThemeManager, ThemeStyle, ThemeColors, Theme

LOGGER = logging.getLogger(__name__)


class SystemThemeMode(Enum):
    """System theme detection mode."""

    AUTO = "auto"  # Follow system setting
    DARK = "dark"  # Force dark
    LIGHT = "light"  # Force light


@dataclass
class GaugeCustomization:
    """Gauge customization settings."""

    needle_color: str = "#00e0ff"
    background_color: str = "#1a1f35"
    scale_color: str = "#ffffff"
    text_color: str = "#ffffff"
    warning_zone_color: str = "#ffaa00"
    critical_zone_color: str = "#ff4444"


@dataclass
class ThemeCustomization:
    """Complete theme customization settings."""

    system_theme_mode: SystemThemeMode = SystemThemeMode.AUTO
    accent_color: str = "#00e0ff"
    gauge_customization: GaugeCustomization = field(default_factory=GaugeCustomization)
    oled_optimized: bool = False
    true_black_background: bool = False
    high_contrast: bool = True
    font_size_scale: float = 1.0


class ContrastValidator:
    """Validates color contrast for accessibility."""

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def get_luminance(r: int, g: int, b: int) -> float:
        """Calculate relative luminance (WCAG)."""
        rs = r / 255.0
        gs = g / 255.0
        bs = b / 255.0

        def adjust(c: float) -> float:
            return ((c + 0.055) / 1.055) ** 2.4 if c > 0.03928 else c / 12.92

        rs = adjust(rs)
        gs = adjust(gs)
        bs = adjust(bs)

        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs

    @staticmethod
    def get_contrast_ratio(color1: str, color2: str) -> float:
        """
        Calculate contrast ratio between two colors.

        Args:
            color1: First color (hex)
            color2: Second color (hex)

        Returns:
            Contrast ratio (1.0-21.0)
        """
        rgb1 = ContrastValidator.hex_to_rgb(color1)
        rgb2 = ContrastValidator.hex_to_rgb(color2)

        lum1 = ContrastValidator.get_luminance(*rgb1)
        lum2 = ContrastValidator.get_luminance(*rgb2)

        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)

        return (lighter + 0.05) / (darker + 0.05)

    @staticmethod
    def is_accessible(text_color: str, background_color: str, level: str = "AA") -> Tuple[bool, float]:
        """
        Check if color combination meets accessibility standards.

        Args:
            text_color: Text color (hex)
            background_color: Background color (hex)
            level: "AA" or "AAA"

        Returns:
            (is_accessible, contrast_ratio)
        """
        ratio = ContrastValidator.get_contrast_ratio(text_color, background_color)

        if level == "AAA":
            required = 7.0  # AAA requires 7:1 for normal text
        else:  # AA
            required = 4.5  # AA requires 4.5:1 for normal text

        return (ratio >= required, ratio)

    @staticmethod
    def suggest_accessible_color(text_color: str, background_color: str) -> str:
        """
        Suggest an accessible text color for given background.

        Args:
            text_color: Current text color
            background_color: Background color

        Returns:
            Suggested accessible color (hex)
        """
        rgb_bg = ContrastValidator.hex_to_rgb(background_color)
        bg_lum = ContrastValidator.get_luminance(*rgb_bg)

        # If background is dark, use light text; if light, use dark text
        if bg_lum < 0.5:
            # Dark background - use light text
            return "#ffffff"
        else:
            # Light background - use dark text
            return "#000000"


class SystemThemeDetector:
    """Detects system theme preference."""

    @staticmethod
    def detect_system_theme() -> SystemThemeMode:
        """
        Detect system theme preference.

        Returns:
            System theme mode
        """
        system = platform.system()

        if system == "Windows":
            try:
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                )
                apps_use_light_theme = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                winreg.CloseKey(key)
                return SystemThemeMode.LIGHT if apps_use_light_theme else SystemThemeMode.DARK
            except Exception:
                return SystemThemeMode.DARK  # Default to dark

        elif system == "Darwin":  # macOS
            try:
                import subprocess

                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True,
                    text=True,
                )
                if "Dark" in result.stdout:
                    return SystemThemeMode.DARK
                return SystemThemeMode.LIGHT
            except Exception:
                return SystemThemeMode.DARK

        elif system == "Linux":
            # Try to detect via gsettings (GNOME)
            try:
                import subprocess

                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                    capture_output=True,
                    text=True,
                )
                if "dark" in result.stdout.lower():
                    return SystemThemeMode.DARK
                return SystemThemeMode.LIGHT
            except Exception:
                return SystemThemeMode.DARK

        return SystemThemeMode.DARK  # Default


class AdvancedThemeCustomizer(QDialog):
    """Advanced theme customization dialog."""

    theme_changed = Signal(Theme)  # Emitted when theme changes

    def __init__(self, theme_manager: ThemeManager, parent: Optional[QWidget] = None) -> None:
        """
        Initialize advanced theme customizer.

        Args:
            theme_manager: Theme manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Advanced Theme Customization")
        self.resize(900, 700)

        self.theme_manager = theme_manager
        self.customization = ThemeCustomization()
        self.config_file = Path("config/theme_customization.json")
        self._load_customization()

        # Create UI
        self._create_ui()

        # Apply initial theme
        self._apply_theme()

        # Setup preview timer for instant updates
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._apply_theme)

    def _create_ui(self) -> None:
        """Create UI components."""
        layout = QVBoxLayout(self)

        # Create tab widget
        tabs = QTabWidget(self)
        tabs.addTab(self._create_general_tab(), "General")
        tabs.addTab(self._create_colors_tab(), "Colors")
        tabs.addTab(self._create_gauges_tab(), "Gauges")
        tabs.addTab(self._create_accessibility_tab(), "Accessibility")
        tabs.addTab(self._create_preview_tab(), "Preview")

        layout.addWidget(tabs)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).setText("Reset to Defaults")
        buttons.accepted.connect(self._apply_and_close)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._reset_to_defaults)
        layout.addWidget(buttons)

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # System theme detection
        system_group = QGroupBox("System Theme Detection")
        system_layout = QVBoxLayout(system_group)

        self.system_theme_auto = QRadioButton("Follow System (Auto)")
        self.system_theme_dark = QRadioButton("Force Dark Mode")
        self.system_theme_light = QRadioButton("Force Light Mode")

        if self.customization.system_theme_mode == SystemThemeMode.AUTO:
            self.system_theme_auto.setChecked(True)
        elif self.customization.system_theme_mode == SystemThemeMode.DARK:
            self.system_theme_dark.setChecked(True)
        else:
            self.system_theme_light.setChecked(True)

        self.system_theme_auto.toggled.connect(lambda: self._on_system_theme_changed(SystemThemeMode.AUTO))
        self.system_theme_dark.toggled.connect(lambda: self._on_system_theme_changed(SystemThemeMode.DARK))
        self.system_theme_light.toggled.connect(lambda: self._on_system_theme_changed(SystemThemeMode.LIGHT))

        system_layout.addWidget(self.system_theme_auto)
        system_layout.addWidget(self.system_theme_dark)
        system_layout.addWidget(self.system_theme_light)

        # Show detected system theme
        detected = SystemThemeDetector.detect_system_theme()
        detected_label = QLabel(f"Detected System Theme: {detected.value.title()}")
        detected_label.setStyleSheet("color: #888888; font-style: italic;")
        system_layout.addWidget(detected_label)

        layout.addWidget(system_group)

        # OLED optimization
        oled_group = QGroupBox("OLED/AMOLED Optimization")
        oled_layout = QVBoxLayout(oled_group)

        self.oled_checkbox = QCheckBox("Enable OLED Optimization (True Black)")
        self.oled_checkbox.setChecked(self.customization.oled_optimized)
        self.oled_checkbox.toggled.connect(self._on_oled_changed)
        oled_layout.addWidget(self.oled_checkbox)

        self.true_black_checkbox = QCheckBox("Use True Black Background (#000000)")
        self.true_black_checkbox.setChecked(self.customization.true_black_background)
        self.true_black_checkbox.toggled.connect(self._on_true_black_changed)
        oled_layout.addWidget(self.true_black_checkbox)

        info_label = QLabel("True black saves battery on OLED displays and provides maximum contrast.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888888; font-size: 11px;")
        oled_layout.addWidget(info_label)

        layout.addWidget(oled_group)

        # High contrast
        contrast_group = QGroupBox("Display Options")
        contrast_layout = QVBoxLayout(contrast_group)

        self.high_contrast_checkbox = QCheckBox("High Contrast Mode")
        self.high_contrast_checkbox.setChecked(self.customization.high_contrast)
        self.high_contrast_checkbox.toggled.connect(self._on_high_contrast_changed)
        contrast_layout.addWidget(self.high_contrast_checkbox)

        # Font size scale
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font Size Scale:"))
        self.font_scale_spin = QSpinBox()
        self.font_scale_spin.setRange(50, 200)
        self.font_scale_spin.setValue(int(self.customization.font_size_scale * 100))
        self.font_scale_spin.setSuffix("%")
        self.font_scale_spin.valueChanged.connect(self._on_font_scale_changed)
        font_layout.addWidget(self.font_scale_spin)
        font_layout.addStretch()
        contrast_layout.addLayout(font_layout)

        layout.addWidget(contrast_group)

        layout.addStretch()
        return widget

    def _create_colors_tab(self) -> QWidget:
        """Create colors customization tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Accent color
        accent_group = QGroupBox("Accent Color")
        accent_layout = QFormLayout(accent_group)

        accent_color_layout = QHBoxLayout()
        self.accent_color_label = QLabel()
        self.accent_color_label.setFixedSize(50, 30)
        self.accent_color_label.setStyleSheet(f"background-color: {self.customization.accent_color}; border: 1px solid #666;")
        self.accent_color_btn = QPushButton("Choose Color...")
        self.accent_color_btn.clicked.connect(self._choose_accent_color)
        accent_color_layout.addWidget(self.accent_color_label)
        accent_color_layout.addWidget(self.accent_color_btn)
        accent_color_layout.addStretch()
        accent_layout.addRow("Accent Color:", accent_color_layout)

        # Preset accent colors
        preset_label = QLabel("Preset Colors:")
        accent_layout.addRow(preset_label)

        preset_layout = QHBoxLayout()
        presets = [
            ("Electric Blue", "#00e0ff"),
            ("Racing Green", "#00ff88"),
            ("Safety Orange", "#ff8000"),
            ("Vibrant Red", "#ff4444"),
            ("Bright Yellow", "#ffff00"),
            ("Neon Purple", "#ff00ff"),
        ]

        for name, color in presets:
            btn = QPushButton()
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(f"background-color: {color}; border: 2px solid #666; border-radius: 4px;")
            btn.setToolTip(name)
            btn.clicked.connect(lambda checked, c=color: self._set_accent_color(c))
            preset_layout.addWidget(btn)

        accent_layout.addRow(preset_layout)
        layout.addWidget(accent_group)

        # Color validation
        validation_group = QGroupBox("Accessibility Validation")
        validation_layout = QVBoxLayout(validation_group)

        self.contrast_status_label = QLabel()
        self._update_contrast_status()
        validation_layout.addWidget(self.contrast_status_label)

        auto_fix_btn = QPushButton("Auto-Fix Contrast Issues")
        auto_fix_btn.clicked.connect(self._auto_fix_contrast)
        validation_layout.addWidget(auto_fix_btn)

        layout.addWidget(validation_group)

        layout.addStretch()
        return widget

    def _create_gauges_tab(self) -> QWidget:
        """Create gauge customization tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        gauge_group = QGroupBox("Gauge Customization")
        gauge_layout = QFormLayout(gauge_group)

        # Needle color
        needle_layout = QHBoxLayout()
        self.needle_color_label = QLabel()
        self.needle_color_label.setFixedSize(50, 30)
        self.needle_color_label.setStyleSheet(
            f"background-color: {self.customization.gauge_customization.needle_color}; border: 1px solid #666;"
        )
        needle_btn = QPushButton("Choose...")
        needle_btn.clicked.connect(lambda: self._choose_gauge_color("needle"))
        needle_layout.addWidget(self.needle_color_label)
        needle_layout.addWidget(needle_btn)
        gauge_layout.addRow("Needle Color:", needle_layout)

        # Background color
        bg_layout = QHBoxLayout()
        self.bg_color_label = QLabel()
        self.bg_color_label.setFixedSize(50, 30)
        self.bg_color_label.setStyleSheet(
            f"background-color: {self.customization.gauge_customization.background_color}; border: 1px solid #666;"
        )
        bg_btn = QPushButton("Choose...")
        bg_btn.clicked.connect(lambda: self._choose_gauge_color("background"))
        bg_layout.addWidget(self.bg_color_label)
        bg_layout.addWidget(bg_btn)
        gauge_layout.addRow("Background Color:", bg_layout)

        # Scale color
        scale_layout = QHBoxLayout()
        self.scale_color_label = QLabel()
        self.scale_color_label.setFixedSize(50, 30)
        self.scale_color_label.setStyleSheet(
            f"background-color: {self.customization.gauge_customization.scale_color}; border: 1px solid #666;"
        )
        scale_btn = QPushButton("Choose...")
        scale_btn.clicked.connect(lambda: self._choose_gauge_color("scale"))
        scale_layout.addWidget(self.scale_color_label)
        scale_layout.addWidget(scale_btn)
        gauge_layout.addRow("Scale Color:", scale_layout)

        # Text color
        text_layout = QHBoxLayout()
        self.text_color_label = QLabel()
        self.text_color_label.setFixedSize(50, 30)
        self.text_color_label.setStyleSheet(
            f"background-color: {self.customization.gauge_customization.text_color}; border: 1px solid #666;"
        )
        text_btn = QPushButton("Choose...")
        text_btn.clicked.connect(lambda: self._choose_gauge_color("text"))
        text_layout.addWidget(self.text_color_label)
        text_layout.addWidget(text_btn)
        gauge_layout.addRow("Text Color:", text_layout)

        # Warning zone color
        warning_layout = QHBoxLayout()
        self.warning_color_label = QLabel()
        self.warning_color_label.setFixedSize(50, 30)
        self.warning_color_label.setStyleSheet(
            f"background-color: {self.customization.gauge_customization.warning_zone_color}; border: 1px solid #666;"
        )
        warning_btn = QPushButton("Choose...")
        warning_btn.clicked.connect(lambda: self._choose_gauge_color("warning"))
        warning_layout.addWidget(self.warning_color_label)
        warning_layout.addWidget(warning_btn)
        gauge_layout.addRow("Warning Zone Color:", warning_layout)

        # Critical zone color
        critical_layout = QHBoxLayout()
        self.critical_color_label = QLabel()
        self.critical_color_label.setFixedSize(50, 30)
        self.critical_color_label.setStyleSheet(
            f"background-color: {self.customization.gauge_customization.critical_zone_color}; border: 1px solid #666;"
        )
        critical_btn = QPushButton("Choose...")
        critical_btn.clicked.connect(lambda: self._choose_gauge_color("critical"))
        critical_layout.addWidget(self.critical_color_label)
        critical_layout.addWidget(critical_btn)
        gauge_layout.addRow("Critical Zone Color:", critical_layout)

        layout.addWidget(gauge_group)

        # Preview gauge
        preview_group = QGroupBox("Gauge Preview")
        preview_layout = QVBoxLayout(preview_group)
        # Preview will be added dynamically
        layout.addWidget(preview_group)

        layout.addStretch()
        return widget

    def _create_accessibility_tab(self) -> QWidget:
        """Create accessibility settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Contrast information
        info_group = QGroupBox("Contrast Information")
        info_layout = QVBoxLayout(info_group)

        info_text = QLabel(
            "WCAG Accessibility Standards:\n\n"
            "• AA Level: 4.5:1 contrast ratio (minimum)\n"
            "• AAA Level: 7:1 contrast ratio (enhanced)\n\n"
            "The system automatically validates all color combinations to ensure readability."
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        layout.addWidget(info_group)

        # Current contrast ratios
        contrast_group = QGroupBox("Current Contrast Ratios")
        contrast_layout = QFormLayout(contrast_group)

        # Calculate and display contrast ratios
        current_theme = self.theme_manager.current_theme
        text_bg_ratio = ContrastValidator.get_contrast_ratio(current_theme.colors.text_primary, current_theme.colors.background)
        text_bg_accessible, _ = ContrastValidator.is_accessible(current_theme.colors.text_primary, current_theme.colors.background)

        contrast_layout.addRow("Text/Background:", QLabel(f"{text_bg_ratio:.2f}:1 {'✓' if text_bg_accessible else '✗'}"))

        accent_bg_ratio = ContrastValidator.get_contrast_ratio(current_theme.colors.accent, current_theme.colors.background)
        accent_bg_accessible, _ = ContrastValidator.is_accessible(current_theme.colors.accent, current_theme.colors.background)

        contrast_layout.addRow("Accent/Background:", QLabel(f"{accent_bg_ratio:.2f}:1 {'✓' if accent_bg_accessible else '✗'}"))

        layout.addWidget(contrast_group)

        layout.addStretch()
        return widget

    def _create_preview_tab(self) -> QWidget:
        """Create preview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        preview_label = QLabel("Theme Preview (Updates Instantly)")
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(preview_label)

        # Preview widget will show current theme
        self.preview_widget = QWidget()
        self.preview_widget.setMinimumHeight(400)
        self.preview_widget.setStyleSheet(self.theme_manager.get_stylesheet())
        layout.addWidget(self.preview_widget)

        return widget

    def _on_system_theme_changed(self, mode: SystemThemeMode) -> None:
        """Handle system theme mode change."""
        self.customization.system_theme_mode = mode
        self._apply_theme()

    def _on_oled_changed(self, enabled: bool) -> None:
        """Handle OLED optimization change."""
        self.customization.oled_optimized = enabled
        if enabled:
            self.true_black_checkbox.setChecked(True)
        self._apply_theme()

    def _on_true_black_changed(self, enabled: bool) -> None:
        """Handle true black background change."""
        self.customization.true_black_background = enabled
        self._apply_theme()

    def _on_high_contrast_changed(self, enabled: bool) -> None:
        """Handle high contrast mode change."""
        self.customization.high_contrast = enabled
        self._apply_theme()

    def _on_font_scale_changed(self, value: int) -> None:
        """Handle font scale change."""
        self.customization.font_size_scale = value / 100.0
        self._apply_theme()

    def _choose_accent_color(self) -> None:
        """Open color dialog for accent color."""
        color = QColorDialog.getColor(QColor(self.customization.accent_color), self, "Choose Accent Color")
        if color.isValid():
            self._set_accent_color(color.name())

    def _set_accent_color(self, color: str) -> None:
        """Set accent color."""
        self.customization.accent_color = color
        self.accent_color_label.setStyleSheet(f"background-color: {color}; border: 1px solid #666;")
        self._update_contrast_status()
        self._apply_theme()

    def _choose_gauge_color(self, color_type: str) -> None:
        """Open color dialog for gauge color."""
        current_color = getattr(self.customization.gauge_customization, f"{color_type}_color")
        color = QColorDialog.getColor(QColor(current_color), self, f"Choose {color_type.title()} Color")
        if color.isValid():
            setattr(self.customization.gauge_customization, f"{color_type}_color", color.name())
            label = getattr(self, f"{color_type}_color_label")
            label.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #666;")
            self._apply_theme()

    def _update_contrast_status(self) -> None:
        """Update contrast validation status."""
        current_theme = self.theme_manager.current_theme
        text_accessible, text_ratio = ContrastValidator.is_accessible(
            current_theme.colors.text_primary, current_theme.colors.background
        )
        accent_accessible, accent_ratio = ContrastValidator.is_accessible(
            self.customization.accent_color, current_theme.colors.background
        )

        status = f"Text/Background: {text_ratio:.2f}:1 {'✓' if text_accessible else '✗'}\n"
        status += f"Accent/Background: {accent_ratio:.2f}:1 {'✓' if accent_accessible else '✗'}"

        if not (text_accessible and accent_accessible):
            status += "\n⚠️ Some color combinations may not meet accessibility standards."

        self.contrast_status_label.setText(status)

    def _auto_fix_contrast(self) -> None:
        """Auto-fix contrast issues."""
        current_theme = self.theme_manager.current_theme

        # Fix text color if needed
        text_accessible, _ = ContrastValidator.is_accessible(current_theme.colors.text_primary, current_theme.colors.background)
        if not text_accessible:
            suggested = ContrastValidator.suggest_accessible_color(
                current_theme.colors.text_primary, current_theme.colors.background
            )
            current_theme.colors.text_primary = suggested

        # Fix accent color if needed
        accent_accessible, _ = ContrastValidator.is_accessible(self.customization.accent_color, current_theme.colors.background)
        if not accent_accessible:
            suggested = ContrastValidator.suggest_accessible_color(
                self.customization.accent_color, current_theme.colors.background
            )
            self.customization.accent_color = suggested
            self.accent_color_label.setStyleSheet(f"background-color: {suggested}; border: 1px solid #666;")

        self._update_contrast_status()
        self._apply_theme()

        QMessageBox.information(self, "Contrast Fixed", "Color combinations have been adjusted for better accessibility.")

    def _apply_theme(self) -> None:
        """Apply current theme customization."""
        # Determine base theme based on system mode
        if self.customization.system_theme_mode == SystemThemeMode.AUTO:
            system_theme = SystemThemeDetector.detect_system_theme()
            base_style = ThemeStyle.DARK if system_theme == SystemThemeMode.DARK else ThemeStyle.LIGHT
        elif self.customization.system_theme_mode == SystemThemeMode.DARK:
            base_style = ThemeStyle.DARK
        else:
            base_style = ThemeStyle.LIGHT

        # Get base theme
        base_theme = self.theme_manager.THEMES[base_style]

        # Apply customizations
        if self.customization.true_black_background:
            base_theme.colors.background = "#000000"
            base_theme.colors.background_secondary = "#000000"
            base_theme.colors.background_tertiary = "#0a0a0a"

        # Apply accent color
        base_theme.colors.primary = self.customization.accent_color
        base_theme.colors.accent = self.customization.accent_color

        # Apply high contrast if enabled
        if self.customization.high_contrast:
            base_theme.colors.text_primary = "#ffffff" if base_style == ThemeStyle.DARK else "#000000"
            base_theme.colors.border = "#ffffff" if base_style == ThemeStyle.DARK else "#000000"

        # Set current theme
        self.theme_manager.current_theme = base_theme

        # Update preview
        if hasattr(self, "preview_widget"):
            self.preview_widget.setStyleSheet(self.theme_manager.get_stylesheet())
            self.preview_widget.update()

        # Emit signal
        self.theme_changed.emit(base_theme)

    def _apply_and_close(self) -> None:
        """Apply theme and close dialog."""
        self._save_customization()
        self._apply_theme()
        self.accept()

    def _reset_to_defaults(self) -> None:
        """Reset to default customization."""
        self.customization = ThemeCustomization()
        self._load_ui_from_customization()
        self._apply_theme()

    def _load_ui_from_customization(self) -> None:
        """Load UI from customization settings."""
        # Update checkboxes
        if hasattr(self, "oled_checkbox"):
            self.oled_checkbox.setChecked(self.customization.oled_optimized)
        if hasattr(self, "true_black_checkbox"):
            self.true_black_checkbox.setChecked(self.customization.true_black_background)
        if hasattr(self, "high_contrast_checkbox"):
            self.high_contrast_checkbox.setChecked(self.customization.high_contrast)

        # Update radio buttons
        if hasattr(self, "system_theme_auto"):
            if self.customization.system_theme_mode == SystemThemeMode.AUTO:
                self.system_theme_auto.setChecked(True)
            elif self.customization.system_theme_mode == SystemThemeMode.DARK:
                self.system_theme_dark.setChecked(True)
            else:
                self.system_theme_light.setChecked(True)

        # Update color labels
        if hasattr(self, "accent_color_label"):
            self.accent_color_label.setStyleSheet(f"background-color: {self.customization.accent_color}; border: 1px solid #666;")

    def _load_customization(self) -> None:
        """Load customization from file."""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)

            self.customization.system_theme_mode = SystemThemeMode(data.get("system_theme_mode", "auto"))
            self.customization.accent_color = data.get("accent_color", "#00e0ff")
            self.customization.oled_optimized = data.get("oled_optimized", False)
            self.customization.true_black_background = data.get("true_black_background", False)
            self.customization.high_contrast = data.get("high_contrast", True)
            self.customization.font_size_scale = data.get("font_size_scale", 1.0)

            # Load gauge customization
            gauge_data = data.get("gauge_customization", {})
            if gauge_data:
                self.customization.gauge_customization = GaugeCustomization(**gauge_data)

        except Exception as e:
            LOGGER.warning("Failed to load theme customization: %s", e)

    def _save_customization(self) -> None:
        """Save customization to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "system_theme_mode": self.customization.system_theme_mode.value,
                "accent_color": self.customization.accent_color,
                "oled_optimized": self.customization.oled_optimized,
                "true_black_background": self.customization.true_black_background,
                "high_contrast": self.customization.high_contrast,
                "font_size_scale": self.customization.font_size_scale,
                "gauge_customization": asdict(self.customization.gauge_customization),
            }

            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            LOGGER.error("Failed to save theme customization: %s", e)

    def get_gauge_customization(self) -> GaugeCustomization:
        """Get gauge customization settings."""
        return self.customization.gauge_customization


__all__ = [
    "AdvancedThemeCustomizer",
    "ThemeCustomization",
    "GaugeCustomization",
    "SystemThemeMode",
    "SystemThemeDetector",
    "ContrastValidator",
]



