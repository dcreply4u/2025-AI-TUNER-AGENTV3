"""
Tune/Map Database UI Tab

Provides interface for browsing, searching, and loading tunes from the database.
"""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QGroupBox,
    QTextEdit,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QCheckBox,
    QScrollArea,
)

from ui.ui_scaling import get_scaled_size, get_scaled_font_size

LOGGER = logging.getLogger(__name__)

try:
    from services.tune_map_database import (
        TuneMapDatabase,
        TuneMap,
        VehicleIdentifier,
        TuneType,
        MapCategory,
    )
    TUNE_DB_AVAILABLE = True
except ImportError:
    TUNE_DB_AVAILABLE = False
    LOGGER.warning("Tune database service not available")


class TuneDetailsDialog(QDialog):
    """Dialog showing detailed tune information."""
    
    def __init__(self, tune: TuneMap, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tune = tune
        self.setWindowTitle(f"Tune Details: {tune.name}")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic info
        info_group = QGroupBox("Tune Information")
        info_layout = QFormLayout()
        info_layout.addRow("Name:", QLabel(tune.name))
        info_layout.addRow("Type:", QLabel(tune.tune_type.value.replace("_", " ").title()))
        info_layout.addRow("ECU Type:", QLabel(tune.ecu_type))
        info_layout.addRow("Version:", QLabel(tune.version))
        info_layout.addRow("Created By:", QLabel(tune.created_by))
        info_group.setLayout(info_layout)
        scroll_layout.addWidget(info_group)
        
        # Vehicle info
        vehicle_group = QGroupBox("Vehicle")
        vehicle_layout = QFormLayout()
        vehicle_layout.addRow("Make:", QLabel(tune.vehicle.make))
        vehicle_layout.addRow("Model:", QLabel(tune.vehicle.model))
        vehicle_layout.addRow("Year:", QLabel(str(tune.vehicle.year)))
        if tune.vehicle.engine_code:
            vehicle_layout.addRow("Engine Code:", QLabel(tune.vehicle.engine_code))
        vehicle_layout.addRow("Fuel Type:", QLabel(tune.vehicle.fuel_type))
        vehicle_group.setLayout(vehicle_layout)
        scroll_layout.addWidget(vehicle_group)
        
        # Description
        desc_label = QLabel("Description:")
        desc_label.setFont(QFont("", get_scaled_font_size(10), QFont.Bold))
        scroll_layout.addWidget(desc_label)
        desc_text = QTextEdit()
        desc_text.setPlainText(tune.description)
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(100)
        scroll_layout.addWidget(desc_text)
        
        # Hardware requirements
        if tune.hardware_requirements:
            hw_group = QGroupBox("Hardware Requirements")
            hw_layout = QVBoxLayout()
            for req in tune.hardware_requirements:
                req_text = f"{'[REQUIRED]' if req.required else '[RECOMMENDED]'} {req.component}"
                if req.description:
                    req_text += f": {req.description}"
                hw_label = QLabel(req_text)
                hw_layout.addWidget(hw_label)
            hw_group.setLayout(hw_layout)
            scroll_layout.addWidget(hw_group)
        
        # Performance gains
        if tune.performance_gains:
            perf_group = QGroupBox("Performance Gains")
            perf_layout = QFormLayout()
            if tune.performance_gains.hp_gain:
                perf_layout.addRow("HP Gain:", QLabel(f"+{tune.performance_gains.hp_gain} HP"))
            if tune.performance_gains.torque_gain:
                perf_layout.addRow("Torque Gain:", QLabel(f"+{tune.performance_gains.torque_gain} lb-ft"))
            if tune.performance_gains.notes:
                perf_layout.addRow("Notes:", QLabel(tune.performance_gains.notes))
            perf_group.setLayout(perf_layout)
            scroll_layout.addWidget(perf_group)
        
        # Maps included
        maps_group = QGroupBox("Maps Included")
        maps_layout = QVBoxLayout()
        for map_item in tune.maps:
            map_text = f"{map_item.category.value.replace('_', ' ').title()}: {map_item.name}"
            if map_item.description:
                map_text += f" - {map_item.description}"
            map_label = QLabel(map_text)
            maps_layout.addWidget(map_label)
        maps_group.setLayout(maps_layout)
        scroll_layout.addWidget(maps_group)
        
        # Safety warnings
        if tune.safety_warnings:
            safety_group = QGroupBox("Safety Warnings")
            safety_layout = QVBoxLayout()
            for warning in tune.safety_warnings:
                warning_label = QLabel(f"⚠ {warning}")
                warning_label.setStyleSheet("color: orange; font-weight: bold;")
                safety_layout.addWidget(warning_label)
            safety_group.setLayout(safety_layout)
            scroll_layout.addWidget(safety_group)
        
        # Notes
        if tune.tuning_notes or tune.installation_notes:
            notes_group = QGroupBox("Notes")
            notes_layout = QVBoxLayout()
            if tune.tuning_notes:
                notes_label = QLabel("Tuning Notes:")
                notes_label.setFont(QFont("", get_scaled_font_size(10), QFont.Bold))
                notes_layout.addWidget(notes_label)
                tuning_notes = QTextEdit()
                tuning_notes.setPlainText(tune.tuning_notes)
                tuning_notes.setReadOnly(True)
                tuning_notes.setMaximumHeight(80)
                notes_layout.addWidget(tuning_notes)
            if tune.installation_notes:
                install_label = QLabel("Installation Notes:")
                install_label.setFont(QFont("", get_scaled_font_size(10), QFont.Bold))
                notes_layout.addWidget(install_label)
                install_notes = QTextEdit()
                install_notes.setPlainText(tune.installation_notes)
                install_notes.setReadOnly(True)
                install_notes.setMaximumHeight(80)
                notes_layout.addWidget(install_notes)
            notes_group.setLayout(notes_layout)
            scroll_layout.addWidget(notes_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class TuneDatabaseTab(QWidget):
    """Tab for browsing and managing tune/map database."""
    
    tune_selected = Signal(str)  # Emitted when tune is selected for loading
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        if not TUNE_DB_AVAILABLE:
            self._create_unavailable_widget()
            return
        
        self.tune_db = TuneMapDatabase()
        self.current_tunes: List[TuneMap] = []
        
        self._create_ui()
        self._refresh_tunes()
    
    def _create_unavailable_widget(self):
        """Create widget when database is unavailable."""
        layout = QVBoxLayout(self)
        label = QLabel("Tune Database service is not available.")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
    
    def _create_ui(self):
        """Create the UI."""
        layout = QVBoxLayout(self)
        
        # Search/filter section
        search_group = QGroupBox("Search & Filter")
        search_layout = QVBoxLayout()
        
        # Search row
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tune name, description, tags...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.search_input)
        search_layout.addLayout(search_row)
        
        # Filter row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Make:"))
        self.make_combo = QComboBox()
        self.make_combo.setEditable(True)
        self.make_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.make_combo)
        
        filter_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.model_combo)
        
        filter_row.addWidget(QLabel("Year:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1900, 2100)
        self.year_spin.setValue(2020)
        self.year_spin.setSpecialValueText("Any")
        self.year_spin.valueChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.year_spin)
        
        filter_row.addWidget(QLabel("ECU Type:"))
        self.ecu_combo = QComboBox()
        self.ecu_combo.setEditable(True)
        self.ecu_combo.addItems(["Any", "Holley", "Haltech", "AEM", "MoTeC", "MegaSquirt", "Bosch", "Denso"])
        self.ecu_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.ecu_combo)
        
        filter_row.addWidget(QLabel("Tune Type:"))
        self.tune_type_combo = QComboBox()
        self.tune_type_combo.addItems(["Any", "Base Map", "Performance", "Economy", "Race", "Custom", "Community"])
        self.tune_type_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.tune_type_combo)
        
        filter_row.addStretch()
        search_layout.addLayout(filter_row)
        
        # Action buttons
        action_row = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_tunes)
        action_row.addWidget(self.refresh_btn)
        
        self.create_from_current_btn = QPushButton("Create Tune from Current ECU")
        self.create_from_current_btn.clicked.connect(self._create_from_current)
        action_row.addWidget(self.create_from_current_btn)
        
        action_row.addStretch()
        search_layout.addLayout(action_row)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Tunes table
        table_group = QGroupBox("Available Tunes")
        table_layout = QVBoxLayout()
        
        self.tunes_table = QTableWidget()
        self.tunes_table.setColumnCount(7)
        self.tunes_table.setHorizontalHeaderLabels([
            "Name", "Vehicle", "ECU Type", "Type", "HP Gain", "Rating", "Actions"
        ])
        self.tunes_table.horizontalHeader().setStretchLastSection(True)
        self.tunes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tunes_table.setSelectionMode(QTableWidget.SingleSelection)
        self.tunes_table.itemDoubleClicked.connect(self._on_tune_double_clicked)
        table_layout.addWidget(self.tunes_table)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Action buttons
        action_group = QGroupBox("Actions")
        action_layout = QHBoxLayout()
        
        self.view_details_btn = QPushButton("View Details")
        self.view_details_btn.clicked.connect(self._view_details)
        self.view_details_btn.setEnabled(False)
        action_layout.addWidget(self.view_details_btn)
        
        self.load_tune_btn = QPushButton("Load Tune")
        self.load_tune_btn.clicked.connect(self._load_tune)
        self.load_tune_btn.setEnabled(False)
        action_layout.addWidget(self.load_tune_btn)
        
        self.share_tune_btn = QPushButton("Share Tune")
        self.share_tune_btn.clicked.connect(self._share_tune)
        self.share_tune_btn.setEnabled(False)
        action_layout.addWidget(self.share_tune_btn)
        
        action_layout.addStretch()
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # Connect table selection
        self.tunes_table.selectionModel().selectionChanged.connect(self._on_selection_changed)
    
    def _refresh_tunes(self):
        """Refresh the tunes list."""
        # Get all tunes
        all_tunes = list(self.tune_db.tunes_index.values())
        
        # Update filter options
        makes = sorted(set(t.vehicle.make for t in all_tunes))
        self.make_combo.clear()
        self.make_combo.addItem("Any")
        self.make_combo.addItems(makes)
        
        models = sorted(set(t.vehicle.model for t in all_tunes))
        self.model_combo.clear()
        self.model_combo.addItem("Any")
        self.model_combo.addItems(models)
        
        # Apply filters
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply current filters and update table."""
        # Get filter values
        make = self.make_combo.currentText() if self.make_combo.currentText() != "Any" else None
        model = self.model_combo.currentText() if self.model_combo.currentText() != "Any" else None
        year = self.year_spin.value() if self.year_spin.value() > 1900 else None
        ecu_type = self.ecu_combo.currentText() if self.ecu_combo.currentText() != "Any" else None
        
        tune_type_str = self.tune_type_combo.currentText()
        tune_type = None
        if tune_type_str != "Any":
            try:
                tune_type = TuneType[tune_type_str.upper().replace(" ", "_")]
            except KeyError:
                pass
        
        # Search
        search_text = self.search_input.text().lower()
        
        # Search tunes
        self.current_tunes = self.tune_db.search_tunes(
            make=make,
            model=model,
            year=year,
            ecu_type=ecu_type,
            tune_type=tune_type,
        )
        
        # Filter by search text
        if search_text:
            filtered = []
            for tune in self.current_tunes:
                if (search_text in tune.name.lower() or
                    search_text in tune.description.lower() or
                    any(search_text in tag.lower() for tag in tune.tags)):
                    filtered.append(tune)
            self.current_tunes = filtered
        
        # Update table
        self._update_table()
    
    def _update_table(self):
        """Update the tunes table."""
        self.tunes_table.setRowCount(len(self.current_tunes))
        
        for row, tune in enumerate(self.current_tunes):
            # Name
            name_item = QTableWidgetItem(tune.name)
            name_item.setData(Qt.UserRole, tune.tune_id)
            self.tunes_table.setItem(row, 0, name_item)
            
            # Vehicle
            vehicle_str = f"{tune.vehicle.make} {tune.vehicle.model} {tune.vehicle.year}"
            if tune.vehicle.engine_code:
                vehicle_str += f" ({tune.vehicle.engine_code})"
            self.tunes_table.setItem(row, 1, QTableWidgetItem(vehicle_str))
            
            # ECU Type
            self.tunes_table.setItem(row, 2, QTableWidgetItem(tune.ecu_type))
            
            # Type
            type_str = tune.tune_type.value.replace("_", " ").title()
            self.tunes_table.setItem(row, 3, QTableWidgetItem(type_str))
            
            # HP Gain
            hp_gain = ""
            if tune.performance_gains and tune.performance_gains.hp_gain:
                hp_gain = f"+{tune.performance_gains.hp_gain} HP"
            self.tunes_table.setItem(row, 4, QTableWidgetItem(hp_gain))
            
            # Rating
            rating_str = ""
            if tune.rating:
                rating_str = f"{tune.rating:.1f} ({tune.rating_count})"
            self.tunes_table.setItem(row, 5, QTableWidgetItem(rating_str))
            
            # Actions (placeholder)
            self.tunes_table.setItem(row, 6, QTableWidgetItem(""))
        
        # Resize columns
        self.tunes_table.resizeColumnsToContents()
    
    def _on_search_changed(self):
        """Handle search text change."""
        self._apply_filters()
    
    def _on_filter_changed(self):
        """Handle filter change."""
        self._apply_filters()
    
    def _on_selection_changed(self):
        """Handle table selection change."""
        has_selection = len(self.tunes_table.selectedItems()) > 0
        self.view_details_btn.setEnabled(has_selection)
        self.load_tune_btn.setEnabled(has_selection)
        self.share_tune_btn.setEnabled(has_selection)
    
    def _on_tune_double_clicked(self, item: QTableWidgetItem):
        """Handle tune double-click."""
        self._view_details()
    
    def _get_selected_tune(self) -> Optional[TuneMap]:
        """Get currently selected tune."""
        selected = self.tunes_table.selectedItems()
        if not selected:
            return None
        
        tune_id = selected[0].data(Qt.UserRole)
        return self.tune_db.get_tune(tune_id) if tune_id else None
    
    def _view_details(self):
        """View tune details."""
        tune = self._get_selected_tune()
        if not tune:
            return
        
        dialog = TuneDetailsDialog(tune, self)
        dialog.exec()
    
    def _load_tune(self):
        """Load selected tune."""
        tune = self._get_selected_tune()
        if not tune:
            return
        
        # Confirm action
        reply = QMessageBox.question(
            self,
            "Load Tune",
            f"Load tune '{tune.name}'?\n\nThis will apply the tune to your ECU.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            self.tune_selected.emit(tune.tune_id)
            QMessageBox.information(self, "Tune Loaded", f"Tune '{tune.name}' has been loaded.")
    
    def _share_tune(self):
        """Share selected tune."""
        tune = self._get_selected_tune()
        if not tune:
            return
        
        share_id = self.tune_db.share_tune(tune.tune_id)
        if share_id:
            QMessageBox.information(
                self,
                "Tune Shared",
                f"Tune '{tune.name}' has been shared.\n\nShare ID: {share_id}",
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to share tune.")
    
    def _create_from_current(self):
        """Create tune from current ECU settings."""
        # This would need ECU control instance
        QMessageBox.information(
            self,
            "Create Tune",
            "This feature requires connection to ECU.\n\n"
            "Please connect to your ECU first, then use this feature to save your current tune.",
        )



