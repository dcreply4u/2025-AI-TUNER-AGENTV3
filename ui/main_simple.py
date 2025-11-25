"""
Simplified MainWindow - Minimal version to test basic functionality
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SimpleMainWindow(QWidget):
    """Simplified main window for testing."""
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Tuner Agent - Simple Test")
        self.resize(1400, 800)
        
        # Basic layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("TelemetryIQ Command Center - Simple Test")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Status
        status = QLabel("Window loaded successfully!")
        status.setStyleSheet("font-size: 14px; color: #27ae60; padding: 10px;")
        layout.addWidget(status)
        
        # Test button
        test_btn = QPushButton("Test Button - Click Me")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        test_btn.clicked.connect(lambda: status.setText("Button clicked! Window is working."))
        layout.addWidget(test_btn)
        
        # Add console log button
        console_btn = QPushButton("Open Console Logs")
        console_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        console_btn.clicked.connect(self.show_console_logs)
        layout.addWidget(console_btn)
        
        layout.addStretch()
        
        # Set background
        self.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
            }
        """)
        
        print("[SUCCESS] SimpleMainWindow created successfully")
    
    def show_console_logs(self) -> None:
        """Show console log viewer."""
        try:
            from ui.console_log_viewer import ConsoleLogViewer
            if not hasattr(self, '_console_log_viewer') or not self._console_log_viewer:
                self._console_log_viewer = ConsoleLogViewer(parent=self)
            self._console_log_viewer.show()
            self._console_log_viewer.raise_()
            self._console_log_viewer.activateWindow()
        except Exception as e:
            print(f"[ERROR] Failed to open console logs: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    print("[INFO] Creating SimpleMainWindow...")
    try:
        window = SimpleMainWindow()
        print("[SUCCESS] Window created")
        
        window.show()
        window.raise_()
        window.activateWindow()
        
        print("[SUCCESS] Window shown")
        print("[INFO] Application running...")
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"[FATAL] Failed to create window: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()





