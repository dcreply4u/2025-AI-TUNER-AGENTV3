"""
Minimal Window Test - Simplest possible window to test if Qt works
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Testing minimal Qt window...")

try:
    from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
    
    app = QApplication(sys.argv)
    
    # Create minimal window
    window = QWidget()
    window.setWindowTitle("Minimal Test Window")
    window.resize(400, 300)
    
    layout = QVBoxLayout(window)
    label = QLabel("If you see this, Qt is working!")
    label.setStyleSheet("font-size: 20px; padding: 20px;")
    layout.addWidget(label)
    
    window.show()
    
    print("Window created and shown. It should be visible now.")
    print("Close the window to exit.")
    
    sys.exit(app.exec())
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
    sys.exit(1)





