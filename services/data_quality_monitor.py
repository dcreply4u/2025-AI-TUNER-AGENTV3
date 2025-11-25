"""
Data Quality Monitor

Monitors data quality, accuracy, and freshness across all data sources.
Provides alerts and recommendations for data improvement.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)

from services.advanced_data_integration import DataQuality, DataStatistics


@dataclass
class QualityAlert:
    """Data quality alert."""
    alert_id: str
    source_id: str
    alert_type: str  # "low_quality", "stale_data", "missing_data", "validation_failure"
    severity: str  # "low", "medium", "high", "critical"
    message: str
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False


@dataclass
class QualityReport:
    """Data quality report."""
    source_id: str
    overall_score: float  # 0-1
    quality_breakdown: Dict[str, float]  # Field-level quality
    freshness_score: float  # 0-1
    completeness_score: float  # 0-1
    accuracy_score: float  # 0-1
    recommendations: List[str] = field(default_factory=list)


class DataQualityMonitor:
    """
    Data quality monitoring system.
    
    Features:
    - Real-time quality monitoring
    - Quality scoring
    - Alert generation
    - Trend analysis
    - Recommendations
    - Automated quality checks
    """
    
    def __init__(self, data_integration: Any):
        """
        Initialize quality monitor.
        
        Args:
            data_integration: Data integration platform instance
        """
        self.data_integration = data_integration
        self.alerts: Dict[str, QualityAlert] = {}
        self.quality_history: Dict[str, List[float]] = {}  # source_id -> quality scores over time
        
        # Quality thresholds
        self.thresholds = {
            "excellent": 0.95,
            "good": 0.80,
            "fair": 0.60,
            "poor": 0.40,
        }
        
        LOGGER.info("Data quality monitor initialized")
    
    def monitor_source(self, source_id: str) -> QualityReport:
        """
        Monitor data quality for a source.
        
        Args:
            source_id: Source identifier
        
        Returns:
            Quality report
        """
        # Get statistics
        stats = self.data_integration.get_statistics()
        
        # Calculate quality scores
        quality_breakdown = {}
        completeness_score = 1.0
        accuracy_score = 1.0
        
        # Get records for source
        records = self.data_integration.query_data(source_ids=[source_id], limit=1000)
        
        if records:
            # Calculate field-level quality
            field_quality = {}
            for record in records:
                for field, value in record.data.items():
                    if field not in field_quality:
                        field_quality[field] = []
                    field_quality[field].append(record.quality_score)
            
            for field, scores in field_quality.items():
                quality_breakdown[field] = sum(scores) / len(scores) if scores else 0.0
            
            # Overall quality
            overall_scores = [r.quality_score for r in records]
            overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
            
            # Completeness (check for missing values)
            total_fields = len(quality_breakdown) * len(records)
            missing_fields = sum(
                1 for r in records
                for field in quality_breakdown.keys()
                if field not in r.data or r.data[field] is None
            )
            completeness_score = 1.0 - (missing_fields / total_fields) if total_fields > 0 else 1.0
            
            # Accuracy (based on validation errors)
            records_with_errors = sum(1 for r in records if r.validation_errors)
            accuracy_score = 1.0 - (records_with_errors / len(records)) if records else 1.0
        else:
            overall_score = 0.0
        
        # Freshness score
        source = self.data_integration.sources.get(source_id)
        if source and source.last_update:
            hours_old = (time.time() - source.last_update) / 3600
            expected_frequency_hours = source.update_frequency / 3600
            freshness_score = max(0.0, 1.0 - (hours_old / (expected_frequency_hours * 2)))
        else:
            freshness_score = 0.0
        
        # Generate recommendations
        recommendations = []
        if overall_score < self.thresholds["good"]:
            recommendations.append("Data quality below acceptable threshold - review data source")
        if freshness_score < 0.5:
            recommendations.append("Data is stale - check update schedule")
        if completeness_score < 0.9:
            recommendations.append("Missing values detected - improve data collection")
        if accuracy_score < 0.9:
            recommendations.append("Validation errors detected - review data validation rules")
        
        report = QualityReport(
            source_id=source_id,
            overall_score=overall_score,
            quality_breakdown=quality_breakdown,
            freshness_score=freshness_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            recommendations=recommendations,
        )
        
        # Check for alerts
        self._check_alerts(source_id, report)
        
        # Track quality history
        if source_id not in self.quality_history:
            self.quality_history[source_id] = []
        self.quality_history[source_id].append(overall_score)
        # Keep last 100 scores
        if len(self.quality_history[source_id]) > 100:
            self.quality_history[source_id] = self.quality_history[source_id][-100:]
        
        return report
    
    def _check_alerts(self, source_id: str, report: QualityReport) -> None:
        """Check for quality alerts and generate if needed."""
        # Low quality alert
        if report.overall_score < self.thresholds["poor"]:
            self._create_alert(
                source_id=source_id,
                alert_type="low_quality",
                severity="critical",
                message=f"Data quality is critically low: {report.overall_score:.2f}",
            )
        elif report.overall_score < self.thresholds["fair"]:
            self._create_alert(
                source_id=source_id,
                alert_type="low_quality",
                severity="high",
                message=f"Data quality is below acceptable: {report.overall_score:.2f}",
            )
        
        # Stale data alert
        if report.freshness_score < 0.3:
            self._create_alert(
                source_id=source_id,
                alert_type="stale_data",
                severity="high",
                message="Data is very stale - update required",
            )
        
        # Missing data alert
        if report.completeness_score < 0.7:
            self._create_alert(
                source_id=source_id,
                alert_type="missing_data",
                severity="medium",
                message=f"High percentage of missing data: {(1 - report.completeness_score) * 100:.1f}%",
            )
    
    def _create_alert(
        self,
        source_id: str,
        alert_type: str,
        severity: str,
        message: str
    ) -> None:
        """Create quality alert."""
        alert_id = f"alert_{source_id}_{int(time.time())}"
        
        # Check if similar alert already exists
        existing = [
            a for a in self.alerts.values()
            if a.source_id == source_id and a.alert_type == alert_type and not a.resolved
        ]
        
        if existing:
            # Update existing alert
            existing[0].message = message
            existing[0].timestamp = time.time()
            return
        
        alert = QualityAlert(
            alert_id=alert_id,
            source_id=source_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
        )
        
        self.alerts[alert_id] = alert
        LOGGER.warning("Quality alert: %s - %s", severity.upper(), message)
    
    def get_active_alerts(self, severity: Optional[str] = None) -> List[QualityAlert]:
        """Get active quality alerts."""
        alerts = [a for a in self.alerts.values() if not a.resolved]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(a.severity, 0),
            -a.timestamp
        ), reverse=True)
    
    def get_quality_trend(self, source_id: str) -> Dict[str, Any]:
        """Get quality trend over time."""
        if source_id not in self.quality_history:
            return {"trend": "stable", "scores": []}
        
        scores = self.quality_history[source_id]
        if len(scores) < 2:
            return {"trend": "stable", "scores": scores}
        
        # Calculate trend
        recent_avg = sum(scores[-10:]) / len(scores[-10:]) if len(scores) >= 10 else scores[-1]
        older_avg = sum(scores[:-10]) / len(scores[:-10]) if len(scores) > 10 else scores[0]
        
        if recent_avg > older_avg * 1.05:
            trend = "improving"
        elif recent_avg < older_avg * 0.95:
            trend = "degrading"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "scores": scores,
            "current": scores[-1] if scores else 0.0,
            "average": sum(scores) / len(scores) if scores else 0.0,
            "min": min(scores) if scores else 0.0,
            "max": max(scores) if scores else 0.0,
        }


__all__ = [
    "DataQualityMonitor",
    "QualityAlert",
    "QualityReport",
]









