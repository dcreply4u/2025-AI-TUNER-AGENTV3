"""
Session Management Tab
Named sessions with metadata, comparison tools, and export/import
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
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
    QLineEdit,
    QTextEdit,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QCheckBox,
    QDoubleSpinBox,
    QDateEdit,
    QTimeEdit,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_theme, RacingColor

LOGGER = logging.getLogger(__name__)

try:
    from services.session_manager import SessionManager, SessionMetadata, SessionComparison
except ImportError:
    SessionManager = None
    SessionMetadata = None
    SessionComparison = None


class SessionCreateDialog(QDialog):
    """Dialog for creating a new session."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create New Session")
        self.resize(500, 400)
        
        theme = get_racing_theme()
        self.setStyleSheet(f"background-color: {theme.bg_primary}; color: {theme.text_primary};")
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Session name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter session name...")
        self.name_edit.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px;")
        form.addRow("Session Name:", self.name_edit)
        
        # Track name
        self.track_edit = QLineEdit()
        self.track_edit.setPlaceholderText("Enter track name...")
        self.track_edit.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px;")
        form.addRow("Track Name:", self.track_edit)
        
        # Weather
        self.weather_combo = QComboBox()
        self.weather_combo.addItems(["Sunny", "Cloudy", "Rain", "Snow", "Other"])
        self.weather_combo.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary};")
        form.addRow("Weather:", self.weather_combo)
        
        # Temperature
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(-40, 150)
        self.temp_spin.setSuffix(" °F")
        self.temp_spin.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary};")
        form.addRow("Temperature:", self.temp_spin)
        
        # Humidity
        self.humidity_spin = QDoubleSpinBox()
        self.humidity_spin.setRange(0, 100)
        self.humidity_spin.setSuffix(" %")
        self.humidity_spin.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary};")
        form.addRow("Humidity:", self.humidity_spin)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Enter session notes...")
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary};")
        form.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_session_data(self) -> Dict:
        """Get session data from dialog."""
        return {
            "name": self.name_edit.text() or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "track_name": self.track_edit.text() or None,
            "weather": self.weather_combo.currentText() if self.weather_combo.currentText() != "Other" else None,
            "temperature": self.temp_spin.value() if self.temp_spin.value() != 0 else None,
            "humidity": self.humidity_spin.value() if self.humidity_spin.value() != 0 else None,
            "notes": self.notes_edit.toPlainText() or None,
        }


class SessionManagementTab(QWidget):
    """Session Management tab."""
    
    session_created = Signal(str)  # Emits session_id
    session_selected = Signal(str)  # Emits session_id
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        self.session_manager: Optional[SessionManager] = None
        
        # Initialize session manager
        if SessionManager:
            try:
                self.session_manager = SessionManager()
            except Exception as e:
                LOGGER.error(f"Failed to initialize SessionManager: {e}")
        
        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._refresh_sessions)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        self.setup_ui()
        self._refresh_sessions()
        
    def setup_ui(self) -> None:
        """Setup session management tab UI."""
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
        
        # Left: Session list
        left_panel = self._create_session_list_panel()
        splitter.addWidget(left_panel)
        
        # Right: Session details and comparison
        right_panel = self._create_details_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter, stretch=1)
        
    def _create_control_bar(self) -> QWidget:
        """Create control bar."""
        bar = QWidget()
        theme = get_racing_theme()
        padding = get_scaled_size(5)
        bar.setStyleSheet(f"background-color: {theme.bg_secondary}; padding: {padding}px; border: 1px solid {theme.border_default};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(get_scaled_size(10), padding, get_scaled_size(10), padding)
        
        title = QLabel("Session Management")
        title_font = get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: {theme.text_primary};")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Create session button
        self.create_btn = QPushButton("Create Session")
        btn_font = get_scaled_font_size(11)
        self.create_btn.setStyleSheet(f"background-color: {theme.status_optimal}; color: #000000; padding: 5px 10px; font-weight: bold; font-size: {btn_font}px;")
        self.create_btn.clicked.connect(self._create_session)
        layout.addWidget(self.create_btn)
        
        # Export button
        self.export_btn = QPushButton("Export")
        self.export_btn.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px 10px; font-size: {btn_font}px;")
        self.export_btn.clicked.connect(self._export_session)
        layout.addWidget(self.export_btn)
        
        # Import button
        self.import_btn = QPushButton("Import")
        self.import_btn.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px 10px; font-size: {btn_font}px;")
        self.import_btn.clicked.connect(self._import_session)
        layout.addWidget(self.import_btn)
        
        # Delete button
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet(f"background-color: {theme.status_critical}; color: #ffffff; padding: 5px 10px; font-size: {btn_font}px;")
        self.delete_btn.clicked.connect(self._delete_session)
        layout.addWidget(self.delete_btn)
        
        return bar
        
    def _create_session_list_panel(self) -> QWidget:
        """Create session list panel."""
        panel = QWidget()
        theme = get_racing_theme()
        panel.setStyleSheet(f"background-color: {theme.bg_secondary}; border: 1px solid {theme.border_default};")
        panel.setMaximumWidth(get_scaled_size(400))
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        layout.setSpacing(get_scaled_size(10))
        
        # Filter/search
        filter_group = QGroupBox("Filter")
        filter_layout = QVBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search sessions...")
        self.search_edit.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary}; padding: 5px;")
        self.search_edit.textChanged.connect(self._filter_sessions)
        filter_layout.addWidget(self.search_edit)
        
        self.track_filter = QComboBox()
        self.track_filter.addItem("All Tracks")
        self.track_filter.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary};")
        self.track_filter.currentTextChanged.connect(self._filter_sessions)
        filter_layout.addWidget(self.track_filter)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Session list
        sessions_group = QGroupBox("Sessions")
        sessions_layout = QVBoxLayout()
        
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(4)
        self.session_table.setHorizontalHeaderLabels(["Name", "Track", "Date", "Best Lap"])
        self.session_table.horizontalHeader().setStretchLastSection(True)
        self.session_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.session_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.session_table.itemSelectionChanged.connect(self._on_session_selected)
        self.session_table.setStyleSheet(f"color: {theme.text_primary}; background-color: {theme.bg_tertiary};")
        self.session_table.setAlternatingRowColors(True)
        sessions_layout.addWidget(self.session_table)
        
        sessions_group.setLayout(sessions_layout)
        layout.addWidget(sessions_group)
        
        return panel
        
    def _create_details_panel(self) -> QWidget:
        """Create session details panel."""
        panel = QWidget()
        theme = get_racing_theme()
        panel.setStyleSheet(f"background-color: {theme.bg_secondary}; border: 1px solid {theme.border_default};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(get_scaled_size(10), get_scaled_size(10), get_scaled_size(10), get_scaled_size(10))
        layout.setSpacing(get_scaled_size(15))
        
        # Session details
        details_group = QGroupBox("Session Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary};")
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Comparison
        compare_group = QGroupBox("Compare Sessions")
        compare_layout = QVBoxLayout()
        
        compare_layout.addWidget(QLabel("Select two sessions to compare:"))
        
        self.compare_session1 = QComboBox()
        self.compare_session1.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary};")
        compare_layout.addWidget(self.compare_session1)
        
        self.compare_session2 = QComboBox()
        self.compare_session2.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary};")
        compare_layout.addWidget(self.compare_session2)
        
        compare_btn = QPushButton("Compare")
        compare_btn.setStyleSheet(f"background-color: {theme.accent_neon_blue}; color: #000000; padding: 5px;")
        compare_btn.clicked.connect(self._compare_sessions)
        compare_layout.addWidget(compare_btn)
        
        self.comparison_text = QTextEdit()
        self.comparison_text.setReadOnly(True)
        self.comparison_text.setStyleSheet(f"background-color: {theme.bg_tertiary}; color: {theme.text_primary};")
        compare_layout.addWidget(self.comparison_text)
        
        compare_group.setLayout(compare_layout)
        layout.addWidget(compare_group)
        
        layout.addStretch()
        return panel
        
    def _create_session(self) -> None:
        """Create a new session."""
        if not self.session_manager:
            QMessageBox.warning(self, "Error", "Session manager not available")
            return
            
        dialog = SessionCreateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_session_data()
            session = self.session_manager.create_session(**data)
            self.session_created.emit(session.session_id)
            self._refresh_sessions()
            
    def _export_session(self) -> None:
        """Export selected session."""
        if not self.session_manager:
            return
            
        selected = self.session_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a session to export")
            return
            
        row = selected[0].row()
        session_id = self.session_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if not session_id:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Session",
            f"session_{session_id}.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.session_manager.export_session(session_id, Path(file_path))
                QMessageBox.information(self, "Success", f"Session exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export session: {e}")
                
    def _import_session(self) -> None:
        """Import a session."""
        if not self.session_manager:
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Session",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                session = self.session_manager.import_session(Path(file_path))
                QMessageBox.information(self, "Success", f"Session '{session.name}' imported")
                self._refresh_sessions()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import session: {e}")
                
    def _delete_session(self) -> None:
        """Delete selected session."""
        if not self.session_manager:
            return
            
        selected = self.session_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a session to delete")
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            row = selected[0].row()
            session_id = self.session_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            if session_id:
                self.session_manager.delete_session(session_id)
                self._refresh_sessions()
                
    def _filter_sessions(self) -> None:
        """Filter sessions by search and track."""
        self._refresh_sessions()
        
    def _refresh_sessions(self) -> None:
        """Refresh session list."""
        if not self.session_manager:
            return
            
        # Get filter criteria
        search_text = self.search_edit.text().lower()
        track_filter = self.track_filter.currentText()
        
        # Get sessions
        sessions = self.session_manager.list_sessions()
        
        # Filter
        if track_filter != "All Tracks":
            sessions = [s for s in sessions if s.track_name == track_filter]
            
        if search_text:
            sessions = [s for s in sessions if search_text in s.name.lower() or 
                       (s.track_name and search_text in s.track_name.lower())]
        
        # Update track filter
        tracks = set(s.track_name for s in self.session_manager.list_sessions() if s.track_name)
        current_track = self.track_filter.currentText()
        self.track_filter.clear()
        self.track_filter.addItem("All Tracks")
        for track in sorted(tracks):
            self.track_filter.addItem(track)
        if current_track in [self.track_filter.itemText(i) for i in range(self.track_filter.count())]:
            self.track_filter.setCurrentText(current_track)
        
        # Update table
        self.session_table.setRowCount(len(sessions))
        for i, session in enumerate(sessions):
            name_item = QTableWidgetItem(session.name)
            name_item.setData(Qt.ItemDataRole.UserRole, session.session_id)
            self.session_table.setItem(i, 0, name_item)
            
            track_item = QTableWidgetItem(session.track_name or "")
            self.session_table.setItem(i, 1, track_item)
            
            date_str = datetime.fromtimestamp(session.start_time).strftime("%Y-%m-%d %H:%M")
            date_item = QTableWidgetItem(date_str)
            self.session_table.setItem(i, 2, date_item)
            
            if session.best_lap_time:
                minutes = int(session.best_lap_time // 60)
                seconds = session.best_lap_time % 60
                lap_str = f"{minutes:02d}:{seconds:05.2f}"
            else:
                lap_str = "--:--.---"
            lap_item = QTableWidgetItem(lap_str)
            self.session_table.setItem(i, 3, lap_item)
        
        # Update comparison combos
        self.compare_session1.clear()
        self.compare_session2.clear()
        for session in sessions:
            self.compare_session1.addItem(session.name, session.session_id)
            self.compare_session2.addItem(session.name, session.session_id)
            
    def _on_session_selected(self) -> None:
        """Handle session selection."""
        selected = self.session_table.selectedItems()
        if not selected or not self.session_manager:
            self.details_text.clear()
            return
            
        row = selected[0].row()
        session_id = self.session_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if not session_id:
            return
            
        session = self.session_manager.get_session(session_id)
        if not session:
            return
            
        # Update details
        details = []
        details.append(f"Name: {session.name}")
        details.append(f"Track: {session.track_name or 'N/A'}")
        details.append(f"Start: {datetime.fromtimestamp(session.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        if session.end_time:
            details.append(f"End: {datetime.fromtimestamp(session.end_time).strftime('%Y-%m-%d %H:%M:%S')}")
            details.append(f"Duration: {session.duration:.1f} seconds" if session.duration else "Duration: N/A")
        details.append(f"Weather: {session.weather or 'N/A'}")
        details.append(f"Temperature: {session.temperature}°F" if session.temperature else "Temperature: N/A")
        details.append(f"Humidity: {session.humidity}%" if session.humidity else "Humidity: N/A")
        details.append(f"Laps: {session.lap_count}")
        if session.best_lap_time:
            minutes = int(session.best_lap_time // 60)
            seconds = session.best_lap_time % 60
            details.append(f"Best Lap: {minutes:02d}:{seconds:05.2f}")
        details.append(f"Max Speed: {session.max_speed:.1f} mph" if session.max_speed else "Max Speed: N/A")
        details.append(f"Avg Speed: {session.avg_speed:.1f} mph" if session.avg_speed else "Avg Speed: N/A")
        if session.notes:
            details.append(f"\nNotes:\n{session.notes}")
        
        self.details_text.setText("\n".join(details))
        self.session_selected.emit(session_id)
        
    def _compare_sessions(self) -> None:
        """Compare two sessions."""
        if not self.session_manager:
            return
            
        session_id1 = self.compare_session1.currentData()
        session_id2 = self.compare_session2.currentData()
        
        if not session_id1 or not session_id2 or session_id1 == session_id2:
            QMessageBox.warning(self, "Invalid Selection", "Please select two different sessions")
            return
            
        comparison = self.session_manager.compare_sessions(session_id1, session_id2)
        if not comparison:
            return
            
        # Format comparison
        comp_text = []
        comp_text.append("=== Session Comparison ===\n")
        comp_text.append(f"Session 1: {comparison.session1.name}")
        comp_text.append(f"Session 2: {comparison.session2.name}\n")
        
        if comparison.lap_time_diff is not None:
            diff_str = f"{comparison.lap_time_diff:+.3f} seconds"
            comp_text.append(f"Lap Time Difference: {diff_str}")
        
        if comparison.speed_diff is not None:
            diff_str = f"{comparison.speed_diff:+.1f} mph"
            comp_text.append(f"Speed Difference: {diff_str}")
        
        if comparison.distance_diff is not None:
            diff_str = f"{comparison.distance_diff:+.2f} miles"
            comp_text.append(f"Distance Difference: {diff_str}")
        
        comp_text.append("\n=== Detailed Differences ===")
        for key, value in comparison.differences.items():
            comp_text.append(f"{key}: {value:+.2f}")
        
        self.comparison_text.setText("\n".join(comp_text))


__all__ = ["SessionManagementTab", "SessionCreateDialog"]







