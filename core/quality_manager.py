"""
ISO/IEC 25010 Software Quality Management
Software quality characteristics and metrics.
"""

from __future__ import annotations

import logging
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
import statistics

LOGGER = logging.getLogger(__name__)


class QualityCharacteristic(Enum):
    """ISO/IEC 25010 Quality Characteristics."""
    FUNCTIONAL_SUITABILITY = "functional_suitability"
    PERFORMANCE_EFFICIENCY = "performance_efficiency"
    COMPATIBILITY = "compatibility"
    USABILITY = "usability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    PORTABILITY = "portability"


class QualityMetric(Enum):
    """Quality metrics."""
    # Functional Suitability
    FUNCTIONAL_COMPLETENESS = "functional_completeness"
    FUNCTIONAL_CORRECTNESS = "functional_correctness"
    FUNCTIONAL_APPROPRIATENESS = "functional_appropriateness"
    
    # Performance Efficiency
    TIME_BEHAVIOR = "time_behavior"
    RESOURCE_UTILIZATION = "resource_utilization"
    CAPACITY = "capacity"
    
    # Reliability
    MATURITY = "maturity"
    AVAILABILITY = "availability"
    FAULT_TOLERANCE = "fault_tolerance"
    RECOVERABILITY = "recoverability"
    
    # Security
    CONFIDENTIALITY = "confidentiality"
    INTEGRITY = "integrity"
    NON_REPUDIATION = "non_repudiation"
    ACCOUNTABILITY = "accountability"
    AUTHENTICITY = "authenticity"
    
    # Maintainability
    MODULARITY = "modularity"
    REUSABILITY = "reusability"
    ANALYSABILITY = "analysability"
    MODIFIABILITY = "modifiability"
    TESTABILITY = "testability"


@dataclass
class QualityMeasurement:
    """Quality measurement record."""
    metric: QualityMetric
    value: float
    timestamp: float
    component: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FaultRecord:
    """Fault/error record."""
    fault_id: str
    timestamp: float
    component: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[float] = None


class QualityManager:
    """Manages software quality according to ISO/IEC 25010."""
    
    def __init__(self):
        self.measurements: Dict[QualityMetric, List[QualityMeasurement]] = defaultdict(list)
        self.faults: List[FaultRecord] = []
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recovery_actions: List[Dict[str, Any]] = []
        
        # Quality thresholds
        self.thresholds = {
            QualityMetric.TIME_BEHAVIOR: 1.0,  # seconds
            QualityMetric.AVAILABILITY: 0.99,  # 99%
            QualityMetric.FAULT_TOLERANCE: 0.95,  # 95% fault tolerance
        }
        
        # Start time for availability calculation
        self.start_time = time.time()
        self.downtime = 0.0
        self.last_downtime_start: Optional[float] = None
    
    def record_measurement(
        self,
        metric: QualityMetric,
        value: float,
        component: str = "system",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a quality measurement."""
        measurement = QualityMeasurement(
            metric=metric,
            value=value,
            timestamp=time.time(),
            component=component,
            context=context or {},
        )
        
        self.measurements[metric].append(measurement)
        
        # Keep only last 1000 measurements per metric
        if len(self.measurements[metric]) > 1000:
            self.measurements[metric] = self.measurements[metric][-1000:]
    
    def record_fault(
        self,
        component: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
    ) -> str:
        """Record a fault/error."""
        fault_id = f"FAULT-{int(time.time() * 1000)}"
        
        fault = FaultRecord(
            fault_id=fault_id,
            timestamp=time.time(),
            component=component,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
        )
        
        self.faults.append(fault)
        self.error_counts[error_type] += 1
        
        # Keep only last 1000 faults
        if len(self.faults) > 1000:
            self.faults = self.faults[-1000:]
        
        # Start downtime tracking if not already started
        if self.last_downtime_start is None:
            self.last_downtime_start = time.time()
        
        LOGGER.error("Fault recorded: %s - %s - %s", fault_id, component, error_message)
        
        return fault_id
    
    def resolve_fault(self, fault_id: str) -> bool:
        """Mark a fault as resolved."""
        for fault in self.faults:
            if fault.fault_id == fault_id and not fault.resolved:
                fault.resolved = True
                fault.resolution_time = time.time() - fault.timestamp
                
                # Update downtime
                if self.last_downtime_start:
                    self.downtime += time.time() - self.last_downtime_start
                    self.last_downtime_start = None
                
                LOGGER.info("Fault resolved: %s (resolution time: %.2fs)", fault_id, fault.resolution_time)
                return True
        
        return False
    
    def record_performance(
        self,
        operation: str,
        duration: float,
    ) -> None:
        """Record performance metric."""
        self.performance_metrics[operation].append(duration)
        
        # Keep only last 1000 measurements
        if len(self.performance_metrics[operation]) > 1000:
            self.performance_metrics[operation] = self.performance_metrics[operation][-1000:]
        
        # Record as time behavior metric
        self.record_measurement(
            QualityMetric.TIME_BEHAVIOR,
            duration,
            component=operation,
        )
    
    def record_recovery_action(
        self,
        action: str,
        component: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a recovery action."""
        self.recovery_actions.append({
            "action": action,
            "component": component,
            "success": success,
            "timestamp": time.time(),
            "details": details or {},
        })
        
        # Keep only last 1000 actions
        if len(self.recovery_actions) > 1000:
            self.recovery_actions = self.recovery_actions[-1000:]
    
    def get_availability(self) -> float:
        """Calculate system availability."""
        total_time = time.time() - self.start_time
        if total_time == 0:
            return 1.0
        
        # Add current downtime if system is down
        current_downtime = self.downtime
        if self.last_downtime_start:
            current_downtime += time.time() - self.last_downtime_start
        
        uptime = total_time - current_downtime
        availability = uptime / total_time if total_time > 0 else 1.0
        
        self.record_measurement(QualityMetric.AVAILABILITY, availability)
        
        return availability
    
    def get_fault_tolerance(self) -> float:
        """Calculate fault tolerance (percentage of faults recovered)."""
        if not self.faults:
            return 1.0
        
        recovered = sum(1 for f in self.faults if f.resolved)
        total = len(self.faults)
        tolerance = recovered / total if total > 0 else 1.0
        
        self.record_measurement(QualityMetric.FAULT_TOLERANCE, tolerance)
        
        return tolerance
    
    def get_average_performance(self, operation: Optional[str] = None) -> Dict[str, float]:
        """Get average performance metrics."""
        if operation:
            if operation in self.performance_metrics:
                values = self.performance_metrics[operation]
                return {
                    operation: {
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "min": min(values),
                        "max": max(values),
                        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                    }
                }
            return {}
        
        # All operations
        result = {}
        for op, values in self.performance_metrics.items():
            if values:
                result[op] = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                }
        
        return result
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Get comprehensive quality report."""
        return {
            "availability": self.get_availability(),
            "fault_tolerance": self.get_fault_tolerance(),
            "total_faults": len(self.faults),
            "resolved_faults": sum(1 for f in self.faults if f.resolved),
            "unresolved_faults": sum(1 for f in self.faults if not f.resolved),
            "error_counts": dict(self.error_counts),
            "performance_metrics": self.get_average_performance(),
            "recovery_actions": len(self.recovery_actions),
            "successful_recoveries": sum(1 for a in self.recovery_actions if a["success"]),
            "measurements": {
                metric.value: {
                    "count": len(measurements),
                    "latest": measurements[-1].value if measurements else None,
                    "average": statistics.mean([m.value for m in measurements]) if measurements else None,
                }
                for metric, measurements in self.measurements.items()
                if measurements
            },
        }
    
    def check_quality_thresholds(self) -> Dict[QualityMetric, bool]:
        """Check if quality metrics meet thresholds."""
        results = {}
        
        for metric, threshold in self.thresholds.items():
            if metric in self.measurements and self.measurements[metric]:
                latest = self.measurements[metric][-1].value
                
                # For time behavior, lower is better
                if metric == QualityMetric.TIME_BEHAVIOR:
                    results[metric] = latest <= threshold
                # For others, higher is better
                else:
                    results[metric] = latest >= threshold
            else:
                results[metric] = None  # No data
        
        return results


# Global instance
_quality_manager: Optional[QualityManager] = None


def get_quality_manager() -> QualityManager:
    """Get global quality manager instance."""
    global _quality_manager
    if _quality_manager is None:
        _quality_manager = QualityManager()
    return _quality_manager


__all__ = [
    "QualityManager",
    "QualityCharacteristic",
    "QualityMetric",
    "QualityMeasurement",
    "FaultRecord",
    "get_quality_manager",
]

