"""
Virtual Dyno View - Real-time HP/Torque Display and Dyno Curves

Beautiful UI for displaying:
- Real-time horsepower and torque
- Live dyno curve plotting
- Before/after comparisons
- Power band analysis
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict

import pyqtgraph as pg
from PySide6.QtCore import Qt  # type: ignore
from PySide6.QtGui import QColor, QFont  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from services.virtual_dyno import DynoCurve, DynoReading

pg.setConfigOptions(antialias=True, background="black", foreground="white")


class RealTimeHPMeter(QFrame):
    """Real-time horsepower display meter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        self.title_label = QLabel("HORSEPOWER")
        self.title_label.setStyleSheet("font-size: 12px; color: #9aa0a6; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.hp_label = QLabel("--")
        self.hp_label.setStyleSheet(
            "font-size: 48px; font-weight: bold; color: #00e0ff;"
        )
        self.hp_label.setAlignment(Qt.AlignCenter)

        self.rpm_label = QLabel("RPM: --")
        self.rpm_label.setStyleSheet("font-size: 14px; color: #5f6368;")
        self.rpm_label.setAlignment(Qt.AlignCenter)

        self.torque_label = QLabel("Torque: -- ft-lb")
        self.torque_label.setStyleSheet("font-size: 14px; color: #5f6368;")
        self.torque_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.title_label)
        layout.addWidget(self.hp_label)
        layout.addWidget(self.rpm_label)
        layout.addWidget(self.torque_label)

    def update_reading(self, reading: "DynoReading") -> None:
        """Update with latest dyno reading."""
        self.hp_label.setText(f"{reading.horsepower_crank:.0f}")
        if reading.rpm:
            self.rpm_label.setText(f"RPM: {reading.rpm:.0f}")
        if reading.torque_ftlb:
            self.torque_label.setText(f"Torque: {reading.torque_ftlb:.0f} ft-lb")


class DynoCurveWidget(QWidget):
    """Widget for displaying dyno curves (HP and torque vs RPM)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Dyno Curve")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: white; padding: 8px;")
        layout.addWidget(title)

        # Graph widget
        self.graph = pg.GraphicsLayoutWidget()
        self.graph.setBackground("black")
        layout.addWidget(self.graph)

        # HP plot
        self.hp_plot = self.graph.addPlot(row=0, col=0)
        self.hp_plot.setLabel("left", "Horsepower", color="#00e0ff")
        self.hp_plot.setLabel("bottom", "RPM")
        self.hp_plot.showGrid(x=True, y=True, alpha=0.3)
        self.hp_plot.setXRange(0, 8000)
        self.hp_plot.setYRange(0, 1000)

        # HP curve
        self.hp_curve = self.hp_plot.plot(
            pen=pg.mkPen(color="#00e0ff", width=3),
            name="HP",
        )

        # Torque plot (right axis)
        self.torque_plot = self.graph.addPlot(row=1, col=0)
        self.torque_plot.setLabel("left", "Torque (ft-lb)", color="#ff6b6b")
        self.torque_plot.setLabel("bottom", "RPM")
        self.torque_plot.showGrid(x=True, y=True, alpha=0.3)
        self.torque_plot.setXRange(0, 8000)
        self.torque_plot.setYRange(0, 1000)

        # Torque curve
        self.torque_curve = self.torque_plot.plot(
            pen=pg.mkPen(color="#ff6b6b", width=3),
            name="Torque",
        )

        # Peak markers
        self.hp_peak_marker = None
        self.torque_peak_marker = None

        # Comparison curves (for before/after)
        self.comparison_hp_curves: list = []
        self.comparison_torque_curves: list = []
        
        # Multiple loaded files tracking
        self.loaded_file_curves: Dict[str, Dict] = {}  # key: file_path, value: {hp_curve, torque_curve, name, color}
        
        # Add legend
        self.hp_plot.addLegend(offset=(10, 10))
        self.torque_plot.addLegend(offset=(10, 10))

    def update_curve(self, curve: "DynoCurve", color: str = "#00e0ff") -> None:
        """Update dyno curve display."""
        if not curve.readings:
            return

        # Filter readings with RPM
        readings_with_rpm = [
            r for r in curve.readings if r.rpm is not None and r.rpm > 0
        ]
        if not readings_with_rpm:
            return

        # Sort by RPM
        sorted_readings = sorted(readings_with_rpm, key=lambda x: x.rpm or 0)

        # Extract data
        rpms = [r.rpm for r in sorted_readings if r.rpm]
        hp_values = [r.horsepower_crank for r in sorted_readings]
        torque_values = [
            r.torque_ftlb for r in sorted_readings if r.torque_ftlb is not None
        ]

        # Update HP curve
        if rpms and hp_values:
            self.hp_curve.setData(rpms, hp_values)

            # Update Y range
            if hp_values:
                max_hp = max(hp_values)
                self.hp_plot.setYRange(0, max_hp * 1.1)

            # Mark peak HP
            if curve.peak_hp_rpm > 0:
                peak_hp_idx = min(
                    range(len(rpms)),
                    key=lambda i: abs(rpms[i] - curve.peak_hp_rpm),
                )
                peak_hp_value = hp_values[peak_hp_idx]

                # Remove old marker
                if self.hp_peak_marker:
                    self.hp_plot.removeItem(self.hp_peak_marker)

                # Add peak marker
                self.hp_peak_marker = pg.InfiniteLine(
                    pos=curve.peak_hp_rpm,
                    angle=90,
                    pen=pg.mkPen(color="#00e0ff", width=2, style=Qt.DashLine),
                )
                self.hp_plot.addItem(self.hp_peak_marker)

        # Update torque curve
        if rpms and torque_values and len(torque_values) == len(rpms):
            self.torque_curve.setData(rpms, torque_values)

            # Update Y range
            if torque_values:
                max_torque = max(torque_values)
                self.torque_plot.setYRange(0, max_torque * 1.1)

            # Mark peak torque
            if curve.peak_torque_rpm > 0:
                peak_torque_idx = min(
                    range(len(rpms)),
                    key=lambda i: abs(rpms[i] - curve.peak_torque_rpm),
                )
                peak_torque_value = torque_values[peak_torque_idx]

                # Remove old marker
                if self.torque_peak_marker:
                    self.torque_plot.removeItem(self.torque_peak_marker)

                # Add peak marker
                self.torque_peak_marker = pg.InfiniteLine(
                    pos=curve.peak_torque_rpm,
                    angle=90,
                    pen=pg.mkPen(color="#ff6b6b", width=2, style=Qt.DashLine),
                )
                self.torque_plot.addItem(self.torque_peak_marker)

    def add_comparison_curve(
        self, curve: "DynoCurve", name: str, color: str = "#ffff00"
    ) -> None:
        """Add a comparison curve (e.g., before/after mods)."""
        if not curve.readings:
            return

        readings_with_rpm = [
            r for r in curve.readings if r.rpm is not None and r.rpm > 0
        ]
        if not readings_with_rpm:
            return

        sorted_readings = sorted(readings_with_rpm, key=lambda x: x.rpm or 0)
        rpms = [r.rpm for r in sorted_readings if r.rpm]
        hp_values = [r.horsepower_crank for r in sorted_readings]
        torque_values = [
            r.torque_ftlb for r in sorted_readings if r.torque_ftlb is not None
        ]

        # Add HP comparison curve
        if rpms and hp_values:
            hp_curve = self.hp_plot.plot(
                rpms,
                hp_values,
                pen=pg.mkPen(color=color, width=2, style=Qt.DashLine),
                name=name,
            )
            self.comparison_hp_curves.append(hp_curve)

        # Add torque comparison curve
        if rpms and torque_values and len(torque_values) == len(rpms):
            torque_curve = self.torque_plot.plot(
                rpms,
                torque_values,
                pen=pg.mkPen(color=color, width=2, style=Qt.DashLine),
                name=name,
            )
            self.comparison_torque_curves.append(torque_curve)

    def add_loaded_file_curve(
        self, file_path: str, curve: "DynoCurve", name: str, color: str, visible: bool = True
    ) -> None:
        """
        Add a loaded dyno file curve to the graph.
        
        Args:
            file_path: Unique identifier for the file
            curve: DynoCurve to display
            name: Display name
            color: Color for the curve
            visible: Whether curve is visible
        """
        if not curve.readings:
            return

        readings_with_rpm = [
            r for r in curve.readings if r.rpm is not None and r.rpm > 0
        ]
        if not readings_with_rpm:
            return

        sorted_readings = sorted(readings_with_rpm, key=lambda x: x.rpm or 0)
        rpms = [r.rpm for r in sorted_readings if r.rpm]
        hp_values = [r.horsepower_crank for r in sorted_readings]
        torque_values = [
            r.torque_ftlb for r in sorted_readings if r.torque_ftlb is not None
        ]

        # Remove existing curves for this file if present
        if file_path in self.loaded_file_curves:
            self.remove_loaded_file_curve(file_path)

        # Add HP curve
        hp_curve = None
        if rpms and hp_values:
            hp_curve = self.hp_plot.plot(
                rpms,
                hp_values,
                pen=pg.mkPen(color=color, width=2, style=Qt.DashLine),
                name=name,
            )
            if not visible:
                hp_curve.hide()

        # Add torque curve
        torque_curve = None
        if rpms and torque_values and len(torque_values) == len(rpms):
            torque_curve = self.torque_plot.plot(
                rpms,
                torque_values,
                pen=pg.mkPen(color=color, width=2, style=Qt.DashLine),
                name=name,
            )
            if not visible:
                torque_curve.hide()

        # Store curve references
        self.loaded_file_curves[file_path] = {
            'hp_curve': hp_curve,
            'torque_curve': torque_curve,
            'name': name,
            'color': color,
            'visible': visible,
        }

    def remove_loaded_file_curve(self, file_path: str) -> None:
        """Remove a loaded file curve from the graph."""
        if file_path in self.loaded_file_curves:
            curve_data = self.loaded_file_curves[file_path]
            if curve_data['hp_curve']:
                self.hp_plot.removeItem(curve_data['hp_curve'])
            if curve_data['torque_curve']:
                self.torque_plot.removeItem(curve_data['torque_curve'])
            del self.loaded_file_curves[file_path]

    def set_loaded_file_visibility(self, file_path: str, visible: bool) -> None:
        """Set visibility of a loaded file curve."""
        if file_path in self.loaded_file_curves:
            curve_data = self.loaded_file_curves[file_path]
            curve_data['visible'] = visible
            if curve_data['hp_curve']:
                if visible:
                    curve_data['hp_curve'].show()
                else:
                    curve_data['hp_curve'].hide()
            if curve_data['torque_curve']:
                if visible:
                    curve_data['torque_curve'].show()
                else:
                    curve_data['torque_curve'].hide()

    def clear_loaded_files(self) -> None:
        """Clear all loaded file curves."""
        file_paths = list(self.loaded_file_curves.keys())
        for file_path in file_paths:
            self.remove_loaded_file_curve(file_path)

    def clear_comparisons(self) -> None:
        """Clear all comparison curves."""
        for curve in self.comparison_hp_curves:
            self.hp_plot.removeItem(curve)
        for curve in self.comparison_torque_curves:
            self.torque_plot.removeItem(curve)
        self.comparison_hp_curves.clear()
        self.comparison_torque_curves.clear()
        
    def update_all_curves(self, live_curve: "DynoCurve") -> None:
        """
        Update all curves including live data and loaded files.
        Updates Y-axis ranges to accommodate all visible curves.
        """
        # Update live curve
        self.update_curve(live_curve)
        
        # Update Y ranges to accommodate all curves
        all_hp_values = []
        all_torque_values = []
        all_rpms = []
        
        # Collect from live curve
        if live_curve.readings:
            readings_with_rpm = [r for r in live_curve.readings if r.rpm is not None and r.rpm > 0]
            if readings_with_rpm:
                all_hp_values.extend([r.horsepower_crank for r in readings_with_rpm])
                all_torque_values.extend([r.torque_ftlb for r in readings_with_rpm if r.torque_ftlb])
                all_rpms.extend([r.rpm for r in readings_with_rpm if r.rpm])
        
        # Collect from loaded files
        for curve_data in self.loaded_file_curves.values():
            if curve_data['visible'] and curve_data['hp_curve']:
                # Get data from curve (pyqtgraph stores data)
                if hasattr(curve_data['hp_curve'], 'xData') and hasattr(curve_data['hp_curve'], 'yData'):
                    hp_data = curve_data['hp_curve'].yData
                    rpm_data = curve_data['hp_curve'].xData
                    if hp_data is not None and rpm_data is not None:
                        all_hp_values.extend(hp_data)
                        all_rpms.extend(rpm_data)
                if curve_data['torque_curve'] and hasattr(curve_data['torque_curve'], 'yData'):
                    torque_data = curve_data['torque_curve'].yData
                    if torque_data is not None:
                        all_torque_values.extend(torque_data)
        
        # Update Y ranges
        if all_hp_values:
            max_hp = max(all_hp_values)
            self.hp_plot.setYRange(0, max_hp * 1.15)
        if all_torque_values:
            max_torque = max(all_torque_values)
            self.torque_plot.setYRange(0, max_torque * 1.15)
        if all_rpms:
            max_rpm = max(all_rpms)
            self.hp_plot.setXRange(0, max_rpm * 1.05)
            self.torque_plot.setXRange(0, max_rpm * 1.05)


class VirtualDynoView(QWidget):
    """Main virtual dyno view widget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header
        header = QHBoxLayout()
        title = QLabel("Virtual Dyno")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        header.addWidget(title)

        # Buttons
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet(
            "QPushButton { padding: 6px 12px; background: #2d2d2d; color: white; border: 1px solid #555; }"
            "QPushButton:hover { background: #3d3d3d; }"
        )
        self.export_btn = QPushButton("Export")
        self.export_btn.setStyleSheet(
            "QPushButton { padding: 6px 12px; background: #2d2d2d; color: white; border: 1px solid #555; }"
            "QPushButton:hover { background: #3d3d3d; }"
        )
        header.addStretch()
        header.addWidget(self.reset_btn)
        header.addWidget(self.export_btn)
        layout.addLayout(header)

        # Real-time HP meter
        self.hp_meter = RealTimeHPMeter()
        layout.addWidget(self.hp_meter)

        # Dyno curve widget
        self.curve_widget = DynoCurveWidget()
        layout.addWidget(self.curve_widget)

        # Stats
        stats_layout = QGridLayout()
        self.peak_hp_label = QLabel("Peak HP: --")
        self.peak_hp_label.setStyleSheet("font-size: 12px; color: #9aa0a6;")
        self.peak_torque_label = QLabel("Peak Torque: --")
        self.peak_torque_label.setStyleSheet("font-size: 12px; color: #9aa0a6;")
        self.accuracy_label = QLabel("Accuracy: --")
        self.accuracy_label.setStyleSheet("font-size: 12px; color: #9aa0a6;")

        stats_layout.addWidget(self.peak_hp_label, 0, 0)
        stats_layout.addWidget(self.peak_torque_label, 0, 1)
        stats_layout.addWidget(self.accuracy_label, 0, 2)
        layout.addLayout(stats_layout)

    def update_reading(self, reading: "DynoReading") -> None:
        """Update with latest dyno reading."""
        self.hp_meter.update_reading(reading)

    def update_curve(self, curve: "DynoCurve") -> None:
        """Update dyno curve."""
        self.curve_widget.update_curve(curve)
        self.peak_hp_label.setText(
            f"Peak HP: {curve.peak_hp_crank:.1f} @ {curve.peak_hp_rpm:.0f} RPM"
        )
        self.peak_torque_label.setText(
            f"Peak Torque: {curve.peak_torque_ftlb:.1f} @ {curve.peak_torque_rpm:.0f} RPM"
        )
        self.accuracy_label.setText(
            f"Accuracy: {curve.accuracy_estimate * 100:.0f}%"
        )

    def add_comparison(self, curve: "DynoCurve", name: str) -> None:
        """Add comparison curve."""
        self.curve_widget.add_comparison_curve(curve, name)

    def clear_comparisons(self) -> None:
        """Clear comparisons."""
        self.curve_widget.clear_comparisons()


__all__ = ["VirtualDynoView", "RealTimeHPMeter", "DynoCurveWidget"]

