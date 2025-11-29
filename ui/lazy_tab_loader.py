"""
Lazy Tab Loader

Provides lazy loading for expensive tab widgets to improve startup performance.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QLabel

LOGGER = logging.getLogger(__name__)


class LazyTabLoader:
    """
    Manages lazy loading of tab widgets.
    
    Tabs are created only when first accessed, improving startup performance.
    """
    
    def __init__(self, tab_widget: QTabWidget):
        """
        Initialize lazy tab loader.
        
        Args:
            tab_widget: The QTabWidget to manage
        """
        self.tab_widget = tab_widget
        self._tab_factories: dict[int, Callable[[], QWidget]] = {}
        self._tab_labels: dict[int, str] = {}
        self._loaded_tabs: dict[int, QWidget] = {}
        self._placeholder_widget: Optional[QWidget] = None
        
        # Connect to tab change signal to load tabs on demand
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def add_lazy_tab(self, factory: Callable[[], QWidget], label: str) -> int:
        """
        Add a tab that will be loaded lazily.
        
        Args:
            factory: Function that creates the tab widget when called
            label: Tab label text
        
        Returns:
            Tab index
        """
        index = self.tab_widget.count()
        self._tab_factories[index] = factory
        self._tab_labels[index] = label
        
        # Add placeholder widget initially
        if self._placeholder_widget is None:
            self._placeholder_widget = QWidget()
            placeholder_label = QWidget()
            placeholder_label.setStyleSheet("background-color: #050711; color: #00e5ff; padding: 20px;")
            from PySide6.QtWidgets import QVBoxLayout, QLabel
            layout = QVBoxLayout(placeholder_label)
            label_widget = QLabel("Loading...")
            label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label_widget)
            self._placeholder_widget = placeholder_label
        
        self.tab_widget.addTab(self._placeholder_widget, label)
        
        return index
    
    def _on_tab_changed(self, index: int) -> None:
        """
        Handle tab change - load tab if not already loaded.
        
        Args:
            index: Tab index that was selected
        """
        if index in self._loaded_tabs:
            return  # Already loaded
        
        if index not in self._tab_factories:
            return  # Not a lazy tab
        
        try:
            LOGGER.debug(f"Lazy loading tab {index}: {self._tab_labels.get(index, 'unknown')}")
            widget = self._tab_factories[index]()
            self._loaded_tabs[index] = widget
            
            # Replace placeholder with actual widget
            self.tab_widget.removeTab(index)
            self.tab_widget.insertTab(index, widget, self._tab_labels[index])
            self.tab_widget.setCurrentIndex(index)
            
            LOGGER.debug(f"Tab {index} loaded successfully")
        except Exception as e:
            LOGGER.error(f"Failed to load tab {index}: {e}", exc_info=True)
            # Keep placeholder, but show error
            from PySide6.QtWidgets import QLabel
            error_widget = QWidget()
            error_widget.setStyleSheet("background-color: #050711; color: #e74c3c; padding: 20px;")
            layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"Failed to load tab:\n{str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(error_label)
            self.tab_widget.removeTab(index)
            self.tab_widget.insertTab(index, error_widget, self._tab_labels[index])
    
    def preload_tab(self, index: int) -> None:
        """
        Preload a tab before it's accessed.
        
        Args:
            index: Tab index to preload
        """
        if index not in self._loaded_tabs and index in self._tab_factories:
            self._on_tab_changed(index)
    
    def is_loaded(self, index: int) -> bool:
        """
        Check if a tab is loaded.
        
        Args:
            index: Tab index
        
        Returns:
            True if tab is loaded
        """
        return index in self._loaded_tabs

