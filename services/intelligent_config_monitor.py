"""
Intelligent Configuration Monitor
Monitors configuration changes and provides proactive AI advice
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from services.config_version_control import (
    ConfigVersionControl,
    ConfigChange,
    ChangeType,
    ChangeSeverity,
)
from services.ai_advisor_q import AIAdvisorQ

LOGGER = logging.getLogger(__name__)


@dataclass
class ConfigWarning:
    """Configuration warning."""
    severity: str  # "info", "warning", "critical"
    message: str
    suggestion: Optional[str] = None
    alternative_value: Optional[Any] = None
    reasoning: str = ""


class IntelligentConfigMonitor:
    """
    Intelligent configuration monitor with proactive AI advice.
    
    Features:
    - Monitors configuration changes in real-time
    - Analyzes historical data
    - Provides proactive warnings
    - Suggests better alternatives
    - Learns from past configurations
    """
    
    def __init__(self, config_vc: Optional[ConfigVersionControl] = None, advisor: Optional[AIAdvisorQ] = None):
        """
        Initialize intelligent config monitor.
        
        Args:
            config_vc: Configuration version control instance
            advisor: AI advisor instance
        """
        self.config_vc = config_vc or ConfigVersionControl()
        self.advisor = advisor
        
        # Change monitoring
        self.pending_changes: Dict[str, ConfigChange] = {}
        self.active_warnings: List[ConfigWarning] = []
        
        # Historical analysis cache
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timeout = 300  # 5 minutes
    
    def monitor_change(
        self,
        change_type: ChangeType,
        category: str,
        parameter: str,
        old_value: Any,
        new_value: Any,
        telemetry: Optional[Dict[str, float]] = None,
    ) -> List[ConfigWarning]:
        """
        Monitor a configuration change and provide warnings/suggestions.
        
        Args:
            change_type: Type of change
            category: Category
            parameter: Parameter name
            old_value: Previous value
            new_value: New value
            telemetry: Current telemetry data
            
        Returns:
            List of warnings and suggestions
        """
        warnings = []
        
        # Determine severity
        severity = self._determine_severity(category, parameter, old_value, new_value)
        
        # Record change
        change = self.config_vc.record_change(
            change_type=change_type,
            category=category,
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            severity=severity,
            telemetry=telemetry,
        )
        
        # Analyze change impact
        analysis = self.config_vc.analyze_change_impact(change)
        
        # Generate warnings from analysis
        for warning_msg in analysis.get("warnings", []):
            warnings.append(ConfigWarning(
                severity="warning",
                message=warning_msg,
                reasoning="Historical data analysis",
            ))
        
        # Check for specific dangerous patterns
        pattern_warnings = self._check_dangerous_patterns(change, telemetry)
        warnings.extend(pattern_warnings)
        
        # Get suggestions from historical data
        suggestions = analysis.get("suggestions", [])
        for suggestion in suggestions:
            warnings.append(ConfigWarning(
                severity="info",
                message=suggestion,
                reasoning="Historical performance data",
            ))
        
        # Get AI advisor suggestion
        if self.advisor:
            ai_suggestion = self._get_ai_suggestion(change, telemetry)
            if ai_suggestion:
                warnings.append(ai_suggestion)
        
        # Store pending change
        self.pending_changes[change.change_id] = change
        self.active_warnings = warnings
        
        return warnings
    
    def _determine_severity(
        self,
        category: str,
        parameter: str,
        old_value: Any,
        new_value: Any,
    ) -> ChangeSeverity:
        """Determine change severity."""
        # Critical parameters
        critical_params = [
            "rev_limit", "egt_limit", "lean_cut", "knock_retard",
            "boost_limit", "fuel_cut",
        ]
        
        if any(critical in parameter.lower() for critical in critical_params):
            return ChangeSeverity.CRITICAL
        
        # High impact parameters
        high_impact = [
            "ignition_timing", "fuel_ve", "boost_target", "nitrous_activation",
        ]
        
        if any(high in parameter.lower() for high in high_impact):
            # Check magnitude of change
            if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                change_pct = abs((new_value - old_value) / old_value * 100) if old_value != 0 else abs(new_value)
                if change_pct > 20:
                    return ChangeSeverity.HIGH
                elif change_pct > 10:
                    return ChangeSeverity.MEDIUM
        
        return ChangeSeverity.MEDIUM
    
    def _check_dangerous_patterns(
        self,
        change: ConfigChange,
        telemetry: Optional[Dict[str, float]],
    ) -> List[ConfigWarning]:
        """Check for dangerous configuration patterns."""
        warnings = []
        
        # Get recent changes
        recent_changes = [
            c for c in self.pending_changes.values()
            if c.change_id != change.change_id
            and time.time() - c.timestamp < 60  # Last minute
        ]
        
        # Pattern 1: High timing + High boost
        if "timing" in change.parameter.lower() or "ignition" in change.category.lower():
            boost_changes = [c for c in recent_changes if "boost" in c.category.lower()]
            if boost_changes:
                timing_val = change.new_value if isinstance(change.new_value, (int, float)) else 0
                if timing_val > 30:  # High advance
                    warnings.append(ConfigWarning(
                        severity="critical",
                        message=f"⚠️ CRITICAL: High ignition advance ({timing_val:.1f}°) with boost changes detected!",
                        suggestion="Reduce timing to 25° or less when running boost, or monitor knock sensor closely.",
                        alternative_value=min(25.0, timing_val - 5) if isinstance(timing_val, (int, float)) else None,
                        reasoning="High timing + boost = high knock risk",
                    ))
        
        # Pattern 2: Lean fuel + High load
        if "fuel" in change.parameter.lower() or "ve" in change.parameter.lower():
            if isinstance(change.new_value, (int, float)) and isinstance(change.old_value, (int, float)):
                fuel_reduction = change.old_value - change.new_value
                if fuel_reduction > 10:  # Significant fuel reduction
                    # Check telemetry for high load
                    if telemetry:
                        load = telemetry.get("load", telemetry.get("MAP", 0))
                        rpm = telemetry.get("RPM", telemetry.get("Engine_RPM", 0))
                        
                        if load > 80 or rpm > 6000:
                            warnings.append(ConfigWarning(
                                severity="critical",
                                message=f"⚠️ CRITICAL: Large fuel reduction ({fuel_reduction:.1f}%) at high load/RPM!",
                                suggestion="Add fuel back or reduce load. Lean condition at high load can cause engine damage.",
                                alternative_value=change.old_value,  # Suggest reverting
                                reasoning="Lean condition at high load is extremely dangerous",
                            ))
        
        # Pattern 3: Nitrous without fuel enrichment
        if "nitrous" in change.category.lower():
            # Check if fuel offset is configured
            fuel_changes = [c for c in recent_changes if "fuel" in c.category.lower()]
            if not fuel_changes:
                warnings.append(ConfigWarning(
                    severity="high",
                    message="⚠️ Nitrous activation requires additional fuel!",
                    suggestion="Configure fuel offset map before activating nitrous. Typical: +30-50% fuel with nitrous.",
                    reasoning="Nitrous requires significant fuel enrichment to prevent lean condition",
                ))
        
        # Pattern 4: EGT limit too high
        if "egt" in change.parameter.lower() and "limit" in change.parameter.lower():
            if isinstance(change.new_value, (int, float)):
                if change.new_value > 1600:  # Too high
                    warnings.append(ConfigWarning(
                        severity="high",
                        message=f"⚠️ EGT limit ({change.new_value:.0f}°C) is very high!",
                        suggestion="Consider reducing to 1500°C for safety. High EGT can damage exhaust valves and turbo.",
                        alternative_value=1500.0,
                        reasoning="EGT above 1500°C is dangerous for most engines",
                    ))
        
        # Pattern 5: Rev limit too high
        if "rev_limit" in change.parameter.lower():
            if isinstance(change.new_value, (int, float)):
                if change.new_value > 8000:  # Very high
                    warnings.append(ConfigWarning(
                        severity="high",
                        message=f"⚠️ Rev limit ({change.new_value:.0f} RPM) is very high!",
                        suggestion="Ensure engine internals can handle this RPM. Consider valve float and piston speed limits.",
                        reasoning="High RPM requires proper engine preparation",
                    ))
        
        return warnings
    
    def _get_ai_suggestion(
        self,
        change: ConfigChange,
        telemetry: Optional[Dict[str, float]],
    ) -> Optional[ConfigWarning]:
        """Get AI advisor suggestion for configuration change."""
        if not self.advisor:
            return None
        
        # Build question for AI advisor
        question = f"I'm changing {change.category} {change.parameter} from {change.old_value} to {change.new_value}. "
        question += "Is this safe? What should I watch for?"
        
        if telemetry:
            question += f" Current RPM: {telemetry.get('RPM', 0):.0f}, Load: {telemetry.get('load', 0):.0f}%"
        
        # Get AI response
        response = self.advisor.ask(question, context={"change": change})
        
        # Parse response for suggestions
        if "warning" in response.lower() or "dangerous" in response.lower() or "critical" in response.lower():
            return ConfigWarning(
                severity="warning",
                message=f"Q says: {response}",
                reasoning="AI advisor analysis",
            )
        
        return None
    
    def get_best_alternative(
        self,
        category: str,
        parameter: str,
        current_value: Any,
        telemetry: Optional[Dict[str, float]] = None,
    ) -> Optional[Any]:
        """
        Get best alternative value based on historical data.
        
        Args:
            category: Configuration category
            parameter: Parameter name
            current_value: Current value
            telemetry: Current telemetry
            
        Returns:
            Suggested alternative value or None
        """
        # Get best performing config
        config_type_map = {
            "Fuel VE": ChangeType.ECU_TUNING,
            "Ignition Timing": ChangeType.ECU_TUNING,
            "Boost Control": ChangeType.ECU_TUNING,
            "Nitrous": ChangeType.MOTORSPORT,
        }
        
        config_type = config_type_map.get(category, ChangeType.ECU_TUNING)
        best_config = self.config_vc.get_best_performing_config(config_type)
        
        if best_config and parameter in best_config.configuration:
            best_value = best_config.configuration[parameter]
            
            # Only suggest if significantly different
            if isinstance(best_value, (int, float)) and isinstance(current_value, (int, float)):
                diff_pct = abs((best_value - current_value) / current_value * 100) if current_value != 0 else abs(best_value)
                if diff_pct > 5:  # More than 5% difference
                    return best_value
        
        return None
    
    def get_active_warnings(self) -> List[ConfigWarning]:
        """Get currently active warnings."""
        return self.active_warnings.copy()
    
    def clear_warnings(self) -> None:
        """Clear active warnings."""
        self.active_warnings = []
















