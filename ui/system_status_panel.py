"""
System Status Panel - Modern, visual system monitoring dashboard.

Displays:
- Live system health indicators with animated status rings
- Active fault codes with severity visualization
- Real-time notification feed with auto-fade
- Subsystem connectivity status
"""

from __future__ import annotations

import math
import time
from collections import deque
from enum import Enum
from typing import Deque, Dict, List, Optional, Tuple

from PySide6.QtCore import Property, QPropertyAnimation, QTimer, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QLinearGradient
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SystemHealth(Enum):
    """System health status levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class SubsystemStatus(Enum):
    """Individual subsystem status."""
    ONLINE = "online"
    DEGRADED = "degraded"
    ERROR = "error"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class StatusRing(QWidget):
    """
    Animated circular status indicator with pulsing effect.
    """
    
    def __init__(
        self,
        label: str,
        size: int = 60,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        
        self.label = label
        self.ring_size = size
        self.status = SubsystemStatus.UNKNOWN
        self.value = 0.0  # 0-100 for arc fill
        self._pulse_phase = 0.0
        
        # Colors
        self.colors = {
            SubsystemStatus.ONLINE: "#27ae60",
            SubsystemStatus.DEGRADED: "#f39c12",
            SubsystemStatus.ERROR: "#e74c3c",
            SubsystemStatus.OFFLINE: "#7f8c8d",
            SubsystemStatus.UNKNOWN: "#95a5a6",
        }
        
        self.setMinimumSize(size + 20, size + 35)
        self.setMaximumSize(size + 25, size + 40)
        
        # Pulse animation timer
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.pulse_timer.start(50)
    
    def set_status(self, status: SubsystemStatus, value: float = 100.0) -> None:
        """Set the status and fill value."""
        self.status = status
        self.value = max(0, min(100, value))
        self.update()
    
    def _update_pulse(self) -> None:
        """Update pulse animation phase."""
        self._pulse_phase = (self._pulse_phase + 0.1) % (2 * math.pi)
        self.update()
    
    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint the status ring."""
        try:
            painter = QPainter(self)
            if not painter.isActive():
                return
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            width = self.width()
            height = self.height()
            
            # Ring dimensions
            ring_x = (width - self.ring_size) // 2
            ring_y = 5
            
            # Get status color
            color = QColor(self.colors.get(self.status, "#95a5a6"))
            
            # Draw background ring
            bg_color = QColor("#1a1f35")
            bg_color.setAlpha(100)
            pen = QPen(bg_color, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(ring_x, ring_y, self.ring_size, self.ring_size, 0, 360 * 16)
            
            # Draw status arc (based on value)
            arc_span = int((self.value / 100.0) * 360)
            
            # Pulse effect for online status
            if self.status == SubsystemStatus.ONLINE:
                pulse = 0.8 + 0.2 * math.sin(self._pulse_phase)
                color.setAlphaF(pulse)
            
            pen = QPen(color, 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(ring_x, ring_y, self.ring_size, self.ring_size, 90 * 16, -arc_span * 16)
            
            # Draw center icon/indicator
            center_x = ring_x + self.ring_size // 2
            center_y = ring_y + self.ring_size // 2
            
            # Status dot
            dot_color = QColor(color)
            dot_color.setAlpha(255)
            painter.setBrush(QBrush(dot_color))
            painter.setPen(Qt.PenStyle.NoPen)
            dot_size = 12 if self.status == SubsystemStatus.ONLINE else 8
            painter.drawEllipse(center_x - dot_size // 2, center_y - dot_size // 2, dot_size, dot_size)
            
            # Draw label
            painter.setPen(QColor("#2c3e50"))
            font = QFont("Arial", 8, QFont.Weight.Bold)
            painter.setFont(font)
            label_rect = painter.fontMetrics().boundingRect(self.label)
            painter.drawText(
                width // 2 - label_rect.width() // 2,
                height - 5,
                self.label,
            )
            
        except Exception as e:
            print(f"[WARN] StatusRing.paintEvent error: {e}")


class FaultIndicator(QFrame):
    """
    Visual fault code indicator with severity styling.
    """
    
    def __init__(
        self,
        code: str,
        description: str,
        severity: str = "warning",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(50)
        self.setMaximumHeight(70)
        
        # Severity colors
        severity_colors = {
            "critical": ("#c62828", "#ffebee", "🔴"),
            "warning": ("#e65100", "#fff3e0", "🟡"),
            "info": ("#1565c0", "#e3f2fd", "🔵"),
            "pending": ("#6a1b9a", "#f3e5f5", "🟣"),
        }
        
        text_color, bg_color, icon = severity_colors.get(severity, severity_colors["info"])
        
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {bg_color}, stop:0.02 {text_color}, stop:0.025 {bg_color});
                border: 1px solid {text_color};
                border-radius: 6px;
                border-left: 4px solid {text_color};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px; background: transparent;")
        layout.addWidget(icon_label)
        
        # Code and description
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        code_label = QLabel(code)
        code_label.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {text_color}; background: transparent;")
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 10px; color: #555; background: transparent;")
        desc_label.setWordWrap(True)
        
        text_layout.addWidget(code_label)
        text_layout.addWidget(desc_label)
        layout.addLayout(text_layout, 1)


class NotificationFeed(QWidget):
    """
    Modern notification feed with animated entries.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 3px;
                min-height: 20px;
            }
        """)
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.feed_layout = QVBoxLayout(self.container)
        self.feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_layout.setSpacing(3)
        self.feed_layout.addStretch()
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
        
        self.notifications: Deque[Tuple[float, QWidget]] = deque(maxlen=15)
        
        # Cleanup timer
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self._cleanup)
        self.cleanup_timer.start(1000)
    
    def add_notification(self, message: str, level: str = "info") -> None:
        """Add a notification to the feed."""
        # Create notification widget
        notif = QFrame()
        notif.setMinimumHeight(28)
        notif.setMaximumHeight(35)
        
        # Level styling
        level_config = {
            "info": ("#3498db", "ℹ️"),
            "success": ("#27ae60", "✅"),
            "warning": ("#f39c12", "⚠️"),
            "error": ("#e74c3c", "❌"),
        }
        color, icon = level_config.get(level, level_config["info"])
        
        notif.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border-left: 3px solid {color};
                border-radius: 4px;
            }}
        """)
        
        notif_layout = QHBoxLayout(notif)
        notif_layout.setContentsMargins(8, 4, 8, 4)
        notif_layout.setSpacing(6)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 12px; background: transparent;")
        
        time_str = time.strftime("%H:%M:%S")
        msg_label = QLabel(f"<span style='color:#888;font-size:9px;'>{time_str}</span> {message}")
        msg_label.setStyleSheet("font-size: 10px; color: #2c3e50; background: transparent;")
        msg_label.setWordWrap(True)
        
        notif_layout.addWidget(icon_label)
        notif_layout.addWidget(msg_label, 1)
        
        # Insert at top
        self.feed_layout.insertWidget(0, notif)
        self.notifications.append((time.time() + 30, notif))  # 30 second expiry
    
    def _cleanup(self) -> None:
        """Remove expired notifications."""
        now = time.time()
        while self.notifications and self.notifications[0][0] < now:
            _, widget = self.notifications.popleft()
            widget.deleteLater()


class SystemStatusPanel(QFrame):
    """
    Complete system status monitoring panel with modern visual design.
    
    Features:
    - Animated subsystem status rings
    - Visual fault code display
    - Real-time notification feed
    - Overall system health indicator
    """
    
    fault_cleared = Signal()
    
    def __init__(self, obd_interface=None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self.obd = obd_interface
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame#SystemStatusPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f5f6fa);
                border: 1px solid #dcdde1;
                border-radius: 10px;
            }
        """)
        self.setObjectName("SystemStatusPanel")
        
        self.setMinimumSize(280, 450)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header with overall health
        header = self._create_header()
        layout.addWidget(header)
        
        # Subsystem status rings
        status_section = self._create_status_rings()
        layout.addWidget(status_section)
        
        # Fault codes section
        fault_section = self._create_fault_section()
        layout.addWidget(fault_section, 1)
        
        # Notification feed
        feed_section = self._create_notification_section()
        layout.addWidget(feed_section)
        
        # Demo timer
        self.demo_timer = QTimer(self)
        self.demo_timer.timeout.connect(self._update_demo)
        self.demo_timer.start(2000)
        
        # Initialize with demo data
        self._init_demo_state()
    
    def _create_header(self) -> QWidget:
        """Create header with overall health indicator."""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("🖥️ System Status")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        
        # Overall health badge
        self.health_badge = QLabel("● HEALTHY")
        self.health_badge.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            font-size: 10px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 10px;
        """)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.health_badge)
        
        return header
    
    def _create_status_rings(self) -> QWidget:
        """Create subsystem status ring indicators."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(6)
        
        # Section title
        title = QLabel("Subsystems")
        title.setStyleSheet("font-size: 11px; font-weight: bold; color: #7f8c8d;")
        section_layout.addWidget(title)
        
        # Status rings in a grid
        ring_container = QWidget()
        ring_layout = QGridLayout(ring_container)
        ring_layout.setSpacing(8)
        ring_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_rings: Dict[str, StatusRing] = {}
        
        subsystems = [
            ("ECU", "ECU"),
            ("OBD", "OBD"),
            ("GPS", "GPS"),
            ("CAM", "Camera"),
            ("NET", "Network"),
            ("USB", "Storage"),
        ]
        
        for i, (key, label) in enumerate(subsystems):
            ring = StatusRing(label, size=50)
            self.status_rings[key] = ring
            ring_layout.addWidget(ring, i // 3, i % 3)
        
        section_layout.addWidget(ring_container)
        return section
    
    def _create_fault_section(self) -> QWidget:
        """Create fault codes display section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(10, 10, 10, 10)
        section_layout.setSpacing(8)
        
        # Header with buttons
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("⚠️ Fault Codes")
        title.setStyleSheet("font-size: 11px; font-weight: bold; color: #2c3e50; background: transparent;")
        
        self.fault_count_badge = QLabel("0")
        self.fault_count_badge.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            font-size: 10px;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 8px;
        """)
        
        header_layout.addWidget(title)
        header_layout.addWidget(self.fault_count_badge)
        header_layout.addStretch()
        
        # Buttons
        self.refresh_btn = QPushButton("🔄 Scan")
        self.clear_btn = QPushButton("🗑️ Clear")
        
        btn_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
        self.refresh_btn.setStyleSheet(btn_style)
        self.clear_btn.setStyleSheet(btn_style.replace("#3498db", "#e74c3c").replace("#2980b9", "#c0392b"))
        
        self.refresh_btn.clicked.connect(self.scan_faults)
        self.clear_btn.clicked.connect(self.clear_faults)
        
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.clear_btn)
        
        section_layout.addWidget(header)
        
        # Fault list scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")
        
        self.fault_container = QWidget()
        self.fault_container.setStyleSheet("background: transparent;")
        self.fault_layout = QVBoxLayout(self.fault_container)
        self.fault_layout.setContentsMargins(0, 0, 0, 0)
        self.fault_layout.setSpacing(6)
        
        # Placeholder
        self.no_faults_label = QLabel("✅ No active fault codes")
        self.no_faults_label.setStyleSheet("""
            color: #27ae60;
            font-size: 11px;
            padding: 20px;
            background: transparent;
        """)
        self.no_faults_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fault_layout.addWidget(self.no_faults_label)
        self.fault_layout.addStretch()
        
        scroll.setWidget(self.fault_container)
        section_layout.addWidget(scroll, 1)
        
        return section
    
    def _create_notification_section(self) -> QWidget:
        """Create notification feed section."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(4)
        
        title = QLabel("📢 Notifications")
        title.setStyleSheet("font-size: 11px; font-weight: bold; color: #7f8c8d;")
        section_layout.addWidget(title)
        
        self.notification_feed = NotificationFeed()
        section_layout.addWidget(self.notification_feed)
        
        return section
    
    def _init_demo_state(self) -> None:
        """Initialize demo state."""
        # Set initial status
        self.status_rings["ECU"].set_status(SubsystemStatus.ONLINE, 100)
        self.status_rings["OBD"].set_status(SubsystemStatus.ONLINE, 100)
        self.status_rings["GPS"].set_status(SubsystemStatus.DEGRADED, 60)
        self.status_rings["CAM"].set_status(SubsystemStatus.ONLINE, 100)
        self.status_rings["NET"].set_status(SubsystemStatus.ONLINE, 85)
        self.status_rings["USB"].set_status(SubsystemStatus.ONLINE, 100)
        
        # Initial notifications
        self.notification_feed.add_notification("System initialized", "success")
        self.notification_feed.add_notification("ECU connection established", "info")
    
    def _update_demo(self) -> None:
        """Update demo data."""
        import random
        
        # Randomly update a subsystem
        keys = list(self.status_rings.keys())
        key = random.choice(keys)
        
        # Random status changes (mostly stay online)
        if random.random() < 0.1:
            statuses = [SubsystemStatus.ONLINE, SubsystemStatus.DEGRADED]
            self.status_rings[key].set_status(
                random.choice(statuses),
                random.uniform(70, 100),
            )
        
        # Random notifications
        if random.random() < 0.15:
            messages = [
                ("Data stream active", "info"),
                ("Telemetry logged", "success"),
                ("GPS signal acquired", "success"),
                ("Cloud sync complete", "info"),
            ]
            msg, level = random.choice(messages)
            self.notification_feed.add_notification(msg, level)
    
    def set_obd_interface(self, interface) -> None:
        """Set OBD interface."""
        self.obd = interface
    
    def set_subsystem_status(self, subsystem: str, status: SubsystemStatus, value: float = 100) -> None:
        """Set status for a specific subsystem."""
        if subsystem in self.status_rings:
            self.status_rings[subsystem].set_status(status, value)
    
    def add_fault(self, code: str, description: str, severity: str = "warning") -> None:
        """Add a fault code to the display."""
        self.no_faults_label.hide()
        
        indicator = FaultIndicator(code, description, severity)
        self.fault_layout.insertWidget(0, indicator)
        
        # Update badge
        count = self.fault_layout.count() - 2  # Subtract stretch and hidden label
        self.fault_count_badge.setText(str(max(0, count)))
        
        if count > 0:
            self.fault_count_badge.setStyleSheet("""
                background-color: #e74c3c;
                color: white;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 8px;
            """)
            self.health_badge.setText("● WARNING")
            self.health_badge.setStyleSheet("""
                background-color: #f39c12;
                color: white;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 10px;
                border-radius: 10px;
            """)
    
    def clear_faults_display(self) -> None:
        """Clear all fault indicators from display."""
        while self.fault_layout.count() > 2:
            item = self.fault_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.no_faults_label.show()
        self.fault_count_badge.setText("0")
        self.fault_count_badge.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            font-size: 10px;
            font-weight: bold;
            padding: 2px 8px;
            border-radius: 8px;
        """)
        self.health_badge.setText("● HEALTHY")
        self.health_badge.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            font-size: 10px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 10px;
        """)
    
    def scan_faults(self) -> None:
        """Scan for fault codes."""
        if self.obd:
            codes = self.obd.get_dtc_codes()
            self.clear_faults_display()
            for code, desc in codes:
                severity = "critical" if code.startswith("P0") else "warning"
                self.add_fault(code, desc, severity)
        else:
            # Demo mode - add some sample faults
            self.clear_faults_display()
            import random
            if random.random() < 0.5:
                self.add_fault("P0300", "Random/Multiple Cylinder Misfire Detected", "warning")
            if random.random() < 0.3:
                self.add_fault("P0420", "Catalyst System Efficiency Below Threshold", "info")
        
        self.notification_feed.add_notification("Fault scan complete", "info")
    
    def clear_faults(self) -> None:
        """Clear fault codes."""
        if self.obd:
            self.obd.clear_dtc_codes()
        
        self.clear_faults_display()
        self.notification_feed.add_notification("Fault codes cleared", "success")
        self.fault_cleared.emit()
    
    def show_notification(self, message: str, level: str = "info") -> None:
        """Add a notification to the feed."""
        self.notification_feed.add_notification(message, level)
    
    def stop_demo(self) -> None:
        """Stop demo updates."""
        self.demo_timer.stop()


__all__ = [
    "SystemStatusPanel",
    "StatusRing",
    "FaultIndicator",
    "NotificationFeed",
    "SystemHealth",
    "SubsystemStatus",
]






