"""
USB Camera Management Tab
UI for managing and configuring USB cameras with auto-detection
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QSpinBox,
    QGroupBox,
    QMessageBox,
    QTextEdit,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
from ui.racing_ui_theme import get_racing_stylesheet, RacingColor

try:
    from services.usb_camera_manager import (
        USBCameraManager,
        USBCameraInfo,
        CameraVendor,
        CameraDriver,
    )
    import cv2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    USBCameraManager = None  # type: ignore
    USBCameraInfo = None  # type: ignore
    CameraVendor = None  # type: ignore
    CameraDriver = None  # type: ignore
    cv2 = None  # type: ignore


class USBCameraTab(QWidget):
    """USB camera management tab."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        
        # Initialize USB camera manager
        self.camera_manager: Optional[USBCameraManager] = None
        if CAMERA_AVAILABLE and USBCameraManager:
            try:
                self.camera_manager = USBCameraManager()
                self.camera_manager.detect_all_cameras()
            except Exception as e:
                print(f"Failed to initialize camera manager: {e}")
        
        self.preview_timers: Dict[str, QTimer] = {}
        self.setup_ui()
        self._update_cameras_table()
        
        # Start auto-detection timer
        self.detection_timer = QTimer(self)
        self.detection_timer.timeout.connect(self._refresh_cameras)
        self.detection_timer.start(10000)  # Refresh every 10 seconds
    
    def setup_ui(self) -> None:
        """Setup USB camera tab."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        spacing = self.scaler.get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Title
        title = QLabel("USB Camera Manager - Auto-Detection & Configuration")
        title_font = self.scaler.get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: {RacingColor.ACCENT_NEON_BLUE.value};")
        main_layout.addWidget(title)
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh Detection")
        btn_padding_v = self.scaler.get_scaled_size(5)
        btn_padding_h = self.scaler.get_scaled_size(15)
        btn_font = self.scaler.get_scaled_font_size(11)
        refresh_btn.setStyleSheet(get_racing_stylesheet("button_primary"))
        refresh_btn.clicked.connect(self._refresh_cameras)
        controls_layout.addWidget(refresh_btn)
        
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)
        
        # Main content
        content_layout = QHBoxLayout()
        
        # Left: Cameras table
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        cameras_label = QLabel("Detected USB Cameras")
        cameras_label.setStyleSheet(f"font-size: {self.scaler.get_scaled_font_size(14)}px; font-weight: bold; color: #ffffff;")
        left_layout.addWidget(cameras_label)
        
        self.cameras_table = QTableWidget()
        self.cameras_table.setColumnCount(7)
        self.cameras_table.setHorizontalHeaderLabels([
            "Device ID", "Vendor", "Model", "Driver", "Resolution", "FPS", "Actions"
        ])
        self.cameras_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cameras_table.setMinimumHeight(self.scaler.get_scaled_size(400))
        self.cameras_table.setStyleSheet(get_racing_stylesheet("table"))
        self.cameras_table.itemDoubleClicked.connect(self._on_camera_selected)
        left_layout.addWidget(self.cameras_table)
        
        content_layout.addWidget(left_panel, stretch=2)
        
        # Right: Camera details and preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # Camera details
        details_group = QGroupBox("Camera Details")
        details_group.setStyleSheet(get_racing_stylesheet("group_box"))
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_font = self.scaler.get_scaled_font_size(11)
        self.details_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: {details_font}px;
                border: 1px solid #404040;
            }}
        """)
        self.details_text.setMinimumHeight(self.scaler.get_scaled_size(200))
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        right_layout.addWidget(details_group)
        
        # Preview
        preview_group = QGroupBox("Live Preview")
        preview_group.setStyleSheet(get_racing_stylesheet("group_box"))
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("No camera selected")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(
            self.scaler.get_scaled_size(320),
            self.scaler.get_scaled_size(240)
        )
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #0a0a0a;
                color: #606060;
                border: 2px solid #404040;
                font-size: 14px;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        
        preview_controls = QHBoxLayout()
        
        start_preview_btn = QPushButton("Start Preview")
        start_preview_btn.setStyleSheet(get_racing_stylesheet("button_primary"))
        start_preview_btn.clicked.connect(self._start_preview)
        preview_controls.addWidget(start_preview_btn)
        
        stop_preview_btn = QPushButton("Stop Preview")
        stop_preview_btn.setStyleSheet(get_racing_stylesheet("button_danger"))
        stop_preview_btn.clicked.connect(self._stop_preview)
        preview_controls.addWidget(stop_preview_btn)
        
        preview_controls.addStretch()
        preview_layout.addLayout(preview_controls)
        
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        content_layout.addWidget(right_panel, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #00ff00; font-size: 11px;")
        main_layout.addWidget(self.status_label)
    
    def _refresh_cameras(self) -> None:
        """Refresh camera detection."""
        if self.camera_manager:
            self.camera_manager.detect_all_cameras()
            self._update_cameras_table()
            self.status_label.setText(f"Detected {len(self.camera_manager.list_cameras())} cameras")
    
    def _update_cameras_table(self) -> None:
        """Update cameras table."""
        if not self.camera_manager:
            return
        
        cameras = self.camera_manager.list_cameras()
        self.cameras_table.setRowCount(len(cameras))
        
        for row, camera in enumerate(cameras):
            self.cameras_table.setItem(row, 0, QTableWidgetItem(camera.device_id))
            
            vendor_str = camera.vendor.value if hasattr(camera.vendor, 'value') else str(camera.vendor)
            vendor_item = QTableWidgetItem(vendor_str)
            if camera.vendor == CameraVendor.LOGITECH:
                vendor_item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_BLUE.value)))
            elif camera.vendor == CameraVendor.MICROSOFT:
                vendor_item.setForeground(QBrush(QColor(RacingColor.ACCENT_NEON_GREEN.value)))
            self.cameras_table.setItem(row, 1, vendor_item)
            
            self.cameras_table.setItem(row, 2, QTableWidgetItem(camera.model))
            
            driver_str = camera.driver.value if hasattr(camera.driver, 'value') else str(camera.driver)
            self.cameras_table.setItem(row, 3, QTableWidgetItem(driver_str))
            
            # Resolution
            if camera.supported_resolutions:
                max_res = max(camera.supported_resolutions, key=lambda x: x[0] * x[1])
                res_str = f"{max_res[0]}x{max_res[1]}"
            else:
                res_str = "Unknown"
            self.cameras_table.setItem(row, 4, QTableWidgetItem(res_str))
            
            self.cameras_table.setItem(row, 5, QTableWidgetItem(str(camera.max_fps)))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            preview_btn = QPushButton("Preview")
            preview_btn.setStyleSheet("background-color: #0080ff; color: #ffffff; padding: 2px 8px; font-size: 9px;")
            preview_btn.clicked.connect(lambda checked, c=camera: self._show_camera_details(c))
            actions_layout.addWidget(preview_btn)
            
            self.cameras_table.setCellWidget(row, 6, actions_widget)
    
    def _on_camera_selected(self, item: QTableWidgetItem) -> None:
        """Handle camera selection."""
        row = item.row()
        device_id = self.cameras_table.item(row, 0).text()
        
        if self.camera_manager:
            camera = self.camera_manager.get_camera_info(device_id)
            if camera:
                self._show_camera_details(camera)
    
    def _show_camera_details(self, camera: USBCameraInfo) -> None:
        """Show camera details."""
        details = f"""
Camera Information:
===================

Device ID: {camera.device_id}
Vendor: {camera.vendor.value if hasattr(camera.vendor, 'value') else camera.vendor}
Model: {camera.model}
Driver: {camera.driver.value if hasattr(camera.driver, 'value') else camera.driver}

Capabilities:
  Max FPS: {camera.max_fps}
  UVC Compliant: {camera.is_uvc}
  
Supported Resolutions:
"""
        for res in camera.supported_resolutions:
            details += f"  {res[0]}x{res[1]}\n"
        
        if camera.vendor_id:
            details += f"\nVendor ID: {camera.vendor_id}\n"
        if camera.product_id:
            details += f"Product ID: {camera.product_id}\n"
        if camera.device_path:
            details += f"Device Path: {camera.device_path}\n"
        
        self.details_text.setText(details)
        self._current_camera = camera
    
    def _start_preview(self) -> None:
        """Start camera preview."""
        if not hasattr(self, '_current_camera') or not self._current_camera:
            QMessageBox.warning(self, "No Camera", "Please select a camera first.")
            return
        
        if not CAMERA_AVAILABLE or not cv2:
            QMessageBox.warning(self, "OpenCV Not Available", "OpenCV is required for camera preview.")
            return
        
        camera = self._current_camera
        device_id = camera.device_id
        
        # Open camera
        cap = self.camera_manager.open_camera(device_id, width=640, height=480, fps=30)
        if not cap:
            QMessageBox.warning(self, "Error", f"Failed to open camera {device_id}")
            return
        
        # Start preview timer
        if device_id in self.preview_timers:
            self.preview_timers[device_id].stop()
        
        preview_timer = QTimer(self)
        preview_timer.timeout.connect(lambda: self._update_preview(device_id, cap))
        preview_timer.start(33)  # ~30 FPS
        self.preview_timers[device_id] = preview_timer
        
        self.status_label.setText(f"Previewing: {camera.model}")
    
    def _update_preview(self, device_id: str, cap: any) -> None:
        """Update camera preview."""
        if not cv2:
            return
        
        ret, frame = cap.read()
        if ret:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize for preview
            height, width = rgb_frame.shape[:2]
            max_width = self.scaler.get_scaled_size(320)
            max_height = self.scaler.get_scaled_size(240)
            
            if width > max_width or height > max_height:
                scale = min(max_width / width, max_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                rgb_frame = cv2.resize(rgb_frame, (new_width, new_height))
            
            # Convert to QImage
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Display
            pixmap = QPixmap.fromImage(qt_image)
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setText("")
    
    def _stop_preview(self) -> None:
        """Stop camera preview."""
        if not hasattr(self, '_current_camera') or not self._current_camera:
            return
        
        device_id = self._current_camera.device_id
        
        # Stop timer
        if device_id in self.preview_timers:
            self.preview_timers[device_id].stop()
            del self.preview_timers[device_id]
        
        # Close camera
        if self.camera_manager:
            self.camera_manager.close_camera(device_id)
        
        self.preview_label.clear()
        self.preview_label.setText("No camera selected")
        self.status_label.setText("Preview stopped")
    
    def closeEvent(self, event) -> None:
        """Cleanup on close."""
        # Stop all previews
        for device_id in list(self.preview_timers.keys()):
            self._stop_preview()
        event.accept()
















