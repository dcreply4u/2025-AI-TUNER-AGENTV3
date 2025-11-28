"""
Video Recording and Streaming Tests

Tests video recording, streaming, and overlay functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestVideoRecording:
    """Test video recording functionality."""
    
    def test_camera_interface_import(self):
        """Test camera interface can be imported."""
        try:
            from interfaces.camera_interface import CameraInterface
            assert CameraInterface is not None
        except ImportError:
            pytest.skip("Camera interface not available")
    
    def test_video_logger_import(self):
        """Test video logger can be imported."""
        try:
            from services.video_logger import VideoLogger
            assert VideoLogger is not None
        except ImportError:
            pytest.skip("Video logger not available")
    
    def test_live_streamer_import(self):
        """Test live streamer can be imported."""
        try:
            from services.live_streamer import LiveStreamer, StreamConfig
            assert LiveStreamer is not None
            assert StreamConfig is not None
        except ImportError:
            pytest.skip("Live streamer not available")
    
    def test_stream_config_creation(self):
        """Test stream configuration creation."""
        try:
            from services.live_streamer import StreamConfig, StreamingPlatform
            
            config = StreamConfig(
                platform=StreamingPlatform.YOUTUBE,
                stream_key="test_key",
                bitrate=2500,
                resolution=(1920, 1080),
            )
            
            assert config.platform == StreamingPlatform.YOUTUBE
            assert config.bitrate == 2500
            assert config.resolution == (1920, 1080)
        except ImportError:
            pytest.skip("Live streamer not available")


class TestVideoOverlay:
    """Test video overlay functionality."""
    
    def test_video_overlay_import(self):
        """Test video overlay can be imported."""
        try:
            # Check for video overlay modules
            overlay_modules = [
                "ui.video_overlay_tab",
                "services.video_data_integration",
            ]
            
            imported = False
            for module_name in overlay_modules:
                try:
                    __import__(module_name)
                    imported = True
                    break
                except ImportError:
                    continue
            
            if not imported:
                pytest.skip("Video overlay modules not available")
        except Exception:
            pytest.skip("Video overlay not available")

