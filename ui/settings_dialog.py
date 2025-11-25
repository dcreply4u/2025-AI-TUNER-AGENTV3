from __future__ import annotations

"""\
=========================================================
Settings Dialog – mission control for data-source configs
=========================================================
"""

from PySide6.QtWidgets import QComboBox, QDialog, QFormLayout, QLineEdit, QPushButton


class SettingsDialog(QDialog):
    """Modal dialog for selecting telemetry source and connection params."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")

        layout = QFormLayout(self)
        self.source_select = QComboBox()
        self.source_select.addItems(["Auto", "RaceCapture", "OBD-II"])
        self.port_input = QLineEdit("/dev/ttyUSB0")
        self.baud_input = QLineEdit("115200")

        self.network_pref = QComboBox()
        self.network_pref.addItems(["Auto", "Wi-Fi", "LTE"])
        self.obd_transport = QComboBox()
        self.obd_transport.addItems(["Auto", "USB", "Bluetooth"])

        self.bluetooth_addr = QLineEdit("")
        self.bluetooth_addr.setPlaceholderText("e.g. 00:1D:A5:12:34:56")
        self.wifi_iface_input = QLineEdit("wlan0")
        self.lte_iface_input = QLineEdit("wwan0")

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)

        layout.addRow("Data Source:", self.source_select)
        layout.addRow("Port:", self.port_input)
        layout.addRow("Baud Rate:", self.baud_input)
        layout.addRow("Network Preference:", self.network_pref)
        layout.addRow("OBD Transport:", self.obd_transport)
        layout.addRow("Bluetooth Address:", self.bluetooth_addr)
        layout.addRow("Wi-Fi Interface:", self.wifi_iface_input)
        layout.addRow("LTE Interface:", self.lte_iface_input)
        layout.addWidget(save_btn)

    def get_settings(self) -> dict:
        return {
            "source": self.source_select.currentText(),
            "port": self.port_input.text().strip(),
            "baud": int(self.baud_input.text() or "115200"),
            "network_preference": self.network_pref.currentText(),
            "obd_transport": self.obd_transport.currentText(),
            "bluetooth_address": self.bluetooth_addr.text().strip(),
            "wifi_interface": self.wifi_iface_input.text().strip() or "wlan0",
            "lte_interface": self.lte_iface_input.text().strip() or "wwan0",
        }


__all__ = ["SettingsDialog"]

