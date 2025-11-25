"""
Auto-Detection Tab
UI for global auto-detection system
"""

from __future__ import annotations

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
    QGridLayout,
    QTextEdit,
    QProgressBar,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size, get_scaled_stylesheet

try:
    from services.global_auto_detection import (
        GlobalAutoDetector,
        AutoDetectionResults,
    )
except ImportError:
    GlobalAutoDetector = None
    AutoDetectionResults = None


class AutoDetectionTab(QWidget):
    """Auto-Detection tab for comprehensive component detection."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        
        # Initialize auto-detector
        self.detector: Optional[GlobalAutoDetector] = None
        if GlobalAutoDetector:
            try:
                self.detector = GlobalAutoDetector()
            except Exception as e:
                print(f"Failed to initialize auto-detector: {e}")
        
        self.results: Optional[AutoDetectionResults] = None
        self.setup_ui()
        self._start_auto_detection()
    
    def setup_ui(self) -> None:
        """Setup auto-detection tab."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        spacing = self.scaler.get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Title
        title = QLabel("Global Auto-Detection - Automatic Component & Configuration Detection")
        title_font = self.scaler.get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.detect_btn = QPushButton("Run Auto-Detection")
        btn_padding_v = self.scaler.get_scaled_size(8)
        btn_padding_h = self.scaler.get_scaled_size(20)
        btn_font = self.scaler.get_scaled_font_size(12)
        self.detect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0080ff;
                color: #ffffff;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0066cc;
            }}
        """)
        self.detect_btn.clicked.connect(self._run_detection)
        control_layout.addWidget(self.detect_btn)
        
        self.apply_btn = QPushButton("Apply Detected Settings")
        self.apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #00ff00;
                color: #000000;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #00cc00;
            }}
        """)
        self.apply_btn.clicked.connect(self._apply_settings)
        self.apply_btn.setEnabled(False)
        control_layout.addWidget(self.apply_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #404040;
                border-radius: 3px;
                text-align: center;
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #0080ff;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Results tabs
        results_tabs = QTabWidget()
        tab_padding_v = self.scaler.get_scaled_size(6)
        tab_padding_h = self.scaler.get_scaled_size(15)
        tab_font = self.scaler.get_scaled_font_size(10)
        tab_border = self.scaler.get_scaled_size(1)
        tab_margin = self.scaler.get_scaled_size(2)
        results_tabs.setStyleSheet(f"""
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
        
        # Sensors tab
        results_tabs.addTab(self._create_sensors_tab(), "Sensors")
        
        # Engine tab
        results_tabs.addTab(self._create_engine_tab(), "Engine")
        
        # Transmission tab
        results_tabs.addTab(self._create_transmission_tab(), "Transmission")
        
        # Communication tab
        results_tabs.addTab(self._create_communication_tab(), "Communication")
        
        # ECU Parameters tab
        results_tabs.addTab(self._create_ecu_parameters_tab(), "ECU Parameters")
        
        # ECU Detection tab
        results_tabs.addTab(self._create_ecu_detection_tab(), "ECU Detection")
        
        # Recommendations tab
        results_tabs.addTab(self._create_recommendations_tab(), "Recommendations")
        
        main_layout.addWidget(results_tabs, stretch=1)
    
    def _create_sensors_tab(self) -> QWidget:
        """Create sensors detection tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Detected Sensors")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.sensors_table = QTableWidget()
        self.sensors_table.setColumnCount(7)
        self.sensors_table.setHorizontalHeaderLabels([
            "Sensor", "Type", "Min", "Max", "Unit", "Detected", "Confidence"
        ])
        self.sensors_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sensors_table.setMinimumHeight(self.scaler.get_scaled_size(300))
        table_padding = self.scaler.get_scaled_size(5)
        table_border = self.scaler.get_scaled_size(1)
        self.sensors_table.setStyleSheet(f"""
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
        layout.addWidget(self.sensors_table)
        
        return panel
    
    def _create_engine_tab(self) -> QWidget:
        """Create engine detection tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Detected Engine")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.engine_info = QTextEdit()
        self.engine_info.setReadOnly(True)
        info_font = self.scaler.get_scaled_font_size(11)
        info_border = self.scaler.get_scaled_size(1)
        self.engine_info.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: {info_font}px;
                border: {info_border}px solid #404040;
            }}
        """)
        self.engine_info.setMinimumHeight(self.scaler.get_scaled_size(400))
        layout.addWidget(self.engine_info)
        
        return panel
    
    def _create_transmission_tab(self) -> QWidget:
        """Create transmission detection tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Detected Transmission")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.transmission_info = QTextEdit()
        self.transmission_info.setReadOnly(True)
        info_font = self.scaler.get_scaled_font_size(11)
        info_border = self.scaler.get_scaled_size(1)
        self.transmission_info.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: {info_font}px;
                border: {info_border}px solid #404040;
            }}
        """)
        self.transmission_info.setMinimumHeight(self.scaler.get_scaled_size(400))
        layout.addWidget(self.transmission_info)
        
        return panel
    
    def _create_communication_tab(self) -> QWidget:
        """Create communication interfaces tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Detected Communication Interfaces")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.communication_table = QTableWidget()
        self.communication_table.setColumnCount(5)
        self.communication_table.setHorizontalHeaderLabels([
            "Type", "Port/Device", "Speed/Baudrate", "Description", "Status"
        ])
        self.communication_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.communication_table.setMinimumHeight(self.scaler.get_scaled_size(300))
        table_padding = self.scaler.get_scaled_size(5)
        table_border = self.scaler.get_scaled_size(1)
        self.communication_table.setStyleSheet(f"""
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
        layout.addWidget(self.communication_table)
        
        return panel
    
    def _create_ecu_parameters_tab(self) -> QWidget:
        """Create ECU parameters tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Detected ECU Parameters")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.ecu_params_info = QTextEdit()
        self.ecu_params_info.setReadOnly(True)
        info_font = self.scaler.get_scaled_font_size(10)
        info_border = self.scaler.get_scaled_size(1)
        self.ecu_params_info.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: {info_font}px;
                border: {info_border}px solid #404040;
            }}
        """)
        self.ecu_params_info.setMinimumHeight(self.scaler.get_scaled_size(400))
        layout.addWidget(self.ecu_params_info)
        
        return panel
    
    def _create_ecu_detection_tab(self) -> QWidget:
        """Create ECU detection tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Multi-ECU Detection - Standalone, Piggyback, OEM ECUs")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Detected ECUs table
        self.ecus_table = QTableWidget()
        self.ecus_table.setColumnCount(8)
        self.ecus_table.setHorizontalHeaderLabels([
            "ECU ID", "Vendor", "Type", "Primary", "CAN IDs", "Message Rate", "Conflicts", "Status"
        ])
        self.ecus_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ecus_table.setMinimumHeight(self.scaler.get_scaled_size(300))
        table_padding = self.scaler.get_scaled_size(5)
        table_border = self.scaler.get_scaled_size(1)
        self.ecus_table.setStyleSheet(f"""
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
        layout.addWidget(self.ecus_table)
        
        # Conflicts summary
        conflicts_group = QGroupBox("ECU Conflicts & Warnings")
        conflicts_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {self.scaler.get_scaled_font_size(12)}px; font-weight: bold; color: #ffffff;
                border: {table_border}px solid #404040; border-radius: {self.scaler.get_scaled_size(3)}px;
                margin-top: {self.scaler.get_scaled_size(10)}px; padding-top: {self.scaler.get_scaled_size(10)}px;
            }}
        """)
        conflicts_layout = QVBoxLayout()
        
        self.conflicts_info = QTextEdit()
        self.conflicts_info.setReadOnly(True)
        info_font = self.scaler.get_scaled_font_size(11)
        self.conflicts_info.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #ff8000;
                font-family: 'Courier New', monospace;
                font-size: {info_font}px;
                border: {table_border}px solid #404040;
            }}
        """)
        self.conflicts_info.setMinimumHeight(self.scaler.get_scaled_size(150))
        conflicts_layout.addWidget(self.conflicts_info)
        
        conflicts_group.setLayout(conflicts_layout)
        layout.addWidget(conflicts_group)
        
        return panel
    
    def _create_recommendations_tab(self) -> QWidget:
        """Create recommendations tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Recommended Settings Based on Detected Components")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.recommendations_info = QTextEdit()
        self.recommendations_info.setReadOnly(True)
        info_font = self.scaler.get_scaled_font_size(11)
        info_border = self.scaler.get_scaled_size(1)
        self.recommendations_info.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: {info_font}px;
                border: {info_border}px solid #404040;
            }}
        """)
        self.recommendations_info.setMinimumHeight(self.scaler.get_scaled_size(400))
        layout.addWidget(self.recommendations_info)
        
        return panel
    
    def _start_auto_detection(self) -> None:
        """Start automatic detection on initialization."""
        # Run detection after a short delay to allow UI to initialize
        QTimer.singleShot(1000, self._run_detection)
    
    def _run_detection(self) -> None:
        """Run comprehensive auto-detection."""
        if not self.detector:
            return
        
        self.progress_bar.setValue(0)
        self.detect_btn.setEnabled(False)
        
        # Simulate progress (in real implementation, this would be async)
        def update_progress():
            for i in range(0, 101, 10):
                self.progress_bar.setValue(i)
                QTimer.singleShot(100 * (i // 10), lambda v=i: self.progress_bar.setValue(v))
        
        # Run detection (this would ideally be in a thread)
        try:
            # Get current telemetry if available
            telemetry = getattr(self, '_last_telemetry', {})
            self.results = self.detector.detect_all(telemetry)
            self._update_displays()
            self.apply_btn.setEnabled(True)
            self.progress_bar.setValue(100)
        except Exception as e:
            print(f"Auto-detection error: {e}")
        finally:
            self.detect_btn.setEnabled(True)
    
    def _update_displays(self) -> None:
        """Update all display tabs with detection results."""
        if not self.results:
            return
        
        # Update sensors table
        self.sensors_table.setRowCount(len(self.results.sensors))
        for row, sensor in enumerate(self.results.sensors):
            self.sensors_table.setItem(row, 0, QTableWidgetItem(sensor.name))
            self.sensors_table.setItem(row, 1, QTableWidgetItem(sensor.sensor_type))
            self.sensors_table.setItem(row, 2, QTableWidgetItem(str(sensor.min_value) if sensor.min_value else "N/A"))
            self.sensors_table.setItem(row, 3, QTableWidgetItem(str(sensor.max_value) if sensor.max_value else "N/A"))
            self.sensors_table.setItem(row, 4, QTableWidgetItem(sensor.unit or "N/A"))
            detected_item = QTableWidgetItem("Yes" if sensor.detected else "No")
            detected_item.setForeground(QBrush(QColor("#00ff00" if sensor.detected else "#ff0000")))
            self.sensors_table.setItem(row, 5, detected_item)
            self.sensors_table.setItem(row, 6, QTableWidgetItem(f"{sensor.confidence:.2f}"))
        
        # Update engine info
        engine_text = f"""
Engine Detection Results:
========================
Type: {self.results.engine.engine_type.value}
Cylinders: {self.results.engine.cylinder_count}
Displacement: {self.results.engine.displacement:.2f}L
Forced Induction: {self.results.engine.forced_induction.value}
Max RPM: {self.results.engine.max_rpm}
Redline: {self.results.engine.redline}
Confidence: {self.results.engine.confidence:.2f}
"""
        self.engine_info.setText(engine_text)
        
        # Update transmission info
        trans_text = f"""
Transmission Detection Results:
==============================
Type: {self.results.transmission.transmission_type.value}
Gear Count: {self.results.transmission.gear_count}
Gear Ratios: {', '.join([f'{r:.2f}' for r in self.results.transmission.gear_ratios]) if self.results.transmission.gear_ratios else 'N/A'}
Final Drive: {self.results.transmission.final_drive if self.results.transmission.final_drive else 'N/A'}
Confidence: {self.results.transmission.confidence:.2f}
"""
        self.transmission_info.setText(trans_text)
        
        # Update communication table
        self.communication_table.setRowCount(len(self.results.communication))
        for row, comm in enumerate(self.results.communication):
            self.communication_table.setItem(row, 0, QTableWidgetItem(comm.interface_type))
            self.communication_table.setItem(row, 1, QTableWidgetItem(comm.port or comm.device_id or "N/A"))
            speed = str(comm.can_speed or comm.baudrate or "N/A")
            self.communication_table.setItem(row, 2, QTableWidgetItem(speed))
            self.communication_table.setItem(row, 3, QTableWidgetItem(comm.description))
            status_item = QTableWidgetItem("Detected" if comm.detected else "Not Detected")
            status_item.setForeground(QBrush(QColor("#00ff00" if comm.detected else "#ff0000")))
            self.communication_table.setItem(row, 4, status_item)
        
        # Update ECU parameters
        params_text = f"""
ECU Parameters Detection:
=========================
Total Parameters: {self.results.ecu_parameters.parameter_count}

Available Parameters:
{chr(10).join(f'  - {p}' for p in self.results.ecu_parameters.available_parameters[:50])}
{'  ... (showing first 50)' if len(self.results.ecu_parameters.available_parameters) > 50 else ''}

Parameter Ranges (sample):
{chr(10).join(f'  {k}: {v[0]:.2f} - {v[1]:.2f}' for k, v in list(self.results.ecu_parameters.parameter_ranges.items())[:20])}
"""
        self.ecu_params_info.setText(params_text)
        
        # Update ECU detection table
        self.ecus_table.setRowCount(len(self.results.detected_ecus))
        for row, ecu in enumerate(self.results.detected_ecus):
            self.ecus_table.setItem(row, 0, QTableWidgetItem(ecu.ecu_id))
            self.ecus_table.setItem(row, 1, QTableWidgetItem(ecu.vendor.value.upper() if hasattr(ecu.vendor, 'value') else str(ecu.vendor)))
            ecu_type_str = ecu.ecu_type.value.upper() if hasattr(ecu.ecu_type, 'value') else str(ecu.ecu_type)
            self.ecus_table.setItem(row, 2, QTableWidgetItem(ecu_type_str))
            
            primary_item = QTableWidgetItem("Yes" if ecu.is_primary else "No")
            primary_item.setForeground(QBrush(QColor("#00ff00" if ecu.is_primary else "#808080")))
            self.ecus_table.setItem(row, 3, primary_item)
            
            can_ids_str = ", ".join([f"0x{cid:X}" for cid in list(ecu.can_ids)[:5]])
            if len(ecu.can_ids) > 5:
                can_ids_str += "..."
            self.ecus_table.setItem(row, 4, QTableWidgetItem(can_ids_str))
            self.ecus_table.setItem(row, 5, QTableWidgetItem(f"{ecu.message_rate:.1f} msg/s"))
            
            conflicts_str = ", ".join([c.value if hasattr(c, 'value') else str(c) for c in ecu.conflicts[:3]])
            if len(ecu.conflicts) > 3:
                conflicts_str += "..."
            conflicts_item = QTableWidgetItem(conflicts_str if conflicts_str else "None")
            if ecu.conflicts:
                conflicts_item.setForeground(QBrush(QColor("#ff0000")))
            else:
                conflicts_item.setForeground(QBrush(QColor("#00ff00")))
            self.ecus_table.setItem(row, 6, conflicts_item)
            
            status_item = QTableWidgetItem("Active" if ecu.is_active else "Inactive")
            status_item.setForeground(QBrush(QColor("#00ff00" if ecu.is_active else "#808080")))
            self.ecus_table.setItem(row, 7, status_item)
        
        # Update conflicts info
        if self.results.ecu_conflicts:
            conflicts_text = "ECU Conflicts Summary:\n" + "=" * 50 + "\n\n"
            conflicts_text += f"Total Conflicts: {self.results.ecu_conflicts.get('total_conflicts', 0)}\n"
            conflicts_text += f"CAN ID Collisions: {self.results.ecu_conflicts.get('can_id_collisions', 0)}\n"
            conflicts_text += f"Piggyback Conflicts: {self.results.ecu_conflicts.get('piggyback_conflicts', 0)}\n"
            conflicts_text += f"Dual Control Issues: {self.results.ecu_conflicts.get('dual_control', 0)}\n\n"
            conflicts_text += f"Affected ECUs: {', '.join(self.results.ecu_conflicts.get('affected_ecus', []))}\n"
            
            # Get recommendations from multi-ECU detector
            if self.detector and self.detector.multi_ecu_detector:
                recommendations = self.detector.multi_ecu_detector.get_recommendations()
                if recommendations:
                    conflicts_text += "\nRecommendations:\n" + "-" * 50 + "\n"
                    for rec in recommendations:
                        conflicts_text += f"• {rec}\n"
        else:
            conflicts_text = "No ECU conflicts detected.\n"
        
        self.conflicts_info.setText(conflicts_text)
        
        # Update recommendations
        recommendations = self.detector.get_recommended_settings() if self.detector else {}
        rec_text = "Recommended Settings:\n" + "=" * 50 + "\n\n"
        for category, settings in recommendations.items():
            rec_text += f"{category.upper()}:\n"
            for key, value in settings.items():
                rec_text += f"  {key}: {value}\n"
            rec_text += "\n"
        
        # Add ECU recommendations
        if self.detector and self.detector.multi_ecu_detector:
            ecu_recs = self.detector.multi_ecu_detector.get_recommendations()
            if ecu_recs:
                rec_text += "\nECU Detection Recommendations:\n" + "-" * 50 + "\n"
                for rec in ecu_recs:
                    rec_text += f"• {rec}\n"
        
        self.recommendations_info.setText(rec_text)
    
    def _apply_settings(self) -> None:
        """Apply detected settings to system."""
        if not self.results:
            return
        
        # This would integrate with the actual configuration system
        print("Applying detected settings...")
        # TODO: Implement actual application of settings
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data for continuous detection."""
        self._last_telemetry = data
        
        # Optionally re-run detection periodically
        # For now, just store the data

