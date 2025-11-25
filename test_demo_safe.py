"""
Safe Demo Launcher - Keeps console open and logs all errors
"""

import sys
import traceback
from pathlib import Path

# Redirect stderr to a file and console
error_log = Path("logs/demo_errors.log")
error_log.parent.mkdir(parents=True, exist_ok=True)

class TeeOutput:
    """Write to both file and console."""
    def __init__(self, file_path):
        self.file = open(file_path, 'w', encoding='utf-8')
        self.stdout = sys.stdout
        self.stderr = sys.stderr
    
    def write(self, text):
        self.file.write(text)
        self.file.flush()
        self.stdout.write(text)
        self.stdout.flush()
    
    def flush(self):
        self.file.flush()
        self.stdout.flush()
    
    def close(self):
        self.file.close()

# Set up error logging
tee = TeeOutput(error_log)
sys.stdout = tee
sys.stderr = tee

print("=" * 80)
print("SAFE DEMO LAUNCHER - Error Logging Enabled")
print("=" * 80)
print(f"Errors will be logged to: {error_log}")
print("=" * 80)
print()

try:
    # Set demo mode
    import os
    os.environ["AITUNER_DEMO_MODE"] = "true"
    
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    print("[STEP 1] Importing PySide6...")
    from PySide6.QtWidgets import QApplication
    print("[OK] PySide6 imported successfully")
    
    print("[STEP 2] Creating QApplication...")
    app = QApplication(sys.argv)
    print("[OK] QApplication created")
    
    print("[STEP 3] Importing MainWindow...")
    from ui.main import MainWindow
    print("[OK] MainWindow imported")
    
    print("[STEP 4] Creating MainWindow instance...")
    try:
        window = MainWindow()
        print("[OK] MainWindow created successfully")
        print(f"[INFO] Window size: {window.width()}x{window.height()}")
    except Exception as e:
        print(f"[ERROR] Failed to create MainWindow: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("\n" + "=" * 80)
        print("Press Enter to exit...")
        input()
        sys.exit(1)
    
    print("[STEP 5] Setting window properties...")
    window.setMinimumSize(1000, 700)
    window.resize(1400, 800)
    window.setWindowTitle("AI Tuner Agent - Demo Mode (Safe)")
    print("[OK] Window properties set")
    
    print("[STEP 6] Showing window...")
    window.setVisible(True)
    window.show()
    window.raise_()
    window.activateWindow()
    print("[OK] Window shown")
    
    # Process events
    app.processEvents()
    
    print("\n" + "=" * 80)
    print("DEMO LAUNCHED SUCCESSFULLY!")
    print("=" * 80)
    print("Window should be visible now.")
    print("Close the window or press Ctrl+C to exit.")
    print("=" * 80)
    print()
    
    # Run application
    exit_code = app.exec()
    print(f"\nApplication exited with code: {exit_code}")
    
except KeyboardInterrupt:
    print("\n[INFO] Interrupted by user")
    sys.exit(0)
except Exception as e:
    print(f"\n[FATAL ERROR] Unhandled exception: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    print("\n" + "=" * 80)
    print("Press Enter to exit...")
    input()
    sys.exit(1)
finally:
    tee.close()
    print("\nError log saved to:", error_log)





