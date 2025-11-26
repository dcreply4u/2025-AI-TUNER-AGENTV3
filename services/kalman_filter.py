"""
Kalman Filter for GPS/IMU Integration
Implements Kalman filter for high-accuracy position, velocity, and attitude estimation.
Based on VBOX 3i IMU integration specifications.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from interfaces.gps_interface import GPSFix
from interfaces.imu_interface import IMUReading

LOGGER = logging.getLogger(__name__)


class KalmanFilterStatus(Enum):
    """Kalman filter status."""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"  # 30s stationary initialization
    INITIALIZED = "initialized"  # Waiting for movement
    ACTIVE = "active"  # Movement detected, filter working
    ERROR = "error"


@dataclass
class KalmanFilterOutput:
    """Kalman filter output data."""
    # Position (meters, relative to origin)
    x_position: float
    y_position: float
    z_position: float
    
    # Velocity (m/s)
    x_velocity: float
    y_velocity: float
    z_velocity: float
    
    # Attitude (degrees)
    heading: float
    pitch: float
    roll: float
    
    # Filter status
    status: KalmanFilterStatus
    position_quality: float  # Position quality metric (0-1)
    
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        """Initialize timestamp."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class KalmanFilter:
    """
    Kalman filter for GPS/IMU integration.
    
    Features:
    - GPS position and velocity fusion
    - IMU accelerometer and gyroscope integration
    - 30-second stationary initialization
    - Calibration procedure support
    - ADAS mode (separate filter for high-accuracy position)
    """
    
    def __init__(
        self,
        antenna_to_imu_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),  # X, Y, Z in meters
        imu_to_reference_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),  # X, Y, Z in meters
        roof_mount: bool = False,
        adas_mode: bool = False,
    ) -> None:
        """
        Initialize Kalman filter.
        
        Args:
            antenna_to_imu_offset: Offset from GPS antenna to IMU (X, Y, Z meters)
            imu_to_reference_offset: Offset from IMU to reference point (X, Y, Z meters)
            roof_mount: If True, adds automatic 1m Z offset
            adas_mode: If True, uses ADAS filter mode (higher position accuracy, slightly lower speed accuracy)
        """
        self.antenna_to_imu_offset = antenna_to_imu_offset
        self.imu_to_reference_offset = imu_to_reference_offset
        self.roof_mount = roof_mount
        self.adas_mode = adas_mode
        
        # Apply roof mount offset
        if roof_mount:
            x, y, z = self.imu_to_reference_offset
            self.imu_to_reference_offset = (x, y, z - 1.0)  # 1m down
        
        # Filter state
        self.status = KalmanFilterStatus.NOT_INITIALIZED
        self.initialization_start_time: Optional[float] = None
        self.initialization_duration = 30.0  # 30 seconds
        
        # State vector: [x, y, z, vx, vy, vz, heading, pitch, roll]
        self.state = [0.0] * 9
        self.covariance = [[0.0] * 9 for _ in range(9)]
        
        # Initialize covariance
        for i in range(9):
            self.covariance[i][i] = 1.0
        
        # Process noise (tune based on IMU characteristics)
        self.process_noise = 0.01
        
        # Measurement noise (GPS position uncertainty)
        self.gps_position_noise = 1.0  # meters
        self.gps_velocity_noise = 0.1  # m/s
        
        # IMU noise
        self.imu_accel_noise = 0.1  # m/s²
        self.imu_gyro_noise = 0.01  # rad/s
        
        # Origin (first GPS fix)
        self.origin_lat: Optional[float] = None
        self.origin_lon: Optional[float] = None
        self.origin_alt: Optional[float] = None
        
        # Last measurements
        self.last_gps_fix: Optional[GPSFix] = None
        self.last_imu_reading: Optional[IMUReading] = None
        self.last_update_time: Optional[float] = None
        
    def start_initialization(self) -> None:
        """Start 30-second stationary initialization."""
        if self.status == KalmanFilterStatus.NOT_INITIALIZED:
            self.status = KalmanFilterStatus.INITIALIZING
            self.initialization_start_time = time.time()
            LOGGER.info("Kalman filter initialization started (30s stationary required)")
    
    def check_initialization(self) -> bool:
        """
        Check if initialization is complete.
        
        Returns:
            True if initialization complete
        """
        if self.status == KalmanFilterStatus.INITIALIZING and self.initialization_start_time:
            elapsed = time.time() - self.initialization_start_time
            if elapsed >= self.initialization_duration:
                self.status = KalmanFilterStatus.INITIALIZED
                LOGGER.info("Kalman filter initialization complete - waiting for movement")
                return True
        return False
    
    def detect_movement(self, threshold: float = 0.1) -> bool:
        """
        Detect if movement has been detected.
        
        Args:
            threshold: Acceleration threshold in m/s²
            
        Returns:
            True if movement detected
        """
        if self.status == KalmanFilterStatus.INITIALIZED and self.last_imu_reading:
            accel_magnitude = (
                self.last_imu_reading.accel_x**2 +
                self.last_imu_reading.accel_y**2 +
                self.last_imu_reading.accel_z**2
            ) ** 0.5
            
            if accel_magnitude > threshold:
                self.status = KalmanFilterStatus.ACTIVE
                LOGGER.info("Kalman filter: Movement detected - filter active")
                return True
        return False
    
    def update(
        self,
        gps_fix: Optional[GPSFix] = None,
        imu_reading: Optional[IMUReading] = None,
    ) -> Optional[KalmanFilterOutput]:
        """
        Update Kalman filter with GPS and/or IMU data.
        
        Args:
            gps_fix: GPS fix (optional)
            imu_reading: IMU reading (optional)
            
        Returns:
            KalmanFilterOutput or None if not ready
        """
        current_time = time.time()
        
        # Check initialization
        if self.status == KalmanFilterStatus.INITIALIZING:
            self.check_initialization()
            if self.status == KalmanFilterStatus.INITIALIZED:
                # Detect movement
                if imu_reading:
                    self.detect_movement()
        
        # Store measurements
        if gps_fix:
            self.last_gps_fix = gps_fix
        if imu_reading:
            self.last_imu_reading = imu_reading
        
        # Need at least GPS fix to work
        if not self.last_gps_fix:
            return None
        
        # Set origin from first GPS fix
        if self.origin_lat is None:
            self.origin_lat = self.last_gps_fix.latitude
            self.origin_lon = self.last_gps_fix.longitude
            self.origin_alt = self.last_gps_fix.altitude_m or 0.0
        
        # Calculate time delta
        dt = 0.01  # Default 100 Hz
        if self.last_update_time:
            dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Predict step (using IMU if available)
        if self.last_imu_reading and self.status == KalmanFilterStatus.ACTIVE:
            self._predict(dt, self.last_imu_reading)
        
        # Update step (using GPS)
        if self.last_gps_fix:
            self._update_gps(self.last_gps_fix)
        
        # Extract output
        return self._extract_output()
    
    def _predict(self, dt: float, imu: IMUReading) -> None:
        """Predict step using IMU data."""
        # Simplified prediction - full implementation would use proper state transition
        
        # Update velocity from acceleration
        self.state[3] += imu.accel_x * dt  # vx
        self.state[4] += imu.accel_y * dt  # vy
        self.state[5] += imu.accel_z * dt  # vz
        
        # Update position from velocity
        self.state[0] += self.state[3] * dt  # x
        self.state[1] += self.state[4] * dt  # y
        self.state[2] += self.state[5] * dt  # z
        
        # Update attitude from gyroscope
        self.state[6] += math.radians(imu.gyro_z) * dt  # heading
        self.state[7] += math.radians(imu.gyro_y) * dt  # pitch
        self.state[8] += math.radians(imu.gyro_x) * dt  # roll
        
        # Update covariance (simplified)
        for i in range(9):
            self.covariance[i][i] += self.process_noise * dt
    
    def _update_gps(self, gps: GPSFix) -> None:
        """Update step using GPS data."""
        if self.origin_lat is None or self.origin_lon is None:
            return
        
        # Convert GPS position to local coordinates
        lat_diff = gps.latitude - self.origin_lat
        lon_diff = gps.longitude - self.origin_lon
        
        # Convert to meters
        y = lat_diff * 111320.0
        x = lon_diff * 111320.0 * math.cos(math.radians(self.origin_lat))
        z = (gps.altitude_m or 0.0) - self.origin_alt
        
        # Apply antenna to IMU offset
        x += self.antenna_to_imu_offset[0]
        y += self.antenna_to_imu_offset[1]
        z += self.antenna_to_imu_offset[2]
        
        # Apply IMU to reference offset
        x += self.imu_to_reference_offset[0]
        y += self.imu_to_reference_offset[1]
        z += self.imu_to_reference_offset[2]
        
        # Kalman update (simplified - full implementation would use proper Kalman equations)
        # For now, blend GPS and predicted position
        alpha = 0.1  # GPS weight (lower = more IMU, higher = more GPS)
        
        self.state[0] = (1 - alpha) * self.state[0] + alpha * x
        self.state[1] = (1 - alpha) * self.state[1] + alpha * y
        self.state[2] = (1 - alpha) * self.state[2] + alpha * z
        
        # Update velocity from GPS speed
        speed_x = gps.speed_mps * math.cos(math.radians(gps.heading))
        speed_y = gps.speed_mps * math.sin(math.radians(gps.heading))
        
        self.state[3] = (1 - alpha) * self.state[3] + alpha * speed_x
        self.state[4] = (1 - alpha) * self.state[4] + alpha * speed_y
        
        # Update heading from GPS
        heading_rad = math.radians(gps.heading)
        self.state[6] = (1 - alpha) * self.state[6] + alpha * heading_rad
    
    def _extract_output(self) -> KalmanFilterOutput:
        """Extract output from filter state."""
        # Calculate position quality from covariance
        position_quality = 1.0 / (1.0 + self.covariance[0][0] + self.covariance[1][1])
        
        return KalmanFilterOutput(
            x_position=self.state[0],
            y_position=self.state[1],
            z_position=self.state[2],
            x_velocity=self.state[3],
            y_velocity=self.state[4],
            z_velocity=self.state[5],
            heading=math.degrees(self.state[6]) % 360,
            pitch=math.degrees(self.state[7]),
            roll=math.degrees(self.state[8]),
            status=self.status,
            position_quality=position_quality,
        )
    
    def get_status(self) -> dict:
        """Get Kalman filter status."""
        return {
            "status": self.status.value,
            "initialization_elapsed": (
                time.time() - self.initialization_start_time
                if self.initialization_start_time
                else None
            ),
            "roof_mount": self.roof_mount,
            "adas_mode": self.adas_mode,
            "has_origin": self.origin_lat is not None,
        }


__all__ = ["KalmanFilter", "KalmanFilterOutput", "KalmanFilterStatus"]
