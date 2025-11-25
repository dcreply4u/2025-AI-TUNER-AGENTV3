"""
telemetryIQ Enhanced Widgets
Enhanced graph panel, logger, oscilloscope, and system status utilities
"""

from __future__ import annotations

from typing import Dict, Optional
from collections import deque

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QComboBox,
    QTextEdit,
    QTabWidget,
    QSizePolicy,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

try:
    import pyqtgraph as pg
except ImportError:
    pg = None


class EnhancedGraphPanel(QWidget):
    """Enhanced bottom graph panel with Live Logger, Internal Log Status, Trigger Oscilloscope, and Trigger Logger."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.setup_ui()
        self.data_buffers = {
            "lambda": deque(maxlen=2000),
            "boost_aim": deque(maxlen=2000),
            "ego_correction": deque(maxlen=2000),
            "time": deque(maxlen=2000),
        }
        self.trigger_data = {
            "crank": deque(maxlen=1000),
            "cam": deque(maxlen=1000),
            "time": deque(maxlen=1000),
        }
        self.time_counter = 0.0
        self.trigger_time_counter = 0.0
        self.internal_log_active = False
        
    def setup_ui(self) -> None:
        """Setup enhanced graph panel UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(5)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Tab widget for different views
        self.tabs = QTabWidget()
        tab_border = get_scaled_size(1)
        tab_padding_v = get_scaled_size(6)
        tab_padding_h = get_scaled_size(15)
        tab_margin = get_scaled_size(2)
        tab_font = get_scaled_font_size(10)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {tab_border}px solid #404040;
                background-color: #1a1a1a;
            }}
            QTabBar::tab {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: {tab_margin}px;
                border: {tab_border}px solid #404040;
                font-size: {tab_font}px;
                min-height: {get_scaled_size(25)}px;
            }}
            QTabBar::tab:selected {{
                background-color: #1a1a1a;
                border-bottom: {get_scaled_size(2)}px solid #0080ff;
            }}
        """)
        
        # Live Logger tab
        live_logger_tab = self._create_live_logger_tab()
        self.tabs.addTab(live_logger_tab, "Live Logger")
        
        # Trigger Oscilloscope tab
        oscilloscope_tab = self._create_oscilloscope_tab()
        self.tabs.addTab(oscilloscope_tab, "Trigger Oscilloscope")
        
        # Trigger Logger tab
        trigger_logger_tab = self._create_trigger_logger_tab()
        self.tabs.addTab(trigger_logger_tab, "Trigger Logger")
        
        main_layout.addWidget(self.tabs)
        
    def _create_live_logger_tab(self) -> QWidget:
        """Create live logger tab with graph and internal log status."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(5)
        spacing = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Internal Log Status
        status_bar = QWidget()
        padding = get_scaled_size(5)
        border = get_scaled_size(1)
        status_bar.setStyleSheet(f"background-color: #2a2a2a; padding: {padding}px; border: {border}px solid #404040;")
        status_layout = QHBoxLayout(status_bar)
        margin_h = get_scaled_size(10)
        margin_v = get_scaled_size(5)
        status_layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        self.log_status_label = QLabel("Internal Log: ON - Auto-Start Triggered (Speed > 50 kph, MAP > 100 kPa)")
        status_font = get_scaled_font_size(11)
        self.log_status_label.setStyleSheet(f"font-size: {status_font}px; color: #00ff00; font-weight: bold;")
        status_layout.addWidget(self.log_status_label)
        status_layout.addStretch()
        
        # Log controls
        self.log_start_btn = QPushButton("Start Log")
        btn_padding_v = get_scaled_size(3)
        btn_padding_h = get_scaled_size(10)
        self.log_start_btn.setStyleSheet(f"background-color: #0080ff; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px;")
        status_layout.addWidget(self.log_start_btn)
        
        self.log_stop_btn = QPushButton("Stop Log")
        self.log_stop_btn.setStyleSheet(f"background-color: #ff0000; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px;")
        status_layout.addWidget(self.log_stop_btn)
        
        layout.addWidget(status_bar)
        
        # Live Logger Graph (20Hz PC data streams)
        if pg:
            self.live_plot = pg.PlotWidget()
            self.live_plot.setBackground("#000000")
            self.live_plot.setLabel("bottom", "Time (s)", color="#ffffff")
            self.live_plot.setLabel("left", "Lambda / Boost Aim / Ego Correction", color="#ffffff")
            self.live_plot.showGrid(x=True, y=True, alpha=0.3)
            self.live_plot.setYRange(0, 20)
            
            # Create curves
            self.lambda_curve = self.live_plot.plot(
                pen=pg.mkPen("#00ff00", width=2),
                name="Lambda",
            )
            self.boost_curve = self.live_plot.plot(
                pen=pg.mkPen("#0080ff", width=2),
                name="Boost Aim",
            )
            self.ego_curve = self.live_plot.plot(
                pen=pg.mkPen("#ff0000", width=2),
                name="Ego Correction",
            )
            
            layout.addWidget(self.live_plot, stretch=1)
        else:
            placeholder = QLabel("pyqtgraph required for live logger graph")
            placeholder_padding = get_scaled_size(20)
            placeholder.setStyleSheet(f"color: #ffffff; background: #000000; padding: {placeholder_padding}px;")
            layout.addWidget(placeholder, stretch=1)
        
        return tab
        
    def _create_oscilloscope_tab(self) -> QWidget:
        """Create trigger oscilloscope tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(5)
        spacing = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Controls
        controls = QWidget()
        padding = get_scaled_size(5)
        border = get_scaled_size(1)
        controls.setStyleSheet(f"background-color: #2a2a2a; padding: {padding}px; border: {border}px solid #404040;")
        controls_layout = QHBoxLayout(controls)
        margin_h = get_scaled_size(10)
        margin_v = get_scaled_size(5)
        controls_layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        controls_layout.addWidget(QLabel("Sample Time:"))
        self.sample_time = QComboBox()
        self.sample_time.addItems(["1ms", "5ms", "10ms", "50ms", "100ms"])
        self.sample_time.setStyleSheet("color: #ffffff; background-color: #1a1a1a;")
        controls_layout.addWidget(self.sample_time)
        
        controls_layout.addWidget(QLabel("Trigger Source:"))
        self.trigger_source = QComboBox()
        self.trigger_source.addItems(["Crank", "Cam", "Both"])
        self.trigger_source.setStyleSheet("color: #ffffff; background-color: #1a1a1a;")
        controls_layout.addWidget(self.trigger_source)
        
        controls_layout.addWidget(QLabel("Start Mode:"))
        self.start_mode = QComboBox()
        self.start_mode.addItems(["Continuous", "Single"])
        self.start_mode.setStyleSheet("color: #ffffff; background-color: #1a1a1a;")
        controls_layout.addWidget(self.start_mode)
        
        controls_layout.addStretch()
        
        self.trigger_start_btn = QPushButton("Start")
        btn_padding_v = get_scaled_size(3)
        btn_padding_h = get_scaled_size(10)
        self.trigger_start_btn.setStyleSheet(f"background-color: #0080ff; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px;")
        controls_layout.addWidget(self.trigger_start_btn)
        
        layout.addWidget(controls)
        
        # Oscilloscope graph
        if pg:
            self.oscilloscope_plot = pg.PlotWidget()
            self.oscilloscope_plot.setBackground("#000000")
            self.oscilloscope_plot.setLabel("bottom", "Time (ms)", color="#ffffff")
            self.oscilloscope_plot.setLabel("left", "Voltage (V)", color="#ffffff")
            self.oscilloscope_plot.showGrid(x=True, y=True, alpha=0.3)
            self.oscilloscope_plot.setYRange(-1, 6)
            
            # Create curves for trigger signals
            self.crank_curve = self.oscilloscope_plot.plot(
                pen=pg.mkPen("#00ff00", width=2),
                name="Crank (Trigger)",
            )
            self.cam_curve = self.oscilloscope_plot.plot(
                pen=pg.mkPen("#ff8000", width=2),
                name="Cam (Home)",
            )
            
            layout.addWidget(self.oscilloscope_plot, stretch=1)
        else:
            placeholder = QLabel("pyqtgraph required for oscilloscope")
            placeholder_padding = get_scaled_size(20)
            placeholder.setStyleSheet(f"color: #ffffff; background: #000000; padding: {placeholder_padding}px;")
            layout.addWidget(placeholder, stretch=1)
        
        return tab
        
    def _create_trigger_logger_tab(self) -> QWidget:
        """Create trigger logger tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        margin = get_scaled_size(5)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Trigger logger text area
        self.trigger_log = QTextEdit()
        self.trigger_log.setReadOnly(True)
        border = get_scaled_size(1)
        log_font = get_scaled_font_size(10)
        self.trigger_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #ffffff;
                border: {border}px solid #404040;
                font-family: 'Courier New', monospace;
                font-size: {log_font}px;
            }}
        """)
        
        # Initial log message
        self.trigger_log.append("telemetryIQ Trigger Support - Logger Active")
        self.trigger_log.append("Monitoring trigger signals...")
        self.trigger_log.append("")
        
        layout.addWidget(self.trigger_log, stretch=1)
        
        # Clear button
        clear_btn = QPushButton("Clear Log")
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        clear_btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px;")
        clear_btn.clicked.connect(self.trigger_log.clear)
        layout.addWidget(clear_btn)
        
        return tab
        
    def update_live_logger(self, lambda_val: float, boost_aim: float, ego_correction: float) -> None:
        """Update live logger graph with 20Hz data."""
        if not pg:
            return
            
        self.time_counter += 0.05  # 20Hz = 0.05s per update
        
        self.data_buffers["time"].append(self.time_counter)
        self.data_buffers["lambda"].append(lambda_val)
        self.data_buffers["boost_aim"].append(boost_aim)
        self.data_buffers["ego_correction"].append(ego_correction)
        
        if len(self.data_buffers["time"]) > 1:
            time_data = list(self.data_buffers["time"])
            self.lambda_curve.setData(time_data, list(self.data_buffers["lambda"]))
            self.boost_curve.setData(time_data, list(self.data_buffers["boost_aim"]))
            self.ego_curve.setData(time_data, list(self.data_buffers["ego_correction"]))
            
    def update_oscilloscope(self, crank_signal: list, cam_signal: list, time_data: list) -> None:
        """Update oscilloscope with trigger signals."""
        if not pg:
            return
            
        self.crank_curve.setData(time_data, crank_signal)
        self.cam_curve.setData(time_data, cam_signal)
        
    def add_trigger_log_message(self, message: str) -> None:
        """Add message to trigger logger."""
        self.trigger_log.append(message)
        
    def set_internal_log_status(self, active: bool, message: str = "") -> None:
        """Update internal log status indicator."""
        status_font = get_scaled_font_size(11)
        if active:
            self.log_status_label.setText(f"Internal Log: ON - {message}")
            self.log_status_label.setStyleSheet(f"font-size: {status_font}px; color: #00ff00; font-weight: bold;")
        else:
            self.log_status_label.setText("Internal Log: OFF")
            self.log_status_label.setStyleSheet(f"font-size: {status_font}px; color: #ff0000; font-weight: bold;")
        self.internal_log_active = active


class SystemStatusPanel(QWidget):
    """System Status & Utilities Panel with Connectivity, Hardware Utils, Tach/Speed Out."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Setup system status panel."""
        layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Connectivity
        conn_group = QGroupBox("Connectivity")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        conn_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        conn_layout = QVBoxLayout()
        
        # Connection status
        status_layout = QHBoxLayout()
        self.conn_led = QLabel()
        led_size = get_scaled_size(12)
        self.conn_led.setFixedSize(led_size, led_size)
        led_radius = get_scaled_size(6)
        self.conn_led.setStyleSheet(f"background-color: #00ff00; border-radius: {led_radius}px; border: {group_border}px solid #00ff00;")
        status_layout.addWidget(self.conn_led)
        
        self.conn_label = QLabel("Connected @ 5.0 Gbps")
        conn_font = get_scaled_font_size(11)
        self.conn_label.setStyleSheet(f"font-size: {conn_font}px; color: #00ff00; font-weight: bold;")
        status_layout.addWidget(self.conn_label)
        status_layout.addStretch()
        conn_layout.addLayout(status_layout)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Hardware Utils
        hw_group = QGroupBox("Hardware Utils")
        hw_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        hw_layout = QVBoxLayout()
        
        self.measure_injector_btn = QPushButton("Measure Injector Resistance")
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        self.measure_injector_btn.setStyleSheet(f"background-color: #0080ff; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px;")
        self.measure_injector_btn.clicked.connect(self._show_injector_resistance)
        hw_layout.addWidget(self.measure_injector_btn)
        
        hw_group.setLayout(hw_layout)
        layout.addWidget(hw_group)
        
        # Tach/Speed Out
        tach_group = QGroupBox("Tach/Speed Out")
        tach_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        tach_layout = QVBoxLayout()
        
        tach_layout.addWidget(QLabel("Speedometer Output Function:"))
        self.speed_out = QComboBox()
        self.speed_out.addItems(["Vehicle Speed", "RPM", "MAP", "Disabled"])
        self.speed_out.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        tach_layout.addWidget(self.speed_out)
        
        tach_layout.addWidget(QLabel("Tachometer Output:"))
        self.tach_out = QComboBox()
        self.tach_out.addItems(["5V", "12V"])
        self.tach_out.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        tach_layout.addWidget(self.tach_out)
        
        tach_group.setLayout(tach_layout)
        layout.addWidget(tach_group)
        
        layout.addStretch()
        
    def _show_injector_resistance(self) -> None:
        """Show injector resistance popup."""
        from PySide6.QtWidgets import QMessageBox
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Injector Resistance")
        msg.setText("Injector Resistance Measurements:")
        msg.setDetailedText(
            "Cylinder 1: 12.3 Ω\n"
            "Cylinder 2: 12.1 Ω\n"
            "Cylinder 3: 12.4 Ω\n"
            "Cylinder 4: 12.2 Ω\n"
            "Cylinder 5: 12.3 Ω\n"
            "Cylinder 6: 12.1 Ω\n"
            "Cylinder 7: 12.4 Ω\n"
            "Cylinder 8: 12.2 Ω"
        )
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
        """)
        msg.exec()
        
    def set_connection_status(self, connected: bool, speed: str = "5.0 Gbps") -> None:
        """Update connection status."""
        led_radius = get_scaled_size(6)
        border = get_scaled_size(1)
        conn_font = get_scaled_font_size(11)
        if connected:
            self.conn_led.setStyleSheet(f"background-color: #00ff00; border-radius: {led_radius}px; border: {border}px solid #00ff00;")
            self.conn_label.setText(f"Connected @ {speed}")
            self.conn_label.setStyleSheet(f"font-size: {conn_font}px; color: #00ff00; font-weight: bold;")
        else:
            self.conn_led.setStyleSheet(f"background-color: #ff0000; border-radius: {led_radius}px; border: {border}px solid #ff0000;")
            self.conn_label.setText("Disconnected")
            self.conn_label.setStyleSheet(f"font-size: {conn_font}px; color: #ff0000; font-weight: bold;")


__all__ = ["EnhancedGraphPanel", "SystemStatusPanel"]



