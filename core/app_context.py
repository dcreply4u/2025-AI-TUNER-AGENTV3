from __future__ import annotations

"""
App Context / Service Registry
------------------------------

Provides a lightweight, centralized place to construct and share core
application services (logging, performance tracking, analysis, etc.) so that
UI components and controllers don't all new them up independently.

This is intentionally minimal and backwards-compatible: existing code can
continue constructing services directly, while new code can opt into using
AppContext.
"""

from dataclasses import dataclass
from pathlib import Path

from services.data_logger import DataLogger
from services.performance_tracker import PerformanceTracker
from services.session_analysis_service import SessionAnalysisService
from services.tuning_suggestion_service import TuningSuggestionService
from services.driver_performance_summary import DriverPerformanceSummaryService
from services import CloudSync, GeoLogger


@dataclass
class AppContext:
    """
    Central registry for core, long-lived services.

    Instances are meant to be created once near application startup and then
    passed into windows/widgets that need access to shared services.
    """

    data_logger: DataLogger
    performance_tracker: PerformanceTracker
    session_analyzer: SessionAnalysisService
    tuning_suggestion_service: TuningSuggestionService
    driver_performance_summary: DriverPerformanceSummaryService
    cloud_sync: CloudSync
    geo_logger: GeoLogger

    @classmethod
    def create(cls, log_dir: Path | str = "logs/telemetry") -> "AppContext":
        """
        Factory that builds a default AppContext using the given log directory.

        Args:
            log_dir: Base directory for telemetry logs.
        """
        base = Path(log_dir)
        base.mkdir(parents=True, exist_ok=True)

        data_logger = DataLogger(log_dir=base)
        performance_tracker = PerformanceTracker()
        session_analyzer = SessionAnalysisService(log_dir=base.parent if base.name == "telemetry" else base)
        tuning_svc = TuningSuggestionService()
        driver_summary = DriverPerformanceSummaryService()
        cloud_sync = CloudSync()
        geo_logger = GeoLogger()

        return cls(
            data_logger=data_logger,
            performance_tracker=performance_tracker,
            session_analyzer=session_analyzer,
            tuning_suggestion_service=tuning_svc,
            driver_performance_summary=driver_summary,
            cloud_sync=cloud_sync,
            geo_logger=geo_logger,
        )


__all__ = ["AppContext"]


