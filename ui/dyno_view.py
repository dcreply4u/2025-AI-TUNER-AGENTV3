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

        # Secondary Y-axis for AFR, Boost, Ignition Timing
        self.secondary_axis = pg.ViewBox()
        self.hp_plot.showAxis('right')
        self.hp_plot.scene().addItem(self.secondary_axis)
        self.hp_plot.getAxis('right').linkToView(self.secondary_axis)
        self.secondary_axis.setXLink(self.hp_plot.vb)
        
        # Update secondary axis when primary axis changes
        def update_views():
            self.secondary_axis.setGeometry(self.hp_plot.vb.sceneBoundingRect())
            self.secondary_axis.linkedViewChanged(self.hp_plot.vb, self.secondary_axis.XAxis)
        
        self.hp_plot.vb.sigResized.connect(update_views)
        update_views()  # Initial update
        
        # Secondary parameter curves
        self.afr_curve = None
        self.boost_curve = None
        self.timing_curve = None
        self.show_afr = False
        self.show_boost = False
        self.show_timing = False

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
        
        # Current curve for secondary parameter updates
        self.current_curve: Optional["DynoCurve"] = None
        
        # Add legend
        self.hp_plot.addLegend(offset=(10, 10))
        self.torque_plot.addLegend(offset=(10, 10))

    def update_curve(self, curve: "DynoCurve", color: str = "#00e0ff") -> None:
        """Update dyno curve display."""
        self.current_curve = curve
        
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
        
        # Apply smoothing to displayed curves if smoothing_level is set
        # (This is additional smoothing for visualization, beyond calculation smoothing)
        smoothing_level = getattr(self, 'display_smoothing_level', None)
        if smoothing_level and smoothing_level > 1 and len(hp_values) > 3:
            try:
                from services.dyno_enhancements import apply_smoothing
                import numpy as np
                hp_values = apply_smoothing(np.array(hp_values), smoothing_level=smoothing_level).tolist()
                if len(torque_values) == len(rpms) and len(torque_values) > 3:
                    torque_values = apply_smoothing(np.array(torque_values), smoothing_level=smoothing_level).tolist()
            except ImportError:
                pass  # Use unsmoothed if enhancements not available
        
        # Extract secondary parameters
        afr_values = [r.afr for r in sorted_readings if r.afr is not None]
        boost_values = [r.boost_psi for r in sorted_readings if r.boost_psi is not None]
        timing_values = [r.ignition_timing for r in sorted_readings if r.ignition_timing is not None]
        
        # Get RPMs for secondary parameters (may have different length)
        afr_rpms = [r.rpm for r in sorted_readings if r.rpm is not None and r.afr is not None]
        boost_rpms = [r.rpm for r in sorted_readings if r.rpm is not None and r.boost_psi is not None]
        timing_rpms = [r.rpm for r in sorted_readings if r.rpm is not None and r.ignition_timing is not None]

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
        
        # Update secondary parameter curves
        self._update_secondary_curves(afr_rpms, afr_values, boost_rpms, boost_values, timing_rpms, timing_values)
    
    def _update_secondary_curves(
        self,
        afr_rpms: List[float],
        afr_values: List[float],
        boost_rpms: List[float],
        boost_values: List[float],
        timing_rpms: List[float],
        timing_values: List[float],
    ) -> None:
        """Update secondary parameter curves (AFR, Boost, Ignition Timing)."""
        # Remove old curves
        if self.afr_curve:
            self.secondary_axis.removeItem(self.afr_curve)
            self.afr_curve = None
        if self.boost_curve:
            self.secondary_axis.removeItem(self.boost_curve)
            self.boost_curve = None
        if self.timing_curve:
            self.secondary_axis.removeItem(self.timing_curve)
            self.timing_curve = None
        
        # Update secondary axis label
        labels = []
        if self.show_afr and afr_rpms and afr_values:
            labels.append("AFR")
        if self.show_boost and boost_rpms and boost_values:
            labels.append("Boost (PSI)")
        if self.show_timing and timing_rpms and timing_values:
            labels.append("Timing (°)")
        
        if labels:
            self.hp_plot.setLabel("right", " / ".join(labels), color="#ffff00")
        else:
            self.hp_plot.setLabel("right", "")
        
        # Collect all visible values for combined Y range
        all_secondary_values = []
        
        # Plot AFR
        if self.show_afr and afr_rpms and afr_values and len(afr_rpms) == len(afr_values):
            self.afr_curve = pg.PlotDataItem(
                afr_rpms,
                afr_values,
                pen=pg.mkPen(color="#00ff00", width=2, style=Qt.DashLine),
                name="AFR",
            )
            self.secondary_axis.addItem(self.afr_curve)
            all_secondary_values.extend(afr_values)
        
        # Plot Boost
        if self.show_boost and boost_rpms and boost_values and len(boost_rpms) == len(boost_values):
            self.boost_curve = pg.PlotDataItem(
                boost_rpms,
                boost_values,
                pen=pg.mkPen(color="#ff00ff", width=2, style=Qt.DashLine),
                name="Boost",
            )
            self.secondary_axis.addItem(self.boost_curve)
            all_secondary_values.extend(boost_values)
        
        # Plot Ignition Timing
        if self.show_timing and timing_rpms and timing_values and len(timing_rpms) == len(timing_values):
            self.timing_curve = pg.PlotDataItem(
                timing_rpms,
                timing_values,
                pen=pg.mkPen(color="#ffaa00", width=2, style=Qt.DashLine),
                name="Timing",
            )
            self.secondary_axis.addItem(self.timing_curve)
            all_secondary_values.extend(timing_values)
        
        # Set combined Y range for all secondary parameters
        if all_secondary_values:
            min_val = min(all_secondary_values)
            max_val = max(all_secondary_values)
            range_val = max_val - min_val
            if range_val > 0:
                self.secondary_axis.setYRange(min_val - range_val * 0.1, max_val + range_val * 0.1)
            else:
                # Fallback if all values are the same
                self.secondary_axis.setYRange(min_val * 0.9, max_val * 1.1)
    
    def set_secondary_parameters_visibility(
        self,
        show_afr: bool = False,
        show_boost: bool = False,
        show_timing: bool = False,
    ) -> None:
        """Set visibility of secondary parameters."""
        self.show_afr = show_afr
        self.show_boost = show_boost
        self.show_timing = show_timing
        # Trigger update to refresh curves
        if hasattr(self, 'current_curve'):
            self.update_curve(self.current_curve)

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
    
    def update_all_curves(self, live_curve: "DynoCurve") -> None:
        """Update all curves including live data and loaded files."""
        if hasattr(self.curve_widget, 'update_all_curves'):
            self.curve_widget.update_all_curves(live_curve)
        else:
            self.update_curve(live_curve)

    def add_comparison(self, curve: "DynoCurve", name: str) -> None:
        """Add comparison curve."""
        self.curve_widget.add_comparison_curve(curve, name)

    def clear_comparisons(self) -> None:
        """Clear comparisons."""
        self.curve_widget.clear_comparisons()
    
    def add_loaded_file_curve(
        self, file_path: str, curve: "DynoCurve", name: str, color: str, visible: bool = True
    ) -> None:
        """Add a loaded dyno file curve."""
        self.curve_widget.add_loaded_file_curve(file_path, curve, name, color, visible)
    
    def set_loaded_file_visibility(self, file_path: str, visible: bool) -> None:
        """Set visibility of a loaded file curve."""
        self.curve_widget.set_loaded_file_visibility(file_path, visible)


__all__ = ["VirtualDynoView", "RealTimeHPMeter", "DynoCurveWidget"]

