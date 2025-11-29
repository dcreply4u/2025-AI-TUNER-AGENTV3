from __future__ import annotations

"""
Analysis & Coach Tab
--------------------

Compact dashboard that surfaces:
 - Latest session summary (from SessionAnalysisService)
 - Telemetry anomalies (AFR, temps, boost)
 - Tuning suggestions (from TuningSuggestionService)
 - Straight-line performance summary (from DriverPerformanceSummaryService)

This is a read-only, low-risk view intended for trackside sanity checks. It does
not modify tunes – it only reads logs and PerformanceTracker state.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
)

from services.driver_performance_summary import DriverPerformanceSummaryService
from services.performance_tracker import PerformanceTracker
from services.session_analysis_service import SessionAnalysisService, SessionAnalysisReport
from services.tuning_suggestion_service import TuningSuggestionService, TuningSuggestion


class AnalysisCoachTab(QWidget):
    """Unified Analysis & Coach dashboard."""

    def __init__(
        self,
        performance_tracker: Optional[PerformanceTracker] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        # Lightweight services – no side effects, only read data
        self._session_analyzer = SessionAnalysisService()
        self._tuning_service = TuningSuggestionService()
        self._driver_summary = DriverPerformanceSummaryService()
        self._performance_tracker = performance_tracker

        self._report: Optional[SessionAnalysisReport] = None
        self._tuning: list[TuningSuggestion] = []

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        title = QLabel("📊 Analysis & Coach")
        title.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #00e5ff; padding: 2px 4px;"
        )
        header_row.addWidget(title)

        header_row.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setToolTip("Re-run session analysis and update coaching summary.")
        refresh_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #00e5ff;"
            "  color: #001018;"
            "  border-radius: 4px;"
            "  padding: 4px 10px;"
            "  font-size: 11px;"
            "  font-weight: 600;"
            "}"
            "QPushButton:hover { background-color: #00bcd4; }"
            "QPushButton:pressed { background-color: #0097a7; }"
        )
        refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(refresh_btn)

        layout.addLayout(header_row)

        # Session summary
        summary_group = QGroupBox("Session Summary")
        summary_group.setStyleSheet(
            "QGroupBox {"
            "  color: #00e5ff;"
            "  border: 1px solid #00e5ff;"
            "  border-radius: 6px;"
            "  margin-top: 6px;"
            "  font-size: 11px;"
            "  font-weight: 600;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  subcontrol-position: top left;"
            "  padding: 0 4px;"
            "}"
        )
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setContentsMargins(6, 6, 6, 4)
        summary_layout.setSpacing(2)

        self.summary_label = QLabel("No recent session logs found.")
        self.summary_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.summary_label.setStyleSheet(
            "color: #e5e7eb; font-size: 11px; padding: 0 2px;"
        )
        summary_layout.addWidget(self.summary_label)

        layout.addWidget(summary_group)

        # Middle row: anomalies + tuning suggestions
        middle_row = QHBoxLayout()
        middle_row.setSpacing(8)

        anomalies_group = QGroupBox("Telemetry Anomalies")
        anomalies_group.setStyleSheet(
            "QGroupBox {"
            "  color: #fbbf24;"
            "  border: 1px solid #fbbf24;"
            "  border-radius: 6px;"
            "  margin-top: 6px;"
            "  font-size: 11px;"
            "  font-weight: 600;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  subcontrol-position: top left;"
            "  padding: 0 4px;"
            "}"
        )
        anomalies_layout = QVBoxLayout(anomalies_group)
        anomalies_layout.setContentsMargins(4, 4, 4, 4)
        anomalies_layout.setSpacing(2)

        self.anomalies_list = QListWidget()
        self.anomalies_list.setStyleSheet(
            "QListWidget {"
            "  background-color: #050711;"
            "  color: #e5e7eb;"
            "  border: 1px solid #1f2937;"
            "  border-radius: 4px;"
            "  font-size: 11px;"
            "}"
            "QListWidget::item { padding: 3px 4px; }"
            "QListWidget::item:selected {"
            "  background-color: #1f2937;"
            "  color: #ffffff;"
            "}"
        )
        anomalies_layout.addWidget(self.anomalies_list)

        middle_row.addWidget(anomalies_group, stretch=1)

        tuning_group = QGroupBox("Tuning Suggestions")
        tuning_group.setStyleSheet(
            "QGroupBox {"
            "  color: #10b981;"
            "  border: 1px solid #10b981;"
            "  border-radius: 6px;"
            "  margin-top: 6px;"
            "  font-size: 11px;"
            "  font-weight: 600;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  subcontrol-position: top left;"
            "  padding: 0 4px;"
            "}"
        )
        tuning_layout = QVBoxLayout(tuning_group)
        tuning_layout.setContentsMargins(4, 4, 4, 4)
        tuning_layout.setSpacing(2)

        self.tuning_list = QListWidget()
        self.tuning_list.setStyleSheet(
            "QListWidget {"
            "  background-color: #050711;"
            "  color: #e5e7eb;"
            "  border: 1px solid #1f2937;"
            "  border-radius: 4px;"
            "  font-size: 11px;"
            "}"
            "QListWidget::item { padding: 3px 4px; }"
            "QListWidget::item:selected {"
            "  background-color: #064e3b;"
            "  color: #ffffff;"
            "}"
        )
        tuning_layout.addWidget(self.tuning_list)

        middle_row.addWidget(tuning_group, stretch=1)
        layout.addLayout(middle_row)

        # Bottom: straight-line performance summary
        perf_group = QGroupBox("Straight-line Performance")
        perf_group.setStyleSheet(
            "QGroupBox {"
            "  color: #e11d48;"
            "  border: 1px solid #e11d48;"
            "  border-radius: 6px;"
            "  margin-top: 6px;"
            "  font-size: 11px;"
            "  font-weight: 600;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  subcontrol-position: top left;"
            "  padding: 0 4px;"
            "}"
        )
        perf_layout = QVBoxLayout(perf_group)
        perf_layout.setContentsMargins(6, 6, 6, 4)
        perf_layout.setSpacing(2)

        self.perf_label = QLabel(
            "No performance snapshot yet. Start driving with GPS to populate metrics."
        )
        self.perf_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.perf_label.setStyleSheet(
            "color: #e5e7eb; font-size: 11px; padding: 0 2px;"
        )
        perf_layout.addWidget(self.perf_label)

        layout.addWidget(perf_group)

    # ------------------------------------------------------------------ #
    # Refresh logic
    # ------------------------------------------------------------------ #

    def refresh(self) -> None:
        """Re-run analysis, tuning suggestions, and performance summary."""
        self._refresh_session_analysis()
        self._refresh_tuning_suggestions()
        self._refresh_performance()

    def _refresh_session_analysis(self) -> None:
        try:
            report = self._session_analyzer.analyze_latest_session()
        except Exception as exc:  # pragma: no cover - defensive
            self.summary_label.setText(
                f"Error analyzing latest session: {exc}\n"
                "Check that logs are being written and try again."
            )
            self.anomalies_list.clear()
            self._report = None
            return

        self._report = report

        if report.sample_count == 0:
            self.summary_label.setText(
                "No recent session logs found.\n"
                "Run a session with logging enabled to populate this view."
            )
            self.anomalies_list.clear()
            return

        duration = (
            f"~{report.duration_s:.0f}s"
            if report.duration_s is not None
            else "unknown duration"
        )
        log_name = report.log_file or "(unknown file)"
        self.summary_label.setText(
            f"Log file: {log_name}\n"
            f"Samples: {report.sample_count} • Duration: {duration}\n"
            f"Channels analyzed: {len(report.channel_summaries)}"
        )

        # Populate anomalies list
        self.anomalies_list.clear()
        if not report.anomalies:
            none_item = QListWidgetItem("No major AFR, temperature, or boost issues detected.")
            none_item.setForeground(Qt.GlobalColor.lightGray)
            self.anomalies_list.addItem(none_item)
            return

        for anomaly in report.anomalies:
            prefix = "•"
            color = Qt.GlobalColor.cyan
            if anomaly.severity == "warning":
                prefix = "⚠️"
                color = Qt.GlobalColor.yellow
            elif anomaly.severity == "critical":
                prefix = "🚨"
                color = Qt.GlobalColor.red
            text = f"{prefix} {anomaly.message}"
            item = QListWidgetItem(text)
            item.setForeground(color)
            self.anomalies_list.addItem(item)

    def _refresh_tuning_suggestions(self) -> None:
        self.tuning_list.clear()
        self._tuning = []

        if not self._report or self._report.sample_count == 0:
            self.tuning_list.addItem(
                "No session data available for tuning suggestions yet."
            )
            return

        try:
            suggestions = self._tuning_service.suggest_from_session(self._report)
        except Exception as exc:  # pragma: no cover - defensive
            self.tuning_list.addItem(
                f"Unable to compute tuning suggestions: {exc}"
            )
            return

        if not suggestions:
            self.tuning_list.addItem(
                "No major tuning or safety issues detected. Current tune looks reasonable."
            )
            return

        for s in suggestions:
            prefix = "•"
            color = Qt.GlobalColor.cyan
            if s.severity == "warning":
                prefix = "⚠️"
                color = Qt.GlobalColor.yellow
            elif s.severity == "critical":
                prefix = "🚨"
                color = Qt.GlobalColor.red

            text = f"{prefix} [{s.category}] {s.message}"
            item = QListWidgetItem(text)
            item.setToolTip(s.rationale)
            item.setForeground(color)
            self.tuning_list.addItem(item)
            self._tuning.append(s)

    def _refresh_performance(self) -> None:
        if not self._performance_tracker:
            self.perf_label.setText(
                "Performance tracker not available in this context.\n"
                "Driver metrics will appear here when running from the main app."
            )
            return

        try:
            snapshot = self._performance_tracker.snapshot()
            summary = self._driver_summary.summarize(snapshot)
        except Exception as exc:  # pragma: no cover - defensive
            self.perf_label.setText(
                f"Error summarizing performance: {exc}\n"
                "Ensure GPS speed is available and try again."
            )
            return

        lines: list[str] = []
        lines.append("Latest session straight-line metrics:")
        if summary.best_0_60_s:
            lines.append(f"• Best 0–60 mph: {summary.best_0_60_s:.2f} s")
        else:
            lines.append("• 0–60 mph: no complete run detected yet.")

        if summary.best_quarter_mile_s:
            lines.append(f"• Best 1/4 mile ET: {summary.best_quarter_mile_s:.2f} s")
        if summary.best_half_mile_s:
            lines.append(f"• Best 1/2 mile ET: {summary.best_half_mile_s:.2f} s")

        lines.append(f"• Total distance: {summary.total_distance_km:.2f} km")

        self.perf_label.setText("\n".join(lines))


