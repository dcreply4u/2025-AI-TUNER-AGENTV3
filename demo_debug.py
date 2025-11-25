"""
Debug Demo Launcher - Logs every step to find the crash
"""

import sys
import traceback
from pathlib import Path

# Redirect all output to file
log_file = Path("logs/debug_demo.log")
log_file.parent.mkdir(parents=True, exist_ok=True)

class DebugOutput:
    def __init__(self, file_path):
        self.file = open(file_path, 'w', encoding='utf-8')
        self.stdout = sys.stdout
    
    def write(self, text):
        self.file.write(text)
        self.file.flush()
        if self.stdout:
            self.stdout.write(text)
            self.stdout.flush()
    
    def flush(self):
        self.file.flush()
        if self.stdout:
            self.stdout.flush()
    
    def close(self):
        self.file.close()

debug_out = DebugOutput(log_file)
sys.stdout = debug_out
sys.stderr = debug_out

print("=" * 80)
print("DEBUG DEMO LAUNCHER")
print("=" * 80)
print(f"All output logged to: {log_file}")
print("=" * 80)
print()

try:
    print("[STEP 1] Setting environment...")
    import os
    os.environ["AITUNER_DEMO_MODE"] = "true"
    print("[OK] Environment set")
    
    print("[STEP 2] Adding project to path...")
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    print(f"[OK] Path added: {project_root}")
    
    print("[STEP 3] Importing PySide6...")
    from PySide6.QtWidgets import QApplication
    print("[OK] PySide6 imported")
    
    print("[STEP 4] Creating QApplication...")
    app = QApplication(sys.argv)
    print("[OK] QApplication created")
    
    print("[STEP 5] Creating minimal test window...")
    from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
    test_window = QWidget()
    test_window.setWindowTitle("Debug Test")
    test_window.resize(600, 400)
    test_layout = QVBoxLayout(test_window)
    test_label = QLabel("If you see this, Qt is working!")
    test_layout.addWidget(test_label)
    test_window.show()
    app.processEvents()
    print("[OK] Test window shown")
    
    print("[STEP 6] Importing MainWindow module...")
    try:
        import ui.main as main_module
        print("[OK] MainWindow module imported")
    except Exception as e:
        print(f"[ERROR] Failed to import MainWindow module: {e}")
        traceback.print_exc()
        raise
    
    print("[STEP 7] Getting MainWindow class...")
    try:
        MainWindow = main_module.MainWindow
        print("[OK] MainWindow class obtained")
    except Exception as e:
        print(f"[ERROR] Failed to get MainWindow class: {e}")
        traceback.print_exc()
        raise
    
    print("[STEP 8] Creating MainWindow instance...")
    print("  [8.1] Calling MainWindow.__init__...")
    try:
        window = MainWindow()
        print("[OK] MainWindow instance created")
    except Exception as e:
        print(f"[ERROR] Failed to create MainWindow instance: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("\n" + "=" * 80)
        print("CRASH DETECTED - Check traceback above")
        print("=" * 80)
        
        # Show error in window
        error_label = QLabel(f"ERROR: {str(e)}\n\nCheck {log_file} for details")
        error_label.setStyleSheet("color: red; padding: 20px;")
        test_layout.addWidget(error_label)
        test_window.show()
        
        # Keep window open
        print("\nWindow will stay open. Close it to exit.")
        sys.exit(app.exec())
    
    print("[STEP 9] Setting window properties...")
    window.setMinimumSize(1000, 700)
    window.resize(1400, 800)
    window.setWindowTitle("AI Tuner Agent - Debug Mode")
    print("[OK] Window properties set")
    
    print("[STEP 10] Showing window...")
    try:
        print("  [10.1] Calling window.show()...")
        window.show()
        print("  [OK] window.show() succeeded")
        
        print("  [10.2] Calling window.raise_()...")
        window.raise_()
        print("  [OK] window.raise_() succeeded")
        
        print("  [10.3] Calling window.activateWindow()...")
        window.activateWindow()
        print("  [OK] window.activateWindow() succeeded")
        
        print("  [10.4] Processing events...")
        app.processEvents()
        print("  [OK] Events processed")
        
        print("[OK] Window shown successfully")
    except Exception as e:
        print(f"[ERROR] Failed to show window: {e}")
        traceback.print_exc()
        raise
    
    print("[STEP 11] Hiding test window...")
    test_window.hide()
    print("[OK] Test window hidden")
    
    print("\n" + "=" * 80)
    print("SUCCESS - MainWindow loaded and shown!")
    print("=" * 80)
    print(f"Debug log: {log_file}")
    print("=" * 80)
    print()
    
    # Try to start demo controller
    print("[STEP 12] Starting demo controller...")
    try:
        from demo import DemoController
        demo = DemoController(window, mode="demo")
        demo.start()
        print("[OK] Demo controller started")
    except Exception as e:
        print(f"[WARN] Demo controller failed (non-critical): {e}")
        traceback.print_exc()
    
    print("\nApplication running. Close window to exit.")
    sys.exit(app.exec())
    
except KeyboardInterrupt:
    print("\n[INFO] Interrupted by user")
    sys.exit(0)
except Exception as e:
    print(f"\n[FATAL ERROR] Unhandled exception: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    print("\n" + "=" * 80)
    print(f"Check {log_file} for full details")
    print("=" * 80)
    input("\nPress Enter to exit...")
    sys.exit(1)
finally:
    debug_out.close()
    print(f"\nDebug log saved to: {log_file}")

