"""
Enhanced Telemetry Panel - Advanced graphing with dynamic sensor selection
Features:
- Add/remove any sensor dynamically
- Click sensor to configure
- Multiple Y-axes
- Zoom, pan, export
- Sensor legend with enable/disable
- Advanced features for professional tuners
"""

from __future__ import annotations

import csv
import json
import logging
from collections import deque
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Set, Tuple

from PySide6.QtCore import Qt, QTimer, Signal, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QToolBar,
    QSizePolicy,
    QMenu,
    QFileDialog,
    QMessageBox,
    QCheckBox,
    QScrollArea,
    QGroupBox,
    QSplitter,
    QFrame,
    QDialog,
    QComboBox,
)

try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget, PlotItem, PlotDataItem, InfiniteLine
    PG_AVAILABLE = True
except ImportError:
    pg = None
    PG_AVAILABLE = False

try:
    from ui.responsive_layout_manager import get_responsive_manager, scaled_font_size, scaled_spacing
    RESPONSIVE_AVAILABLE = True
except ImportError:
    RESPONSIVE_AVAILABLE = False
    get_responsive_manager = None
    scaled_font_size = lambda x: x
    scaled_spacing = lambda x: x

from ui.sensor_selection_dialog import SensorSelectionDialog
from ui.sensor_settings_dialog import SensorConfig, SensorSettingsDialog
from ui.advanced_graph_features import (
    AdvancedGraphFeaturesDialog,
    MathChannel,
    MathChannelDialog,
)

LOGGER = logging.getLogger(__name__)

if PG_AVAILABLE:
    pg.setConfigOptions(antialias=True, background="#ffffff", foreground="#2c3e50")


@dataclass
class SensorData:
    """Data storage for a sensor."""
    name: str
    values: deque
    config: SensorConfig
    curve: Optional[PlotDataItem] = None
    min_line: Optional[InfiniteLine] = None
    max_line: Optional[InfiniteLine] = None
    alert_min_line: Optional[InfiniteLine] = None
    alert_max_line: Optional[InfiniteLine] = None


class EnhancedTelemetryPanel(QWidget):
    """Advanced telemetry graphing panel with dynamic sensor selection."""
    
    # Default sensor colors (distinct colors for visibility)
    DEFAULT_COLORS = [
        "#ff6b6b", "#4ecdc4", "#ffe66d", "#36c5f0", "#ffa94d", "#b197fc",
        "#ff8787", "#63e6be", "#ff922b", "#fab005", "#10b981", "#3b82f6",
        "#8b5cf6", "#f59e0b", "#ef4444", "#06b6d4", "#84cc16", "#ec4899",
        "#14b8a6", "#a855f7", "#f97316", "#22c55e", "#eab308", "#3b82f6"
    ]
    
    def __init__(self, parent: Optional[QWidget] = None, max_len: int = 1000) -> None:
        super().__init__(parent)
        self.max_len = max_len
        self.sensors: Dict[str, SensorData] = {}
        self.available_sensors: Set[str] = set()
        self.math_channels: Dict[str, MathChannel] = {}  # Custom calculated channels
        self.xdata = deque(maxlen=max_len)
        self.counter = 0
        self.config_file = Path.home() / ".aituner" / "telemetry_config.json"
        
        # Graph widgets
        self.main_plot: Optional[PlotWidget] = None
        self.legend_widget: Optional[QWidget] = None
        
        # UI state
        self.zoom_mode = False
        self.pan_mode = False
        self.time_range = None  # None = all data, or (start, end) tuple
        
        self.setup_ui()
        self.load_config()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(scaled_spacing(4))
        layout.setContentsMargins(
            scaled_spacing(8), scaled_spacing(8),
            scaled_spacing(8), scaled_spacing(8)
        )
        
        # Header with toolbar
        header_layout = QHBoxLayout()
        
        title = QLabel("Advanced Telemetry Graphing")
        title_font_size = scaled_font_size(18)
        title.setStyleSheet(
            f"font-size: {title_font_size}px; font-weight: 600; color: #1f2a44;"
        )
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Toolbar buttons
        self.add_sensor_btn = QPushButton("➕ Add Sensor")
        self.add_sensor_btn.setToolTip("Add sensors to graph")
        self.add_sensor_btn.clicked.connect(self._show_sensor_selection)
        header_layout.addWidget(self.add_sensor_btn)
        
        self.zoom_btn = QPushButton("🔍 Zoom")
        self.zoom_btn.setCheckable(True)
        self.zoom_btn.setToolTip("Enable zoom mode (mouse wheel)")
        self.zoom_btn.clicked.connect(self._toggle_zoom)
        header_layout.addWidget(self.zoom_btn)
        
        self.pan_btn = QPushButton("✋ Pan")
        self.pan_btn.setCheckable(True)
        self.pan_btn.setToolTip("Enable pan mode (drag to pan)")
        self.pan_btn.clicked.connect(self._toggle_pan)
        header_layout.addWidget(self.pan_btn)
        
        self.reset_view_btn = QPushButton("↺ Reset View")
        self.reset_view_btn.setToolTip("Reset zoom and pan")
        self.reset_view_btn.clicked.connect(self._reset_view)
        header_layout.addWidget(self.reset_view_btn)
        
        self.export_btn = QPushButton("💾 Export")
        self.export_btn.setToolTip("Export graph data")
        self.export_btn.clicked.connect(self._export_data)
        header_layout.addWidget(self.export_btn)
        
        # Advanced features button
        self.advanced_btn = QPushButton("⚡ Advanced")
        self.advanced_btn.setToolTip("Advanced features: X-Y plots, FFT, Histograms, Math Channels")
        self.advanced_btn.clicked.connect(self._show_advanced_features)
        header_layout.addWidget(self.advanced_btn)
        
        # Time range selector
        time_range_layout = QHBoxLayout()
        time_range_layout.addWidget(QLabel("Time Range:"))
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["All", "Last 100", "Last 500", "Last 1000", "Custom"])
        self.time_range_combo.currentTextChanged.connect(self._change_time_range)
        time_range_layout.addWidget(self.time_range_combo)
        header_layout.addLayout(time_range_layout)
        
        layout.addLayout(header_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Graph area
        graph_container = QWidget()
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        
        if PG_AVAILABLE:
            # Create main plot with multiple Y-axes support
            self.main_plot = PlotWidget(title="Telemetry Data")
            self.main_plot.setBackground("w")
            self.main_plot.setMinimumHeight(400)
            self.main_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # Configure plot
            self.main_plot.setLabel("left", "Value", color="#2c3e50")
            self.main_plot.setLabel("bottom", "Time (samples)", color="#2c3e50")
            self.main_plot.showGrid(x=True, y=True, alpha=0.3)
            self.main_plot.addLegend(offset=(10, 10))
            
            # Enable mouse interaction
            self.main_plot.setMouseEnabled(x=True, y=True)
            
            # Connect click events - pyqtgraph uses scene's sigMouseClicked
            if hasattr(self.main_plot.scene(), 'sigMouseClicked'):
                self.main_plot.scene().sigMouseClicked.connect(self._on_plot_click)
            
            graph_layout.addWidget(self.main_plot)
        else:
            error_label = QLabel("pyqtgraph not available. Install with: pip install pyqtgraph")
            error_label.setStyleSheet("color: red; padding: 20px;")
            graph_layout.addWidget(error_label)
        
        splitter.addWidget(graph_container)
        
        # Legend/sensor list panel
        legend_container = QWidget()
        legend_container.setMaximumWidth(250)
        legend_layout = QVBoxLayout(legend_container)
        legend_layout.setContentsMargins(4, 4, 4, 4)
        
        legend_title = QLabel("Sensors")
        legend_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        legend_layout.addWidget(legend_title)
        
        # Scrollable legend
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(400)
        
        self.legend_widget = QWidget()
        self.legend_layout = QVBoxLayout(self.legend_widget)
        self.legend_layout.setContentsMargins(0, 0, 0, 0)
        self.legend_layout.setSpacing(2)
        
        scroll.setWidget(self.legend_widget)
        legend_layout.addWidget(scroll)
        
        legend_layout.addStretch()
        
        splitter.addWidget(legend_container)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 11px; padding: 4px;")
        layout.addWidget(self.status_label)
    
    def _show_sensor_selection(self):
        """Show sensor selection dialog."""
        if not PG_AVAILABLE:
            QMessageBox.warning(self, "Error", "pyqtgraph not available")
            return
        
        # Get currently selected sensors
        current_sensors = list(self.sensors.keys())
        
        # Get available sensors (all sensors that have been seen)
        available = list(self.available_sensors) if self.available_sensors else []
        
        dialog = SensorSelectionDialog(available, current_sensors, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_sensors()
            self._update_sensor_selection(selected)
    
    def add_math_channel(self, math_channel: MathChannel):
        """Add a math channel programmatically."""
        self.math_channels[math_channel.name] = math_channel
        self._update_legend()
        self.save_config()
    
    def _update_sensor_selection(self, selected: List[str]):
        """Update which sensors are displayed."""
        # Remove sensors not in selection
        to_remove = [name for name in self.sensors.keys() if name not in selected]
        for name in to_remove:
            self._remove_sensor(name)
        
        # Add new sensors
        for name in selected:
            if name not in self.sensors:
                self._add_sensor(name)
        
        self.save_config()
        self._update_legend()
    
    def _add_sensor(self, name: str):
        """Add a sensor to the graph."""
        if not PG_AVAILABLE or not self.main_plot:
            return
        
        # Get color (cycle through defaults)
        color_index = len(self.sensors) % len(self.DEFAULT_COLORS)
        color = self.DEFAULT_COLORS[color_index]
        
        # Create config
        config = SensorConfig(
            name=name,
            enabled=True,
            color=color,
            line_width=2,
            axis=0
        )
        
        # Create sensor data
        sensor_data = SensorData(
            name=name,
            values=deque(maxlen=self.max_len),
            config=config
        )
        
        # Create curve
        pen = pg.mkPen(color=color, width=config.line_width)
        curve = self.main_plot.plot([], [], pen=pen, name=name)
        sensor_data.curve = curve
        
        # Store sensor name for click detection (we'll use a different method)
        # The curve itself will be used to identify the sensor
        
        self.sensors[name] = sensor_data
        LOGGER.info(f"Added sensor to graph: {name}")
    
    def _remove_sensor(self, name: str):
        """Remove a sensor from the graph."""
        if name not in self.sensors:
            return
        
        sensor_data = self.sensors[name]
        
        # Remove curve from plot
        if sensor_data.curve and self.main_plot:
            self.main_plot.removeItem(sensor_data.curve)
        
        # Remove threshold lines
        for line in [sensor_data.min_line, sensor_data.max_line, 
                     sensor_data.alert_min_line, sensor_data.alert_max_line]:
            if line and self.main_plot:
                self.main_plot.removeItem(line)
        
        del self.sensors[name]
        LOGGER.info(f"Removed sensor from graph: {name}")
    
    def _on_plot_click(self, event):
        """Handle clicks on the plot."""
        if not PG_AVAILABLE or not self.main_plot:
            return
        
        # Right-click shows context menu, left-click on curve shows settings
        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event)
            return
        
        # Get clicked item from scene
        scene_pos = event.scenePos() if hasattr(event, 'scenePos') else event.pos()
        items = self.main_plot.scene().items(scene_pos)
        
        for item in items:
            if isinstance(item, PlotDataItem):
                # Find which sensor this curve belongs to
                for name, sensor_data in self.sensors.items():
                    if sensor_data.curve == item:
                        self._show_sensor_settings(name)
                        return
        
        # If clicking on legend, try to find sensor by legend item
        # Get mouse position in plot coordinates for proximity check
        vb = self.main_plot.getViewBox()
        if vb and hasattr(event, 'scenePos'):
            try:
                mouse_point = vb.mapSceneToView(event.scenePos())
                # Check each curve for proximity (within 10 pixels)
                closest_sensor = None
                closest_dist = float('inf')
                
                for name, sensor_data in self.sensors.items():
                    if sensor_data.curve and len(sensor_data.values) > 0:
                        # Find closest point on curve
                        x_data = list(self.xdata)
                        y_data = list(sensor_data.values)
                        if len(x_data) == len(y_data) and len(x_data) > 0:
                            # Check distance to each point
                            for i, (x, y) in enumerate(zip(x_data, y_data)):
                                dist = ((mouse_point.x() - x)**2 + (mouse_point.y() - y)**2)**0.5
                                if dist < closest_dist and dist < 20:  # 20 pixel threshold
                                    closest_dist = dist
                                    closest_sensor = name
                
                if closest_sensor:
                    self._show_sensor_settings(closest_sensor)
            except Exception as e:
                LOGGER.debug(f"Error in click detection: {e}")
    
    def _show_context_menu(self, event):
        """Show context menu on right-click."""
        menu = QMenu(self)
        
        add_action = menu.addAction("➕ Add Sensor")
        add_action.triggered.connect(self._show_sensor_selection)
        
        menu.addSeparator()
        
        reset_action = menu.addAction("↺ Reset View")
        reset_action.triggered.connect(self._reset_view)
        
        export_action = menu.addAction("💾 Export Data")
        export_action.triggered.connect(self._export_data)
        
        if hasattr(event, 'globalPos'):
            menu.exec(event.globalPos())
        elif hasattr(event, 'screenPos'):
            menu.exec(event.screenPos().toPoint())
        else:
            menu.exec(event.pos())
    
    def _show_sensor_settings(self, sensor_name: str):
        """Show settings dialog for a sensor."""
        if sensor_name not in self.sensors:
            return
        
        sensor_data = self.sensors[sensor_name]
        dialog = SensorSettingsDialog(sensor_name, sensor_data.config, self)
        dialog.config_changed.connect(self._on_sensor_config_changed)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._apply_sensor_config(sensor_name, dialog.get_config())
            self.save_config()
    
    def _on_sensor_config_changed(self, sensor_name: str, config: SensorConfig):
        """Handle sensor config changes."""
        self._apply_sensor_config(sensor_name, config)
    
    def _apply_sensor_config(self, sensor_name: str, config: SensorConfig):
        """Apply configuration to a sensor."""
        if sensor_name not in self.sensors:
            return
        
        sensor_data = self.sensors[sensor_name]
        sensor_data.config = config
        
        # Update curve appearance
        if sensor_data.curve:
            pen = pg.mkPen(
                color=config.color,
                width=config.line_width,
                style=Qt.PenStyle.SolidLine if config.line_style == "solid" else
                      Qt.PenStyle.DashLine if config.line_style == "dashed" else
                      Qt.PenStyle.DotLine
            )
            sensor_data.curve.setPen(pen)
            sensor_data.curve.setVisible(config.enabled)
        
        # Update threshold lines
        self._update_threshold_lines(sensor_name)
        self._update_legend()
    
    def _update_threshold_lines(self, sensor_name: str):
        """Update min/max/alert lines for a sensor."""
        if sensor_name not in self.sensors or not self.main_plot:
            return
        
        sensor_data = self.sensors[sensor_name]
        config = sensor_data.config
        
        # Remove old lines
        for line in [sensor_data.min_line, sensor_data.max_line,
                     sensor_data.alert_min_line, sensor_data.alert_max_line]:
            if line:
                self.main_plot.removeItem(line)
        
        # Add new lines
        if config.min_value is not None:
            sensor_data.min_line = InfiniteLine(
                pos=config.min_value, angle=0, pen=pg.mkPen(color="#ff6b6b", style=Qt.PenStyle.DashLine)
            )
            self.main_plot.addItem(sensor_data.min_line)
        
        if config.max_value is not None:
            sensor_data.max_line = InfiniteLine(
                pos=config.max_value, angle=0, pen=pg.mkPen(color="#ff6b6b", style=Qt.PenStyle.DashLine)
            )
            self.main_plot.addItem(sensor_data.max_line)
        
        if config.alert_min is not None:
            sensor_data.alert_min_line = InfiniteLine(
                pos=config.alert_min, angle=0, pen=pg.mkPen(color="#e74c3c", style=Qt.PenStyle.DashDotLine)
            )
            self.main_plot.addItem(sensor_data.alert_min_line)
        
        if config.alert_max is not None:
            sensor_data.alert_max_line = InfiniteLine(
                pos=config.alert_max, angle=0, pen=pg.mkPen(color="#e74c3c", style=Qt.PenStyle.DashDotLine)
            )
            self.main_plot.addItem(sensor_data.alert_max_line)
    
    def _update_legend(self):
        """Update the sensor legend widget."""
        if not self.legend_widget:
            return
        
        # Clear existing
        while self.legend_layout.count():
            child = self.legend_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add sensors (excluding math channels)
        regular_sensors = [(name, sd) for name, sd in sorted(self.sensors.items()) if name not in self.math_channels]
        for name, sensor_data in regular_sensors:
            item_widget = self._create_legend_item(name, sensor_data)
            self.legend_layout.addWidget(item_widget)
        
        # Add math channels (separate section)
        if self.math_channels:
            separator = QLabel("─── Calculated Channels ───")
            separator.setStyleSheet("color: #999; font-weight: bold; padding: 4px;")
            self.legend_layout.addWidget(separator)
            
            for name, math_channel in sorted(self.math_channels.items()):
                item_widget = self._create_math_channel_legend_item(name, math_channel)
                self.legend_layout.addWidget(item_widget)
    
    def _create_legend_item(self, name: str, sensor_data: SensorData) -> QWidget:
        """Create a legend item widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        
        # Color indicator
        color_label = QLabel("■")
        color_label.setStyleSheet(f"color: {sensor_data.config.color}; font-size: 16px;")
        layout.addWidget(color_label)
        
        # Checkbox for enable/disable
        checkbox = QCheckBox(name)
        checkbox.setChecked(sensor_data.config.enabled)
        checkbox.stateChanged.connect(lambda state, n=name: self._toggle_sensor(n, state == Qt.CheckState.Checked.value))
        layout.addWidget(checkbox)
        
        # Settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(20, 20)
        settings_btn.setToolTip(f"Configure {name}")
        settings_btn.clicked.connect(lambda checked, n=name: self._show_sensor_settings(n))
        layout.addWidget(settings_btn)
        
        return widget
    
    def _create_math_channel_legend_item(self, name: str, math_channel: MathChannel) -> QWidget:
        """Create a legend item for a math channel."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        
        # Color indicator (dashed to distinguish from regular sensors)
        color_label = QLabel("◊")
        color_label.setStyleSheet(f"color: {math_channel.color}; font-size: 16px; font-weight: bold;")
        layout.addWidget(color_label)
        
        # Label with formula indicator
        checkbox = QCheckBox(f"{name} (calc)")
        checkbox.setChecked(math_channel.enabled)
        checkbox.stateChanged.connect(lambda state, n=name: self._toggle_math_channel(n, state == Qt.CheckState.Checked.value))
        layout.addWidget(checkbox)
        
        # Settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(20, 20)
        settings_btn.setToolTip(f"Edit {name}")
        settings_btn.clicked.connect(lambda checked, n=name: self._edit_math_channel(n))
        layout.addWidget(settings_btn)
        
        return widget
    
    def _toggle_math_channel(self, name: str, enabled: bool):
        """Toggle math channel visibility."""
        if name in self.math_channels:
            self.math_channels[name].enabled = enabled
            # Math channels are calculated on-the-fly, so we just need to update display
            self._update_display_range()
    
    def _edit_math_channel(self, name: str):
        """Edit a math channel."""
        if name not in self.math_channels:
            return
        
        math_channel = self.math_channels[name]
        dialog = MathChannelDialog(list(self.available_sensors), math_channel, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_channel = dialog.get_math_channel()
            if new_channel:
                self.math_channels[name] = new_channel
                self._update_legend()
                self.save_config()
    
    def _toggle_sensor(self, name: str, enabled: bool):
        """Toggle sensor visibility."""
        if name in self.sensors:
            self.sensors[name].config.enabled = enabled
            if self.sensors[name].curve:
                self.sensors[name].curve.setVisible(enabled)
    
    def _toggle_zoom(self, checked: bool):
        """Toggle zoom mode."""
        self.zoom_mode = checked
        self.pan_mode = False
        self.pan_btn.setChecked(False)
        if self.main_plot:
            self.main_plot.setMouseEnabled(x=checked, y=checked)
    
    def _toggle_pan(self, checked: bool):
        """Toggle pan mode."""
        self.pan_mode = checked
        self.zoom_mode = False
        self.zoom_btn.setChecked(False)
        if self.main_plot:
            # Pan is handled by pyqtgraph's built-in pan
            pass
    
    def _reset_view(self):
        """Reset zoom and pan."""
        if self.main_plot:
            self.main_plot.autoRange()
        self.zoom_btn.setChecked(False)
        self.pan_btn.setChecked(False)
        self.zoom_mode = False
        self.pan_mode = False
    
    def _export_data(self):
        """Export graph data to file."""
        if not self.sensors:
            QMessageBox.warning(self, "No Data", "No sensors to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "", "CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if not filename:
            return
        
        try:
            if filename.endswith('.csv'):
                self._export_csv(filename)
            else:
                self._export_json(filename)
            QMessageBox.information(self, "Success", f"Data exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")
            LOGGER.error(f"Export error: {e}", exc_info=True)
    
    def _export_csv(self, filename: str):
        """Export data as CSV."""
        if not self.sensors:
            raise ValueError("No sensors to export")
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['Sample'] + list(self.sensors.keys()))
            # Data
            max_len = max((len(s.values) for s in self.sensors.values() if s.values), default=0)
            for i in range(max_len):
                row = [i]
                for name in self.sensors.keys():
                    values = list(self.sensors[name].values)
                    row.append(values[i] if i < len(values) else '')
                writer.writerow(row)
    
    def _export_json(self, filename: str):
        """Export data as JSON."""
        data = {
            'sensors': {},
            'config': {}
        }
        for name, sensor_data in self.sensors.items():
            data['sensors'][name] = list(sensor_data.values)
            data['config'][name] = asdict(sensor_data.config)
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def update_data(self, data: Mapping[str, float]) -> None:
        """Update graph with new telemetry data."""
        if not PG_AVAILABLE or not self.main_plot:
            return
        
        # Track available sensors
        self.available_sensors.update(data.keys())
        
        self.counter += 1
        self.xdata.append(self.counter)
        
        # Update each sensor
        for name, sensor_data in self.sensors.items():
            if not sensor_data.config.enabled:
                continue
            
            # Get value with aliases
            value = self._get_sensor_value(name, data)
            if value is None:
                continue
            
            # Apply scale and offset
            value = (value * sensor_data.config.scale) + sensor_data.config.offset
            
            # Apply smoothing if enabled
            if sensor_data.config.smoothing > 0 and len(sensor_data.values) > 0:
                # Simple moving average
                window = min(sensor_data.config.smoothing, len(sensor_data.values))
                avg = sum(list(sensor_data.values)[-window:]) / window
                value = (value + avg * (window - 1)) / window
            
            sensor_data.values.append(value)
            
            # Update curve
            if sensor_data.curve:
                x = list(self.xdata)
                y = list(sensor_data.values)
                sensor_data.curve.setData(x, y)
        
        # Update math channels
        self._update_math_channels(data)
        
        # Update status
        if self.sensors or self.math_channels:
            active_sensors = sum(1 for s in self.sensors.values() if s.config.enabled and s.name not in self.math_channels)
            active_math = sum(1 for m in self.math_channels.values() if m.enabled)
            total = len([s for s in self.sensors.values() if s.name not in self.math_channels]) + len(self.math_channels)
            active_total = active_sensors + active_math
            self.status_label.setText(f"Graphing {active_total}/{total} channels ({active_sensors} sensors, {active_math} calculated) | Sample #{self.counter}")
        else:
            self.status_label.setText(f"No sensors selected | Sample #{self.counter} | Click 'Add Sensor' to start")
    
    def _update_math_channels(self, data: Mapping[str, float]):
        """Update math channels with current data."""
        if not self.math_channels:
            return
        
        # Collect sensor data for math channel evaluation
        sensor_data_dict = {}
        for name, sensor_data in self.sensors.items():
            if sensor_data.values and name not in self.math_channels:
                sensor_data_dict[name] = list(sensor_data.values)
        
        # Evaluate each math channel
        for name, math_channel in self.math_channels.items():
            if not math_channel.enabled:
                continue
            
            # Evaluate formula
            result = math_channel.evaluate(sensor_data_dict)
            if result:
                # Add or update math channel sensor
                if name not in self.sensors:
                    self._add_math_channel_sensor(name, math_channel)
                
                # Update values
                if name in self.sensors:
                    sensor_data = self.sensors[name]
                    # Clear and repopulate with new calculated values
                    sensor_data.values.clear()
                    for val in result:
                        sensor_data.values.append(val)
                    
                    # Update curve
                    if sensor_data.curve:
                        x = list(self.xdata)
                        y = list(sensor_data.values)
                        
                        # Apply time range filter
                        if self.time_range is not None and len(x) > 0:
                            start_idx = max(0, len(x) - (self.counter - self.time_range))
                            x = x[start_idx:]
                            y = y[start_idx:]
                        
                        sensor_data.curve.setData(x, y)
    
    def _add_math_channel_sensor(self, name: str, math_channel: MathChannel):
        """Add a math channel as a sensor for graphing."""
        if not PG_AVAILABLE or not self.main_plot:
            return
        
        # Create config
        config = SensorConfig(
            name=name,
            enabled=math_channel.enabled,
            color=math_channel.color,
            line_width=2,
            axis=0
        )
        
        # Create sensor data
        sensor_data = SensorData(
            name=name,
            values=deque(maxlen=self.max_len),
            config=config
        )
        
        # Create curve with dashed line to distinguish from regular sensors
        pen = pg.mkPen(color=math_channel.color, width=config.line_width, style=Qt.PenStyle.DashLine)
        curve = self.main_plot.plot([], [], pen=pen, name=f"{name} (calc)")
        sensor_data.curve = curve
        
        self.sensors[name] = sensor_data
        LOGGER.info(f"Added math channel to graph: {name}")
    
    def _show_advanced_features(self):
        """Show advanced graph features dialog."""
        # Collect current sensor data
        sensor_data = {}
        for name, sensor_data_obj in self.sensors.items():
            if sensor_data_obj.values and name not in self.math_channels:
                sensor_data[name] = list(sensor_data_obj.values)
        
        # Add math channel data
        for name, math_channel in self.math_channels.items():
            if math_channel.enabled and name in self.sensors:
                sensor_data_obj = self.sensors[name]
                if sensor_data_obj.values:
                    sensor_data[name] = list(sensor_data_obj.values)
        
        available = list(self.available_sensors) + list(self.math_channels.keys())
        
        dialog = AdvancedGraphFeaturesDialog(sensor_data, available, self)
        dialog.exec()
    
    def _change_time_range(self, text: str):
        """Change the time range displayed."""
        if text == "All":
            self.time_range = None
        elif text == "Last 100":
            self.time_range = max(0, self.counter - 100)
        elif text == "Last 500":
            self.time_range = max(0, self.counter - 500)
        elif text == "Last 1000":
            self.time_range = max(0, self.counter - 1000)
        else:
            # Custom - would show a dialog, for now just use all
            self.time_range = None
        
        # Update display
        self._update_display_range()
    
    def _update_display_range(self):
        """Update the displayed data range."""
        if not PG_AVAILABLE or not self.main_plot:
            return
        
        for name, sensor_data in self.sensors.items():
            if sensor_data.curve:
                x = list(self.xdata)
                y = list(sensor_data.values)
                
                # Apply time range filter
                if self.time_range is not None and len(x) > 0:
                    start_idx = max(0, len(x) - (self.counter - self.time_range))
                    x = x[start_idx:]
                    y = y[start_idx:]
                
                sensor_data.curve.setData(x, y)
    
    def _get_sensor_value(self, name: str, data: Mapping[str, float]) -> Optional[float]:
        """Get sensor value with comprehensive alias support."""
        # Direct match (case-insensitive)
        for key in data.keys():
            if key.lower() == name.lower():
                return float(data[key])
        
        # Comprehensive aliases for all sensor types
        aliases = {
            # Powertrain
            "RPM": ("Engine_RPM", "rpm", "engine_rpm", "RPM"),
            "Engine_RPM": ("RPM", "rpm", "engine_rpm"),
            "Speed": ("Vehicle_Speed", "speed", "vehicle_speed", "GPS_Speed", "KF_Speed"),
            "Vehicle_Speed": ("Speed", "speed", "vehicle_speed"),
            "Throttle": ("Throttle_Position", "throttle", "TPS", "tps"),
            "Throttle_Position": ("Throttle", "throttle", "TPS", "tps"),
            "Boost": ("Boost_Pressure", "MAP", "boost", "boost_pressure", "Manifold_Absolute_Pressure"),
            "Boost_Pressure": ("Boost", "MAP", "boost", "Manifold_Absolute_Pressure"),
            "Timing_Advance": ("Timing", "timing", "spark_advance", "Ignition_Timing"),
            "Lambda": ("AFR", "Air_Fuel_Ratio", "lambda", "afr", "air_fuel_ratio"),
            "AFR": ("Lambda", "Air_Fuel_Ratio", "lambda", "air_fuel_ratio"),
            
            # Thermal
            "CoolantTemp": ("Coolant_Temp", "ECT", "coolant_temp", "Engine_Coolant_Temp"),
            "Coolant_Temp": ("CoolantTemp", "ECT", "coolant_temp", "Engine_Coolant_Temp"),
            "OilPressure": ("Oil_Pressure", "oil_pressure", "oil_p"),
            "Oil_Pressure": ("OilPressure", "oil_pressure", "oil_p"),
            "Oil_Temp": ("oil_temp", "oil_t", "OilTemp"),
            "Intake_Temp": ("IAT", "intake_temp", "IntakeAirTemp", "IntakeTemp"),
            "IAT": ("Intake_Temp", "intake_temp", "IntakeAirTemp"),
            "EGT": ("Exhaust_Gas_Temp", "exhaust_temp", "EGT_Temp", "ExhaustTemp"),
            "Exhaust_Gas_Temp": ("EGT", "exhaust_temp", "EGT_Temp"),
            "Fuel_Pressure": ("FuelPressure", "fuel_pressure", "fuel_p"),
            "FuelPressure": ("Fuel_Pressure", "fuel_pressure", "fuel_p"),
            
            # Forced Induction
            "Turbo_RPM": ("turbo_rpm", "TurboSpeed", "turbine_rpm"),
            "Wastegate_Position": ("wastegate", "wastegate_pos", "Wastegate"),
            "Intercooler_Temp": ("intercooler_temp", "IC_Temp", "IntercoolerTemp"),
            
            # Nitrous
            "NitrousBottlePressure": ("nitrous_pressure", "nitrous_bottle", "NitrousPressure", "N2O_Pressure"),
            "NitrousSolenoidState": ("nitrous_solenoid", "nitrous_active", "NitrousOn", "N2O_Active"),
            "NitrousFlowRate": ("nitrous_flow", "N2O_Flow", "NitrousFlow"),
            "NitrousTemperature": ("nitrous_temp", "N2O_Temp", "NitrousTemp"),
            
            # Methanol/Water Injection
            "MethInjectionDuty": ("meth_duty", "meth_injection", "MethDuty", "WaterMethDuty"),
            "MethTankLevel": ("meth_level", "meth_tank", "MethLevel", "WaterMethLevel"),
            "MethFlowRate": ("meth_flow", "MethFlow", "WaterMethFlow"),
            "MethPressure": ("meth_pressure", "MethPressure", "WaterMethPressure"),
            
            # Fuel System
            "FlexFuelPercent": ("flex_fuel", "ethanol_percent", "E85_Percent", "EthanolPercent"),
            "FuelLevel": ("fuel_level", "FuelTankLevel", "fuel_gauge"),
            "InjectorDutyCycle": ("injector_duty", "injector_pulse", "InjectorDuty"),
            
            # Transmission
            "TransBrakeActive": ("trans_brake", "transbrake", "TransBrake", "LineLock"),
            "Gear": ("Current_Gear", "gear", "current_gear", "TransGear"),
            "Current_Gear": ("Gear", "gear", "TransGear"),
            "Clutch_Position": ("clutch", "clutch_pos", "ClutchPosition"),
            "TransTemp": ("trans_temp", "TransmissionTemp", "transmission_temp"),
            
            # Suspension
            "Suspension_FL": ("susp_fl", "front_left_suspension", "SuspensionFrontLeft"),
            "Suspension_FR": ("susp_fr", "front_right_suspension", "SuspensionFrontRight"),
            "Suspension_RL": ("susp_rl", "rear_left_suspension", "SuspensionRearLeft"),
            "Suspension_RR": ("susp_rr", "rear_right_suspension", "SuspensionRearRight"),
            
            # G-Forces
            "GForce_Lateral": ("LatG", "GForce_X", "Lateral_G", "lateral_g", "lat_g"),
            "GForce_Longitudinal": ("LongG", "GForce_Y", "Longitudinal_G", "longitudinal_g", "long_g"),
            "GForce_X": ("GForce_Lateral", "LatG", "lateral_g"),
            "GForce_Y": ("GForce_Longitudinal", "LongG", "longitudinal_g"),
            "Gyro_X": ("gyro_x", "GyroX", "angular_velocity_x"),
            "Gyro_Y": ("gyro_y", "GyroY", "angular_velocity_y"),
            "Gyro_Z": ("gyro_z", "GyroZ", "angular_velocity_z"),
            
            # GPS
            "GPS_Speed": ("gps_speed", "GPS_Speed_mps", "KF_Speed", "kf_speed"),
            "GPS_Heading": ("gps_heading", "heading", "GPS_Heading_deg", "KF_Heading", "kf_heading"),
            "GPS_Altitude": ("gps_altitude", "altitude_m", "GPS_Altitude_m", "altitude"),
            "GPS_Latitude": ("gps_lat", "latitude", "lat", "GPS_Lat"),
            "GPS_Longitude": ("gps_lon", "longitude", "lon", "GPS_Lon"),
            
            # Electrical
            "BatteryVoltage": ("Battery_Voltage", "battery_voltage", "battery_v", "Voltage"),
            "Battery_Voltage": ("BatteryVoltage", "battery_voltage", "battery_v"),
            
            # Braking
            "BrakePressure": ("Brake_Pressure", "brake_pressure", "brake_p"),
            "Brake_Pressure": ("BrakePressure", "brake_pressure", "brake_p"),
            
            # Other
            "Knock_Count": ("KnockCount", "knock_count", "knock", "Knock"),
            "KnockCount": ("Knock_Count", "knock_count", "knock"),
            "Density_Altitude": ("density_altitude", "DA", "density_alt", "DensityAlt"),
        }
        
        # Check aliases
        if name in aliases:
            for alias in aliases[name]:
                if alias in data:
                    return float(data[alias])
        
        # Try case-insensitive search
        name_lower = name.lower()
        for key, value in data.items():
            if key.lower() == name_lower:
                return float(value)
        
        return None
    
    def load_config(self):
        """Load sensor configuration from file."""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Load sensor selections
            if 'sensors' in config_data:
                self._update_sensor_selection(config_data['sensors'])
            
            # Load sensor configs
            if 'sensor_configs' in config_data:
                for name, config_dict in config_data['sensor_configs'].items():
                    if name in self.sensors:
                        config = SensorConfig(**config_dict)
                        self._apply_sensor_config(name, config)
            
            # Load math channels
            if 'math_channels' in config_data:
                for name, mc_dict in config_data['math_channels'].items():
                    math_channel = MathChannel(**mc_dict)
                    self.math_channels[name] = math_channel
        except Exception as e:
            LOGGER.error(f"Failed to load config: {e}", exc_info=True)
    
    def save_config(self):
        """Save sensor configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'sensors': list(self.sensors.keys()),
                'sensor_configs': {
                    name: asdict(sensor_data.config)
                    for name, sensor_data in self.sensors.items()
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            LOGGER.error(f"Failed to save config: {e}", exc_info=True)


__all__ = ["EnhancedTelemetryPanel", "SensorConfig", "SensorData"]

