"""
Windows Launcher for AI Tuner Agent

Optimized for Windows platform with Treehopper USB support.

Usage:
    python launch_windows.py
    python launch_windows.py --demo
    python launch_windows.py --check-hardware
"""

import argparse
import os
import sys
import platform
from pathlib import Path

# Verify we're on Windows
if platform.system() != "Windows":
    print("[WARNING] This launcher is designed for Windows.")
    print(f"Detected platform: {platform.system()}")
    print("Consider using demo.py or main.py instead.")
    response = input("Continue anyway? (y/n): ")
    if response.lower() != 'y':
        sys.exit(1)

# Set demo mode environment variable if needed
if "--demo" in sys.argv:
    os.environ["AITUNER_DEMO_MODE"] = "true"

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Initialize logging
from core.init_logging import initialize_logging
initialize_logging(
    log_level="INFO",
    log_file=Path("logs/windows.log"),
    enable_performance=True,
    enable_structured=False,
    colorize=True,
)

import logging
LOGGER = logging.getLogger(__name__)

from PySide6.QtWidgets import QApplication


def check_hardware() -> dict:
    """Check for available hardware on Windows."""
    hardware_status = {
        "treehopper": False,
        "treehopper_details": None,
        "can_adapters": [],
        "platform": "Windows",
    }
    
    print("=" * 60)
    print("Hardware Detection - Windows Platform")
    print("=" * 60)
    
    # Check for Treehopper
    try:
        from interfaces.treehopper_adapter import get_treehopper_adapter
        treehopper = get_treehopper_adapter()
        if treehopper and treehopper.is_connected():
            hardware_status["treehopper"] = True
            hardware_status["treehopper_details"] = {
                "gpio_pins": treehopper.GPIO_PINS,
                "adc_channels": treehopper.ADC_CHANNELS,
                "pwm_channels": treehopper.PWM_CHANNELS,
            }
            print("[✓] Treehopper USB device detected")
            print(f"    - GPIO Pins: {treehopper.GPIO_PINS}")
            print(f"    - ADC Channels: {treehopper.ADC_CHANNELS}")
            print(f"    - PWM Channels: {treehopper.PWM_CHANNELS}")
        else:
            print("[✗] Treehopper USB device not detected")
            print("    - Connect Treehopper via USB to enable GPIO/ADC")
    except Exception as e:
        print(f"[✗] Treehopper detection failed: {e}")
        print("    - Install 'hid' library: pip install hidapi")
    
    # Check for CAN adapters (would need specific detection)
    print("\n[!] CAN Bus adapters:")
    print("    - USB-CAN adapters should be detected automatically")
    print("    - Check Device Manager for connected CAN interfaces")
    
    # Check hardware platform config
    try:
        from core.hardware_platform import get_hardware_config
        config = get_hardware_config()
        print(f"\n[✓] Platform detected: {config.platform_name}")
        print(f"    - GPIO Available: {config.gpio_available}")
        print(f"    - CAN Channels: {config.can_channels}")
        if config.has_treehopper:
            print(f"    - Treehopper: Connected ({config.total_gpio_pins} GPIO, {config.total_adc_channels} ADC)")
    except Exception as e:
        print(f"\n[✗] Platform detection failed: {e}")
    
    print("=" * 60)
    return hardware_status


def main():
    """Main Windows launcher."""
    parser = argparse.ArgumentParser(description="AI Tuner Agent - Windows Launcher")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with simulated data",
    )
    parser.add_argument(
        "--check-hardware",
        action="store_true",
        help="Check for connected hardware (Treehopper, CAN adapters)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()
    
    # Hardware check mode
    if args.check_hardware:
        check_hardware()
        return
    
    # Set debug mode if requested
    if args.debug:
        os.environ["AITUNER_DEBUG"] = "true"
        log_level = "DEBUG"
    else:
        log_level = "INFO"
    
    # Re-initialize logging with correct level
    initialize_logging(
        log_level=log_level,
        log_file=Path("logs/windows.log"),
        enable_performance=True,
        enable_structured=False,
        colorize=True,
    )
    
    print("=" * 60)
    print("AI Tuner Agent - Windows Platform")
    print("=" * 60)
    
    # Check hardware status
    hardware = check_hardware()
    
    if not hardware["treehopper"]:
        print("\n[INFO] Treehopper not detected - GPIO/ADC features will be limited")
        print("       Connect Treehopper USB device to enable full I/O capabilities")
        print()
    
    # Demo mode
    if args.demo:
        print("[INFO] Running in DEMO MODE - Simulated data only")
        print("=" * 60)
        print()
        
        # Import demo components
        from controllers.data_stream_controller import DataStreamController, StreamSettings
        from interfaces.simulated_interface import SimulatedInterface
        from services.data_simulator import DataSimulator
        from ui.main_container import MainContainerWindow
        
        app = QApplication(sys.argv)
        
        # Create main window
        window = MainContainerWindow()
        window.setWindowTitle("AI Tuner Agent - Windows Demo Mode")
        
        # Create demo controller (similar to demo.py)
        from PySide6.QtCore import QTimer
        
        simulator = DataSimulator(mode="demo")
        simulated_interface = SimulatedInterface(mode="demo")
        
        def update_telemetry():
            try:
                data = simulator.poll()
                telemetry_dict = {
                    "RPM": data.get("rpm", 0),
                    "Engine_RPM": data.get("rpm", 0),
                    "Boost_Pressure": data.get("boost_pressure", 0),
                    "boost_psi": data.get("boost_pressure", 0),
                    "AFR": data.get("lambda_value", 1.0) * 14.7,
                    "lambda_value": data.get("lambda_value", 1.0),
                    "Throttle_Position": data.get("throttle_position", 0),
                    "throttle": data.get("throttle_position", 0),
                    "Speed": data.get("vehicle_speed", 0),
                    "Vehicle_Speed": data.get("vehicle_speed", 0),
                }
                if hasattr(window, 'update_telemetry') and window.isVisible():
                    window.update_telemetry(telemetry_dict)
            except Exception as e:
                LOGGER.debug(f"Error updating telemetry: {e}")
        
        timer = QTimer()
        timer.timeout.connect(update_telemetry)
        timer.start(200)  # 5 Hz
        
        window.show()
        window.raise_()
        window.activateWindow()
        
        print("[SUCCESS] GUI launched! Close the window to exit.")
        print()
        
        sys.exit(app.exec())
    
    # Full mode - import main application
    else:
        print("[INFO] Starting full application...")
        print("=" * 60)
        print()
        
        try:
            from ui.main_container import MainContainerWindow
            
            app = QApplication(sys.argv)
            
            # Create main window
            window = MainContainerWindow()
            window.setWindowTitle("AI Tuner Agent - Windows")
            
            # Show window
            window.show()
            window.raise_()
            window.activateWindow()
            
            print("[SUCCESS] Application launched! Close the window to exit.")
            print()
            
            sys.exit(app.exec())
            
        except Exception as e:
            print(f"[ERROR] Failed to start application: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()




