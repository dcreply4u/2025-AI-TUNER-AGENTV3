"""
Car Image Upload Widget
Allows users to upload and display an image of their car on the homepage
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
)


class CarImageWidget(QWidget):
    """Widget for uploading and displaying a car image."""
    
    # Default image storage directory
    IMAGE_DIR = Path(__file__).parent.parent / "user_data" / "images"
    DEFAULT_IMAGE_PATH = IMAGE_DIR / "car_image.jpg"
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.image_path: Optional[Path] = None
        self.setup_ui()
        self.load_saved_image()
        
    def setup_ui(self) -> None:
        """Setup UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Your Vehicle")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #0f294d;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Image display area - use a container to prevent button overlap
        image_container = QWidget()
        image_container_layout = QVBoxLayout(image_container)
        image_container_layout.setContentsMargins(0, 0, 0, 0)
        image_container_layout.setSpacing(0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(300, 200)
        self.image_label.setMaximumSize(400, 300)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f5f7fa;
                border: 2px dashed #d5dce5;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.image_label.setText("No image uploaded\nClick 'Upload Image' to add your vehicle")
        self.image_label.setWordWrap(True)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_container_layout.addWidget(self.image_label, stretch=1)
        
        # Button layout - positioned below image, not overlapping
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(5, 5, 5, 5)
        
        # Upload button
        self.upload_btn = QPushButton("Upload Image")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.upload_btn.clicked.connect(self.upload_image)
        button_layout.addWidget(self.upload_btn)
        
        # Remove button
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.remove_btn.clicked.connect(self.remove_image)
        self.remove_btn.setEnabled(False)
        button_layout.addWidget(self.remove_btn)
        
        # Add button layout to image container (below image)
        image_container_layout.addLayout(button_layout)
        
        # Add image container to main layout
        layout.addWidget(image_container, stretch=1)
        
    def upload_image(self) -> None:
        """Open file dialog to upload an image."""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select Vehicle Image")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                source_path = Path(selected_files[0])
                self.save_and_display_image(source_path)
                
    def save_and_display_image(self, source_path: Path) -> None:
        """Save image to user data directory and display it."""
        try:
            # Ensure image directory exists
            self.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            
            # Copy image to user data directory
            destination = self.DEFAULT_IMAGE_PATH
            shutil.copy2(source_path, destination)
            self.image_path = destination
            
            # Display the image
            self.display_image(destination)
            
            # Enable remove button
            self.remove_btn.setEnabled(True)
            
            QMessageBox.information(
                self,
                "Image Uploaded",
                "Vehicle image uploaded successfully!",
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Upload Failed",
                f"Failed to upload image: {str(e)}",
            )
            
    def display_image(self, image_path: Path) -> None:
        """Display image in the label."""
        try:
            if not image_path.exists():
                return
                
            pixmap = QPixmap(str(image_path))
            
            if pixmap.isNull():
                self.image_label.setText("Failed to load image")
                return
            
            # Scale image to fit label while maintaining aspect ratio
            label_size = self.image_label.size()
            if label_size.width() == 0 or label_size.height() == 0:
                label_size = QSize(300, 200)  # Default size
                
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("")  # Clear placeholder text
            
        except Exception as e:
            print(f"[ERROR] Failed to display image: {e}")
            self.image_label.setText(f"Error loading image: {str(e)}")
            
    def load_saved_image(self) -> None:
        """Load previously saved image if it exists."""
        if self.DEFAULT_IMAGE_PATH.exists():
            self.image_path = self.DEFAULT_IMAGE_PATH
            self.display_image(self.DEFAULT_IMAGE_PATH)
            self.remove_btn.setEnabled(True)
            
    def remove_image(self) -> None:
        """Remove the uploaded image."""
        reply = QMessageBox.question(
            self,
            "Remove Image",
            "Are you sure you want to remove the vehicle image?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.image_path and self.image_path.exists():
                    self.image_path.unlink()
                    
                self.image_path = None
                self.image_label.clear()
                self.image_label.setText("No image uploaded\nClick 'Upload Image' to add your vehicle")
                self.remove_btn.setEnabled(False)
                
                QMessageBox.information(
                    self,
                    "Image Removed",
                    "Vehicle image removed successfully.",
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Remove Failed",
                    f"Failed to remove image: {str(e)}",
                )
                
    def resizeEvent(self, event) -> None:  # noqa: N802
        """Resize event to update image scaling."""
        super().resizeEvent(event)
        if self.image_path and self.image_path.exists():
            self.display_image(self.image_path)


__all__ = ["CarImageWidget"]

