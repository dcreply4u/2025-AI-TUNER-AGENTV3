"""
Futuristic HUD Main Window - Neo-Cyberpunk Design
Advanced system monitoring and diagnostics interface
"""

from __future__ import annotations

from typing import Optional, Dict

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSizePolicy

from ui.hud_theme import HUDTheme, HUDColors
from ui.hud_widgets import GridBackgroundWidget, HUDLabel
from ui.hud_advanced_widgets import (
    FragmentedRingWidget,
    TimelineBarWidget,
    TelemetryDataBlock,
    VerticalSegmentedBarGraph,
    ParametricDisplay,
    DataFlowCluster,
    WaveformEqualizerWidget,
)


class HUDMainWindow(GridBackgroundWidget):
    """Futuristic HUD main window with Neo-Cyberpunk layout."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.theme = HUDTheme()
        self._telemetry_data: Dict[str, float] = {}
        self.setup_ui()
        self._start_data_timer()
        
    def setup_ui(self) -> None:
        """Setup HUD layout structure."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top: Timeline Bar
        self.timeline_bar = TimelineBarWidget()
        main_layout.addWidget(self.timeline_bar)
        
        # Middle: Three-column layout
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(15)
        
        # Left Column: Telemetry Data Blocks and Vertical Bar Graphs
        left_panel = self._create_left_panel()
        middle_layout.addWidget(left_panel, stretch=1)
        
        # Center: Fragmented Ring (focal anchor)
        center_panel = self._create_center_panel()
        middle_layout.addWidget(center_panel, stretch=2)
        
        # Right Column: Monitoring with Radial Gauges and Parametric Displays
        right_panel = self._create_right_panel()
        middle_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(middle_layout, stretch=1)
        
        # Bottom: Data Flow Cluster and Waveform/Equalizer
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)
        
        # Bottom Left: Data Flow Cluster
        self.data_flow = DataFlowCluster()
        bottom_layout.addWidget(self.data_flow, stretch=1)
        
        # Bottom Center: Waveform/Equalizer
        self.waveform_eq = WaveformEqualizerWidget()
        bottom_layout.addWidget(self.waveform_eq, stretch=2)
        
        main_layout.addLayout(bottom_layout)
        
    def _create_left_panel(self) -> QWidget:
        """Create left telemetry column."""
        panel = GridBackgroundWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = HUDLabel("TELEMETRY", self.theme.colors.electric_cyan, 12)
        layout.addWidget(title)
        
        # Stacked data blocks with paired readouts
        self.data_blocks = []
        data_pairs = [
            ("RPM", "SPEED"),
            ("BOOST", "OIL_P"),
            ("COOLANT", "BATTERY"),
            ("THROTTLE", "G_FORCE"),
        ]
        
        for label1, label2 in data_pairs:
            block_layout = QHBoxLayout()
            block1 = TelemetryDataBlock(label1, 0, 0)
            block2 = TelemetryDataBlock(label2, 0, 0)
            self.data_blocks.append((block1, block2))
            block_layout.addWidget(block1)
            block_layout.addWidget(block2)
            layout.addLayout(block_layout)
        
        # Large vertical segmented bar graphs (4 columns)
        self.vertical_bars = VerticalSegmentedBarGraph()
        layout.addWidget(self.vertical_bars, stretch=1)
        
        return panel
        
    def _create_center_panel(self) -> QWidget:
        """Create center panel with fragmented ring."""
        panel = GridBackgroundWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Fragmented ring (central focal anchor)
        self.fragmented_ring = FragmentedRingWidget()
        layout.addWidget(self.fragmented_ring, stretch=1, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create right monitoring column."""
        panel = GridBackgroundWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = HUDLabel("MONITORING", self.theme.colors.vibrant_traffic_orange, 12)
        layout.addWidget(title)
        
        # Cluster of small radial gauges (mini-pie charts) at top
        from ui.hud_widgets import RadialGauge
        gauges_layout = QHBoxLayout()
        self.mini_gauges = []
        gauge_labels = ["CPU1", "CPU2", "CPU3", "CPU4"]
        for label in gauge_labels:
            gauge = RadialGauge(label, 0, 100, 50, self.theme.colors.electric_cyan)
            gauge.setMinimumSize(60, 60)
            gauge.setMaximumSize(70, 70)
            self.mini_gauges.append(gauge)
            gauges_layout.addWidget(gauge)
        layout.addLayout(gauges_layout)
        
        # Row of three larger parametric displays
        param_layout = QHBoxLayout()
        self.parametric_displays = []
        param_titles = ["POWER", "EFF", "FLOW"]
        for title in param_titles:
            display = ParametricDisplay(title, 50.0)
            self.parametric_displays.append(display)
            param_layout.addWidget(display)
        layout.addLayout(param_layout)
        
        layout.addStretch()
        return panel
        
    def _start_data_timer(self) -> None:
        """Start timer to update with real telemetry data."""
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self._update_from_telemetry)
        self.data_timer.start(100)  # 10 Hz update rate
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update HUD with new telemetry data."""
        self._telemetry_data = data
        self._update_from_telemetry()
        
    def _update_from_telemetry(self) -> None:
        """Update all widgets with current telemetry data."""
        data = self._telemetry_data
        
        # Update data blocks
        if self.data_blocks:
            # RPM / SPEED pair
            rpm = data.get("RPM", data.get("Engine_RPM", 0))
            speed = data.get("Speed", data.get("Vehicle_Speed", 0))
            throttle = data.get("Throttle_Position", data.get("throttle", 0)) * 100
            if self.data_blocks and len(self.data_blocks) > 0:
                self.data_blocks[0][0].update_values(int(rpm), int(speed))  # RPM block: cyan=rpm, orange=speed
                self.data_blocks[0][1].update_values(int(speed), int(throttle))  # SPEED block: cyan=speed, orange=throttle
            
            # BOOST / OIL_P pair
            boost = data.get("Boost_Pressure", data.get("boost_psi", 0))
            oil_p = data.get("Oil_Pressure", data.get("oil_pressure", 0))
            if len(self.data_blocks) > 1:
                self.data_blocks[1][0].update_values(int(boost), int(oil_p))  # BOOST block: cyan=boost, orange=oil_p
                self.data_blocks[1][1].update_values(int(oil_p), int(boost))  # OIL_P block: cyan=oil_p, orange=boost
            
            # COOLANT / BATTERY pair
            coolant = data.get("Coolant_Temp", data.get("coolant_temp", 0))
            battery = data.get("Battery_Voltage", data.get("battery_voltage", 0)) * 10  # Scale
            if len(self.data_blocks) > 2:
                self.data_blocks[2][0].update_values(int(coolant), int(battery))  # COOLANT block: cyan=coolant, orange=battery
                self.data_blocks[2][1].update_values(int(battery), int(coolant))  # BATTERY block: cyan=battery, orange=coolant
            
            # THROTTLE / G_FORCE pair
            throttle_val = data.get("Throttle_Position", data.get("throttle", 0)) * 100  # Scale to 0-100
            g_force = abs(data.get("GForce_Lateral", data.get("g_force_lat", 0))) * 10  # Scale
            if len(self.data_blocks) > 3:
                self.data_blocks[3][0].update_values(int(throttle_val), int(g_force))  # THROTTLE block: cyan=throttle, orange=g_force
                self.data_blocks[3][1].update_values(int(g_force), int(throttle_val))  # G_FORCE block: cyan=g_force, orange=throttle
        
        # Update vertical bar graphs with suspension data
        if self.vertical_bars and hasattr(self.vertical_bars, "_values"):
            # Use suspension travel data if available
            sus_fl = data.get("Suspension_Travel_FL", data.get("suspension_travel_fl", 50))
            sus_fr = data.get("Suspension_Travel_FR", data.get("suspension_travel_fr", 50))
            sus_rl = data.get("Suspension_Travel_RL", data.get("suspension_travel_rl", 50))
            sus_rr = data.get("Suspension_Travel_RR", data.get("suspension_travel_rr", 50))
            
            # Update each column with suspension data
            self.vertical_bars._values[0] = [sus_fl + i * 5 for i in range(8)]
            self.vertical_bars._values[1] = [sus_fr + i * 5 for i in range(8)]
            self.vertical_bars._values[2] = [sus_rl + i * 5 for i in range(8)]
            self.vertical_bars._values[3] = [sus_rr + i * 5 for i in range(8)]
            self.vertical_bars.update()
        
        # Update mini gauges (CPU load simulation based on RPM)
        if self.mini_gauges:
            rpm = data.get("RPM", data.get("Engine_RPM", 0))
            base_load = min(100, (rpm / 8000) * 100)
            for i, gauge in enumerate(self.mini_gauges):
                load = base_load + (i * 5) + (hash(str(i)) % 20)
                gauge.set_value(min(100, max(0, load)))
        
        # Update parametric displays
        if self.parametric_displays:
            # POWER (based on RPM and throttle)
            rpm = data.get("RPM", data.get("Engine_RPM", 0))
            throttle = data.get("Throttle_Position", data.get("throttle", 0))
            power = min(100, (rpm / 8000) * 100 * throttle)
            self.parametric_displays[0].set_value(power)
            
            # EFF (efficiency - based on AFR and throttle)
            afr = data.get("AFR", data.get("lambda_value", 1.0))
            eff = min(100, max(0, (1.0 - abs(afr - 1.0)) * 100))
            self.parametric_displays[1].set_value(eff)
            
            # FLOW (airflow - based on boost and RPM)
            boost = data.get("Boost_Pressure", data.get("boost_psi", 0))
            flow = min(100, (boost / 30) * 50 + (rpm / 8000) * 50)
            self.parametric_displays[2].set_value(flow)
        
        # Update waveform/equalizer with RPM-based frequency data
        if self.waveform_eq and hasattr(self.waveform_eq, "_bar_values"):
            rpm = data.get("RPM", data.get("Engine_RPM", 0))
            # Simulate frequency response based on RPM
            base_freq = (rpm / 8000) * 100
            self.waveform_eq._bar_values = [
                max(10, min(90, base_freq + (i % 5) * 10 + hash(str(i)) % 15))
                for i in range(20)
            ]
            self.waveform_eq.update()


__all__ = ["HUDMainWindow"]
