"""
Safety Alerts System
Clear, unmistakable visual and auditory warnings for potential problems
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_stylesheet, RacingColor


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class SafetyAlert:
    """Safety alert information."""
    alert_id: str
    severity: AlertSeverity
    title: str
    message: str
    action_required: str
    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False
    data: Dict[str, float] = field(default_factory=dict)


class SafetyAlertsSystem(QObject):
    """
    Safety alerts system with clear, unmistakable warnings.
    
    Features:
    - Visual alerts with high contrast
    - Auditory warnings (optional)
    - Priority-based alerting
    - Actionable recommendations
    """
    
    # Signals
    alert_triggered = Signal(SafetyAlert)
    alert_acknowledged = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.active_alerts: Dict[str, SafetyAlert] = {}
        self.alert_history: List[SafetyAlert] = []
        self.audio_enabled = True
    
    def check_conditions(self, telemetry: Dict[str, float]) -> List[SafetyAlert]:
        """
        Check telemetry for safety conditions and generate alerts.
        
        Args:
            telemetry: Current telemetry data
            
        Returns:
            List of triggered alerts
        """
        alerts = []
        
        # Critical AFR check
        afr = telemetry.get("AFR", telemetry.get("lambda_value", 1.0) * 14.7)
        if afr > 16.0:
            alert = SafetyAlert(
                alert_id="lean_critical",
                severity=AlertSeverity.EMERGENCY,
                title="CRITICAL: LEAN CONDITION",
                message=f"AFR is dangerously lean: {afr:.2f}",
                action_required="IMMEDIATELY reduce throttle or add fuel",
                data={"AFR": afr}
            )
            alerts.append(alert)
        elif afr > 15.0:
            alert = SafetyAlert(
                alert_id="lean_warning",
                severity=AlertSeverity.CRITICAL,
                title="WARNING: LEAN CONDITION",
                message=f"AFR is lean: {afr:.2f}",
                action_required="Add fuel or reduce throttle",
                data={"AFR": afr}
            )
            alerts.append(alert)
        
        # EGT check
        egt = telemetry.get("EGT", telemetry.get("ExhaustTemp", 800))
        if egt > 1700:
            alert = SafetyAlert(
                alert_id="egt_critical",
                severity=AlertSeverity.EMERGENCY,
                title="CRITICAL: EGT TOO HIGH",
                message=f"Exhaust gas temperature critical: {egt:.0f}°C",
                action_required="IMMEDIATELY reduce power or add fuel",
                data={"EGT": egt}
            )
            alerts.append(alert)
        elif egt > 1600:
            alert = SafetyAlert(
                alert_id="egt_warning",
                severity=AlertSeverity.CRITICAL,
                title="WARNING: HIGH EGT",
                message=f"Exhaust gas temperature high: {egt:.0f}°C",
                action_required="Reduce timing or add fuel",
                data={"EGT": egt}
            )
            alerts.append(alert)
        
        # Coolant temperature
        coolant = telemetry.get("Coolant_Temp", telemetry.get("ECT", 90))
        if coolant > 110:
            alert = SafetyAlert(
                alert_id="coolant_critical",
                severity=AlertSeverity.CRITICAL,
                title="WARNING: ENGINE OVERHEATING",
                message=f"Coolant temperature critical: {coolant:.0f}°C",
                action_required="Reduce power and check cooling system",
                data={"Coolant_Temp": coolant}
            )
            alerts.append(alert)
        
        # Oil pressure
        oil_pressure = telemetry.get("Oil_Pressure", telemetry.get("oil_pressure", 50))
        if oil_pressure < 20:
            alert = SafetyAlert(
                alert_id="oil_pressure_critical",
                severity=AlertSeverity.EMERGENCY,
                title="EMERGENCY: LOW OIL PRESSURE",
                message=f"Oil pressure critically low: {oil_pressure:.1f} psi",
                action_required="IMMEDIATELY shut down engine",
                data={"Oil_Pressure": oil_pressure}
            )
            alerts.append(alert)
        
        # Knock detection
        knock = telemetry.get("Knock_Count", telemetry.get("knock_retard", 0))
        if knock > 10:
            alert = SafetyAlert(
                alert_id="knock_critical",
                severity=AlertSeverity.CRITICAL,
                title="WARNING: EXCESSIVE KNOCK",
                message=f"Knock count high: {knock}",
                action_required="Retard ignition timing immediately",
                data={"Knock": knock}
            )
            alerts.append(alert)
        
        # Process alerts
        for alert in alerts:
            if alert.alert_id not in self.active_alerts:
                self.active_alerts[alert.alert_id] = alert
                self.alert_history.append(alert)
                self.alert_triggered.emit(alert)
        
        # Remove resolved alerts
        alert_ids = {a.alert_id for a in alerts}
        resolved = [aid for aid in self.active_alerts.keys() if aid not in alert_ids]
        for aid in resolved:
            del self.active_alerts[aid]
        
        return alerts


class SafetyAlertsPanel(QWidget):
    """UI panel for displaying safety alerts."""
    
    def __init__(self, alerts_system: SafetyAlertsSystem, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.alerts_system = alerts_system
        self.setup_ui()
        
        # Connect signals
        self.alerts_system.alert_triggered.connect(self._on_alert_triggered)
        self.alerts_system.alert_acknowledged.connect(self._on_alert_acknowledged)
    
    def setup_ui(self) -> None:
        """Setup alerts panel."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.scaler.scale(5))
        
        # Active alerts (critical/emergency only)
        self.active_alerts_list = QListWidget()
        self.active_alerts_list.setStyleSheet("""
            QListWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 2px solid #ff0000;
                font-size: 14px;
                font-weight: bold;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #404040;
            }
        """)
        self.active_alerts_list.setMaximumHeight(self.scaler.get_scaled_size(200))
        layout.addWidget(self.active_alerts_list)
        
        # Emergency alert banner (for critical alerts)
        self.emergency_banner = QLabel()
        self.emergency_banner.setVisible(False)
        self.emergency_banner.setStyleSheet(f"""
            QLabel {{
                background-color: {RacingColor.ACCENT_NEON_RED.value};
                color: #ffffff;
                font-size: {get_scaled_font_size(20)}px;
                font-weight: bold;
                padding: {get_scaled_size(15)}px;
                border: {get_scaled_size(3)}px solid {RacingColor.ACCENT_NEON_RED.value};
                text-align: center;
            }}
        """)
        self.emergency_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.emergency_banner)
    
    def _on_alert_triggered(self, alert: SafetyAlert) -> None:
        """Handle new alert."""
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
            # Add to active alerts list
            item = QListWidgetItem(f"⚠ {alert.title}: {alert.message}")
            
            if alert.severity == AlertSeverity.EMERGENCY:
                item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_RED.value)))
                item.setBackground(QBrush(QColor("#ff000033")))
                # Show emergency banner
                self.emergency_banner.setText(f"⚠ EMERGENCY: {alert.message} - {alert.action_required}")
                self.emergency_banner.setVisible(True)
            else:
                item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_ORANGE.value)))
                item.setBackground(QBrush(QColor("#ff800033")))
            
            item.setData(Qt.ItemDataRole.UserRole, alert)
            self.active_alerts_list.addItem(item)
            
            # Scroll to top
            self.active_alerts_list.scrollToTop()
    
    def _on_alert_acknowledged(self, alert_id: str) -> None:
        """Handle alert acknowledgment."""
        # Remove from list
        for i in range(self.active_alerts_list.count()):
            item = self.active_alerts_list.item(i)
            if item:
                alert = item.data(Qt.ItemDataRole.UserRole)
                if alert and alert.alert_id == alert_id:
                    self.active_alerts_list.takeItem(i)
                    break
        
        # Hide emergency banner if no critical alerts
        if self.active_alerts_list.count() == 0:
            self.emergency_banner.setVisible(False)

