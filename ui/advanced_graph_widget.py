"""
Advanced Graphing Widget with Zoom, Pan, Annotations, Overlays, and Export

Features:
- Interactive zoom and pan
- Annotations (text, arrows, markers)
- Multiple overlay curves
- Export to PNG/PDF
- Measurement tools
- Cursor tracking
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import pyqtgraph as pg
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QAction,
    QFileDialog,
    QMenu,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

LOGGER = logging.getLogger(__name__)

pg.setConfigOptions(antialias=True, background="black", foreground="white")


class AnnotationItem(pg.TextItem):
    """Annotation text item with arrow."""

    def __init__(self, text: str, pos: Tuple[float, float], color: str = "#ffff00"):
        """Initialize annotation."""
        super().__init__(text=text, color=color, anchor=(0.5, 1))
        self.setPos(*pos)
        self.arrow = None


class AdvancedGraphWidget(QWidget):
    """Advanced graphing widget with full interactivity and auto-detection."""

    # Signals
    data_point_selected = Signal(float, float)  # x, y
    annotation_added = Signal(str, float, float)  # text, x, y
    data_type_detected = Signal(str, str)  # data_type, unit

    def __init__(self, parent: Optional[QWidget] = None, title: str = "Graph") -> None:
        """Initialize advanced graph widget."""
        super().__init__(parent)
        
        self.title = title
        self.annotations: List[AnnotationItem] = []
        self.overlay_curves: Dict[str, pg.PlotDataItem] = {}
        self.measurement_lines: List[pg.InfiniteLine] = []
        self.data_types: Dict[str, str] = {}  # label -> detected type
        self.units: Dict[str, str] = {}  # label -> detected unit
        self.color_index = 0
        
        self._setup_ui()
        self._setup_interactions()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet("QToolBar { background: #1e1e1e; border: none; }")
        
        # Zoom tools
        self.zoom_in_action = QAction("🔍+", self)
        self.zoom_in_action.setToolTip("Zoom In")
        self.zoom_in_action.triggered.connect(self.zoom_in)
        
        self.zoom_out_action = QAction("🔍-", self)
        self.zoom_out_action.setToolTip("Zoom Out")
        self.zoom_out_action.triggered.connect(self.zoom_out)
        
        self.zoom_fit_action = QAction("⤢", self)
        self.zoom_fit_action.setToolTip("Fit to Data")
        self.zoom_fit_action.triggered.connect(self.zoom_fit)
        
        # Pan tool
        self.pan_action = QAction("✋", self)
        self.pan_action.setToolTip("Pan")
        self.pan_action.setCheckable(True)
        self.pan_action.triggered.connect(self.toggle_pan)
        
        # Annotation tool
        self.annotation_action = QAction("📝", self)
        self.annotation_action.setToolTip("Add Annotation")
        self.annotation_action.setCheckable(True)
        self.annotation_action.triggered.connect(self.toggle_annotation_mode)
        
        # Measurement tool
        self.measurement_action = QAction("📏", self)
        self.measurement_action.setToolTip("Measure Distance")
        self.measurement_action.setCheckable(True)
        self.measurement_action.triggered.connect(self.toggle_measurement_mode)
        
        # Export
        self.export_action = QAction("💾", self)
        self.export_action.setToolTip("Export Graph")
        self.export_action.triggered.connect(self.export_graph)
        
        # Clear
        self.clear_action = QAction("🗑️", self)
        self.clear_action.setToolTip("Clear Annotations")
        self.clear_action.triggered.connect(self.clear_annotations)
        
        self.toolbar.addAction(self.zoom_in_action)
        self.toolbar.addAction(self.zoom_out_action)
        self.toolbar.addAction(self.zoom_fit_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.pan_action)
        self.toolbar.addAction(self.annotation_action)
        self.toolbar.addAction(self.measurement_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.export_action)
        self.toolbar.addAction(self.clear_action)
        
        layout.addWidget(self.toolbar)
        
        # Graph widget
        self.graph = pg.GraphicsLayoutWidget()
        self.graph.setBackground("black")
        layout.addWidget(self.graph)
        
        # Main plot
        self.plot = self.graph.addPlot(row=0, col=0, title=self.title)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setLabel("left", "Y Axis")
        self.plot.setLabel("bottom", "X Axis")
        
        # Legend
        self.plot.addLegend(offset=(10, 10))
        
        # Cursor tracking
        self.cursor_label = pg.TextItem("", color="#00ff00", anchor=(0, 1))
        self.plot.addItem(self.cursor_label)
        self.cursor_label.hide()
        
        # Auto-detection status
        self.auto_detect_label = QLabel("Auto-detection: Enabled")
        self.auto_detect_label.setStyleSheet("color: #00ff00; font-size: 10px;")
        layout.addWidget(self.auto_detect_label)
        
        # Main curve
        self.main_curve = None
        
        # Interaction state
        self.annotation_mode = False
        self.measurement_mode = False
        self.pan_mode = False
        self.measurement_start = None
        self.auto_detection_enabled = True

    def _setup_interactions(self) -> None:
        """Setup mouse interactions."""
        self.plot.scene().sigMouseMoved.connect(self._on_mouse_move)
        self.plot.scene().sigMouseClicked.connect(self._on_mouse_click)

    def set_data(self, x_data: List[float], y_data: List[float], 
                 x_label: Optional[str] = None, y_label: Optional[str] = None,
                 label: str = "Data", color: Optional[str] = None, 
                 clear: bool = True) -> None:
        """
        Set main data curve with auto-detection.
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data
            x_label: X-axis label (auto-detected if None)
            y_label: Y-axis label (auto-detected if None)
            label: Curve label
            color: Curve color (auto-assigned if None)
            clear: Clear existing curves
        """
        if clear and self.main_curve:
            self.plot.removeItem(self.main_curve)
        
        # Auto-detect data types and units
        if self.auto_detection_enabled:
            if x_label is None:
                x_label = self._auto_detect_label(label, x_data, is_x=True)
            if y_label is None:
                y_label = self._auto_detect_label(label, y_data, is_x=False)
            
            # Auto-assign color if not provided
            if color is None:
                color = self._get_next_color()
            
            # Store detected types
            self.data_types[label] = self._detect_data_type(label, y_data)
            self.units[label] = self._extract_unit(label)
        
        # Use provided color or default
        if color is None:
            color = "#00e0ff"
        
        self.main_curve = self.plot.plot(
            x_data, y_data,
            pen=pg.mkPen(color=color, width=2),
            name=label,
        )
        
        # Update axis labels
        self.plot.setLabel("bottom", x_label or "X Axis")
        self.plot.setLabel("left", y_label or "Y Axis")
        
        # Auto-scale
        if x_data and y_data:
            self.plot.setXRange(min(x_data), max(x_data), padding=0.1)
            self.plot.setYRange(min(y_data), max(y_data), padding=0.1)
        
        # Emit detection signal
        if self.auto_detection_enabled:
            detected_type = self.data_types.get(label, "unknown")
            unit = self.units.get(label, "")
            self.data_type_detected.emit(detected_type, unit)

    def add_overlay(self, x_data: List[float], y_data: List[float],
                    label: str = "Overlay", color: str = "#ffff00") -> None:
        """Add overlay curve."""
        curve = self.plot.plot(
            x_data, y_data,
            pen=pg.mkPen(color=color, width=2, style=Qt.DashLine),
            name=label,
        )
        self.overlay_curves[label] = curve

    def remove_overlay(self, label: str) -> None:
        """Remove overlay curve."""
        if label in self.overlay_curves:
            self.plot.removeItem(self.overlay_curves[label])
            del self.overlay_curves[label]

    def add_annotation(self, text: str, x: float, y: float, 
                      color: str = "#ffff00") -> None:
        """Add text annotation."""
        annotation = AnnotationItem(text, (x, y), color)
        self.plot.addItem(annotation)
        self.annotations.append(annotation)
        self.annotation_added.emit(text, x, y)

    def clear_annotations(self) -> None:
        """Clear all annotations."""
        for annotation in self.annotations:
            self.plot.removeItem(annotation)
        self.annotations.clear()
        
        for line in self.measurement_lines:
            self.plot.removeItem(line)
        self.measurement_lines.clear()
        self.measurement_start = None

    def zoom_in(self) -> None:
        """Zoom in by 20%."""
        view_range = self.plot.viewRange()
        x_range = view_range[0]
        y_range = view_range[1]
        
        x_center = (x_range[0] + x_range[1]) / 2
        y_center = (y_range[0] + y_range[1]) / 2
        x_span = (x_range[1] - x_range[0]) * 0.8
        y_span = (y_range[1] - y_range[0]) * 0.8
        
        self.plot.setXRange(x_center - x_span/2, x_center + x_span/2)
        self.plot.setYRange(y_center - y_span/2, y_center + y_span/2)

    def zoom_out(self) -> None:
        """Zoom out by 20%."""
        view_range = self.plot.viewRange()
        x_range = view_range[0]
        y_range = view_range[1]
        
        x_center = (x_range[0] + x_range[1]) / 2
        y_center = (y_range[0] + y_range[1]) / 2
        x_span = (x_range[1] - x_range[0]) * 1.25
        y_span = (y_range[1] - y_range[0]) * 1.25
        
        self.plot.setXRange(x_center - x_span/2, x_center + x_span/2)
        self.plot.setYRange(y_center - y_span/2, y_center + y_span/2)

    def zoom_fit(self) -> None:
        """Fit to all data."""
        if self.main_curve:
            x_data, y_data = self.main_curve.getData()
            if x_data and y_data:
                self.plot.setXRange(min(x_data), max(x_data), padding=0.1)
                self.plot.setYRange(min(y_data), max(y_data), padding=0.1)

    def toggle_pan(self, enabled: bool) -> None:
        """Toggle pan mode."""
        self.pan_mode = enabled
        if enabled:
            self.annotation_action.setChecked(False)
            self.measurement_action.setChecked(False)
            self.annotation_mode = False
            self.measurement_mode = False

    def toggle_annotation_mode(self, enabled: bool) -> None:
        """Toggle annotation mode."""
        self.annotation_mode = enabled
        if enabled:
            self.pan_action.setChecked(False)
            self.measurement_action.setChecked(False)
            self.pan_mode = False
            self.measurement_mode = False

    def toggle_measurement_mode(self, enabled: bool) -> None:
        """Toggle measurement mode."""
        self.measurement_mode = enabled
        if enabled:
            self.pan_action.setChecked(False)
            self.annotation_action.setChecked(False)
            self.pan_mode = False
            self.annotation_mode = False

    def _on_mouse_move(self, pos: QPointF) -> None:
        """Handle mouse movement."""
        if self.plot.sceneBoundingRect().contains(pos):
            # Convert to plot coordinates
            plot_pos = self.plot.vb.mapSceneToView(pos)
            x, y = plot_pos.x(), plot_pos.y()
            
            # Update cursor label
            self.cursor_label.setText(f"X: {x:.2f}, Y: {y:.2f}")
            self.cursor_label.setPos(plot_pos)
            self.cursor_label.show()

    def _on_mouse_click(self, event) -> None:
        """Handle mouse click."""
        if event.button() != Qt.LeftButton:
            return
        
        pos = event.scenePos()
        if not self.plot.sceneBoundingRect().contains(pos):
            return
        
        plot_pos = self.plot.vb.mapSceneToView(pos)
        x, y = plot_pos.x(), plot_pos.y()
        
        if self.annotation_mode:
            # Add annotation
            from PySide6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self, "Annotation", "Enter annotation text:")
            if ok and text:
                self.add_annotation(text, x, y)
        
        elif self.measurement_mode:
            # Add measurement line
            if self.measurement_start is None:
                self.measurement_start = (x, y)
                line = pg.InfiniteLine(
                    pos=x, angle=90,
                    pen=pg.mkPen(color="#00ff00", width=2),
                )
                self.plot.addItem(line)
                self.measurement_lines.append(line)
            else:
                # Draw second line and calculate distance
                line = pg.InfiniteLine(
                    pos=x, angle=90,
                    pen=pg.mkPen(color="#00ff00", width=2),
                )
                self.plot.addItem(line)
                self.measurement_lines.append(line)
                
                distance = abs(x - self.measurement_start[0])
                self.add_annotation(f"ΔX: {distance:.2f}", (x + self.measurement_start[0])/2, y)
                self.measurement_start = None
        
        else:
            # Emit data point selected signal
            self.data_point_selected.emit(x, y)

    def export_graph(self) -> None:
        """Export graph to file."""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Graph",
            f"{self.title}.png",
            "PNG Image (*.png);;PDF Document (*.pdf);;SVG Image (*.svg)",
        )
        
        if not file_path:
            return
        
        try:
            exporter = pg.exporters.ImageExporter(self.plot)
            
            if file_path.endswith('.png'):
                exporter.export(file_path)
            elif file_path.endswith('.pdf'):
                exporter = pg.exporters.PDFExporter(self.plot)
                exporter.export(file_path)
            elif file_path.endswith('.svg'):
                exporter = pg.exporters.SVGExporter(self.plot)
                exporter.export(file_path)
            
            LOGGER.info("Exported graph to: %s", file_path)
        except Exception as e:
            LOGGER.error("Failed to export graph: %s", e)

    def set_labels(self, x_label: str, y_label: str) -> None:
        """Set axis labels."""
        self.plot.setLabel("bottom", x_label)
        self.plot.setLabel("left", y_label)

    def set_title(self, title: str) -> None:
        """Set plot title."""
        self.title = title
        self.plot.setTitle(title)

    def _auto_detect_label(self, label: str, data: List[float], is_x: bool = False) -> str:
        """
        Auto-detect axis label from data label and values.
        
        Args:
            label: Data label/name
            data: Data values
            is_x: Whether this is X-axis data
            
        Returns:
            Detected label with unit
        """
        # Detect unit from label
        unit = self._extract_unit(label)
        data_type = self._detect_data_type(label, data)
        
        # Format label
        if unit:
            return f"{data_type} ({unit})"
        return data_type

    def _detect_data_type(self, label: str, data: List[float]) -> str:
        """
        Detect data type from label and value ranges.
        
        Args:
            label: Data label
            data: Data values
            
        Returns:
            Detected data type name
        """
        label_lower = label.lower()
        
        # Check label patterns
        for unit_type, (pattern, names) in UNIT_PATTERNS.items():
            if re.search(pattern, label_lower, re.IGNORECASE):
                return names[0]  # Return primary name
        
        # Detect from value ranges if label doesn't match
        if data:
            min_val = min(data)
            max_val = max(data)
            
            # RPM detection (typically 0-10000)
            if 500 <= max_val <= 10000 and min_val >= 0:
                return "RPM"
            
            # Speed detection (MPH typically 0-200, KMH 0-300)
            if 0 <= max_val <= 300:
                if max_val <= 200:
                    return "Speed (MPH)"
                return "Speed (KMH)"
            
            # Pressure (PSI typically 0-100, Bar 0-7)
            if 0 <= max_val <= 100:
                return "Pressure (PSI)"
            if 0 <= max_val <= 7:
                return "Pressure (Bar)"
            
            # Temperature (Celsius 0-150, Fahrenheit 32-300)
            if 0 <= max_val <= 150:
                return "Temperature (°C)"
            if 32 <= min_val <= 300:
                return "Temperature (°F)"
            
            # Voltage (typically 0-20V)
            if 0 <= max_val <= 20:
                return "Voltage (V)"
            
            # G-Force (typically -2 to +2)
            if -3 <= min_val <= 3 and -3 <= max_val <= 3:
                return "G-Force"
            
            # HP (typically 0-2000)
            if 0 <= max_val <= 2000:
                return "Horsepower (HP)"
            
            # Torque (typically 0-2000 ft-lb)
            if 0 <= max_val <= 2000:
                return "Torque (ft-lb)"
        
        # Default: use label as-is
        return label.replace("_", " ").title()

    def _extract_unit(self, label: str) -> str:
        """
        Extract unit from label.
        
        Args:
            label: Data label
            
        Returns:
            Unit string or empty string
        """
        label_lower = label.lower()
        
        for unit_type, (pattern, names) in UNIT_PATTERNS.items():
            if re.search(pattern, label_lower, re.IGNORECASE):
                return names[0]  # Return primary unit name
        
        return ""

    def _get_next_color(self) -> str:
        """Get next color from palette."""
        color = COLOR_PALETTE[self.color_index % len(COLOR_PALETTE)]
        self.color_index += 1
        return color

    def enable_auto_detection(self, enabled: bool = True) -> None:
        """Enable or disable auto-detection."""
        self.auto_detection_enabled = enabled
        status = "Enabled" if enabled else "Disabled"
        self.auto_detect_label.setText(f"Auto-detection: {status}")
        self.auto_detect_label.setStyleSheet(
            f"color: {'#00ff00' if enabled else '#ff6b6b'}; font-size: 10px;"
        )

    def auto_detect_and_plot(self, data_dict: Dict[str, List[float]], 
                            x_key: Optional[str] = None) -> None:
        """
        Auto-detect and plot multiple data series.
        
        Args:
            data_dict: Dictionary of {label: [values]} or {label: {'x': [...], 'y': [...]}}
            x_key: Key to use for X-axis (auto-detected if None)
        """
        if not data_dict:
            return
        
        # Determine X-axis
        if x_key is None:
            # Look for common X-axis keys
            x_candidates = ['time', 'timestamp', 'rpm', 'x', 'index']
            for candidate in x_candidates:
                if candidate in data_dict:
                    x_key = candidate
                    break
            
            # If still not found, use first key
            if x_key is None:
                x_key = list(data_dict.keys())[0]
        
        # Get X data
        x_data = None
        if isinstance(data_dict[x_key], dict):
            x_data = data_dict[x_key].get('x', data_dict[x_key].get('values', []))
        elif isinstance(data_dict[x_key], list):
            x_data = data_dict[x_key]
        
        if x_data is None:
            LOGGER.warning("Could not extract X-axis data")
            return
        
        # Plot each series
        first = True
        for key, value in data_dict.items():
            if key == x_key:
                continue
            
            # Extract Y data
            y_data = None
            if isinstance(value, dict):
                y_data = value.get('y', value.get('values', []))
            elif isinstance(value, list):
                y_data = value
            
            if y_data is None or len(y_data) != len(x_data):
                LOGGER.warning(f"Skipping {key}: data length mismatch")
                continue
            
            # Plot
            if first:
                self.set_data(x_data, y_data, x_label=None, y_label=None, 
                            label=key, clear=True)
                first = False
            else:
                self.add_overlay(x_data, y_data, label=key)


__all__ = ["AdvancedGraphWidget", "AnnotationItem"]

