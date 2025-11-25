"""
AI Racing Coach Service
Real-time voice coaching like professional instructor.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class CoachingEvent(Enum):
    """Coaching event types."""
    BRAKE_EARLIER = "brake_earlier"
    BRAKE_LATER = "brake_later"
    THROTTLE_EARLIER = "throttle_earlier"
    THROTTLE_LATER = "throttle_later"
    SHIFT_UP = "shift_up"
    SHIFT_DOWN = "shift_down"
    CORNER_ENTRY = "corner_entry"
    CORNER_EXIT = "corner_exit"
    STRAIGHT_LINE = "straight_line"
    OPTIMIZATION = "optimization"


@dataclass
class CoachingAdvice:
    """Coaching advice."""
    event_type: CoachingEvent
    message: str
    priority: int = 1  # 1-5, higher is more urgent
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LapAnalysis:
    """Lap analysis."""
    lap_number: int
    lap_time: float
    best_lap_time: Optional[float] = None
    improvement: Optional[float] = None  # Seconds improvement
    sectors: List[float] = field(default_factory=list)
    advice: List[CoachingAdvice] = field(default_factory=list)


class AIRacingCoach:
    """
    AI Racing Coach service.
    
    Features:
    - Real-time voice coaching
    - Lap analysis
    - Sector comparison
    - Personalized feedback
    - Learning from best laps
    """
    
    def __init__(
        self,
        voice_enabled: bool = True,
        learning_enabled: bool = True,
    ):
        """
        Initialize AI racing coach.
        
        Args:
            voice_enabled: Enable voice output
            learning_enabled: Learn from user's best laps
        """
        self.voice_enabled = voice_enabled
        self.learning_enabled = learning_enabled
        
        # Learning data
        self.best_laps: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Any] = {}
        self.coaching_history: List[CoachingAdvice] = []
        
        # Current session
        self.current_lap: Optional[Dict[str, Any]] = None
        self.lap_start_time: Optional[float] = None
        self.sector_times: List[float] = []
    
    def start_lap(self) -> None:
        """Start a new lap."""
        self.lap_start_time = time.time()
        self.sector_times = []
        self.current_lap = {
            "start_time": self.lap_start_time,
            "telemetry": [],
        }
        LOGGER.info("Lap started")
    
    def process_telemetry(
        self,
        telemetry_data: Dict[str, Any],
        gps_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[CoachingAdvice]:
        """
        Process telemetry and provide coaching advice.
        
        Args:
            telemetry_data: Current telemetry data
            gps_data: GPS/location data
        
        Returns:
            CoachingAdvice if advice available
        """
        if not self.current_lap:
            return None
        
        # Store telemetry
        self.current_lap["telemetry"].append({
            "timestamp": time.time(),
            "data": telemetry_data,
        })
        
        # Analyze and provide advice
        advice = self._analyze_and_advise(telemetry_data, gps_data)
        
        if advice:
            self.coaching_history.append(advice)
            if self.voice_enabled:
                self._speak_advice(advice)
        
        return advice
    
    def end_lap(self) -> LapAnalysis:
        """
        End current lap and analyze.
        
        Returns:
            LapAnalysis with results
        """
        if not self.current_lap or not self.lap_start_time:
            LOGGER.warning("No active lap to end")
            return LapAnalysis(lap_number=0, lap_time=0.0)
        
        lap_time = time.time() - self.lap_start_time
        
        # Get best lap time
        best_lap_time = self._get_best_lap_time()
        improvement = None
        if best_lap_time:
            improvement = best_lap_time - lap_time
        
        # Analyze lap
        advice = self._analyze_lap(self.current_lap, lap_time, best_lap_time)
        
        # Store if best
        if not best_lap_time or lap_time < best_lap_time:
            self.best_laps.append({
                "lap_time": lap_time,
                "sector_times": self.sector_times.copy(),
                "telemetry": self.current_lap["telemetry"].copy(),
                "timestamp": time.time(),
            })
            # Keep only top 10
            self.best_laps = sorted(self.best_laps, key=lambda x: x["lap_time"])[:10]
        
        analysis = LapAnalysis(
            lap_number=len(self.best_laps),
            lap_time=lap_time,
            best_lap_time=best_lap_time,
            improvement=improvement,
            sectors=self.sector_times.copy(),
            advice=advice,
        )
        
        # Reset
        self.current_lap = None
        self.lap_start_time = None
        self.sector_times = []
        
        LOGGER.info("Lap completed: %.2fs (best: %.2fs)", lap_time, best_lap_time or 0.0)
        return analysis
    
    def _analyze_and_advise(
        self,
        telemetry: Dict[str, Any],
        gps_data: Optional[Dict[str, Any]],
    ) -> Optional[CoachingAdvice]:
        """Analyze telemetry and generate advice."""
        # Check RPM
        rpm = telemetry.get("rpm", 0)
        if rpm > 7000:
            return CoachingAdvice(
                event_type=CoachingEvent.SHIFT_UP,
                message="Shift up now",
                priority=3,
            )
        elif rpm < 2000:
            return CoachingAdvice(
                event_type=CoachingEvent.SHIFT_DOWN,
                message="Shift down for more power",
                priority=2,
            )
        
        # Check throttle
        throttle = telemetry.get("throttle_position", 0)
        if throttle < 50 and rpm > 5000:
            return CoachingAdvice(
                event_type=CoachingEvent.THROTTLE_EARLIER,
                message="Get on throttle earlier",
                priority=2,
            )
        
        # Check speed (if GPS available)
        if gps_data:
            speed = gps_data.get("speed", 0)
            # Would compare with best lap data for specific location
        
        return None
    
    def _analyze_lap(
        self,
        lap_data: Dict[str, Any],
        lap_time: float,
        best_lap_time: Optional[float],
    ) -> List[CoachingAdvice]:
        """Analyze completed lap and provide feedback."""
        advice = []
        
        if best_lap_time:
            if lap_time < best_lap_time:
                advice.append(CoachingAdvice(
                    event_type=CoachingEvent.OPTIMIZATION,
                    message=f"New best lap! {lap_time:.2f}s (improved by {best_lap_time - lap_time:.2f}s)",
                    priority=5,
                ))
            else:
                improvement_needed = lap_time - best_lap_time
                advice.append(CoachingAdvice(
                    event_type=CoachingEvent.OPTIMIZATION,
                    message=f"Lap time: {lap_time:.2f}s (best: {best_lap_time:.2f}s, need {improvement_needed:.2f}s improvement)",
                    priority=2,
                ))
        else:
            advice.append(CoachingAdvice(
                event_type=CoachingEvent.OPTIMIZATION,
                message=f"First lap: {lap_time:.2f}s",
                priority=1,
            ))
        
        # Analyze sectors if available
        if self.sector_times and len(self.sector_times) >= 2:
            # Compare sectors
            for i, sector_time in enumerate(self.sector_times):
                if i < len(self.best_laps) and self.best_laps:
                    best_sectors = self.best_laps[0].get("sector_times", [])
                    if i < len(best_sectors):
                        sector_diff = sector_time - best_sectors[i]
                        if sector_diff > 0.5:  # Lost more than 0.5s
                            advice.append(CoachingAdvice(
                                event_type=CoachingEvent.OPTIMIZATION,
                                message=f"Sector {i+1} lost {sector_diff:.2f}s - focus on this section",
                                priority=3,
                            ))
        
        return advice
    
    def _get_best_lap_time(self) -> Optional[float]:
        """Get best lap time."""
        if not self.best_laps:
            return None
        return min(lap["lap_time"] for lap in self.best_laps)
    
    def _speak_advice(self, advice: CoachingAdvice) -> None:
        """Speak coaching advice (voice output)."""
        # In real implementation, would use TTS
        LOGGER.info("Coaching: %s", advice.message)
    
    def mark_sector(self) -> None:
        """Mark sector time."""
        if self.lap_start_time:
            sector_time = time.time() - (self.sector_times[-1] if self.sector_times else self.lap_start_time)
            self.sector_times.append(sector_time)
            LOGGER.info("Sector %d: %.2fs", len(self.sector_times), sector_time)
    
    def get_coaching_summary(self) -> Dict[str, Any]:
        """Get coaching session summary."""
        return {
            "total_laps": len(self.best_laps),
            "best_lap_time": self._get_best_lap_time(),
            "total_advice": len(self.coaching_history),
            "recent_advice": self.coaching_history[-10:] if self.coaching_history else [],
        }
