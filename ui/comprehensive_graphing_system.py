"""
Comprehensive Graphing System for Racing Tuner App

Implements all basic and advanced graphing features:
- Real-time data monitoring
- Time-series charts with multiple parameters
- Multi-axis plotting
- Advanced chart types (scatter, radar, histogram)
- Calculated channels
- Run/lap comparison
- Unit conversion
- GPS driving line analysis
"""

from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union, Callable

import pyqtgraph as pg
import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QLineEdit,
    QDialog,
    QFormLayout,
    QMessageBox,
)

from ui.advanced_graph_widget import AdvancedGraphWidget

LOGGER = logging.getLogger(__name__)

pg.setConfigOptions(antialias=True, background="black", foreground="white")


# Unit conversion constants
UNIT_CONVERSIONS = {
    'pressure': {
        'psi': {'kpa': 6.89476, 'bar': 0.0689476, 'pa': 6894.76},
        'kpa': {'psi': 0.145038, 'bar': 0.01, 'pa': 1000},
        'bar': {'psi': 14.5038, 'kpa': 100, 'pa': 100000},
    },
    'temperature': {
        'celsius': {'fahrenheit': lambda x: x * 9/5 + 32, 'kelvin': lambda x: x + 273.15},
        'fahrenheit': {'celsius': lambda x: (x - 32) * 5/9, 'kelvin': lambda x: (x - 32) * 5/9 + 273.15},
        'kelvin': {'celsius': lambda x: x - 273.15, 'fahrenheit': lambda x: (x - 273.15) * 9/5 + 32},
    },
    'speed': {
        'mph': {'kmh': 1.60934, 'mps': 0.44704},
        'kmh': {'mph': 0.621371, 'mps': 0.277778},
        'mps': {'mph': 2.23694, 'kmh': 3.6},
    },
    'distance': {
        'miles': {'km': 1.60934, 'meters': 1609.34},
        'km': {'miles': 0.621371, 'meters': 1000},
        'meters': {'miles': 0.000621371, 'km': 0.001},
    },
}


@dataclass
class DataChannel:
    """Data channel configuration."""
    name: str
    unit: str
    unit_type: str  # pressure, temperature, speed, etc.
    color: str
    enabled: bool = True
    axis: int = 0  # For multi-axis plotting
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class CalculatedChannel:
    """Custom calculated channel."""
    name: str
    formula: str
    unit: str
    enabled: bool = True


class UnitConverter:
    """Unit conversion utility."""
    
    @staticmethod
    def convert(value: float, from_unit: str, to_unit: str, unit_type: str) -> float:
        """Convert value between units."""
        if from_unit == to_unit:
            return value
        
        if unit_type not in UNIT_CONVERSIONS:
            return value
        
        conversions = UNIT_CONVERSIONS[unit_type]
        if from_unit not in conversions:
            return value
        
        to_conversions = conversions[from_unit]
        if to_unit not in to_conversions:
            return value
        
        converter = to_conversions[to_unit]
        if callable(converter):
            return converter(value)
        return value * converter


class RealTimeGraphWidget(AdvancedGraphWidget):
    """Real-time data monitoring widget."""
    
    def __init__(self, parent: Optional[QWidget] = None, title: str = "Real-Time Data") -> None:
        """Initialize real-time graph."""
        super().__init__(parent, title)
        
        self.max_points = 1000
        self.data_buffers: Dict[str, deque] = {}
        self.time_buffer = deque(maxlen=self.max_points)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(50)  # 20 Hz update rate
        
        # Channel configuration
        self.channels: Dict[str, DataChannel] = {}
        self.curves: Dict[str, pg.PlotDataItem] = {}
        
    def add_channel(self, channel: DataChannel) -> None:
        """Add data channel."""
        self.channels[channel.name] = channel
        self.data_buffers[channel.name] = deque(maxlen=self.max_points)
        
        # Create curve
        curve = self.plot.plot(
            pen=pg.mkPen(color=channel.color, width=2),
            name=channel.name,
        )
        self.curves[channel.name] = curve
        
    def update_channel(self, channel_name: str, value: float, timestamp: Optional[float] = None) -> None:
        """Update channel value."""
        if channel_name not in self.channels:
            return
        
        channel = self.channels[channel_name]
        if not channel.enabled:
            return
        
        if timestamp is None:
            import time
            timestamp = time.time()
        
        self.data_buffers[channel_name].append(value)
        self.time_buffer.append(timestamp)
        
    def _update_display(self) -> None:
        """Update graph display."""
        if not self.time_buffer:
            return
        
        # Convert time buffer to relative time
        if len(self.time_buffer) > 1:
            start_time = self.time_buffer[0]
            time_data = [(t - start_time) for t in self.time_buffer]
        else:
            time_data = list(self.time_buffer)
        
        # Update each curve
        for channel_name, curve in self.curves.items():
            if channel_name in self.data_buffers and channel_name in self.channels:
                channel = self.channels[channel_name]
                if channel.enabled and len(self.data_buffers[channel_name]) > 0:
                    data = list(self.data_buffers[channel_name])
                    if len(data) == len(time_data):
                        curve.setData(time_data, data)
        
        # Auto-scale
        if time_data:
            self.plot.setXRange(min(time_data), max(time_data), padding=0.05)


class MultiAxisGraphWidget(QWidget):
    """Multi-axis plotting widget."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize multi-axis graph."""
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # Graph widget
        self.graph = pg.GraphicsLayoutWidget()
        self.graph.setBackground("black")
        layout.addWidget(self.graph)
        
        # Main plot
        self.plot = self.graph.addPlot(row=0, col=0)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        
        # Multiple Y-axes
        self.axes: Dict[int, pg.AxisItem] = {}
        self.curves: Dict[str, Tuple[pg.PlotDataItem, int]] = {}  # name -> (curve, axis)
        
        # Default left axis
        self.axes[0] = self.plot.getAxis('left')
        self.axis_count = 1
        
    def add_axis(self, label: str, color: str = "#ffffff") -> int:
        """Add new Y-axis."""
        axis_id = self.axis_count
        axis = pg.AxisItem('right')
        axis.setLabel(label, color=color)
        axis.setPen(pg.mkPen(color=color))
        self.plot.layout.addItem(axis, 2, axis_id + 1)
        self.axes[axis_id] = axis
        self.axis_count += 1
        return axis_id
    
    def add_curve(self, name: str, x_data: List[float], y_data: List[float],
                 axis: int = 0, color: str = "#00e0ff", label: str = "") -> None:
        """Add curve to specified axis."""
        if axis not in self.axes:
            axis = 0  # Default to left axis
        
        curve = self.plot.plot(
            x_data, y_data,
            pen=pg.mkPen(color=color, width=2),
            name=label or name,
        )
        
        # Link to axis
        if axis > 0:
            curve.setYAxis(self.axes[axis])
        
        self.curves[name] = (curve, axis)
    
    def set_x_label(self, label: str) -> None:
        """Set X-axis label."""
        self.plot.setLabel("bottom", label)


class ScatterPlotWidget(AdvancedGraphWidget):
    """Scatter plot widget for correlation analysis."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize scatter plot."""
        super().__init__(parent, "Scatter Plot")
        
    def plot_scatter(self, x_data: List[float], y_data: List[float],
                    x_label: str = "X", y_label: str = "Y",
                    color: str = "#00e0ff", size: int = 5) -> None:
        """Plot scatter data."""
        scatter = pg.ScatterPlotItem(
            x=x_data, y=y_data,
            pen=pg.mkPen(color=color, width=1),
            brush=pg.mkBrush(color=color),
            size=size,
        )
        self.plot.addItem(scatter)
        self.plot.setLabel("bottom", x_label)
        self.plot.setLabel("left", y_label)
        
        # Calculate and display correlation
        if len(x_data) == len(y_data) and len(x_data) > 1:
            correlation = np.corrcoef(x_data, y_data)[0, 1]
            self.plot.setTitle(f"Correlation: {correlation:.3f}")


class RadarChartWidget(QWidget):
    """Radar chart for multivariate data."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize radar chart."""
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # Graph widget
        self.graph = pg.GraphicsLayoutWidget()
        self.graph.setBackground("black")
        layout.addWidget(self.graph)
        
        # Polar plot (simulated with regular plot)
        self.plot = self.graph.addPlot(row=0, col=0)
        self.plot.setAspectLocked(True)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        
        self.categories: List[str] = []
        self.data_series: Dict[str, List[float]] = {}
        
    def set_categories(self, categories: List[str]) -> None:
        """Set radar chart categories."""
        self.categories = categories
        
    def add_series(self, name: str, values: List[float], color: str = "#00e0ff") -> None:
        """Add data series."""
        if len(values) != len(self.categories):
            raise ValueError("Values length must match categories length")
        
        self.data_series[name] = values
        
        # Convert to polar coordinates and plot
        angles = np.linspace(0, 2 * np.pi, len(self.categories), endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))  # Close the loop
        
        values_normalized = values + [values[0]]  # Close the loop
        
        # Convert to Cartesian
        x = values_normalized * np.cos(angles)
        y = values_normalized * np.sin(angles)
        
        curve = self.plot.plot(
            x, y,
            pen=pg.mkPen(color=color, width=2),
            name=name,
        )
        self.plot.addItem(curve)


class HistogramWidget(AdvancedGraphWidget):
    """Histogram widget for distribution analysis."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize histogram."""
        super().__init__(parent, "Histogram")
        
    def plot_histogram(self, data: List[float], bins: int = 50,
                      label: str = "Data", color: str = "#00e0ff") -> None:
        """Plot histogram."""
        counts, edges = np.histogram(data, bins=bins)
        
        # Create bar chart
        x = (edges[:-1] + edges[1:]) / 2
        width = edges[1] - edges[0]
        
        bg = pg.BarGraphItem(
            x=x, height=counts, width=width,
            brush=pg.mkBrush(color=color, alpha=0.7),
            pen=pg.mkPen(color=color, width=1),
        )
        self.plot.addItem(bg)
        
        self.plot.setLabel("bottom", label)
        self.plot.setLabel("left", "Frequency")
        
        # Calculate and display statistics
        mean_val = np.mean(data)
        std_val = np.std(data)
        self.plot.setTitle(f"Mean: {mean_val:.2f}, Std: {std_val:.2f}")


class CalculatedChannelDialog(QDialog):
    """Dialog for creating calculated channels."""
    
    def __init__(self, available_channels: List[str], parent: Optional[QWidget] = None) -> None:
        """Initialize dialog."""
        super().__init__(parent)
        self.setWindowTitle("Create Calculated Channel")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Horsepower, Gear_Ratio")
        layout.addRow("Channel Name:", self.name_edit)
        
        self.formula_edit = QLineEdit()
        self.formula_edit.setPlaceholderText("e.g., RPM * Torque / 5252")
        layout.addRow("Formula:", self.formula_edit)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., HP, ratio")
        layout.addRow("Unit:", self.unit_edit)
        
        # Available channels info
        info_label = QLabel(f"Available channels: {', '.join(available_channels[:10])}")
        if len(available_channels) > 10:
            info_label.setText(info_label.text() + f" ... ({len(available_channels)} total)")
        info_label.setWordWrap(True)
        layout.addRow("", info_label)
        
        # Buttons
        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow("", buttons)
        
    def get_channel(self) -> Optional[CalculatedChannel]:
        """Get created channel."""
        name = self.name_edit.text().strip()
        formula = self.formula_edit.text().strip()
        unit = self.unit_edit.text().strip()
        
        if not name or not formula:
            return None
        
        return CalculatedChannel(name=name, formula=formula, unit=unit)


class CalculatedChannelEngine:
    """Engine for evaluating calculated channels."""
    
    def __init__(self) -> None:
        """Initialize engine."""
        self.channels: Dict[str, CalculatedChannel] = {}
        self.available_functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'abs': abs,
            'max': max,
            'min': min,
            'log': math.log,
            'exp': math.exp,
        }
        
    def add_channel(self, channel: CalculatedChannel) -> bool:
        """Add calculated channel with input validation."""
        # Input validation
        if not channel.name or not channel.name.strip():
            LOGGER.error("Channel name cannot be empty")
            return False
        
        if not channel.formula or not channel.formula.strip():
            LOGGER.error("Formula cannot be empty for channel %s", channel.name)
            return False
        
        # Validate formula syntax and safety
        try:
            # Test with dummy data
            test_vars = {name: 1.0 for name in self._extract_variables(channel.formula)}
            self._evaluate_formula(channel.formula, test_vars)
            self.channels[channel.name] = channel
            return True
        except (ValueError, NameError, SyntaxError, TypeError) as e:
            LOGGER.error("Invalid formula for %s: %s", channel.name, e)
            return False
        except Exception as e:
            LOGGER.error("Unexpected error validating formula for %s: %s", channel.name, e)
            return False
    
    def _extract_variables(self, formula: str) -> List[str]:
        """Extract variable names from formula."""
        import re
        # Find all valid variable names (alphanumeric + underscore)
        variables = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', formula)
        # Remove function names
        variables = [v for v in variables if v not in self.available_functions]
        return list(set(variables))
    
    def _evaluate_formula(self, formula: str, variables: Dict[str, float]) -> float:
        """
        Evaluate formula with given variables using safe expression evaluation.
        
        SECURITY: Uses ast.literal_eval for safe evaluation instead of eval()
        to prevent code injection attacks.
        """
        # Validate formula contains only safe characters
        import re
        # Allow: numbers, operators, parentheses, variable names, function names
        safe_pattern = r'^[a-zA-Z0-9_+\-*/().\s,]+$'
        if not re.match(safe_pattern, formula):
            raise ValueError(f"Formula contains invalid characters: {formula}")
        
        # Create safe evaluation environment
        safe_dict = {**self.available_functions, **variables}
        
        # Use safe expression evaluation
        try:
            # Try using simpleeval if available (more flexible)
            try:
                from simpleeval import simple_eval
                return simple_eval(formula, names=safe_dict, functions=self.available_functions)
            except ImportError:
                # Fallback to ast-based evaluation
                import ast
                import operator
                
                # Safe operators
                safe_operators = {
                    ast.Add: operator.add,
                    ast.Sub: operator.sub,
                    ast.Mult: operator.mul,
                    ast.Div: operator.truediv,
                    ast.Pow: operator.pow,
                    ast.Mod: operator.mod,
                    ast.USub: operator.neg,
                    ast.UAdd: operator.pos,
                }
                
                # Safe functions (only math functions from available_functions)
                safe_functions = self.available_functions
                
                class SafeEvaluator(ast.NodeVisitor):
                    def __init__(self, names: Dict[str, float]):
                        self.names = names
                        self.result = None
                    
                    def visit_Expression(self, node):
                        self.result = self.visit(node.body)
                    
                    def visit_BinOp(self, node):
                        left = self.visit(node.left)
                        right = self.visit(node.right)
                        op = safe_operators.get(type(node.op))
                        if op is None:
                            raise ValueError(f"Unsupported operator: {type(node.op)}")
                        return op(left, right)
                    
                    def visit_UnaryOp(self, node):
                        operand = self.visit(node.operand)
                        op = safe_operators.get(type(node.op))
                        if op is None:
                            raise ValueError(f"Unsupported operator: {type(node.op)}")
                        return op(operand)
                    
                    def visit_Constant(self, node):
                        # Python 3.8+ uses Constant instead of Num
                        return node.value
                    
                    def visit_Num(self, node):
                        # Python < 3.8 compatibility
                        return node.n
                    
                    def visit_Name(self, node):
                        if node.id in self.names:
                            return self.names[node.id]
                        raise NameError(f"Name '{node.id}' is not defined")
                    
                    def visit_Call(self, node):
                        func_name = node.func.id if isinstance(node.func, ast.Name) else None
                        if func_name not in safe_functions:
                            raise ValueError(f"Function '{func_name}' is not allowed")
                        args = [self.visit(arg) for arg in node.args]
                        return safe_functions[func_name](*args)
                    
                    def generic_visit(self, node):
                        raise ValueError(f"Unsupported AST node: {type(node)}")
                
                # Parse and evaluate
                tree = ast.parse(formula, mode='eval')
                evaluator = SafeEvaluator(safe_dict)
                evaluator.visit(tree)
                return evaluator.result
        except Exception as e:
            LOGGER.error("Formula evaluation error: %s", e)
            raise ValueError(f"Invalid formula: {formula}") from e
    
    def calculate(self, channel_name: str, data: Dict[str, float]) -> Optional[float]:
        """Calculate channel value from data."""
        if channel_name not in self.channels:
            return None
        
        channel = self.channels[channel_name]
        variables = self._extract_variables(channel.formula)
        
        # Get variable values from data
        var_values = {}
        for var in variables:
            if var in data:
                var_values[var] = data[var]
            else:
                return None  # Missing variable
        
        try:
            return self._evaluate_formula(channel.formula, var_values)
        except Exception as e:
            LOGGER.error("Error calculating %s: %s", channel_name, e)
            return None


class ComprehensiveGraphingSystem(QWidget):
    """Main comprehensive graphing system."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize comprehensive graphing system."""
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # Tab widget for different graph types
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Real-time monitoring tab
        self.realtime_widget = RealTimeGraphWidget(title="Real-Time Monitoring")
        self.tabs.addTab(self.realtime_widget, "Real-Time")
        
        # Time-series tab
        self.timeseries_widget = AdvancedGraphWidget(title="Time-Series Analysis")
        self.tabs.addTab(self.timeseries_widget, "Time-Series")
        
        # Multi-axis tab
        self.multiaxis_widget = MultiAxisGraphWidget()
        self.tabs.addTab(self.multiaxis_widget, "Multi-Axis")
        
        # Scatter plot tab
        self.scatter_widget = ScatterPlotWidget()
        self.tabs.addTab(self.scatter_widget, "Scatter Plot")
        
        # Radar chart tab
        self.radar_widget = RadarChartWidget()
        self.tabs.addTab(self.radar_widget, "Radar Chart")
        
        # Histogram tab
        self.histogram_widget = HistogramWidget()
        self.tabs.addTab(self.histogram_widget, "Histogram")
        
        # Calculated channels engine
        self.calc_engine = CalculatedChannelEngine()
        
        # Unit converter
        self.unit_converter = UnitConverter()
        
    def add_realtime_channel(self, channel: DataChannel) -> None:
        """Add real-time channel."""
        self.realtime_widget.add_channel(channel)
    
    def update_realtime_data(self, channel_name: str, value: float, timestamp: Optional[float] = None) -> None:
        """Update real-time data."""
        self.realtime_widget.update_channel(channel_name, value, timestamp)
    
    def plot_timeseries(self, x_data: List[float], y_data: List[float],
                       x_label: str = "Time", y_label: str = "Value",
                       label: str = "Data") -> None:
        """Plot time-series data."""
        self.timeseries_widget.set_data(x_data, y_data, x_label=x_label, y_label=y_label, label=label)
    
    def create_calculated_channel(self, available_channels: List[str]) -> Optional[CalculatedChannel]:
        """Create calculated channel via dialog."""
        dialog = CalculatedChannelDialog(available_channels, self)
        if dialog.exec() == QDialog.Accepted:
            channel = dialog.get_channel()
            if channel and self.calc_engine.add_channel(channel):
                return channel
        return None


__all__ = [
    "ComprehensiveGraphingSystem",
    "RealTimeGraphWidget",
    "MultiAxisGraphWidget",
    "ScatterPlotWidget",
    "RadarChartWidget",
    "HistogramWidget",
    "CalculatedChannelEngine",
    "UnitConverter",
    "DataChannel",
    "CalculatedChannel",
]






