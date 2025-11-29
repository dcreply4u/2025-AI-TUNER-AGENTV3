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

import logging
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from typing import Optional

from services.data_logger import DataLogger
from services.performance_tracker import PerformanceTracker
from services.session_analysis_service import SessionAnalysisService
from services.tuning_suggestion_service import TuningSuggestionService
from services.driver_performance_summary import DriverPerformanceSummaryService
from services import CloudSync, GeoLogger

LOGGER = logging.getLogger(__name__)


@dataclass
class AppContext:
    """
    Central registry for core, long-lived services.

    Instances are meant to be created once near application startup and then
    passed into windows/widgets that need access to shared services.
    """

    data_logger: DataLogger
    performance_tracker: PerformanceTracker
    session_analyzer: Optional[SessionAnalysisService]
    tuning_suggestion_service: Optional[TuningSuggestionService]
    driver_performance_summary: Optional[DriverPerformanceSummaryService]
    cloud_sync: CloudSync
    geo_logger: GeoLogger

    @classmethod
    def create(cls, log_dir: Path | str = "logs/telemetry", defer_heavy_init: bool = False) -> "AppContext":
        """
        Factory that builds a default AppContext using the given log directory.

        Args:
            log_dir: Base directory for telemetry logs.
            defer_heavy_init: If True, defer initialization of heavy services to background thread.
        """
        base = Path(log_dir)
        base.mkdir(parents=True, exist_ok=True)

        # Always create lightweight services immediately
        data_logger = DataLogger(log_dir=base)
        performance_tracker = PerformanceTracker()
        cloud_sync = CloudSync()
        geo_logger = GeoLogger()

        # Create context with lightweight services
        context = cls(
            data_logger=data_logger,
            performance_tracker=performance_tracker,
            session_analyzer=None,  # Will be initialized
            tuning_suggestion_service=None,  # Will be initialized
            driver_performance_summary=None,  # Will be initialized
            cloud_sync=cloud_sync,
            geo_logger=geo_logger,
        )

        if defer_heavy_init:
            # Initialize heavy services in background
            def init_heavy_services():
                try:
                    LOGGER.info("Initializing heavy services in background...")
                    context.session_analyzer = SessionAnalysisService(
                        log_dir=base.parent if base.name == "telemetry" else base
                    )
                    context.tuning_suggestion_service = TuningSuggestionService()
                    context.driver_performance_summary = DriverPerformanceSummaryService()
                    LOGGER.info("Heavy services initialized")
                except Exception as e:
                    LOGGER.error(f"Failed to initialize heavy services: {e}", exc_info=True)
            
            thread = Thread(target=init_heavy_services, daemon=True)
            thread.start()
        else:
            # Initialize immediately (original behavior)
            context.session_analyzer = SessionAnalysisService(
                log_dir=base.parent if base.name == "telemetry" else base
            )
            context.tuning_suggestion_service = TuningSuggestionService()
            context.driver_performance_summary = DriverPerformanceSummaryService()

        return context


__all__ = ["AppContext"]


