"""
Multi-Row Tab Widget
Custom tab widget that displays tabs in 2 rows instead of a single scrollable row
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
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_stylesheet, RacingColor


class MultiRowTabWidget(QWidget):
    """Custom tab widget that displays tabs in 2 rows."""
    
    currentChanged = Signal(int)  # Emitted when tab changes
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.tabs_per_row = 10  # Number of tabs per row (will be calculated dynamically)
        self.current_index = 0
        self.tab_buttons: Dict[int, QPushButton] = {}
        self.tab_widgets: Dict[int, QWidget] = {}
        self.tab_labels: Dict[int, str] = {}
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup multi-row tab widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab bar area (2 rows of buttons)
        self.tab_bar_widget = QWidget()
        self.tab_bar_layout = QVBoxLayout(self.tab_bar_widget)
        self.tab_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_bar_layout.setSpacing(get_scaled_size(4))  # More spacing between rows
        
        # Create two rows for tabs
        self.row1_layout = QHBoxLayout()
        self.row1_layout.setContentsMargins(0, 0, 0, 0)
        self.row1_layout.setSpacing(get_scaled_size(4))  # More spacing between tabs
        
        self.row2_layout = QHBoxLayout()
        self.row2_layout.setContentsMargins(0, 0, 0, 0)
        self.row2_layout.setSpacing(get_scaled_size(4))  # More spacing between tabs
        
        self.tab_bar_layout.addLayout(self.row1_layout)
        self.tab_bar_layout.addLayout(self.row2_layout)
        
        # Stacked widget for tab content
        self.stacked_widget = QStackedWidget()
        
        layout.addWidget(self.tab_bar_widget)
        layout.addWidget(self.stacked_widget, stretch=1)
        
        # Apply styling
        self._apply_styling()
    
    def _apply_styling(self) -> None:
        """Apply racing theme styling to tab bar."""
        btn_padding_v = get_scaled_size(8)
        btn_padding_h = get_scaled_size(15)
        btn_font = get_scaled_font_size(11)
        
        # Base button style (inactive)
        self.base_button_style = f"""
            QPushButton {{
                background-color: {RacingColor.BG_SECONDARY.value};
                color: {RacingColor.TEXT_PRIMARY.value};
                border: {get_scaled_size(1)}px solid {RacingColor.BORDER_DEFAULT.value};
                border-radius: {get_scaled_size(3)}px;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
                font-weight: bold;
                text-align: center;
                min-height: {get_scaled_size(30)}px;
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
                border-radius: {get_scaled_size(3)}px;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
                font-weight: bold;
                text-align: center;
                min-height: {get_scaled_size(30)}px;
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
        
        # Create tab button with better sizing
        button = QPushButton(label)
        # Calculate minimum width based on text length to ensure readability
        text_width = len(label) * get_scaled_size(7)  # Approximate width per character
        min_width = max(get_scaled_size(100), text_width + get_scaled_size(40))  # Text + padding
        # Don't set max width - let them expand equally
        
        # Use Expanding so buttons fill space evenly
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.setMinimumWidth(min_width)
        button.setStyleSheet(self.base_button_style)
        button.clicked.connect(lambda checked, idx=index: self.setCurrentIndex(idx))
        self.tab_buttons[index] = button
        
        # Set first tab as active
        if index == 0:
            self.setCurrentIndex(0)
        
        # We'll redistribute all tabs after adding this one
        self._redistribute_tabs()
        
        return index
    
    def _redistribute_tabs(self) -> None:
        """Redistribute all tabs evenly across the two rows."""
        # Clear both rows
        while self.row1_layout.count():
            item = self.row1_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        while self.row2_layout.count():
            item = self.row2_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Calculate how many tabs per row (split evenly)
        total_tabs = len(self.tab_widgets)
        if total_tabs == 0:
            return
        
        # Split evenly - first half in row 1, second half in row 2
        tabs_per_row = (total_tabs + 1) // 2  # Round up for first row
        
        # Add tabs to appropriate rows with stretch factors
        for index in sorted(self.tab_buttons.keys()):
            button = self.tab_buttons[index]
            # Use stretch factor of 1 so all buttons get equal space
            if index < tabs_per_row:
                self.row1_layout.addWidget(button, stretch=1)
            else:
                self.row2_layout.addWidget(button, stretch=1)
        
        # Add stretch at the end of each row to fill remaining space
        self.row1_layout.addStretch()
        self.row2_layout.addStretch()
    
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
        # For simplicity, just add at the end and reorder if needed
        # This is a simplified implementation
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

