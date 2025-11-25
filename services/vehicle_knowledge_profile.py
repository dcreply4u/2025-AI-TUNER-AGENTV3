"""
Vehicle-Specific Knowledge Profile

Builds and maintains knowledge profiles for individual vehicles,
learning their characteristics, successful tunings, and optimal settings.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)


@dataclass
class VehicleSpecs:
    """Vehicle specifications."""
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    engine: Optional[str] = None
    displacement: Optional[float] = None  # liters
    forced_induction: Optional[str] = None  # "turbo", "supercharger", "na"
    fuel_type: Optional[str] = None  # "gasoline", "e85", "diesel"
    modifications: List[str] = field(default_factory=list)


@dataclass
class TuningHistory:
    """History of tuning changes for vehicle."""
    timestamp: float
    change_type: str  # "fuel", "timing", "boost", etc.
    old_value: Any
    new_value: Any
    result: Optional[Dict[str, float]] = None  # Performance metrics
    success: bool = False
    notes: str = ""


@dataclass
class OptimalSettings:
    """Optimal settings learned for vehicle."""
    setting_type: str
    value: Any
    conditions: Dict[str, Any]  # When this setting is optimal
    confidence: float  # 0-1
    usage_count: int = 0
    last_updated: float = field(default_factory=time.time)


@dataclass
class KnownIssue:
    """Known issue with vehicle."""
    issue_id: str
    description: str
    symptoms: List[str]
    solutions: List[str]
    severity: str  # "low", "medium", "high", "critical"
    first_seen: float = field(default_factory=time.time)
    occurrences: int = 1


class VehicleKnowledgeProfile:
    """
    Vehicle-specific knowledge profile.
    
    Learns and stores:
    - Vehicle specifications
    - Successful tuning settings
    - Known issues and solutions
    - Optimal configurations
    - Tuning history
    """
    
    def __init__(self, vehicle_id: str, storage_path: Optional[Path] = None):
        """
        Initialize vehicle knowledge profile.
        
        Args:
            vehicle_id: Unique vehicle identifier
            storage_path: Path to store profile data
        """
        self.vehicle_id = vehicle_id
        self.storage_path = storage_path or Path(f"data/vehicles/{vehicle_id}.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Vehicle information
        self.specs = VehicleSpecs()
        self.tuning_history: List[TuningHistory] = []
        self.optimal_settings: Dict[str, OptimalSettings] = {}
        self.known_issues: Dict[str, KnownIssue] = {}
        
        # Statistics
        self.total_tuning_sessions: int = 0
        self.successful_sessions: int = 0
        self.last_tuning_date: Optional[float] = None
        
        # Load existing profile
        self._load_profile()
    
    def update_specs(self, **kwargs) -> None:
        """Update vehicle specifications."""
        for key, value in kwargs.items():
            if hasattr(self.specs, key):
                setattr(self.specs, key, value)
        self._save_profile()
    
    def record_tuning_change(
        self,
        change_type: str,
        old_value: Any,
        new_value: Any,
        result: Optional[Dict[str, float]] = None,
        success: bool = False,
        notes: str = ""
    ) -> None:
        """
        Record a tuning change.
        
        Args:
            change_type: Type of change (fuel, timing, boost, etc.)
            old_value: Previous value
            new_value: New value
            result: Performance results
            success: Whether change was successful
            notes: Additional notes
        """
        history_entry = TuningHistory(
            timestamp=time.time(),
            change_type=change_type,
            old_value=old_value,
            new_value=new_value,
            result=result,
            success=success,
            notes=notes,
        )
        
        self.tuning_history.append(history_entry)
        self.total_tuning_sessions += 1
        self.last_tuning_date = time.time()
        
        if success:
            self.successful_sessions += 1
            self._update_optimal_settings(change_type, new_value, result)
        
        # Keep only recent history (last 200 entries)
        if len(self.tuning_history) > 200:
            self.tuning_history = self.tuning_history[-200:]
        
        self._save_profile()
    
    def get_optimal_setting(
        self,
        setting_type: str,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Optional[OptimalSettings]:
        """
        Get optimal setting for given type and conditions.
        
        Args:
            setting_type: Type of setting (fuel, timing, etc.)
            conditions: Current conditions (RPM, load, etc.)
        
        Returns:
            Optimal settings or None
        """
        if setting_type in self.optimal_settings:
            setting = self.optimal_settings[setting_type]
            # Check if conditions match (simple matching for now)
            if conditions:
                # Could do more sophisticated matching
                pass
            return setting
        return None
    
    def get_vehicle_specific_advice(
        self,
        question: str,
        current_telemetry: Optional[Dict[str, float]] = None
    ) -> Optional[str]:
        """
        Get vehicle-specific advice based on history.
        
        Args:
            question: User question
            current_telemetry: Current telemetry data
        
        Returns:
            Vehicle-specific advice or None
        """
        question_lower = question.lower()
        
        # Check for known issues
        for issue in self.known_issues.values():
            if any(symptom in question_lower for symptom in issue.symptoms):
                advice = f"Known issue with this vehicle: {issue.description}\n"
                if issue.solutions:
                    advice += f"Solutions: {', '.join(issue.solutions)}"
                return advice
        
        # Check optimal settings
        if "fuel" in question_lower or "afr" in question_lower:
            fuel_setting = self.get_optimal_setting("fuel")
            if fuel_setting and fuel_setting.confidence > 0.7:
                return f"For this vehicle, optimal fuel settings have been: {fuel_setting.value}"
        
        if "timing" in question_lower:
            timing_setting = self.get_optimal_setting("timing")
            if timing_setting and timing_setting.confidence > 0.7:
                return f"For this vehicle, optimal timing settings have been: {timing_setting.value}"
        
        # Check tuning history
        if "worked" in question_lower or "success" in question_lower:
            successful_changes = [h for h in self.tuning_history if h.success]
            if successful_changes:
                recent_success = successful_changes[-1]
                return (
                    f"Recent successful change: {recent_success.change_type} = "
                    f"{recent_success.new_value} (resulted in improved performance)"
                )
        
        return None
    
    def add_known_issue(
        self,
        description: str,
        symptoms: List[str],
        solutions: List[str],
        severity: str = "medium"
    ) -> None:
        """
        Add known issue for vehicle.
        
        Args:
            description: Issue description
            symptoms: List of symptoms
            solutions: List of solutions
            severity: Issue severity
        """
        issue_id = f"issue_{int(time.time())}"
        issue = KnownIssue(
            issue_id=issue_id,
            description=description,
            symptoms=symptoms,
            solutions=solutions,
            severity=severity,
        )
        
        self.known_issues[issue_id] = issue
        self._save_profile()
    
    def _update_optimal_settings(
        self,
        setting_type: str,
        value: Any,
        result: Optional[Dict[str, float]]
    ) -> None:
        """Update optimal settings based on successful tuning."""
        if setting_type not in self.optimal_settings:
            self.optimal_settings[setting_type] = OptimalSettings(
                setting_type=setting_type,
                value=value,
                conditions={},
                confidence=0.5,
                usage_count=1,
            )
        else:
            setting = self.optimal_settings[setting_type]
            setting.usage_count += 1
            # Increase confidence with more successful uses
            setting.confidence = min(1.0, 0.5 + (setting.usage_count * 0.1))
            setting.last_updated = time.time()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vehicle profile statistics."""
        return {
            "vehicle_id": self.vehicle_id,
            "specs": asdict(self.specs),
            "total_tuning_sessions": self.total_tuning_sessions,
            "successful_sessions": self.successful_sessions,
            "success_rate": (
                self.successful_sessions / self.total_tuning_sessions
                if self.total_tuning_sessions > 0 else 0.0
            ),
            "optimal_settings_count": len(self.optimal_settings),
            "known_issues_count": len(self.known_issues),
            "last_tuning_date": self.last_tuning_date,
        }
    
    def _save_profile(self) -> None:
        """Save profile to disk."""
        try:
            data = {
                "vehicle_id": self.vehicle_id,
                "specs": asdict(self.specs),
                "tuning_history": [asdict(h) for h in self.tuning_history[-100:]],  # Keep last 100
                "optimal_settings": {
                    k: asdict(v) for k, v in self.optimal_settings.items()
                },
                "known_issues": {
                    k: asdict(v) for k, v in self.known_issues.items()
                },
                "statistics": {
                    "total_tuning_sessions": self.total_tuning_sessions,
                    "successful_sessions": self.successful_sessions,
                    "last_tuning_date": self.last_tuning_date,
                },
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save vehicle profile: %s", e)
    
    def _load_profile(self) -> None:
        """Load profile from disk."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Load specs
            if "specs" in data:
                self.specs = VehicleSpecs(**data["specs"])
            
            # Load tuning history
            self.tuning_history = [
                TuningHistory(**h) for h in data.get("tuning_history", [])
            ]
            
            # Load optimal settings
            self.optimal_settings = {
                k: OptimalSettings(**v)
                for k, v in data.get("optimal_settings", {}).items()
            }
            
            # Load known issues
            self.known_issues = {
                k: KnownIssue(**v)
                for k, v in data.get("known_issues", {}).items()
            }
            
            # Load statistics
            stats = data.get("statistics", {})
            self.total_tuning_sessions = stats.get("total_tuning_sessions", 0)
            self.successful_sessions = stats.get("successful_sessions", 0)
            self.last_tuning_date = stats.get("last_tuning_date")
            
            LOGGER.info("Loaded vehicle profile: %s (%d sessions)", self.vehicle_id, self.total_tuning_sessions)
        except Exception as e:
            LOGGER.error("Failed to load vehicle profile: %s", e)


__all__ = [
    "VehicleKnowledgeProfile",
    "VehicleSpecs",
    "TuningHistory",
    "OptimalSettings",
    "KnownIssue",
]









