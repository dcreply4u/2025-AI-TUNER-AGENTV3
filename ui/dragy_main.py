from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from controllers.dragy_controller import DragyController
from interfaces import GPSInterface
from services import PerformanceTracker
from ui.dragy_view import DragyView


class DragyWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Tuner Dragy Mode")
        self.resize(1024, 600)

        layout = QVBoxLayout(self)
        self.dragy_view = DragyView()
        layout.addWidget(self.dragy_view, 1)

        button_row = QHBoxLayout()
        self.start_btn = QPushButton("Start GPS")
        self.stop_btn = QPushButton("Stop")
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        button_row.addWidget(self.start_btn)
        button_row.addWidget(self.stop_btn)
        layout.addLayout(button_row)

        self.controller = DragyController(
            view=self.dragy_view,
            gps=GPSInterface(),
            tracker=PerformanceTracker(),
            parent=self,
        )

    def start(self) -> None:
        self.controller.start()

    def stop(self) -> None:
        self.controller.stop()


def run() -> None:
    app = QApplication(sys.argv)
    window = DragyWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()

