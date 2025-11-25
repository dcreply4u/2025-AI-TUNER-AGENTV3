"""
Backup Manager Tab
UI for managing backups and reverting files
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QFileDialog,
    QMessageBox,
    QTextEdit,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size, get_scaled_stylesheet

try:
    from services.backup_manager import (
        BackupManager,
        BackupType,
        BackupEntry,
        BackupSettings,
    )
except ImportError:
    BackupManager = None
    BackupType = None
    BackupEntry = None
    BackupSettings = None


class BackupManagerTab(QWidget):
    """Backup Manager tab for managing backups and reverts."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        
        # Initialize backup manager
        self.backup_manager: Optional[BackupManager] = None
        if BackupManager:
            try:
                self.backup_manager = BackupManager()
            except Exception as e:
                print(f"Failed to initialize backup manager: {e}")
        
        self.current_file_path: Optional[str] = None
        self.setup_ui()
        self._update_displays()
    
    def setup_ui(self) -> None:
        """Setup backup manager tab."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        spacing = self.scaler.get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Title
        title = QLabel("Backup Manager - Auto-Backup & Version Control")
        title_font = self.scaler.get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        tab_padding_v = self.scaler.get_scaled_size(6)
        tab_padding_h = self.scaler.get_scaled_size(15)
        tab_font = self.scaler.get_scaled_font_size(10)
        tab_border = self.scaler.get_scaled_size(1)
        tab_margin = self.scaler.get_scaled_size(2)
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {tab_border}px solid #404040;
                background-color: #1a1a1a;
            }}
            QTabBar::tab {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: {tab_margin}px;
                border: {tab_border}px solid #404040;
                font-size: {tab_font}px;
            }}
            QTabBar::tab:selected {{
                background-color: #1a1a1a;
                border-bottom: {self.scaler.get_scaled_size(2)}px solid #0080ff;
            }}
        """)
        
        # Backup Settings tab
        tabs.addTab(self._create_settings_tab(), "Backup Settings")
        
        # File Backups tab
        tabs.addTab(self._create_file_backups_tab(), "File Backups")
        
        # Statistics tab
        tabs.addTab(self._create_statistics_tab(), "Statistics")
        
        main_layout.addWidget(tabs, stretch=1)
    
    def _create_settings_tab(self) -> QWidget:
        """Create backup settings tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Backup Configuration Settings")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {self.scaler.get_scaled_font_size(12)}px; font-weight: bold; color: #ffffff;
                border: {self.scaler.get_scaled_size(1)}px solid #404040; border-radius: {self.scaler.get_scaled_size(3)}px;
                margin-top: {self.scaler.get_scaled_size(10)}px; padding-top: {self.scaler.get_scaled_size(10)}px;
            }}
        """)
        general_layout = QVBoxLayout()
        
        self.enabled_check = QCheckBox("Enable Backups")
        self.enabled_check.setChecked(True)
        self.enabled_check.setStyleSheet("color: #ffffff;")
        self.enabled_check.stateChanged.connect(self._on_settings_changed)
        general_layout.addWidget(self.enabled_check)
        
        self.auto_backup_check = QCheckBox("Auto-Backup Enabled")
        self.auto_backup_check.setChecked(True)
        self.auto_backup_check.setStyleSheet("color: #ffffff;")
        self.auto_backup_check.stateChanged.connect(self._on_settings_changed)
        general_layout.addWidget(self.auto_backup_check)
        
        self.backup_on_save_check = QCheckBox("Backup on File Save")
        self.backup_on_save_check.setChecked(True)
        self.backup_on_save_check.setStyleSheet("color: #ffffff;")
        self.backup_on_save_check.stateChanged.connect(self._on_settings_changed)
        general_layout.addWidget(self.backup_on_save_check)
        
        self.backup_on_change_check = QCheckBox("Backup on File Change")
        self.backup_on_change_check.setChecked(True)
        self.backup_on_change_check.setStyleSheet("color: #ffffff;")
        self.backup_on_change_check.stateChanged.connect(self._on_settings_changed)
        general_layout.addWidget(self.backup_on_change_check)
        
        self.backup_before_apply_check = QCheckBox("Backup Before Apply to ECU")
        self.backup_before_apply_check.setChecked(True)
        self.backup_before_apply_check.setStyleSheet("color: #ffffff;")
        self.backup_before_apply_check.stateChanged.connect(self._on_settings_changed)
        general_layout.addWidget(self.backup_before_apply_check)
        
        self.backup_before_burn_check = QCheckBox("Backup Before Burn to ECU")
        self.backup_before_burn_check.setChecked(True)
        self.backup_before_burn_check.setStyleSheet("color: #ffffff;")
        self.backup_before_burn_check.stateChanged.connect(self._on_settings_changed)
        general_layout.addWidget(self.backup_before_burn_check)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Retention settings
        retention_group = QGroupBox("Backup Retention")
        retention_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {self.scaler.get_scaled_font_size(12)}px; font-weight: bold; color: #ffffff;
                border: {self.scaler.get_scaled_size(1)}px solid #404040; border-radius: {self.scaler.get_scaled_size(3)}px;
                margin-top: {self.scaler.get_scaled_size(10)}px; padding-top: {self.scaler.get_scaled_size(10)}px;
            }}
        """)
        retention_layout = QVBoxLayout()
        
        retention_layout.addWidget(QLabel("Max Backups Per File:"))
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setRange(1, 1000)
        self.max_backups_spin.setValue(50)
        self.max_backups_spin.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.max_backups_spin.valueChanged.connect(self._on_settings_changed)
        retention_layout.addWidget(self.max_backups_spin)
        
        retention_layout.addWidget(QLabel("Backup Interval (seconds):"))
        self.backup_interval_spin = QDoubleSpinBox()
        self.backup_interval_spin.setRange(1.0, 3600.0)
        self.backup_interval_spin.setValue(300.0)
        self.backup_interval_spin.setSingleStep(60.0)
        self.backup_interval_spin.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.backup_interval_spin.valueChanged.connect(self._on_settings_changed)
        retention_layout.addWidget(self.backup_interval_spin)
        
        retention_layout.addWidget(QLabel("Keep Daily Backups (days):"))
        self.keep_daily_spin = QSpinBox()
        self.keep_daily_spin.setRange(1, 365)
        self.keep_daily_spin.setValue(30)
        self.keep_daily_spin.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.keep_daily_spin.valueChanged.connect(self._on_settings_changed)
        retention_layout.addWidget(self.keep_daily_spin)
        
        retention_layout.addWidget(QLabel("Keep Weekly Backups (weeks):"))
        self.keep_weekly_spin = QSpinBox()
        self.keep_weekly_spin.setRange(1, 104)
        self.keep_weekly_spin.setValue(12)
        self.keep_weekly_spin.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        self.keep_weekly_spin.valueChanged.connect(self._on_settings_changed)
        retention_layout.addWidget(self.keep_weekly_spin)
        
        retention_group.setLayout(retention_layout)
        layout.addWidget(retention_group)
        
        # Backup directory
        directory_group = QGroupBox("Backup Directory")
        directory_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {self.scaler.get_scaled_font_size(12)}px; font-weight: bold; color: #ffffff;
                border: {self.scaler.get_scaled_size(1)}px solid #404040; border-radius: {self.scaler.get_scaled_size(3)}px;
                margin-top: {self.scaler.get_scaled_size(10)}px; padding-top: {self.scaler.get_scaled_size(10)}px;
            }}
        """)
        directory_layout = QVBoxLayout()
        
        self.directory_label = QLabel("backups/")
        self.directory_label.setStyleSheet("color: #ffffff; font-family: 'Courier New', monospace;")
        directory_layout.addWidget(self.directory_label)
        
        change_dir_btn = QPushButton("Change Directory")
        btn_padding_v = self.scaler.get_scaled_size(5)
        btn_padding_h = self.scaler.get_scaled_size(15)
        btn_font = self.scaler.get_scaled_font_size(11)
        change_dir_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0080ff;
                color: #ffffff;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
            }}
        """)
        change_dir_btn.clicked.connect(self._change_backup_directory)
        directory_layout.addWidget(change_dir_btn)
        
        directory_group.setLayout(directory_layout)
        layout.addWidget(directory_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #00ff00;
                color: #000000;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
                font-weight: bold;
            }}
        """)
        save_settings_btn.clicked.connect(self._save_settings)
        actions_layout.addWidget(save_settings_btn)
        
        cleanup_btn = QPushButton("Cleanup Old Backups")
        cleanup_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ff8000;
                color: #ffffff;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
            }}
        """)
        cleanup_btn.clicked.connect(self._cleanup_backups)
        actions_layout.addWidget(cleanup_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        return panel
    
    def _create_file_backups_tab(self) -> QWidget:
        """Create file backups tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("File Backups & Revert")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("File:"))
        
        self.file_path_edit = QTextEdit()
        self.file_path_edit.setMaximumHeight(self.scaler.get_scaled_size(30))
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setStyleSheet("background-color: #2a2a2a; color: #ffffff; border: 1px solid #404040;")
        file_layout.addWidget(self.file_path_edit, stretch=1)
        
        browse_btn = QPushButton("Browse...")
        btn_padding_v = self.scaler.get_scaled_size(5)
        btn_padding_h = self.scaler.get_scaled_size(15)
        btn_font = self.scaler.get_scaled_font_size(11)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0080ff;
                color: #ffffff;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
            }}
        """)
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # Backups table
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(6)
        self.backups_table.setHorizontalHeaderLabels([
            "Timestamp", "Description", "Size", "Type", "Hash", "Actions"
        ])
        self.backups_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.backups_table.setMinimumHeight(self.scaler.get_scaled_size(400))
        table_padding = self.scaler.get_scaled_size(5)
        table_border = self.scaler.get_scaled_size(1)
        self.backups_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: {table_border}px solid #404040;
            }}
            QHeaderView::section {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {table_padding}px;
                border: {table_border}px solid #404040;
            }}
        """)
        layout.addWidget(self.backups_table)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        create_backup_btn = QPushButton("Create Backup Now")
        create_backup_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0080ff;
                color: #ffffff;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
                font-weight: bold;
            }}
        """)
        create_backup_btn.clicked.connect(self._create_backup_now)
        actions_layout.addWidget(create_backup_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        return panel
    
    def _create_statistics_tab(self) -> QWidget:
        """Create statistics tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Backup Statistics")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_font = self.scaler.get_scaled_font_size(11)
        stats_border = self.scaler.get_scaled_size(1)
        self.stats_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: {stats_font}px;
                border: {stats_border}px solid #404040;
            }}
        """)
        self.stats_text.setMinimumHeight(self.scaler.get_scaled_size(500))
        layout.addWidget(self.stats_text)
        
        return panel
    
    def _on_settings_changed(self) -> None:
        """Handle settings change."""
        # Settings are applied immediately
        pass
    
    def _save_settings(self) -> None:
        """Save backup settings."""
        if not self.backup_manager:
            return
        
        self.backup_manager.settings.enabled = self.enabled_check.isChecked()
        self.backup_manager.settings.auto_backup_enabled = self.auto_backup_check.isChecked()
        self.backup_manager.settings.backup_on_save = self.backup_on_save_check.isChecked()
        self.backup_manager.settings.backup_on_change = self.backup_on_change_check.isChecked()
        self.backup_manager.settings.backup_before_apply = self.backup_before_apply_check.isChecked()
        self.backup_manager.settings.backup_before_burn = self.backup_before_burn_check.isChecked()
        self.backup_manager.settings.max_backups_per_file = self.max_backups_spin.value()
        self.backup_manager.settings.backup_interval_seconds = self.backup_interval_spin.value()
        self.backup_manager.settings.keep_daily_backups = self.keep_daily_spin.value()
        self.backup_manager.settings.keep_weekly_backups = self.keep_weekly_spin.value()
        
        QMessageBox.information(self, "Settings Saved", "Backup settings have been saved.")
    
    def _change_backup_directory(self) -> None:
        """Change backup directory."""
        if not self.backup_manager:
            return
        
        directory = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if directory:
            self.backup_manager.backup_dir = Path(directory)
            self.directory_label.setText(directory)
    
    def _cleanup_backups(self) -> None:
        """Cleanup old backups."""
        if not self.backup_manager:
            return
        
        deleted = self.backup_manager.cleanup_old_backups()
        QMessageBox.information(self, "Cleanup Complete", f"Deleted {deleted} old backups.")
        self._update_displays()
    
    def _browse_file(self) -> None:
        """Browse for file to manage backups."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File for Backup Management",
            "",
            "All Files (*.*)"
        )
        if file_path:
            self.current_file_path = file_path
            self.file_path_edit.setText(file_path)
            self._update_backups_table()
    
    def _create_backup_now(self) -> None:
        """Create backup of current file."""
        if not self.backup_manager or not self.current_file_path:
            QMessageBox.warning(self, "No File", "Please select a file first.")
            return
        
        # Determine backup type from file extension
        backup_type = BackupType.GLOBAL
        if self.current_file_path.endswith(('.bin', '.hex')):
            backup_type = BackupType.ECU_BINARY
        elif self.current_file_path.endswith(('.cal', '.tune')):
            backup_type = BackupType.ECU_CALIBRATION
        
        backup = self.backup_manager.create_backup(
            self.current_file_path,
            backup_type,
            description="Manual backup",
            force=True
        )
        
        if backup:
            QMessageBox.information(self, "Backup Created", f"Backup created successfully:\n{backup.backup_id}")
            self._update_backups_table()
            self._update_displays()
        else:
            QMessageBox.warning(self, "Backup Failed", "Failed to create backup.")
    
    def _update_backups_table(self) -> None:
        """Update backups table."""
        if not self.backup_manager or not self.current_file_path:
            return
        
        backups = self.backup_manager.get_backups(self.current_file_path)
        self.backups_table.setRowCount(len(backups))
        
        for row, backup in enumerate(backups):
            # Timestamp
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(backup.timestamp))
            self.backups_table.setItem(row, 0, QTableWidgetItem(timestamp_str))
            
            # Description
            self.backups_table.setItem(row, 1, QTableWidgetItem(backup.description))
            
            # Size
            size_mb = backup.file_size / (1024 * 1024)
            self.backups_table.setItem(row, 2, QTableWidgetItem(f"{size_mb:.2f} MB"))
            
            # Type
            type_str = backup.backup_type.value if hasattr(backup.backup_type, 'value') else str(backup.backup_type)
            self.backups_table.setItem(row, 3, QTableWidgetItem(type_str))
            
            # Hash (shortened)
            hash_short = backup.file_hash[:8] + "..."
            self.backups_table.setItem(row, 4, QTableWidgetItem(hash_short))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            revert_btn = QPushButton("Revert")
            revert_btn.setStyleSheet("background-color: #ff8000; color: #ffffff; padding: 2px 8px; font-size: 9px;")
            revert_btn.clicked.connect(lambda checked, b=backup: self._revert_to_backup(b))
            actions_layout.addWidget(revert_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #ff0000; color: #ffffff; padding: 2px 8px; font-size: 9px;")
            delete_btn.clicked.connect(lambda checked, b=backup: self._delete_backup(b))
            actions_layout.addWidget(delete_btn)
            
            self.backups_table.setCellWidget(row, 5, actions_widget)
    
    def _revert_to_backup(self, backup: BackupEntry) -> None:
        """Revert file to backup."""
        if not self.backup_manager:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Revert",
            f"Revert file to backup from {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(backup.timestamp))}?\n\n"
            "A backup of the current file will be created first.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.backup_manager.revert_to_backup(backup, create_backup=True)
            if success:
                QMessageBox.information(self, "Revert Successful", "File has been reverted to the selected backup.")
                self._update_backups_table()
            else:
                QMessageBox.critical(self, "Revert Failed", "Failed to revert file.")
    
    def _delete_backup(self, backup: BackupEntry) -> None:
        """Delete backup."""
        if not self.backup_manager:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete backup from {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(backup.timestamp))}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.backup_manager.delete_backup(backup)
            if success:
                QMessageBox.information(self, "Delete Successful", "Backup has been deleted.")
                self._update_backups_table()
                self._update_displays()
            else:
                QMessageBox.critical(self, "Delete Failed", "Failed to delete backup.")
    
    def _update_displays(self) -> None:
        """Update all displays."""
        if not self.backup_manager:
            return
        
        # Update statistics
        stats = self.backup_manager.get_backup_statistics()
        stats_text = f"""
Backup Statistics:
==================
Total Backups: {stats['total_backups']}
Total Files: {stats['total_files']}
Total Size: {stats['total_size_mb']:.2f} MB
Backup Directory: {stats['backup_directory']}
"""
        self.stats_text.setText(stats_text)
        
        # Update directory label
        if self.backup_manager:
            self.directory_label.setText(str(self.backup_manager.backup_dir))
    
    def create_ecu_backup(self, file_path: str, backup_type: BackupType, description: str = "") -> Optional[BackupEntry]:
        """Create backup for ECU file (called from ECU tuning tabs)."""
        if not self.backup_manager:
            return None
        
        return self.backup_manager.create_backup(
            file_path,
            backup_type,
            description=description
        )
    
    def get_ecu_backups(self, file_path: str) -> list:
        """Get backups for ECU file."""
        if not self.backup_manager:
            return []
        
        return self.backup_manager.get_backups(file_path)
    
    def revert_ecu_file(self, backup: BackupEntry) -> bool:
        """Revert ECU file to backup."""
        if not self.backup_manager:
            return False
        
        return self.backup_manager.revert_to_backup(backup, create_backup=True)

