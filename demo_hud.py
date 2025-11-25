"""
Demo script for Futuristic HUD Interface with Real Telemetry Data
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from ui.hud_main_window import HUDMainWindow
from services.data_simulator import DataSimulator


def main() -> None:
    """Run HUD demo with simulated telemetry data."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for better appearance
    
    # Create HUD window
    window = HUDMainWindow()
    window.setWindowTitle("AI Tuner Agent - Futuristic HUD Mode")
    window.resize(1600, 900)
    window.show()
    
    # Create data simulator and connect to HUD
    simulator = DataSimulator(mode="racing")
    
    def update_hud() -> None:
        """Update HUD with simulated telemetry data."""
        data = simulator.poll()
        # Convert to dict format expected by HUD
        telemetry_dict = {
            "RPM": data.get("rpm", 0),
            "Engine_RPM": data.get("rpm", 0),
            "Speed": data.get("vehicle_speed", 0),
            "Vehicle_Speed": data.get("vehicle_speed", 0),
            "Boost_Pressure": data.get("boost_pressure", 0),
            "boost_psi": data.get("boost_pressure", 0),
            "Oil_Pressure": data.get("oil_pressure", 0),
            "oil_pressure": data.get("oil_pressure", 0),
            "Coolant_Temp": data.get("coolant_temp", 0),
            "coolant_temp": data.get("coolant_temp", 0),
            "Battery_Voltage": data.get("battery_voltage", 0),
            "battery_voltage": data.get("battery_voltage", 0),
            "Throttle_Position": data.get("throttle_position", 0),
            "throttle": data.get("throttle_position", 0),
            "GForce_Lateral": data.get("g_force_lat", 0),
            "g_force_lat": data.get("g_force_lat", 0),
            "Suspension_Travel_FL": data.get("suspension_travel_fl", 50),
            "suspension_travel_fl": data.get("suspension_travel_fl", 50),
            "Suspension_Travel_FR": data.get("suspension_travel_fr", 50),
            "suspension_travel_fr": data.get("suspension_travel_fr", 50),
            "Suspension_Travel_RL": data.get("suspension_travel_rl", 50),
            "suspension_travel_rl": data.get("suspension_travel_rl", 50),
            "Suspension_Travel_RR": data.get("suspension_travel_rr", 50),
            "suspension_travel_rr": data.get("suspension_travel_rr", 50),
            "AFR": data.get("lambda_value", 1.0) * 14.7,  # Convert lambda to AFR
            "lambda_value": data.get("lambda_value", 1.0),
        }
        window.update_telemetry(telemetry_dict)
    
    # Start update timer
    update_timer = QTimer()
    update_timer.timeout.connect(update_hud)
    update_timer.start(100)  # 10 Hz update rate
    
    # Initial update
    update_hud()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


