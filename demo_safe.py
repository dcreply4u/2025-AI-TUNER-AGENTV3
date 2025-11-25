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
    
    app = QApplication(sys.argv)
    print("[OK] QApplication created")
    
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
