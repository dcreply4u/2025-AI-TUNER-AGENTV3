"""
Encryption Settings Dialog - Configure File Encryption

Allows users to:
- Enable/disable encryption
- Choose encryption method (YubiKey or password)
- Encrypt/decrypt existing files
- Set encryption preferences
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from core.file_encryption import EncryptedFileManager, FileEncryption


class EncryptionSettingsDialog(QDialog):
    """Dialog for configuring file encryption."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("File Encryption Settings")
        self.setMinimumWidth(500)
        
        self.encryption_manager: Optional[EncryptedFileManager] = None
        
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up UI components."""
        layout = QVBoxLayout(self)

        # Encryption enabled
        self.enable_checkbox = QCheckBox("Enable file encryption")
        self.enable_checkbox.setToolTip(
            "Encrypt configuration and data files for security"
        )
        layout.addWidget(self.enable_checkbox)

        # Encryption method
        method_group = QGroupBox("Encryption Method")
        method_layout = QVBoxLayout()
        
        self.yubikey_radio = QRadioButton("Use YubiKey (Hardware Security)")
        self.yubikey_radio.setToolTip(
            "Store encryption key on YubiKey hardware device"
        )
        method_layout.addWidget(self.yubikey_radio)
        
        self.password_radio = QRadioButton("Use Password")
        self.password_radio.setToolTip("Use password-based encryption")
        method_layout.addWidget(self.password_radio)
        
        self.device_radio = QRadioButton("Use Device Key (Automatic)")
        self.device_radio.setToolTip(
            "Use device-based key (no password needed)"
        )
        self.device_radio.setChecked(True)
        method_layout.addWidget(self.device_radio)
        
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)

        # Password input (if password method selected)
        self.password_label = QLabel("Encryption Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter encryption password")
        self.password_input.setEnabled(False)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # Connect signals
        self.password_radio.toggled.connect(
            lambda checked: self.password_input.setEnabled(checked)
        )

        # File operations
        files_group = QGroupBox("File Operations")
        files_layout = QVBoxLayout()
        
        encrypt_btn = QPushButton("Encrypt Existing Files...")
        encrypt_btn.setToolTip("Encrypt existing configuration and data files")
        encrypt_btn.clicked.connect(self._encrypt_existing_files)
        files_layout.addWidget(encrypt_btn)
        
        decrypt_btn = QPushButton("Decrypt Existing Files...")
        decrypt_btn.setToolTip("Decrypt encrypted files")
        decrypt_btn.clicked.connect(self._decrypt_existing_files)
        files_layout.addWidget(decrypt_btn)
        
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        # Directories to encrypt
        dirs_group = QGroupBox("Directories to Encrypt")
        dirs_layout = QVBoxLayout()
        
        self.encrypt_config_checkbox = QCheckBox("Configuration files (config/)")
        self.encrypt_config_checkbox.setChecked(True)
        dirs_layout.addWidget(self.encrypt_config_checkbox)
        
        self.encrypt_data_checkbox = QCheckBox("Data logs (logs/)")
        self.encrypt_data_checkbox.setChecked(True)
        dirs_layout.addWidget(self.encrypt_data_checkbox)
        
        self.encrypt_db_checkbox = QCheckBox("Database files (*.db, *.sqlite)")
        self.encrypt_db_checkbox.setChecked(True)
        dirs_layout.addWidget(self.encrypt_db_checkbox)
        
        dirs_group.setLayout(dirs_layout)
        layout.addWidget(dirs_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_settings(self) -> None:
        """Load current encryption settings."""
        # Load from config or environment
        import os
        encryption_enabled = os.environ.get("AI_TUNER_ENCRYPTION_ENABLED", "false").lower() == "true"
        use_yubikey = os.environ.get("AI_TUNER_USE_YUBIKEY", "false").lower() == "true"
        
        self.enable_checkbox.setChecked(encryption_enabled)
        self.yubikey_radio.setChecked(use_yubikey)
        if not use_yubikey:
            self.device_radio.setChecked(True)

    def _save_settings(self) -> None:
        """Save encryption settings."""
        encryption_enabled = self.enable_checkbox.isChecked()
        use_yubikey = self.yubikey_radio.isChecked()
        password = self.password_input.text() if self.password_radio.isChecked() else None

        # Validate password if required
        if self.password_radio.isChecked() and not password:
            QMessageBox.warning(
                self,
                "Password Required",
                "Please enter an encryption password.",
            )
            return

        # Initialize encryption manager
        try:
            self.encryption_manager = EncryptedFileManager(
                encryption_enabled=encryption_enabled,
                use_yubikey=use_yubikey,
                password=password,
            )

            # Save settings to environment/config
            import os
            os.environ["AI_TUNER_ENCRYPTION_ENABLED"] = str(encryption_enabled).lower()
            os.environ["AI_TUNER_USE_YUBIKEY"] = str(use_yubikey).lower()
            if password:
                os.environ["AI_TUNER_ENCRYPTION_PASSWORD"] = password

            QMessageBox.information(
                self,
                "Settings Saved",
                "Encryption settings saved successfully.",
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to initialize encryption: {e}",
            )

    def _encrypt_existing_files(self) -> None:
        """Encrypt existing files."""
        if not self.encryption_manager:
            QMessageBox.warning(
                self,
                "Encryption Not Initialized",
                "Please save settings first.",
            )
            return

        # Ask for directory
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Encrypt",
            str(Path.cwd()),
        )
        if not directory:
            return

        # Ask for file pattern
        from PySide6.QtWidgets import QInputDialog
        pattern, ok = QInputDialog.getText(
            self,
            "File Pattern",
            "Enter file pattern (e.g., *.json, *.db, *):",
            text="*",
        )
        if not ok:
            return

        # Encrypt files
        encryption = FileEncryption(
            encryption_enabled=True,
            use_yubikey=self.yubikey_radio.isChecked(),
            password=self.password_input.text() if self.password_radio.isChecked() else None,
        )

        count = encryption.encrypt_directory(directory, pattern=pattern)
        QMessageBox.information(
            self,
            "Encryption Complete",
            f"Encrypted {count} files in {directory}",
        )

    def _decrypt_existing_files(self) -> None:
        """Decrypt existing files."""
        if not self.encryption_manager:
            QMessageBox.warning(
                self,
                "Encryption Not Initialized",
                "Please save settings first.",
            )
            return

        # Ask for directory
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Decrypt",
            str(Path.cwd()),
        )
        if not directory:
            return

        # Decrypt files
        encryption = FileEncryption(
            encryption_enabled=True,
            use_yubikey=self.yubikey_radio.isChecked(),
            password=self.password_input.text() if self.password_radio.isChecked() else None,
        )

        count = encryption.decrypt_directory(directory, pattern="*.encrypted")
        QMessageBox.information(
            self,
            "Decryption Complete",
            f"Decrypted {count} files in {directory}",
        )

    def get_encryption_manager(self) -> Optional[EncryptedFileManager]:
        """Get encryption manager instance."""
        return self.encryption_manager


__all__ = ["EncryptionSettingsDialog"]

