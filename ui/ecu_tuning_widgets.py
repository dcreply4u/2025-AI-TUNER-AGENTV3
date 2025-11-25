"""
ECU Tuning Interface Widgets
Professional race car engine tuning software components
"""

from __future__ import annotations

import math
from collections import deque
from typing import Dict, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
)

from ui.ui_scaling import get_scaled_size, get_scaled_font_size

try:
    import pyqtgraph as pg
except ImportError:
    pg = None


class AnalogGauge(QWidget):
    """Classic analog-style circular gauge with white face and red needle."""
    
    def __init__(
        self,
        title: str,
        min_value: float,
        max_value: float,
        unit: str = "",
        warning_start: Optional[float] = None,
        warning_end: Optional[float] = None,
        warning_color: str = "#ffaa00",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.unit = unit
        self.warning_start = warning_start
        self.warning_end = warning_end
        self.warning_color = warning_color
        self.current_value = min_value
        # Use scaled sizes for gauges
        min_w = get_scaled_size(180)
        min_h = get_scaled_size(200)
        max_w = get_scaled_size(220)
        max_h = get_scaled_size(240)
        self.setMinimumSize(min_w, min_h)
        self.setMaximumSize(max_w, max_h)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
    def set_value(self, value: float) -> None:
        """Update gauge value."""
        self.current_value = max(self.min_value, min(self.max_value, value))
        self.update()
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw analog gauge with industrial realism."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2 - 10
        radius = min(width, height - 40) // 2 - 10
        
        # Draw dark charcoal background (industrial realism)
        painter.fillRect(self.rect(), QColor("#1a1a1a"))
        
        # Draw beveled border for depth
        bevel_pen = QPen(QColor("#404040"), 2)
        painter.setPen(bevel_pen)
        painter.drawRect(0, 0, width - 1, height - 1)
        
        # Draw slightly recessed white gauge face with subtle shadow
        # Shadow effect
        shadow_offset = 2
        shadow_brush = QBrush(QColor("#000000"))
        painter.setBrush(shadow_brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            center_x - radius + shadow_offset,
            center_y - radius + shadow_offset,
            radius * 2, radius * 2
        )
        
        # Main white face (slightly recessed appearance)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Draw scale marks and numbers (crisp black markings) - scaled
        scale_range = self.max_value - self.min_value
        num_marks = 10
        font_size = get_scaled_font_size(9)
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        painter.setFont(font)
        pen_width = max(1, get_scaled_size(2))
        painter.setPen(QPen(QColor("#000000"), pen_width))  # Crisp, bold markings
        
        for i in range(num_marks + 1):
            value = self.min_value + (i / num_marks) * scale_range
            angle = -135 + (i / num_marks) * 270  # 270 degree arc
            angle_rad = math.radians(angle)
            
            # Draw tick mark
            x1 = center_x + (radius - 5) * math.cos(angle_rad)
            y1 = center_y + (radius - 5) * math.sin(angle_rad)
            x2 = center_x + radius * math.cos(angle_rad)
            y2 = center_y + radius * math.sin(angle_rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # Draw number
            if i % 2 == 0:  # Every other mark
                text = f"{int(value)}"
                if self.unit == "x 1000":
                    text = f"{int(value / 1000)}"
                text_rect = painter.fontMetrics().boundingRect(text)
                text_x = center_x + (radius - 20) * math.cos(angle_rad) - text_rect.width() // 2
                text_y = center_y + (radius - 20) * math.sin(angle_rad) + text_rect.height() // 2
                painter.drawText(int(text_x), int(text_y), text)
        
        # Draw warning zone if specified
        if self.warning_start is not None and self.warning_end is not None:
            start_angle = -135 + ((self.warning_start - self.min_value) / scale_range) * 270
            end_angle = -135 + ((self.warning_end - self.min_value) / scale_range) * 270
            span = end_angle - start_angle
            
            warning_pen = QPen(QColor(self.warning_color), 8)
            painter.setPen(warning_pen)
            painter.drawArc(
                center_x - radius, center_y - radius,
                radius * 2, radius * 2,
                int(start_angle * 16),
                int(span * 16),
            )
        
        # Draw vibrant red needle (thicker, more prominent - racing theme)
        normalized = (self.current_value - self.min_value) / scale_range if scale_range > 0 else 0
        needle_angle = -135 + normalized * 270
        needle_angle_rad = math.radians(needle_angle)
        
        needle_length = radius - 15
        needle_x = center_x + needle_length * math.cos(needle_angle_rad)
        needle_y = center_y + needle_length * math.sin(needle_angle_rad)
        
        # Use racing theme critical color for needle
        needle_pen = QPen(QColor(RacingColor.ACCENT_NEON_RED.value), max(4, get_scaled_size(4)))
        needle_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(needle_pen)
        painter.drawLine(center_x, center_y, int(needle_x), int(needle_y))
        
        # Draw center hub
        painter.setBrush(QBrush(QColor("#000000")))
        painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)
        
        # Draw digital readout (larger, more legible - racing theme)
        readout_font_size = get_scaled_font_size(16)  # Increased from 10 for better legibility
        font = QFont("Segoe UI", readout_font_size, QFont.Weight.Bold)
        painter.setFont(font)
        readout_text = f"{int(self.current_value)}"
        if self.unit:
            readout_text += f" {self.unit}"
        text_rect = painter.fontMetrics().boundingRect(readout_text)
        # Use vibrant accent color for readout
        painter.setPen(QPen(QColor(RacingColor.ACCENT_NEON_BLUE.value)))
        readout_offset = get_scaled_size(25)
        painter.drawText(
            center_x - text_rect.width() // 2,
            center_y + radius + readout_offset,
            readout_text,
        )
        
        # Draw title (scaled)
        title_font_size = get_scaled_font_size(10)
        font = QFont("Arial", title_font_size)
        painter.setFont(font)
        title_rect = painter.fontMetrics().boundingRect(self.title)
        title_offset = get_scaled_size(5)
        painter.drawText(
            center_x - title_rect.width() // 2,
            height - title_offset,
            self.title,
        )


class VETableWidget(QWidget):
    """Volumetric Efficiency table with color-coded cells."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.old_cell_values: Dict[Tuple[int, int], float] = {}  # Track old values for change detection
        self.setup_ui()
        self._initialize_table()
        
        # Connect cell change signal
        self.table.itemChanged.connect(self._on_cell_changed)
        
    def setup_ui(self) -> None:
        """Setup UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title - industrial realism styling
        title = QLabel("Fuel VE Table 1")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Toolbar - industrial realism styling with enhanced tools
        toolbar = QHBoxLayout()
        toolbar.setSpacing(get_scaled_size(10))
        
        # Interpolation buttons
        interp_h_btn = QPushButton("Interp H")
        interp_h_btn.setToolTip("Horizontal Interpolation (Shortcut: Ctrl+H)")
        interp_h_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 4px 8px; font-size: 10px;")
        toolbar.addWidget(interp_h_btn)
        
        interp_v_btn = QPushButton("Interp V")
        interp_v_btn.setToolTip("Vertical Interpolation (Shortcut: Ctrl+V)")
        interp_v_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 4px 8px; font-size: 10px;")
        toolbar.addWidget(interp_v_btn)
        
        # Table smoothing
        smooth_btn = QPushButton("Smooth")
        smooth_btn.setToolTip("Table Smoothing (Shortcut: Ctrl+S)")
        smooth_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 4px 8px; font-size: 10px;")
        toolbar.addWidget(smooth_btn)
        
        # 2D/3D toggle
        self.view_2d3d_btn = QPushButton("2D View")
        self.view_2d3d_btn.setToolTip("Toggle 2D/3D View (Shortcut: V)")
        self.view_2d3d_btn.setCheckable(True)
        self.view_2d3d_btn.setStyleSheet("background-color: #404040; color: #ffffff; padding: 4px 8px; font-size: 10px;")
        self.view_2d3d_btn.clicked.connect(self._toggle_2d3d)
        toolbar.addWidget(self.view_2d3d_btn)
        
        toolbar.addWidget(QLabel("|"))  # Separator
        toolbar.addWidget(QLabel("Cell Weighting:"))
        self.weighting_combo = QComboBox()
        self.weighting_combo.addItems(["None", "Low", "Medium", "High"])
        self.weighting_combo.setStyleSheet("color: #ffffff; background-color: #2a2a2a; padding: 4px; font-size: 10px;")
        toolbar.addWidget(self.weighting_combo)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Store buttons for connections
        self.interp_h_btn = interp_h_btn
        self.interp_v_btn = interp_v_btn
        self.smooth_btn = smooth_btn
        self.is_3d_view = False
        
        # Table - industrial realism styling
        self.table = QTableWidget()
        self.table.setRowCount(16)  # MAP rows
        self.table.setColumnCount(12)  # RPM columns
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(400)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QTableWidget::item {
                padding: 3px;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        layout.addWidget(self.table)
        
    def _initialize_table(self) -> None:
        """Initialize table with default VE values."""
        # RPM headers (columns)
        rpm_values = [800, 1100, 1400, 1700, 2000, 2500, 3000, 3500, 4000, 5000, 6000, 7000]
        for col, rpm in enumerate(rpm_values):
            item = QTableWidgetItem(f"{rpm}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setHorizontalHeaderItem(col, item)
        
        # MAP headers (rows) - descending
        map_values = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25]
        for row, map_val in enumerate(map_values):
            item = QTableWidgetItem(f"{map_val}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setVerticalHeaderItem(row, item)
        
        # Initialize cells with default VE values (simulated)
        import random
        for row in range(16):
            for col in range(12):
                # Generate realistic VE values (typically 30-130)
                ve_value = random.randint(40, 120)
                item = QTableWidgetItem(str(ve_value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)
                self._color_cell(item, ve_value)
        
    def _color_cell(self, item: QTableWidgetItem, value: int) -> None:
        """Color code cell based on VE value - intense saturation for industrial realism."""
        if value < 50:
            color = QColor("#00ff00")  # Intense green for optimal/safe
        elif value < 70:
            color = QColor("#40ff40")  # Bright green
        elif value < 90:
            color = QColor("#0080ff")  # Electric blue for adjustable
        elif value < 110:
            color = QColor("#ff8000")  # Vivid orange for high-load
        else:
            color = QColor("#ff0000")  # Vivid red for critical/high-load
        
        item.setBackground(QBrush(color))
        item.setForeground(QBrush(QColor("#ffffff")))  # White text for high contrast
        
    def _toggle_2d3d(self) -> None:
        """Toggle between 2D and 3D view."""
        self.is_3d_view = not self.is_3d_view
        if self.is_3d_view:
            self.view_2d3d_btn.setText("3D View")
            # TODO: Implement 3D view using pyqtgraph or similar
            print("Switching to 3D view (not yet implemented)")
        else:
            self.view_2d3d_btn.setText("2D View")
            
    def interpolate_horizontal(self) -> None:
        """Perform horizontal interpolation on selected cells."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        # TODO: Implement horizontal interpolation
        print("Horizontal interpolation (not yet implemented)")
        
    def interpolate_vertical(self) -> None:
        """Perform vertical interpolation on selected cells."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        # TODO: Implement vertical interpolation
        print("Vertical interpolation (not yet implemented)")
        
    def smooth_table(self) -> None:
        """Apply table smoothing algorithm."""
        # TODO: Implement table smoothing
        print("Table smoothing (not yet implemented)")
        
    def _on_cell_changed(self, item: QTableWidgetItem) -> None:
        """Handle cell value change and notify config monitor."""
        row = item.row()
        col = item.column()
        
        try:
            new_value = float(item.text())
        except ValueError:
            return
        
        # Get old value
        old_value = self.old_cell_values.get((row, col))
        if old_value is None:
            # First time, just store
            self.old_cell_values[(row, col)] = new_value
            return
        
        # Value changed - notify config monitor
        if abs(new_value - old_value) > 0.1:  # Only notify for significant changes
            try:
                from services.config_change_hook import ConfigChangeHook
                from services.config_version_control import ChangeType, ChangeSeverity
                
                # Get RPM and MAP for this cell
                map_values = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25]
                rpm_values = [800, 1100, 1400, 1700, 2000, 2500, 3000, 3500, 4000, 5000, 6000, 7000]
                
                map_val = map_values[row] if row < len(map_values) else 0
                rpm_val = rpm_values[col] if col < len(rpm_values) else 0
                
                parameter = f"VE[{rpm_val}RPM,{map_val}MAP]"
                
                # Determine severity
                change_pct = abs((new_value - old_value) / old_value * 100) if old_value != 0 else abs(new_value)
                severity = ChangeSeverity.CRITICAL if change_pct > 30 else ChangeSeverity.HIGH if change_pct > 15 else ChangeSeverity.MEDIUM
                
                # Notify config monitor
                hook = ConfigChangeHook.get_instance()
                hook.notify_change(
                    change_type=ChangeType.ECU_TUNING,
                    category="Fuel VE",
                    parameter=parameter,
                    old_value=old_value,
                    new_value=new_value,
                    telemetry=None,  # Could get from parent
                )
            except Exception as e:
                print(f"Error notifying config change: {e}")
        
        # Update stored value
        self.old_cell_values[(row, col)] = new_value
        
        # Update cell color
        self._color_cell(item, int(new_value))
    
    def update_from_telemetry(self, rpm: float, map: float, ve_value: float) -> None:
        """Update table based on current telemetry."""
        # Find closest row/column
        map_values = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25]
        rpm_values = [800, 1100, 1400, 1700, 2000, 2500, 3000, 3500, 4000, 5000, 6000, 7000]
        
        closest_row = min(range(len(map_values)), key=lambda i: abs(map_values[i] - map))
        closest_col = min(range(len(rpm_values)), key=lambda i: abs(rpm_values[i] - rpm))
        
        # Store old value before updating
        item = self.table.item(closest_row, closest_col)
        if item:
            try:
                old_value = float(item.text())
                self.old_cell_values[(closest_row, closest_col)] = old_value
            except (ValueError, AttributeError):
                pass
        
        # Update cell
        if item:
            new_value = int(ve_value)
            item.setText(str(new_value))
            self._color_cell(item, new_value)


class RealTimeGraph(QWidget):
    """Real-time graph panel for engine sensor data."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        self.data_buffers = {
            "rpm": deque(maxlen=1000),
            "map": deque(maxlen=1000),
            "afr": deque(maxlen=1000),
            "ego": deque(maxlen=1000),
        }
        self.x_data = deque(maxlen=1000)
        self.counter = 0
        
    def setup_ui(self) -> None:
        """Setup graph UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        if pg:
            self.plot = pg.PlotWidget()
            self.plot.setBackground("#000000")
            self.plot.setLabel("bottom", "rpm", color="#ffffff")
            self.plot.setLabel("left", "MAP(kPa)", color="#00ff00")
            self.plot.setLabel("right", "AFR(RPM) / egoCorrection(%)", color="#ffffff")
            self.plot.showGrid(x=True, y=True, alpha=0.3)
            
            # Create curves
            self.map_curve = self.plot.plot(
                pen=pg.mkPen("#00ff00", width=2),
                name="MAP",
            )
            self.afr_curve = self.plot.plot(
                pen=pg.mkPen("#ffff00", width=2),
                name="AFR",
            )
            self.ego_curve = self.plot.plot(
                pen=pg.mkPen("#ff0000", width=2),
                name="egoCorrection",
            )
            
            layout.addWidget(self.plot)
        else:
            label = QLabel("pyqtgraph required for real-time graphs")
            label.setStyleSheet("color: #ffffff; background: #000000; padding: 20px;")
            layout.addWidget(label)
            
    def update_data(self, rpm: float, map: float, afr: float, ego: float) -> None:
        """Update graph with new data."""
        if not pg:
            return
            
        self.x_data.append(self.counter)
        self.data_buffers["rpm"].append(rpm)
        self.data_buffers["map"].append(map)
        self.data_buffers["afr"].append(afr)
        self.data_buffers["ego"].append(ego)
        self.counter += 1
        
        if len(self.x_data) > 1:
            self.map_curve.setData(list(self.x_data), list(self.data_buffers["map"]))
            self.afr_curve.setData(list(self.x_data), list(self.data_buffers["afr"]))
            self.ego_curve.setData(list(self.x_data), list(self.data_buffers["ego"]))


class CellWeightingWidget(QWidget):
    """Heat-map style widget for cell weighting visualization."""
    
    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.title = title
        self.setMinimumSize(150, 150)
        self.setMaximumSize(200, 200)
        
    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw heat-map grid."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw title
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#000000")))
        painter.drawText(5, 15, self.title)
        
        # Draw grid
        grid_size = 8
        cell_width = (width - 10) / grid_size
        cell_height = (height - 25) / grid_size
        
        import random
        for row in range(grid_size):
            for col in range(grid_size):
                x = 5 + col * cell_width
                y = 20 + row * cell_height
                
                # Simulate weighting (green to orange gradient)
                weight = random.random()
                if weight < 0.3:
                    color = QColor("#2d5016")  # Dark green
                elif weight < 0.6:
                    color = QColor("#6ba3d8")  # Blue
                else:
                    color = QColor("#ffaa44")  # Orange
                
                painter.fillRect(
                    int(x), int(y),
                    int(cell_width - 1), int(cell_height - 1),
                    QBrush(color),
                )


class StatisticsPanel(QWidget):
    """Statistics display panel."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup statistics UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title = QLabel("VeAnalyze Stats")
        title.setStyleSheet("font-size: 12px; font-weight: bold; color: #000000;")
        layout.addWidget(title)
        
        # Statistics fields
        self.stats = {}
        stat_names = [
            "Total Records", "Total Table Cells", "Average Cell Change",
            "Filtered Records", "Cells Altered", "Max Cell Change",
            "Used Records", "Average Cell Weight", "Active Filter",
        ]
        
        for name in stat_names:
            row = QHBoxLayout()
            label = QLabel(f"{name}:")
            label.setStyleSheet("font-size: 10px; color: #000000;")
            value = QLabel("0")
            value.setStyleSheet("font-size: 10px; color: #000000; font-weight: bold;")
            self.stats[name] = value
            row.addWidget(label)
            row.addWidget(value)
            row.addStretch()
            layout.addLayout(row)
            
    def update_stats(self, stats: Dict[str, str]) -> None:
        """Update statistics display."""
        for name, value in stats.items():
            if name in self.stats:
                self.stats[name].setText(str(value))


__all__ = [
    "AnalogGauge",
    "VETableWidget",
    "RealTimeGraph",
    "CellWeightingWidget",
    "StatisticsPanel",
]
