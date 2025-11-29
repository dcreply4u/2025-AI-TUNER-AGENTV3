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
from pathlib import Path
from datetime import datetime

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
    QComboBox,
)

from services.driver_performance_summary import DriverPerformanceSummaryService
from services.performance_tracker import PerformanceTracker
from services.session_analysis_service import SessionAnalysisService, SessionAnalysisReport
from services.tuning_suggestion_service import TuningSuggestionService, TuningSuggestion
from core.app_context import AppContext


class AnalysisCoachTab(QWidget):
    """Unified Analysis & Coach dashboard."""

    def __init__(
        self,
        performance_tracker: Optional[PerformanceTracker] = None,
        app_context: Optional[AppContext] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        # Lightweight services – prefer AppContext if provided
        if app_context:
            self._session_analyzer = app_context.session_analyzer
            self._tuning_service = app_context.tuning_suggestion_service
            self._driver_summary = app_context.driver_performance_summary
            self._performance_tracker = app_context.performance_tracker
        else:
            self._session_analyzer = SessionAnalysisService()
            self._tuning_service = TuningSuggestionService()
            self._driver_summary = DriverPerformanceSummaryService()
            self._performance_tracker = performance_tracker

        self._report: Optional[SessionAnalysisReport] = None
        self._tuning: list[TuningSuggestion] = []
        self._driver_goal: str = self._load_driver_goal()

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

        # Driver goal/profile selector
        goal_label = QLabel("Goal:")
        goal_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        header_row.addWidget(goal_label)

        self.goal_combo = QComboBox()
        self.goal_combo.addItems(
            ["Balanced", "Safe track day", "Drag PB", "Endurance"]
        )
        # Map stored goal to combo index
        goal_map = {
            "safe track day": "Safe track day",
            "safe": "Safe track day",
            "pb": "Drag PB",
            "drag pb": "Drag PB",
            "endurance": "Endurance",
        }
        display_goal = goal_map.get(self._driver_goal.lower(), "Balanced")
        index = self.goal_combo.findText(display_goal)
        if index >= 0:
            self.goal_combo.setCurrentIndex(index)
        self.goal_combo.setStyleSheet(
            "QComboBox {"
            "  background-color: #020617;"
            "  color: #e5e7eb;"
            "  border-radius: 4px;"
            "  border: 1px solid #1f2937;"
            "  padding: 2px 6px;"
            "  font-size: 11px;"
            "}"
        )
        self.goal_combo.currentTextChanged.connect(self._on_goal_changed)
        header_row.addWidget(self.goal_combo)

        # Export button (left of Refresh)
        export_btn = QPushButton("Export Report")
        export_btn.setToolTip("Export latest analysis, tuning suggestions, and performance as a markdown report.")
        export_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #1f2937;"
            "  color: #e5e7eb;"
            "  border-radius: 4px;"
            "  padding: 4px 8px;"
            "  font-size: 10px;"
            "  font-weight: 500;"
            "}"
            "QPushButton:hover { background-color: #111827; }"
            "QPushButton:pressed { background-color: #020617; }"
        )
        export_btn.clicked.connect(self._export_report)
        header_row.addWidget(export_btn)

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

    def _on_goal_changed(self, text: str) -> None:
        """Handle driver goal/profile change and persist to config."""
        self._driver_goal = text
        self._save_driver_goal(text)
        # Recompute tuning suggestions with new goal weighting
        self._refresh_tuning_suggestions()

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
            # Map UI goal to internal short code
            goal_map = {
                "balanced": "",
                "safe track day": "safe",
                "drag pb": "pb",
                "endurance": "endurance",
            }
            goal_key = goal_map.get(self._driver_goal.lower(), "")
            suggestions = self._tuning_service.suggest_from_session(
                self._report,
                goal=goal_key or None,
            )
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

    # ------------------------------------------------------------------ #
    # Export helpers
    # ------------------------------------------------------------------ #

    def _export_report(self) -> None:
        """
        Export a single markdown report summarizing the latest analysis, tuning
        suggestions, and performance metrics.
        """
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_path = reports_dir / f"analysis_report_{timestamp}.md"

        lines: list[str] = []
        lines.append("# TelemetryIQ Analysis Report")
        lines.append("")
        lines.append(f"- Generated: {datetime.now().isoformat(timespec='seconds')}")
        if self._report and self._report.log_file:
            lines.append(f"- Log file: `{self._report.log_file}`")
        lines.append("")

        # Session summary
        lines.append("## Session Summary")
        if not self._report or self._report.sample_count == 0:
            lines.append("No recent session logs found.")
        else:
            duration = (
                f"~{self._report.duration_s:.0f}s"
                if self._report.duration_s is not None
                else "unknown duration"
            )
            lines.append(f"- Samples: **{self._report.sample_count}**")
            lines.append(f"- Duration: **{duration}**")
            lines.append(f"- Channels analyzed: **{len(self._report.channel_summaries)}**")
        lines.append("")

        # Anomalies
        lines.append("## Telemetry Anomalies")
        if not self._report or not self._report.anomalies:
            lines.append("- No major AFR, temperature, or boost issues detected.")
        else:
            for a in self._report.anomalies:
                lines.append(f"- **[{a.severity.upper()}]** {a.message}")
        lines.append("")

        # Tuning suggestions
        lines.append("## Tuning Suggestions")
        if not self._tuning:
            lines.append("- No tuning or safety suggestions at this time.")
        else:
            for s in self._tuning:
                lines.append(f"- **[{s.severity.upper()} • {s.category}]** {s.message}")
                if s.rationale:
                    lines.append(f"  - _Why_: {s.rationale}")
        lines.append("")

        # Performance summary
        lines.append("## Straight-line Performance")
        if not self._performance_tracker:
            lines.append(
                "Performance tracker not available in this context; "
                "run from the main app to record acceleration metrics."
            )
        else:
            try:
                snapshot = self._performance_tracker.snapshot()
                summary = self._driver_summary.summarize(snapshot)
                if summary.best_0_60_s:
                    lines.append(f"- Best 0–60 mph: **{summary.best_0_60_s:.2f} s**")
                else:
                    lines.append("- 0–60 mph: no complete run detected yet.")
                if summary.best_quarter_mile_s:
                    lines.append(f"- Best 1/4 mile ET: **{summary.best_quarter_mile_s:.2f} s**")
                if summary.best_half_mile_s:
                    lines.append(f"- Best 1/2 mile ET: **{summary.best_half_mile_s:.2f} s**")
                lines.append(f"- Total distance: **{summary.total_distance_km:.2f} km**")
            except Exception as exc:  # pragma: no cover - defensive
                lines.append(f"- Error summarizing performance: {exc}")

        out_path.write_text("\n".join(lines), encoding="utf-8")

    # ------------------------------------------------------------------ #
    # Driver goal persistence
    # ------------------------------------------------------------------ #

    def _load_driver_goal(self) -> str:
        cfg_path = Path("config/driver_goal.json")
        if not cfg_path.exists():
            return "Balanced"
        try:
            import json

            data = json.load(cfg_path.open("r", encoding="utf-8"))
            return str(data.get("goal", "Balanced"))
        except Exception:
            return "Balanced"

    def _save_driver_goal(self, goal: str) -> None:
        cfg_path = Path("config/driver_goal.json")
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import json

            json.dump({"goal": goal}, cfg_path.open("w", encoding="utf-8"), indent=2)
        except Exception:
            # Best-effort only
            pass



