"""
Module Base Features
Standard features that all modules should have for consistency.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QGroupBox,
)

LOGGER = logging.getLogger(__name__)


class StandardModuleFeatures(ABC):
    """
    Base class for modules with standard features.
    
    All modules should have:
    1. Graphing capabilities
    2. Import/Export functionality
    3. Data logging
    4. Telemetry updates
    5. Settings/Configuration
    6. Help/Documentation
    """
    
    def __init__(self):
        """Initialize standard features."""
        self.has_graphing = False
        self.has_import = False
        self.has_export = False
        self.has_logging = False
        self.has_settings = False
    
    @abstractmethod
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update module with telemetry data."""
        pass
    
    def add_graphing_panel(self, parent: QWidget) -> Optional[QWidget]:
        """
        Add standard graphing panel.
        
        Returns:
            Graphing widget or None
        """
        try:
            from ui.advanced_log_graphing import AdvancedLogGraphingWidget
            graph_widget = AdvancedLogGraphingWidget()
            self.has_graphing = True
            return graph_widget
        except ImportError:
            try:
                from ui.ecu_tuning_widgets import RealTimeGraph
                graph_widget = RealTimeGraph()
                self.has_graphing = True
                return graph_widget
            except ImportError:
                LOGGER.warning("Graphing widgets not available")
                return None
    
    def add_import_export_buttons(self, parent: QWidget, layout: QVBoxLayout) -> None:
        """Add standard import/export buttons."""
        import_export_group = QGroupBox("Import/Export")
        import_export_layout = QHBoxLayout()
        
        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(lambda: self._handle_import())
        import_export_layout.addWidget(import_btn)
        
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(lambda: self._handle_export())
        import_export_layout.addWidget(export_btn)
        
        import_export_group.setLayout(import_export_layout)
        layout.addWidget(import_export_group)
        
        self.has_import = True
        self.has_export = True
    
    def _handle_import(self) -> None:
        """Handle import action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self if isinstance(self, QWidget) else None,
            "Import File",
            "",
            "All Files (*.*)"
        )
        
        if file_path:
            try:
                self.import_data(file_path)
                QMessageBox.information(
                    self if isinstance(self, QWidget) else None,
                    "Import Success",
                    "File imported successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self if isinstance(self, QWidget) else None,
                    "Import Error",
                    f"Failed to import file:\n{str(e)}"
                )
    
    def _handle_export(self) -> None:
        """Handle export action."""
        file_path, _ = QFileDialog.getSaveFileName(
            self if isinstance(self, QWidget) else None,
            "Export File",
            "",
            "All Files (*.*)"
        )
        
        if file_path:
            try:
                self.export_data(file_path)
                QMessageBox.information(
                    self if isinstance(self, QWidget) else None,
                    "Export Success",
                    "File exported successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self if isinstance(self, QWidget) else None,
                    "Export Error",
                    f"Failed to export file:\n{str(e)}"
                )
    
    def import_data(self, file_path: str) -> None:
        """
        Import data from file.
        
        Override in subclasses for specific import logic.
        """
        LOGGER.warning("import_data not implemented in %s", self.__class__.__name__)
    
    def export_data(self, file_path: str) -> None:
        """
        Export data to file.
        
        Override in subclasses for specific export logic.
        """
        LOGGER.warning("export_data not implemented in %s", self.__class__.__name__)
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported import/export formats.
        
        Returns:
            List of format descriptions
        """
        return ["All Files (*.*)"]
    
    def add_settings_panel(self, parent: QWidget, layout: QVBoxLayout) -> None:
        """Add standard settings panel."""
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        
        # Add module-specific settings here
        settings_label = QLabel("Module-specific settings")
        settings_layout.addWidget(settings_label)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        self.has_settings = True
    
    def add_help_button(self, parent: QWidget, layout: QVBoxLayout) -> None:
        """Add help/documentation button."""
        help_btn = QPushButton("❓ Help")
        help_btn.clicked.connect(lambda: self._show_help())
        layout.addWidget(help_btn)
    
    def _show_help(self) -> None:
        """Show help/documentation."""
        help_text = self.get_help_text()
        QMessageBox.information(
            self if isinstance(self, QWidget) else None,
            "Help",
            help_text
        )
    
    def get_help_text(self) -> str:
        """
        Get help text for this module.
        
        Override in subclasses.
        """
        return f"Help for {self.__class__.__name__}"

