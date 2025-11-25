"""
License Entry Dialog

UI for entering and activating license keys.
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QCheckBox,
    QMessageBox,
    QGroupBox,
    QWidget,
)

from ui.ui_scaling import get_scaled_size, get_scaled_font_size

from core.license_manager import get_license_manager, LicenseType

LOGGER = logging.getLogger(__name__)


class LicenseDialog(QDialog):
    """Dialog for entering and activating license keys."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.license_manager = get_license_manager()
        self.setWindowTitle("License Activation")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self) -> None:
        """Setup the license dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("License Activation")
        title.setStyleSheet(f"font-size: {get_scaled_font_size(16)}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Current license status
        status_group = QGroupBox("Current License Status")
        status_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }}
        """)
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #ffffff; font-size: 11px;")
        status_layout.addWidget(self.status_label)
        
        self.license_info_label = QLabel()
        self.license_info_label.setStyleSheet("color: #808080; font-size: 10px;")
        status_layout.addWidget(self.license_info_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # License key entry
        entry_group = QGroupBox("Enter License Key")
        entry_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {get_scaled_font_size(11)}px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }}
        """)
        entry_layout = QVBoxLayout()
        
        entry_layout.addWidget(QLabel("License Key:"))
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("AI-TUNER-XXXX-XXXX-XXXX-XXXX")
        self.license_input.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 5px;")
        self.license_input.textChanged.connect(self._on_key_changed)
        entry_layout.addWidget(self.license_input)
        
        # YubiKey option
        self.yubikey_checkbox = QCheckBox("Use YubiKey for activation (if available)")
        self.yubikey_checkbox.setStyleSheet("color: #ffffff; font-size: 10px;")
        self.yubikey_checkbox.setEnabled(self.license_manager.yubikey_enabled)
        if not self.license_manager.yubikey_enabled:
            self.yubikey_checkbox.setToolTip("YubiKey not detected")
        entry_layout.addWidget(self.yubikey_checkbox)
        
        entry_group.setLayout(entry_layout)
        layout.addWidget(entry_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.activate_btn = QPushButton("Activate License")
        self.activate_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 8px; font-weight: bold;")
        self.activate_btn.clicked.connect(self._activate_license)
        self.activate_btn.setEnabled(False)
        button_layout.addWidget(self.activate_btn)
        
        if self.license_manager.is_licensed():
            self.deactivate_btn = QPushButton("Deactivate")
            self.deactivate_btn.setStyleSheet("background-color: #ff8000; color: #ffffff; padding: 8px;")
            self.deactivate_btn.clicked.connect(self._deactivate_license)
            button_layout.addWidget(self.deactivate_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 8px;")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Info text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(100)
        info_text.setPlainText(
            "License Key Format: AI-TUNER-XXXX-XXXX-XXXX-XXXX\n\n"
            "License Types:\n"
            "• BASIC: ECU tuning, basic features\n"
            "• PRO: All features including advanced AI, cloud sync\n"
            "• ENTERPRISE: All features + custom support\n\n"
            "YubiKey: Hardware-based license activation for maximum security."
        )
        info_text.setStyleSheet("background-color: #0a0a0a; color: #808080; border: 1px solid #404040; font-size: 10px;")
        layout.addWidget(info_text)
    
    def _on_key_changed(self, text: str) -> None:
        """Handle license key input change."""
        # Remove spaces and convert to uppercase
        cleaned = text.strip().upper().replace(' ', '')
        if cleaned != text:
            self.license_input.setText(cleaned)
        
        # Enable activate button if key looks valid
        is_valid = self.license_manager.validate_license_key(cleaned)
        self.activate_btn.setEnabled(is_valid and len(cleaned) > 0)
    
    def _activate_license(self) -> None:
        """Activate the entered license key."""
        license_key = self.license_input.text().strip().upper()
        use_yubikey = self.yubikey_checkbox.isChecked()
        
        success, message = self.license_manager.activate_license(
            license_key,
            save_to_file=True,
            use_yubikey=use_yubikey,
        )
        
        if success:
            QMessageBox.information(
                self,
                "License Activated",
                f"License activated successfully!\n\n{message}\n\n"
                "Please restart the application for all features to be enabled."
            )
            self.update_display()
            self.license_input.clear()
        else:
            QMessageBox.warning(
                self,
                "Activation Failed",
                f"Failed to activate license:\n\n{message}\n\n"
                "Please check your license key and try again."
            )
    
    def _deactivate_license(self) -> None:
        """Deactivate current license."""
        reply = QMessageBox.question(
            self,
            "Deactivate License",
            "Are you sure you want to deactivate the current license?\n\n"
            "The application will run in demo mode after deactivation.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.license_manager.deactivate_license():
                QMessageBox.information(
                    self,
                    "License Deactivated",
                    "License has been deactivated.\n\n"
                    "The application will run in demo mode."
                )
                self.update_display()
            else:
                QMessageBox.warning(
                    self,
                    "Deactivation Failed",
                    "Failed to deactivate license."
                )
    
    def update_display(self) -> None:
        """Update license status display."""
        info = self.license_manager.get_license_info()
        
        if info['licensed']:
            license_type = info['type'].upper()
            self.status_label.setText(f"Status: LICENSED ({license_type})")
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 11px;")
            
            status_text = f"License Type: {license_type}\n"
            if info.get('activated_date'):
                status_text += f"Activated: {info['activated_date']}\n"
            if info.get('expires'):
                status_text += f"Expires: {info['expires']}\n"
            if info.get('yubikey_used'):
                status_text += "YubiKey: Enabled\n"
            
            self.license_info_label.setText(status_text)
        else:
            self.status_label.setText("Status: DEMO MODE")
            self.status_label.setStyleSheet("color: #ff8000; font-weight: bold; font-size: 11px;")
            
            status_text = "No license active - Running in demo mode\n"
            status_text += "Enter a license key to unlock full features\n"
            if info.get('yubikey_available'):
                status_text += "YubiKey: Available (can be used for activation)"
            
            self.license_info_label.setText(status_text)


__all__ = ["LicenseDialog"]

