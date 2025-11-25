"""
Multi-Row Tab Widget
Custom tab widget that displays tabs in multiple rows with vertical scrolling
"""

from __future__ import annotations

from typing import Optional, Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QSizePolicy,
    QScrollArea,
    QFrame,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_stylesheet, RacingColor


class MultiRowTabWidget(QWidget):
    """Custom tab widget that displays tabs in multiple rows with scrolling."""
    
    currentChanged = Signal(int)  # Emitted when tab changes
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.tabs_per_row = 8  # Number of tabs per row
        self.current_index = 0
        self.tab_buttons: Dict[int, QPushButton] = {}
        self.tab_widgets: Dict[int, QWidget] = {}
        self.tab_labels: Dict[int, str] = {}
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup multi-row tab widget UI with scrolling."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area for tab buttons
        self.tab_scroll = QScrollArea()
        self.tab_scroll.setWidgetResizable(True)
        self.tab_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tab_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.tab_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #00e0ff;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Container for all tab rows
        self.tab_bar_widget = QWidget()
        self.tab_bar_layout = QVBoxLayout(self.tab_bar_widget)
        self.tab_bar_layout.setContentsMargins(4, 4, 4, 4)
        self.tab_bar_layout.setSpacing(get_scaled_size(6))
        
        # We'll create rows dynamically as tabs are added
        self.row_layouts: list[QHBoxLayout] = []
        
        self.tab_scroll.setWidget(self.tab_bar_widget)
        
        # Set a reasonable max height for the tab area (allows ~3-4 rows visible)
        max_tab_height = get_scaled_size(150)
        self.tab_scroll.setMaximumHeight(max_tab_height)
        self.tab_scroll.setMinimumHeight(get_scaled_size(50))
        
        # Stacked widget for tab content
        self.stacked_widget = QStackedWidget()
        
        layout.addWidget(self.tab_scroll)
        layout.addWidget(self.stacked_widget, stretch=1)
        
        # Apply styling
        self._apply_styling()
    
    def _apply_styling(self) -> None:
        """Apply racing theme styling to tab bar."""
        btn_padding_v = get_scaled_size(6)
        btn_padding_h = get_scaled_size(12)
        btn_font = get_scaled_font_size(10)
        
        # Base button style (inactive)
        self.base_button_style = f"""
            QPushButton {{
                background-color: {RacingColor.BG_SECONDARY.value};
                color: {RacingColor.TEXT_PRIMARY.value};
                border: {get_scaled_size(1)}px solid {RacingColor.BORDER_DEFAULT.value};
                border-radius: {get_scaled_size(4)}px;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
                font-weight: bold;
                text-align: center;
                min-height: {get_scaled_size(28)}px;
            }}
            QPushButton:hover {{
                background-color: {RacingColor.BG_TERTIARY.value};
                border-color: {RacingColor.ACCENT_NEON_BLUE.value};
            }}
        """
        
        # Active button style
        self.active_button_style = f"""
            QPushButton {{
                background-color: {RacingColor.ACCENT_NEON_BLUE.value};
                color: {RacingColor.BG_PRIMARY.value};
                border: {get_scaled_size(2)}px solid {RacingColor.ACCENT_NEON_BLUE.value};
                border-radius: {get_scaled_size(4)}px;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
                font-weight: bold;
                text-align: center;
                min-height: {get_scaled_size(28)}px;
            }}
            QPushButton:hover {{
                background-color: {RacingColor.ACCENT_NEON_BLUE.value}dd;
            }}
        """
    
    def addTab(self, widget: QWidget, label: str) -> int:
        """
        Add a tab to the widget.
        
        Args:
            widget: Widget to display in the tab
            label: Tab label text
            
        Returns:
            Tab index
        """
        index = len(self.tab_widgets)
        self.tab_widgets[index] = widget
        self.tab_labels[index] = label
        
        # Add widget to stacked widget
        self.stacked_widget.addWidget(widget)
        
        # Create tab button
        button = QPushButton(label)
        button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        button.setMinimumWidth(get_scaled_size(80))
        button.setStyleSheet(self.base_button_style)
        button.clicked.connect(lambda checked, idx=index: self.setCurrentIndex(idx))
        self.tab_buttons[index] = button
        
        # Set first tab as active
        if index == 0:
            self.setCurrentIndex(0)
        
        # Redistribute tabs across rows
        self._redistribute_tabs()
        
        return index
    
    def _redistribute_tabs(self) -> None:
        """Redistribute all tabs across multiple rows."""
        # Clear existing row layouts
        for row_layout in self.row_layouts:
            while row_layout.count():
                item = row_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
        
        # Clear row layouts from main layout
        while self.tab_bar_layout.count():
            item = self.tab_bar_layout.takeAt(0)
            if item.layout():
                # Don't delete, we'll reuse
                pass
        
        self.row_layouts.clear()
        
        total_tabs = len(self.tab_widgets)
        if total_tabs == 0:
            return
        
        # Calculate number of rows needed
        num_rows = (total_tabs + self.tabs_per_row - 1) // self.tabs_per_row
        
        # Create row layouts
        for _ in range(num_rows):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(get_scaled_size(6))
            self.row_layouts.append(row)
            self.tab_bar_layout.addLayout(row)
        
        # Add tabs to rows
        for index in sorted(self.tab_buttons.keys()):
            button = self.tab_buttons[index]
            row_idx = index // self.tabs_per_row
            if row_idx < len(self.row_layouts):
                self.row_layouts[row_idx].addWidget(button)
        
        # Add stretch to each row
        for row in self.row_layouts:
            row.addStretch()
        
        # Add stretch at bottom
        self.tab_bar_layout.addStretch()
    
    def insertTab(self, index: int, widget: QWidget, label: str) -> int:
        """
        Insert a tab at the specified index.
        
        Args:
            index: Position to insert tab
            widget: Widget to display in the tab
            label: Tab label text
            
        Returns:
            Tab index
        """
        # For simplicity, just add at the end
        return self.addTab(widget, label)
    
    def setCurrentIndex(self, index: int) -> None:
        """
        Set the current active tab.
        
        Args:
            index: Tab index to activate
        """
        if index < 0 or index >= len(self.tab_widgets):
            return
        
        # Update button styles
        for idx, button in self.tab_buttons.items():
            if idx == index:
                button.setStyleSheet(self.active_button_style)
            else:
                button.setStyleSheet(self.base_button_style)
        
        # Update stacked widget
        self.stacked_widget.setCurrentIndex(index)
        self.current_index = index
        
        # Scroll to make the selected tab visible
        if index in self.tab_buttons:
            self.tab_scroll.ensureWidgetVisible(self.tab_buttons[index])
        
        # Emit signal
        self.currentChanged.emit(index)
    
    def currentIndex(self) -> int:
        """Get the current active tab index."""
        return self.current_index
    
    def count(self) -> int:
        """Get the total number of tabs."""
        return len(self.tab_widgets)
    
    def widget(self, index: int) -> Optional[QWidget]:
        """Get the widget at the specified index."""
        return self.tab_widgets.get(index)
    
    def setTabText(self, index: int, text: str) -> None:
        """Set the text for a tab."""
        if index in self.tab_buttons:
            self.tab_buttons[index].setText(text)
            self.tab_labels[index] = text
    
    def tabText(self, index: int) -> str:
        """Get the text for a tab."""
        return self.tab_labels.get(index, "")
    
    def setStyleSheet(self, stylesheet: str) -> None:
        """Override to apply stylesheet to stacked widget."""
        self.stacked_widget.setStyleSheet(stylesheet)
