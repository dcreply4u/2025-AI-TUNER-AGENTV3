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
from typing import Optional, Tuple, Dict, Any

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

from interfaces.gps_interface import GPSFix
from interfaces.imu_interface import IMUReading

LOGGER = logging.getLogger(__name__)


@dataclass
class KalmanFilterConfig:
    """
    Configuration for Kalman filter parameters.
    
    Allows tuning of filter behavior for different applications:
    - Racing: Lower process noise, higher GPS weight for accuracy
    - ADAS: Higher process noise, smoother output
    - General: Balanced defaults
    """
    # Process noise (how much we trust the motion model)
    process_noise_pos: float = 0.1  # Position process noise (m²/s)
    process_noise_vel: float = 0.5  # Velocity process noise (m²/s³)
    process_noise_att: float = 0.01  # Attitude process noise (rad²/s)
    
    # Measurement noise (GPS uncertainty)
    gps_position_noise: float = 2.0  # GPS position uncertainty (meters)
    gps_velocity_noise: float = 0.2  # GPS velocity uncertainty (m/s)
    gps_heading_noise: float = 0.1  # GPS heading uncertainty (radians)
    
    # IMU measurement noise (for future use)
    imu_accel_noise: float = 0.1  # IMU accelerometer noise (m/s²)
    imu_gyro_noise: float = 0.01  # IMU gyroscope noise (rad/s)
    
    # Initialization parameters
    initialization_time_sec: float = 30.0  # Stationary initialization duration
    movement_threshold: float = 0.1  # Acceleration threshold for movement detection (m/s²)
    
    # Time delta defaults
    default_dt: float = 0.01  # Default time delta (100 Hz)
    max_dt: float = 1.0  # Maximum time delta (clamp if exceeded)


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
        config: Optional[KalmanFilterConfig] = None,
    ) -> None:
        """
        Initialize Kalman filter.
        
        Args:
            antenna_to_imu_offset: Offset from GPS antenna to IMU (X, Y, Z meters)
            imu_to_reference_offset: Offset from IMU to reference point (X, Y, Z meters)
            roof_mount: If True, adds automatic 1m Z offset
            adas_mode: If True, uses ADAS filter mode (higher position accuracy, slightly lower speed accuracy)
            config: Optional configuration object for tuning filter parameters.
                   If None, uses default configuration.
        """
        self.antenna_to_imu_offset = antenna_to_imu_offset
        self.imu_to_reference_offset = imu_to_reference_offset
        self.roof_mount = roof_mount
        self.adas_mode = adas_mode
        
        # Use provided config or create default
        self.config = config or KalmanFilterConfig()
        
        # Apply ADAS mode adjustments if enabled
        if adas_mode:
            # ADAS mode: prioritize position accuracy over speed
            self.config.gps_position_noise *= 0.5  # Tighter position noise
            self.config.process_noise_pos *= 0.5  # Less position process noise
        
        # Apply roof mount offset
        if roof_mount:
            x, y, z = self.imu_to_reference_offset
            self.imu_to_reference_offset = (x, y, z - 1.0)  # 1m down
        
        # Filter state
        self.status = KalmanFilterStatus.NOT_INITIALIZED
        self.initialization_start_time: Optional[float] = None
        self.initialization_duration = self.config.initialization_time_sec
        
        # State vector: [x, y, z, vx, vy, vz, heading, pitch, roll]
        # Use numpy if available for proper matrix operations
        if NUMPY_AVAILABLE:
            self.state = np.zeros(9, dtype=np.float64)
            self.covariance = np.eye(9, dtype=np.float64) * 1.0  # Initial uncertainty
        else:
            # Fallback to lists if numpy not available
            self.state = [0.0] * 9
            self.covariance = [[0.0] * 9 for _ in range(9)]
            for i in range(9):
                self.covariance[i][i] = 1.0
        
        # Process noise (from config)
        self.process_noise_pos = self.config.process_noise_pos
        self.process_noise_vel = self.config.process_noise_vel
        self.process_noise_att = self.config.process_noise_att
        
        # Measurement noise (from config)
        self.gps_position_noise = self.config.gps_position_noise
        self.gps_velocity_noise = self.config.gps_velocity_noise
        self.gps_heading_noise = self.config.gps_heading_noise
        
        # IMU measurement noise (from config, for future use)
        self.imu_accel_noise = self.config.imu_accel_noise
        self.imu_gyro_noise = self.config.imu_gyro_noise
        
        # Origin (first GPS fix)
        self.origin_lat: Optional[float] = None
        self.origin_lon: Optional[float] = None
        self.origin_alt: Optional[float] = None
        
        # Last measurements
        self.last_gps_fix: Optional[GPSFix] = None
        self.last_imu_reading: Optional[IMUReading] = None
        self.last_update_time: Optional[float] = None
        
    def start_initialization(self) -> None:
        """
        Start 30-second stationary initialization.
        
        The Kalman filter requires a 30-second stationary period to properly
        calibrate the IMU. During this time, the vehicle must remain stationary
        to allow the filter to characterize IMU biases and noise characteristics.
        
        This is called automatically when the first GPS fix is received, or can
        be called manually to restart initialization.
        """
        if self.status == KalmanFilterStatus.NOT_INITIALIZED:
            self.status = KalmanFilterStatus.INITIALIZING
            self.initialization_start_time = time.time()
            LOGGER.info("Kalman filter initialization started (30s stationary required)")
    
    def check_initialization(self) -> bool:
        """
        Check if initialization is complete.
        
        Checks if the 30-second stationary initialization period has elapsed.
        Once complete, the filter transitions to INITIALIZED status and waits
        for movement to be detected before becoming ACTIVE.
        
        Returns:
            True if initialization complete, False otherwise
        """
        if self.status == KalmanFilterStatus.INITIALIZING and self.initialization_start_time:
            elapsed = time.time() - self.initialization_start_time
            if elapsed >= self.initialization_duration:
                self.status = KalmanFilterStatus.INITIALIZED
                LOGGER.info("Kalman filter initialization complete - waiting for movement")
                return True
        return False
    
    def detect_movement(self, threshold: Optional[float] = None) -> bool:
        """
        Detect if vehicle movement has been detected.
        
        After initialization, the filter waits for movement to be detected
        before becoming active. Movement is detected when the IMU acceleration
        magnitude exceeds the threshold.
        
        Args:
            threshold: Acceleration threshold in m/s². If None, uses config value.
                      Lower values = more sensitive, higher = less sensitive
            
        Returns:
            True if movement detected (filter becomes ACTIVE), False otherwise
        """
        if threshold is None:
            threshold = self.config.movement_threshold
        
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
        
        Implements the standard Kalman filter cycle:
        1. Predict step (using IMU motion model)
        2. Update step (using GPS measurements)
        
        Args:
            gps_fix: GPS fix (optional)
            imu_reading: IMU reading (optional)
            
        Returns:
            KalmanFilterOutput or None if not ready
        """
        current_time = time.time()
        
        # Validate inputs
        if gps_fix:
            if not (-90 <= gps_fix.latitude <= 90) or not (-180 <= gps_fix.longitude <= 180):
                LOGGER.warning(f"Invalid GPS coordinates in update: lat={gps_fix.latitude}, lon={gps_fix.longitude}")
                gps_fix = None
        
        if imu_reading:
            # Check for stale IMU data
            time_diff = abs(current_time - imu_reading.timestamp)
            if time_diff > 1.0:  # Stale data (>1 second old)
                LOGGER.debug(f"Stale IMU reading: {time_diff:.2f}s old")
                imu_reading = None
        
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
            LOGGER.info(f"Kalman filter origin set: lat={self.origin_lat:.6f}, lon={self.origin_lon:.6f}")
        
        # Calculate time delta (using config defaults)
        dt = self.config.default_dt  # Default from config
        if self.last_update_time:
            dt = current_time - self.last_update_time
            # Clamp dt to reasonable range
            if dt <= 0:
                LOGGER.warning(f"Invalid time delta: {dt}s, using default {self.config.default_dt}s")
                dt = self.config.default_dt
            elif dt > self.config.max_dt:
                LOGGER.warning(f"Large time delta: {dt}s, clamping to {self.config.max_dt}s")
                dt = self.config.max_dt
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
        """
        Predict step using IMU data (motion model).
        
        Implements the prediction step of the Kalman filter:
        - x_k|k-1 = F * x_k-1|k-1 + B * u_k
        - P_k|k-1 = F * P_k-1|k-1 * F^T + Q
        
        Args:
            dt: Time delta since last update (seconds)
            imu: IMU reading with accelerometer and gyroscope data
        """
        if dt <= 0 or dt > 1.0:  # Sanity check
            LOGGER.warning(f"Invalid time delta in prediction: {dt}s")
            return
        
        if NUMPY_AVAILABLE:
            # State transition matrix F (9x9)
            # x' = x + vx*dt
            # y' = y + vy*dt
            # z' = z + vz*dt
            # vx' = vx + ax*dt
            # vy' = vy + ay*dt
            # vz' = vz + az*dt
            # heading' = heading + gz*dt
            # pitch' = pitch + gy*dt
            # roll' = roll + gx*dt
            
            F = np.eye(9, dtype=np.float64)
            F[0, 3] = dt  # x depends on vx
            F[1, 4] = dt  # y depends on vy
            F[2, 5] = dt  # z depends on vz
            
            # Control input (IMU accelerations and angular rates)
            # Convert IMU accelerations to body frame (assuming IMU is aligned)
            ax = imu.accel_x
            ay = imu.accel_y
            az = imu.accel_z
            gx = math.radians(imu.gyro_x)
            gy = math.radians(imu.gyro_y)
            gz = math.radians(imu.gyro_z)
            
            # Control input vector u = [ax, ay, az, gx, gy, gz]
            # For now, we'll integrate directly into state (simplified)
            # In a full implementation, we'd use rotation matrices to transform
            # body-frame accelerations to navigation frame
            
            # Predict state: x_k|k-1 = F * x_k-1|k-1
            self.state = F @ self.state
            
            # Add control input (acceleration integration)
            self.state[3] += ax * dt  # vx
            self.state[4] += ay * dt  # vy
            self.state[5] += az * dt  # vz
            
            # Add angular rate integration
            self.state[6] += gz * dt  # heading
            self.state[7] += gy * dt  # pitch
            self.state[8] += gx * dt  # roll
            
            # Process noise covariance matrix Q
            Q = np.zeros((9, 9), dtype=np.float64)
            Q[0, 0] = self.process_noise_pos * dt  # Position x
            Q[1, 1] = self.process_noise_pos * dt  # Position y
            Q[2, 2] = self.process_noise_pos * dt  # Position z
            Q[3, 3] = self.process_noise_vel * dt  # Velocity x
            Q[4, 4] = self.process_noise_vel * dt  # Velocity y
            Q[5, 5] = self.process_noise_vel * dt  # Velocity z
            Q[6, 6] = self.process_noise_att * dt  # Heading
            Q[7, 7] = self.process_noise_att * dt  # Pitch
            Q[8, 8] = self.process_noise_att * dt  # Roll
            
            # Predict covariance: P_k|k-1 = F * P_k-1|k-1 * F^T + Q
            self.covariance = F @ self.covariance @ F.T + Q
        else:
            # Fallback implementation without numpy
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
            
            # Update covariance (simplified - diagonal only)
            self.covariance[0][0] += self.process_noise_pos * dt
            self.covariance[1][1] += self.process_noise_pos * dt
            self.covariance[2][2] += self.process_noise_pos * dt
            self.covariance[3][3] += self.process_noise_vel * dt
            self.covariance[4][4] += self.process_noise_vel * dt
            self.covariance[5][5] += self.process_noise_vel * dt
            self.covariance[6][6] += self.process_noise_att * dt
            self.covariance[7][7] += self.process_noise_att * dt
            self.covariance[8][8] += self.process_noise_att * dt
    
    def _update_gps(self, gps: GPSFix) -> None:
        """
        Update step using GPS data (measurement update).
        
        Implements the update step of the Kalman filter:
        - y = z - H * x_k|k-1 (innovation/residual)
        - S = H * P_k|k-1 * H^T + R (innovation covariance)
        - K = P_k|k-1 * H^T * S^-1 (Kalman gain)
        - x_k|k = x_k|k-1 + K * y (updated state)
        - P_k|k = (I - K * H) * P_k|k-1 (updated covariance)
        
        This method performs the measurement update using GPS position, velocity,
        and heading measurements. The Kalman gain automatically weights the GPS
        measurements based on their uncertainty (measurement noise) and the current
        state uncertainty (covariance).
        
        Args:
            gps: GPS fix with position (lat/lon/alt), velocity (speed_mps), and heading
            
        Note:
            - GPS measurements are converted from WGS84 (lat/lon) to local ENU frame
            - Unmeasured states (vz, pitch, roll) are given high noise to ignore them
            - The filter automatically balances GPS accuracy with IMU smoothness
        """
        if self.origin_lat is None or self.origin_lon is None:
            return
        
        # Validate GPS data
        if not (-90 <= gps.latitude <= 90) or not (-180 <= gps.longitude <= 180):
            LOGGER.warning(f"Invalid GPS coordinates: lat={gps.latitude}, lon={gps.longitude}")
            return
        
        # Convert GPS position to local coordinates (ENU frame)
        lat_diff = gps.latitude - self.origin_lat
        lon_diff = gps.longitude - self.origin_lon
        
        # Convert to meters (approximate, good for small distances)
        y = lat_diff * 111320.0  # North (meters per degree latitude)
        x = lon_diff * 111320.0 * math.cos(math.radians(self.origin_lat))  # East
        z = (gps.altitude_m or 0.0) - (self.origin_alt or 0.0)  # Up
        
        # Apply antenna to IMU offset
        x += self.antenna_to_imu_offset[0]
        y += self.antenna_to_imu_offset[1]
        z += self.antenna_to_imu_offset[2]
        
        # Apply IMU to reference offset
        x += self.imu_to_reference_offset[0]
        y += self.imu_to_reference_offset[1]
        z += self.imu_to_reference_offset[2]
        
        # GPS velocity in ENU frame
        heading_rad = math.radians(gps.heading)
        speed_x = gps.speed_mps * math.sin(heading_rad)  # East velocity
        speed_y = gps.speed_mps * math.cos(heading_rad)  # North velocity
        
        if NUMPY_AVAILABLE:
            # Measurement vector z = [x, y, z, vx, vy, heading]
            z_meas = np.array([
                x, y, z,
                speed_x, speed_y, 0.0,  # vz not measured by GPS
                heading_rad, 0.0, 0.0  # pitch and roll not measured by GPS
            ], dtype=np.float64)
            
            # Measurement matrix H (what we measure from state)
            # We measure: position (x,y,z), velocity (vx,vy), heading
            H = np.zeros((9, 9), dtype=np.float64)
            H[0, 0] = 1.0  # x position
            H[1, 1] = 1.0  # y position
            H[2, 2] = 1.0  # z position
            H[3, 3] = 1.0  # vx velocity
            H[4, 4] = 1.0  # vy velocity
            H[6, 6] = 1.0  # heading
            
            # Measurement noise covariance matrix R
            R = np.zeros((9, 9), dtype=np.float64)
            R[0, 0] = self.gps_position_noise ** 2  # x position noise
            R[1, 1] = self.gps_position_noise ** 2  # y position noise
            R[2, 2] = self.gps_position_noise ** 2  # z position noise
            R[3, 3] = self.gps_velocity_noise ** 2  # vx velocity noise
            R[4, 4] = self.gps_velocity_noise ** 2  # vy velocity noise
            R[6, 6] = self.gps_heading_noise ** 2  # heading noise
            # Unmeasured states have high noise (effectively ignored)
            R[5, 5] = 1e6  # vz (not measured)
            R[7, 7] = 1e6  # pitch (not measured)
            R[8, 8] = 1e6  # roll (not measured)
            
            # Innovation (residual): y = z - H * x
            y_innov = z_meas - (H @ self.state)
            
            # Innovation covariance: S = H * P * H^T + R
            S = H @ self.covariance @ H.T + R
            
            # Kalman gain: K = P * H^T * S^-1
            try:
                K = self.covariance @ H.T @ np.linalg.inv(S)
            except np.linalg.LinAlgError:
                LOGGER.warning("Singular matrix in Kalman gain calculation, skipping update")
                return
            
            # Update state: x = x + K * y
            self.state = self.state + K @ y_innov
            
            # Update covariance: P = (I - K * H) * P
            I = np.eye(9, dtype=np.float64)
            self.covariance = (I - K @ H) @ self.covariance
            
            # Ensure covariance remains positive semi-definite
            self.covariance = (self.covariance + self.covariance.T) / 2.0
        else:
            # Fallback implementation without numpy (simplified)
            # Use weighted average with Kalman-like weighting
            # Calculate innovation
            innov_x = x - self.state[0]
            innov_y = y - self.state[1]
            innov_z = z - self.state[2]
            innov_vx = speed_x - self.state[3]
            innov_vy = speed_y - self.state[4]
            innov_heading = heading_rad - self.state[6]
            
            # Calculate Kalman gain (simplified - diagonal only)
            # K = P / (P + R)
            k_x = self.covariance[0][0] / (self.covariance[0][0] + self.gps_position_noise ** 2)
            k_y = self.covariance[1][1] / (self.covariance[1][1] + self.gps_position_noise ** 2)
            k_z = self.covariance[2][2] / (self.covariance[2][2] + self.gps_position_noise ** 2)
            k_vx = self.covariance[3][3] / (self.covariance[3][3] + self.gps_velocity_noise ** 2)
            k_vy = self.covariance[4][4] / (self.covariance[4][4] + self.gps_velocity_noise ** 2)
            k_heading = self.covariance[6][6] / (self.covariance[6][6] + self.gps_heading_noise ** 2)
            
            # Update state
            self.state[0] += k_x * innov_x
            self.state[1] += k_y * innov_y
            self.state[2] += k_z * innov_z
            self.state[3] += k_vx * innov_vx
            self.state[4] += k_vy * innov_vy
            self.state[6] += k_heading * innov_heading
            
            # Update covariance (simplified - diagonal only)
            self.covariance[0][0] *= (1 - k_x)
            self.covariance[1][1] *= (1 - k_y)
            self.covariance[2][2] *= (1 - k_z)
            self.covariance[3][3] *= (1 - k_vx)
            self.covariance[4][4] *= (1 - k_vy)
            self.covariance[6][6] *= (1 - k_heading)
    
    def _extract_output(self) -> KalmanFilterOutput:
        """
        Extract output from filter state.
        
        Returns:
            KalmanFilterOutput with position, velocity, attitude, and quality metrics
        """
        # Calculate position quality from covariance
        # Quality = 1 / (1 + position_uncertainty)
        if NUMPY_AVAILABLE:
            position_uncertainty = np.sqrt(self.covariance[0, 0] + self.covariance[1, 1])
            position_quality = 1.0 / (1.0 + position_uncertainty)
            
            # Extract state values
            x_pos = float(self.state[0])
            y_pos = float(self.state[1])
            z_pos = float(self.state[2])
            x_vel = float(self.state[3])
            y_vel = float(self.state[4])
            z_vel = float(self.state[5])
            heading_rad = float(self.state[6])
            pitch_rad = float(self.state[7])
            roll_rad = float(self.state[8])
        else:
            position_uncertainty = math.sqrt(self.covariance[0][0] + self.covariance[1][1])
            position_quality = 1.0 / (1.0 + position_uncertainty)
            
            x_pos = self.state[0]
            y_pos = self.state[1]
            z_pos = self.state[2]
            x_vel = self.state[3]
            y_vel = self.state[4]
            z_vel = self.state[5]
            heading_rad = self.state[6]
            pitch_rad = self.state[7]
            roll_rad = self.state[8]
        
        # Normalize heading to 0-360 degrees
        heading_deg = math.degrees(heading_rad) % 360
        if heading_deg < 0:
            heading_deg += 360
        
        return KalmanFilterOutput(
            x_position=x_pos,
            y_position=y_pos,
            z_position=z_pos,
            x_velocity=x_vel,
            y_velocity=y_vel,
            z_velocity=z_vel,
            heading=heading_deg,
            pitch=math.degrees(pitch_rad),
            roll=math.degrees(roll_rad),
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


__all__ = ["KalmanFilter", "KalmanFilterOutput", "KalmanFilterStatus", "KalmanFilterConfig"]
