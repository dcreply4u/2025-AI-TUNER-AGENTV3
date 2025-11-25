"""
Email Logs Dialog

Simple UI for selecting and emailing recent log files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

from services.email_service import EmailService


class EmailLogsDialog(QDialog):
    """Dialog for selecting and emailing log files."""

    def __init__(
        self,
        log_directories: List[str | Path],
        email_service: Optional[EmailService] = None,
        max_files: int = 10,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Email Log Files")
        self.resize(600, 700)

        self.log_directories = [Path(d) for d in log_directories]
        self.email_service = email_service or EmailService()
        self.max_files = max_files
        self.selected_files: List[Path] = []

        layout = QVBoxLayout(self)

        # Email configuration
        config_group = QGroupBox("Email Configuration")
        config_layout = QFormLayout(config_group)

        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("recipient@example.com")
        config_layout.addRow("To:", self.to_input)

        self.subject_input = QLineEdit()
        self.subject_input.setText("AI Tuner Log Files")
        config_layout.addRow("Subject:", self.subject_input)

        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Optional message...")
        self.body_input.setMaximumHeight(100)
        config_layout.addRow("Message:", self.body_input)

        layout.addWidget(config_group)

        # Recent log files
        files_group = QGroupBox(f"Recent Log Files (Select up to {max_files})")
        files_layout = QVBoxLayout(files_group)

        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        files_layout.addWidget(self.files_list)

        # Load recent files
        self._load_recent_files()

        # File selection buttons
        file_buttons = QVBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        file_buttons.addWidget(select_all_btn)

        clear_selection_btn = QPushButton("Clear Selection")
        clear_selection_btn.clicked.connect(self._clear_selection)
        file_buttons.addWidget(clear_selection_btn)

        add_file_btn = QPushButton("Add Other File...")
        add_file_btn.clicked.connect(self._add_other_file)
        file_buttons.addWidget(add_file_btn)

        files_layout.addLayout(file_buttons)
        layout.addWidget(files_group)

        # Status
        self.status_label = QLabel("Ready to send")
        layout.addWidget(self.status_label)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Send | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Send).setText("Send Email")
        buttons.accepted.connect(self._send_email)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_recent_files(self) -> None:
        """Load recent log files from log directories."""
        all_files: List[tuple[Path, float]] = []

        # Collect all log files
        for log_dir in self.log_directories:
            if not log_dir.exists():
                continue

            # Find all CSV, MP4, JSON, and other log files
            for ext in ["*.csv", "*.mp4", "*.json", "*.log", "*.txt"]:
                for file_path in log_dir.rglob(ext):
                    if file_path.is_file():
                        try:
                            mtime = file_path.stat().st_mtime
                            all_files.append((file_path, mtime))
                        except Exception:
                            continue

        # Sort by modification time (newest first)
        all_files.sort(key=lambda x: x[1], reverse=True)

        # Add to list widget (limit to max_files)
        for file_path, mtime in all_files[: self.max_files]:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            item_text = f"{file_path.name} ({size_mb:.2f} MB) - {file_path.parent.name}"
            self.files_list.addItem(item_text)
            self.files_list.item(self.files_list.count() - 1).setData(Qt.ItemDataRole.UserRole, str(file_path))

    def _select_all(self) -> None:
        """Select all files in the list."""
        for i in range(self.files_list.count()):
            self.files_list.item(i).setSelected(True)

    def _clear_selection(self) -> None:
        """Clear file selection."""
        self.files_list.clearSelection()

    def _add_other_file(self) -> None:
        """Add a file not in the recent list."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Attach",
            "",
            "All Files (*.*);;CSV Files (*.csv);;Video Files (*.mp4);;Log Files (*.log)",
        )
        if file_path:
            # Add to list
            path = Path(file_path)
            size_mb = path.stat().st_size / (1024 * 1024)
            item_text = f"{path.name} ({size_mb:.2f} MB) - [External]"
            self.files_list.addItem(item_text)
            self.files_list.item(self.files_list.count() - 1).setData(Qt.ItemDataRole.UserRole, file_path)
            self.files_list.item(self.files_list.count() - 1).setSelected(True)

    def _get_selected_files(self) -> List[Path]:
        """Get list of selected file paths."""
        selected = []
        for item in self.files_list.selectedItems():
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                path = Path(file_path)
                if path.exists():
                    selected.append(path)
        return selected

    def _send_email(self) -> None:
        """Send email with selected files."""
        # Validate inputs
        to_address = self.to_input.text().strip()
        if not to_address or "@" not in to_address:
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid recipient email address.")
            return

        # Get selected files
        selected_files = self._get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "No Files Selected", "Please select at least one file to attach.")
            return

        # Check total size (warn if > 25MB)
        total_size_mb = sum(f.stat().st_size for f in selected_files) / (1024 * 1024)
        if total_size_mb > 25:
            reply = QMessageBox.warning(
                self,
                "Large Attachments",
                f"Total attachment size is {total_size_mb:.1f} MB. Some email providers may reject large attachments.\n\nContinue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Prepare email
        subject = self.subject_input.text().strip() or "AI Tuner Log Files"
        body = self.body_input.toPlainText().strip()

        # Send email
        self.status_label.setText("Sending email...")
        self.setEnabled(False)

        try:
            success = self.email_service.send_log_files(
                to_address=to_address,
                log_files=selected_files,
                subject=subject,
                body=body if body else None,
            )

            if success:
                QMessageBox.information(
                    self,
                    "Email Sent",
                    f"Successfully sent {len(selected_files)} file(s) to {to_address}.",
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Email Failed",
                    "Failed to send email. Please check your email configuration and try again.",
                )
                self.status_label.setText("Email failed - check configuration")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
        finally:
            self.setEnabled(True)


__all__ = ["EmailLogsDialog"]

