"""
Diesel Tuning Tab
UI for diesel-specific tuning features.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTabWidget, QGroupBox, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QComboBox, QLineEdit, QTextEdit,
    QProgressBar, QListWidget, QListWidgetItem,
)

from services.diesel_engine_detector import DieselEngineDetector, DieselEngineProfile
from services.diesel_auto_tuning import DieselAutoTuning, DieselTuningMode
from services.diesel_tune_database import DieselTuneDatabase, TuneCategory
from services.diesel_tuner_integration import DieselTunerIntegration, TunerFormat

LOGGER = logging.getLogger(__name__)


class DieselTuningTab(QWidget):
    """
    Diesel tuning tab with all diesel-specific features.
    
    Features:
    - Engine detection
    - Auto-tuning
    - Tune map database
    - Tuner integration
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize diesel tuning tab."""
        super().__init__(parent)
        
        self.detector = DieselEngineDetector()
        self.tune_database = DieselTuneDatabase()
        self.tuner_integration = DieselTunerIntegration()
        
        self.current_engine_profile: Optional[DieselEngineProfile] = None
        self.current_telemetry: Dict[str, Any] = {}
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("Diesel Tuning")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)
        layout.addWidget(title)
        
        # Sub-tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 8px 20px;
                margin-right: 2px;
                border: 1px solid #bdc3c7;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #3498db;
            }
        """)
        
        # Detection tab
        detection_tab = self._create_detection_tab()
        self.tabs.addTab(detection_tab, "Engine Detection")
        
        # Auto-tuning tab
        auto_tuning_tab = self._create_auto_tuning_tab()
        self.tabs.addTab(auto_tuning_tab, "Auto-Tuning")
        
        # Tune database tab
        database_tab = self._create_database_tab()
        self.tabs.addTab(database_tab, "Tune Database")
        
        # Tuner integration tab
        integration_tab = self._create_integration_tab()
        self.tabs.addTab(integration_tab, "Tuner Integration")
        
        # Graphing tab
        graphing_tab = self._create_graphing_tab()
        self.tabs.addTab(graphing_tab, "📊 Graphing")
        
        layout.addWidget(self.tabs)
    
    def _create_detection_tab(self) -> QWidget:
        """Create engine detection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Detection button
        detect_btn = QPushButton("🔍 Detect Diesel Engine")
        detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        detect_btn.clicked.connect(self._detect_engine)
        layout.addWidget(detect_btn)
        
        # Results
        self.detection_results = QTextEdit()
        self.detection_results.setReadOnly(True)
        self.detection_results.setMaximumHeight(300)
        self.detection_results.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                background-color: #ecf0f1;
            }
        """)
        layout.addWidget(self.detection_results)
        
        layout.addStretch()
        return tab
    
    def _create_auto_tuning_tab(self) -> QWidget:
        """Create auto-tuning tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Tuning mode selection
        mode_group = QGroupBox("Tuning Mode")
        mode_layout = QVBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Balanced",
            "Economy",
            "Performance",
            "Towing",
            "Racing",
            "Emissions",
        ])
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Optimize button
        optimize_btn = QPushButton("⚙️ Optimize Engine")
        optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        optimize_btn.clicked.connect(self._optimize_engine)
        layout.addWidget(optimize_btn)
        
        # Results
        self.tuning_results = QTextEdit()
        self.tuning_results.setReadOnly(True)
        self.tuning_results.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 10px;
                background-color: #ecf0f1;
            }
        """)
        layout.addWidget(self.tuning_results)
        
        return tab
    
    def _create_database_tab(self) -> QWidget:
        """Create tune database tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Search
        search_group = QGroupBox("Search Tunes")
        search_layout = QVBoxLayout()
        
        search_row = QHBoxLayout()
        self.search_make = QLineEdit()
        self.search_make.setPlaceholderText("Make (e.g., Ram)")
        search_row.addWidget(self.search_make)
        
        self.search_model = QLineEdit()
        self.search_model.setPlaceholderText("Model (e.g., 2500)")
        search_row.addWidget(self.search_model)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._search_tunes)
        search_row.addWidget(search_btn)
        
        search_layout.addLayout(search_row)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Tunes list
        self.tunes_list = QListWidget()
        self.tunes_list.itemDoubleClicked.connect(self._view_tune)
        layout.addWidget(self.tunes_list)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_tunes)
        layout.addWidget(refresh_btn)
        
        return tab
    
    def _create_integration_tab(self) -> QWidget:
        """Create tuner integration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Import section
        import_group = QGroupBox("Import Tune")
        import_layout = QVBoxLayout()
        
        import_btn = QPushButton("📥 Import Tune File")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        import_btn.clicked.connect(self._import_tune)
        import_layout.addWidget(import_btn)
        
        self.import_status = QLabel("Ready to import")
        import_layout.addWidget(self.import_status)
        
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # Supported formats
        formats_group = QGroupBox("Supported Formats")
        formats_layout = QVBoxLayout()
        
        formats_text = QLabel(
            "• EFI Live (.ctz, .ctd)\n"
            "• HPTuners (.hpt)\n"
            "• SCT (.sct)\n"
            "• Bully Dog (.bdx)\n"
            "• Edge (CSV)\n"
            "• Smarty (.smr)\n"
            "• DiabloSport (.trx)"
        )
        formats_text.setStyleSheet("color: #555;")
        formats_layout.addWidget(formats_text)
        
        formats_group.setLayout(formats_layout)
        layout.addWidget(formats_group)
        
        # Export section
        export_group = QGroupBox("Export Tune")
        export_layout = QVBoxLayout()
        
        export_btn = QPushButton("📤 Export Tune File")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        export_btn.clicked.connect(self._export_tune)
        export_layout.addWidget(export_btn)
        
        self.export_status = QLabel("Ready to export")
        export_layout.addWidget(self.export_status)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        return tab
    
    def _create_graphing_tab(self) -> QWidget:
        """Create graphing tab for data visualization."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Graph selection
        graph_group = QGroupBox("Graph Configuration")
        graph_layout = QVBoxLayout()
        
        # Channel selection
        channel_label = QLabel("Select Channels to Graph:")
        graph_layout.addWidget(channel_label)
        
        self.graph_channels = QListWidget()
        self.graph_channels.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.graph_channels.addItems([
            "RPM", "Boost Pressure", "EGT", "Injection Pressure",
            "Injection Timing", "Fuel Quantity", "AFR", "Coolant Temp",
            "Oil Pressure", "DPF Pressure", "EGR Position"
        ])
        graph_layout.addWidget(self.graph_channels)
        
        # Graph button
        graph_btn = QPushButton("📊 Create Graph")
        graph_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        graph_btn.clicked.connect(self._create_graph)
        graph_layout.addWidget(graph_btn)
        
        graph_group.setLayout(graph_layout)
        layout.addWidget(graph_group)
        
        # Graph display area
        try:
            from ui.advanced_log_graphing import AdvancedLogGraphingWidget
            self.graph_widget = AdvancedLogGraphingWidget()
            layout.addWidget(self.graph_widget, stretch=1)
        except ImportError:
            try:
                from ui.ecu_tuning_widgets import RealTimeGraph
                self.graph_widget = RealTimeGraph()
                layout.addWidget(self.graph_widget, stretch=1)
            except ImportError:
                graph_placeholder = QLabel("Graphing widget not available")
                graph_placeholder.setStyleSheet("color: #555; padding: 20px;")
                layout.addWidget(graph_placeholder, stretch=1)
                self.graph_widget = None
        
        return tab
    
    def _create_graph(self) -> None:
        """Create graph from selected channels."""
        if not self.graph_widget:
            QMessageBox.warning(self, "Graphing Unavailable", "Graphing widget not available.")
            return
        
        selected_items = self.graph_channels.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Channels", "Please select at least one channel to graph.")
            return
        
        channels = [item.text() for item in selected_items]
        
        # Update graph with current telemetry data
        if self.current_telemetry:
            # Convert channel names to telemetry keys
            channel_map = {
                "RPM": "rpm",
                "Boost Pressure": "boost_pressure",
                "EGT": "egt",
                "Injection Pressure": "rail_pressure",
                "Injection Timing": "injection_timing",
                "Fuel Quantity": "fuel_quantity",
                "AFR": "afr",
                "Coolant Temp": "coolant_temp",
                "Oil Pressure": "oil_pressure",
                "DPF Pressure": "dpf_pressure",
                "EGR Position": "egr_position",
            }
            
            graph_data = {}
            for channel in channels:
                key = channel_map.get(channel, channel.lower())
                if key in self.current_telemetry:
                    graph_data[channel] = self.current_telemetry[key]
            
            if graph_data:
                # Update graph widget
                if hasattr(self.graph_widget, 'add_data'):
                    for channel, value in graph_data.items():
                        self.graph_widget.add_data(channel, value)
                elif hasattr(self.graph_widget, 'update_data'):
                    self.graph_widget.update_data(**graph_data)
    
    def _export_tune(self) -> None:
        """Export tune file."""
        if not self.current_engine_profile:
            QMessageBox.warning(self, "No Engine", "Please detect engine first.")
            return
        
        # Ask for format
        formats = ["Edge CSV", "JSON"]
        format_choice, ok = QMessageBox.getItem(
            self,
            "Export Format",
            "Select export format:",
            formats,
            0,
            False,
        )
        
        if not ok:
            return
        
        # Ask for location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Tune",
            f"diesel_tune_{self.current_engine_profile.make}_{self.current_engine_profile.model}",
            f"{format_choice} Files (*.{format_choice.lower().replace(' ', '_')})",
        )
        
        if not file_path:
            return
        
        # Export based on format
        if format_choice == "Edge CSV":
            from services.diesel_tuner_integration import TunerFormat
            # Create a temporary tune for export
            from services.diesel_tune_database import DieselTuneMap, TuneCategory, TuneSource
            tune = DieselTuneMap(
                tune_id="export_tune",
                name="Exported Tune",
                category=TuneCategory.PERFORMANCE,
                source=TuneSource.CUSTOM,
                engine_profile=self.current_engine_profile,
            )
            success = self.tuner_integration.export_tune(tune, file_path, TunerFormat.EDGE_CSV)
        else:
            # JSON export
            import json
            export_data = {
                "engine_profile": {
                    "make": self.current_engine_profile.make,
                    "model": self.current_engine_profile.model,
                    "year": self.current_engine_profile.year,
                    "engine_type": self.current_engine_profile.engine_type.value,
                },
                "telemetry": self.current_telemetry,
            }
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            success = True
        
        if success:
            self.export_status.setText(f"Exported to: {file_path}")
            QMessageBox.information(self, "Export Success", f"Tune exported to:\n{file_path}")
        else:
            self.export_status.setText("Export failed")
            QMessageBox.warning(self, "Export Failed", "Failed to export tune.")
    
    def set_telemetry_data(self, telemetry: Dict[str, Any]) -> None:
        """Set current telemetry data."""
        self.current_telemetry = telemetry
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update telemetry data (compatible with main container)."""
        # Convert float values to Any for compatibility
        telemetry_dict = {k: float(v) for k, v in data.items()}
        self.set_telemetry_data(telemetry_dict)
    
    def _detect_engine(self) -> None:
        """Detect diesel engine."""
        if not self.current_telemetry:
            QMessageBox.warning(self, "No Data", "No telemetry data available.")
            return
        
        result = self.detector.detect_engine(self.current_telemetry)
        
        if result.is_diesel:
            self.current_engine_profile = result.engine_profile
            
            info = f"""Diesel Engine Detected!

Confidence: {result.confidence * 100:.0f}%
Engine Type: {result.engine_profile.engine_type.value}
Make: {result.engine_profile.make}
Model: {result.engine_profile.model}
Year: {result.engine_profile.year}
Displacement: {result.engine_profile.displacement}L
Cylinders: {result.engine_profile.cylinders}
Injection System: {result.engine_profile.injection_system}
Turbo Type: {result.engine_profile.turbo_type}

Detected Systems:
"""
            for system in result.detected_systems:
                info += f"  • {system.value.upper()}\n"
            
            info += f"\nReasoning: {result.reasoning}"
        else:
            info = f"Not detected as diesel engine.\nConfidence: {result.confidence * 100:.0f}%\n{result.reasoning}"
        
        self.detection_results.setPlainText(info)
    
    def _optimize_engine(self) -> None:
        """Optimize engine."""
        if not self.current_engine_profile:
            QMessageBox.warning(self, "No Engine", "Please detect engine first.")
            return
        
        if not self.current_telemetry:
            QMessageBox.warning(self, "No Data", "No telemetry data available.")
            return
        
        # Get tuning mode
        mode_text = self.mode_combo.currentText()
        mode_map = {
            "Balanced": DieselTuningMode.BALANCED,
            "Economy": DieselTuningMode.ECONOMY,
            "Performance": DieselTuningMode.PERFORMANCE,
            "Towing": DieselTuningMode.TOWING,
            "Racing": DieselTuningMode.RACING,
            "Emissions": DieselTuningMode.EMISSIONS,
        }
        mode = mode_map.get(mode_text, DieselTuningMode.BALANCED)
        
        # Create auto-tuning engine
        auto_tuning = DieselAutoTuning(self.current_engine_profile, mode)
        
        # Get current parameters (simplified - would get from ECU)
        current_params = {
            "injection_timing": self.current_telemetry.get("injection_timing", 0),
            "injection_pressure": self.current_telemetry.get("rail_pressure", 0),
            "boost_pressure": self.current_telemetry.get("boost_pressure", 0),
        }
        
        # Optimize
        recommendation = auto_tuning.analyze_and_optimize(
            self.current_telemetry,
            current_params,
        )
        
        # Display results
        results_text = f"""Optimization Results

Tuning Mode: {mode_text}
Confidence: {recommendation.confidence * 100:.0f}%

Expected Improvements:
"""
        if recommendation.expected_power_gain:
            results_text += f"  Power: +{recommendation.expected_power_gain:.1f} HP\n"
        if recommendation.expected_torque_gain:
            results_text += f"  Torque: +{recommendation.expected_torque_gain:.1f} lb-ft\n"
        if recommendation.expected_efficiency_gain:
            results_text += f"  Efficiency: +{recommendation.expected_efficiency_gain:.1f}%\n"
        
        results_text += f"\nRecommendations ({len(recommendation.recommendations)}):\n"
        for rec in recommendation.recommendations:
            results_text += f"\n{rec.parameter_name}:\n"
            results_text += f"  Current: {rec.current_value:.2f}\n"
            results_text += f"  Optimized: {rec.optimized_value:.2f}\n"
            results_text += f"  Improvement: {rec.improvement_estimate:.1f}%\n"
            results_text += f"  {rec.reasoning}\n"
        
        self.tuning_results.setPlainText(results_text)
    
    def _search_tunes(self) -> None:
        """Search tunes."""
        make = self.search_make.text() or None
        model = self.search_model.text() or None
        
        tunes = self.tune_database.search_tunes(make=make, model=model)
        
        self.tunes_list.clear()
        for tune in tunes:
            item = QListWidgetItem(f"{tune.name} - {tune.engine_profile.make} {tune.engine_profile.model}")
            item.setData(Qt.ItemDataRole.UserRole, tune.tune_id)
            self.tunes_list.addItem(item)
    
    def _view_tune(self, item: QListWidgetItem) -> None:
        """View tune details."""
        tune_id = item.data(Qt.ItemDataRole.UserRole)
        tune = self.tune_database.get_tune(tune_id)
        
        if tune:
            info = f"""Tune: {tune.name}
Category: {tune.category.value}
Source: {tune.source.value}
Engine: {tune.engine_profile.make} {tune.engine_profile.model} {tune.engine_profile.year}
Description: {tune.description}
"""
            if tune.power_hp:
                info += f"Power: {tune.power_hp} HP\n"
            if tune.torque_lbft:
                info += f"Torque: {tune.torque_lbft} lb-ft\n"
            
            QMessageBox.information(self, "Tune Details", info)
    
    def _refresh_tunes(self) -> None:
        """Refresh tunes list."""
        self._search_tunes()
    
    def _import_tune(self) -> None:
        """Import tune file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Tune File",
            "",
            "All Supported (*.ctz *.ctd *.hpt *.sct *.bdx *.csv *.smr *.trx);;"
            "EFI Live (*.ctz *.ctd);;HPTuners (*.hpt);;SCT (*.sct);;"
            "Bully Dog (*.bdx);;Edge (*.csv);;Smarty (*.smr);;DiabloSport (*.trx);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        self.import_status.setText("Importing...")
        
        tune = self.tune_database.import_from_file(file_path)
        
        if tune:
            self.import_status.setText(f"Imported: {tune.name}")
            QMessageBox.information(self, "Import Success", f"Successfully imported tune: {tune.name}")
            self._refresh_tunes()
        else:
            self.import_status.setText("Import failed")
            QMessageBox.warning(self, "Import Failed", "Failed to import tune file.")

