"""Simple test to verify window appears on Windows"""
import sys
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Test Window - If you see this, PySide6 works!")
window.resize(400, 200)

layout = QVBoxLayout()
label = QLabel("Window Test\n\nIf you can see this window, PySide6 is working!\nClick the button to test MainWindow.")
label.setStyleSheet("font-size: 14px; padding: 20px;")
layout.addWidget(label)

def test_main():
    try:
        from ui.main import MainWindow
        window.hide()
        main = MainWindow()
        main.show()
        main.raise_()
        main.activateWindow()
        print("MainWindow created and shown!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

btn = QPushButton("Test MainWindow")
btn.clicked.connect(test_main)
layout.addWidget(btn)

window.setLayout(layout)
window.show()
window.raise_()
window.activateWindow()

# Windows-specific: Force to front
try:
    import ctypes
    hwnd = int(window.winId())
    ctypes.windll.user32.SetForegroundWindow(hwnd)
except:
    pass

print("Test window should be visible now!")
print("If you don't see it, try Alt+Tab to find it")
sys.exit(app.exec())
