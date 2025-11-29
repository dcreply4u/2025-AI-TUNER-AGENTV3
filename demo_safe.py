"""
Safe Demo Launcher - Shows basic window first, then adds components
"""

import sys
import traceback
from pathlib import Path

# Set demo mode
import os
os.environ["AITUNER_DEMO_MODE"] = "true"

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Initialize logging
try:
    from core.init_logging import initialize_logging
    initialize_logging(
        log_level="INFO",
        log_file=Path("logs/demo.log"),
        enable_performance=False,
        enable_structured=False,
        colorize=True,
    )
except Exception as e:
    print(f"[WARN] Logging initialization failed: {e}")

print("=" * 80)
print("SAFE DEMO LAUNCHER")
print("=" * 80)

try:
    from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
    from PySide6.QtCore import QTimer, Qt

    from ui.startup_splash import show_startup_splash_if_available
    
    app = QApplication(sys.argv)
    print("[OK] QApplication created")

    # Show startup splash (non-blocking, fades in/out)
    try:
        show_startup_splash_if_available()
        print("[OK] Startup splash (if image available)")
    except Exception as e:
        print(f"[WARN] Startup splash failed: {e}")
    
    # Create minimal window first
    print("[STEP 1] Creating minimal window...")
    window = QWidget()
    window.setWindowTitle("AI Tuner Agent - Loading...")
    window.resize(1400, 800)
    
    layout = QVBoxLayout(window)
    status_label = QLabel("Initializing...")
    status_label.setStyleSheet("font-size: 16px; padding: 20px;")
    layout.addWidget(status_label)
    
    window.show()
    app.processEvents()
    print("[OK] Basic window shown")
    
    # Store main_window reference at module level to prevent garbage collection
    main_window_ref = None
    
    # Now try to load MainWindow
    def load_main_window():
        global main_window_ref
        try:
            status_label.setText("Loading MainWindow...")
            app.processEvents()
            
            print("[STEP 2] Importing MainWindow...")
            from ui.main import MainWindow
            
            status_label.setText("Creating MainWindow instance...")
            app.processEvents()
            
            print("[STEP 3] Creating MainWindow...")
            main_window = MainWindow()
            main_window_ref = main_window  # Keep reference to prevent GC
            
            status_label.setText("MainWindow created successfully!")
            app.processEvents()
            
            # Hide simple window, show main window (simple approach)
            window.hide()
            main_window.setWindowFlags(main_window.windowFlags() | Qt.WindowType.Window)
            main_window.show()
            
            print("[SUCCESS] MainWindow loaded and shown")
            
            # Start unified knowledge update service (runs in background automatically)
            try:
                from services.knowledge_update_service import start_knowledge_update_service
                if start_knowledge_update_service():
                    print("[OK] Knowledge Update Service started (runs automatically)")
                else:
                    print("[WARN] Knowledge Update Service could not start")
            except Exception as e:
                print(f"[WARN] Could not start knowledge update service: {e}")
                traceback.print_exc()
            
            # Start demo controller
            try:
                from demo import DemoController
                status_label.setText("Starting demo controller...")
                app.processEvents()
                
                demo = DemoController(main_window, mode="demo")
                demo.start()
                # Store demo reference too
                main_window.demo_controller = demo
                print("[OK] Demo controller started")
            except Exception as e:
                print(f"[WARN] Demo controller failed: {e}")
                traceback.print_exc()
            
            # Start data stream to enable telemetry graphs
            try:
                status_label.setText("Starting data stream...")
                app.processEvents()
                print("[DEBUG] Setting stream settings...")
                # Set source to simulated for demo mode
                main_window.stream_settings["source"] = "simulated"
                main_window.stream_settings["mode"] = "live"
                print(f"[DEBUG] Stream settings: source={main_window.stream_settings['source']}, mode={main_window.stream_settings['mode']}")
                # Start the data stream to feed telemetry panel
                print("[DEBUG] Calling start_session()...")
                main_window.start_session()
                print("[OK] Data stream started with simulated data - telemetry graphs should be active")
                # Verify data stream controller was created
                if hasattr(main_window, 'data_stream_controller'):
                    print(f"[DEBUG] Data stream controller exists: {main_window.data_stream_controller}")
                    if main_window.data_stream_controller:
                        print(f"[DEBUG] Timer active: {main_window.data_stream_controller.timer.isActive()}")
                else:
                    print("[WARN] Data stream controller not found on main_window")
            except Exception as e:
                print(f"[ERROR] Failed to start data stream: {e}")
                traceback.print_exc()
            
        except Exception as e:
            print(f"[ERROR] Failed to load MainWindow: {e}")
            traceback.print_exc()
            status_label.setText(f"ERROR: {str(e)}")
            status_label.setStyleSheet("font-size: 14px; padding: 20px; color: #e74c3c;")
            window.show()  # Show error window
    
    # Load main window after a short delay
    QTimer.singleShot(500, load_main_window)
    
    print("[INFO] Application running...")
    print("[INFO] Window should be visible and movable normally")
    
    # Run event loop
    sys.exit(app.exec())
    
except Exception as e:
    print(f"[FATAL] Critical error: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")
    sys.exit(1)
