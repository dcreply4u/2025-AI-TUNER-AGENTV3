"""
Module Feature Helper
Utility functions to add standard features to modules.
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox,
    QFileDialog, QMessageBox, QTabWidget, QLabel,
)

from ui.ui_scaling import get_scaled_size


def add_import_export_bar(parent: QWidget, layout: QVBoxLayout, 
                         import_callback=None, export_callback=None) -> None:
    """
    Add standard import/export bar to a module.
    
    Args:
        parent: Parent widget
        layout: Layout to add bar to
        import_callback: Optional import callback function
        export_callback: Optional export callback function
    """
    bar = QWidget()
    bar.setStyleSheet("background-color: #2a2a2a; padding: 5px; border: 1px solid #404040;")
    bar_layout = QHBoxLayout(bar)
    bar_layout.setContentsMargins(10, 5, 10, 5)
    
    import_btn = QPushButton("📥 Import")
    import_btn.setStyleSheet("background-color: #3498db; color: white; padding: 5px 10px;")
    if import_callback:
        import_btn.clicked.connect(import_callback)
    else:
        import_btn.clicked.connect(lambda: _default_import(parent))
    bar_layout.addWidget(import_btn)
    
    export_btn = QPushButton("📤 Export")
    export_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 5px 10px;")
    if export_callback:
        export_btn.clicked.connect(export_callback)
    else:
        export_btn.clicked.connect(lambda: _default_export(parent))
    bar_layout.addWidget(export_btn)
    
    bar_layout.addStretch()
    layout.addWidget(bar)


def add_graphing_tab(tab_widget: QTabWidget, module_name: str) -> QWidget:
    """
    Add standard graphing tab to a tab widget.
    
    Args:
        tab_widget: Tab widget to add to
        module_name: Name of module for labeling
    
    Returns:
        Created graph widget
    """
    graph_tab = QWidget()
    graph_layout = QVBoxLayout(graph_tab)
    graph_layout.setContentsMargins(10, 10, 10, 10)
    
    try:
        from ui.advanced_log_graphing import AdvancedLogGraphingWidget
        graph_widget = AdvancedLogGraphingWidget()
        graph_layout.addWidget(graph_widget, stretch=1)
    except ImportError:
        try:
            from ui.ecu_tuning_widgets import RealTimeGraph
            graph_widget = RealTimeGraph()
            graph_layout.addWidget(graph_widget, stretch=1)
        except ImportError:
            from PySide6.QtWidgets import QLabel
            placeholder = QLabel(f"Graphing not available for {module_name}")
            placeholder.setStyleSheet("color: #ffffff; padding: 20px;")
            graph_layout.addWidget(placeholder, stretch=1)
            graph_widget = None
    
    tab_widget.addTab(graph_tab, "📊 Graphing")
    return graph_widget


def add_import_export_tab(tab_widget: QTabWidget, module_name: str,
                         import_callback=None, export_callback=None) -> None:
    """
    Add standard import/export tab to a tab widget.
    
    Args:
        tab_widget: Tab widget to add to
        module_name: Name of module for labeling
        import_callback: Optional import callback
        export_callback: Optional export callback
    """
    ie_tab = QWidget()
    ie_layout = QVBoxLayout(ie_tab)
    ie_layout.setContentsMargins(10, 10, 10, 10)
    
    import_group = QGroupBox("Import")
    import_layout = QVBoxLayout()
    import_btn = QPushButton(f"📥 Import {module_name} Data")
    import_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
    if import_callback:
        import_btn.clicked.connect(import_callback)
    else:
        import_btn.clicked.connect(lambda: _default_import(ie_tab))
    import_layout.addWidget(import_btn)
    import_group.setLayout(import_layout)
    ie_layout.addWidget(import_group)
    
    export_group = QGroupBox("Export")
    export_layout = QVBoxLayout()
    export_btn = QPushButton(f"📤 Export {module_name} Data")
    export_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
    if export_callback:
        export_btn.clicked.connect(export_callback)
    else:
        export_btn.clicked.connect(lambda: _default_export(ie_tab))
    export_layout.addWidget(export_btn)
    export_group.setLayout(export_layout)
    ie_layout.addWidget(export_group)
    
    ie_layout.addStretch()
    tab_widget.addTab(ie_tab, "Import/Export")


def _default_import(parent: QWidget) -> None:
    """Default import handler."""
    file_path, _ = QFileDialog.getOpenFileName(parent, "Import Data", "", "All Files (*.*)")
    if file_path:
        QMessageBox.information(parent, "Import", f"Importing from: {file_path}")


def _default_export(parent: QWidget) -> None:
    """Default export handler."""
    file_path, _ = QFileDialog.getSaveFileName(parent, "Export Data", "", "All Files (*.*)")
    if file_path:
        QMessageBox.information(parent, "Export", f"Exporting to: {file_path}")

