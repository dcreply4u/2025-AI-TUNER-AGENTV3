"""
USB Setup Dialog

Prompts user when USB device is detected, asking if they want to format
and configure it automatically.
"""

from __future__ import annotations

from typing import Optional

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
        QLineEdit,
        QMessageBox,
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
        QLineEdit,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

from services.usb_manager import USBDevice, USBManager


class USBSetupDialog(QDialog):
    """Dialog for setting up a detected USB device."""

    def __init__(self, device: USBDevice, usb_manager: USBManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.device = device
        self.usb_manager = usb_manager
        self.setup_complete = False

        self.setWindowTitle("USB Device Detected")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Device info
        info_group = QGroupBox("Device Information")
        info_layout = QFormLayout(info_group)

        info_layout.addRow("Label:", QLabel(device.label))
        info_layout.addRow("Mount Point:", QLabel(device.mount_point))
        info_layout.addRow("Size:", QLabel(f"{device.size_gb:.2f} GB"))
        info_layout.addRow("Filesystem:", QLabel(device.filesystem))

        layout.addWidget(info_group)

        # Setup options
        setup_group = QGroupBox("Setup Options")
        setup_layout = QVBoxLayout(setup_group)

        self.auto_setup_cb = QCheckBox("Automatically configure directory structure")
        self.auto_setup_cb.setChecked(True)
        setup_layout.addWidget(self.auto_setup_cb)

        self.format_cb = QCheckBox("Format device (WARNING: This will erase all data!)")
        self.format_cb.setChecked(False)
        setup_layout.addWidget(self.format_cb)

        # Format options (only shown if format is checked)
        format_group = QGroupBox("Format Options")
        format_layout = QFormLayout(format_group)

        self.filesystem_combo = QComboBox()
        self.filesystem_combo.addItems(["exfat", "fat32", "ntfs"])
        self.filesystem_combo.setCurrentText("exfat")
        format_layout.addRow("Filesystem:", self.filesystem_combo)

        self.label_input = QLineEdit("AITUNER")
        format_layout.addRow("Volume Label:", self.label_input)

        format_group.setEnabled(False)
        self.format_cb.toggled.connect(format_group.setEnabled)
        setup_layout.addWidget(format_group)

        layout.addWidget(setup_group)

        # Warning message
        warning_label = QLabel(
            "<b>Warning:</b> Formatting will erase all data on this device. "
            "Make sure you have backed up any important files."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: red;")
        layout.addWidget(warning_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ignore
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Setup")
        buttons.button(QDialogButtonBox.StandardButton.Ignore).setText("Skip")
        buttons.accepted.connect(self._setup_device)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Ignore).clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _setup_device(self) -> None:
        """Set up the USB device."""
        try:
            # Format if requested
            if self.format_cb.isChecked():
                reply = QMessageBox.warning(
                    self,
                    "Confirm Format",
                    f"Are you sure you want to format {self.device.label}?\n\n"
                    "This will erase ALL data on the device!\n\n"
                    "This action cannot be undone.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if reply != QMessageBox.StandardButton.Yes:
                    return

                # Show progress
                QMessageBox.information(self, "Formatting", "Formatting device... This may take a moment.")
                self.setEnabled(False)

                filesystem = self.filesystem_combo.currentText()
                label = self.label_input.text() or "AITUNER"

                if not self.usb_manager.format_device(self.device, filesystem=filesystem, label=label):
                    QMessageBox.critical(self, "Error", "Failed to format device. Please check permissions and try again.")
                    self.setEnabled(True)
                    return

                # Rescan for device after formatting
                devices = self.usb_manager.scan_for_devices()
                # Find the device again (it might have a new mount point)
                for dev in devices:
                    if dev.device_path == self.device.device_path:
                        self.device = dev
                        break

                self.setEnabled(True)

            # Set up directory structure
            if self.auto_setup_cb.isChecked():
                if self.usb_manager.setup_device(self.device):
                    self.setup_complete = True
                    QMessageBox.information(
                        self,
                        "Setup Complete",
                        f"USB device '{self.device.label}' has been configured successfully.\n\n"
                        f"Session directory created at:\n{self.usb_manager.session_base_path}",
                    )
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to set up device directories. Please check permissions.")
            else:
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during setup:\n{str(e)}")


class USBMonitorWidget(QWidget):
    """Widget that monitors for USB devices and shows setup dialog."""

    def __init__(self, usb_manager: USBManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.usb_manager = usb_manager
        self.processed_devices: set[str] = set()

        # Set up callback
        self.usb_manager.on_device_detected = self._on_device_detected

    def _on_device_detected(self, device: USBDevice) -> None:
        """Handle device detection."""
        # Skip if already processed
        if device.mount_point in self.processed_devices:
            return

        # Show setup dialog
        dialog = USBSetupDialog(device, self.usb_manager, parent=self)
        if dialog.exec():
            self.processed_devices.add(device.mount_point)
            if dialog.setup_complete:
                # Device is ready to use
                pass


__all__ = ["USBSetupDialog", "USBMonitorWidget"]

