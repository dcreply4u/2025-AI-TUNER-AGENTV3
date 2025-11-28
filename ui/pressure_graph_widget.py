"""
Pressure Graph Widget - Display cylinder pressure vs. crank angle

Professional-grade visualization for cylinder pressure analysis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

import pyqtgraph as pg
import numpy as np
from PySide6.QtCore import Qt  # type: ignore
from PySide6.QtGui import QColor  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from services.cylinder_pressure_analyzer import PressureCycle, PressureReading

pg.setConfigOptions(antialias=True, background="black", foreground="white")

# Color palette for cylinders
CYLINDER_COLORS = [
    "#00e0ff",  # Cyan
    "#ff6b6b",  # Red
    "#4ecdc4",  # Teal
    "#ffe66d",  # Yellow
    "#95e1d3",  # Mint
    "#f38181",  # Coral
    "#aa96da",  # Purple
    "#fcbad3",  # Pink
]


class PressureGraphWidget(QWidget):
    """
    Widget for displaying cylinder pressure vs. crank angle.
    
    Features:
    - Multi-cylinder overlay
    - Multi-run comparison
    - AFR/Timing overlays on secondary axis
    - Smoothed and raw data views
    - Zoom and pan
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title
        title = QLabel("Cylinder Pressure Analysis")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: white; padding: 8px;")
        layout.addWidget(title)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Cylinder selection
        controls_layout.addWidget(QLabel("Cylinders:"))
        self.cylinder_checkboxes: Dict[int, QCheckBox] = {}
        for i in range(1, 9):  # Support up to 8 cylinders
            checkbox = QCheckBox(f"#{i}")
            checkbox.setChecked(True)
            checkbox.setStyleSheet("color: white;")
            self.cylinder_checkboxes[i] = checkbox
            controls_layout.addWidget(checkbox)
        
        controls_layout.addStretch()
        
        # View options
        controls_layout.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Full Cycle (720°)", "Compression/Power (0-180°)", "Zoom to Combustion"])
        self.view_combo.setStyleSheet("color: white; background: #2b2b2b;")
        controls_layout.addWidget(self.view_combo)
        
        # Smoothing
        controls_layout.addWidget(QLabel("Smoothing:"))
        self.smoothing_combo = QComboBox()
        self.smoothing_combo.addItems(["Raw", "Light", "Medium", "Heavy"])
        self.smoothing_combo.setCurrentText("Medium")
        self.smoothing_combo.setStyleSheet("color: white; background: #2b2b2b;")
        controls_layout.addWidget(self.smoothing_combo)
        
        # Show overlays
        self.show_afr_checkbox = QCheckBox("AFR")
        self.show_afr_checkbox.setStyleSheet("color: white;")
        controls_layout.addWidget(self.show_afr_checkbox)
        
        self.show_timing_checkbox = QCheckBox("Timing")
        self.show_timing_checkbox.setStyleSheet("color: white;")
        controls_layout.addWidget(self.show_timing_checkbox)
        
        layout.addLayout(controls_layout)
        
        # Graph widget
        self.graph = pg.GraphicsLayoutWidget()
        self.graph.setBackground("black")
        layout.addWidget(self.graph)
        
        # Main pressure plot
        self.pressure_plot = self.graph.addPlot(row=0, col=0)
        self.pressure_plot.setLabel("left", "Pressure (PSI)", color="white")
        self.pressure_plot.setLabel("bottom", "Crank Angle (degrees)")
        self.pressure_plot.showGrid(x=True, y=True, alpha=0.3)
        self.pressure_plot.setXRange(0, 720)
        self.pressure_plot.setYRange(0, 2000)
        
        # Secondary Y-axis for AFR/Timing
        self.secondary_axis = pg.ViewBox()
        self.pressure_plot.showAxis('right')
        self.pressure_plot.scene().addItem(self.secondary_axis)
        self.pressure_plot.getAxis('right').linkToView(self.secondary_axis)
        self.secondary_axis.setXLink(self.pressure_plot.vb)
        
        def update_views():
            self.secondary_axis.setGeometry(self.pressure_plot.vb.sceneBoundingRect())
            self.secondary_axis.linkedViewChanged(self.pressure_plot.vb, self.secondary_axis.XAxis)
        
        self.pressure_plot.vb.sigResized.connect(update_views)
        update_views()
        
        # Pressure curves for each cylinder
        self.pressure_curves: Dict[int, pg.PlotDataItem] = {}
        for i in range(1, 9):
            color = CYLINDER_COLORS[(i - 1) % len(CYLINDER_COLORS)]
            curve = self.pressure_plot.plot(
                pen=pg.mkPen(color=color, width=2),
                name=f"Cylinder {i}",
            )
            self.pressure_curves[i] = curve
        
        # Comparison curves (for before/after)
        self.comparison_curves: List[pg.PlotDataItem] = []
        
        # Secondary parameter curves
        self.afr_curve: Optional[pg.PlotDataItem] = None
        self.timing_curve: Optional[pg.PlotDataItem] = None
        
        # TDC/BDC markers
        self.tdc_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color="yellow", width=1, style=Qt.DashLine),
            label="TDC",
        )
        self.pressure_plot.addItem(self.tdc_line)
        
        self.bdc_line = pg.InfiniteLine(
            pos=180,
            angle=90,
            pen=pg.mkPen(color="orange", width=1, style=Qt.DashLine),
            label="BDC",
        )
        self.pressure_plot.addItem(self.bdc_line)
        
        # Connect signals
        self.view_combo.currentTextChanged.connect(self._on_view_changed)
        self.smoothing_combo.currentTextChanged.connect(self._update_display)
        
    def update_cycle(self, cycle: "PressureCycle", cylinder: int) -> None:
        """
        Update pressure curve for a cylinder.
        
        Args:
            cycle: Pressure cycle to display
            cylinder: Cylinder number
        """
        if cylinder not in self.pressure_curves:
            return
        
        # Get data
        angles = cycle.get_crank_angle_array()
        pressures = cycle.get_pressure_array()
        
        # Apply smoothing if needed
        smoothing = self.smoothing_combo.currentText()
        if smoothing != "Raw":
            if smoothing == "Light":
                window = 3
            elif smoothing == "Medium":
                window = 5
            else:  # Heavy
                window = 9
            
            if len(pressures) > window:
                kernel = np.ones(window) / window
                pressures = np.convolve(pressures, kernel, mode='same')
        
        # Update curve
        curve = self.pressure_curves[cylinder]
        curve.setData(angles, pressures)
        
        # Show/hide based on checkbox
        checkbox = self.cylinder_checkboxes.get(cylinder)
        if checkbox:
            curve.setVisible(checkbox.isChecked())
    
    def update_secondary_parameters(
        self,
        angles: np.ndarray,
        afr: Optional[np.ndarray] = None,
        timing: Optional[np.ndarray] = None
    ) -> None:
        """
        Update secondary parameter overlays (AFR, Timing).
        
        Args:
            angles: Crank angle array
            afr: Air-fuel ratio array (optional)
            timing: Ignition timing array (optional)
        """
        # Remove old curves
        if self.afr_curve:
            self.secondary_axis.removeItem(self.afr_curve)
            self.afr_curve = None
        
        if self.timing_curve:
            self.secondary_axis.removeItem(self.timing_curve)
            self.timing_curve = None
        
        # Update secondary axis label
        labels = []
        if afr is not None and self.show_afr_checkbox.isChecked():
            self.afr_curve = pg.PlotDataItem(
                angles,
                afr,
                pen=pg.mkPen(color="#00ff00", width=2),
                name="AFR",
            )
            self.secondary_axis.addItem(self.afr_curve)
            labels.append("AFR")
        
        if timing is not None and self.show_timing_checkbox.isChecked():
            self.timing_curve = pg.PlotDataItem(
                angles,
                timing,
                pen=pg.mkPen(color="#ff00ff", width=2),
                name="Timing",
            )
            self.secondary_axis.addItem(self.timing_curve)
            labels.append("Timing")
        
        if labels:
            self.pressure_plot.setLabel("right", " / ".join(labels), color="white")
        else:
            self.pressure_plot.setLabel("right", "")
    
    def add_comparison_cycle(
        self,
        cycle: "PressureCycle",
        label: str = "Comparison",
        color: Optional[str] = None
    ) -> None:
        """
        Add a comparison cycle (e.g., before/after tuning).
        
        Args:
            cycle: Pressure cycle to compare
            label: Label for this comparison
            color: Color for the curve (default: gray)
        """
        angles = cycle.get_crank_angle_array()
        pressures = cycle.get_pressure_array()
        
        if color is None:
            color = "#888888"  # Gray
        
        curve = self.pressure_plot.plot(
            angles,
            pressures,
            pen=pg.mkPen(color=color, width=2, style=Qt.DashLine),
            name=label,
        )
        self.comparison_curves.append(curve)
    
    def clear_comparisons(self) -> None:
        """Clear all comparison curves."""
        for curve in self.comparison_curves:
            self.pressure_plot.removeItem(curve)
        self.comparison_curves.clear()
    
    def _on_view_changed(self, view: str) -> None:
        """Handle view change."""
        if view == "Full Cycle (720°)":
            self.pressure_plot.setXRange(0, 720)
        elif view == "Compression/Power (0-180°)":
            self.pressure_plot.setXRange(0, 180)
        elif view == "Zoom to Combustion":
            # Zoom to typical combustion range (TDC to 90° ATDC)
            self.pressure_plot.setXRange(-10, 90)
    
    def _update_display(self) -> None:
        """Update display when settings change."""
        # This would trigger a redraw of all cycles
        # For now, just a placeholder
        pass

