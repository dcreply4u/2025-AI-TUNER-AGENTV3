"""
ECU Control Dialog

User interface for ECU control module with full parameter management.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSlider,
        QSpinBox,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSlider,
        QSpinBox,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )

from services.ecu_control import ECUControl, ECUParameter, SafetyLevel


class ParameterEditor(QWidget):
    """Widget for editing a single ECU parameter."""

    def __init__(self, parameter: ECUParameter, ecu_control: ECUControl, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.parameter = parameter
        self.ecu_control = ecu_control

        layout = QVBoxLayout(self)

        # Parameter info
        info_group = QGroupBox(parameter.name)
        info_layout = QVBoxLayout(info_group)

        info_layout.addWidget(QLabel(f"Category: {parameter.category}"))
        info_layout.addWidget(QLabel(f"Description: {parameter.description}"))
        info_layout.addWidget(QLabel(f"Unit: {parameter.unit}"))
        info_layout.addWidget(QLabel(f"Safety Level: {parameter.safety_level.value.upper()}"))

        layout.addWidget(info_group)

        # Value editor
        value_group = QGroupBox("Value")
        value_layout = QVBoxLayout(value_group)

        self.value_input = QSpinBox() if isinstance(parameter.current_value, (int, float)) else QLineEdit()
        if isinstance(parameter.current_value, (int, float)):
            if parameter.min_value is not None:
                self.value_input.setMinimum(int(parameter.min_value))
            if parameter.max_value is not None:
                self.value_input.setMaximum(int(parameter.max_value))
            self.value_input.setValue(int(parameter.current_value))
        else:
            self.value_input.setText(str(parameter.current_value))

        value_layout.addWidget(QLabel("Current Value:"))
        value_layout.addWidget(self.value_input)

        # Safety analysis
        self.safety_label = QLabel()
        self.safety_label.setWordWrap(True)
        value_layout.addWidget(self.safety_label)

        # Update safety analysis when value changes
        if isinstance(self.value_input, QSpinBox):
            self.value_input.valueChanged.connect(self._update_safety_analysis)
        else:
            self.value_input.textChanged.connect(self._update_safety_analysis)

        layout.addWidget(value_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply Change")
        self.apply_btn.clicked.connect(self._apply_change)
        self.preview_btn = QPushButton("Preview Safety")
        self.preview_btn.clicked.connect(self._preview_safety)
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.apply_btn)
        layout.addLayout(button_layout)

        layout.addStretch()

    def _update_safety_analysis(self) -> None:
        """Update safety analysis display."""
        if isinstance(self.value_input, QSpinBox):
            new_value = self.value_input.value()
        else:
            try:
                new_value = float(self.value_input.text())
            except ValueError:
                return

        analysis = self.ecu_control.get_safety_analysis(self.parameter.name, new_value)

        if "error" in analysis:
            self.safety_label.setText(f"Error: {analysis['error']}")
            return

        safety_level = analysis["safety_level"]
        warnings = analysis.get("warnings", [])

        color_map = {
            "safe": "green",
            "caution": "orange",
            "warning": "orange",
            "dangerous": "red",
            "critical": "red",
        }
        color = color_map.get(safety_level, "black")

        text = f'<span style="color: {color}; font-weight: bold;">Safety: {safety_level.upper()}</span>'
        if warnings:
            text += "<br>Warnings:<br>" + "<br>".join(f"• {w}" for w in warnings)

        self.safety_label.setText(text)

    def _preview_safety(self) -> None:
        """Show detailed safety preview."""
        if isinstance(self.value_input, QSpinBox):
            new_value = self.value_input.value()
        else:
            try:
                new_value = float(self.value_input.text())
            except ValueError:
                QMessageBox.warning(self, "Invalid Value", "Please enter a valid number")
                return

        analysis = self.ecu_control.get_safety_analysis(self.parameter.name, new_value)

        if "error" in analysis:
            QMessageBox.warning(self, "Error", analysis["error"])
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Safety Analysis")
        msg.setText(f"Safety Analysis for {self.parameter.name}")

        details = f"Old Value: {analysis['old_value']}\n"
        details += f"New Value: {analysis['new_value']}\n"
        details += f"Safety Level: {analysis['safety_level'].upper()}\n\n"

        if analysis.get("warnings"):
            details += "Warnings:\n"
            for warning in analysis["warnings"]:
                details += f"• {warning}\n"
            details += "\n"

        if analysis.get("recommendations"):
            details += "Recommendations:\n"
            for rec in analysis["recommendations"]:
                details += f"• {rec}\n"

        msg.setDetailedText(details)
        msg.exec()

    def _apply_change(self) -> None:
        """Apply the change."""
        if isinstance(self.value_input, QSpinBox):
            new_value = self.value_input.value()
        else:
            try:
                new_value = float(self.value_input.text())
            except ValueError:
                QMessageBox.warning(self, "Invalid Value", "Please enter a valid number")
                return

        # Confirm if dangerous
        analysis = self.ecu_control.get_safety_analysis(self.parameter.name, new_value)
        if analysis.get("safety_level") in ["dangerous", "critical"]:
            reply = QMessageBox.warning(
                self,
                "Dangerous Change",
                f"This change is {analysis['safety_level'].upper()}.\n\n"
                f"Warnings:\n" + "\n".join(analysis.get("warnings", [])) + "\n\n"
                "Are you sure you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        success, warnings = self.ecu_control.set_parameter(self.parameter.name, new_value)

        if success:
            QMessageBox.information(self, "Success", f"Parameter {self.parameter.name} updated successfully")
            if warnings:
                QMessageBox.warning(self, "Warnings", "\n".join(warnings))
        else:
            QMessageBox.critical(self, "Error", f"Failed to update parameter {self.parameter.name}")


class ECUControlDialog(QDialog):
    """Main ECU control dialog."""

    def __init__(self, ecu_control: ECUControl, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ECU Control Module")
        self.resize(1000, 700)

        self.ecu_control = ecu_control

        layout = QVBoxLayout(self)

        # Connection status
        status_layout = QHBoxLayout()
        self.status_label = QLabel("ECU: Not Connected")
        self.connect_btn = QPushButton("Connect ECU")
        self.connect_btn.clicked.connect(self._connect_ecu)
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self._disconnect_ecu)
        self.disconnect_btn.setEnabled(False)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.connect_btn)
        status_layout.addWidget(self.disconnect_btn)
        layout.addLayout(status_layout)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_parameters_tab(), "Parameters")
        tabs.addTab(self._create_backups_tab(), "Backups")
        tabs.addTab(self._create_history_tab(), "Change History")
        tabs.addTab(self._create_safety_tab(), "Safety Analysis")
        layout.addWidget(tabs)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Update UI
        self._update_ui()

    def _create_parameters_tab(self) -> QWidget:
        """Create parameters tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Parameter list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)

        list_layout.addWidget(QLabel("Parameters:"))
        self.param_list = QTreeWidget()
        self.param_list.setHeaderLabels(["Parameter", "Value", "Safety"])
        self.param_list.itemSelectionChanged.connect(self._on_parameter_selected)
        list_layout.addWidget(self.param_list)

        layout.addWidget(list_widget, 1)

        # Parameter editor
        self.param_editor = QScrollArea()
        self.param_editor.setWidgetResizable(True)
        self.param_editor.setWidget(QWidget())
        layout.addWidget(self.param_editor, 2)

        return widget

    def _create_backups_tab(self) -> QWidget:
        """Create backups tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        button_layout = QHBoxLayout()
        self.backup_btn = QPushButton("Create Backup")
        self.backup_btn.clicked.connect(self._create_backup)
        self.restore_btn = QPushButton("Restore Backup")
        self.restore_btn.clicked.connect(self._restore_backup)
        self.validate_btn = QPushButton("Validate Backup")
        self.validate_btn.clicked.connect(self._validate_backup)
        button_layout.addWidget(self.backup_btn)
        button_layout.addWidget(self.restore_btn)
        button_layout.addWidget(self.validate_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.backup_list = QTableWidget()
        self.backup_list.setColumnCount(5)
        self.backup_list.setHorizontalHeaderLabels(["ID", "Date", "Type", "Validated", "Hash"])
        self.backup_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.backup_list)

        return widget

    def _create_history_tab(self) -> QWidget:
        """Create change history tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        button_layout = QHBoxLayout()
        self.rollback_btn = QPushButton("Rollback Selected")
        self.rollback_btn.clicked.connect(self._rollback_change)
        button_layout.addWidget(self.rollback_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Time", "Parameter", "Old Value", "New Value", "Warnings"])
        layout.addWidget(self.history_table)

        return widget

    def _create_safety_tab(self) -> QWidget:
        """Create safety analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.safety_text = QTextEdit()
        self.safety_text.setReadOnly(True)
        layout.addWidget(self.safety_text)

        return widget

    def _connect_ecu(self) -> None:
        """Connect to ECU."""
        # This would show a connection dialog
        # For now, simulate connection
        success = self.ecu_control.connect_ecu("Holley", {})
        if success:
            self.status_label.setText("ECU: Connected (Holley)")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self._update_ui()

    def _disconnect_ecu(self) -> None:
        """Disconnect from ECU."""
        self.ecu_control.disconnect_ecu()
        self.status_label.setText("ECU: Not Connected")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self._update_ui()

    def _update_ui(self) -> None:
        """Update UI with current data."""
        # Update parameter list
        self.param_list.clear()
        categories = {}
        for name, param in self.ecu_control.current_parameters.items():
            category = param.category
            if category not in categories:
                category_item = QTreeWidgetItem(self.param_list, [category, "", ""])
                categories[category] = category_item

            item = QTreeWidgetItem(categories[category], [name, str(param.current_value), param.safety_level.value])
            item.setData(0, Qt.ItemDataRole.UserRole, name)

        self.param_list.expandAll()

        # Update backup list
        self.backup_list.setRowCount(len(self.ecu_control.backups))
        for row, (backup_id, backup) in enumerate(self.ecu_control.backups.items()):
            from datetime import datetime

            date_str = datetime.fromtimestamp(backup.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            self.backup_list.setItem(row, 0, QTableWidgetItem(backup_id))
            self.backup_list.setItem(row, 1, QTableWidgetItem(date_str))
            self.backup_list.setItem(row, 2, QTableWidgetItem(backup.ecu_type))
            self.backup_list.setItem(row, 3, QTableWidgetItem("Yes" if backup.validated else "No"))
            self.backup_list.setItem(row, 4, QTableWidgetItem(backup.file_hash[:16] + "..."))

        # Update history
        self.history_table.setRowCount(len(self.ecu_control.change_history))
        for row, change in enumerate(self.ecu_control.change_history):
            from datetime import datetime

            date_str = datetime.fromtimestamp(change.timestamp).strftime("%H:%M:%S")
            self.history_table.setItem(row, 0, QTableWidgetItem(date_str))
            self.history_table.setItem(row, 1, QTableWidgetItem(change.parameter_name))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(change.old_value)))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(change.new_value)))
            self.history_table.setItem(row, 4, QTableWidgetItem(str(len(change.safety_warnings)) + " warnings"))

    def _on_parameter_selected(self) -> None:
        """Handle parameter selection."""
        items = self.param_list.selectedItems()
        if not items:
            return

        item = items[0]
        param_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not param_name:
            return

        param = self.ecu_control.current_parameters.get(param_name)
        if param:
            editor = ParameterEditor(param, self.ecu_control)
            self.param_editor.setWidget(editor)

    def _create_backup(self) -> None:
        """Create ECU backup."""
        description, ok = QLineEdit.getText(None, "Backup Description", "Enter backup description:")
        if not ok:
            return

        backup = self.ecu_control.backup_ecu(description)
        QMessageBox.information(self, "Backup Created", f"Backup created: {backup.backup_id}")
        self._update_ui()

    def _restore_backup(self) -> None:
        """Restore from backup."""
        selected = self.backup_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a backup to restore")
            return

        backup_id = self.backup_list.item(selected[0].row(), 0).text()

        reply = QMessageBox.warning(
            self,
            "Confirm Restore",
            f"Restore from backup {backup_id}?\n\nThis will overwrite current ECU settings.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.ecu_control.restore_ecu(backup_id)
            if success:
                QMessageBox.information(self, "Success", "ECU restored successfully")
                self._update_ui()
            else:
                QMessageBox.critical(self, "Error", "Failed to restore ECU")

    def _validate_backup(self) -> None:
        """Validate selected backup."""
        selected = self.backup_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a backup to validate")
            return

        backup_id = self.backup_list.item(selected[0].row(), 0).text()
        backup = self.ecu_control.backups.get(backup_id)

        if backup:
            is_valid, errors = self.ecu_control.validate_ecu_file(backup.file_path)
            if is_valid:
                QMessageBox.information(self, "Valid", "Backup file is valid")
            else:
                QMessageBox.warning(self, "Invalid", "Backup file has errors:\n" + "\n".join(errors))

    def _rollback_change(self) -> None:
        """Rollback selected change."""
        selected = self.history_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a change to rollback")
            return

        row = selected[0].row()
        success = self.ecu_control.rollback_change(row)
        if success:
            QMessageBox.information(self, "Success", "Change rolled back successfully")
            self._update_ui()
        else:
            QMessageBox.critical(self, "Error", "Failed to rollback change")


__all__ = ["ECUControlDialog"]

