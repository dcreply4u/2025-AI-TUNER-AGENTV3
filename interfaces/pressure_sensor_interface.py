"""
Pressure Sensor Interface - Integration with existing sensor system

Provides abstraction layer for cylinder pressure sensors that integrates
with the existing sensor management system.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from interfaces.pressure_daq_interface import (
    PressureDAQInterface,
    DAQConfig,
    DAQType,
    PressureSample,
    create_daq_interface,
)
from services.cylinder_pressure_analyzer import (
    CylinderPressureAnalyzer,
    PressureCycle,
    PressureReading,
    CombustionMetrics,
    StabilityMetrics,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class PressureSensorConfig:
    """Configuration for pressure sensor system."""
    daq_config: DAQConfig
    engine_displacement_cc: float = 5000.0
    number_of_cylinders: int = 8
    tdc_sync_enabled: bool = True
    tdc_sync_channel: Optional[int] = None


class PressureSensorInterface:
    """
    Pressure sensor interface that integrates with the sensor management system.
    
    This class bridges the DAQ interface and the pressure analyzer,
    providing a unified interface for the application.
    """
    
    def __init__(self, config: PressureSensorConfig) -> None:
        """
        Initialize pressure sensor interface.
        
        Args:
            config: Pressure sensor configuration
        """
        self.config = config
        self.daq: Optional[PressureDAQInterface] = None
        self.analyzer = CylinderPressureAnalyzer(
            engine_displacement_cc=config.engine_displacement_cc,
            number_of_cylinders=config.number_of_cylinders,
        )
        self.connected = False
        self.acquiring = False
        
        # Thread lock for thread-safe buffer access
        import threading
        self._buffer_lock = threading.Lock()
        
        # Buffer for building cycles
        self.cycle_buffers: Dict[int, List[PressureReading]] = {}
        self.current_crank_angle = 0.0
        self.last_tdc_time = 0.0
        
    def initialize(self) -> bool:
        """
        Initialize and connect to DAQ system.
        
        Returns:
            True if initialization successful
        """
        try:
            self.daq = create_daq_interface(self.config.daq_config)
            if self.daq.connect():
                self.connected = True
                LOGGER.info("Pressure sensor interface initialized")
                return True
            else:
                LOGGER.error("Failed to connect to DAQ")
                return False
        except Exception as e:
            LOGGER.error(f"Failed to initialize pressure sensor: {e}")
            return False
    
    def start_acquisition(self) -> bool:
        """
        Start pressure data acquisition.
        
        Returns:
            True if started successfully
        """
        if not self.connected or not self.daq:
            return False
        
        if self.daq.start_acquisition():
            self.acquiring = True
            LOGGER.info("Started pressure data acquisition")
            return True
        return False
    
    def stop_acquisition(self) -> None:
        """Stop pressure data acquisition."""
        if self.daq:
            self.daq.stop_acquisition()
        self.acquiring = False
        LOGGER.info("Stopped pressure data acquisition")
    
    def disconnect(self) -> None:
        """Disconnect from DAQ system."""
        self.stop_acquisition()
        if self.daq:
            self.daq.disconnect()
        self.connected = False
        LOGGER.info("Disconnected from pressure sensor")
    
    def read_pressure_data(self, max_samples: int = 1000) -> List[PressureSample]:
        """
        Read pressure samples from DAQ.
        
        Args:
            max_samples: Maximum number of samples to read
            
        Returns:
            List of pressure samples
        """
        if not self.daq or not self.acquiring:
            return []
        
        return self.daq.read_samples(max_samples)
    
    def process_samples(
        self,
        samples: List[PressureSample],
        rpm: Optional[float] = None
    ) -> List[PressureCycle]:
        """
        Process pressure samples and build complete cycles.
        
        Args:
            samples: Pressure samples from DAQ
            rpm: Current engine RPM (if available)
            
        Returns:
            List of complete pressure cycles
        """
        cycles = []
        
        with self._buffer_lock:
            for sample in samples:
                # Update crank angle based on TDC sync or time-based estimation
                if sample.tdc_sync:
                    self.current_crank_angle = 0.0
                    self.last_tdc_time = sample.timestamp
                elif rpm and rpm > 0:
                    # Estimate crank angle from time and RPM
                    time_delta = sample.timestamp - self.last_tdc_time
                    angle_delta = (time_delta * rpm * 360.0) / 60.0
                    self.current_crank_angle = (self.current_crank_angle + angle_delta) % 720.0
                
                # Create pressure reading
                reading = PressureReading(
                    crank_angle_deg=self.current_crank_angle,
                    pressure=sample.pressure,
                    timestamp=sample.timestamp,
                    cylinder=sample.channel,
                    rpm=sample.rpm or rpm,
                )
                
                # Add to cycle buffer for this cylinder
                if sample.channel not in self.cycle_buffers:
                    self.cycle_buffers[sample.channel] = []
                
                buffer = self.cycle_buffers[sample.channel]
                buffer.append(reading)
                
                # Check if we have a complete cycle (720 degrees)
                if len(buffer) > 1:
                    first_angle = buffer[0].crank_angle_deg
                    last_angle = buffer[-1].crank_angle_deg
                    
                    # Handle wrap-around
                    if last_angle < first_angle:
                        cycle_span = (360.0 - first_angle) + last_angle
                    else:
                        cycle_span = last_angle - first_angle
                    
                    # If we've covered a full cycle, create cycle object
                    if cycle_span >= 720.0 or (len(buffer) > 100 and sample.tdc_sync):
                        cycle = PressureCycle(
                            cylinder=sample.channel,
                            readings=buffer.copy(),
                            cycle_number=len(cycles) + 1,
                            timestamp_start=buffer[0].timestamp,
                            timestamp_end=buffer[-1].timestamp,
                        )
                        cycles.append(cycle)
                        
                        # Clear buffer (keep last few readings for overlap)
                        self.cycle_buffers[sample.channel] = buffer[-10:]
        
        return cycles
    
    def analyze_cycle(self, cycle: PressureCycle) -> CombustionMetrics:
        """
        Analyze a pressure cycle and return metrics.
        
        Args:
            cycle: Pressure cycle to analyze
            
        Returns:
            CombustionMetrics
        """
        return self.analyzer.add_cycle(cycle)
    
    def get_stability_metrics(self, num_cycles: int = 10) -> StabilityMetrics:
        """
        Get stability metrics for recent cycles.
        
        Args:
            num_cycles: Number of recent cycles to analyze
            
        Returns:
            StabilityMetrics
        """
        return self.analyzer.get_recent_stability(num_cycles)
    
    def calculate_hp_from_imep(self, imep: float, rpm: float) -> float:
        """
        Calculate horsepower from IMEP.
        
        Args:
            imep: Indicated Mean Effective Pressure
            rpm: Engine RPM
            
        Returns:
            Horsepower
        """
        return self.analyzer.calculate_hp_from_imep(imep, rpm)
    
    def get_current_pressure(self, cylinder: int) -> Optional[float]:
        """
        Get current pressure reading for a cylinder.
        
        Args:
            cylinder: Cylinder number (1-based)
            
        Returns:
            Current pressure or None if not available
        """
        with self._buffer_lock:
            if cylinder in self.cycle_buffers and self.cycle_buffers[cylinder]:
                return self.cycle_buffers[cylinder][-1].pressure
        return None
    
    def get_all_current_pressures(self) -> Dict[int, float]:
        """
        Get current pressure readings for all cylinders.
        
        Returns:
            Dictionary mapping cylinder number to pressure
        """
        pressures = {}
        with self._buffer_lock:
            for cylinder in range(1, self.config.number_of_cylinders + 1):
                if cylinder in self.cycle_buffers and self.cycle_buffers[cylinder]:
                    pressures[cylinder] = self.cycle_buffers[cylinder][-1].pressure
        return pressures

