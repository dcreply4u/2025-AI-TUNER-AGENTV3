"""
Camera Configuration Dialog

UI for adding/removing cameras and configuring camera settings.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

from interfaces.camera_interface import CameraConfig, CameraType


class CameraConfigDialog(QDialog):
    """Dialog for configuring cameras."""

    def __init__(self, camera_manager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Camera Configuration")
        self.resize(500, 400)
        self.camera_manager = camera_manager

        layout = QVBoxLayout(self)

        # Existing cameras
        existing_group = QGroupBox("Existing Cameras")
        existing_layout = QVBoxLayout(existing_group)
        self.camera_list = QComboBox()
        self.camera_list.addItem("-- Select Camera --", None)
        if camera_manager:
            for name in camera_manager.camera_manager.cameras.keys():
                self.camera_list.addItem(name, name)
        existing_layout.addWidget(QLabel("Camera:"))
        existing_layout.addWidget(self.camera_list)

        remove_btn = QPushButton("Remove Camera")
        remove_btn.clicked.connect(self._remove_camera)
        existing_layout.addWidget(remove_btn)
        layout.addWidget(existing_group)

        # Add new camera
        add_group = QGroupBox("Add New Camera")
        add_layout = QFormLayout(add_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., front, rear")
        add_layout.addRow("Name:", self.name_input)

        self.type_combo = QComboBox()
        for cam_type in CameraType:
            self.type_combo.addItem(cam_type.value.upper(), cam_type)
        add_layout.addRow("Type:", self.type_combo)

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("0 (USB), rtsp://..., http://...")
        add_layout.addRow("Source:", self.source_input)

        self.position_combo = QComboBox()
        self.position_combo.addItems(["front", "rear", "other"])
        add_layout.addRow("Position:", self.position_combo)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(320, 3840)
        self.width_spin.setValue(1920)
        add_layout.addRow("Width:", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(240, 2160)
        self.height_spin.setValue(1080)
        add_layout.addRow("Height:", self.height_spin)

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(30)
        add_layout.addRow("FPS:", self.fps_spin)

        self.enabled_cb = QCheckBox()
        self.enabled_cb.setChecked(False)
        add_layout.addRow("Enabled:", self.enabled_cb)

        add_btn = QPushButton("Add Camera")
        add_btn.clicked.connect(self._add_camera)
        add_layout.addRow("", add_btn)

        layout.addWidget(add_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_camera(self) -> None:
        """Add a new camera."""
        if not self.camera_manager:
            return

        name = self.name_input.text().strip()
        if not name:
            return

        config = CameraConfig(
            name=name,
            camera_type=self.type_combo.currentData(),
            source=self.source_input.text().strip(),
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            fps=self.fps_spin.value(),
            enabled=self.enabled_cb.isChecked(),
            position=self.position_combo.currentText(),
        )

        if self.camera_manager.add_camera(config):
            self.camera_list.addItem(name, name)
            self.name_input.clear()
            self.source_input.clear()

    def _remove_camera(self) -> None:
        """Remove selected camera."""
        if not self.camera_manager:
            return

        name = self.camera_list.currentData()
        if name:
            self.camera_manager.remove_camera(name)
            idx = self.camera_list.findData(name)
            if idx >= 0:
                self.camera_list.removeItem(idx)


__all__ = ["CameraConfigDialog"]

