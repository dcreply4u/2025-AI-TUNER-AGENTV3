"""
Advanced Log Graphing System
Sophisticated graphing features for multi-log comparison and analysis.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QObject
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QLabel, QSlider, QSpinBox, QDoubleSpinBox, QCheckBox,
    QLineEdit, QTextEdit, QTabWidget, QSplitter, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QGroupBox,
    QScrollArea, QFormLayout,
)

from services.multi_log_comparison import MultiLogComparison, AlignmentMethod
from services.universal_log_parser import UniversalLogParser

LOGGER = logging.getLogger(__name__)


class GraphMode(Enum):
    """Graph display mode."""
    TIME = "time"
    DISTANCE = "distance"
    RPM = "rpm"
    CUSTOM = "custom"


@dataclass
class GraphChannel:
    """Graph channel configuration."""
    name: str
    visible: bool = True
    color: str = "#FF0000"
    line_width: float = 2.0
    y_min: Optional[float] = None
    y_max: Optional[float] = None
    unit: str = ""


class AdvancedLogGraphWidget(QWidget):
    """
    Advanced log graphing widget with multi-log support.
    
    Features:
    - Multi-log overlay
    - Synchronized cursors
    - Time/distance alignment
    - Zoom and pan
    - Interactive cursors
    - Customizable channels
    """
    
    cursor_moved = Signal(float)  # Emitted when cursor moves
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize advanced log graph widget."""
        super().__init__(parent)
        
        self.comparison = MultiLogComparison()
        self.channels: Dict[str, GraphChannel] = {}
        self.cursor_position = 0.0
        self.x_min = 0.0
        self.x_max = 10.0
        self.y_min = 0.0
        self.y_max = 100.0
        self.zoom_factor = 1.0
        self.pan_offset = 0.0
        self.graph_mode = GraphMode.TIME
        
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Load log button
        self.load_btn = QPushButton("Load Log")
        self.load_btn.clicked.connect(self._load_log)
        toolbar.addWidget(self.load_btn)
        
        # Alignment controls
        toolbar.addWidget(QLabel("Align:"))
        self.align_combo = QComboBox()
        self.align_combo.addItems(["Time Zero", "Event Start", "Peak Value", "Manual"])
        self.align_combo.currentIndexChanged.connect(self._on_alignment_changed)
        toolbar.addWidget(self.align_combo)
        
        # Zoom controls
        toolbar.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(1, 1000)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        toolbar.addWidget(self.zoom_slider)
        
        # Cursor position display
        self.cursor_label = QLabel("Cursor: 0.00s")
        toolbar.addWidget(self.cursor_label)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Graph area (will be drawn in paintEvent)
        self.setStyleSheet("background-color: #1a1a1a;")
    
    def _load_log(self) -> None:
        """Load a log file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Log File",
            "",
            "Log Files (*.csv *.tsv *.json *.txt *.bin);;All Files (*.*)"
        )
        
        if file_path:
            if self.comparison.load_log(file_path):
                self._update_channels()
                self.update()
                QMessageBox.information(self, "Success", f"Loaded log: {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load log file")
    
    def _update_channels(self) -> None:
        """Update available channels."""
        # Get channels from all loaded logs
        all_channels = set()
        for log in self.comparison.logs:
            if log.visible:
                all_channels.update(log.log_data.data.keys())
        
        # Create graph channels
        for channel_name in all_channels:
            if channel_name not in self.channels:
                self.channels[channel_name] = GraphChannel(name=channel_name)
    
    def _on_alignment_changed(self, index: int) -> None:
        """Handle alignment method change."""
        methods = [
            AlignmentMethod.TIME_ZERO,
            AlignmentMethod.EVENT_START,
            AlignmentMethod.PEAK_VALUE,
            AlignmentMethod.MANUAL,
        ]
        
        if index < len(methods):
            self.comparison.align_logs(methods[index])
            self.update()
    
    def _on_zoom_changed(self, value: int) -> None:
        """Handle zoom change."""
        self.zoom_factor = value / 100.0
        self.update()
    
    def paintEvent(self, event: Any) -> None:
        """Paint the graph."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(26, 26, 26))
        
        # Calculate graph area (with margins)
        margin = 50
        graph_rect = QRectF(
            margin,
            margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin
        )
        
        # Draw grid
        self._draw_grid(painter, graph_rect)
        
        # Draw axes
        self._draw_axes(painter, graph_rect)
        
        # Draw data
        self._draw_data(painter, graph_rect)
        
        # Draw cursor
        self._draw_cursor(painter, graph_rect)
        
        # Draw legend
        self._draw_legend(painter)
    
    def _draw_grid(self, painter: QPainter, rect: QRectF) -> None:
        """Draw grid lines."""
        pen = QPen(QColor(60, 60, 60), 1, Qt.DashLine)
        painter.setPen(pen)
        
        # Vertical lines
        num_v_lines = 10
        for i in range(num_v_lines + 1):
            x = rect.left() + (rect.width() / num_v_lines) * i
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
        
        # Horizontal lines
        num_h_lines = 8
        for i in range(num_h_lines + 1):
            y = rect.top() + (rect.height() / num_h_lines) * i
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
    
    def _draw_axes(self, painter: QPainter, rect: QRectF) -> None:
        """Draw axes with labels."""
        pen = QPen(QColor(200, 200, 200), 2)
        painter.setPen(pen)
        
        # X axis
        painter.drawLine(int(rect.left()), int(rect.bottom()), int(rect.right()), int(rect.bottom()))
        
        # Y axis
        painter.drawLine(int(rect.left()), int(rect.top()), int(rect.left()), int(rect.bottom()))
        
        # Labels
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QColor(200, 200, 200))
        
        # X axis labels
        num_labels = 10
        for i in range(num_labels + 1):
            x = rect.left() + (rect.width() / num_labels) * i
            value = self.x_min + (self.x_max - self.x_min) * (i / num_labels)
            label = f"{value:.1f}"
            painter.drawText(int(x - 20), int(rect.bottom() + 20), 40, 20, Qt.AlignCenter, label)
        
        # Y axis labels
        for i in range(9):
            y = rect.top() + (rect.height() / 8) * i
            value = self.y_max - (self.y_max - self.y_min) * (i / 8)
            label = f"{value:.1f}"
            painter.drawText(0, int(y - 10), int(rect.left() - 10), 20, Qt.AlignRight | Qt.AlignVCenter, label)
    
    def _draw_data(self, painter: QPainter, rect: QRectF) -> None:
        """Draw log data."""
        if not self.comparison.logs:
            return
        
        # Draw each visible channel
        for channel_name, channel_config in self.channels.items():
            if not channel_config.visible:
                continue
            
            # Get aligned data for this channel
            aligned_data = self.comparison.get_aligned_data(channel_name)
            
            if not aligned_data:
                continue
            
            # Draw each log's data
            for log_name, data_points in aligned_data.items():
                if not data_points:
                    continue
                
                # Find log color
                log = next((l for l in self.comparison.logs if l.name == log_name), None)
                if not log or not log.visible:
                    continue
                
                color = QColor(channel_config.color if channel_config.color else log.color)
                pen = QPen(color, channel_config.line_width)
                painter.setPen(pen)
                
                # Draw line
                points = []
                for time, value in data_points:
                    # Map to screen coordinates
                    x = rect.left() + ((time - self.x_min) / (self.x_max - self.x_min)) * rect.width()
                    y = rect.bottom() - ((value - self.y_min) / (self.y_max - self.y_min)) * rect.height()
                    
                    # Clamp to graph area
                    x = max(rect.left(), min(rect.right(), x))
                    y = max(rect.top(), min(rect.bottom(), y))
                    
                    points.append(QPointF(x, y))
                
                # Draw polyline
                if len(points) > 1:
                    for i in range(len(points) - 1):
                        painter.drawLine(points[i], points[i + 1])
    
    def _draw_cursor(self, painter: QPainter, rect: QRectF) -> None:
        """Draw cursor line."""
        # Map cursor position to screen
        x = rect.left() + ((self.cursor_position - self.x_min) / (self.x_max - self.x_min)) * rect.width()
        
        if rect.left() <= x <= rect.right():
            pen = QPen(QColor(255, 255, 0), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
    
    def _draw_legend(self, painter: QPainter) -> None:
        """Draw legend."""
        if not self.comparison.logs:
            return
        
        font = QFont("Arial", 9)
        painter.setFont(font)
        
        x = self.width() - 200
        y = 20
        
        for log in self.comparison.logs:
            if not log.visible:
                continue
            
            # Draw color box
            color = QColor(log.color)
            painter.fillRect(x, y, 15, 15, color)
            
            # Draw name
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(x + 20, y, 150, 15, Qt.AlignLeft | Qt.AlignVCenter, log.name)
            
            y += 20
    
    def mousePressEvent(self, event: Any) -> None:
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            self._update_cursor_from_mouse(event.pos())
    
    def mouseMoveEvent(self, event: Any) -> None:
        """Handle mouse move."""
        if event.buttons() & Qt.LeftButton:
            self._update_cursor_from_mouse(event.pos())
    
    def _update_cursor_from_mouse(self, pos: Any) -> None:
        """Update cursor position from mouse position."""
        margin = 50
        graph_rect = QRectF(
            margin,
            margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin
        )
        
        if graph_rect.contains(pos):
            # Map mouse X to time
            relative_x = (pos.x() - graph_rect.left()) / graph_rect.width()
            self.cursor_position = self.x_min + (self.x_max - self.x_min) * relative_x
            
            # Update label
            self.cursor_label.setText(f"Cursor: {self.cursor_position:.2f}s")
            
            # Emit signal
            self.cursor_moved.emit(self.cursor_position)
            
            # Update comparison cursor
            self.comparison.set_cursor_position(self.cursor_position)
            
            self.update()


class AdvancedLogGraphingWindow(QWidget):
    """
    Complete advanced log graphing window with all features.
    
    Features:
    - Multi-log comparison (up to 15 files)
    - Synchronized cursors
    - Time/distance alignment
    - Customizable chart pages
    - Math channels
    - Interactive table overlays
    - Data analysis tools
    - Export capabilities
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize advanced log graphing window."""
        super().__init__(parent)
        
        self.setWindowTitle("Advanced Log Graphing")
        self.setMinimumSize(1200, 800)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Controls
        left_panel = self._create_control_panel()
        splitter.addWidget(left_panel)
        
        # Center: Graph area
        self.graph_widget = AdvancedLogGraphWidget()
        self.graph_widget.cursor_moved.connect(self._on_cursor_moved)
        splitter.addWidget(self.graph_widget)
        
        # Right panel: Data table
        right_panel = self._create_data_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)
        
        layout.addWidget(splitter)
    
    def _create_control_panel(self) -> QWidget:
        """Create control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Log management
        log_group = QGroupBox("Log Files")
        log_layout = QVBoxLayout()
        
        self.log_list = QComboBox()
        log_layout.addWidget(self.log_list)
        
        load_btn = QPushButton("Load Log")
        load_btn.clicked.connect(self._load_log)
        log_layout.addWidget(load_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_log)
        log_layout.addWidget(remove_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Channel selection
        channel_group = QGroupBox("Channels")
        channel_layout = QVBoxLayout()
        
        self.channel_list = QComboBox()
        channel_layout.addWidget(self.channel_list)
        
        channel_group.setLayout(channel_layout)
        layout.addWidget(channel_group)
        
        # Math channels
        math_group = QGroupBox("Math Channels")
        math_layout = QVBoxLayout()
        
        self.math_name_edit = QLineEdit()
        self.math_name_edit.setPlaceholderText("Channel Name")
        math_layout.addWidget(self.math_name_edit)
        
        self.math_formula_edit = QLineEdit()
        self.math_formula_edit.setPlaceholderText("Formula (e.g., RPM * TPS)")
        math_layout.addWidget(self.math_formula_edit)
        
        add_math_btn = QPushButton("Add Math Channel")
        add_math_btn.clicked.connect(self._add_math_channel)
        math_layout.addWidget(add_math_btn)
        
        math_group.setLayout(math_layout)
        layout.addWidget(math_group)
        
        # Chart pages
        page_group = QGroupBox("Chart Pages")
        page_layout = QVBoxLayout()
        
        self.page_combo = QComboBox()
        self.page_combo.addItem("Default")
        page_layout.addWidget(self.page_combo)
        
        page_group.setLayout(page_layout)
        layout.addWidget(page_group)
        
        layout.addStretch()
        return panel
    
    def _create_data_panel(self) -> QWidget:
        """Create data panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Cursor values table
        table_group = QGroupBox("Cursor Values")
        table_layout = QVBoxLayout()
        
        self.value_table = QTableWidget()
        self.value_table.setColumnCount(3)
        self.value_table.setHorizontalHeaderLabels(["Log", "Channel", "Value"])
        table_layout.addWidget(self.value_table)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Analysis tools
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QVBoxLayout()
        
        self.range_start_edit = QDoubleSpinBox()
        self.range_start_edit.setDecimals(2)
        analysis_layout.addWidget(QLabel("Start:"))
        analysis_layout.addWidget(self.range_start_edit)
        
        self.range_end_edit = QDoubleSpinBox()
        self.range_end_edit.setDecimals(2)
        analysis_layout.addWidget(QLabel("End:"))
        analysis_layout.addWidget(self.range_end_edit)
        
        analyze_btn = QPushButton("Analyze Range")
        analyze_btn.clicked.connect(self._analyze_range)
        analysis_layout.addWidget(analyze_btn)
        
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(4)
        self.analysis_table.setHorizontalHeaderLabels(["Log", "Channel", "Min", "Max", "Avg"])
        analysis_layout.addWidget(self.analysis_table)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # Export
        export_btn = QPushButton("Export Data")
        export_btn.clicked.connect(self._export_data)
        layout.addWidget(export_btn)
        
        layout.addStretch()
        return panel
    
    def _load_log(self) -> None:
        """Load a log file."""
        self.graph_widget._load_log()
        self._update_log_list()
    
    def _remove_log(self) -> None:
        """Remove selected log."""
        index = self.log_list.currentIndex()
        if index >= 0:
            self.graph_widget.comparison.remove_log(index)
            self._update_log_list()
            self.graph_widget.update()
    
    def _update_log_list(self) -> None:
        """Update log list."""
        self.log_list.clear()
        for log in self.graph_widget.comparison.logs:
            self.log_list.addItem(log.name)
    
    def _add_math_channel(self) -> None:
        """Add math channel."""
        name = self.math_name_edit.text()
        formula = self.math_formula_edit.text()
        
        if name and formula:
            if self.graph_widget.comparison.add_math_channel(name, formula):
                QMessageBox.information(self, "Success", f"Added math channel: {name}")
                self.math_name_edit.clear()
                self.math_formula_edit.clear()
            else:
                QMessageBox.warning(self, "Error", "Failed to add math channel")
    
    def _on_cursor_moved(self, position: float) -> None:
        """Handle cursor movement."""
        # Get values at cursor
        result = self.graph_widget.comparison.get_cursor_values()
        
        # Update table
        self.value_table.setRowCount(0)
        
        for log_name, values in result.values.items():
            for channel, value in values.items():
                row = self.value_table.rowCount()
                self.value_table.insertRow(row)
                self.value_table.setItem(row, 0, QTableWidgetItem(log_name))
                self.value_table.setItem(row, 1, QTableWidgetItem(channel))
                self.value_table.setItem(row, 2, QTableWidgetItem(f"{value:.2f}"))
    
    def _analyze_range(self) -> None:
        """Analyze data range."""
        start = self.range_start_edit.value()
        end = self.range_end_edit.value()
        
        if start >= end:
            QMessageBox.warning(self, "Error", "Start must be less than end")
            return
        
        # Analyze
        result = self.graph_widget.comparison.analyze_range(start, end)
        
        # Update table
        self.analysis_table.setRowCount(0)
        
        for log_name, channels in result.items():
            for channel, stats in channels.items():
                row = self.analysis_table.rowCount()
                self.analysis_table.insertRow(row)
                self.analysis_table.setItem(row, 0, QTableWidgetItem(log_name))
                self.analysis_table.setItem(row, 1, QTableWidgetItem(channel))
                self.analysis_table.setItem(row, 2, QTableWidgetItem(f"{stats['min']:.2f}"))
                self.analysis_table.setItem(row, 3, QTableWidgetItem(f"{stats['max']:.2f}"))
                self.analysis_table.setItem(row, 4, QTableWidgetItem(f"{stats['avg']:.2f}"))
    
    def _export_data(self) -> None:
        """Export data."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if file_path:
            format = "csv" if file_path.endswith(".csv") else "json"
            if self.graph_widget.comparison.export_comparison(file_path, format):
                QMessageBox.information(self, "Success", f"Exported to {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to export data")


