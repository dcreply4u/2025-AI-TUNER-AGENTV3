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

        # Auto-detect button
        detect_layout = QHBoxLayout()
        detect_btn = QPushButton("🔍 Auto-Detect USB Cameras")
        detect_btn.clicked.connect(self._auto_detect_cameras)
        detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        detect_layout.addWidget(detect_btn)
        detect_layout.addStretch()
        layout.addLayout(detect_layout)
        
        # Existing cameras
        existing_group = QGroupBox("Existing Cameras")
        existing_layout = QVBoxLayout(existing_group)
        self.camera_list = QComboBox()
        self.camera_list.addItem("-- Select Camera --", None)
        self._refresh_camera_list()
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

        # Source input with detected cameras dropdown
        source_layout = QHBoxLayout()
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("0 (USB), rtsp://..., http://...")
        source_layout.addWidget(self.source_input)
        
        # Dropdown for detected USB cameras
        self.detected_cameras_combo = QComboBox()
        self.detected_cameras_combo.addItem("-- Select Detected Camera --", None)
        self.detected_cameras_combo.currentTextChanged.connect(self._on_detected_camera_selected)
        source_layout.addWidget(self.detected_cameras_combo)
        add_layout.addRow("Source:", source_layout)

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
        
        # Refresh detected cameras on dialog show
        self._refresh_detected_cameras()

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
            self._refresh_camera_list()
            self._refresh_detected_cameras()
            self.name_input.clear()
            self.source_input.clear()
            # Reset detected camera dropdown
            self.detected_cameras_combo.setCurrentIndex(0)

    def _refresh_camera_list(self) -> None:
        """Refresh the camera list dropdown."""
        self.camera_list.clear()
        self.camera_list.addItem("-- Select Camera --", None)
        if self.camera_manager and hasattr(self.camera_manager, 'camera_manager'):
            for name in self.camera_manager.camera_manager.cameras.keys():
                self.camera_list.addItem(name, name)
    
    def _auto_detect_cameras(self) -> None:
        """Auto-detect and add USB cameras."""
        if not self.camera_manager:
            return
        
        try:
            # Trigger auto-detection
            added = self.camera_manager.auto_detect_and_add_cameras(include_network=False)
            
            if added:
                # Refresh camera list
                self._refresh_camera_list()
                # Refresh detected cameras dropdown
                self._refresh_detected_cameras()
                
                # Show success message
                from PySide6.QtWidgets import QMessageBox
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Cameras Detected")
                msg.setText(f"Found and added {len(added)} camera(s):\n" + "\n".join(f"  • {name}" for name in added))
                msg.exec()
            else:
                # Show no cameras found message
                from PySide6.QtWidgets import QMessageBox
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("No Cameras Found")
                msg.setText("No USB cameras were detected.\n\nMake sure your camera is connected and try again.")
                msg.exec()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Detection Error")
            msg.setText(f"Error detecting cameras: {str(e)}")
            msg.exec()
    
    def _refresh_detected_cameras(self) -> None:
        """Refresh the detected cameras dropdown."""
        self.detected_cameras_combo.clear()
        self.detected_cameras_combo.addItem("-- Select Detected Camera --", None)
        
        if not self.camera_manager:
            return
        
        try:
            from interfaces.camera_interface import CameraAutoDetector
            detected = CameraAutoDetector.detect_all_cameras(include_network=False)
            
            # Filter out cameras that are already added
            existing_names = set()
            if hasattr(self.camera_manager, 'camera_manager'):
                existing_names = set(self.camera_manager.camera_manager.cameras.keys())
            
            for cam in detected:
                if cam.name not in existing_names:
                    display_text = f"{cam.name} ({cam.camera_type.value}) - {cam.source}"
                    self.detected_cameras_combo.addItem(display_text, cam)
        except Exception as e:
            print(f"Error refreshing detected cameras: {e}")
    
    def _on_detected_camera_selected(self, text: str) -> None:
        """Handle selection of a detected camera."""
        cam_data = self.detected_cameras_combo.currentData()
        if cam_data:
            # Auto-fill the form with detected camera info
            self.name_input.setText(cam_data.name)
            self.source_input.setText(cam_data.source)
            self.type_combo.setCurrentText(cam_data.camera_type.value.upper())
            self.width_spin.setValue(cam_data.width or 1920)
            self.height_spin.setValue(cam_data.height or 1080)
            self.fps_spin.setValue(cam_data.fps or 30)
            if cam_data.position:
                idx = self.position_combo.findText(cam_data.position)
                if idx >= 0:
                    self.position_combo.setCurrentIndex(idx)
    
    def _remove_camera(self) -> None:
        """Remove selected camera."""
        if not self.camera_manager:
            return

        name = self.camera_list.currentData()
        if name:
            self.camera_manager.remove_camera(name)
            self._refresh_camera_list()
            self._refresh_detected_cameras()


__all__ = ["CameraConfigDialog"]

