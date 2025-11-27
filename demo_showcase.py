"""
Demo Showcase - Enhanced demo with all features enabled
Shows off all the magic we've built!
"""

import sys
import time
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
        log_file=Path("logs/demo_showcase.log"),
        enable_performance=False,
        enable_structured=False,
        colorize=True,
    )
except Exception as e:
    print(f"[WARN] Logging initialization failed: {e}")

print("=" * 80)
print("🎯 AI TUNER AGENT - DEMO SHOWCASE 🎯")
print("=" * 80)
print()
print("✨ Features Enabled:")
print("  ✅ Advanced Intelligence & Algorithms")
print("  ✅ Real-time Sensor Correlation")
print("  ✅ Anomaly Detection")
print("  ✅ Kalman Filter GPS/IMU Fusion")
print("  ✅ Wheel Slip Calculation")
print("  ✅ Live Telemetry Graphs")
print("  ✅ AI Advisor with 52+ Knowledge Entries")
print("  ✅ Drag Mode Analysis")
print("  ✅ Performance Tracking")
print("=" * 80)
print()

try:
    from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtGui import QFont
    
    app = QApplication(sys.argv)
    print("[OK] QApplication created")
    
    # Create showcase window
    print("[STEP 1] Creating showcase window...")
    window = QWidget()
    window.setWindowTitle("AI Tuner Agent - Demo Showcase")
    window.resize(1600, 900)
    
    layout = QVBoxLayout(window)
    
    # Title
    title = QLabel("🎯 AI TUNER AGENT - LIVE DEMO")
    title_font = QFont()
    title_font.setPointSize(20)
    title_font.setBold(True)
    title.setFont(title_font)
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("color: #007acc; padding: 20px;")
    layout.addWidget(title)
    
    # Status display
    status_display = QTextEdit()
    status_display.setReadOnly(True)
    status_display.setMaximumHeight(200)
    status_display.setStyleSheet("font-family: 'Courier New'; font-size: 11px; background: #1e1e1e; color: #d4d4d4;")
    layout.addWidget(status_display)
    
    def log_status(message: str):
        """Log status message."""
        status_display.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        status_display.verticalScrollBar().setValue(status_display.verticalScrollBar().maximum())
        print(message)
    
    # Start button
    start_btn = QPushButton("🚀 START DEMO")
    start_btn.setStyleSheet("""
        QPushButton {
            background-color: #007acc;
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 15px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #005a9e;
        }
    """)
    layout.addWidget(start_btn)
    
    window.show()
    log_status("Showcase window created")
    
    # Load main window
    def load_main_window():
        log_status("Loading main application window...")
        try:
            from ui.main import MainWindow
            
            log_status("Creating main window...")
            main_window = MainWindow()
            main_window.setWindowTitle("AI Tuner Agent - Live Demo")
            main_window.show()
            log_status("✅ Main window displayed")
            
            # Start demo controller
            try:
                from demo import DemoController
                log_status("Starting demo controller...")
                app.processEvents()
                
                demo = DemoController(main_window, mode="demo")
                demo.start()
                main_window.demo_controller = demo
                log_status("✅ Demo controller started")
            except Exception as e:
                log_status(f"⚠️ Demo controller failed: {e}")
                traceback.print_exc()
            
            # Start data stream to enable telemetry graphs
            try:
                log_status("Starting data stream...")
                app.processEvents()
                # Set source to simulated for demo mode
                main_window.stream_settings["source"] = "simulated"
                main_window.stream_settings["mode"] = "live"
                # Start the data stream to feed telemetry panel
                main_window.start_session()
                log_status("✅ Data stream started with simulated data")
                log_status("")
                log_status("🎉 DEMO IS RUNNING!")
                log_status("")
                log_status("📊 Watch the telemetry graphs update in real-time")
                log_status("🤖 Try asking the AI Advisor questions about tuning")
                log_status("🏁 Check out the drag mode panel")
                log_status("📈 See advanced algorithms processing data")
                log_status("")
                log_status("✨ All systems operational! ✨")
            except Exception as e:
                log_status(f"⚠️ Failed to start data stream: {e}")
                traceback.print_exc()
            
            # Hide showcase window
            window.hide()
            
        except Exception as e:
            log_status(f"❌ Error loading main window: {e}")
            traceback.print_exc()
    
    start_btn.clicked.connect(load_main_window)
    
    # Auto-start after 2 seconds
    QTimer.singleShot(2000, load_main_window)
    
    print("[OK] Showcase window ready - auto-starting in 2 seconds...")
    print()
    print("=" * 80)
    print("🎯 DEMO SHOWCASE READY")
    print("=" * 80)
    print()
    print("The application will start automatically in 2 seconds...")
    print("Or click the START DEMO button to begin immediately!")
    print()
    
    sys.exit(app.exec())
    
except Exception as e:
    print(f"[ERROR] Failed to create showcase: {e}")
    traceback.print_exc()
    sys.exit(1)

