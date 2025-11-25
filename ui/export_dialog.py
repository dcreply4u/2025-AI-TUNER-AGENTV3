"""
Export Dialog

UI for exporting data in various formats (CSV, JSON, Excel, GPX, KML, etc.)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
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
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

from services.data_exporter import DataExporter


class ExportDialog(QDialog):
    """Dialog for exporting data in various formats."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export Data")
        self.resize(600, 500)
        self.exported_files: Dict[str, Path] = {}

        layout = QVBoxLayout(self)

        # Data selection
        data_group = QGroupBox("Select Data to Export")
        data_layout = QVBoxLayout(data_group)

        self.telemetry_cb = QCheckBox("Telemetry Data")
        self.telemetry_cb.setChecked(True)
        data_layout.addWidget(self.telemetry_cb)

        self.gps_cb = QCheckBox("GPS Data")
        self.gps_cb.setChecked(True)
        data_layout.addWidget(self.gps_cb)

        self.diagnostics_cb = QCheckBox("Diagnostics")
        self.diagnostics_cb.setChecked(False)
        data_layout.addWidget(self.diagnostics_cb)

        self.video_cb = QCheckBox("Video Files")
        self.video_cb.setChecked(False)
        data_layout.addWidget(self.video_cb)

        layout.addWidget(data_group)

        # Format selection
        format_group = QGroupBox("Export Formats")
        format_layout = QFormLayout(format_group)

        self.telemetry_format = QComboBox()
        self.telemetry_format.addItems(["CSV", "JSON", "Excel", "Parquet"])
        self.telemetry_format.setCurrentText("CSV")
        format_layout.addRow("Telemetry Format:", self.telemetry_format)

        self.gps_format = QComboBox()
        self.gps_format.addItems(["GPX", "KML", "CSV", "JSON"])
        self.gps_format.setCurrentText("GPX")
        format_layout.addRow("GPS Format:", self.gps_format)

        self.diagnostics_format = QComboBox()
        self.diagnostics_format.addItems(["JSON", "CSV", "Excel"])
        self.diagnostics_format.setCurrentText("JSON")
        format_layout.addRow("Diagnostics Format:", self.diagnostics_format)

        layout.addWidget(format_group)

        # Output location
        output_group = QGroupBox("Output Location")
        output_layout = QHBoxLayout(output_group)

        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Select output directory...")
        output_layout.addWidget(self.output_path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(browse_btn)

        layout.addWidget(output_group)

        # Filename prefix
        filename_group = QGroupBox("Filename")
        filename_layout = QFormLayout(filename_group)

        self.filename_prefix = QLineEdit()
        self.filename_prefix.setPlaceholderText("session_20240101_120000 (auto-generated if empty)")
        filename_layout.addRow("Filename Prefix:", self.filename_prefix)

        layout.addWidget(filename_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self.include_metadata_cb = QCheckBox("Include metadata in exports")
        self.include_metadata_cb.setChecked(True)
        options_layout.addWidget(self.include_metadata_cb)

        self.open_folder_cb = QCheckBox("Open export folder when complete")
        self.open_folder_cb.setChecked(True)
        options_layout.addWidget(self.open_folder_cb)

        layout.addWidget(options_group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Export")
        buttons.accepted.connect(self._export_data)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_output(self) -> None:
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Export Directory", str(Path.home()))
        if directory:
            self.output_path_edit.setText(directory)

    def _export_data(self) -> None:
        """Export selected data."""
        # Get output directory
        output_dir = self.output_path_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "Output Required", "Please select an output directory.")
            return

        output_path = Path(output_dir)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot create output directory:\n{str(e)}")
                return

        # Get filename prefix
        filename_prefix = self.filename_prefix.text().strip() or None

        # Initialize exporter
        exporter = DataExporter(output_dir=str(output_path))

        # Get data from parent (main window)
        parent = self.parent()
        exported_files = {}

        try:
            # Export telemetry
            if self.telemetry_cb.isChecked():
                telemetry_data = self._get_telemetry_data()
                if telemetry_data:
                    format = self.telemetry_format.currentText().lower()
                    filename = f"{filename_prefix}_telemetry.{format}" if filename_prefix else None
                    path = exporter.export_telemetry(
                        telemetry_data,
                        format=format,
                        filename=filename,
                        include_metadata=self.include_metadata_cb.isChecked(),
                    )
                    exported_files["telemetry"] = path

            # Export GPS
            if self.gps_cb.isChecked():
                gps_data = self._get_gps_data()
                if gps_data:
                    format = self.gps_format.currentText().lower()
                    filename = f"{filename_prefix}_gps.{format}" if filename_prefix else None
                    path = exporter.export_gps(gps_data, format=format, filename=filename)
                    exported_files["gps"] = path

            # Export diagnostics
            if self.diagnostics_cb.isChecked():
                diagnostics_data = self._get_diagnostics_data()
                if diagnostics_data:
                    format = self.diagnostics_format.currentText().lower()
                    filename = f"{filename_prefix}_diagnostics.{format}" if filename_prefix else None
                    path = exporter.export_diagnostics(diagnostics_data, format=format, filename=filename)
                    exported_files["diagnostics"] = path

            # Copy video files if requested
            if self.video_cb.isChecked():
                video_files = self._get_video_files()
                for video_file in video_files:
                    if video_file.exists():
                        dest = output_path / video_file.name
                        import shutil

                        shutil.copy2(video_file, dest)
                        exported_files[f"video_{video_file.name}"] = dest

            if exported_files:
                self.exported_files = exported_files
                message = f"Exported {len(exported_files)} file(s) to:\n{output_path}"
                QMessageBox.information(self, "Export Complete", message)

                # Open folder if requested
                if self.open_folder_cb.isChecked():
                    import platform

                    if platform.system() == "Windows":
                        import os

                        os.startfile(output_path)
                    elif platform.system() == "Darwin":  # macOS
                        import subprocess

                        subprocess.run(["open", str(output_path)])
                    else:  # Linux
                        import subprocess

                        subprocess.run(["xdg-open", str(output_path)])

                self.accept()
            else:
                QMessageBox.warning(self, "No Data", "No data available to export.")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error during export:\n{str(e)}")

    def _get_telemetry_data(self) -> List[Dict]:
        """Get telemetry data from parent/main window."""
        parent = self.parent()
        if hasattr(parent, "data_logger") and parent.data_logger:
            # Try to read from log file
            log_file = parent.data_logger.file_path
            if log_file.exists():
                import csv

                data = []
                with open(log_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
                return data
        return []

    def _get_gps_data(self) -> List[Dict]:
        """Get GPS data from parent/main window."""
        parent = self.parent()
        gps_data = []

        # Try to get from geo logger
        if hasattr(parent, "geo_logger") and parent.geo_logger:
            # GeoLogger might have stored GPS data
            pass

        # Try to get from performance tracker
        if hasattr(parent, "performance_tracker") and parent.performance_tracker:
            snapshot = parent.performance_tracker.snapshot()
            if snapshot and snapshot.track_points:
                for lat, lon in snapshot.track_points:
                    gps_data.append({"lat": lat, "lon": lon})

        return gps_data

    def _get_diagnostics_data(self) -> Dict:
        """Get diagnostics data from parent/main window."""
        parent = self.parent()
        diagnostics = {}

        # Get health score
        if hasattr(parent, "health_widget") and parent.health_widget:
            diagnostics["health_score"] = getattr(parent.health_widget, "current_score", None)

        # Get fault codes
        if hasattr(parent, "fault_panel") and parent.fault_panel:
            diagnostics["fault_codes"] = getattr(parent.fault_panel, "current_codes", [])

        return diagnostics

    def _get_video_files(self) -> List[Path]:
        """Get video file paths from parent/main window."""
        parent = self.parent()
        video_files = []

        # Try to get from camera manager
        if hasattr(parent, "camera_manager") and parent.camera_manager:
            if hasattr(parent.camera_manager, "video_logger"):
                video_dir = parent.camera_manager.video_logger.output_dir
                if video_dir.exists():
                    video_files.extend(video_dir.glob("*.mp4"))
                    video_files.extend(video_dir.glob("*.avi"))

        return video_files

    def get_exported_files(self) -> Dict[str, Path]:
        """Get dictionary of exported files."""
        return self.exported_files


__all__ = ["ExportDialog"]

