"""
Video and Data Integration
Overlay data logs onto video footage.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import cv2
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False
    cv2 = None  # type: ignore

LOGGER = logging.getLogger(__name__)


@dataclass
class VideoOverlayConfig:
    """Video overlay configuration."""
    channels: List[str]  # Channels to display
    position: str = "bottom"  # top, bottom, left, right
    font_size: int = 24
    font_color: tuple = (255, 255, 255)  # RGB
    background_color: tuple = (0, 0, 0)  # RGB
    background_alpha: float = 0.7
    show_time: bool = True
    show_cursor: bool = True


class VideoDataIntegrator:
    """
    Video and data integration service.
    
    Features:
    - Overlay telemetry data on video
    - Synchronize video with log data
    - Customizable overlay positions
    - Export video with overlays
    """
    
    def __init__(self):
        """Initialize video data integrator."""
        if not CV_AVAILABLE:
            LOGGER.warning("OpenCV not available - video features limited")
    
    def overlay_data_on_video(
        self,
        video_path: str,
        log_data: Any,  # LogData from universal_log_parser
        output_path: str,
        config: Optional[VideoOverlayConfig] = None,
    ) -> bool:
        """
        Overlay data logs on video.
        
        Args:
            video_path: Input video path
            log_data: Log data to overlay
            output_path: Output video path
            config: Overlay configuration
        
        Returns:
            True if successful
        """
        if not CV_AVAILABLE:
            LOGGER.error("OpenCV required for video overlay")
            return False
        
        if config is None:
            config = VideoOverlayConfig(channels=list(log_data.data.keys())[:5])
        
        try:
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                LOGGER.error("Failed to open video: %s", video_path)
                return False
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_count = 0
            log_times = log_data.time
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate current time in video
                video_time = frame_count / fps
                
                # Find closest log data point
                if log_times:
                    closest_idx = min(
                        range(len(log_times)),
                        key=lambda i: abs(log_times[i] - video_time)
                    )
                    
                    # Overlay data
                    frame = self._draw_overlay(
                        frame,
                        log_data,
                        closest_idx,
                        config,
                        width,
                        height,
                    )
                
                out.write(frame)
                frame_count += 1
            
            cap.release()
            out.release()
            
            LOGGER.info("Video overlay complete: %s", output_path)
            return True
            
        except Exception as e:
            LOGGER.error("Failed to overlay video: %s", e)
            return False
    
    def _draw_overlay(
        self,
        frame: Any,
        log_data: Any,
        data_index: int,
        config: VideoOverlayConfig,
        width: int,
        height: int,
    ) -> Any:
        """Draw data overlay on frame."""
        if not CV_AVAILABLE:
            return frame
        
        # Create overlay background
        overlay = frame.copy()
        
        # Calculate overlay position
        if config.position == "bottom":
            overlay_y = height - 150
            overlay_height = 150
        elif config.position == "top":
            overlay_y = 0
            overlay_height = 150
        else:
            overlay_y = height // 2 - 75
            overlay_height = 150
        
        # Draw semi-transparent background
        cv2.rectangle(
            overlay,
            (0, overlay_y),
            (width, overlay_y + overlay_height),
            config.background_color,
            -1,
        )
        
        # Blend with original frame
        cv2.addWeighted(overlay, config.background_alpha, frame, 1 - config.background_alpha, 0, frame)
        
        # Draw text
        y_offset = overlay_y + 30
        x_offset = 20
        
        # Time
        if config.show_time and data_index < len(log_data.time):
            time_text = f"Time: {log_data.time[data_index]:.2f}s"
            cv2.putText(
                frame,
                time_text,
                (x_offset, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                config.font_size / 30.0,
                config.font_color,
                2,
            )
            y_offset += 30
        
        # Channel values
        for channel in config.channels:
            if channel in log_data.data and data_index < len(log_data.data[channel]):
                value = log_data.data[channel][data_index]
                text = f"{channel}: {value:.2f}"
                cv2.putText(
                    frame,
                    text,
                    (x_offset, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    config.font_size / 30.0,
                    config.font_color,
                    2,
                )
                y_offset += 30
        
        return frame
    
    def sync_video_with_log(
        self,
        video_path: str,
        log_data: Any,
    ) -> Dict[str, Any]:
        """
        Synchronize video with log data.
        
        Args:
            video_path: Video path
            log_data: Log data
        
        Returns:
            Synchronization info
        """
        if not CV_AVAILABLE:
            return {}
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {}
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            log_duration = log_data.time[-1] - log_data.time[0] if log_data.time else 0
            
            return {
                "video_fps": fps,
                "video_duration": duration,
                "log_duration": log_duration,
                "sync_ratio": duration / log_duration if log_duration > 0 else 1.0,
            }
        except Exception as e:
            LOGGER.error("Failed to sync video: %s", e)
            return {}


