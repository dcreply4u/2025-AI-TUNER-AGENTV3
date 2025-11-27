"""
Advanced Graph Features - X-Y plots, FFT, Histograms, Math Channels, etc.
"""

from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Callable, Any

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget, PlotDataItem
    PG_AVAILABLE = True
except ImportError:
    pg = None
    PG_AVAILABLE = False

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QLineEdit,
    QDialog,
    QFormLayout,
    QTextEdit,
    QMessageBox,
    QTabWidget,
    QGroupBox,
    QCheckBox,
    QDoubleSpinBox,
    QSpinBox,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class MathChannel:
    """Custom calculated math channel."""
    name: str
    formula: str
    unit: str = ""
    enabled: bool = True
    color: str = "#ff00ff"
    
    def evaluate(self, sensor_data: Dict[str, List[float]]) -> Optional[List[float]]:
        """Evaluate formula using sensor data."""
        try:
            # Create safe evaluation context
            safe_dict = {
                "__builtins__": {},
                "abs": abs,
                "min": min,
                "max": max,
                "sum": sum,
                "len": len,
                "math": math,
            }
            
            # Add sensor data as variables (use first available length)
            if not sensor_data:
                return None
            
            # Get common length
            lengths = [len(v) for v in sensor_data.values() if v]
            if not lengths:
                return None
            
            common_len = min(lengths)
            
            # Evaluate for each index
            result = []
            for i in range(common_len):
                # Create context for this index
                context = safe_dict.copy()
                for sensor_name, values in sensor_data.items():
                    if i < len(values):
                        # Use sanitized variable name
                        var_name = sensor_name.replace(" ", "_").replace("-", "_")
                        context[var_name] = values[i]
                
                try:
                    value = eval(self.formula, context)
                    result.append(float(value))
                except Exception:
                    result.append(0.0)
            
            return result
        except Exception as e:
            LOGGER.error(f"Error evaluating math channel {self.name}: {e}")
            return None


class MathChannelDialog(QDialog):
    """Dialog for creating/editing math channels."""
    
    def __init__(self, available_sensors: List[str], existing_channel: Optional[MathChannel] = None, parent=None):
        super().__init__(parent)
        self.available_sensors = available_sensors
        self.existing_channel = existing_channel
        self.setWindowTitle("Math Channel Editor" if existing_channel else "Create Math Channel")
        self.setMinimumWidth(600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit()
        if self.existing_channel:
            self.name_edit.setText(self.existing_channel.name)
        form.addRow("Channel Name:", self.name_edit)
        
        # Formula
        formula_label = QLabel("Formula (Python syntax, use sensor names as variables):")
        self.formula_edit = QTextEdit()
        self.formula_edit.setMaximumHeight(100)
        if self.existing_channel:
            self.formula_edit.setText(self.existing_channel.formula)
        self.formula_edit.setPlaceholderText("Example: Engine_RPM * Throttle_Position / 100")
        form.addRow(formula_label, self.formula_edit)
        
        # Available sensors helper
        sensors_label = QLabel("Available Sensors:")
        sensors_text = QLabel(", ".join(self.available_sensors[:20]) + ("..." if len(self.available_sensors) > 20 else ""))
        sensors_text.setWordWrap(True)
        form.addRow(sensors_label, sensors_text)
        
        # Unit
        self.unit_edit = QLineEdit()
        if self.existing_channel:
            self.unit_edit.setText(self.existing_channel.unit)
        form.addRow("Unit:", self.unit_edit)
        
        # Color
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 30)
        color = self.existing_channel.color if self.existing_channel else "#ff00ff"
        self.color_btn.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
        self.color_btn.clicked.connect(self._pick_color)
        self.color = color
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        form.addRow("Color:", color_layout)
        
        layout.addLayout(form)
        
        # Examples
        examples_group = QGroupBox("Formula Examples")
        examples_layout = QVBoxLayout()
        examples = [
            "Power = Engine_RPM * Torque / 5252",
            "SlipAngle = atan(Lateral_G * 9.81 / (Speed * 0.447))",
            "Load = (Boost_Pressure + 14.7) / 14.7",
            "Efficiency = (Speed * 0.447) / (Engine_RPM / 60) * GearRatio",
        ]
        for example in examples:
            example_label = QLabel(f"• {example}")
            example_label.setStyleSheet("color: #666; font-family: monospace;")
            examples_layout.addWidget(example_label)
        examples_group.setLayout(examples_layout)
        layout.addWidget(examples_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        test_btn = QPushButton("Test Formula")
        test_btn.clicked.connect(self._test_formula)
        button_layout.addWidget(test_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _pick_color(self):
        """Open color picker."""
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        color = QColorDialog.getColor(QColor(self.color), self, "Choose Color")
        if color.isValid():
            self.color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.color}; border: 1px solid #ccc;")
    
    def _test_formula(self):
        """Test formula with sample data."""
        formula = self.formula_edit.toPlainText().strip()
        if not formula:
            QMessageBox.warning(self, "Error", "Please enter a formula")
            return
        
        # Create sample data
        sample_data = {}
        for sensor in self.available_sensors[:5]:  # Test with first 5 sensors
            sample_data[sensor] = [10.0, 20.0, 30.0, 40.0, 50.0]
        
        try:
            # Test evaluation
            safe_dict = {"__builtins__": {}, "abs": abs, "min": min, "max": max, "math": math}
            for sensor_name, values in sample_data.items():
                var_name = sensor_name.replace(" ", "_").replace("-", "_")
                safe_dict[var_name] = values[0]
            
            result = eval(formula, safe_dict)
            QMessageBox.information(self, "Test Result", f"Formula evaluates to: {result}\n(Using sample data)")
        except Exception as e:
            QMessageBox.warning(self, "Formula Error", f"Formula error: {e}\n\nMake sure sensor names match available sensors.")
    
    def get_math_channel(self) -> Optional[MathChannel]:
        """Get the configured math channel."""
        name = self.name_edit.text().strip()
        formula = self.formula_edit.toPlainText().strip()
        
        if not name or not formula:
            return None
        
        return MathChannel(
            name=name,
            formula=formula,
            unit=self.unit_edit.text().strip(),
            color=self.color
        )


class XYPlotWidget(PlotWidget):
    """X-Y plot widget for signal vs signal plotting."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLabel("left", "Y-Axis Signal")
        self.setLabel("bottom", "X-Axis Signal")
        self.showGrid(x=True, y=True, alpha=0.3)
        self.addLegend()
    
    def plot_signals(self, x_sensor: str, y_sensor: str, x_data: List[float], y_data: List[float], color: str = "#3498db"):
        """Plot one signal against another."""
        # Ensure equal lengths
        min_len = min(len(x_data), len(y_data))
        if min_len == 0:
            return
        
        x_plot = x_data[:min_len]
        y_plot = y_data[:min_len]
        
        # Create scatter plot
        pen = pg.mkPen(color=color, width=2)
        self.plot(x_plot, y_plot, pen=pen, name=f"{y_sensor} vs {x_sensor}", symbol='o', symbolSize=3)


class HistogramWidget(PlotWidget):
    """Histogram widget for frequency distribution analysis."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLabel("left", "Frequency")
        self.setLabel("bottom", "Value")
        self.showGrid(x=True, y=True, alpha=0.3)
    
    def plot_histogram(self, data: List[float], bins: int = 50, color: str = "#3498db", sensor_name: str = ""):
        """Plot histogram of data distribution."""
        if not data:
            return
        
        if NUMPY_AVAILABLE:
            hist, edges = np.histogram(data, bins=bins)
            # Convert to bar chart
            x = [(edges[i] + edges[i+1]) / 2 for i in range(len(edges)-1)]
            y = hist.tolist()
        else:
            # Manual histogram
            min_val, max_val = min(data), max(data)
            bin_width = (max_val - min_val) / bins if max_val > min_val else 1.0
            hist = [0] * bins
            for value in data:
                bin_idx = min(int((value - min_val) / bin_width), bins - 1)
                hist[bin_idx] += 1
            x = [min_val + (i + 0.5) * bin_width for i in range(bins)]
            y = hist
        
        # Plot as bar chart
        bg = pg.BarGraphItem(x=x, height=y, width=bin_width if not NUMPY_AVAILABLE else (max(data) - min(data)) / bins, brush=color)
        self.clear()
        self.addItem(bg)
        self.setTitle(f"Histogram: {sensor_name}" if sensor_name else "Histogram")


class FFTWidget(PlotWidget):
    """FFT/Frequency analysis widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLabel("left", "Magnitude")
        self.setLabel("bottom", "Frequency (Hz)")
        self.showGrid(x=True, y=True, alpha=0.3)
    
    def plot_fft(self, data: List[float], sample_rate: float = 1.0, color: str = "#3498db", sensor_name: str = ""):
        """Plot FFT of data."""
        if not data or len(data) < 2:
            return
        
        if not NUMPY_AVAILABLE:
            QMessageBox.warning(self, "FFT Unavailable", "NumPy required for FFT analysis. Install with: pip install numpy")
            return
        
        try:
            # Compute FFT
            fft_data = np.fft.fft(data)
            fft_magnitude = np.abs(fft_data)
            frequencies = np.fft.fftfreq(len(data), 1.0 / sample_rate)
            
            # Only plot positive frequencies
            positive_freq_idx = frequencies >= 0
            frequencies = frequencies[positive_freq_idx]
            fft_magnitude = fft_magnitude[positive_freq_idx]
            
            # Plot
            pen = pg.mkPen(color=color, width=2)
            self.plot(frequencies, fft_magnitude, pen=pen, name=sensor_name or "FFT")
            self.setTitle(f"FFT Analysis: {sensor_name}" if sensor_name else "FFT Analysis")
        except Exception as e:
            LOGGER.error(f"FFT error: {e}", exc_info=True)
            QMessageBox.warning(self, "FFT Error", f"Failed to compute FFT: {e}")


class AdvancedGraphFeaturesDialog(QDialog):
    """Dialog for accessing advanced graph features."""
    
    def __init__(self, sensor_data: Dict[str, List[float]], available_sensors: List[str], parent=None):
        super().__init__(parent)
        self.sensor_data = sensor_data
        self.available_sensors = available_sensors
        self.setWindowTitle("Advanced Graph Features")
        self.setMinimumSize(900, 700)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget for different features
        tabs = QTabWidget()
        
        # X-Y Plot tab
        xy_tab = self._create_xy_plot_tab()
        tabs.addTab(xy_tab, "X-Y Plot")
        
        # Histogram tab
        hist_tab = self._create_histogram_tab()
        tabs.addTab(hist_tab, "Histogram")
        
        # FFT tab
        fft_tab = self._create_fft_tab()
        tabs.addTab(fft_tab, "FFT Analysis")
        
        # Math Channels tab
        math_tab = self._create_math_channels_tab()
        tabs.addTab(math_tab, "Math Channels")
        
        # Scatter Plot tab
        scatter_tab = self._create_scatter_tab()
        tabs.addTab(scatter_tab, "Scatter Plot")
        
        layout.addWidget(tabs)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def _create_xy_plot_tab(self) -> QWidget:
        """Create X-Y plot tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        controls.addWidget(QLabel("X-Axis:"))
        x_combo = QComboBox()
        x_combo.addItems([""] + self.available_sensors)
        controls.addWidget(x_combo)
        
        controls.addWidget(QLabel("Y-Axis:"))
        y_combo = QComboBox()
        y_combo.addItems([""] + self.available_sensors)
        controls.addWidget(y_combo)
        
        plot_btn = QPushButton("Plot")
        plot_btn.clicked.connect(lambda: self._plot_xy(x_combo.currentText(), y_combo.currentText()))
        controls.addWidget(plot_btn)
        
        layout.addLayout(controls)
        
        # Plot widget
        if PG_AVAILABLE:
            self.xy_plot = XYPlotWidget()
            layout.addWidget(self.xy_plot)
        else:
            layout.addWidget(QLabel("pyqtgraph not available"))
        
        return widget
    
    def _create_histogram_tab(self) -> QWidget:
        """Create histogram tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Sensor:"))
        sensor_combo = QComboBox()
        sensor_combo.addItems([""] + self.available_sensors)
        controls.addWidget(sensor_combo)
        
        controls.addWidget(QLabel("Bins:"))
        bins_spin = QSpinBox()
        bins_spin.setRange(10, 200)
        bins_spin.setValue(50)
        controls.addWidget(bins_spin)
        
        plot_btn = QPushButton("Plot Histogram")
        plot_btn.clicked.connect(lambda: self._plot_histogram(sensor_combo.currentText(), bins_spin.value()))
        controls.addWidget(plot_btn)
        
        layout.addLayout(controls)
        
        # Plot widget
        if PG_AVAILABLE:
            self.hist_plot = HistogramWidget()
            layout.addWidget(self.hist_plot)
        else:
            layout.addWidget(QLabel("pyqtgraph not available"))
        
        return widget
    
    def _create_fft_tab(self) -> QWidget:
        """Create FFT tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Sensor:"))
        sensor_combo = QComboBox()
        sensor_combo.addItems([""] + self.available_sensors)
        controls.addWidget(sensor_combo)
        
        controls.addWidget(QLabel("Sample Rate (Hz):"))
        sample_rate_spin = QDoubleSpinBox()
        sample_rate_spin.setRange(0.1, 1000.0)
        sample_rate_spin.setValue(10.0)
        controls.addWidget(sample_rate_spin)
        
        plot_btn = QPushButton("Plot FFT")
        plot_btn.clicked.connect(lambda: self._plot_fft(sensor_combo.currentText(), sample_rate_spin.value()))
        controls.addWidget(plot_btn)
        
        layout.addLayout(controls)
        
        # Plot widget
        if PG_AVAILABLE:
            self.fft_plot = FFTWidget()
            layout.addWidget(self.fft_plot)
        else:
            layout.addWidget(QLabel("pyqtgraph not available"))
        
        return widget
    
    def _create_math_channels_tab(self) -> QWidget:
        """Create math channels tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info
        info = QLabel("Create custom calculated channels using formulas. Use sensor names as variables.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # List of math channels (placeholder - would need storage)
        list_label = QLabel("Math Channels:")
        layout.addWidget(list_label)
        
        # Add button
        add_btn = QPushButton("➕ Create Math Channel")
        add_btn.clicked.connect(self._create_math_channel)
        layout.addWidget(add_btn)
        
        layout.addStretch()
        
        return widget
    
    def _create_scatter_tab(self) -> QWidget:
        """Create scatter plot tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        controls.addWidget(QLabel("X-Axis:"))
        x_combo = QComboBox()
        x_combo.addItems([""] + self.available_sensors)
        controls.addWidget(x_combo)
        
        controls.addWidget(QLabel("Y-Axis:"))
        y_combo = QComboBox()
        y_combo.addItems([""] + self.available_sensors)
        controls.addWidget(y_combo)
        
        plot_btn = QPushButton("Plot Scatter")
        plot_btn.clicked.connect(lambda: self._plot_scatter(x_combo.currentText(), y_combo.currentText()))
        controls.addWidget(plot_btn)
        
        layout.addLayout(controls)
        
        # Plot widget
        if PG_AVAILABLE:
            self.scatter_plot = PlotWidget()
            self.scatter_plot.setLabel("left", "Y-Axis")
            self.scatter_plot.setLabel("bottom", "X-Axis")
            self.scatter_plot.showGrid(x=True, y=True, alpha=0.3)
            layout.addWidget(self.scatter_plot)
        else:
            layout.addWidget(QLabel("pyqtgraph not available"))
        
        return widget
    
    def _plot_xy(self, x_sensor: str, y_sensor: str):
        """Plot X-Y relationship."""
        if not x_sensor or not y_sensor or not PG_AVAILABLE:
            return
        
        x_data = self.sensor_data.get(x_sensor, [])
        y_data = self.sensor_data.get(y_sensor, [])
        
        if not x_data or not y_data:
            QMessageBox.warning(self, "No Data", f"No data available for {x_sensor} or {y_sensor}")
            return
        
        self.xy_plot.clear()
        self.xy_plot.plot_signals(x_sensor, y_sensor, x_data, y_data)
    
    def _plot_histogram(self, sensor: str, bins: int):
        """Plot histogram."""
        if not sensor or not PG_AVAILABLE:
            return
        
        data = self.sensor_data.get(sensor, [])
        if not data:
            QMessageBox.warning(self, "No Data", f"No data available for {sensor}")
            return
        
        self.hist_plot.clear()
        self.hist_plot.plot_histogram(data, bins=bins, sensor_name=sensor)
    
    def _plot_fft(self, sensor: str, sample_rate: float):
        """Plot FFT."""
        if not sensor or not PG_AVAILABLE:
            return
        
        data = self.sensor_data.get(sensor, [])
        if not data:
            QMessageBox.warning(self, "No Data", f"No data available for {sensor}")
            return
        
        self.fft_plot.clear()
        self.fft_plot.plot_fft(data, sample_rate=sample_rate, sensor_name=sensor)
    
    def _plot_scatter(self, x_sensor: str, y_sensor: str):
        """Plot scatter plot."""
        if not x_sensor or not y_sensor or not PG_AVAILABLE:
            return
        
        x_data = self.sensor_data.get(x_sensor, [])
        y_data = self.sensor_data.get(y_sensor, [])
        
        if not x_data or not y_data:
            QMessageBox.warning(self, "No Data", f"No data available for {x_sensor} or {y_sensor}")
            return
        
        min_len = min(len(x_data), len(y_data))
        self.scatter_plot.clear()
        pen = pg.mkPen(color="#3498db", width=1)
        self.scatter_plot.plot(x_data[:min_len], y_data[:min_len], pen=None, symbol='o', symbolSize=5, name=f"{y_sensor} vs {x_sensor}")
    
    def _create_math_channel(self):
        """Create a new math channel."""
        dialog = MathChannelDialog(self.available_sensors, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            channel = dialog.get_math_channel()
            if channel:
                QMessageBox.information(self, "Math Channel Created", f"Math channel '{channel.name}' created.\n\nNote: Math channels will be integrated into the main graph in a future update.")
                # TODO: Store math channel and integrate into main graph


__all__ = [
    "MathChannel",
    "MathChannelDialog",
    "XYPlotWidget",
    "HistogramWidget",
    "FFTWidget",
    "AdvancedGraphFeaturesDialog",
]

