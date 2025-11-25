"""
Minimal Demo - Just shows basic UI without heavy initialization
"""
import sys
import os

# Set demo mode to skip hardware
os.environ["AITUNER_DEMO_MODE"] = "true"
os.environ["QT_LOGGING_RULES"] = "*.debug=false"

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QProgressBar
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
import random

class MinimalDemo(QWidget):
    """Minimal demo showing core UI without heavy services."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Tuner Agent - Demo")
        self.resize(1200, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #eaeaea;
                font-family: 'Segoe UI', Arial;
            }
            QFrame {
                background-color: #16213e;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e94560;
            }
            QProgressBar {
                border: 2px solid #0f3460;
                border-radius: 5px;
                text-align: center;
                background-color: #16213e;
            }
            QProgressBar::chunk {
                background-color: #e94560;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("🏎️ AI Tuner Agent - Demo Mode")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #e94560; padding: 20px;")
        layout.addWidget(header)
        
        # Main content
        content = QHBoxLayout()
        
        # Left panel - Telemetry
        left = QFrame()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("📊 Live Telemetry"))
        
        self.rpm_label = QLabel("RPM: 0")
        self.rpm_label.setFont(QFont("Segoe UI", 18))
        left_layout.addWidget(self.rpm_label)
        
        self.rpm_bar = QProgressBar()
        self.rpm_bar.setMaximum(8000)
        left_layout.addWidget(self.rpm_bar)
        
        self.speed_label = QLabel("Speed: 0 mph")
        self.speed_label.setFont(QFont("Segoe UI", 18))
        left_layout.addWidget(self.speed_label)
        
        self.temp_label = QLabel("Coolant: 180°F")
        self.temp_label.setFont(QFont("Segoe UI", 14))
        left_layout.addWidget(self.temp_label)
        
        self.boost_label = QLabel("Boost: 0.0 psi")
        self.boost_label.setFont(QFont("Segoe UI", 14))
        left_layout.addWidget(self.boost_label)
        
        left_layout.addStretch()
        content.addWidget(left)
        
        # Right panel - AI Insights
        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("🤖 AI Insights"))
        
        self.insight_label = QLabel("Analyzing telemetry data...")
        self.insight_label.setWordWrap(True)
        self.insight_label.setStyleSheet("padding: 10px; background-color: #0f3460; border-radius: 5px;")
        right_layout.addWidget(self.insight_label)
        
        self.health_label = QLabel("Health Score: 95%")
        self.health_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.health_label.setStyleSheet("color: #27ae60;")
        right_layout.addWidget(self.health_label)
        
        # Buttons
        start_btn = QPushButton("▶ Start Session")
        start_btn.clicked.connect(self.toggle_simulation)
        right_layout.addWidget(start_btn)
        self.start_btn = start_btn
        
        right_layout.addStretch()
        content.addWidget(right)
        
        layout.addLayout(content)
        
        # Status bar
        self.status = QLabel("Status: Ready - Click 'Start Session' to begin simulation")
        self.status.setStyleSheet("padding: 10px; background-color: #0f3460; border-radius: 5px;")
        layout.addWidget(self.status)
        
        # Simulation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.running = False
        self.rpm = 800
        self.speed = 0
        
        # Insights
        self.insights = [
            "✅ Engine running smoothly - all parameters nominal",
            "💡 Tip: Shift at 6500 RPM for optimal performance",
            "📈 Fuel efficiency improved 3% this session",
            "⚠️ Consider checking air filter - slight restriction detected",
            "🎯 Current tune optimized for 91 octane fuel",
            "✅ Transmission temps within optimal range",
            "💡 ECU learning in progress - 78% complete",
        ]
        
    def toggle_simulation(self):
        if self.running:
            self.timer.stop()
            self.running = False
            self.start_btn.setText("▶ Start Session")
            self.status.setText("Status: Session paused")
        else:
            self.timer.start(100)
            self.running = True
            self.start_btn.setText("⏹ Stop Session")
            self.status.setText("Status: Session active - Simulating telemetry data")
    
    def update_simulation(self):
        # Simulate RPM changes
        self.rpm += random.randint(-200, 300)
        self.rpm = max(800, min(7500, self.rpm))
        
        # Simulate speed based on RPM
        self.speed = int(self.rpm / 50)
        
        # Update displays
        self.rpm_label.setText(f"RPM: {self.rpm}")
        self.rpm_bar.setValue(self.rpm)
        self.speed_label.setText(f"Speed: {self.speed} mph")
        
        # Random temp/boost
        temp = 175 + random.randint(0, 20)
        boost = round(random.uniform(0, 15), 1) if self.rpm > 3000 else 0
        self.temp_label.setText(f"Coolant: {temp}°F")
        self.boost_label.setText(f"Boost: {boost} psi")
        
        # Random insights
        if random.random() < 0.02:
            self.insight_label.setText(random.choice(self.insights))


def main():
    print("=" * 60)
    print("AI Tuner Agent - Minimal Demo")
    print("=" * 60)
    print("Starting lightweight demo...")
    
    app = QApplication(sys.argv)
    window = MinimalDemo()
    window.show()
    
    print("Demo window launched!")
    print("Close the window to exit.")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


