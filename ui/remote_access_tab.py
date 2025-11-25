"""
Remote Access Management Tab
UI for managing remote tuner access sessions.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional, Dict, Any

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QGroupBox, QLineEdit,
        QComboBox, QTextEdit, QMessageBox, QCheckBox, QSpinBox,
    )
    from PySide6.QtCore import Qt, QTimer, Signal, QObject
    from PySide6.QtGui import QFont, QClipboard, QApplication
except ImportError:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QGroupBox, QLineEdit,
        QComboBox, QTextEdit, QMessageBox, QCheckBox, QSpinBox,
    )
    from PyQt5.QtCore import Qt, QTimer, Signal as Signal, QObject
    from PyQt5.QtGui import QFont, QClipboard, QApplication

LOGGER = logging.getLogger(__name__)


class RemoteAccessTab(QWidget):
    """Tab for managing remote access sessions."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
        
        # Try to import remote access service
        self.remote_service = None
        try:
            from services.remote_access_service import RemoteAccessService, RemoteAccessConfig
            self.remote_service = RemoteAccessService(RemoteAccessConfig(enabled=True))
        except Exception as e:
            LOGGER.warning("Remote access service not available: %s", e)
    
    def setup_ui(self) -> None:
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Remote Access Management")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Configuration section
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()
        
        # Enable remote access
        self.enable_checkbox = QCheckBox("Enable Remote Access")
        self.enable_checkbox.setChecked(True)
        config_layout.addWidget(self.enable_checkbox)
        
        # Max sessions
        max_sessions_layout = QHBoxLayout()
        max_sessions_layout.addWidget(QLabel("Max Sessions:"))
        self.max_sessions_spin = QSpinBox()
        self.max_sessions_spin.setMinimum(1)
        self.max_sessions_spin.setMaximum(50)
        self.max_sessions_spin.setValue(10)
        max_sessions_layout.addWidget(self.max_sessions_spin)
        max_sessions_layout.addStretch()
        config_layout.addLayout(max_sessions_layout)
        
        # Session timeout
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Session Timeout (minutes):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setMinimum(5)
        self.timeout_spin.setMaximum(480)
        self.timeout_spin.setValue(60)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        config_layout.addLayout(timeout_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Create session section
        create_group = QGroupBox("Create New Session")
        create_layout = QVBoxLayout()
        
        # Client name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Client Name:"))
        self.client_name_input = QLineEdit()
        self.client_name_input.setPlaceholderText("e.g., Remote Tuner, John's Laptop")
        name_layout.addWidget(self.client_name_input)
        create_layout.addLayout(name_layout)
        
        # Access level
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Access Level:"))
        self.access_level_combo = QComboBox()
        self.access_level_combo.addItems([
            "View Only",
            "View & Annotate",
            "View & Control",
            "Full Access",
        ])
        level_layout.addWidget(self.access_level_combo)
        create_layout.addLayout(level_layout)
        
        # Create button
        self.create_btn = QPushButton("Create Session")
        self.create_btn.clicked.connect(self.create_session)
        create_layout.addWidget(self.create_btn)
        
        create_group.setLayout(create_layout)
        layout.addWidget(create_group)
        
        # Active sessions table
        sessions_group = QGroupBox("Active Sessions")
        sessions_layout = QVBoxLayout()
        
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(7)
        self.sessions_table.setHorizontalHeaderLabels([
            "Client Name",
            "Access Level",
            "IP Address",
            "Created",
            "Last Activity",
            "Status",
            "Actions",
        ])
        self.sessions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sessions_table.horizontalHeader().setStretchLastSection(True)
        sessions_layout.addWidget(self.sessions_table)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_sessions)
        refresh_layout.addWidget(self.refresh_btn)
        sessions_layout.addLayout(refresh_layout)
        
        sessions_group.setLayout(sessions_layout)
        layout.addWidget(sessions_group)
        
        # Access link display
        link_group = QGroupBox("Session Access Link")
        link_layout = QVBoxLayout()
        
        self.access_link_input = QLineEdit()
        self.access_link_input.setReadOnly(True)
        self.access_link_input.setPlaceholderText("Access link will appear here after creating a session")
        link_layout.addWidget(self.access_link_input)
        
        link_buttons = QHBoxLayout()
        self.copy_link_btn = QPushButton("Copy Link")
        self.copy_link_btn.clicked.connect(self.copy_access_link)
        link_buttons.addWidget(self.copy_link_btn)
        link_buttons.addStretch()
        link_layout.addLayout(link_buttons)
        
        link_group.setLayout(link_layout)
        layout.addWidget(link_group)
        
        layout.addStretch()
    
    def setup_timer(self) -> None:
        """Set up timer for periodic updates."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_sessions)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def create_session(self) -> None:
        """Create a new remote access session."""
        client_name = self.client_name_input.text().strip()
        if not client_name:
            QMessageBox.warning(self, "Error", "Please enter a client name")
            return
        
        access_level_map = {
            "View Only": "view_only",
            "View & Annotate": "view_annotate",
            "View & Control": "view_control",
            "Full Access": "full_access",
        }
        access_level = access_level_map[self.access_level_combo.currentText()]
        
        try:
            # Create session via API or service
            if self.remote_service:
                # Direct service call
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                session = loop.run_until_complete(
                    self.remote_service.create_session(
                        client_name=client_name,
                        access_level=access_level,
                        ip_address="",
                        user_agent="Desktop App",
                    )
                )
                loop.close()
                
                # Generate access link
                try:
                    from config import API_BASE_URL
                    base_url = API_BASE_URL
                except ImportError:
                    # Fallback if config not available
                    import os
                    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
                access_link = self.remote_service.generate_access_link(session.session_id, base_url)
                
                self.access_link_input.setText(access_link)
                QMessageBox.information(
                    self,
                    "Session Created",
                    f"Session created successfully!\n\nAccess Token: {session.access_token[:16]}...\n\nLink copied to clipboard.",
                )
                
                # Copy to clipboard
                clipboard = QApplication.clipboard()
                clipboard.setText(access_link)
                
                # Clear input
                self.client_name_input.clear()
                
                # Refresh sessions
                self.refresh_sessions()
            else:
                QMessageBox.warning(
                    self,
                    "Service Unavailable",
                    "Remote access service is not available. Please check the API server.",
                )
        except Exception as e:
            LOGGER.error("Error creating session: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to create session: {str(e)}")
    
    def refresh_sessions(self) -> None:
        """Refresh the active sessions table."""
        if not self.remote_service:
            return
        
        try:
            sessions = self.remote_service.list_sessions()
            
            self.sessions_table.setRowCount(len(sessions))
            
            for row, session_data in enumerate(sessions):
                # Client name
                self.sessions_table.setItem(row, 0, QTableWidgetItem(session_data.get("client_name", "")))
                
                # Access level
                access_level = session_data.get("access_level", "view_only")
                self.sessions_table.setItem(row, 1, QTableWidgetItem(access_level.replace("_", " ").title()))
                
                # IP address
                self.sessions_table.setItem(row, 2, QTableWidgetItem(session_data.get("ip_address", "")))
                
                # Created time
                created = session_data.get("created_at", 0)
                created_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created)) if created else "N/A"
                self.sessions_table.setItem(row, 3, QTableWidgetItem(created_str))
                
                # Last activity
                last_activity = session_data.get("last_activity", 0)
                last_activity_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_activity)) if last_activity else "N/A"
                self.sessions_table.setItem(row, 4, QTableWidgetItem(last_activity_str))
                
                # Status
                connected = session_data.get("connected", False)
                status_item = QTableWidgetItem("Connected" if connected else "Disconnected")
                status_item.setForeground(Qt.green if connected else Qt.red)
                self.sessions_table.setItem(row, 5, status_item)
                
                # Actions
                disconnect_btn = QPushButton("Disconnect")
                disconnect_btn.clicked.connect(
                    lambda checked, sid=session_data["session_id"]: self.disconnect_session(sid)
                )
                self.sessions_table.setCellWidget(row, 6, disconnect_btn)
            
            self.sessions_table.resizeColumnsToContents()
        except Exception as e:
            LOGGER.error("Error refreshing sessions: %s", e)
    
    def disconnect_session(self, session_id: str) -> None:
        """Disconnect a remote access session."""
        if not self.remote_service:
            return
        
        reply = QMessageBox.question(
            self,
            "Disconnect Session",
            f"Are you sure you want to disconnect session {session_id[:8]}...?",
            QMessageBox.Yes | QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.remote_service.disconnect_session(session_id))
                loop.close()
                self.refresh_sessions()
            except Exception as e:
                LOGGER.error("Error disconnecting session: %s", e)
                QMessageBox.critical(self, "Error", f"Failed to disconnect session: {str(e)}")
    
    def copy_access_link(self) -> None:
        """Copy access link to clipboard."""
        link = self.access_link_input.text()
        if link:
            clipboard = QApplication.clipboard()
            clipboard.setText(link)
            QMessageBox.information(self, "Copied", "Access link copied to clipboard!")
        else:
            QMessageBox.warning(self, "No Link", "No access link available to copy.")


__all__ = ["RemoteAccessTab"]

