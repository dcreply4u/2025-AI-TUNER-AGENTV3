"""
Theme Selection Dialog

Allows users to select themes and customize backgrounds.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSlider,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSlider,
        QVBoxLayout,
        QWidget,
    )

from ui.theme_manager import ThemeManager, ThemeStyle


class ThemePreviewWidget(QWidget):
    """Preview widget showing theme colors."""

    def __init__(self, theme_manager: ThemeManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setMinimumSize(200, 150)
        self.setMaximumSize(300, 200)

    def paintEvent(self, event) -> None:
        """Paint theme preview."""
        from PySide6.QtGui import QPainter, QColor

        painter = QPainter(self)
        c = self.theme_manager.current_theme.colors

        # Draw background
        painter.fillRect(self.rect(), QColor(c.background))

        # Draw sample widgets
        widget_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.fillRect(widget_rect, QColor(c.widget_background))

        # Draw primary color accent
        accent_rect = widget_rect.adjusted(5, 5, -widget_rect.width() + 50, -widget_rect.height() + 30)
        painter.fillRect(accent_rect, QColor(c.primary))

        # Draw text sample
        painter.setPen(QColor(c.text_primary))
        painter.drawText(widget_rect.adjusted(60, 10, -10, -10), Qt.AlignmentFlag.AlignLeft, "Sample Text")


class ThemeDialog(QDialog):
    """Dialog for selecting and customizing themes."""

    def __init__(self, theme_manager: ThemeManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Theme Settings")
        self.resize(600, 500)
        self.theme_manager = theme_manager
        self.selected_theme = theme_manager.current_theme.style

        layout = QVBoxLayout(self)

        # Theme selection
        theme_group = QGroupBox("Theme Selection")
        theme_layout = QVBoxLayout(theme_group)

        # Create theme buttons
        self.theme_buttons = {}
        buttons_layout = QHBoxLayout()

        for style in ThemeStyle:
            btn = QPushButton(theme_manager.THEMES[style].name)
            btn.setCheckable(True)
            btn.setProperty("theme_style", style.value)
            if style == theme_manager.current_theme.style:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, s=style: self._select_theme(s))
            self.theme_buttons[style] = btn
            buttons_layout.addWidget(btn)

        theme_layout.addLayout(buttons_layout)

        # Preview
        preview_label = QLabel("Preview:")
        preview_label.setProperty("class", "subheading")
        theme_layout.addWidget(preview_label)

        self.preview = ThemePreviewWidget(theme_manager, self)
        theme_layout.addWidget(self.preview)

        layout.addWidget(theme_group)

        # Background customization
        bg_group = QGroupBox("Background Customization")
        bg_layout = QFormLayout(bg_group)

        # Background image
        bg_image_layout = QHBoxLayout()
        self.bg_image_label = QLabel(theme_manager.current_theme.background_image or "No image selected")
        bg_image_btn = QPushButton("Select Image")
        bg_image_btn.clicked.connect(self._select_background_image)
        clear_bg_btn = QPushButton("Clear")
        clear_bg_btn.clicked.connect(self._clear_background_image)
        bg_image_layout.addWidget(self.bg_image_label, 1)
        bg_image_layout.addWidget(bg_image_btn)
        bg_image_layout.addWidget(clear_bg_btn)
        bg_layout.addRow("Background Image:", bg_image_layout)

        # Background opacity
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(theme_manager.current_theme.background_opacity * 100))
        self.opacity_slider.valueChanged.connect(self._update_opacity_preview)
        self.opacity_label = QLabel(f"{self.opacity_slider.value()}%")
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        bg_layout.addRow("Opacity:", opacity_layout)

        layout.addWidget(bg_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _select_theme(self, style: ThemeStyle) -> None:
        """Select a theme."""
        self.selected_theme = style
        self.theme_manager.set_theme(style)
        self.preview.update()  # Refresh preview

    def _select_background_image(self) -> None:
        """Select background image."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Background Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*.*)",
        )
        if path:
            self.theme_manager.set_background_image(path, self.opacity_slider.value() / 100.0)
            self.bg_image_label.setText(Path(path).name)
            self.preview.update()

    def _clear_background_image(self) -> None:
        """Clear background image."""
        self.theme_manager.clear_background_image()
        self.bg_image_label.setText("No image selected")
        self.preview.update()

    def _update_opacity_preview(self, value: int) -> None:
        """Update opacity preview."""
        self.opacity_label.setText(f"{value}%")
        if self.theme_manager.current_theme.background_image:
            self.theme_manager.set_background_image(
                self.theme_manager.current_theme.background_image, value / 100.0
            )
        self.preview.update()


__all__ = ["ThemeDialog", "ThemePreviewWidget"]

