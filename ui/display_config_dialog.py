"""
Display Configuration Dialog

UI for configuring external monitor output and display settings.
"""

from __future__ import annotations

from typing import Dict, Optional

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
        QVBoxLayout,
        QWidget,
    )

from services.display_manager import DisplayInfo, DisplayManager


class DisplayConfigDialog(QDialog):
    """Dialog for configuring display output."""

    def __init__(self, display_manager: DisplayManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.display_manager = display_manager
        self.selected_display: Optional[DisplayInfo] = None
        self.fullscreen_mode = False

        self.setWindowTitle("Display Configuration")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Display selection
        display_group = QGroupBox("Select Display")
        display_layout = QVBoxLayout(display_group)

        display_layout.addWidget(QLabel("Available Displays:"))
        self.display_combo = QComboBox()
        self._populate_displays()
        display_layout.addWidget(self.display_combo)

        # Display info
        self.display_info_label = QLabel()
        self.display_info_label.setWordWrap(True)
        display_layout.addWidget(self.display_info_label)

        # Update info when selection changes
        self.display_combo.currentIndexChanged.connect(self._update_display_info)
        self._update_display_info()

        layout.addWidget(display_group)

        # Display options
        options_group = QGroupBox("Display Options")
        options_layout = QVBoxLayout(options_group)

        self.fullscreen_cb = QCheckBox("Fullscreen mode")
        self.fullscreen_cb.setChecked(False)
        options_layout.addWidget(self.fullscreen_cb)

        self.stay_on_top_cb = QCheckBox("Keep window on top")
        self.stay_on_top_cb.setChecked(True)
        options_layout.addWidget(self.stay_on_top_cb)

        layout.addWidget(options_group)

        # Test button
        test_btn = QPushButton("Test Display")
        test_btn.clicked.connect(self._test_display)
        layout.addWidget(test_btn)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_displays(self) -> None:
        """Populate display combo box."""
        self.display_combo.clear()
        displays = self.display_manager.get_displays()

        for display in displays:
            label = f"{display.name}"
            if display.primary:
                label += " (Primary)"
            self.display_combo.addItem(label, display)

    def _update_display_info(self) -> None:
        """Update display information label."""
        display = self.display_combo.currentData()
        if display:
            info = (
                f"Resolution: {display.geometry.width()}x{display.geometry.height()}\n"
                f"Position: ({display.geometry.x()}, {display.geometry.y()})\n"
                f"Primary: {'Yes' if display.primary else 'No'}"
            )
            self.display_info_label.setText(info)
            self.selected_display = display

    def _test_display(self) -> None:
        """Test display by moving main window."""
        display = self.display_combo.currentData()
        if not display:
            return

        parent = self.parent()
        if parent:
            self.display_manager.move_window_to_display(
                parent,
                display,
                fullscreen=self.fullscreen_cb.isChecked(),
            )

    def get_config(self) -> Dict:
        """Get current configuration."""
        display = self.display_combo.currentData()
        return {
            "display": display,
            "fullscreen": self.fullscreen_cb.isChecked(),
            "stay_on_top": self.stay_on_top_cb.isChecked(),
        }


__all__ = ["DisplayConfigDialog"]

