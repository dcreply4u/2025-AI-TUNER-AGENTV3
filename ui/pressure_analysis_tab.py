"""
Cylinder Pressure Analysis Tab

Professional-grade cylinder pressure analysis interface.
"""

from __future__ import annotations

import logging
import time
import threading
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal  # type: ignore
from PySide6.QtWidgets import (  # type: ignore
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.pressure_graph_widget import PressureGraphWidget

try:
    from interfaces.pressure_sensor_interface import (
        PressureSensorInterface,
        PressureSensorConfig,
    )
    from interfaces.pressure_daq_interface import (
        DAQConfig,
        DAQType,
    )
    from services.cylinder_pressure_analyzer import (
        CylinderPressureAnalyzer,
        PressureCycle,
        CombustionMetrics,
        StabilityMetrics,
    )
except ImportError:
    PressureSensorInterface = None
    PressureSensorConfig = None
    DAQConfig = None
    DAQType = None
    CylinderPressureAnalyzer = None
    PressureCycle = None
    CombustionMetrics = None
    StabilityMetrics = None

LOGGER = logging.getLogger(__name__)


class PressureAnalysisTab(QWidget):
    """Cylinder pressure analysis tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.pressure_sensor: Optional[PressureSensorInterface] = None
        self.analyzer: Optional[CylinderPressureAnalyzer] = None
        
        # Data acquisition state
        self.acquiring = False
        self.acquisition_thread: Optional[threading.Thread] = None
        self._acquisition_lock = threading.Lock()  # Thread lock for acquisition state
        
        # Cycle storage (thread-safe access required)
        self.cycles: Dict[int, List[PressureCycle]] = {}  # cylinder -> cycles
        self._cycles_lock = threading.Lock()  # Thread lock for cycles dictionary
        
        self.setup_ui()
        self._start_update_timer()
    
    def setup_ui(self) -> None:
        """Setup pressure analysis tab UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Set background
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(get_scaled_size(15))
        
        # Left: Settings and metrics panel
        left_panel = self._create_settings_panel()
        content_layout.addWidget(left_panel, stretch=1)
        
        # Center: Graph
        center_panel = self._create_graph_panel()
        content_layout.addWidget(center_panel, stretch=3)
        
        # Right: Analysis results
        right_panel = self._create_analysis_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
    
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
        
        title = QLabel("Cylinder Pressure Analysis - Professional Tuning")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # DAQ connection status
        self.connection_status_label = QLabel("Not Connected")
        self.connection_status_label.setStyleSheet("color: #9aa0a6; font-size: 11px; padding: 0 10px;")
        layout.addWidget(self.connection_status_label)
        
        # Connect button
        self.connect_btn = QPushButton("Connect DAQ")
        self.connect_btn.setStyleSheet(
            f"background-color: #2d7d32; color: #ffffff; padding: 5px 10px; "
            f"font-size: 11px; font-weight: bold;"
        )
        self.connect_btn.clicked.connect(self._connect_daq)
        layout.addWidget(self.connect_btn)
        
        # Start/Stop acquisition
        self.start_btn = QPushButton("Start Acquisition")
        self.start_btn.setStyleSheet(
            f"background-color: #0080ff; color: #ffffff; padding: 5px 10px; "
            f"font-size: 11px; font-weight: bold;"
        )
        self.start_btn.clicked.connect(self._start_acquisition)
        self.start_btn.setEnabled(False)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Acquisition")
        self.stop_btn.setStyleSheet(
            f"background-color: #c62828; color: #ffffff; padding: 5px 10px; "
            f"font-size: 11px; font-weight: bold;"
        )
        self.stop_btn.clicked.connect(self._stop_acquisition)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        # Clear data
        self.clear_btn = QPushButton("Clear Data")
        self.clear_btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: 5px 10px; font-size: 11px;")
        self.clear_btn.clicked.connect(self._clear_data)
        layout.addWidget(self.clear_btn)
        
        return bar
    
    def _create_settings_panel(self) -> QWidget:
        """Create settings panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(300))
        layout = QVBoxLayout(panel)
        layout.setSpacing(get_scaled_size(10))
        
        # DAQ Configuration
        daq_group = QGroupBox("DAQ Configuration")
        daq_group.setStyleSheet("color: white; font-weight: bold;")
        daq_layout = QVBoxLayout(daq_group)
        
        daq_layout.addWidget(QLabel("DAQ Type:"))
        self.daq_type_combo = QComboBox()
        self.daq_type_combo.addItems(["AEM Series 2", "Generic CAN", "Serial"])
        self.daq_type_combo.setStyleSheet("color: white; background: #2b2b2b;")
        daq_layout.addWidget(self.daq_type_combo)
        
        daq_layout.addWidget(QLabel("Interface:"))
        self.interface_combo = QComboBox()
        self.interface_combo.addItems(["can0", "can1", "/dev/ttyUSB0"])
        self.interface_combo.setEditable(True)
        self.interface_combo.setStyleSheet("color: white; background: #2b2b2b;")
        daq_layout.addWidget(self.interface_combo)
        
        daq_layout.addWidget(QLabel("Channels:"))
        self.channels_spin = QSpinBox()
        self.channels_spin.setRange(1, 8)
        self.channels_spin.setValue(8)
        self.channels_spin.setStyleSheet("color: white; background: #2b2b2b;")
        daq_layout.addWidget(self.channels_spin)
        
        layout.addWidget(daq_group)
        
        # Engine Configuration
        engine_group = QGroupBox("Engine Configuration")
        engine_group.setStyleSheet("color: white; font-weight: bold;")
        engine_layout = QVBoxLayout(engine_group)
        
        engine_layout.addWidget(QLabel("Displacement (cc):"))
        self.displacement_spin = QDoubleSpinBox()
        self.displacement_spin.setRange(100, 10000)
        self.displacement_spin.setValue(5000)
        self.displacement_spin.setStyleSheet("color: white; background: #2b2b2b;")
        engine_layout.addWidget(self.displacement_spin)
        
        engine_layout.addWidget(QLabel("Cylinders:"))
        self.cylinders_spin = QSpinBox()
        self.cylinders_spin.setRange(1, 8)
        self.cylinders_spin.setValue(8)
        self.cylinders_spin.setStyleSheet("color: white; background: #2b2b2b;")
        engine_layout.addWidget(self.cylinders_spin)
        
        layout.addWidget(engine_group)
        
        # Current Metrics
        metrics_group = QGroupBox("Current Metrics")
        metrics_group.setStyleSheet("color: white; font-weight: bold;")
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.metrics_text.setMaximumHeight(get_scaled_size(200))
        self.metrics_text.setStyleSheet("color: white; background: #0a0a0a;")
        self.metrics_text.setText("No data available")
        metrics_layout.addWidget(self.metrics_text)
        
        layout.addWidget(metrics_group)
        
        layout.addStretch()
        
        return panel
    
    def _create_graph_panel(self) -> QWidget:
        """Create graph panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        
        if PressureGraphWidget:
            self.graph_widget = PressureGraphWidget()
            layout.addWidget(self.graph_widget)
        else:
            layout.addWidget(QLabel("Pressure graph widget not available"))
        
        return panel
    
    def _create_analysis_panel(self) -> QWidget:
        """Create analysis results panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(350))
        layout = QVBoxLayout(panel)
        
        # Stability Metrics
        stability_group = QGroupBox("Stability Metrics")
        stability_group.setStyleSheet("color: white; font-weight: bold;")
        stability_layout = QVBoxLayout(stability_group)
        
        self.stability_table = QTableWidget()
        self.stability_table.setColumnCount(3)
        self.stability_table.setHorizontalHeaderLabels(["Cylinder", "PFP", "COV %"])
        self.stability_table.horizontalHeader().setStretchLastSection(True)
        self.stability_table.setStyleSheet("color: white; background: #0a0a0a;")
        stability_layout.addWidget(self.stability_table)
        
        layout.addWidget(stability_group)
        
        # Analysis Results
        results_group = QGroupBox("Analysis Results")
        results_group.setStyleSheet("color: white; font-weight: bold;")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("color: white; background: #0a0a0a;")
        self.results_text.setText("No analysis results")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        layout.addStretch()
        
        return panel
    
    def _connect_daq(self) -> None:
        """Connect to DAQ system."""
        if not PressureSensorInterface or not DAQConfig or not DAQType:
            LOGGER.error("Pressure sensor modules not available")
            return
        
        try:
            # Get DAQ type
            daq_type_str = self.daq_type_combo.currentText()
            if daq_type_str == "AEM Series 2":
                daq_type = DAQType.AEM_SERIES_2
            elif daq_type_str == "Generic CAN":
                daq_type = DAQType.GENERIC_CAN
            else:
                daq_type = DAQType.SERIAL
            
            # Create DAQ config
            daq_config = DAQConfig(
                daq_type=daq_type,
                interface=self.interface_combo.currentText(),
                channel_count=self.channels_spin.value(),
            )
            
            # Create sensor config
            sensor_config = PressureSensorConfig(
                daq_config=daq_config,
                engine_displacement_cc=self.displacement_spin.value(),
                number_of_cylinders=self.cylinders_spin.value(),
            )
            
            # Create sensor interface
            self.pressure_sensor = PressureSensorInterface(sensor_config)
            if self.pressure_sensor.initialize():
                self.connection_status_label.setText("Connected")
                self.connection_status_label.setStyleSheet("color: #4caf50; font-size: 11px;")
                self.connect_btn.setEnabled(False)
                self.start_btn.setEnabled(True)
                self.analyzer = self.pressure_sensor.analyzer
            else:
                self.connection_status_label.setText("Connection Failed")
                self.connection_status_label.setStyleSheet("color: #f44336; font-size: 11px;")
        except Exception as e:
            LOGGER.error(f"Failed to connect DAQ: {e}")
            self.connection_status_label.setText(f"Error: {e}")
            self.connection_status_label.setStyleSheet("color: #f44336; font-size: 11px;")
    
    def _start_acquisition(self) -> None:
        """Start data acquisition."""
        if not self.pressure_sensor:
            return
        
        if self.pressure_sensor.start_acquisition():
            with self._acquisition_lock:
                self.acquiring = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # Start acquisition thread
            self.acquisition_thread = threading.Thread(target=self._acquisition_loop, daemon=True)
            self.acquisition_thread.start()
    
    def _stop_acquisition(self) -> None:
        """Stop data acquisition."""
        with self._acquisition_lock:
            self.acquiring = False
        
        if self.pressure_sensor:
            self.pressure_sensor.stop_acquisition()
        
        # Wait for thread to finish (with timeout)
        if self.acquisition_thread and self.acquisition_thread.is_alive():
            self.acquisition_thread.join(timeout=5.0)
            if self.acquisition_thread.is_alive():
                LOGGER.warning("Acquisition thread did not stop within timeout")
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def _acquisition_loop(self) -> None:
        """Data acquisition loop (runs in separate thread)."""
        while True:
            # Check acquiring state thread-safely
            with self._acquisition_lock:
                if not self.acquiring or not self.pressure_sensor:
                    break
            
            try:
                samples = self.pressure_sensor.read_pressure_data(1000)
                if samples:
                    cycles = self.pressure_sensor.process_samples(samples)
                    # Store cycles thread-safely
                    with self._cycles_lock:
                        for cycle in cycles:
                            if cycle.cylinder not in self.cycles:
                                self.cycles[cycle.cylinder] = []
                            self.cycles[cycle.cylinder].append(cycle)
                            
                            # Analyze
                            metrics = self.pressure_sensor.analyze_cycle(cycle)
                            
                            # Update UI (via signal/slot if needed)
                            # For now, just log
                            LOGGER.debug(f"Cylinder {cycle.cylinder}: PFP={metrics.pfp:.1f} PSI, ROPR={metrics.ropr_max:.1f} PSI/deg")
                
                time.sleep(0.01)  # Small delay
            except Exception as e:
                LOGGER.error(f"Error in acquisition loop: {e}")
                break
    
    def _clear_data(self) -> None:
        """Clear all collected data."""
        with self._cycles_lock:
            self.cycles.clear()
        if self.analyzer:
            self.analyzer.cycle_history.clear()
            self.analyzer.metrics_history.clear()
        if hasattr(self, 'graph_widget'):
            self.graph_widget.clear_comparisons()
    
    def _start_update_timer(self) -> None:
        """Start update timer for UI refresh."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(100)  # Update every 100ms
    
    def _update_ui(self) -> None:
        """Update UI with latest data."""
        if not self.analyzer or not self.pressure_sensor:
            return
        
        # Get cycles thread-safely (create copy for UI update)
        with self._cycles_lock:
            cycles_copy = {cyl: list(cycle_list) for cyl, cycle_list in self.cycles.items()}
        
        # Update graph with latest cycles
        if hasattr(self, 'graph_widget'):
            for cylinder, cycle_list in cycles_copy.items():
                if cycle_list:
                    latest_cycle = cycle_list[-1]
                    self.graph_widget.update_cycle(latest_cycle, cylinder)
        
        # Update metrics
        if cycles_copy:
            # Get latest metrics for each cylinder
            metrics_text = "Current Metrics:\n\n"
            for cylinder in sorted(cycles_copy.keys()):
                if cycles_copy[cylinder]:
                    cycle = cycles_copy[cylinder][-1]
                    metrics = self.analyzer.analyze_combustion(cycle)
                    metrics_text += f"Cylinder {cylinder}:\n"
                    metrics_text += f"  PFP: {metrics.pfp:.1f} PSI @ {metrics.pfp_angle:.1f}°\n"
                    metrics_text += f"  ROPR: {metrics.ropr_max:.1f} PSI/deg\n"
                    metrics_text += f"  IMEP: {metrics.imep:.1f} PSI\n"
                    if metrics.detonation_detected:
                        metrics_text += f"  ⚠ DETONATION DETECTED!\n"
                    metrics_text += "\n"
            
            self.metrics_text.setText(metrics_text)
            
            # Update stability table
            stability = self.analyzer.get_recent_stability(10)
            self.stability_table.setRowCount(self.analyzer.number_of_cylinders)
            for i, cylinder in enumerate(range(1, self.analyzer.number_of_cylinders + 1)):
                self.stability_table.setItem(i, 0, QTableWidgetItem(str(cylinder)))
                if stability.cylinder_variation and cylinder in stability.cylinder_variation:
                    cov = stability.cylinder_variation[cylinder]
                    self.stability_table.setItem(i, 1, QTableWidgetItem(f"{stability.pfp_mean:.1f}"))
                    self.stability_table.setItem(i, 2, QTableWidgetItem(f"{cov:.2f}%"))

