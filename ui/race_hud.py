from __future__ import annotations

"""
Minimal Race HUD / Overlay
--------------------------

Lightweight always-on-top window showing:
 - Big speed readout (mph)
 - Coolant temp
 - Oil pressure
 - Simple safety light (OK / WARNING)

It polls the parent window's _telemetry_data dict on a short timer so it
does not need to be deeply wired into the data stream controller.
"""

from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class RaceHUD(QWidget):
    """Minimal overlay-style HUD for in-car / overlay use."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Race HUD")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)

        self._telemetry_source = self._find_telemetry_source()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self.speed_label = QLabel("0")
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_label.setStyleSheet(
            "font-size: 42px; font-weight: 700; color: #00e5ff;"
        )
        layout.addWidget(self.speed_label)

        self.speed_unit = QLabel("mph")
        self.speed_unit.setAlignment(Qt.AlignCenter)
        self.speed_unit.setStyleSheet(
            "font-size: 14px; font-weight: 500; color: #9ca3af;"
        )
        layout.addWidget(self.speed_unit)

        self.coolant_label = QLabel("CLT: -- °C")
        self.coolant_label.setAlignment(Qt.AlignCenter)
        self.coolant_label.setStyleSheet(
            "font-size: 12px; color: #e5e7eb; padding-top: 4px;"
        )
        layout.addWidget(self.coolant_label)

        self.oil_label = QLabel("Oil P: -- psi")
        self.oil_label.setAlignment(Qt.AlignCenter)
        self.oil_label.setStyleSheet(
            "font-size: 12px; color: #e5e7eb;"
        )
        layout.addWidget(self.oil_label)

        self.status_label = QLabel("OK")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "background-color: #16a34a; color: #ffffff; "
            "font-size: 13px; font-weight: 600; padding: 4px 8px; border-radius: 4px;"
        )
        layout.addWidget(self.status_label)

        self.setStyleSheet("background-color: #020617;")
        self.resize(200, 150)

        # Poll telemetry at 10 Hz
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_from_telemetry)
        self._timer.start(100)

    def _find_telemetry_source(self) -> Optional[QWidget]:
        """Walk up parents to find a widget with _telemetry_data attribute."""
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "_telemetry_data"):
                return parent
            parent = parent.parent()
        return None

    def _get_telemetry(self) -> Dict[str, Any]:
        if not self._telemetry_source:
            return {}
        data = getattr(self._telemetry_source, "_telemetry_data", None)
        return data or {}

    def _update_from_telemetry(self) -> None:
        data = self._get_telemetry()

        # Speed
        speed = (
            data.get("speed_mph")
            or data.get("vehicle_speed_mph")
            or data.get("GPS_Speed")
        )
        try:
            speed_val = float(speed) if speed is not None else 0.0
        except (TypeError, ValueError):
            speed_val = 0.0
        self.speed_label.setText(f"{speed_val:0.0f}")

        # Coolant temp
        clt = (
            data.get("CoolantTemp")
            or data.get("coolant_temp")
            or data.get("EngineCoolantTemp")
        )
        clt_txt = f"{clt:.0f} °C" if isinstance(clt, (int, float)) else "-- °C"
        self.coolant_label.setText(f"CLT: {clt_txt}")

        # Oil pressure
        oil = data.get("OilPressure") or data.get("oil_pressure")
        oil_txt = f"{oil:.0f} psi" if isinstance(oil, (int, float)) else "-- psi"
        self.oil_label.setText(f"Oil P: {oil_txt}")

        # Simple safety light
        status = "OK"
        color = "#16a34a"  # green
        if isinstance(clt, (int, float)) and clt > 105:
            status = "HOT"
            color = "#f97316"  # orange
        if isinstance(oil, (int, float)) and oil < 15:
            status = "OIL"
            color = "#dc2626"  # red

        self.status_label.setText(status)
        self.status_label.setStyleSheet(
            f"background-color: {color}; color: #ffffff; "
            "font-size: 13px; font-weight: 600; padding: 4px 8px; border-radius: 4px;"
        )


__all__ = ["RaceHUD"]


