"""
AI Intelligence Tab
Advanced Diagnostics Intelligence and Self-Learning Intelligence UI
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGridLayout,
    QTextEdit,
    QProgressBar,
)

from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size, get_scaled_stylesheet

try:
    from services.advanced_diagnostics_intelligence import (
        AdvancedDiagnosticsIntelligence,
        DiagnosticAlert,
        ComponentHealth,
    )
except ImportError:
    AdvancedDiagnosticsIntelligence = None
    DiagnosticAlert = None
    ComponentHealth = None

try:
    from services.advanced_self_learning_intelligence import (
        AdvancedSelfLearningIntelligence,
        TuningAction,
        LearningExperience,
    )
except ImportError:
    AdvancedSelfLearningIntelligence = None
    TuningAction = None
    LearningExperience = None


class AIIntelligenceTab(QWidget):
    """AI Intelligence tab with advanced diagnostics and self-learning."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scaler = UIScaler.get_instance()
        
        # Initialize intelligence engines
        self.diagnostics_engine: Optional[AdvancedDiagnosticsIntelligence] = None
        self.learning_engine: Optional[AdvancedSelfLearningIntelligence] = None
        
        if AdvancedDiagnosticsIntelligence:
            try:
                self.diagnostics_engine = AdvancedDiagnosticsIntelligence(
                    use_lstm=True,
                    use_ensemble=True,
                )
            except Exception as e:
                print(f"Failed to initialize diagnostics engine: {e}")
        
        if AdvancedSelfLearningIntelligence:
            try:
                self.learning_engine = AdvancedSelfLearningIntelligence(
                    use_dqn=True,
                    use_policy_gradient=True,
                )
            except Exception as e:
                print(f"Failed to initialize learning engine: {e}")
        
        self.setup_ui()
        self._start_update_timer()
    
    def setup_ui(self) -> None:
        """Setup AI intelligence tab."""
        main_layout = QVBoxLayout(self)
        margin = self.scaler.get_scaled_size(10)
        spacing = self.scaler.get_scaled_size(10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # Title
        title = QLabel("AI Intelligence - Advanced Diagnostics & Self-Learning Algorithms")
        title_font = self.scaler.get_scaled_font_size(18)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(title)
        
        # Feature tabs
        feature_tabs = QTabWidget()
        tab_padding_v = self.scaler.get_scaled_size(6)
        tab_padding_h = self.scaler.get_scaled_size(15)
        tab_font = self.scaler.get_scaled_font_size(10)
        tab_border = self.scaler.get_scaled_size(1)
        tab_margin = self.scaler.get_scaled_size(2)
        feature_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {tab_border}px solid #404040;
                background-color: #1a1a1a;
            }}
            QTabBar::tab {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {tab_padding_v}px {tab_padding_h}px;
                margin-right: {tab_margin}px;
                border: {tab_border}px solid #404040;
                font-size: {tab_font}px;
            }}
            QTabBar::tab:selected {{
                background-color: #1a1a1a;
                border-bottom: {self.scaler.get_scaled_size(2)}px solid #0080ff;
            }}
        """)
        
        # Advanced Diagnostics
        feature_tabs.addTab(self._create_diagnostics_tab(), "Advanced Diagnostics")
        
        # Self-Learning Intelligence
        feature_tabs.addTab(self._create_learning_tab(), "Self-Learning AI")
        
        # Learning Statistics
        feature_tabs.addTab(self._create_statistics_tab(), "Learning Statistics")
        
        main_layout.addWidget(feature_tabs, stretch=1)
    
    def _create_diagnostics_tab(self) -> QWidget:
        """Create advanced diagnostics tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        margin = self.scaler.get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Advanced Diagnostics Intelligence - LSTM, Ensemble Methods, Predictive Maintenance")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Overall health
        health_group = QGroupBox("Overall Engine Health")
        group_font = self.scaler.get_scaled_font_size(12)
        group_border = self.scaler.get_scaled_size(1)
        group_radius = self.scaler.get_scaled_size(3)
        group_margin = self.scaler.get_scaled_size(10)
        health_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {group_font}px; font-weight: bold; color: #ffffff;
                border: {group_border}px solid #404040; border-radius: {group_radius}px;
                margin-top: {group_margin}px; padding-top: {group_margin}px;
            }}
        """)
        health_layout = QGridLayout()
        
        health_layout.addWidget(QLabel("Health Score:"), 0, 0)
        self.overall_health_score = QLabel("100/100")
        health_score_font = self.scaler.get_scaled_font_size(24)
        self.overall_health_score.setStyleSheet(f"font-size: {health_score_font}px; font-weight: bold; color: #00ff00;")
        health_layout.addWidget(self.overall_health_score, 0, 1)
        
        health_layout.addWidget(QLabel("Status:"), 1, 0)
        self.overall_status = QLabel("Excellent")
        status_font = self.scaler.get_scaled_font_size(14)
        self.overall_status.setStyleSheet(f"font-size: {status_font}px; color: #00ff00;")
        health_layout.addWidget(self.overall_status, 1, 1)
        
        health_group.setLayout(health_layout)
        layout.addWidget(health_group)
        
        # Component health table
        components_group = QGroupBox("Component Health Analysis")
        components_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        components_layout = QVBoxLayout()
        
        self.components_table = QTableWidget()
        self.components_table.setRowCount(10)
        self.components_table.setColumnCount(6)
        self.components_table.setHorizontalHeaderLabels([
            "Component", "Health Score", "Status", "RUL (Hours)", "Trend", "Confidence"
        ])
        self.components_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.components_table.setMinimumHeight(self.scaler.get_scaled_size(300))
        table_padding = self.scaler.get_scaled_size(5)
        table_border = self.scaler.get_scaled_size(1)
        self.components_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: {table_border}px solid #404040;
            }}
            QHeaderView::section {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {table_padding}px;
                border: {table_border}px solid #404040;
            }}
        """)
        components_layout.addWidget(self.components_table)
        components_group.setLayout(components_layout)
        layout.addWidget(components_group)
        
        # Diagnostic alerts
        alerts_group = QGroupBox("Diagnostic Alerts (LSTM + IsolationForest + Correlation Analysis)")
        alerts_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        alerts_layout = QVBoxLayout()
        
        self.alerts_table = QTableWidget()
        self.alerts_table.setRowCount(20)
        self.alerts_table.setColumnCount(5)
        self.alerts_table.setHorizontalHeaderLabels([
            "Component", "Alert Type", "Severity", "Confidence", "Message"
        ])
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.alerts_table.setMinimumHeight(self.scaler.get_scaled_size(200))
        table_padding = self.scaler.get_scaled_size(5)
        table_border = self.scaler.get_scaled_size(1)
        self.alerts_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: {table_border}px solid #404040;
            }}
            QHeaderView::section {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {table_padding}px;
                border: {table_border}px solid #404040;
            }}
        """)
        alerts_layout.addWidget(self.alerts_table)
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)
        
        layout.addStretch()
        return panel
    
    def _create_learning_tab(self) -> QWidget:
        """Create self-learning intelligence tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        margin = self.scaler.get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Self-Learning Intelligence - DQN, Policy Gradient, Multi-Objective Optimization")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Learning status
        status_group = QGroupBox("Learning Status")
        status_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        status_layout = QGridLayout()
        
        status_layout.addWidget(QLabel("Learning Mode:"), 0, 0)
        self.learning_mode = QComboBox()
        self.learning_mode.addItems(["DQN", "Policy Gradient", "Hybrid", "Heuristic"])
        self.learning_mode.setCurrentIndex(2)  # Hybrid
        self.learning_mode.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        status_layout.addWidget(self.learning_mode, 0, 1)
        
        status_layout.addWidget(QLabel("Exploration Rate (ε):"), 1, 0)
        self.epsilon_label = QLabel("0.10")
        self.epsilon_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        status_layout.addWidget(self.epsilon_label, 1, 1)
        
        status_layout.addWidget(QLabel("Total Reward:"), 2, 0)
        self.total_reward_label = QLabel("0.0")
        self.total_reward_label.setStyleSheet("color: #00ff00; font-size: 12px;")
        status_layout.addWidget(self.total_reward_label, 2, 1)
        
        status_layout.addWidget(QLabel("Experiences:"), 3, 0)
        self.experiences_label = QLabel("0")
        self.experiences_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        status_layout.addWidget(self.experiences_label, 3, 1)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Multi-objective optimization
        objectives_group = QGroupBox("Multi-Objective Optimization Weights")
        objectives_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        objectives_layout = QGridLayout()
        
        objectives_layout.addWidget(QLabel("Performance Weight:"), 0, 0)
        self.performance_weight = QDoubleSpinBox()
        self.performance_weight.setRange(0.0, 1.0)
        self.performance_weight.setValue(0.6)
        self.performance_weight.setSingleStep(0.1)
        self.performance_weight.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        objectives_layout.addWidget(self.performance_weight, 0, 1)
        
        objectives_layout.addWidget(QLabel("Safety Weight:"), 1, 0)
        self.safety_weight = QDoubleSpinBox()
        self.safety_weight.setRange(0.0, 1.0)
        self.safety_weight.setValue(0.3)
        self.safety_weight.setSingleStep(0.1)
        self.safety_weight.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        objectives_layout.addWidget(self.safety_weight, 1, 1)
        
        objectives_layout.addWidget(QLabel("Efficiency Weight:"), 2, 0)
        self.efficiency_weight = QDoubleSpinBox()
        self.efficiency_weight.setRange(0.0, 1.0)
        self.efficiency_weight.setValue(0.1)
        self.efficiency_weight.setSingleStep(0.1)
        self.efficiency_weight.setStyleSheet("color: #ffffff; background-color: #2a2a2a;")
        objectives_layout.addWidget(self.efficiency_weight, 2, 1)
        
        objectives_group.setLayout(objectives_layout)
        layout.addWidget(objectives_group)
        
        # Recommended actions
        actions_group = QGroupBox("AI-Recommended Tuning Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        actions_layout = QVBoxLayout()
        
        self.actions_table = QTableWidget()
        self.actions_table.setRowCount(10)
        self.actions_table.setColumnCount(5)
        self.actions_table.setHorizontalHeaderLabels([
            "Parameter", "Adjustment", "Confidence", "Expected Reward", "Safety Score"
        ])
        self.actions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.actions_table.setMinimumHeight(self.scaler.get_scaled_size(200))
        table_padding = self.scaler.get_scaled_size(5)
        table_border = self.scaler.get_scaled_size(1)
        self.actions_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #0a0a0a;
                color: #ffffff;
                gridline-color: #404040;
                border: {table_border}px solid #404040;
            }}
            QHeaderView::section {{
                background-color: #2a2a2a;
                color: #ffffff;
                padding: {table_padding}px;
                border: {table_border}px solid #404040;
            }}
        """)
        actions_layout.addWidget(self.actions_table)
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        layout.addStretch()
        return panel
    
    def _create_statistics_tab(self) -> QWidget:
        """Create learning statistics tab."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        margin = self.scaler.get_scaled_size(10)
        layout.setContentsMargins(margin, margin, margin, margin)
        
        title = QLabel("Learning Statistics & Model Performance")
        title_font = self.scaler.get_scaled_font_size(14)
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        # Statistics display
        stats_group = QGroupBox("Learning Statistics")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_font = self.scaler.get_scaled_font_size(10)
        stats_border = self.scaler.get_scaled_size(1)
        self.stats_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: {stats_font}px;
                border: {stats_border}px solid #404040;
            }}
        """)
        self.stats_text.setMinimumHeight(self.scaler.get_scaled_size(400))
        stats_layout.addWidget(self.stats_text)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Model controls
        controls_group = QGroupBox("Model Controls")
        controls_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px; font-weight: bold; color: #ffffff;
                border: 1px solid #404040; border-radius: 3px;
                margin-top: 10px; padding-top: 10px;
            }
        """)
        controls_layout = QHBoxLayout()
        
        self.save_model_btn = QPushButton("Save Learned Model")
        btn_padding_v = self.scaler.get_scaled_size(5)
        btn_padding_h = self.scaler.get_scaled_size(15)
        btn_font = self.scaler.get_scaled_font_size(11)
        self.save_model_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0080ff;
                color: #ffffff;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
            }}
        """)
        controls_layout.addWidget(self.save_model_btn)
        
        self.load_model_btn = QPushButton("Load Learned Model")
        self.load_model_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #0080ff;
                color: #ffffff;
                padding: {btn_padding_v}px {btn_padding_h}px;
                font-size: {btn_font}px;
            }}
        """)
        controls_layout.addWidget(self.load_model_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        layout.addStretch()
        return panel
    
    def _start_update_timer(self) -> None:
        """Start update timer."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_displays)
        self.update_timer.start(1000)  # Update every second
    
    def _update_displays(self) -> None:
        """Update all displays."""
        if self.learning_engine:
            stats = self.learning_engine.get_learning_statistics()
            self.epsilon_label.setText(f"{stats.get('epsilon', 0.1):.3f}")
            self.total_reward_label.setText(f"{stats.get('total_reward', 0.0):.2f}")
            self.experiences_label.setText(str(stats.get('memory_size', 0)))
            
            # Update statistics text
            stats_text = f"""
Learning Statistics:
====================
Episodes: {stats.get('episode_count', 0)}
Total Reward: {stats.get('total_reward', 0.0):.2f}
Average Reward: {stats.get('average_reward', 0.0):.2f}
Exploration Rate (ε): {stats.get('epsilon', 0.1):.3f}
Memory Size: {stats.get('memory_size', 0)}
Learned Optimal Configs: {stats.get('learned_optimal_count', 0)}
"""
            self.stats_text.setText(stats_text)
    
    def update_telemetry(self, data: Dict[str, float]) -> None:
        """Update with telemetry data."""
        # Update diagnostics
        if self.diagnostics_engine:
            alerts = self.diagnostics_engine.update(data)
            self._update_diagnostics_display(alerts)
        
        # Update learning engine
        if self.learning_engine:
            # Select action
            action = self.learning_engine.select_action(data, "fuel_trim")
            self._update_actions_display([action])
            
            # Update multi-objective weights
            if hasattr(self, 'performance_weight'):
                objectives = {
                    "performance": self.performance_weight.value(),
                    "safety": self.safety_weight.value(),
                    "efficiency": self.efficiency_weight.value(),
                }
                self.learning_engine.optimize_multi_objective(data, objectives)
    
    def _update_diagnostics_display(self, alerts: List) -> None:
        """Update diagnostics display."""
        if not alerts:
            return
        
        # Update alerts table
        self.alerts_table.setRowCount(len(alerts))
        for row, alert in enumerate(alerts[:20]):  # Limit to 20
            if hasattr(alert, 'component'):
                self.alerts_table.setItem(row, 0, QTableWidgetItem(alert.component))
                self.alerts_table.setItem(row, 1, QTableWidgetItem(alert.alert_type))
                
                severity_item = QTableWidgetItem(alert.severity)
                if alert.severity == "critical":
                    severity_item.setForeground(QBrush(QColor("#ff0000")))
                elif alert.severity == "high":
                    severity_item.setForeground(QBrush(QColor("#ff8000")))
                else:
                    severity_item.setForeground(QBrush(QColor("#ffff00")))
                self.alerts_table.setItem(row, 2, severity_item)
                
                self.alerts_table.setItem(row, 3, QTableWidgetItem(f"{alert.confidence:.2f}"))
                self.alerts_table.setItem(row, 4, QTableWidgetItem(alert.message[:50]))
        
        # Update component health
        if self.diagnostics_engine:
            component_health = self.diagnostics_engine.get_component_health()
            self.components_table.setRowCount(len(component_health))
            
            for row, (component, health) in enumerate(component_health.items()):
                self.components_table.setItem(row, 0, QTableWidgetItem(component))
                self.components_table.setItem(row, 1, QTableWidgetItem(f"{health.health_score:.1f}"))
                
                status_item = QTableWidgetItem(health.status)
                if health.status == "excellent":
                    status_item.setForeground(QBrush(QColor("#00ff00")))
                elif health.status == "good":
                    status_item.setForeground(QBrush(QColor("#0080ff")))
                elif health.status == "fair":
                    status_item.setForeground(QBrush(QColor("#ffff00")))
                elif health.status == "poor":
                    status_item.setForeground(QBrush(QColor("#ff8000")))
                else:
                    status_item.setForeground(QBrush(QColor("#ff0000")))
                self.components_table.setItem(row, 2, status_item)
                
                rul_text = f"{health.remaining_useful_life:.1f}" if health.remaining_useful_life else "N/A"
                self.components_table.setItem(row, 3, QTableWidgetItem(rul_text))
                self.components_table.setItem(row, 4, QTableWidgetItem(health.trend))
                self.components_table.setItem(row, 5, QTableWidgetItem(f"{health.confidence:.2f}"))
            
            # Update overall health
            overall_score = self.diagnostics_engine.get_overall_health_score()
            self.overall_health_score.setText(f"{overall_score:.1f}/100")
            
            if overall_score >= 80:
                self.overall_status.setText("Excellent")
                self.overall_status.setStyleSheet("font-size: 14px; color: #00ff00;")
            elif overall_score >= 60:
                self.overall_status.setText("Good")
                self.overall_status.setStyleSheet("font-size: 14px; color: #0080ff;")
            elif overall_score >= 40:
                self.overall_status.setText("Fair")
                self.overall_status.setStyleSheet("font-size: 14px; color: #ffff00;")
            else:
                self.overall_status.setText("Poor")
                self.overall_status.setStyleSheet("font-size: 14px; color: #ff0000;")
    
    def _update_actions_display(self, actions: List) -> None:
        """Update actions display."""
        if not actions:
            return
        
        self.actions_table.setRowCount(len(actions))
        for row, action in enumerate(actions[:10]):  # Limit to 10
            if hasattr(action, 'parameter'):
                self.actions_table.setItem(row, 0, QTableWidgetItem(action.parameter))
                self.actions_table.setItem(row, 1, QTableWidgetItem(f"{action.adjustment:+.2f}%"))
                self.actions_table.setItem(row, 2, QTableWidgetItem(f"{action.confidence:.2f}"))
                self.actions_table.setItem(row, 3, QTableWidgetItem(f"{action.expected_reward:.2f}"))
                
                safety_item = QTableWidgetItem(f"{action.safety_score:.2f}")
                if action.safety_score > 0.8:
                    safety_item.setForeground(QBrush(QColor("#00ff00")))
                elif action.safety_score > 0.5:
                    safety_item.setForeground(QBrush(QColor("#ffff00")))
                else:
                    safety_item.setForeground(QBrush(QColor("#ff0000")))
                self.actions_table.setItem(row, 4, safety_item)

