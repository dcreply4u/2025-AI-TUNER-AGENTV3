"""
Auto Tuning Engine Tab
Dedicated tab for AI-powered automatic ECU tuning
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSizePolicy,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

try:
    from services.auto_tuning_engine import AutoTuningEngine, TuningAdjustment
except ImportError:
    AutoTuningEngine = None
    TuningAdjustment = None


class AutoTuningTab(QWidget):
    """Auto Tuning Engine tab with AI-powered tuning adjustments."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.tuning_engine: Optional[AutoTuningEngine] = None
        self.setup_ui()
        self._start_update_timer()
        
    def setup_ui(self) -> None:
        """Setup auto tuning tab UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(get_scaled_size(15))
        
        # Left: Settings and status
        left_panel = self._create_settings_panel()
        content_layout.addWidget(left_panel, stretch=1)
        
        # Center: Tuning adjustments table
        center_panel = self._create_adjustments_panel()
        content_layout.addWidget(center_panel, stretch=2)
        
        # Right: History and logs
        right_panel = self._create_history_panel()
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Graphing and Import/Export
        bottom_panel = self._create_bottom_panel()
        main_layout.addWidget(bottom_panel, stretch=1)
        
    def _create_control_bar(self) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        padding = get_scaled_size(5)
        border = get_scaled_size(1)
        bar.setStyleSheet(f"background-color: #2a2a2a; padding: {padding}px; border: {border}px solid #404040;")
        layout = QHBoxLayout(bar)
        margin_h = get_scaled_size(10)
        margin_v = get_scaled_size(5)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        title = QLabel("Auto Tuning Engine")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Enable/Disable button
        self.enable_btn = QPushButton("Enable Auto-Tuning")
        btn_padding_v = get_scaled_size(5)
        btn_padding_h = get_scaled_size(10)
        btn_font = get_scaled_font_size(11)
        self.enable_btn.setStyleSheet(f"background-color: #00ff00; color: #000000; padding: {btn_padding_v}px {btn_padding_h}px; font-weight: bold; font-size: {btn_font}px;")
        layout.addWidget(self.enable_btn)
        
        # Apply all button
        self.apply_all_btn = QPushButton("Apply All")
        self.apply_all_btn.setStyleSheet(f"background-color: #0080ff; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        layout.addWidget(self.apply_all_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet(f"background-color: #404040; color: #ffffff; padding: {btn_padding_v}px {btn_padding_h}px; font-size: {btn_font}px;")
        layout.addWidget(self.reset_btn)
        
        return bar
        
    def _create_settings_panel(self) -> QWidget:
        """Create settings panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(250))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(15)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # Auto-tuning settings
        settings_group = QGroupBox("Auto-Tuning Settings")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        settings_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(get_scaled_size(10))
        
        # Auto-apply
        self.auto_apply = QCheckBox("Auto-Apply Adjustments")
        self.auto_apply.setChecked(False)
        self.auto_apply.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.auto_apply)
        
        # Safety level
        settings_layout.addWidget(QLabel("Safety Level:"))
        self.safety_level = QComboBox()
        self.safety_level.addItems(["Safe", "Moderate", "Aggressive"])
        self.safety_level.setCurrentIndex(0)
        self.safety_level.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        settings_layout.addWidget(self.safety_level)
        
        # Learning mode
        self.learning_mode = QCheckBox("Enable Learning Mode")
        self.learning_mode.setChecked(True)
        self.learning_mode.setStyleSheet("color: #ffffff;")
        settings_layout.addWidget(self.learning_mode)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Status
        status_group = QGroupBox("Status")
        status_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Inactive")
        status_font = get_scaled_font_size(14)
        self.status_label.setStyleSheet(f"font-size: {status_font}px; font-weight: bold; color: #ffaa00; padding: {get_scaled_size(5)}px;")
        status_layout.addWidget(self.status_label)
        
        self.adjustments_count = QLabel("Pending: 0")
        count_font = get_scaled_font_size(11)
        self.adjustments_count.setStyleSheet(f"font-size: {count_font}px; color: #9aa0a6;")
        status_layout.addWidget(self.adjustments_count)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        return panel
        
    def _create_adjustments_panel(self) -> QWidget:
        """Create adjustments panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Adjustments table
        title = QLabel("Recommended Tuning Adjustments")
        title_font = get_scaled_font_size(12)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.adjustments_table = QTableWidget()
        self.adjustments_table.setColumnCount(5)
        self.adjustments_table.setHorizontalHeaderLabels(["Parameter", "Current", "Recommended", "Reason", "Action"])
        self.adjustments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.adjustments_table.setMinimumHeight(get_scaled_size(300))
        self.adjustments_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
            }
        """)
        layout.addWidget(self.adjustments_table, stretch=1)
        
        return panel
        
    def _create_history_panel(self) -> QWidget:
        """Create history panel."""
        panel = QWidget()
        border = get_scaled_size(1)
        panel.setStyleSheet(f"background-color: #1a1a1a; border: {border}px solid #404040;")
        panel.setMaximumWidth(get_scaled_size(300))
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Tuning history
        history_group = QGroupBox("Tuning History")
        group_font = get_scaled_font_size(12)
        group_border = get_scaled_size(1)
        group_radius = get_scaled_size(3)
        group_margin = get_scaled_size(10)
        history_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        history_layout = QVBoxLayout()
        
        from PySide6.QtWidgets import QListWidget
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #404040;
            }
        """)
        history_layout.addWidget(self.history_list)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        layout.addStretch()
        return panel
    
    def _create_bottom_panel(self) -> QWidget:
        """Create bottom panel with graphing and import/export."""
        from PySide6.QtWidgets import QTabWidget, QGroupBox, QPushButton, QFileDialog, QMessageBox
        
        panel = QWidget()
        panel.setStyleSheet("background-color: #1a1a1a; border: 1px solid #404040;")
        layout = QVBoxLayout(panel)
        margin = get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # Sub-tabs
        sub_tabs = QTabWidget()
        sub_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #404040; background-color: #1a1a1a; }
            QTabBar::tab { background-color: #2a2a2a; color: #ffffff; padding: 6px 12px; }
            QTabBar::tab:selected { background-color: #1a1a1a; border-bottom: 2px solid #0080ff; }
        """)
        
        # Graphing tab
        graph_tab = QWidget()
        graph_layout = QVBoxLayout(graph_tab)
        try:
            from ui.advanced_log_graphing import AdvancedLogGraphingWidget
            self.auto_tune_graph = AdvancedLogGraphingWidget()
            graph_layout.addWidget(self.auto_tune_graph, stretch=1)
        except ImportError:
            try:
                from ui.ecu_tuning_widgets import RealTimeGraph
                self.auto_tune_graph = RealTimeGraph()
                graph_layout.addWidget(self.auto_tune_graph, stretch=1)
            except ImportError:
                placeholder = QLabel("Graphing not available")
                placeholder.setStyleSheet("color: #ffffff; padding: 20px;")
                graph_layout.addWidget(placeholder, stretch=1)
                self.auto_tune_graph = None
        sub_tabs.addTab(graph_tab, "📊 Graphing")
        
        # Import/Export tab
        import_export_tab = QWidget()
        ie_layout = QVBoxLayout(import_export_tab)
        
        import_group = QGroupBox("Import")
        import_layout = QVBoxLayout()
        import_btn = QPushButton("📥 Import Tuning Data")
        import_btn.clicked.connect(self._import_tuning_data)
        import_layout.addWidget(import_btn)
        import_group.setLayout(import_layout)
        ie_layout.addWidget(import_group)
        
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        export_btn = QPushButton("📤 Export Tuning Data")
        export_btn.clicked.connect(self._export_tuning_data)
        export_layout.addWidget(export_btn)
        export_group.setLayout(export_layout)
        ie_layout.addWidget(export_group)
        
        ie_layout.addStretch()
        sub_tabs.addTab(import_export_tab, "Import/Export")
        
        layout.addWidget(sub_tabs, stretch=1)
        return panel
    
    def _import_tuning_data(self) -> None:
        """Import tuning data."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Tuning Data", "", "All Files (*.*)")
        if file_path:
            QMessageBox.information(self, "Import", f"Importing from: {file_path}")
    
    def _export_tuning_data(self) -> None:
        """Export tuning data."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Tuning Data", "", "All Files (*.*)")
        if file_path:
            QMessageBox.information(self, "Export", f"Exporting to: {file_path}")
        
    def _start_update_timer(self) -> None:
        """Start timer for updates."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_adjustments)
        self.update_timer.start(1000)  # 1 Hz
        
    def _update_adjustments(self) -> None:
        """Update adjustments table."""
        if not self.tuning_engine:
            return
            
        # Get recommended adjustments
        try:
            adjustments = self.tuning_engine.get_recommended_adjustments()
            self._populate_adjustments_table(adjustments)
        except Exception:
            pass
            
    def _populate_adjustments_table(self, adjustments: list) -> None:
        """Populate adjustments table."""
        self.adjustments_table.setRowCount(len(adjustments))
        
        for row, adj in enumerate(adjustments):
            if not hasattr(adj, 'parameter'):
                continue
                
            # Parameter
            item = QTableWidgetItem(str(adj.parameter.value))
            item.setForeground(QColor("#ffffff"))
            self.adjustments_table.setItem(row, 0, item)
            
            # Current value
            item = QTableWidgetItem(f"{adj.current_value:.2f}")
            item.setForeground(QColor("#9aa0a6"))
            self.adjustments_table.setItem(row, 1, item)
            
            # Recommended value
            item = QTableWidgetItem(f"{adj.recommended_value:.2f}")
            item.setForeground(QColor("#00e0ff"))
            self.adjustments_table.setItem(row, 2, item)
            
            # Reason
            item = QTableWidgetItem(adj.adjustment_reason)
            item.setForeground(QColor("#ffffff"))
            self.adjustments_table.setItem(row, 3, item)
            
            # Action button (placeholder)
            item = QTableWidgetItem("Apply")
            item.setForeground(QColor("#0080ff"))
            self.adjustments_table.setItem(row, 4, item)
            
        self.adjustments_count.setText(f"Pending: {len(adjustments)}")
        
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update auto tuning tab with telemetry data."""
        if not self.tuning_engine:
            if AutoTuningEngine:
                try:
                    auto_apply = self.auto_apply.isChecked() if hasattr(self, 'auto_apply') else False
                    self.tuning_engine = AutoTuningEngine(auto_apply=auto_apply)
                except Exception:
                    pass
        
        if self.tuning_engine:
            try:
                # Update tuning engine with telemetry
                self.tuning_engine.update_telemetry(data)
            except Exception:
                pass
        
        # Update graph if available
        if hasattr(self, 'auto_tune_graph') and self.auto_tune_graph:
            try:
                if hasattr(self.auto_tune_graph, 'update_data'):
                    self.auto_tune_graph.update_data(data)
                elif hasattr(self.auto_tune_graph, 'add_data'):
                    for key, value in data.items():
                        self.auto_tune_graph.add_data(key, value)
            except Exception:
                pass


__all__ = ["AutoTuningTab"]



