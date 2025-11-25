"""
Demo Launcher

Quick launcher to preview the GUI with simulated data.
No hardware required!

Usage:
    python demo.py
    python demo.py --mode racing
    python demo.py --mode demo
    python demo.py --debug

Note: This is a GUI application that will block until the window is closed.
If running from Cursor or an IDE, consider running in a separate terminal window
to avoid blocking the IDE interface.
"""

import argparse
import os
import sys
from pathlib import Path

# Set demo mode environment variable to prevent network camera scanning
os.environ["AITUNER_DEMO_MODE"] = "true"

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Initialize logging system early (will be re-initialized in main() with correct level)
from core.init_logging import initialize_logging
# Note: Logging will be re-initialized in main() based on --debug flag
# This is just to ensure logging is available during imports
initialize_logging(
    log_level="INFO",
    log_file=Path("logs/demo.log"),
    enable_performance=True,
    enable_structured=False,  # Simpler for demo
    colorize=True,
)

from PySide6.QtWidgets import QApplication

from controllers.data_stream_controller import DataStreamController, StreamSettings
# Crash detection temporarily disabled - causing initialization issues
# from core.crash_detector import get_crash_detector
# from core.crash_logger import get_crash_logger
get_crash_detector = None
get_crash_logger = None
from interfaces.simulated_interface import SimulatedInterface
from services.data_simulator import DataSimulator
from ui.main_container import MainContainerWindow


class DemoController:
    """Controller for demo mode with simulated data."""

    def __init__(self, window: MainContainerWindow, mode: str = "demo") -> None:
        """
        Initialize demo controller.

        Args:
            window: Main window instance
            mode: Simulation mode
        """
        import logging
        LOGGER = logging.getLogger(__name__)
        
        LOGGER.info("Initializing demo controller (mode: %s)", mode)
        LOGGER.info("Demo mode environment variable set: %s", os.environ.get("AITUNER_DEMO_MODE", "not set"))
        
        self.window = window
        self.mode = mode
        self.simulator = DataSimulator(mode=mode)
        LOGGER.debug("Data simulator created for mode: %s", mode)

        # Create simulated interface
        self.simulated_interface = SimulatedInterface(mode=mode)
        LOGGER.debug("Simulated interface created")

        # Setup data connection for ECU tuning interface
        self._setup_data_connection()

    def _setup_data_connection(self) -> None:
        """Set up data connection for ECU tuning interface."""
        # Create a timer to feed simulated data to the ECU tuning interface
        from PySide6.QtCore import QTimer
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self._update_ecu_interface)
        self.data_timer.start(200)  # 5 Hz update rate - reduced to match main container
        self._running = True
        print("[SETUP] ECU tuning interface data connection established")
        
    def _update_ecu_interface(self) -> None:
        """Update ECU tuning interface with simulated data."""
        if not getattr(self, '_running', True):
            return
        try:
            data = self.simulator.poll()
            # Convert to format expected by ECU interface
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
            if hasattr(self.window, 'update_telemetry') and self.window.isVisible():
                self.window.update_telemetry(telemetry_dict)
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Error updating ECU interface: {e}")

    def start(self) -> None:
        """Start demo simulation."""
        print("[INFO] Starting ECU tuning interface with simulated data...")
        
        # Initial data update
        self._update_ecu_interface()
        
        print("[INFO] ECU tuning interface active - live data should be visible!")
    
    def stop(self) -> None:
        """Stop demo simulation."""
        self._running = False
        if hasattr(self, 'data_timer') and self.data_timer:
            try:
                self.data_timer.stop()
                self.data_timer = None
            except Exception:
                pass


def main():
    """Main demo launcher."""
    parser = argparse.ArgumentParser(description="AI Tuner Agent - GUI Demo")
    parser.add_argument(
        "--mode",
        choices=["idle", "cruising", "racing", "demo"],
        default="demo",
        help="Simulation mode (default: demo)",
    )
    parser.add_argument("--no-voice", action="store_true", help="Disable voice output")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging and verbose output")
    args = parser.parse_args()

    # Set debug mode in environment if requested
    if args.debug:
        os.environ["AITUNER_DEBUG"] = "true"
        log_level = "DEBUG"
        log_file = Path("logs/debug_demo.log")
        print("=" * 60)
        print("AI Tuner Agent - GUI Demo Mode (DEBUG)")
        print("=" * 60)
    else:
        log_level = "INFO"
        log_file = Path("logs/demo.log")
        print("=" * 60)
        print("AI Tuner Agent - GUI Demo Mode")
        print("=" * 60)
    
    # Re-initialize logging with debug level if needed
    initialize_logging(
        log_level=log_level,
        log_file=log_file,
        enable_performance=True,
        enable_structured=False,
        colorize=True,
    )
    
    print(f"Mode: {args.mode}")
    if args.debug:
        print("Debug Mode: ENABLED")
    print("No hardware required - using simulated data")
    print("=" * 60)
    print()

    app = QApplication(sys.argv)
    
    # Check license status
    try:
        from core.license_manager import get_license_manager
        license_manager = get_license_manager()
        if license_manager.is_demo_mode():
            print("[INFO] Running in DEMO MODE - Limited features available")
            print("[INFO] Enter license key in Settings to unlock full features")
        else:
            license_type = license_manager.get_license_type().value.upper()
            print(f"[INFO] License active: {license_type}")
    except Exception as e:
        print(f"[WARN] License check failed: {e}")
    
    # Initialize UI scaling system
    from ui.ui_scaling import UIScaler
    scaler = UIScaler.get_instance()
    print(f"[INFO] UI Scale Factor: {scaler.get_scale_factor():.2f}x")

    # Crash detection temporarily disabled
    crash_detector = None
    crash_logger = None

    # Create main container window with comprehensive error handling
    try:
        if args.debug:
            print("[DEBUG] Creating MainContainerWindow...")
        window = MainContainerWindow()
        if args.debug:
            print("[DEBUG] MainContainerWindow created successfully")
            print(f"[DEBUG] Window size: {window.width()}x{window.height()}")
            print(f"[DEBUG] Window visible: {window.isVisible()}")
            print(f"[DEBUG] Window styleSheet applied: {bool(window.styleSheet())}")
            print(f"[DEBUG] Racing theme loaded: {hasattr(window, 'mode_manager')}")
    except Exception as e:
        print(f"[ERROR] Failed to create MainContainerWindow: {e}")
        import traceback
        traceback.print_exc()
        if args.debug:
            import logging
            logging.getLogger(__name__).exception("Failed to create MainContainerWindow")
        sys.exit(1)

    # Create and start demo controller
    demo = None
    try:
        demo = DemoController(window, mode=args.mode)
        demo.start()
        # Store reference in window for cleanup
        window.demo_controller = demo
        if args.debug:
            print("[DEBUG] Demo controller started")
    except Exception as e:
        print(f"[WARN] Demo controller error: {e}")
        import traceback
        traceback.print_exc()
        if args.debug:
            import logging
            logging.getLogger(__name__).exception("Demo controller error")

    # Ensure window is visible and has proper size
    if args.debug:
        print("[DEBUG] Setting window size and visibility...")
    from ui.ui_scaling import get_scaled_size
    # Don't override window size settings - let the window handle its own sizing
    # The MainContainerWindow already sets appropriate min/max sizes
    
    # Make absolutely sure window is visible
    window.setVisible(True)
    window.show()
    window.raise_()  # Bring to front
    window.activateWindow()  # Activate window
    
    # Update window title
    window.setWindowTitle(f"AI Tuner Agent - Demo Mode ({args.mode})")
    
    # Force multiple event processing cycles to ensure window appears
    for i in range(5):
        app.processEvents()
        if args.debug and i == 0:
            print(f"[DEBUG] Processed events cycle {i+1}")
    
    # Verify window is actually visible
    if args.debug:
        print(f"[DEBUG] Window visible: {window.isVisible()}")
        print(f"[DEBUG] Window size: {window.width()}x{window.height()}")
        print(f"[DEBUG] Window position: {window.x()}, {window.y()}")
        if hasattr(window, 'tabs'):
            print(f"[DEBUG] Tabs widget exists: {window.tabs.count()} tabs loaded")
        # Check theme
        try:
            from ui.racing_ui_theme import get_racing_theme
            theme = get_racing_theme()
            print(f"[DEBUG] Racing theme colors: Primary={theme.colors['accent_neon_blue']}")
            print(f"[DEBUG] Window stylesheet length: {len(window.styleSheet()) if window.styleSheet() else 0}")
        except Exception as e:
            print(f"[DEBUG] Could not check theme: {e}")
    
    if window.isVisible():
        if args.debug:
            print("[SUCCESS] Window is visible and should be on screen!")
        else:
            print("[SUCCESS] GUI launched! Close the window to exit.")
    else:
        print("[ERROR] Window is NOT visible - attempting to fix...")
        window.setVisible(True)
        window.show()
        window.raise_()
        window.activateWindow()
        app.processEvents()
        if args.debug:
            print(f"[DEBUG] After fix - Window visible: {window.isVisible()}")
    
    if not args.debug:
        print("If you don't see the window, check if it's behind other windows or minimized.")
        print()

    # Run application
    # Note: app.exec() blocks until the window is closed
    # This is normal behavior for GUI applications
    exit_code = app.exec()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

