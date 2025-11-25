"""
Overlay Configuration Dialog

UI for configuring video overlay widgets - choose what to display on screen.
"""

from __future__ import annotations

from typing import Dict, List, Optional

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

from services.video_overlay import OverlayPosition, OverlayStyle, OverlayWidget


class WidgetConfigRow(QWidget):
    """Single widget configuration row."""

    def __init__(self, name: str, widget: OverlayWidget, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.name = name
        self.widget = widget

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # Enable checkbox
        self.enabled_cb = QCheckBox(widget.name)
        self.enabled_cb.setChecked(widget.enabled)
        layout.addWidget(self.enabled_cb)

        # Position selector
        layout.addWidget(QLabel("Position:"))
        self.position_combo = QComboBox()
        for pos in OverlayPosition:
            self.position_combo.addItem(pos.value.replace("_", " ").title(), pos)
        current_idx = self.position_combo.findData(widget.position)
        if current_idx >= 0:
            self.position_combo.setCurrentIndex(current_idx)
        layout.addWidget(self.position_combo)

        # Font scale
        layout.addWidget(QLabel("Size:"))
        self.font_scale_spin = QSpinBox()
        self.font_scale_spin.setRange(1, 300)
        self.font_scale_spin.setValue(int(widget.font_scale * 100))
        self.font_scale_spin.setSuffix("%")
        layout.addWidget(self.font_scale_spin)

        # Show label checkbox
        self.show_label_cb = QCheckBox("Show Label")
        self.show_label_cb.setChecked(widget.show_label)
        layout.addWidget(self.show_label_cb)

        layout.addStretch()

    def get_config(self) -> Dict:
        """Get current configuration."""
        return {
            "enabled": self.enabled_cb.isChecked(),
            "position": self.position_combo.currentData(),
            "font_scale": self.font_scale_spin.value() / 100.0,
            "show_label": self.show_label_cb.isChecked(),
        }


class OverlayConfigDialog(QDialog):
    """Dialog for configuring video overlay widgets."""

    def __init__(self, current_config: Optional[Dict] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Video Overlay Configuration")
        self.resize(700, 600)

        layout = QVBoxLayout(self)

        # Style selection
        style_group = QGroupBox("Overlay Style")
        style_layout = QFormLayout(style_group)
        self.style_combo = QComboBox()
        for style in OverlayStyle:
            self.style_combo.addItem(style.value.title(), style)
        style_layout.addRow("Style:", self.style_combo)
        layout.addWidget(style_group)

        # Widget configuration
        widgets_group = QGroupBox("Display Widgets")
        widgets_layout = QVBoxLayout(widgets_group)

        # Scroll area for widget list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Create widget config rows
        self.widget_rows: Dict[str, WidgetConfigRow] = {}
        from services.video_overlay import VideoOverlay

        overlay = VideoOverlay()
        for name, widget in overlay.widgets.items():
            row = WidgetConfigRow(name, widget)
            self.widget_rows[name] = row
            scroll_layout.addWidget(row)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        widgets_layout.addWidget(scroll)
        layout.addWidget(widgets_group)

        # Quick presets
        presets_group = QGroupBox("Quick Presets")
        presets_layout = QHBoxLayout(presets_group)
        self.minimal_btn = QPushButton("Minimal")
        self.racing_btn = QPushButton("Racing")
        self.full_btn = QPushButton("Full")
        self.minimal_btn.clicked.connect(lambda: self._apply_preset("minimal"))
        self.racing_btn.clicked.connect(lambda: self._apply_preset("racing"))
        self.full_btn.clicked.connect(lambda: self._apply_preset("full"))
        presets_layout.addWidget(self.minimal_btn)
        presets_layout.addWidget(self.racing_btn)
        presets_layout.addWidget(self.full_btn)
        presets_layout.addStretch()
        layout.addWidget(presets_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Load current config if provided
        if current_config:
            self.load_config(current_config)

    def _apply_preset(self, preset: str) -> None:
        """Apply a preset configuration."""
        if preset == "minimal":
            # Only essential metrics
            enabled = ["speed", "rpm", "lap_time"]
        elif preset == "racing":
            # Racing essentials
            enabled = ["speed", "rpm", "lap_time", "lap_number", "throttle", "boost", "coolant"]
        else:  # full
            # All widgets
            enabled = list(self.widget_rows.keys())

        for name, row in self.widget_rows.items():
            row.enabled_cb.setChecked(name in enabled)

    def get_config(self) -> Dict:
        """Get current configuration."""
        widget_config = {}
        enabled_widgets = []

        for name, row in self.widget_rows.items():
            config = row.get_config()
            widget_config[name] = config
            if config["enabled"]:
                enabled_widgets.append(name)

        return {
            "style": self.style_combo.currentData().value,
            "enabled_widgets": enabled_widgets,
            "widget_config": widget_config,
        }

    def load_config(self, config: Dict) -> None:
        """Load configuration."""
        # Set style
        if "style" in config:
            style_value = config["style"]
            for i in range(self.style_combo.count()):
                if self.style_combo.itemData(i).value == style_value:
                    self.style_combo.setCurrentIndex(i)
                    break

        # Set widget configs
        if "widget_config" in config:
            for name, widget_config in config["widget_config"].items():
                if name in self.widget_rows:
                    row = self.widget_rows[name]
                    row.enabled_cb.setChecked(widget_config.get("enabled", True))
                    if "position" in widget_config:
                        pos_value = widget_config["position"]
                        # Handle both enum and string values
                        if isinstance(pos_value, str):
                            # Find matching enum
                            for pos_enum in OverlayPosition:
                                if pos_enum.value == pos_value:
                                    pos_value = pos_enum
                                    break
                        for i in range(row.position_combo.count()):
                            if row.position_combo.itemData(i) == pos_value:
                                row.position_combo.setCurrentIndex(i)
                                break
                    if "font_scale" in widget_config:
                        row.font_scale_spin.setValue(int(widget_config["font_scale"] * 100))
                    if "show_label" in widget_config:
                        row.show_label_cb.setChecked(widget_config["show_label"])


__all__ = ["OverlayConfigDialog"]

