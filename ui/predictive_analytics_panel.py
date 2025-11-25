"""
Predictive Analytics & Tips Panel
Smart systems that analyze data and offer actionable setup recommendations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_stylesheet, RacingColor


@dataclass
class AnalyticsTip:
    """Analytics tip/recommendation."""
    category: str  # "Performance", "Safety", "Efficiency", "Setup"
    priority: str  # "low", "medium", "high", "critical"
    message: str
    action: Optional[str] = None
    confidence: float = 0.0  # 0-1
    data_points: Dict[str, float] = None  # type: ignore


class PredictiveAnalyticsPanel(QWidget):
    """
    Predictive analytics panel with smart recommendations.
    
    Features:
    - Real-time data analysis
    - Actionable setup recommendations
    - Performance tips
    - Safety alerts with recommendations
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.tips: List[AnalyticsTip] = []
        self.setup_ui()
        self._start_analysis_timer()
    
    def setup_ui(self) -> None:
        """Setup analytics panel."""
        layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(self.scaler.get_scaled_size(10))
        
        # Title
        title = QLabel("Predictive Analytics & Setup Recommendations")
        title_font = self.scaler.get_scaled_font_size(16)
        title.setStyleSheet(f"""
            font-size: {title_font}px;
            font-weight: bold;
            color: {RacingColor.ACCENT_NEON_BLUE.value};
            padding: {self.scaler.get_scaled_size(5)}px;
        """)
        layout.addWidget(title)
        
        # Tips list
        self.tips_list = QListWidget()
        self.tips_list.setStyleSheet(get_racing_stylesheet("panel") + """
            QListWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #404040;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #00e0ff33;
                color: #00e0ff;
            }
        """)
        self.tips_list.setMinimumHeight(self.scaler.get_scaled_size(300))
        layout.addWidget(self.tips_list)
        
        # Detail view
        detail_group = QGroupBox("Recommendation Details")
        detail_group.setStyleSheet(get_racing_stylesheet("group_box"))
        detail_layout = QVBoxLayout()
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_font = self.scaler.get_scaled_font_size(11)
        self.detail_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: {detail_font}px;
                border: 1px solid #404040;
            }}
        """)
        self.detail_text.setMinimumHeight(self.scaler.get_scaled_size(150))
        detail_layout.addWidget(self.detail_text)
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        # Connect selection
        self.tips_list.itemSelectionChanged.connect(self._on_tip_selected)
    
    def _start_analysis_timer(self) -> None:
        """Start timer for periodic analysis."""
        self.analysis_timer = QTimer(self)
        self.analysis_timer.timeout.connect(self._analyze_data)
        self.analysis_timer.start(2000)  # Analyze every 2 seconds
    
    def _analyze_data(self) -> None:
        """Analyze current telemetry and generate tips."""
        # This would analyze telemetry data and generate recommendations
        # For now, placeholder
        pass
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data and generate recommendations."""
        self.tips = []
        
        # Analyze AFR
        afr = data.get("AFR", data.get("lambda_value", 1.0) * 14.7)
        if afr > 15.0:
            self.tips.append(AnalyticsTip(
                category="Safety",
                priority="critical",
                message="LEAN CONDITION DETECTED - Add fuel immediately",
                action="Increase fuel map values in current cell",
                confidence=0.95,
                data_points={"AFR": afr}
            ))
        elif afr < 12.0:
            self.tips.append(AnalyticsTip(
                category="Efficiency",
                priority="medium",
                message="Rich condition - Consider leaning out for better efficiency",
                action="Reduce fuel map values slightly",
                confidence=0.75,
                data_points={"AFR": afr}
            ))
        
        # Analyze boost
        boost = data.get("Boost_Pressure", data.get("boost_psi", 0))
        rpm = data.get("RPM", data.get("Engine_RPM", 0))
        if boost > 25 and rpm < 3000:
            self.tips.append(AnalyticsTip(
                category="Performance",
                priority="high",
                message="High boost at low RPM - Consider boost ramp adjustment",
                action="Adjust boost control ramp rate",
                confidence=0.80,
                data_points={"Boost": boost, "RPM": rpm}
            ))
        
        # Analyze EGT
        egt = data.get("EGT", data.get("ExhaustTemp", 800))
        if egt > 1600:
            self.tips.append(AnalyticsTip(
                category="Safety",
                priority="critical",
                message="CRITICAL EGT - Reduce timing or add fuel",
                action="Retard ignition timing or enrich fuel mixture",
                confidence=0.90,
                data_points={"EGT": egt}
            ))
        
        # Analyze knock
        knock = data.get("Knock_Count", data.get("knock_retard", 0))
        if knock > 5:
            self.tips.append(AnalyticsTip(
                category="Safety",
                priority="high",
                message="Knock detected - Retard timing",
                action="Reduce ignition advance in current cell",
                confidence=0.85,
                data_points={"Knock": knock}
            ))
        
        # Update UI
        self._update_tips_list()
    
    def _update_tips_list(self) -> None:
        """Update tips list widget."""
        self.tips_list.clear()
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_tips = sorted(self.tips, key=lambda t: priority_order.get(t.priority, 4))
        
        for tip in sorted_tips:
            item = QListWidgetItem(f"[{tip.priority.upper()}] {tip.message}")
            
            # Color by priority
            if tip.priority == "critical":
                item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_RED.value)))
            elif tip.priority == "high":
                item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_ORANGE.value)))
            elif tip.priority == "medium":
                item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_YELLOW.value)))
            else:
                item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_BLUE.value)))
            
            item.setData(Qt.ItemDataRole.UserRole, tip)
            self.tips_list.addItem(item)
    
    def _on_tip_selected(self) -> None:
        """Handle tip selection."""
        current_item = self.tips_list.currentItem()
        if not current_item:
            return
        
        tip: AnalyticsTip = current_item.data(Qt.ItemDataRole.UserRole)
        if not tip:
            return
        
        detail_text = f"""
Category: {tip.category.upper()}
Priority: {tip.priority.upper()}
Confidence: {tip.confidence:.0%}

Message:
{tip.message}

Recommended Action:
{tip.action or "No specific action"}

Data Points:
"""
        for key, value in tip.data_points.items():
            detail_text += f"  {key}: {value:.2f}\n"
        
        self.detail_text.setText(detail_text)

