"""
Shift Points Widget - Display optimal shift point recommendations
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

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
    from services.dyno_enhancements import ShiftPoint

from ui.ui_scaling import get_scaled_size, get_scaled_font_size


class DynoShiftPointsWidget(QWidget):
    """Widget for displaying optimal shift point recommendations."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        
        # Title
        title = QLabel("Optimal Shift Points")
        title.setStyleSheet(f"font-size: {get_scaled_font_size(14)}px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Shift points calculated to keep car in peak power band")
        desc.setStyleSheet(f"font-size: {get_scaled_font_size(11)}px; color: #9aa0a6;")
        layout.addWidget(desc)
        
        # Table for shift points
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Gear", "Shift RPM", "Reason", "Early Loss", "Late Loss"])
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
    
    def update_shift_points(self, shift_points: List["ShiftPoint"]) -> None:
        """Update with shift point recommendations."""
        self.table.setRowCount(len(shift_points))
        
        for row, shift in enumerate(shift_points):
            # Gear transition
            gear_item = QTableWidgetItem(f"{shift.from_gear} → {shift.to_gear}")
            gear_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, gear_item)
            
            # Shift RPM
            rpm_item = QTableWidgetItem(f"{shift.shift_rpm:.0f}")
            rpm_item.setTextAlignment(Qt.AlignCenter)
            rpm_item.setForeground(QColor("#00e0ff"))  # Highlight shift RPM
            self.table.setItem(row, 1, rpm_item)
            
            # Reason
            reason_item = QTableWidgetItem(shift.reason)
            reason_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row, 2, reason_item)
            
            # Early loss
            early_loss_item = QTableWidgetItem(f"{shift.power_loss_if_shift_early:.1f} HP")
            early_loss_item.setTextAlignment(Qt.AlignCenter)
            if shift.power_loss_if_shift_early > 0:
                early_loss_item.setForeground(QColor("#ffaa00"))  # Warning color
            self.table.setItem(row, 3, early_loss_item)
            
            # Late loss
            late_loss_item = QTableWidgetItem(f"{shift.power_loss_if_shift_late:.1f} HP")
            late_loss_item.setTextAlignment(Qt.AlignCenter)
            if shift.power_loss_if_shift_late > 0:
                late_loss_item.setForeground(QColor("#ffaa00"))  # Warning color
            self.table.setItem(row, 4, late_loss_item)
        
        # Resize columns
        self.table.resizeColumnsToContents()
    
    def clear(self) -> None:
        """Clear shift point data."""
        self.table.setRowCount(0)


__all__ = ["DynoShiftPointsWidget"]

