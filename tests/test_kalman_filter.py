"""
Unit tests for Kalman Filter implementation.

Tests the proper Kalman filter mathematics and edge cases.
"""

import math
import time
import unittest
from unittest.mock import Mock

from services.kalman_filter import KalmanFilter, KalmanFilterStatus, KalmanFilterOutput
from interfaces.gps_interface import GPSFix
from interfaces.imu_interface import IMUReading, IMUStatus


class TestKalmanFilter(unittest.TestCase):
    """Test cases for KalmanFilter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.kf = KalmanFilter(
            antenna_to_imu_offset=(0.0, 0.0, 0.0),
            imu_to_reference_offset=(0.0, 0.0, 0.0),
            roof_mount=False,
            adas_mode=False,
        )
    
    def test_initialization(self):
        """Test Kalman filter initialization."""
        self.assertEqual(self.kf.status, KalmanFilterStatus.NOT_INITIALIZED)
        self.assertIsNone(self.kf.origin_lat)
        self.assertIsNone(self.kf.origin_lon)
    
    def test_start_initialization(self):
        """Test initialization start."""
        self.kf.start_initialization()
        self.assertEqual(self.kf.status, KalmanFilterStatus.INITIALIZING)
        self.assertIsNotNone(self.kf.initialization_start_time)
    
    def test_gps_fix_validation(self):
        """Test GPS coordinate validation."""
        # Valid GPS fix
        valid_fix = GPSFix(
            latitude=40.123456,
            longitude=-75.654321,
            speed_mps=10.0,
            heading=45.0,
            timestamp=time.time(),
            altitude_m=100.0,
        )
        
        # Invalid GPS fix (out of range)
        invalid_fix = GPSFix(
            latitude=91.0,  # Invalid
            longitude=-75.654321,
            speed_mps=10.0,
            heading=45.0,
            timestamp=time.time(),
        )
        
        # Test valid fix
        result = self.kf.update(gps_fix=valid_fix)
        self.assertIsNotNone(result)
        self.assertIsNotNone(self.kf.origin_lat)
        
        # Test invalid fix (should be rejected)
        self.kf.origin_lat = None  # Reset
        result = self.kf.update(gps_fix=invalid_fix)
        self.assertIsNone(self.kf.origin_lat)  # Should not set origin
    
    def test_stale_imu_detection(self):
        """Test stale IMU data detection."""
        # Create stale IMU reading (>1 second old)
        stale_imu = IMUReading(
            accel_x=0.0,
            accel_y=0.0,
            accel_z=9.81,
            gyro_x=0.0,
            gyro_y=0.0,
            gyro_z=0.0,
            timestamp=time.time() - 2.0,  # 2 seconds old
            status=IMUStatus.ACTIVE,
        )
        
        # Valid GPS fix
        gps_fix = GPSFix(
            latitude=40.123456,
            longitude=-75.654321,
            speed_mps=10.0,
            heading=45.0,
            timestamp=time.time(),
        )
        
        # Update with stale IMU (should be ignored)
        result = self.kf.update(gps_fix=gps_fix, imu_reading=stale_imu)
        # Should still work with GPS only
        self.assertIsNotNone(result)
    
    def test_time_delta_validation(self):
        """Test time delta validation and clamping."""
        # Valid GPS fix
        gps_fix = GPSFix(
            latitude=40.123456,
            longitude=-75.654321,
            speed_mps=10.0,
            heading=45.0,
            timestamp=time.time(),
        )
        
        # First update (sets origin)
        result1 = self.kf.update(gps_fix=gps_fix)
        self.assertIsNotNone(result1)
        
        # Update with very large time delta (should be clamped)
        # Simulate by manipulating last_update_time
        self.kf.last_update_time = time.time() - 5.0  # 5 seconds ago
        result2 = self.kf.update(gps_fix=gps_fix)
        # Should still work (dt clamped to 1.0)
        self.assertIsNotNone(result2)
    
    def test_kalman_filter_update_cycle(self):
        """Test complete Kalman filter update cycle."""
        # Start initialization
        self.kf.start_initialization()
        
        # Fast-forward initialization
        self.kf.initialization_start_time = time.time() - 31.0
        self.kf.check_initialization()
        self.assertEqual(self.kf.status, KalmanFilterStatus.INITIALIZED)
        
        # Create GPS fix
        gps_fix = GPSFix(
            latitude=40.123456,
            longitude=-75.654321,
            speed_mps=10.0,
            heading=45.0,
            timestamp=time.time(),
            altitude_m=100.0,
        )
        
        # Create IMU reading
        imu_reading = IMUReading(
            accel_x=0.1,
            accel_y=0.05,
            accel_z=9.81,
            gyro_x=0.01,
            gyro_y=0.02,
            gyro_z=0.03,
            timestamp=time.time(),
            status=IMUStatus.ACTIVE,
        )
        
        # First update (sets origin, detects movement)
        result1 = self.kf.update(gps_fix=gps_fix, imu_reading=imu_reading)
        self.assertIsNotNone(result1)
        self.assertEqual(self.kf.status, KalmanFilterStatus.ACTIVE)
        
        # Second update (normal operation)
        time.sleep(0.1)  # Small delay
        gps_fix2 = GPSFix(
            latitude=40.123500,  # Slight movement
            longitude=-75.654350,
            speed_mps=10.5,
            heading=46.0,
            timestamp=time.time(),
            altitude_m=100.0,
        )
        imu_reading2 = IMUReading(
            accel_x=0.2,
            accel_y=0.1,
            accel_z=9.81,
            gyro_x=0.02,
            gyro_y=0.03,
            gyro_z=0.04,
            timestamp=time.time(),
            status=IMUStatus.ACTIVE,
        )
        
        result2 = self.kf.update(gps_fix=gps_fix2, imu_reading=imu_reading2)
        self.assertIsNotNone(result2)
        self.assertIsInstance(result2, KalmanFilterOutput)
        
        # Verify output structure
        self.assertIsNotNone(result2.x_position)
        self.assertIsNotNone(result2.y_position)
        self.assertIsNotNone(result2.x_velocity)
        self.assertIsNotNone(result2.y_velocity)
        self.assertIsNotNone(result2.heading)
        self.assertGreaterEqual(result2.position_quality, 0.0)
        self.assertLessEqual(result2.position_quality, 1.0)
    
    def test_get_status(self):
        """Test get_status method."""
        status = self.kf.get_status()
        self.assertIsInstance(status, dict)
        self.assertIn("status", status)
        self.assertIn("roof_mount", status)
        self.assertIn("adas_mode", status)
        self.assertIn("has_origin", status)
    
    def test_origin_setting(self):
        """Test that origin is set from first GPS fix."""
        gps_fix = GPSFix(
            latitude=40.123456,
            longitude=-75.654321,
            speed_mps=10.0,
            heading=45.0,
            timestamp=time.time(),
        )
        
        self.assertIsNone(self.kf.origin_lat)
        result = self.kf.update(gps_fix=gps_fix)
        self.assertIsNotNone(self.kf.origin_lat)
        self.assertEqual(self.kf.origin_lat, 40.123456)
        self.assertEqual(self.kf.origin_lon, -75.654321)


if __name__ == "__main__":
    unittest.main()

