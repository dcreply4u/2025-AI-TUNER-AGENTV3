"""
Fleet Dashboard Tab

Comprehensive fleet management dashboard with real-time monitoring,
driver management, cost analysis, and compliance tracking.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QTabWidget,
    QScrollArea,
    QFrame,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size

try:
    from services.fleet_management import FleetManagement, FleetMetrics
    from services.driver_behavior import DriverBehaviorAnalyzer
    from services.fuel_efficiency import FuelEfficiencyTracker
    from services.maintenance_scheduler import MaintenanceScheduler
    from services.eld_compliance import ELDComplianceTracker
    FLEET_AVAILABLE = True
except ImportError:
    FLEET_AVAILABLE = False
    FleetManagement = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class FleetDashboardTab(QWidget):
    """Fleet management dashboard tab."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.fleet_manager: Optional[FleetManagement] = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup fleet dashboard UI."""
        main_layout = QVBoxLayout(self)
        margin = get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)

        # Title
        title = QLabel("Fleet Management Dashboard")
        title_font = get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)

        # Metrics overview
        metrics_frame = self._create_metrics_overview()
        main_layout.addWidget(metrics_frame)

        # Tabs for different views
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #1a1a1a;
                border: 1px solid #404040;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 8px 16px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
            }
        """)

        # Vehicles tab
        vehicles_tab = self._create_vehicles_tab()
        tabs.addTab(vehicles_tab, "Vehicles")

        # Drivers tab
        drivers_tab = self._create_drivers_tab()
        tabs.addTab(drivers_tab, "Drivers")

        # Analytics tab
        analytics_tab = self._create_analytics_tab()
        tabs.addTab(analytics_tab, "Analytics")

        # Compliance tab
        compliance_tab = self._create_compliance_tab()
        tabs.addTab(compliance_tab, "Compliance")

        main_layout.addWidget(tabs)

        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_dashboard)
        self.update_timer.start(5000)  # Update every 5 seconds

    def _create_metrics_overview(self) -> QWidget:
        """Create metrics overview panel."""
        frame = QFrame()
        frame.setStyleSheet("background-color: #2a2a2a; border: 1px solid #404040; padding: 10px;")
        layout = QHBoxLayout(frame)

        metrics = [
            ("Total Vehicles", "0", "#3498db"),
            ("Active Vehicles", "0", "#2ecc71"),
            ("In Maintenance", "0", "#e74c3c"),
            ("Avg MPG", "0.0", "#f39c12"),
            ("Fleet Utilization", "0%", "#9b59b6"),
            ("Avg Driver Score", "0", "#1abc9c"),
        ]

        self.metric_labels = {}
        for label_text, value, color in metrics:
            metric_widget = QWidget()
            metric_layout = QVBoxLayout(metric_widget)
            metric_layout.setContentsMargins(10, 10, 10, 10)

            label = QLabel(label_text)
            label.setStyleSheet(f"color: #aaaaaa; font-size: {get_scaled_font_size(11)}px;")
            metric_layout.addWidget(label)

            value_label = QLabel(value)
            value_label.setStyleSheet(f"color: {color}; font-size: {get_scaled_font_size(16)}px; font-weight: bold;")
            metric_layout.addWidget(value_label)

            self.metric_labels[label_text] = value_label
            layout.addWidget(metric_widget)

        layout.addStretch()
        return frame

    def _create_vehicles_tab(self) -> QWidget:
        """Create vehicles management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Vehicle table
        self.vehicle_table = QTableWidget()
        self.vehicle_table.setColumnCount(8)
        self.vehicle_table.setHorizontalHeaderLabels([
            "Vehicle", "Driver", "Status", "MPG", "Driver Score", "Cost/Mile", "Mileage", "Location"
        ])
        self.vehicle_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                gridline-color: #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
            }
        """)
        layout.addWidget(self.vehicle_table)

        return widget

    def _create_drivers_tab(self) -> QWidget:
        """Create drivers management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Driver table
        self.driver_table = QTableWidget()
        self.driver_table.setColumnCount(6)
        self.driver_table.setHorizontalHeaderLabels([
            "Driver", "Vehicle", "Score", "Hours", "Violations", "Status"
        ])
        self.driver_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                gridline-color: #404040;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 5px;
            }
        """)
        layout.addWidget(self.driver_table)

        return widget

    def _create_analytics_tab(self) -> QWidget:
        """Create analytics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Analytics content
        analytics_label = QLabel("Fleet Analytics & Reports")
        analytics_label.setStyleSheet(f"color: #ffffff; font-size: {get_scaled_font_size(14)}px;")
        layout.addWidget(analytics_label)

        # Add analytics widgets here (charts, reports, etc.)
        layout.addStretch()

        return widget

    def _create_compliance_tab(self) -> QWidget:
        """Create compliance tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Compliance content
        compliance_label = QLabel("Compliance & ELD/HOS Tracking")
        compliance_label.setStyleSheet(f"color: #ffffff; font-size: {get_scaled_font_size(14)}px;")
        layout.addWidget(compliance_label)

        # Add compliance widgets here
        layout.addStretch()

        return widget

    def _update_dashboard(self) -> None:
        """Update dashboard with latest data."""
        if not self.fleet_manager:
            return

        try:
            dashboard_data = self.fleet_manager.get_fleet_dashboard()
            metrics = dashboard_data.get("metrics", {})

            # Update metrics
            if "Total Vehicles" in self.metric_labels:
                self.metric_labels["Total Vehicles"].setText(str(metrics.get("total_vehicles", 0)))
            if "Active Vehicles" in self.metric_labels:
                self.metric_labels["Active Vehicles"].setText(str(metrics.get("active_vehicles", 0)))
            if "In Maintenance" in self.metric_labels:
                self.metric_labels["In Maintenance"].setText(str(metrics.get("vehicles_in_maintenance", 0)))
            if "Avg MPG" in self.metric_labels:
                avg_mpg = metrics.get("average_mpg")
                self.metric_labels["Avg MPG"].setText(f"{avg_mpg:.1f}" if avg_mpg else "N/A")
            if "Fleet Utilization" in self.metric_labels:
                util = metrics.get("fleet_utilization", 0.0)
                self.metric_labels["Fleet Utilization"].setText(f"{util:.1f}%")
            if "Avg Driver Score" in self.metric_labels:
                avg_score = metrics.get("average_driver_score")
                self.metric_labels["Avg Driver Score"].setText(f"{avg_score:.0f}" if avg_score else "N/A")

            # Update vehicle table
            vehicles = dashboard_data.get("vehicles", {})
            self.vehicle_table.setRowCount(len(vehicles))
            for row, (vid, vehicle_data) in enumerate(vehicles.items()):
                self.vehicle_table.setItem(row, 0, QTableWidgetItem(vehicle_data.get("name", "")))
                self.vehicle_table.setItem(row, 1, QTableWidgetItem(vehicle_data.get("driver", "Unassigned")))
                self.vehicle_table.setItem(row, 2, QTableWidgetItem(vehicle_data.get("status", "unknown")))
                mpg = vehicle_data.get("fuel_efficiency_mpg")
                self.vehicle_table.setItem(row, 3, QTableWidgetItem(f"{mpg:.1f}" if mpg else "N/A"))
                score = vehicle_data.get("driver_score")
                self.vehicle_table.setItem(row, 4, QTableWidgetItem(f"{score:.0f}" if score else "N/A"))
                cpm = vehicle_data.get("cost_per_mile")
                self.vehicle_table.setItem(row, 5, QTableWidgetItem(f"${cpm:.2f}" if cpm else "N/A"))
                mileage = vehicle_data.get("total_mileage", 0.0)
                self.vehicle_table.setItem(row, 6, QTableWidgetItem(f"{mileage:,.0f}"))

            # Update driver table
            drivers = dashboard_data.get("drivers", {})
            self.driver_table.setRowCount(len(drivers))
            for row, (did, driver_data) in enumerate(drivers.items()):
                self.driver_table.setItem(row, 0, QTableWidgetItem(driver_data.get("name", "")))
                self.driver_table.setItem(row, 1, QTableWidgetItem(driver_data.get("current_vehicle", "None")))
                score = driver_data.get("driver_score", 0.0)
                self.driver_table.setItem(row, 2, QTableWidgetItem(f"{score:.0f}"))
                hours = driver_data.get("total_driving_hours", 0.0)
                self.driver_table.setItem(row, 3, QTableWidgetItem(f"{hours:.1f}"))
                violations = driver_data.get("violations_count", 0)
                self.driver_table.setItem(row, 4, QTableWidgetItem(str(violations)))
                self.driver_table.setItem(row, 5, QTableWidgetItem("Active" if driver_data.get("current_vehicle") else "Available"))

        except Exception as e:
            LOGGER.error("Error updating fleet dashboard: %s", e)

    def set_fleet_manager(self, fleet_manager: FleetManagement) -> None:
        """Set fleet manager instance."""
        self.fleet_manager = fleet_manager


__all__ = ["FleetDashboardTab"]









