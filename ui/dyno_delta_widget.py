"""
Delta Comparison Widget - Display percentage gains at RPM ranges
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QLabel,
    QHeaderView,
)

if TYPE_CHECKING:
    from services.dyno_enhancements import DynoDeltaAnalysis

from ui.ui_scaling import get_scaled_size, get_scaled_font_size


class DynoDeltaWidget(QWidget):
    """Widget for displaying delta comparison between two dyno runs."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        
        # Title
        title = QLabel("Delta Comparison")
        title.setStyleSheet(f"font-size: {get_scaled_font_size(14)}px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # Summary labels
        self.summary_label = QLabel("No comparison data")
        self.summary_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: #9aa0a6;")
        layout.addWidget(self.summary_label)
        
        # Table for RPM-by-RPM comparison
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["RPM", "HP Delta", "HP %", "TQ Delta", "TQ %"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: white;
                gridline-color: #333;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: white;
                padding: 5px;
                border: 1px solid #555;
            }
        """)
        layout.addWidget(self.table)
    
    def update_comparison(self, analysis: "DynoDeltaAnalysis") -> None:
        """Update with delta analysis."""
        # Update summary
        summary_text = (
            f"{analysis.run1_name} → {analysis.run2_name}\n"
            f"Peak HP: {analysis.peak_hp_delta:+.1f} HP ({analysis.peak_hp_percent_change:+.1f}%)\n"
            f"Peak Torque: {analysis.peak_torque_delta:+.1f} ft-lb ({analysis.peak_torque_percent_change:+.1f}%)\n"
            f"Average HP Gain: {analysis.average_hp_gain:+.1f} HP"
        )
        if analysis.best_rpm_range:
            summary_text += f"\nBest Range: {analysis.best_rpm_range[0]:.0f}-{analysis.best_rpm_range[1]:.0f} RPM"
        self.summary_label.setText(summary_text)
        
        # Update table
        self.table.setRowCount(len(analysis.rpm_deltas))
        
        for row, delta in enumerate(analysis.rpm_deltas):
            # RPM
            rpm_item = QTableWidgetItem(f"{delta.rpm:.0f}")
            rpm_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, rpm_item)
            
            # HP Delta
            hp_delta_item = QTableWidgetItem(f"{delta.hp_delta:+.1f}")
            hp_delta_item.setTextAlignment(Qt.AlignCenter)
            if delta.hp_delta > 0:
                hp_delta_item.setForeground(QColor("#00ff00"))  # Green for gains
            elif delta.hp_delta < 0:
                hp_delta_item.setForeground(QColor("#ff0000"))  # Red for losses
            self.table.setItem(row, 1, hp_delta_item)
            
            # HP Percentage
            hp_pct_item = QTableWidgetItem(f"{delta.hp_percent_change:+.1f}%")
            hp_pct_item.setTextAlignment(Qt.AlignCenter)
            if delta.hp_percent_change > 0:
                hp_pct_item.setForeground(QColor("#00ff00"))
            elif delta.hp_percent_change < 0:
                hp_pct_item.setForeground(QColor("#ff0000"))
            self.table.setItem(row, 2, hp_pct_item)
            
            # Torque Delta
            tq_delta_item = QTableWidgetItem(f"{delta.torque_delta:+.1f}")
            tq_delta_item.setTextAlignment(Qt.AlignCenter)
            if delta.torque_delta > 0:
                tq_delta_item.setForeground(QColor("#00ff00"))
            elif delta.torque_delta < 0:
                tq_delta_item.setForeground(QColor("#ff0000"))
            self.table.setItem(row, 3, tq_delta_item)
            
            # Torque Percentage
            tq_pct_item = QTableWidgetItem(f"{delta.torque_percent_change:+.1f}%")
            tq_pct_item.setTextAlignment(Qt.AlignCenter)
            if delta.torque_percent_change > 0:
                tq_pct_item.setForeground(QColor("#00ff00"))
            elif delta.torque_percent_change < 0:
                tq_pct_item.setForeground(QColor("#ff0000"))
            self.table.setItem(row, 4, tq_pct_item)
        
        # Resize columns
        self.table.resizeColumnsToContents()
    
    def clear(self) -> None:
        """Clear comparison data."""
        self.summary_label.setText("No comparison data")
        self.table.setRowCount(0)


__all__ = ["DynoDeltaWidget"]

