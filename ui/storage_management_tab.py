"""
Storage Management Dashboard
Disk usage visualization, cleanup policies, and manual cleanup tools
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QCheckBox,
    QProgressBar,
    QSplitter,
    QMessageBox,
    QFileDialog,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_theme, RacingColor

LOGGER = logging.getLogger(__name__)

try:
    from services.disk_cleanup import DiskCleanup
    from core.disk_manager import DiskManager
except ImportError:
    DiskCleanup = None
    DiskManager = None


class DiskUsageWidget(QWidget):
    """Pie chart widget for disk usage visualization."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.usage_data: Dict[str, float] = {}
        self.setMinimumHeight(get_scaled_size(200))
        self.setMinimumWidth(get_scaled_size(200))

    def update_usage(self, usage_data: Dict[str, float]) -> None:
        """Update disk usage data."""
        self.usage_data = usage_data
        self.update()

    def paintEvent(self, event) -> None:
        """Paint pie chart."""
        if not self.usage_data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        theme = get_racing_theme()
        rect = self.rect().adjusted(10, 10, -10, -10)
        size = min(rect.width(), rect.height())
        center_x = rect.center().x()
        center_y = rect.center().y()
        radius = size // 2 - 10

        # Get usage values
        total = self.usage_data.get("total_gb", 0)
        used = self.usage_data.get("used_gb", 0)
        free = self.usage_data.get("free_gb", 0)

        if total == 0:
            return

        # Calculate angles
        used_angle = int((used / total) * 360 * 16)
        free_angle = int((free / total) * 360 * 16)

        # Draw used space
        if used_angle > 0:
            painter.setBrush(QBrush(QColor(theme.status_critical)))
            painter.setPen(QPen(QColor(theme.border_default), 2))
            painter.drawPie(
                center_x - radius,
                center_y - radius,
                radius * 2,
                radius * 2,
                90 * 16,  # Start at top
                used_angle,
            )

        # Draw free space
        if free_angle > 0:
            painter.setBrush(QBrush(QColor(theme.status_optimal)))
            painter.setPen(QPen(QColor(theme.border_default), 2))
            painter.drawPie(
                center_x - radius,
                center_y - radius,
                radius * 2,
                radius * 2,
                90 * 16 + used_angle,
                free_angle,
            )

        # Draw center text
        painter.setPen(QPen(QColor(theme.text_primary)))
        font = QFont()
        font.setPointSize(get_scaled_font_size(14))
        font.setBold(True)
        painter.setFont(font)

        percent = self.usage_data.get("percent", 0)
        text = f"{percent:.1f}%\nUsed"
        painter.drawText(
            center_x - 50,
            center_y - 20,
            100,
            40,
            Qt.AlignmentFlag.AlignCenter,
            text,
        )


class StorageManagementTab(QWidget):
    """Storage Management Dashboard tab."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.disk_cleanup: Optional[DiskCleanup] = None
        self.disk_manager: Optional[DiskManager] = None

        # Initialize services
        if DiskCleanup:
            try:
                self.disk_cleanup = DiskCleanup()
            except Exception as e:
                LOGGER.error(f"Failed to initialize DiskCleanup: {e}")

        if DiskManager:
            try:
                self.disk_manager = DiskManager()
            except Exception as e:
                LOGGER.error(f"Failed to initialize DiskManager: {e}")

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(5000)  # Update every 5 seconds

        self.setup_ui()
        self._update_display()

    def setup_ui(self) -> None:
        """Setup storage management tab UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        spacing = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)

        theme = get_racing_theme()
        self.setStyleSheet(f"background-color: {theme.bg_primary};")

        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)

        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Disk usage and overview
        left_panel = self._create_overview_panel()
        splitter.addWidget(left_panel)

        # Right: Cleanup settings and tools
        right_panel = self._create_cleanup_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, stretch=1)

    def _create_control_bar(self) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        theme = get_racing_theme()
        padding = get_scaled_size(5)
        bar.setStyleSheet(
            f"background-color: {theme.bg_secondary}; padding: {padding}px; border: 1px solid {theme.border_default};"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(get_scaled_size(10), padding, get_scaled_size(10), padding)

        title = QLabel("Storage Management")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: {theme.text_primary};")
        layout.addWidget(title)

        layout.addStretch()

        # Manual cleanup button
        self.cleanup_btn = QPushButton("Run Cleanup Now")
        btn_font = get_scaled_font_size(11)
        self.cleanup_btn.setStyleSheet(
            f"background-color: {theme.status_warning}; color: #000000; padding: 5px 10px; font-weight: bold; font-size: {btn_font}px;"
        )
        self.cleanup_btn.clicked.connect(self._run_cleanup)
        layout.addWidget(self.cleanup_btn)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(
            f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px 10px; font-size: {btn_font}px;"
        )
        refresh_btn.clicked.connect(self._update_display)
        layout.addWidget(refresh_btn)

        return bar

    def _create_overview_panel(self) -> QWidget:
        """Create overview panel with disk usage."""
        panel = QWidget()
        theme = get_racing_theme()
        panel.setStyleSheet(f"background-color: {theme.bg_secondary}; border: 1px solid {theme.border_default};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        layout.setSpacing(get_scaled_size(15))

        # Disk usage chart
        usage_group = QGroupBox("Disk Usage")
        usage_layout = QVBoxLayout()

        self.disk_usage_widget = DiskUsageWidget()
        usage_layout.addWidget(self.disk_usage_widget)

        # Usage details
        details_layout = QHBoxLayout()

        self.total_label = QLabel("Total: -- GB")
        self.total_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_primary};")
        details_layout.addWidget(self.total_label)

        self.used_label = QLabel("Used: -- GB")
        self.used_label.setStyleSheet(
            f"font-size: {get_scaled_font_size(12)}px; color: {theme.status_critical}; font-weight: bold;"
        )
        details_layout.addWidget(self.used_label)

        self.free_label = QLabel("Free: -- GB")
        self.free_label.setStyleSheet(
            f"font-size: {get_scaled_font_size(12)}px; color: {theme.status_optimal}; font-weight: bold;"
        )
        details_layout.addWidget(self.free_label)

        usage_layout.addLayout(details_layout)
        usage_group.setLayout(usage_layout)
        layout.addWidget(usage_group)

        # Storage breakdown
        breakdown_group = QGroupBox("Storage Breakdown")
        breakdown_layout = QVBoxLayout()

        self.breakdown_table = QTableWidget()
        self.breakdown_table.setColumnCount(3)
        self.breakdown_table.setHorizontalHeaderLabels(["Type", "Size", "Files"])
        self.breakdown_table.horizontalHeader().setStretchLastSection(True)
        self.breakdown_table.setStyleSheet(
            f"color: {theme.text_primary}; background-color: {theme.bg_tertiary};"
        )
        self.breakdown_table.setAlternatingRowColors(True)
        breakdown_layout.addWidget(self.breakdown_table)

        breakdown_group.setLayout(breakdown_layout)
        layout.addWidget(breakdown_group)

        layout.addStretch()
        return panel

    def _create_cleanup_panel(self) -> QWidget:
        """Create cleanup settings panel."""
        panel = QWidget()
        theme = get_racing_theme()
        panel.setStyleSheet(f"background-color: {theme.bg_secondary}; border: 1px solid {theme.border_default};")
        panel.setMaximumWidth(get_scaled_size(350))
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        layout.setSpacing(get_scaled_size(15))

        # Cleanup settings
        settings_group = QGroupBox("Cleanup Settings")
        settings_layout = QVBoxLayout()

        # Auto cleanup enabled
        self.auto_cleanup_cb = QCheckBox("Enable Automatic Cleanup")
        self.auto_cleanup_cb.setChecked(True)
        self.auto_cleanup_cb.setStyleSheet(f"color: {theme.text_primary};")
        settings_layout.addWidget(self.auto_cleanup_cb)

        # Cleanup threshold
        settings_layout.addWidget(QLabel("Cleanup Threshold (%):"))
        self.cleanup_threshold = QSpinBox()
        self.cleanup_threshold.setRange(50, 95)
        self.cleanup_threshold.setValue(90)
        self.cleanup_threshold.setSuffix(" %")
        self.cleanup_threshold.setStyleSheet(
            f"color: {theme.text_primary}; background-color: {theme.bg_tertiary};"
        )
        settings_layout.addWidget(self.cleanup_threshold)

        # Retention days
        settings_layout.addWidget(QLabel("Retention Period (days):"))
        self.retention_days = QSpinBox()
        self.retention_days.setRange(1, 365)
        self.retention_days.setValue(30)
        self.retention_days.setSuffix(" days")
        self.retention_days.setStyleSheet(
            f"color: {theme.text_primary}; background-color: {theme.bg_tertiary};"
        )
        settings_layout.addWidget(self.retention_days)

        # Max disk usage
        settings_layout.addWidget(QLabel("Max Disk Usage (GB):"))
        self.max_usage = QDoubleSpinBox()
        self.max_usage.setRange(1, 1000)
        self.max_usage.setValue(10)
        self.max_usage.setSuffix(" GB")
        self.max_usage.setStyleSheet(
            f"color: {theme.text_primary}; background-color: {theme.bg_tertiary};"
        )
        settings_layout.addWidget(self.max_usage)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Manual cleanup
        manual_group = QGroupBox("Manual Cleanup")
        manual_layout = QVBoxLayout()

        # Clean old files button
        clean_old_btn = QPushButton("Clean Old Files")
        clean_old_btn.setStyleSheet(
            f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px;"
        )
        clean_old_btn.clicked.connect(self._clean_old_files)
        manual_layout.addWidget(clean_old_btn)

        # Clean logs button
        clean_logs_btn = QPushButton("Clean Log Files")
        clean_logs_btn.setStyleSheet(
            f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px;"
        )
        clean_logs_btn.clicked.connect(self._clean_logs)
        manual_layout.addWidget(clean_logs_btn)

        # Clean videos button
        clean_videos_btn = QPushButton("Clean Video Files")
        clean_videos_btn.setStyleSheet(
            f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px;"
        )
        clean_videos_btn.clicked.connect(self._clean_videos)
        manual_layout.addWidget(clean_videos_btn)

        # Clean temp files button
        clean_temp_btn = QPushButton("Clean Temp Files")
        clean_temp_btn.setStyleSheet(
            f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px;"
        )
        clean_temp_btn.clicked.connect(self._clean_temp)
        manual_layout.addWidget(clean_temp_btn)

        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)

        # Status
        status_group = QGroupBox("Last Cleanup")
        status_layout = QVBoxLayout()

        self.last_cleanup_label = QLabel("Never")
        self.last_cleanup_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_secondary};")
        status_layout.addWidget(self.last_cleanup_label)

        self.freed_space_label = QLabel("Freed: 0 MB")
        self.freed_space_label.setStyleSheet(f"font-size: {get_scaled_font_size(12)}px; color: {theme.text_secondary};")
        status_layout.addWidget(self.freed_space_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        layout.addStretch()
        return panel

    def _update_display(self) -> None:
        """Update display with current disk usage."""
        if not self.disk_manager:
            return

        try:
            # Get disk usage
            usage = self.disk_manager.get_disk_usage(".")
            self.disk_usage_widget.update_usage(usage)

            # Update labels
            self.total_label.setText(f"Total: {usage['total_gb']:.2f} GB")
            self.used_label.setText(f"Used: {usage['used_gb']:.2f} GB")
            self.free_label.setText(f"Free: {usage['free_gb']:.2f} GB")

            # Update breakdown
            self._update_breakdown()

        except Exception as e:
            LOGGER.error(f"Error updating disk usage: {e}")

    def _update_breakdown(self) -> None:
        """Update storage breakdown table."""
        # Get breakdown by directory
        breakdown = {
            "Video Files": self._get_directory_size("logs/video"),
            "Log Files": self._get_directory_size("logs"),
            "Sessions": self._get_directory_size("sessions"),
            "Backups": self._get_directory_size("backups"),
            "Cache": self._get_directory_size("cache"),
            "Temp": self._get_directory_size("tmp"),
        }

        self.breakdown_table.setRowCount(len(breakdown))
        row = 0
        for dir_type, size_mb in breakdown.items():
            self.breakdown_table.setItem(row, 0, QTableWidgetItem(dir_type))
            self.breakdown_table.setItem(row, 1, QTableWidgetItem(f"{size_mb:.2f} MB"))
            # File count would require directory scanning
            self.breakdown_table.setItem(row, 2, QTableWidgetItem("--"))
            row += 1

    def _get_directory_size(self, directory: str) -> float:
        """Get directory size in MB."""
        try:
            path = Path(directory)
            if not path.exists():
                return 0.0

            total = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total += file_path.stat().st_size

            return total / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0.0

    def _run_cleanup(self) -> None:
        """Run automatic cleanup."""
        if not self.disk_cleanup:
            QMessageBox.warning(self, "Error", "Disk cleanup service not available")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Cleanup",
            "This will delete old files based on retention settings. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                directories = ["logs", "logs/video", "sessions", "cache", "tmp"]
                result = self.disk_cleanup.cleanup_if_needed(directories)

                if result.get("skipped"):
                    QMessageBox.information(self, "Cleanup Skipped", result.get("reason", "Unknown reason"))
                else:
                    freed_mb = result.get("freed_mb", 0)
                    QMessageBox.information(
                        self,
                        "Cleanup Complete",
                        f"Freed {freed_mb:.2f} MB of disk space.",
                    )
                    self._update_display()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cleanup failed: {e}")

    def _clean_old_files(self) -> None:
        """Clean old files manually."""
        if not self.disk_cleanup:
            return

        try:
            result = self.disk_cleanup.cleanup_old_files("logs", older_than_days=self.retention_days.value())
            freed_mb = result.get("freed_mb", 0)
            QMessageBox.information(self, "Cleanup Complete", f"Freed {freed_mb:.2f} MB")
            self._update_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cleanup failed: {e}")

    def _clean_logs(self) -> None:
        """Clean log files."""
        if not self.disk_cleanup:
            return

        try:
            result = self.disk_cleanup.cleanup_old_files("logs", pattern="*.log")
            freed_mb = result.get("freed_mb", 0)
            QMessageBox.information(self, "Cleanup Complete", f"Freed {freed_mb:.2f} MB from logs")
            self._update_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cleanup failed: {e}")

    def _clean_videos(self) -> None:
        """Clean video files."""
        if not self.disk_cleanup:
            return

        try:
            result = self.disk_cleanup.cleanup_old_files("logs/video", pattern="*.mp4")
            freed_mb = result.get("freed_mb", 0)
            QMessageBox.information(self, "Cleanup Complete", f"Freed {freed_mb:.2f} MB from videos")
            self._update_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cleanup failed: {e}")

    def _clean_temp(self) -> None:
        """Clean temporary files."""
        if not self.disk_cleanup:
            return

        try:
            result = self.disk_cleanup.cleanup_temp_files(["cache", "tmp"])
            freed_mb = result.get("freed_mb", 0)
            QMessageBox.information(self, "Cleanup Complete", f"Freed {freed_mb:.2f} MB from temp files")
            self._update_display()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cleanup failed: {e}")


__all__ = ["StorageManagementTab", "DiskUsageWidget"]







