from __future__ import annotations

"""\
=========================================================
Fault Panel – cozy corner for code reading & clearing
=========================================================
"""

from typing import Iterable, Tuple

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from ai.fault_analyzer import FaultAnalyzer
from interfaces.obd_interface import OBDInterface


class FaultPanel(QWidget):
    """UI helper for reading and clearing DTCs via the selected interface."""

    def __init__(self, obd_interface: OBDInterface | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.obd = obd_interface
        self.analyzer = FaultAnalyzer()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title label with styling
        title_label = QLabel("Diagnostic Trouble Codes (DTCs)")
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #2c3e50; padding: 5px;")
        layout.addWidget(title_label)

        # Text box with proper sizing and styling
        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.setMinimumHeight(120)  # Ensure it's visible
        self.text_box.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
                color: #2c3e50;
                font-size: 11px;
            }
        """)
        
        # Buttons with consistent styling
        self.refresh_btn = QPushButton("Read Codes")
        self.clear_btn = QPushButton("Clear Codes")
        
        # Apply consistent button styling
        button_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        self.refresh_btn.setStyleSheet(button_style)
        self.clear_btn.setStyleSheet(button_style)

        self.refresh_btn.clicked.connect(self.read_codes)
        self.clear_btn.clicked.connect(self.clear_codes)

        layout.addWidget(self.text_box, stretch=1)  # Allow text box to expand
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.clear_btn)
        
        # Set minimum size to ensure visibility
        self.setMinimumSize(280, 200)

    def set_obd_interface(self, interface: OBDInterface) -> None:
        self.obd = interface

    def _render_insights(self, dtcs: Iterable[Tuple[str, str]]) -> None:
        insights = self.analyzer.analyze(dtcs)
        self.text_box.setText("\n".join(insights))

    def read_codes(self) -> None:
        if not self.obd:
            self.text_box.setText("No OBD interface configured.")
            return
        codes = self.obd.get_dtc_codes()
        if not codes:
            self.text_box.setText("No active or pending codes found.")
            return
        self._render_insights(codes)

    def clear_codes(self) -> None:
        if not self.obd:
            self.text_box.setText("No OBD interface configured.")
            return
        success = self.obd.clear_dtc_codes()
        self.text_box.setText(
            "DTCs cleared successfully." if success else "Failed to clear DTCs."
        )


__all__ = ["FaultPanel"]

