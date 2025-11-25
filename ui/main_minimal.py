"""
Minimal MainWindow - Builds up widgets incrementally to find the crash
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
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MinimalMainWindow(QWidget):
    """Minimal main window that builds up incrementally."""
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Tuner Agent - Minimal")
        self.resize(1400, 800)
        
        print("[MINIMAL] Creating basic layout...")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)
        
        # Header
        print("[MINIMAL] Adding header...")
        hero = QWidget()
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("TelemetryIQ Command Center")
        title.setStyleSheet("font-size: 26px; font-weight: 700; color: #0f294d;")
        hero_layout.addWidget(title)
        hero_layout.addStretch()
        
        layout.addWidget(hero)
        
        # Content area
        print("[MINIMAL] Creating content area...")
        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)
        
        # Left side - simple label for now
        left = QVBoxLayout()
        left_label = QLabel("Left Panel - Widgets will be added here")
        left_label.setStyleSheet("padding: 20px; background: #f0f0f0; border-radius: 5px;")
        left.addWidget(left_label)
        left.addStretch()
        content_layout.addLayout(left, stretch=3)
        
        # Right side - simple buttons
        print("[MINIMAL] Creating right panel...")
        right_container = QWidget()
        right_container.setMaximumWidth(300)
        right_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        right = QVBoxLayout(right_container)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(10)
        
        # Test button
        test_btn = QPushButton("Test Button")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        right.addWidget(test_btn)
        
        # Console log button
        console_btn = QPushButton("Console Logs")
        console_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        console_btn.clicked.connect(self.show_console_logs)
        right.addWidget(console_btn)
        
        right.addStretch()
        content_layout.addWidget(right_container, stretch=0)
        
        layout.addLayout(content_layout)
        
        # Status bar
        print("[MINIMAL] Adding status bar...")
        status = QLabel("Status: Ready")
        status.setStyleSheet("padding: 5px; background: #ecf0f1;")
        layout.addWidget(status)
        
        # Basic styling
        self.setStyleSheet("""
            QWidget {
                background-color: #e8e9ea;
            }
        """)
        
        print("[MINIMAL] Window created successfully")
        self._console_log_viewer = None
    
    def show_console_logs(self) -> None:
        """Show console log viewer."""
        try:
            from ui.console_log_viewer import ConsoleLogViewer
            if not self._console_log_viewer:
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
    
    print("[INFO] Creating MinimalMainWindow...")
    try:
        window = MinimalMainWindow()
        print("[SUCCESS] Window created")
        
        window.show()
        window.raise_()
        window.activateWindow()
        
        print("[SUCCESS] Window shown")
        print("[INFO] Application running...")
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"[FATAL] Failed: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()





