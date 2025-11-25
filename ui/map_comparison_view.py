"""
Map Comparison View
Side-by-side or overlay view for comparing current map with base map.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, List, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QFrame,
)

from ui.ui_scaling import get_scaled_size, get_scaled_font_size

LOGGER = logging.getLogger(__name__)


class MapComparisonWidget(QWidget):
    """
    Widget for comparing two maps side-by-side or overlaid.
    
    Features:
    - Side-by-side comparison
    - Overlay mode with color coding
    - Difference highlighting (green for higher, red for lower)
    - Cell-by-cell comparison
    """
    
    cell_selected = Signal(int, int)  # row, col
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_map: Optional[List[List[float]]] = None
        self.base_map: Optional[List[List[float]]] = None
        self.comparison_mode = "side_by_side"  # "side_by_side" or "overlay"
        self.show_differences = True
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup comparison view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Controls
        controls = QHBoxLayout()
        
        mode_combo = QComboBox()
        mode_combo.addItems(["Side-by-Side", "Overlay"])
        mode_combo.currentTextChanged.connect(self._on_mode_changed)
        controls.addWidget(QLabel("Mode:"))
        controls.addWidget(mode_combo)
        
        self.diff_checkbox = QCheckBox("Show Differences")
        self.diff_checkbox.setChecked(True)
        self.diff_checkbox.toggled.connect(self._on_diff_toggled)
        controls.addWidget(self.diff_checkbox)
        
        controls.addStretch()
        
        layout.addLayout(controls)
        
        # Comparison view (will be drawn in paintEvent)
        self.comparison_view = QFrame()
        self.comparison_view.setMinimumSize(800, 600)
        self.comparison_view.setStyleSheet("""
            QFrame {
                background-color: #0a0e27;
                border: 1px solid #00e0ff;
            }
        """)
        layout.addWidget(self.comparison_view, stretch=1)
    
    def set_maps(self, current_map: List[List[float]], base_map: List[List[float]]) -> None:
        """
        Set maps to compare.
        
        Args:
            current_map: 2D list of float values for current map
            base_map: 2D list of float values for base map
            
        Raises:
            TypeError: If maps are not lists
            ValueError: If maps are empty, have mismatched dimensions, or contain invalid values
        """
        # Validate input types
        if not isinstance(current_map, list) or not isinstance(base_map, list):
            raise TypeError("Maps must be lists")
        
        if not current_map or not base_map:
            raise ValueError("Maps cannot be empty")
        
        # Validate dimensions
        if len(current_map) != len(base_map):
            raise ValueError(f"Maps must have same number of rows: {len(current_map)} vs {len(base_map)}")
        
        # Validate all rows have same length
        current_row_lengths = [len(row) for row in current_map]
        base_row_lengths = [len(row) for row in base_map]
        
        if len(set(current_row_lengths)) > 1:
            raise ValueError("All rows in current_map must have same length")
        if len(set(base_row_lengths)) > 1:
            raise ValueError("All rows in base_map must have same length")
        if current_row_lengths[0] != base_row_lengths[0]:
            raise ValueError(f"Maps must have same number of columns: {current_row_lengths[0]} vs {base_row_lengths[0]}")
        
        # Validate all values are numeric
        for i, (curr_row, base_row) in enumerate(zip(current_map, base_map)):
            if len(curr_row) != len(base_row):
                raise ValueError(f"Row {i} has mismatched length")
            for j, (curr_val, base_val) in enumerate(zip(curr_row, base_row)):
                if not isinstance(curr_val, (int, float)):
                    raise TypeError(f"current_map[{i}][{j}] must be numeric, got {type(curr_val)}")
                if not isinstance(base_val, (int, float)):
                    raise TypeError(f"base_map[{i}][{j}] must be numeric, got {type(base_val)}")
                # Check for NaN or Infinity
                if not (float('-inf') < float(curr_val) < float('inf')):
                    raise ValueError(f"current_map[{i}][{j}] is NaN or Infinity")
                if not (float('-inf') < float(base_val) < float('inf')):
                    raise ValueError(f"base_map[{i}][{j}] is NaN or Infinity")
        
        self.current_map = current_map
        self.base_map = base_map
        self.comparison_view.update()
    
    def set_comparison_mode(self, mode: str) -> None:
        """Set comparison mode."""
        self.comparison_mode = mode
        self.comparison_view.update()
    
    def _on_mode_changed(self, text: str) -> None:
        """Handle mode change."""
        self.comparison_mode = "overlay" if text == "Overlay" else "side_by_side"
        self.comparison_view.update()
    
    def _on_diff_toggled(self, checked: bool) -> None:
        """Handle difference toggle."""
        self.show_differences = checked
        self.comparison_view.update()
    
    def paintEvent(self, event) -> None:
        """Paint comparison view."""
        if not self.current_map or not self.base_map:
            return
        
        painter = QPainter(self.comparison_view)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.comparison_view.rect()
        
        if self.comparison_mode == "side_by_side":
            self._paint_side_by_side(painter, rect)
        else:
            self._paint_overlay(painter, rect)
    
    def _paint_side_by_side(self, painter: QPainter, rect) -> None:
        """Paint side-by-side comparison."""
        width = rect.width()
        height = rect.height()
        
        # Split into two halves
        left_rect = rect.adjusted(0, 0, -width // 2, 0)
        right_rect = rect.adjusted(width // 2, 0, 0, 0)
        
        # Draw current map on left
        self._draw_map(painter, self.current_map, left_rect, "Current Map")
        
        # Draw base map on right
        self._draw_map(painter, self.base_map, right_rect, "Base Map")
    
    def _paint_overlay(self, painter: QPainter, rect) -> None:
        """Paint overlay comparison with color coding."""
        if not self.show_differences:
            # Just show current map
            self._draw_map(painter, self.current_map, rect, "Current Map")
            return
        
        # Draw current map with color coding based on differences
        rows = len(self.current_map)
        cols = len(self.current_map[0]) if rows > 0 else 0
        
        if rows == 0 or cols == 0:
            return
        
        # Validate map dimensions match
        if len(self.base_map) != rows:
            LOGGER.warning("Map dimension mismatch: current_map has %d rows, base_map has %d", rows, len(self.base_map))
            return
        
        cell_width = rect.width() / cols
        cell_height = rect.height() / rows
        
        for i, row in enumerate(self.current_map):
            if i >= len(self.base_map):
                continue
            if len(row) != cols:
                continue
            if len(self.base_map[i]) != cols:
                continue
            
            for j, value in enumerate(row):
                if j >= len(self.base_map[i]):
                    continue
                base_value = self.base_map[i][j]
                
                x = j * cell_width
                y = i * cell_height
                cell_rect = rect.adjusted(x, y, x + cell_width, y + cell_height)
                
                # Color code based on difference
                diff = value - base_value
                if diff > 0:
                    # Higher - green
                    color = QColor(0, 255, 0, 150)
                elif diff < 0:
                    # Lower - red
                    color = QColor(255, 0, 0, 150)
                else:
                    # Same - transparent
                    color = QColor(255, 255, 255, 50)
                
                painter.fillRect(cell_rect, QBrush(color))
                
                # Draw value
                painter.setPen(QPen(QColor(255, 255, 255)))
                painter.drawText(cell_rect, Qt.AlignmentFlag.AlignCenter, f"{value:.1f}")
    
    def _draw_map(self, painter: QPainter, map_data: List[List[float]], rect, title: str) -> None:
        """Draw a map in the given rectangle."""
        rows = len(map_data)
        cols = len(map_data[0]) if rows > 0 else 0
        
        if rows == 0 or cols == 0:
            return
        
        # Draw title
        painter.setPen(QPen(QColor(0, 224, 255)))
        font_size = get_scaled_font_size(14)
        painter.setFont(painter.font())
        title_rect = rect.adjusted(0, 0, 0, -rect.height() + 30)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, title)
        
        # Draw map cells
        map_rect = rect.adjusted(0, 30, 0, 0)
        cell_width = map_rect.width() / cols
        cell_height = map_rect.height() / rows
        
        # Find min/max for color scaling
        min_val = min(min(row) for row in map_data)
        max_val = max(max(row) for row in map_data)
        val_range = max_val - min_val if max_val != min_val else 1
        
        for i, row in enumerate(map_data):
            for j, value in enumerate(row):
                x = j * cell_width
                y = i * cell_height
                cell_rect = map_rect.adjusted(x, y, x + cell_width, y + cell_height)
                
                # Color based on value (blue gradient)
                normalized = (value - min_val) / val_range
                blue_intensity = int(255 * normalized)
                color = QColor(0, 100 + blue_intensity // 2, blue_intensity)
                
                painter.fillRect(cell_rect, QBrush(color))
                
                # Draw value
                painter.setPen(QPen(QColor(255, 255, 255)))
                painter.drawText(cell_rect, Qt.AlignmentFlag.AlignCenter, f"{value:.1f}")


class MapComparisonDialog(QWidget):
    """Dialog for map comparison."""
    
    def __init__(self, current_map: List[List[float]], base_map: List[List[float]], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Map Comparison")
        self.setMinimumSize(900, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Comparison widget
        self.comparison_widget = MapComparisonWidget()
        self.comparison_widget.set_maps(current_map, base_map)
        layout.addWidget(self.comparison_widget, stretch=1)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
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
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

