from __future__ import annotations

"""\
=========================================================
Telemetry Panel – neon graphs for the car's vital signs
=========================================================
"""

from collections import deque
from typing import Dict, Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy

try:
    import pyqtgraph as pg
except Exception:  # pragma: no cover - optional dependency
    pg = None  # type: ignore

try:
    from ui.responsive_layout_manager import get_responsive_manager, scaled_font_size, scaled_spacing
    RESPONSIVE_AVAILABLE = True
except ImportError:
    RESPONSIVE_AVAILABLE = False
    get_responsive_manager = None
    scaled_font_size = lambda x: x
    scaled_spacing = lambda x: x


class TelemetryPanel(QWidget):
    """Live plotting widget for key telemetry channels."""

    PRIMARY_CHANNELS = ("RPM", "Speed", "Throttle", "Boost")
    SECONDARY_CHANNELS = ("CoolantTemp", "OilPressure", "BrakePressure", "BatteryVoltage")
    GFORCE_CHANNELS = ("GForce_Lateral", "GForce_Longitudinal")
    GPS_CHANNELS = ("GPS_Speed", "GPS_Heading", "GPS_Altitude")
    CHANNEL_COLORS = {
        "RPM": "#ff6b6b",
        "Speed": "#4ecdc4",
        "Throttle": "#ffe66d",
        "Boost": "#36c5f0",
        "CoolantTemp": "#ffa94d",
        "OilPressure": "#b197fc",
        "BrakePressure": "#ff8787",
        "BatteryVoltage": "#63e6be",
        "GForce_Lateral": "#ff922b",
        "GForce_Longitudinal": "#fab005",
        "GPS_Speed": "#10b981",
        "GPS_Heading": "#3b82f6",
        "GPS_Altitude": "#8b5cf6",
    }

    def __init__(self, parent: QWidget | None = None, max_len: int = 400) -> None:
        super().__init__(parent)
        self.max_len = max_len

        layout = QVBoxLayout(self)
        layout.setSpacing(scaled_spacing(4))
        layout.setContentsMargins(
            scaled_spacing(8), scaled_spacing(8),
            scaled_spacing(8), scaled_spacing(8)
        )
        
        # Allow panel to expand for 4 stacked graphs
        # 4 graphs x 90px = 360px + header (~30px) + spacing (~30px) = ~420px
        self.setMinimumHeight(420)  # Increased to accommodate GPS graph
        self.setMaximumHeight(450)  # Cap max height
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Ensure it takes space
        
        header = QLabel("Live Telemetry Overview", alignment=Qt.AlignLeft)
        header_font_size = scaled_font_size(18)
        header.setStyleSheet(
            f"font-size: {header_font_size}px; font-weight: 600; color: #1f2a44; padding-bottom: {scaled_spacing(4)}px;"
        )
        layout.addWidget(header)

        self.plots: Dict[str, object] = {}
        self.curves: Dict[str, object] = {}
        self.data = {
            **{k: deque(maxlen=self.max_len) for k in self.PRIMARY_CHANNELS},
            **{k: deque(maxlen=self.max_len) for k in self.SECONDARY_CHANNELS},
            **{k: deque(maxlen=self.max_len) for k in self.GFORCE_CHANNELS},
            **{k: deque(maxlen=self.max_len) for k in self.GPS_CHANNELS},
        }
        self.xdata = deque(maxlen=self.max_len)
        self.counter = 0

        if pg:
            # Use light theme for graphs to match main UI
            pg.setConfigOptions(antialias=True, background="#ffffff", foreground="#2c3e50")
            
            # 3 graphs stacked VERTICALLY - full width like Drag Mode
            GRAPH_HEIGHT = 90  # Increased height per graph for better visibility

            # Powertrain graph (Row 1)
            self.plots["primary"] = pg.PlotWidget(title="Powertrain")
            self.plots["primary"].setBackground("w")
            self.plots["primary"].setFixedHeight(GRAPH_HEIGHT)
            self.plots["primary"].setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.plots["primary"].getAxis("left").setPen(pg.mkPen(color="#2c3e50"))
            self.plots["primary"].getAxis("bottom").setPen(pg.mkPen(color="#2c3e50"))
            self._configure_plot(self.plots["primary"], "Time", "Value")
            if RESPONSIVE_AVAILABLE:
                get_responsive_manager().configure_graph_responsive(self.plots["primary"])
            layout.addWidget(self.plots["primary"])

            # Thermals graph (Row 2)
            self.plots["secondary"] = pg.PlotWidget(title="Thermals & Systems")
            self.plots["secondary"].setBackground("w")
            self.plots["secondary"].setFixedHeight(GRAPH_HEIGHT)
            self.plots["secondary"].setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.plots["secondary"].getAxis("left").setPen(pg.mkPen(color="#2c3e50"))
            self.plots["secondary"].getAxis("bottom").setPen(pg.mkPen(color="#2c3e50"))
            self._configure_plot(self.plots["secondary"], "Time", "Value")
            if RESPONSIVE_AVAILABLE:
                get_responsive_manager().configure_graph_responsive(self.plots["secondary"])
            layout.addWidget(self.plots["secondary"])

            # G-Forces graph (Row 3) - Make sure it's visible
            self.plots["gforce"] = pg.PlotWidget(title="G-Forces")
            self.plots["gforce"].setBackground("w")
            self.plots["gforce"].setFixedHeight(GRAPH_HEIGHT)
            self.plots["gforce"].setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.plots["gforce"].getAxis("left").setPen(pg.mkPen(color="#2c3e50"))
            self.plots["gforce"].getAxis("bottom").setPen(pg.mkPen(color="#2c3e50"))
            self._configure_plot(self.plots["gforce"], "Time", "g")
            if RESPONSIVE_AVAILABLE:
                get_responsive_manager().configure_graph_responsive(self.plots["gforce"])
            layout.addWidget(self.plots["gforce"])

            # GPS graph (Row 4) - Add GPS data graph
            self.plots["gps"] = pg.PlotWidget(title="GPS Data")
            self.plots["gps"].setBackground("w")
            self.plots["gps"].setFixedHeight(GRAPH_HEIGHT)
            self.plots["gps"].setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.plots["gps"].getAxis("left").setPen(pg.mkPen(color="#2c3e50"))
            self.plots["gps"].getAxis("bottom").setPen(pg.mkPen(color="#2c3e50"))
            self._configure_plot(self.plots["gps"], "Time", "Value")
            if RESPONSIVE_AVAILABLE:
                get_responsive_manager().configure_graph_responsive(self.plots["gps"])
            layout.addWidget(self.plots["gps"])

            for channel in self.PRIMARY_CHANNELS:
                self.curves[channel] = self.plots["primary"].plot(
                    pen=pg.mkPen(self.CHANNEL_COLORS.get(channel, "#3498db"), width=2),
                    name=channel,
                )
            for channel in self.SECONDARY_CHANNELS:
                self.curves[channel] = self.plots["secondary"].plot(
                    pen=pg.mkPen(self.CHANNEL_COLORS.get(channel, "#3498db"), width=2),
                    name=channel,
                )
            for channel in self.GFORCE_CHANNELS:
                self.curves[channel] = self.plots["gforce"].plot(
                    pen=pg.mkPen(self.CHANNEL_COLORS.get(channel, "#3498db"), width=2),
                    name=channel.replace("_", " "),
                )
            for channel in self.GPS_CHANNELS:
                self.curves[channel] = self.plots["gps"].plot(
                    pen=pg.mkPen(self.CHANNEL_COLORS.get(channel, "#3498db"), width=2),
                    name=channel.replace("_", " "),
                )

            print("[VERIFY] Telemetry panel: Multiple plot widgets created successfully")
        else:
            fallback_label = QLabel(
                "pyqtgraph not installed; telemetry plots disabled.\nInstall with: pip install pyqtgraph"
            )
            fallback_label.setStyleSheet("color: red; padding: 20px;")
            layout.addWidget(fallback_label)
            print("[WARN] pyqtgraph not available - telemetry plots disabled")

    def _configure_plot(self, plot_widget: "pg.PlotWidget", xlabel: str, ylabel: str) -> None:
        # Position legend to avoid overlapping with values
        legend_offset = scaled_spacing(10)
        plot_widget.addLegend(offset=(legend_offset, legend_offset), colCount=2)
        # Use showGrid without pen parameter (newer pyqtgraph API)
        # Grid will use default styling that matches the light theme
        plot_widget.showGrid(x=True, y=True, alpha=0.2)
        plot_widget.setLabel("bottom", xlabel, **{"color": "#2c3e50"})
        plot_widget.setLabel("left", ylabel, **{"color": "#2c3e50"})
        plot_widget.setMenuEnabled(False)
        # Add border to match other widgets
        border_width = max(1, scaled_spacing(1))
        border_radius = scaled_spacing(4)
        plot_widget.setStyleSheet(f"border: {border_width}px solid #bdc3c7; border-radius: {border_radius}px;")
        
        # Configure axes for proper auto-sizing and prevent label overlap
        # Use responsive manager if available, otherwise use fixed values
        if RESPONSIVE_AVAILABLE:
            # Responsive manager will handle axis configuration
            # It will be called after plot creation via configure_graph_responsive
            pass
        else:
            # Fallback: Configure axes manually
            plot_item = plot_widget.getPlotItem()
            if plot_item:
                # Configure Y-axis (left) to auto-size and prevent overlap
                left_axis = plot_item.getAxis("left")
                if left_axis:
                    # Set sufficient width to accommodate labels and prevent overlap
                    left_axis.setWidth(80)  # Increased width for Y-axis labels to prevent overlap
                    
                    # Enable auto SI prefix to shorten large numbers
                    try:
                        left_axis.setAutoSIPrefix(True)  # Auto SI prefix (k, M, etc.)
                    except AttributeError:
                        pass  # Older pyqtgraph versions may not have this
                
                # Configure X-axis (bottom) similarly
                bottom_axis = plot_item.getAxis("bottom")
                if bottom_axis:
                    try:
                        bottom_axis.setAutoSIPrefix(True)
                    except AttributeError:
                        pass
                    bottom_axis.setHeight(45)  # Minimum height for X-axis labels
                
                # Ensure legend doesn't overlap with axis labels
                legend = plot_item.legend
                if legend:
                    legend.setOffset((legend_offset, legend_offset))
                    legend.setColumnCount(2)  # Two columns to prevent overlap
                
                # Enable auto-range for proper scaling
                plot_item.enableAutoRange(axis='y', enable=True)
                plot_item.enableAutoRange(axis='x', enable=True)
                
                # Set minimum margins to ensure labels are visible and don't overlap
                # left margin for Y-axis labels, bottom margin for X-axis labels
                plot_item.layout.setContentsMargins(scaled_spacing(80), scaled_spacing(10), scaled_spacing(10), scaled_spacing(45))  # left, top, right, bottom
                
                # Enable auto-resize when window is resized
                plot_item.vb.setLimits(minXRange=10, maxXRange=None, minYRange=10, maxYRange=None)

    def update_data(self, data: Mapping[str, float]) -> None:
        if not self.curves:
            return

        # Debug first few updates
        if self.counter < 3:
            print(f"[VERIFY] Telemetry update #{self.counter + 1}: {list(data.keys())[:8]}")

        self.counter += 1
        self.xdata.append(self.counter)

        updated_channels = 0
        # Debug GPS data on first few updates
        if self.counter <= 5:
            gps_keys = [k for k in data.keys() if 'GPS' in k.upper() or 'gps' in k.lower()]
            if gps_keys:
                print(f"[GPS DEBUG] Update #{self.counter}: GPS keys in data: {gps_keys}")
                for gk in gps_keys:
                    print(f"  {gk} = {data.get(gk, 'N/A')}")
        
        for key, curve in self.curves.items():
            # Accept CamelCase fallback keys for compatibility
            aliases = {
                "Boost": "Boost_Pressure",
                "OilPressure": "Oil_Pressure",
                "BrakePressure": "Brake_Pressure",
                "BatteryVoltage": "Battery_Voltage",
                "GForce_Lateral": ("GForce_Lateral", "LatG", "GForce_X", "Lateral_G"),
                "GForce_Longitudinal": ("GForce_Longitudinal", "LongG", "GForce_Y", "Longitudinal_G"),
                "GPS_Speed": ("GPS_Speed", "gps_speed", "GPS_Speed_mps", "speed_mps", "KF_Speed"),
                "GPS_Heading": ("GPS_Heading", "gps_heading", "heading", "GPS_Heading_deg", "KF_Heading"),
                "GPS_Altitude": ("GPS_Altitude", "gps_altitude", "altitude_m", "GPS_Altitude_m"),
            }
            lookup_key = key
            # Handle tuple aliases (for G-forces and GPS)
            if lookup_key in aliases:
                alias_list = aliases[lookup_key]
                if isinstance(alias_list, tuple):
                    # Try each alias in order
                    for alias in alias_list:
                        if alias in data:
                            lookup_key = alias
                            break
                elif alias_list in data:
                    lookup_key = alias_list

            # Try to get value - check both key and lookup_key
            value = None
            if key in data:
                value = float(data[key])
            elif lookup_key in data:
                value = float(data[lookup_key])
            else:
                value = 0.0
            
            if key not in self.data:
                continue
            self.data[key].append(value)
            if curve:
                curve.setData(self.xdata, list(self.data[key]))
                updated_channels += 1
                # Debug GPS channels on first few updates
                if self.counter <= 5 and key in self.GPS_CHANNELS:
                    print(f"[GPS DEBUG] Updated {key} curve: value={value}, data_len={len(self.data[key])}")

        if updated_channels == 0 and self.counter > 5:
            print(f"[WARN] No telemetry curves updated. Available keys: {list(data.keys())}")


__all__ = ["TelemetryPanel"]

