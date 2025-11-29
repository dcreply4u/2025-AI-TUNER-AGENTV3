from __future__ import annotations

"""
Developer Debug Dashboard Tab
-----------------------------

Unified internal dashboard for development/debug use:
 - Raw latest SessionAnalysisReport (JSON-ish text)
 - Raw TuningSuggestion list (structured view)
 - Status of AI advisor backend (RAG vs legacy Q)
 - Basic HAT / hardware status placeholders

Visible only when AITUNER_DEV_MODE or AITUNER_DEMO_MODE is enabled, or when
running from demo_safe.py.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
)

from core.app_context import AppContext
from services.ai_advisor_rag import VECTOR_STORE_AVAILABLE
from services.session_analysis_service import SessionAnalysisReport


class DevDebugDashboardTab(QWidget):
    """Development-only debug dashboard."""

    def __init__(
        self,
        app_context: Optional[AppContext] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self._app_context = app_context
        self._report: Optional[SessionAnalysisReport] = None

        self.is_dev_mode = self._check_dev_mode()
        if not self.is_dev_mode:
            self.setVisible(False)
            return

        self._build_ui()
        self._refresh_all()

    # ------------------------------------------------------------------ #
    # Mode detection
    # ------------------------------------------------------------------ #

    def _check_dev_mode(self) -> bool:
        if os.getenv("AITUNER_DEMO_MODE") == "true":
            return True
        if os.getenv("AITUNER_DEV_MODE") == "true":
            return True
        if "demo_safe" in sys.argv[0] or "demo_safe.py" in str(Path(sys.argv[0]).name):
            return True
        try:
            if "demo_safe" in str(Path(__file__).parent):
                return True
        except Exception:
            pass
        return False

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        banner = QLabel("⚠️ DEVELOPMENT/DEBUG DASHBOARD – NOT FOR PRODUCTION USE")
        banner.setStyleSheet(
            "background-color: #f97316; color: #000; font-weight: 600; padding: 6px; border-radius: 4px;"
        )
        layout.addWidget(banner)

        header_row = QHBoxLayout()
        title = QLabel("🧪 Internals Overview")
        title.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #e5e7eb; padding: 2px 4px;"
        )
        header_row.addWidget(title)
        header_row.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #00e5ff;"
            "  color: #001018;"
            "  border-radius: 4px;"
            "  padding: 3px 10px;"
            "  font-size: 11px;"
            "  font-weight: 600;"
            "}"
            "QPushButton:hover { background-color: #00bcd4; }"
            "QPushButton:pressed { background-color: #0097a7; }"
        )
        refresh_btn.clicked.connect(self._refresh_all)
        header_row.addWidget(refresh_btn)

        layout.addLayout(header_row)

        # Top: advisor / hardware status
        status_group = QGroupBox("Advisor & Hardware Status")
        status_group.setStyleSheet(
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
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(6, 6, 6, 4)
        status_layout.setSpacing(2)

        self.status_label = QLabel("Collecting status…")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.status_label.setStyleSheet("color: #e5e7eb; font-size: 11px;")
        status_layout.addWidget(self.status_label)

        layout.addWidget(status_group)

        # Middle: analysis JSON + tuning suggestions
        middle_row = QHBoxLayout()
        middle_row.setSpacing(6)

        analysis_group = QGroupBox("Latest Session Analysis (raw)")
        analysis_group.setStyleSheet(
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
        analysis_layout = QVBoxLayout(analysis_group)
        analysis_layout.setContentsMargins(4, 4, 4, 4)
        analysis_layout.setSpacing(2)

        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setStyleSheet(
            "QTextEdit {"
            "  background-color: #020617;"
            "  color: #e5e7eb;"
            "  font-family: Consolas, Menlo, monospace;"
            "  font-size: 11px;"
            "  border-radius: 4px;"
            "  border: 1px solid #1f2937;"
            "}"
        )
        analysis_layout.addWidget(self.analysis_text)

        middle_row.addWidget(analysis_group, stretch=2)

        tuning_group = QGroupBox("Tuning Suggestions (raw)")
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
            "  background-color: #020617;"
            "  color: #e5e7eb;"
            "  border-radius: 4px;"
            "  border: 1px solid #1f2937;"
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

    # ------------------------------------------------------------------ #
    # Refresh
    # ------------------------------------------------------------------ #

    def _refresh_all(self) -> None:
        self._refresh_status()
        self._refresh_analysis_and_tuning()

    def _refresh_status(self) -> None:
        lines: List[str] = []

        # Advisor backend info (RAG vs legacy)
        if VECTOR_STORE_AVAILABLE:
            lines.append("• AI Advisor: RAG-capable backend available (vector store).")
        else:
            lines.append("• AI Advisor: RAG backend unavailable – using legacy advisor stack.")

        # AppContext presence
        if self._app_context:
            lines.append("• AppContext: present (shared data_logger/performance/analyzer).")
        else:
            lines.append("• AppContext: not provided – using local service instances.")

        # HAT status placeholders – these can be wired to real detectors later
        lines.append("• HATs: Waveshare GPS/Environmental HAT status – see main HUD & logs (placeholder).")

        self.status_label.setText("\n".join(lines))

    def _refresh_analysis_and_tuning(self) -> None:
        self.analysis_text.clear()
        self.tuning_list.clear()

        if not self._app_context:
            self.analysis_text.setPlainText(
                "AppContext not provided – Dev Debug tab is running with no shared analyzer.\n"
                "Open this tab from the main app window to see live data."
            )
            return

        analyzer = self._app_context.session_analyzer if self._app_context else None
        tuning_svc = self._app_context.tuning_suggestion_service if self._app_context else None
        
        # Handle deferred initialization - services may be None
        if analyzer is None or tuning_svc is None:
            self.status_text.setPlainText("Services are still initializing in background...\nPlease wait a moment and refresh.")
            return

        try:
            report = analyzer.analyze_latest_session()
        except Exception as exc:
            self.analysis_text.setPlainText(f"Error analyzing latest session: {exc}")
            return

        self._report = report

        # Pretty-print JSON-like report
        try:
            report_dict = report.to_dict()
            self.analysis_text.setPlainText(json.dumps(report_dict, indent=2))
        except Exception:
            self.analysis_text.setPlainText(str(report))

        # Tuning suggestions
        if report.sample_count == 0:
            self.tuning_list.addItem("No samples – tuning suggestions unavailable.")
            return

        try:
            suggestions = tuning_svc.suggest_from_session(report)
        except Exception as exc:
            self.tuning_list.addItem(f"Error computing tuning suggestions: {exc}")
            return

        if not suggestions:
            self.tuning_list.addItem(
                "No major tuning or safety issues detected in the latest session."
            )
            return

        for s in suggestions:
            text = f"[{s.severity.upper()} • {s.category}] {s.message}"
            item = QListWidgetItem(text)
            item.setToolTip(s.rationale)
            self.tuning_list.addItem(item)


__all__ = ["DevDebugDashboardTab"]


