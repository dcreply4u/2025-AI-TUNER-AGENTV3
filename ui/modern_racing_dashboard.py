"""
Modern Racing Dashboard
Customizable cockpit view with essential real-time data, digital gauges, and warning indicators.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Callable

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)

from ui.ui_scaling import get_scaled_size, get_scaled_font_size
from ui.gauge_widget import CircularGauge

LOGGER = logging.getLogger(__name__)

# Warning thresholds (extracted from magic numbers)
COOLANT_CRITICAL_THRESHOLD = 110.0  # °F
COOLANT_WARNING_THRESHOLD = 100.0   # °F
KNOCK_CRITICAL_THRESHOLD = 80.0     # %
KNOCK_WARNING_THRESHOLD = 50.0      # %
AFR_CRITICAL_THRESHOLD = 16.0       # :1
AFR_WARNING_THRESHOLD = 15.0        # :1
BOOST_CRITICAL_THRESHOLD = 25.0     # psi
BOOST_WARNING_THRESHOLD = 20.0      # psi


class WarningIndicator(QWidget):
    """Color-coded warning indicator with flashing capability."""
    
    def __init__(self, label: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.label = label
        self.is_flashing = False
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self._toggle_flash)
        self.current_state = False
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup warning indicator UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.indicator = QLabel(self.label)
        font_size = get_scaled_font_size(14)
        self.indicator.setStyleSheet(f"""
            font-size: {font_size}px;
            font-weight: bold;
            color: #ffffff;
            background-color: transparent;
            padding: 8px;
            border-radius: 4px;
        """)
        layout.addWidget(self.indicator)
    
    def set_warning(self, severity: str = "warning") -> None:
        """Set warning state."""
        colors = {
            "warning": "#ffaa00",  # Yellow
            "error": "#ff4444",     # Red
            "critical": "#ff0000",  # Bright red
        }
        color = colors.get(severity, "#ffaa00")
        self.indicator.setStyleSheet(f"""
            font-size: {get_scaled_font_size(14)}px;
            font-weight: bold;
            color: #ffffff;
            background-color: {color};
            padding: 8px;
            border-radius: 4px;
        """)
        self.start_flashing(severity == "critical")
    
    def set_normal(self) -> None:
        """Set normal state."""
        self.indicator.setStyleSheet(f"""
            font-size: {get_scaled_font_size(14)}px;
            font-weight: bold;
            color: #00ff00;
            background-color: transparent;
            padding: 8px;
            border-radius: 4px;
        """)
        self.stop_flashing()
    
    def start_flashing(self, enabled: bool = True) -> None:
        """Start flashing animation."""
        if enabled and not self.is_flashing:
            self.is_flashing = True
            self.flash_timer.start(500)  # Flash every 500ms
        elif not enabled:
            self.stop_flashing()
    
    def stop_flashing(self) -> None:
        """Stop flashing animation."""
        self.is_flashing = False
        self.flash_timer.stop()
        self.current_state = False
    
    def _toggle_flash(self) -> None:
        """Toggle flash state."""
        self.current_state = not self.current_state
        opacity = "0.3" if self.current_state else "1.0"
        style = self.indicator.styleSheet()
        # Update opacity by modifying background color
        if "background-color:" in style:
            bg_color = style.split("background-color:")[1].split(";")[0].strip()
            if bg_color.startswith("#"):
                # Convert hex to rgba
                r = int(bg_color[1:3], 16)
                g = int(bg_color[3:5], 16)
                b = int(bg_color[5:7], 16)
                new_style = style.replace(
                    f"background-color: {bg_color}",
                    f"background-color: rgba({r}, {g}, {b}, {opacity})"
                )
                self.indicator.setStyleSheet(new_style)


class ConnectionStatusIndicator(QWidget):
    """Visual connection status indicator."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
        self.set_connected(False)
    
    def setup_ui(self) -> None:
        """Setup connection status UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        self.status_led = QLabel("●")
        font_size = get_scaled_font_size(20)
        self.status_led.setStyleSheet(f"""
            font-size: {font_size}px;
            color: #ff4444;
        """)
        layout.addWidget(self.status_led)
        
        self.status_label = QLabel("Disconnected")
        font_size = get_scaled_font_size(12)
        self.status_label.setStyleSheet(f"""
            font-size: {font_size}px;
            color: #ffffff;
        """)
        layout.addWidget(self.status_label)
    
    def set_connected(self, connected: bool, connection_type: str = "USB") -> None:
        """Set connection status."""
        if connected:
            self.status_led.setStyleSheet(f"""
                font-size: {get_scaled_font_size(20)}px;
                color: #00ff00;
            """)
            self.status_label.setText(f"{connection_type} Connected")
            self.status_label.setStyleSheet(f"""
                font-size: {get_scaled_font_size(12)}px;
                color: #00ff00;
            """)
        else:
            self.status_led.setStyleSheet(f"""
                font-size: {get_scaled_font_size(20)}px;
                color: #ff4444;
            """)
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet(f"""
                font-size: {get_scaled_font_size(12)}px;
                color: #ff4444;
            """)


class PanicButton(QPushButton):
    """Emergency panic button for flashing safe stock map."""
    
    panic_activated = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("PANIC\nSAFE MAP", parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup panic button UI."""
        font_size = get_scaled_font_size(16)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #ff0000;
                color: #ffffff;
                font-size: {font_size}px;
                font-weight: bold;
                border: 3px solid #ffffff;
                border-radius: 8px;
                padding: 15px 25px;
                min-width: 120px;
                min-height: 80px;
            }}
            QPushButton:hover {{
                background-color: #ff3333;
                border: 3px solid #ffff00;
            }}
            QPushButton:pressed {{
                background-color: #cc0000;
            }}
        """)
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self) -> None:
        """Handle panic button click."""
        self.panic_activated.emit()


class ModernRacingDashboard(QWidget):
    """
    Modern racing dashboard with customizable cockpit view.
    
    Features:
    - Digital gauges for RPM, speed, boost, temperature, AFR, knock
    - Color-coded warning indicators
    - Quick access buttons (data logging, AI Advisor)
    - Connection status indicator
    - Panic button for emergency safe map
    """
    
    def __init__(
        self,
        telemetry_provider: Optional[Callable[[], Dict[str, float]]] = None,
        panic_callback: Optional[Callable[[], None]] = None,
        ai_advisor_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        # Validate callbacks are callable
        if telemetry_provider is not None and not callable(telemetry_provider):
            raise TypeError("telemetry_provider must be callable or None")
        if panic_callback is not None and not callable(panic_callback):
            raise TypeError("panic_callback must be callable or None")
        if ai_advisor_callback is not None and not callable(ai_advisor_callback):
            raise TypeError("ai_advisor_callback must be callable or None")
        
        self.telemetry_provider = telemetry_provider
        self.panic_callback = panic_callback
        self.ai_advisor_callback = ai_advisor_callback
        
        self.gauges: Dict[str, CircularGauge] = {}
        self.warning_indicators: Dict[str, WarningIndicator] = {}
        self.logging_active = False
        
        self.setup_ui()
        self._start_update_timer()
    
    def setup_ui(self) -> None:
        """Setup dashboard UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Dark background
        self.setStyleSheet("""
            QWidget {
                background-color: #0a0e27;
                color: #ffffff;
            }
        """)
        
        # Top bar: Connection status, quick actions
        top_bar = QHBoxLayout()
        
        # Connection status
        self.connection_status = ConnectionStatusIndicator()
        top_bar.addWidget(self.connection_status)
        
        top_bar.addStretch()
        
        # Quick action buttons
        self.logging_btn = QPushButton("Start Logging")
        font_size = get_scaled_font_size(12)
        self.logging_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #00e0ff;
                color: #000000;
                font-size: {font_size}px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #33e8ff;
            }}
        """)
        self.logging_btn.clicked.connect(self._toggle_logging)
        top_bar.addWidget(self.logging_btn)
        
        # AI Advisor button
        self.ai_btn = QPushButton("AI Advisor")
        self.ai_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #00ff88;
                color: #000000;
                font-size: {font_size}px;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #33ffaa;
            }}
        """)
        if self.ai_advisor_callback:
            self.ai_btn.clicked.connect(self.ai_advisor_callback)
        top_bar.addWidget(self.ai_btn)
        
        main_layout.addLayout(top_bar)
        
        # Gauges grid
        gauges_layout = QGridLayout()
        gauges_layout.setSpacing(15)
        
        # Create gauges
        gauge_configs = [
            ("RPM", 0, 8000, "rpm", 0, 0),
            ("Speed", 0, 200, "mph", 0, 1),
            ("Boost", -5, 30, "psi", 0, 2),
            ("CoolantTemp", 70, 120, "°F", 1, 0),
            ("AFR", 10, 18, ":1", 1, 1),
            ("Knock", 0, 100, "%", 1, 2),
        ]
        
        for name, min_val, max_val, unit, row, col in gauge_configs:
            gauge = CircularGauge(name, min_value=min_val, max_value=max_val, unit=unit)
            self.gauges[name] = gauge
            gauges_layout.addWidget(gauge, row, col)
        
        main_layout.addLayout(gauges_layout, stretch=1)
        
        # Warning indicators
        warnings_layout = QHBoxLayout()
        
        self.warning_indicators["overheat"] = WarningIndicator("Overheat")
        self.warning_indicators["knock"] = WarningIndicator("Knock")
        self.warning_indicators["lean"] = WarningIndicator("Lean AFR")
        self.warning_indicators["overboost"] = WarningIndicator("Overboost")
        
        for indicator in self.warning_indicators.values():
            warnings_layout.addWidget(indicator)
            indicator.set_normal()
        
        warnings_layout.addStretch()
        
        # Panic button
        self.panic_btn = PanicButton()
        if self.panic_callback:
            self.panic_btn.panic_activated.connect(self.panic_callback)
        warnings_layout.addWidget(self.panic_btn)
        
        main_layout.addLayout(warnings_layout)
    
    def _start_update_timer(self) -> None:
        """Start update timer for real-time data."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_data)
        self.update_timer.start(100)  # Update every 100ms
    
    def _update_data(self) -> None:
        """Update dashboard with latest telemetry data."""
        if not self.telemetry_provider:
            return
        
        try:
            telemetry = self.telemetry_provider()
            if not telemetry:
                return
            
            # Update gauges
            for name, gauge in self.gauges.items():
                value = telemetry.get(name, 0)
                gauge.set_value(value)
            
            # Validate telemetry data
            if not isinstance(telemetry, dict):
                LOGGER.warning("Invalid telemetry data type: %s", type(telemetry))
                return
            
            # Update gauges with validation
            for name, gauge in self.gauges.items():
                value = telemetry.get(name, 0)
                # Validate value is numeric
                try:
                    value = float(value)
                    # Check for NaN or Infinity
                    if not (float('-inf') < value < float('inf')):
                        LOGGER.debug("Invalid gauge value for %s: %s", name, value)
                        continue
                    gauge.set_value(value)
                except (TypeError, ValueError) as e:
                    LOGGER.debug("Invalid gauge value for %s: %s", name, value)
                    continue
            
            # Update warning indicators with validated thresholds
            # Overheat warning
            try:
                coolant = float(telemetry.get("CoolantTemp", 0))
                if coolant > COOLANT_CRITICAL_THRESHOLD:
                    self.warning_indicators["overheat"].set_warning("critical")
                elif coolant > COOLANT_WARNING_THRESHOLD:
                    self.warning_indicators["overheat"].set_warning("warning")
                else:
                    self.warning_indicators["overheat"].set_normal()
            except (TypeError, ValueError):
                pass  # Invalid coolant value, skip warning update
            
            # Knock warning
            try:
                knock = float(telemetry.get("Knock", 0))
                if knock > KNOCK_CRITICAL_THRESHOLD:
                    self.warning_indicators["knock"].set_warning("critical")
                elif knock > KNOCK_WARNING_THRESHOLD:
                    self.warning_indicators["knock"].set_warning("warning")
                else:
                    self.warning_indicators["knock"].set_normal()
            except (TypeError, ValueError):
                pass  # Invalid knock value, skip warning update
            
            # Lean AFR warning
            try:
                afr = float(telemetry.get("AFR", 14.7))
                if afr > AFR_CRITICAL_THRESHOLD:
                    self.warning_indicators["lean"].set_warning("critical")
                elif afr > AFR_WARNING_THRESHOLD:
                    self.warning_indicators["lean"].set_warning("warning")
                else:
                    self.warning_indicators["lean"].set_normal()
            except (TypeError, ValueError):
                pass  # Invalid AFR value, skip warning update
            
            # Overboost warning
            try:
                boost = float(telemetry.get("Boost", 0))
                if boost > BOOST_CRITICAL_THRESHOLD:
                    self.warning_indicators["overboost"].set_warning("critical")
                elif boost > BOOST_WARNING_THRESHOLD:
                    self.warning_indicators["overboost"].set_warning("warning")
                else:
                    self.warning_indicators["overboost"].set_normal()
            except (TypeError, ValueError):
                pass  # Invalid boost value, skip warning update
                
        except (KeyError, TypeError, AttributeError) as e:
            LOGGER.warning("Failed to update dashboard (expected error): %s", e)
        except Exception as e:
            LOGGER.error("Unexpected error updating dashboard: %s", e, exc_info=True)
    
    def _toggle_logging(self) -> None:
        """Toggle data logging."""
        self.logging_active = not self.logging_active
        if self.logging_active:
            self.logging_btn.setText("Stop Logging")
            self.logging_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #ff4444;
                    color: #ffffff;
                    font-size: {get_scaled_font_size(12)}px;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: #ff6666;
                }}
            """)
        else:
            self.logging_btn.setText("Start Logging")
            self.logging_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #00e0ff;
                    color: #000000;
                    font-size: {get_scaled_font_size(12)}px;
                    font-weight: bold;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: #33e8ff;
                }}
            """)
    
    def set_connection_status(self, connected: bool, connection_type: str = "USB") -> None:
        """Update connection status."""
        self.connection_status.set_connected(connected, connection_type)

