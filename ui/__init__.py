"""\
=========================================================
UI Toolkit – modular PySide6 widgets for AI Tuner
=========================================================
Everything in this namespace is designed to be composable Qt widgets so you can mix,
match, or embed them elsewhere without rewriting glue code.
"""

from .ai_insight_panel import AIInsightPanel
from .dragy_view import DragyPerformanceView, DragyView
from .fault_panel import FaultPanel
from .health_score_widget import HealthScoreWidget
from .settings_dialog import SettingsDialog
from .status_bar import StatusBar
from .telemetry_panel import TelemetryPanel

__all__ = [
    "AIInsightPanel",
    "DragyPerformanceView",
    "DragyView",
    "FaultPanel",
    "HealthScoreWidget",
    "SettingsDialog",
    "StatusBar",
    "TelemetryPanel",
]
