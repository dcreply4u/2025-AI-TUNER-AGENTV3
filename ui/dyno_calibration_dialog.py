"""
Dyno Calibration Dialog - Manual Entry of Dyno Data

Allows users to manually enter dyno information if they don't have a file.
Prompts for key values interactively.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from services.dyno_calibration import DynoCalibration
from services.virtual_dyno import DynoCurve, DynoReading


class ManualDynoEntryWidget(QWidget):
    """Widget for manually entering dyno data."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Enter your dyno results manually. You can enter just peak values\n"
            "or multiple RPM points for better accuracy."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #9aa0a6; padding: 8px;")
        layout.addWidget(instructions)

        # Peak values group
        peak_group = QGroupBox("Peak Values (Required)")
        peak_layout = QFormLayout(peak_group)

        self.peak_hp_spin = QSpinBox()
        self.peak_hp_spin.setRange(0, 5000)
        self.peak_hp_spin.setSuffix(" HP")
        self.peak_hp_spin.setValue(0)
        peak_layout.addRow("Peak Horsepower:", self.peak_hp_spin)

        self.peak_hp_rpm_spin = QSpinBox()
        self.peak_hp_rpm_spin.setRange(0, 10000)
        self.peak_hp_rpm_spin.setSuffix(" RPM")
        self.peak_hp_rpm_spin.setValue(0)
        peak_layout.addRow("Peak HP RPM:", self.peak_hp_rpm_spin)

        self.peak_torque_spin = QSpinBox()
        self.peak_torque_spin.setRange(0, 2000)
        self.peak_torque_spin.setSuffix(" ft-lb")
        self.peak_torque_spin.setValue(0)
        peak_layout.addRow("Peak Torque:", self.peak_torque_spin)

        self.peak_torque_rpm_spin = QSpinBox()
        self.peak_torque_rpm_spin.setRange(0, 10000)
        self.peak_torque_rpm_spin.setSuffix(" RPM")
        self.peak_torque_rpm_spin.setValue(0)
        peak_layout.addRow("Peak Torque RPM:", self.peak_torque_rpm_spin)

        layout.addWidget(peak_group)

        # Additional RPM points (optional)
        rpm_group = QGroupBox("Additional RPM Points (Optional - More Accurate)")
        rpm_layout = QVBoxLayout(rpm_group)

        rpm_instructions = QLabel(
            "Enter HP and Torque at specific RPMs for better calibration.\n"
            "Leave blank if you don't have this data."
        )
        rpm_instructions.setWordWrap(True)
        rpm_instructions.setStyleSheet("color: #9aa0a6; font-size: 11px; padding: 4px;")
        rpm_layout.addWidget(rpm_instructions)

        # Common RPM points
        self.rpm_points: list[tuple[QSpinBox, QSpinBox, QSpinBox]] = []
        rpm_form = QFormLayout()

        for rpm in [2000, 3000, 4000, 5000, 6000, 7000]:
            rpm_label = QLabel(f"{rpm} RPM:")
            rpm_label.setStyleSheet("font-weight: bold;")

            hp_spin = QSpinBox()
            hp_spin.setRange(0, 5000)
            hp_spin.setSuffix(" HP")
            hp_spin.setValue(0)

            torque_spin = QSpinBox()
            torque_spin.setRange(0, 2000)
            torque_spin.setSuffix(" ft-lb")
            torque_spin.setValue(0)

            rpm_form.addRow(rpm_label, hp_spin)
            rpm_form.addRow("", torque_spin)  # Indent torque

            self.rpm_points.append((hp_spin, torque_spin, None))  # Store (HP, Torque, RPM value)

        rpm_layout.addLayout(rpm_form)
        layout.addWidget(rpm_group)

        layout.addStretch()

    def get_dyno_curve(self) -> Optional[DynoCurve]:
        """Get dyno curve from entered data."""
        peak_hp = self.peak_hp_spin.value()
        peak_hp_rpm = self.peak_hp_rpm_spin.value()
        peak_torque = self.peak_torque_spin.value()
        peak_torque_rpm = self.peak_torque_rpm_spin.value()

        if peak_hp == 0 or peak_hp_rpm == 0:
            return None

        readings: list[DynoReading] = []

        # Add peak HP reading
        readings.append(
            DynoReading(
                timestamp=0.0,
                rpm=peak_hp_rpm,
                speed_mph=0.0,
                speed_mps=0.0,
                acceleration_mps2=0.0,
                horsepower_wheel=peak_hp,
                horsepower_crank=peak_hp,
                torque_ftlb=None,
                method=None,
                confidence=1.0,
            )
        )

        # Add peak torque reading if provided
        if peak_torque > 0 and peak_torque_rpm > 0:
            readings.append(
                DynoReading(
                    timestamp=0.0,
                    rpm=peak_torque_rpm,
                    speed_mph=0.0,
                    speed_mps=0.0,
                    acceleration_mps2=0.0,
                    horsepower_wheel=0.0,  # Will calculate from torque
                    horsepower_crank=(peak_torque * peak_torque_rpm) / 5252.0,
                    torque_ftlb=peak_torque,
                    method=None,
                    confidence=1.0,
                )
            )

        # Add additional RPM points
        for i, (hp_spin, torque_spin, _) in enumerate(self.rpm_points):
            rpm = [2000, 3000, 4000, 5000, 6000, 7000][i]
            hp = hp_spin.value()
            torque = torque_spin.value()

            if hp > 0 or torque > 0:
                # Calculate missing value if one is provided
                if hp > 0 and torque == 0:
                    torque = (hp * 5252.0) / rpm if rpm > 0 else 0.0
                elif torque > 0 and hp == 0:
                    hp = (torque * rpm) / 5252.0 if rpm > 0 else 0.0

                readings.append(
                    DynoReading(
                        timestamp=0.0,
                        rpm=rpm,
                        speed_mph=0.0,
                        speed_mps=0.0,
                        acceleration_mps2=0.0,
                        horsepower_wheel=hp,
                        horsepower_crank=hp,
                        torque_ftlb=torque if torque > 0 else None,
                        method=None,
                        confidence=0.9,  # Slightly lower confidence for manual entry
                    )
                )

        if not readings:
            return None

        curve = DynoCurve(
            readings=readings,
            peak_hp_wheel=peak_hp,
            peak_hp_crank=peak_hp,
            peak_hp_rpm=peak_hp_rpm,
            peak_torque_ftlb=peak_torque if peak_torque > 0 else 0.0,
            peak_torque_rpm=peak_torque_rpm if peak_torque_rpm > 0 else 0.0,
            accuracy_estimate=0.95,  # High accuracy for manual entry
            calibration_factor=1.0,
        )

        return curve


class DynoCalibrationDialog(QDialog):
    """
    Dialog for calibrating virtual dyno with real dyno data.
    
    Supports:
    - Importing CSV/JSON files
    - Manual entry of dyno values
    - Interactive prompts for missing data
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Calibrate Virtual Dyno")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self.calibration = DynoCalibration()
        self.result_curve: Optional[DynoCurve] = None

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Calibrate Virtual Dyno with Real Dyno Data")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Import a dyno file or manually enter your dyno results.\n"
            "This will calibrate the virtual dyno for maximum accuracy (±3-5%)."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #9aa0a6; padding: 8px;")
        layout.addWidget(instructions)

        # Tabs for import vs manual
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Import tab
        import_widget = QWidget()
        import_layout = QVBoxLayout(import_widget)

        import_instructions = QLabel(
            "Import a dyno file (CSV or JSON).\n"
            "Common formats: Mustang Dyno, Dynojet, etc."
        )
        import_instructions.setWordWrap(True)
        import_instructions.setStyleSheet("color: #9aa0a6; padding: 8px;")
        import_layout.addWidget(import_instructions)

        # Import buttons
        import_buttons = QHBoxLayout()
        self.import_csv_btn = QPushButton("Import CSV File")
        self.import_csv_btn.setStyleSheet(
            "QPushButton { padding: 8px 16px; background: #2d2d2d; color: white; }"
            "QPushButton:hover { background: #3d3d3d; }"
        )
        self.import_csv_btn.clicked.connect(self._import_csv)

        self.import_json_btn = QPushButton("Import JSON File")
        self.import_json_btn.setStyleSheet(
            "QPushButton { padding: 8px 16px; background: #2d2d2d; color: white; }"
            "QPushButton:hover { background: #3d3d3d; }"
        )
        self.import_json_btn.clicked.connect(self._import_json)

        import_buttons.addWidget(self.import_csv_btn)
        import_buttons.addWidget(self.import_json_btn)
        import_buttons.addStretch()
        import_layout.addLayout(import_buttons)

        # File info display
        self.file_info_label = QLabel("No file imported")
        self.file_info_label.setStyleSheet("color: #5f6368; padding: 8px;")
        import_layout.addWidget(self.file_info_label)

        import_layout.addStretch()
        tabs.addTab(import_widget, "Import File")

        # Manual entry tab
        self.manual_widget = ManualDynoEntryWidget()
        tabs.addTab(self.manual_widget, "Manual Entry")

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _import_csv(self) -> None:
        """Import CSV dyno file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Dyno CSV",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )

        if not file_path:
            return

        try:
            curve = self.calibration.import_dyno_csv(file_path)
            self.result_curve = curve
            self.file_info_label.setText(
                f"✓ Imported: {len(curve.readings)} readings\n"
                f"Peak HP: {curve.peak_hp_crank:.1f} @ {curve.peak_hp_rpm:.0f} RPM"
            )
            self.file_info_label.setStyleSheet("color: #00e0ff; padding: 8px;")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Import Error",
                f"Failed to import CSV file:\n{str(e)}\n\n"
                "Please check the file format or use Manual Entry instead.",
            )

    def _import_json(self) -> None:
        """Import JSON dyno file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Dyno JSON",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if not file_path:
            return

        try:
            curve = self.calibration.import_dyno_json(file_path)
            self.result_curve = curve
            self.file_info_label.setText(
                f"✓ Imported: {len(curve.readings)} readings\n"
                f"Peak HP: {curve.peak_hp_crank:.1f} @ {curve.peak_hp_rpm:.0f} RPM"
            )
            self.file_info_label.setStyleSheet("color: #00e0ff; padding: 8px;")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Import Error",
                f"Failed to import JSON file:\n{str(e)}\n\n"
                "Please check the file format or use Manual Entry instead.",
            )

    def _accept(self) -> None:
        """Accept dialog and get dyno curve."""
        # Check if manual entry was used
        if not self.result_curve:
            # Try to get from manual entry
            self.result_curve = self.manual_widget.get_dyno_curve()

        if not self.result_curve:
            QMessageBox.warning(
                self,
                "Missing Data",
                "Please either import a dyno file or enter at least Peak HP and Peak HP RPM.",
            )
            return

        # Validate
        if self.result_curve.peak_hp_crank == 0:
            QMessageBox.warning(
                self,
                "Invalid Data",
                "Peak horsepower must be greater than 0.",
            )
            return

        self.accept()

    def get_dyno_curve(self) -> Optional[DynoCurve]:
        """Get the dyno curve from dialog."""
        return self.result_curve


__all__ = ["DynoCalibrationDialog", "ManualDynoEntryWidget"]

