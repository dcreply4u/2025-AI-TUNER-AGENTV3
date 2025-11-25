"""
Onboarding Wizard

First-time setup wizard for new users.
"""

from __future__ import annotations

from typing import Optional

try:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QLabel,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
        QWizard,
        QWizardPage,
    )
except ImportError:
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QLabel,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
        QWizard,
        QWizardPage,
    )


class WelcomePage(QWizardPage):
    """Welcome page of onboarding wizard."""

    def __init__(self, parent: Optional[QWizard] = None) -> None:
        super().__init__(parent)
        self.setTitle("Welcome to AI Tuner Agent")
        self.setSubTitle("Let's get you set up in just a few steps.")

        layout = QVBoxLayout(self)
        label = QLabel(
            "This wizard will help you configure:\n"
            "• Data source (OBD-II, RaceCapture, or CAN)\n"
            "• Vehicle profile\n"
            "• Camera setup (optional)\n"
            "• Cloud sync (optional)"
        )
        label.setWordWrap(True)
        layout.addWidget(label)


class DataSourcePage(QWizardPage):
    """Data source selection page."""

    def __init__(self, parent: Optional[QWizard] = None) -> None:
        super().__init__(parent)
        self.setTitle("Data Source Configuration")
        self.setSubTitle("Select your primary data source.")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Data Source:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Auto-detect", "OBD-II", "RaceCapture", "CAN Bus"])
        layout.addWidget(self.source_combo)

        layout.addWidget(QLabel("Port/Interface:"))
        self.port_input = QLineEdit("/dev/ttyUSB0")
        layout.addWidget(self.port_input)

        layout.addWidget(QLabel("Baud Rate:"))
        self.baud_input = QLineEdit("115200")
        layout.addWidget(self.baud_input)

        self.registerField("data_source", self.source_combo)
        self.registerField("port", self.port_input)
        self.registerField("baud", self.baud_input)


class VehicleProfilePage(QWizardPage):
    """Vehicle profile creation page."""

    def __init__(self, parent: Optional[QWizard] = None) -> None:
        super().__init__(parent)
        self.setTitle("Vehicle Profile")
        self.setSubTitle("Create a profile for your vehicle.")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Profile Name:"))
        self.name_input = QLineEdit("My Vehicle")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("ECU Vendor:"))
        self.ecu_combo = QComboBox()
        self.ecu_combo.addItems(["Generic", "Holley", "Haltech", "AEM", "Link", "MegaSquirt", "MoTec"])
        layout.addWidget(self.ecu_combo)

        layout.addWidget(QLabel("Vehicle Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Car", "Truck", "Motorcycle", "Other"])
        layout.addWidget(self.type_combo)

        self.registerField("profile_name", self.name_input)
        self.registerField("ecu_vendor", self.ecu_combo)
        self.registerField("vehicle_type", self.type_combo)


class OptionalFeaturesPage(QWizardPage):
    """Optional features page."""

    def __init__(self, parent: Optional[QWizard] = None) -> None:
        super().__init__(parent)
        self.setTitle("Optional Features")
        self.setSubTitle("Enable additional features (can be configured later).")

        layout = QVBoxLayout(self)

        self.camera_cb = QCheckBox("Enable camera support")
        layout.addWidget(self.camera_cb)

        self.gps_cb = QCheckBox("Enable GPS tracking")
        self.gps_cb.setChecked(True)
        layout.addWidget(self.gps_cb)

        self.voice_cb = QCheckBox("Enable voice control")
        self.voice_cb.setChecked(True)
        layout.addWidget(self.voice_cb)

        self.cloud_cb = QCheckBox("Enable cloud sync")
        layout.addWidget(self.cloud_cb)

        self.registerField("enable_camera", self.camera_cb)
        self.registerField("enable_gps", self.gps_cb)
        self.registerField("enable_voice", self.voice_cb)
        self.registerField("enable_cloud", self.cloud_cb)


class OnboardingWizard(QWizard):
    """Onboarding wizard for first-time setup."""

    def __init__(self, parent: Optional[QDialog] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Tuner Agent - Setup Wizard")
        self.resize(600, 400)

        # Add pages
        self.addPage(WelcomePage(self))
        self.addPage(DataSourcePage(self))
        self.addPage(VehicleProfilePage(self))
        self.addPage(OptionalFeaturesPage(self))

    def get_config(self) -> dict:
        """Get configuration from wizard."""
        return {
            "data_source": self.field("data_source"),
            "port": self.field("port"),
            "baud": int(self.field("baud")),
            "profile_name": self.field("profile_name"),
            "ecu_vendor": self.field("ecu_vendor"),
            "vehicle_type": self.field("vehicle_type"),
            "enable_camera": self.field("enable_camera"),
            "enable_gps": self.field("enable_gps"),
            "enable_voice": self.field("enable_voice"),
            "enable_cloud": self.field("enable_cloud"),
        }


__all__ = ["OnboardingWizard"]

