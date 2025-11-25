"""
Dashboard Tab
Customizable dashboard where users can add individual widgets (gauges, graphs, logs)
Each user can have their own dashboard configuration
"""

from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QGridLayout,
    QFileDialog,
    QMessageBox,
    QMenu,
    QSizePolicy,
    QSplitter,
)

from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QColor, QBrush, QPen

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

from ui.ecu_tuning_widgets import AnalogGauge, RealTimeGraph
from ui.telemetryiq_widgets import EnhancedGraphPanel

try:
    import pyqtgraph as pg
except ImportError:
    pg = None


class DashboardWidget(QWidget):
    """Base class for dashboard widgets."""
    
    widget_removed = Signal(QWidget)
    
    def __init__(self, widget_type: str, widget_id: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.widget_type = widget_type
        self.widget_id = widget_id
        self.setup_widget()
        
    def setup_widget(self) -> None:
        """Setup widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title bar with remove button
        title_bar = QHBoxLayout()
        title = QLabel(f"{self.widget_type} - {self.widget_id}")
        title_font = get_scaled_font_size(10)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        title_bar.addWidget(title)
        
        title_bar.addStretch()
        
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(get_scaled_size(20), get_scaled_size(20))
        remove_btn.setStyleSheet("background-color: #ff0000; color: #ffffff; font-weight: bold; border: none;")
        remove_btn.clicked.connect(lambda: self.widget_removed.emit(self))
        title_bar.addWidget(remove_btn)
        
        layout.addLayout(title_bar)
        
        # Widget content area
        self.content_widget = self._create_content()
        if self.content_widget:
            layout.addWidget(self.content_widget, stretch=1)
            
    def _create_content(self) -> Optional[QWidget]:
        """Create widget-specific content. Override in subclasses."""
        return None
        
    def get_config(self) -> Dict[str, Any]:
        """Get widget configuration for saving."""
        return {
            "type": self.widget_type,
            "id": self.widget_id,
        }
        
    def update_data(self, data: Dict[str, float]) -> None:
        """Update widget with telemetry data. Override in subclasses."""
        pass


class GaugeWidget(DashboardWidget):
    """Gauge widget for dashboard."""
    
    def __init__(self, widget_id: str, gauge_config: Optional[Dict] = None, parent: Optional[QWidget] = None) -> None:
        self.gauge_config = gauge_config or {}
        super().__init__("Gauge", widget_id, parent)
        
    def _create_content(self) -> Optional[QWidget]:
        """Create gauge content."""
        title = self.gauge_config.get("title", "RPM")
        min_val = self.gauge_config.get("min_value", 0)
        max_val = self.gauge_config.get("max_value", 8000)
        unit = self.gauge_config.get("unit", "RPM")
        
        self.gauge = AnalogGauge(
            title,
            min_value=min_val,
            max_value=max_val,
            unit=unit,
        )
        return self.gauge
        
    def update_data(self, data: Dict[str, float]) -> None:
        """Update gauge with telemetry data."""
        if hasattr(self, 'gauge'):
            data_key = self.gauge_config.get("data_key", "RPM")
            value = data.get(data_key, data.get("RPM", 0))
            self.gauge.set_value(value)
            
    def get_config(self) -> Dict[str, Any]:
        """Get gauge configuration."""
        config = super().get_config()
        config.update(self.gauge_config)
        return config


class GraphWidget(DashboardWidget):
    """Graph widget for dashboard."""
    
    def __init__(self, widget_id: str, graph_config: Optional[Dict] = None, parent: Optional[QWidget] = None) -> None:
        self.graph_config = graph_config or {}
        super().__init__("Graph", widget_id, parent)
        
    def _create_content(self) -> Optional[QWidget]:
        """Create graph content."""
        if pg:
            self.plot = pg.PlotWidget()
            self.plot.setBackground("#000000")
            self.plot.showGrid(x=True, y=True, alpha=0.3)
            
            # Create curves based on config
            self.curves = {}
            data_keys = self.graph_config.get("data_keys", ["RPM"])
            colors = ["#00ff00", "#0080ff", "#ff8000", "#ff0000"]
            
            for i, key in enumerate(data_keys):
                color = colors[i % len(colors)]
                curve = self.plot.plot(pen=pg.mkPen(color, width=2), name=key)
                self.curves[key] = curve
                
            self.plot.setLabel("bottom", "Time", color="#ffffff")
            self.plot.setLabel("left", "Value", color="#ffffff")
            
            # Data buffers
            self.data_buffers = {key: [] for key in data_keys}
            self.time_buffer = []
            self.max_points = 1000
            
            return self.plot
        else:
            placeholder = QLabel("Graph widget (pyqtgraph not available)")
            placeholder.setStyleSheet("color: #ffffff; padding: 20px;")
            return placeholder
            
    def update_data(self, data: Dict[str, float]) -> None:
        """Update graph with telemetry data."""
        if not pg or not hasattr(self, 'curves'):
            return
            
        data_keys = self.graph_config.get("data_keys", ["RPM"])
        
        for key in data_keys:
            value = data.get(key, 0)
            if key in self.data_buffers:
                self.data_buffers[key].append(value)
                if len(self.data_buffers[key]) > self.max_points:
                    self.data_buffers[key].pop(0)
                    
        # Update time buffer
        if not self.time_buffer:
            self.time_buffer = [0]
        else:
            self.time_buffer.append(self.time_buffer[-1] + 0.1)
            if len(self.time_buffer) > self.max_points:
                self.time_buffer.pop(0)
                
        # Update curves
        for key, curve in self.curves.items():
            if key in self.data_buffers and len(self.data_buffers[key]) > 0:
                curve.setData(self.time_buffer[:len(self.data_buffers[key])], self.data_buffers[key])
                
    def get_config(self) -> Dict[str, Any]:
        """Get graph configuration."""
        config = super().get_config()
        config.update(self.graph_config)
        return config


class LogWidget(DashboardWidget):
    """Log widget for dashboard."""
    
    def __init__(self, widget_id: str, log_config: Optional[Dict] = None, parent: Optional[QWidget] = None) -> None:
        self.log_config = log_config or {}
        super().__init__("Log", widget_id, parent)
        
    def _create_content(self) -> Optional[QWidget]:
        """Create log content."""
        from PySide6.QtWidgets import QTextEdit
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                color: #00ff00;
                border: 1px solid #404040;
                font-family: 'Courier New', monospace;
            }
        """)
        self.log_text.setMaximumBlockCount(1000)  # Limit log entries
        
        return self.log_text
        
    def update_data(self, data: Dict[str, float]) -> None:
        """Update log with telemetry data."""
        if hasattr(self, 'log_text'):
            data_keys = self.log_config.get("data_keys", ["RPM", "Speed"])
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            values = []
            for key in data_keys:
                value = data.get(key, 0)
                values.append(f"{key}: {value:.2f}")
                
            log_line = f"[{timestamp}] {' | '.join(values)}\n"
            self.log_text.append(log_line)
            
    def get_config(self) -> Dict[str, Any]:
        """Get log configuration."""
        config = super().get_config()
        config.update(self.log_config)
        return config


class DashboardTab(QWidget):
    """Customizable dashboard tab with widget management."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.widgets: Dict[str, DashboardWidget] = {}
        self.widget_counter = 0
        self.current_user = "default"
        self.dashboard_configs_dir = Path("configs/dashboards")
        self.dashboard_configs_dir.mkdir(parents=True, exist_ok=True)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup dashboard tab UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Widget library
        widget_library = self._create_widget_library()
        splitter.addWidget(widget_library)
        
        # Center: Dashboard canvas
        dashboard_canvas = self._create_dashboard_canvas()
        splitter.addWidget(dashboard_canvas)
        
        # Right: Properties/Configuration
        properties_panel = self._create_properties_panel()
        splitter.addWidget(properties_panel)
        
        # Set splitter sizes
        splitter.setSizes([get_scaled_size(200), get_scaled_size(800), get_scaled_size(250)])
        
        main_layout.addWidget(splitter, stretch=1)
        
        # Import bar (export already exists in control bar)
        from ui.module_feature_helper import add_import_export_bar
        add_import_export_bar(self, main_layout)
        
    def _create_control_bar(self) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        padding = get_scaled_size(5)
        border = get_scaled_size(1)
        bar.setStyleSheet(f"background-color: #2a2a2a; padding: {padding}px; border: {border}px solid #404040;")
        layout = QHBoxLayout(bar)
        margin_h = get_scaled_size(10)
        margin_v = get_scaled_size(5)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        title = QLabel("Custom Dashboard")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # User selection
        layout.addWidget(QLabel("User:"))
        self.user_combo = QComboBox()
        self.user_combo.addItems(["default", "user1", "user2", "user3"])
        self.user_combo.setCurrentText(self.current_user)
        self.user_combo.currentTextChanged.connect(self._on_user_changed)
        self.user_combo.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 4px;")
        layout.addWidget(self.user_combo)
        
        # Save button
        save_btn = QPushButton("Save Dashboard")
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font = get_scaled_font_size(11)
        save_btn.setStyleSheet(f"background-color: #0080ff; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        save_btn.clicked.connect(self._save_dashboard)
        layout.addWidget(save_btn)
        
        # Load button
        load_btn = QPushButton("Load Dashboard")
        load_btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        load_btn.clicked.connect(self._load_dashboard)
        layout.addWidget(load_btn)
        
        # Export button
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(f"background-color: #00ff00; color: #000000; padding: {btn_padding_v}px {btn_padding_h}px; font-weight: bold; font-size: {btn_font}px;")
        export_btn.clicked.connect(self._export_dashboard)
        layout.addWidget(export_btn)
        
        return bar
        
    def _create_widget_library(self) -> QWidget:
        """Create widget library panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Widget Library")
        title_font = get_scaled_font_size(12)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Available widgets list
        self.widget_library = QListWidget()
        self.widget_library.setStyleSheet("""
            QListWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #404040;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
        """)
        
        # Add available widget types
        widget_types = [
            "Gauge - RPM",
            "Gauge - Speed",
            "Gauge - Boost",
            "Gauge - AFR",
            "Gauge - MAP",
            "Graph - Multi-line",
            "Graph - RPM vs Time",
            "Graph - Boost vs Time",
            "Log - Telemetry",
            "Log - Errors",
        ]
        
        for widget_type in widget_types:
            item = QListWidgetItem(widget_type)
            self.widget_library.addItem(item)
            
        self.widget_library.itemDoubleClicked.connect(self._add_widget_from_library)
        layout.addWidget(self.widget_library)
        
        # Add widget button
        add_btn = QPushButton("Add Selected Widget")
        add_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 5px;")
        add_btn.clicked.connect(self._add_widget_from_library)
        layout.addWidget(add_btn)
        
        return panel
        
    def _create_dashboard_canvas(self) -> QWidget:
        """Create dashboard canvas where widgets are placed."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #0a0a0a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Dashboard Canvas")
        title_font = get_scaled_font_size(12)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Scrollable canvas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #0a0a0a; border: none;")
        
        self.canvas = QWidget()
        self.canvas_layout = QGridLayout(self.canvas)
        self.canvas_layout.setSpacing(get_scaled_size(10))
        self.canvas.setStyleSheet("background-color: #0a0a0a;")
        
        scroll.setWidget(self.canvas)
        layout.addWidget(scroll, stretch=1)
        
        return panel
        
    def _create_properties_panel(self) -> QWidget:
        """Create properties/configuration panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(300))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Widget Properties")
        title_font = get_scaled_font_size(12)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Properties will be shown here when widget is selected
        self.properties_label = QLabel("Select a widget to edit properties")
        self.properties_label.setStyleSheet("color: #9aa0a6; padding: 10px;")
        self.properties_label.setWordWrap(True)
        layout.addWidget(self.properties_label)
        
        layout.addStretch()
        
        return panel
        
    def _add_widget_from_library(self) -> None:
        """Add widget from library to dashboard."""
        current_item = self.widget_library.currentItem()
        if not current_item:
            return
            
        widget_name = current_item.text()
        self._add_widget_by_name(widget_name)
        
    def _add_widget_by_name(self, widget_name: str) -> None:
        """Add widget by name."""
        self.widget_counter += 1
        widget_id = f"{widget_name.replace(' ', '_')}_{self.widget_counter}"
        
        if "Gauge" in widget_name:
            config = self._get_gauge_config(widget_name)
            widget = GaugeWidget(widget_id, config, self.canvas)
        elif "Graph" in widget_name:
            config = self._get_graph_config(widget_name)
            widget = GraphWidget(widget_id, config, self.canvas)
        elif "Log" in widget_name:
            config = self._get_log_config(widget_name)
            widget = LogWidget(widget_id, config, self.canvas)
        else:
            return
            
        widget.widget_removed.connect(self._remove_widget)
        widget.setMinimumSize(get_scaled_size(200), get_scaled_size(150))
        
        # Add to grid layout (auto-position)
        row = len(self.widgets) // 3
        col = len(self.widgets) % 3
        self.canvas_layout.addWidget(widget, row, col)
        
        self.widgets[widget_id] = widget
        
    def _get_gauge_config(self, widget_name: str) -> Dict:
        """Get gauge configuration based on name."""
        configs = {
            "Gauge - RPM": {"title": "RPM", "min_value": 0, "max_value": 8000, "unit": "RPM", "data_key": "RPM"},
            "Gauge - Speed": {"title": "Speed", "min_value": 0, "max_value": 200, "unit": "mph", "data_key": "Speed"},
            "Gauge - Boost": {"title": "Boost", "min_value": 0, "max_value": 50, "unit": "psi", "data_key": "Boost_Pressure"},
            "Gauge - AFR": {"title": "AFR", "min_value": 10, "max_value": 18, "unit": "", "data_key": "AFR"},
            "Gauge - MAP": {"title": "MAP", "min_value": -80, "max_value": 240, "unit": "kPa", "data_key": "MAP"},
        }
        return configs.get(widget_name, configs["Gauge - RPM"])
        
    def _get_graph_config(self, widget_name: str) -> Dict:
        """Get graph configuration based on name."""
        configs = {
            "Graph - Multi-line": {"data_keys": ["RPM", "Speed", "Boost_Pressure"]},
            "Graph - RPM vs Time": {"data_keys": ["RPM"]},
            "Graph - Boost vs Time": {"data_keys": ["Boost_Pressure"]},
        }
        return configs.get(widget_name, configs["Graph - Multi-line"])
        
    def _get_log_config(self, widget_name: str) -> Dict:
        """Get log configuration based on name."""
        configs = {
            "Log - Telemetry": {"data_keys": ["RPM", "Speed", "Boost_Pressure", "AFR"]},
            "Log - Errors": {"data_keys": ["Error_Code", "Error_Message"]},
        }
        return configs.get(widget_name, configs["Log - Telemetry"])
        
    def _remove_widget(self, widget: DashboardWidget) -> None:
        """Remove widget from dashboard."""
        widget_id = widget.widget_id
        if widget_id in self.widgets:
            self.widgets[widget_id].deleteLater()
            del self.widgets[widget_id]
            
    def _on_user_changed(self, user: str) -> None:
        """Handle user change."""
        self.current_user = user
        # Optionally auto-load user's dashboard
        # self._load_dashboard()
        
    def _save_dashboard(self) -> None:
        """Save current dashboard configuration."""
        config = {
            "user": self.current_user,
            "timestamp": datetime.now().isoformat(),
            "widgets": []
        }
        
        # Get widget configurations
        for widget_id, widget in self.widgets.items():
            widget_config = widget.get_config()
            # Get grid position
            index = self.canvas_layout.indexOf(widget)
            if index >= 0:
                row, col, row_span, col_span = self.canvas_layout.getItemPosition(index)
                widget_config["position"] = {"row": row, "col": col}
            config["widgets"].append(widget_config)
            
        # Save to file
        config_file = self.dashboard_configs_dir / f"{self.current_user}_dashboard.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            QMessageBox.information(self, "Saved", f"Dashboard saved for user: {self.current_user}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save dashboard: {e}")
            
    def _load_dashboard(self) -> None:
        """Load dashboard configuration."""
        config_file = self.dashboard_configs_dir / f"{self.current_user}_dashboard.json"
        
        if not config_file.exists():
            QMessageBox.information(self, "Not Found", f"No saved dashboard found for user: {self.current_user}")
            return
            
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            # Clear existing widgets
            for widget in list(self.widgets.values()):
                widget.deleteLater()
            self.widgets.clear()
            
            # Load widgets
            for widget_config in config.get("widgets", []):
                widget_type = widget_config.get("type")
                widget_id = widget_config.get("id", f"widget_{len(self.widgets)}")
                
                if widget_type == "Gauge":
                    widget = GaugeWidget(widget_id, widget_config, self.canvas)
                elif widget_type == "Graph":
                    widget = GraphWidget(widget_id, widget_config, self.canvas)
                elif widget_type == "Log":
                    widget = LogWidget(widget_id, widget_config, self.canvas)
                else:
                    continue
                    
                widget.widget_removed.connect(self._remove_widget)
                
                # Restore position
                position = widget_config.get("position", {})
                row = position.get("row", len(self.widgets) // 3)
                col = position.get("col", len(self.widgets) % 3)
                self.canvas_layout.addWidget(widget, row, col)
                
                self.widgets[widget_id] = widget
                
            QMessageBox.information(self, "Loaded", f"Dashboard loaded for user: {self.current_user}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load dashboard: {e}")
            
    def _export_dashboard(self) -> None:
        """Export dashboard data to multiple file formats."""
        menu = QMenu(self)
        
        json_action = menu.addAction("Export as JSON")
        csv_action = menu.addAction("Export as CSV")
        pdf_action = menu.addAction("Export as PDF (Coming Soon)")
        txt_action = menu.addAction("Export as Text Log")
        
        action = menu.exec(self.mapToGlobal(self.sender().pos()) if hasattr(self, 'sender') else self.mapToGlobal(self.rect().topRight()))
        
        if action == json_action:
            self._export_json()
        elif action == csv_action:
            self._export_csv()
        elif action == txt_action:
            self._export_txt()
        elif action == pdf_action:
            QMessageBox.information(self, "Coming Soon", "PDF export will be available in a future update")
            
    def _export_json(self) -> None:
        """Export dashboard data as JSON."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Dashboard as JSON",
            f"{self.current_user}_dashboard_export.json",
            "JSON Files (*.json);;All Files (*)"
        )
        if not filename:
            return
            
        export_data = {
            "user": self.current_user,
            "export_timestamp": datetime.now().isoformat(),
            "widgets": []
        }
        
        for widget_id, widget in self.widgets.items():
            widget_data = widget.get_config()
            # Get current data if available
            if hasattr(widget, 'gauge'):
                widget_data["current_value"] = widget.gauge.current_value
            elif hasattr(widget, 'data_buffers'):
                widget_data["data_samples"] = {k: v[-100:] for k, v in widget.data_buffers.items()}
            elif hasattr(widget, 'log_text'):
                widget_data["log_content"] = widget.log_text.toPlainText()
            export_data["widgets"].append(widget_data)
            
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            QMessageBox.information(self, "Exported", f"Dashboard exported to: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")
            
    def _export_csv(self) -> None:
        """Export dashboard data as CSV."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Dashboard as CSV",
            f"{self.current_user}_dashboard_export.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not filename:
            return
            
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Widget ID", "Type", "Title/Name", "Data Key", "Current Value", "Timestamp"])
                
                for widget_id, widget in self.widgets.items():
                    config = widget.get_config()
                    widget_type = config.get("type", "Unknown")
                    title = config.get("title", config.get("id", "Unknown"))
                    data_key = config.get("data_key", "N/A")
                    
                    current_value = "N/A"
                    if hasattr(widget, 'gauge'):
                        current_value = widget.gauge.current_value
                    elif hasattr(widget, 'data_buffers'):
                        # Get latest values
                        current_value = ", ".join([f"{k}:{v[-1] if v else 0}" for k, v in widget.data_buffers.items()])
                    elif hasattr(widget, 'log_text'):
                        current_value = f"{len(widget.log_text.toPlainText().splitlines())} lines"
                        
                    writer.writerow([
                        widget_id,
                        widget_type,
                        title,
                        data_key,
                        current_value,
                        datetime.now().isoformat()
                    ])
                    
            QMessageBox.information(self, "Exported", f"Dashboard exported to: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")
            
    def _export_txt(self) -> None:
        """Export dashboard data as text log."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Dashboard as Text",
            f"{self.current_user}_dashboard_export.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        if not filename:
            return
            
        try:
            with open(filename, 'w') as f:
                f.write(f"Dashboard Export - User: {self.current_user}\n")
                f.write(f"Export Timestamp: {datetime.now().isoformat()}\n")
                f.write("=" * 60 + "\n\n")
                
                for widget_id, widget in self.widgets.items():
                    config = widget.get_config()
                    f.write(f"Widget: {widget_id}\n")
                    f.write(f"  Type: {config.get('type', 'Unknown')}\n")
                    f.write(f"  Title: {config.get('title', config.get('id', 'Unknown'))}\n")
                    
                    if hasattr(widget, 'gauge'):
                        f.write(f"  Current Value: {widget.gauge.current_value}\n")
                    elif hasattr(widget, 'log_text'):
                        f.write(f"  Log Content:\n{widget.log_text.toPlainText()}\n")
                    f.write("\n")
                    
            QMessageBox.information(self, "Exported", f"Dashboard exported to: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")
            
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update all dashboard widgets with telemetry data."""
        for widget in self.widgets.values():
            try:
                widget.update_data(data)
            except Exception:
                pass


__all__ = ["DashboardTab"]



