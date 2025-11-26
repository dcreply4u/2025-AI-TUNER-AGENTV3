"""
Session Review and Post-Analysis
Provides detailed post-session analysis with strengths, weaknesses, and recommendations.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)


@dataclass
class SessionMetrics:
    """Metrics for a session."""
    session_id: str
    duration: float  # seconds
    laps: int
    best_lap_time: float
    average_lap_time: float
    top_speed: float
    average_speed: float
    sectors: List[Dict[str, float]] = field(default_factory=list)
    telemetry_samples: List[Dict[str, float]] = field(default_factory=list)
    incidents: List[Dict[str, Any]] = field(default_factory=list)  # crashes, spins, etc.
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionAnalysis:
    """Complete session analysis."""
    session_id: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    theoretical_best_lap: Optional[float] = None
    performance_gap: Optional[float] = None  # seconds
    sector_analysis: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    consistency_score: float = 0.0  # 0-1
    improvement_areas: List[str] = field(default_factory=list)


class SessionReviewAnalyzer:
    """
    Analyzes sessions and provides detailed post-analysis reports.
    
    Features:
    - Strength/weakness identification
    - Theoretical best lap calculation
    - Sector-by-sector analysis
    - Consistency scoring
    - Improvement recommendations
    """
    
    def __init__(self):
        """Initialize session analyzer."""
        self.session_history: Dict[str, SessionMetrics] = {}
    
    def analyze_session(self, metrics: SessionMetrics) -> SessionAnalysis:
        """
        Analyze a session and generate report.
        
        Args:
            metrics: Session metrics to analyze
            
        Returns:
            Complete session analysis
        """
        analysis = SessionAnalysis(session_id=metrics.session_id)
        
        # Calculate consistency
        if metrics.laps > 1:
            lap_times = [s.get("lap_time", 0) for s in metrics.sectors if "lap_time" in s]
            if lap_times:
                avg_lap = sum(lap_times) / len(lap_times)
                variance = sum((t - avg_lap) ** 2 for t in lap_times) / len(lap_times)
                std_dev = variance ** 0.5
                # Consistency: lower std dev = higher consistency
                analysis.consistency_score = max(0, 1 - (std_dev / avg_lap)) if avg_lap > 0 else 0
        
        # Identify strengths
        analysis.strengths = self._identify_strengths(metrics)
        
        # Identify weaknesses
        analysis.weaknesses = self._identify_weaknesses(metrics)
        
        # Calculate theoretical best lap
        analysis.theoretical_best_lap = self._calculate_theoretical_best(metrics)
        if analysis.theoretical_best_lap and metrics.best_lap_time:
            analysis.performance_gap = metrics.best_lap_time - analysis.theoretical_best_lap
        
        # Sector analysis
        analysis.sector_analysis = self._analyze_sectors(metrics)
        
        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(metrics, analysis)
        
        # Improvement areas
        analysis.improvement_areas = self._identify_improvement_areas(metrics, analysis)
        
        return analysis
    
    def _identify_strengths(self, metrics: SessionMetrics) -> List[str]:
        """Identify session strengths."""
        strengths = []
        
        # Consistency
        if metrics.laps > 3:
            lap_times = [s.get("lap_time", 0) for s in metrics.sectors if "lap_time" in s]
            if lap_times:
                variance = sum((t - sum(lap_times)/len(lap_times)) ** 2 for t in lap_times) / len(lap_times)
                if variance < 0.5:  # Low variance = consistent
                    strengths.append("Excellent lap time consistency")
        
        # Speed
        if metrics.top_speed > 0:
            strengths.append(f"Good top speed: {metrics.top_speed:.1f} mph")
        
        # Few incidents
        if len(metrics.incidents) == 0:
            strengths.append("Clean session with no incidents")
        elif len(metrics.incidents) < metrics.laps * 0.1:  # Less than 10% of laps
            strengths.append("Good incident rate")
        
        # Improvement over session
        if metrics.laps > 5:
            early_laps = [s.get("lap_time", 0) for s in metrics.sectors[:3] if "lap_time" in s]
            late_laps = [s.get("lap_time", 0) for s in metrics.sectors[-3:] if "lap_time" in s]
            if early_laps and late_laps:
                early_avg = sum(early_laps) / len(early_laps)
                late_avg = sum(late_laps) / len(late_laps)
                if late_avg < early_avg * 0.98:  # 2% improvement
                    strengths.append("Showed improvement throughout session")
        
        return strengths
    
    def _identify_weaknesses(self, metrics: SessionMetrics) -> List[str]:
        """Identify session weaknesses."""
        weaknesses = []
        
        # Inconsistency
        if metrics.laps > 3:
            lap_times = [s.get("lap_time", 0) for s in metrics.sectors if "lap_time" in s]
            if lap_times:
                variance = sum((t - sum(lap_times)/len(lap_times)) ** 2 for t in lap_times) / len(lap_times)
                if variance > 2.0:  # High variance
                    weaknesses.append("Inconsistent lap times - work on consistency")
        
        # Many incidents
        if len(metrics.incidents) > metrics.laps * 0.2:  # More than 20% of laps
            weaknesses.append(f"High incident rate ({len(metrics.incidents)} incidents in {metrics.laps} laps)")
        
        # Slow sectors
        if metrics.sectors:
            sector_times = {}
            for sector in metrics.sectors:
                sector_num = sector.get("sector", 0)
                if sector_num not in sector_times:
                    sector_times[sector_num] = []
                sector_times[sector_num].append(sector.get("time", 0))
            
            for sector_num, times in sector_times.items():
                if times:
                    avg_time = sum(times) / len(times)
                    # Compare to best (simplified - would need reference data)
                    if avg_time > min(times) * 1.1:  # 10% slower than best
                        weaknesses.append(f"Sector {sector_num} shows room for improvement")
        
        return weaknesses
    
    def _calculate_theoretical_best(self, metrics: SessionMetrics) -> Optional[float]:
        """Calculate theoretical best lap from best sectors."""
        if not metrics.sectors:
            return None
        
        # Group by sector
        sector_bests = {}
        for sector in metrics.sectors:
            sector_num = sector.get("sector", 0)
            sector_time = sector.get("time", 0)
            if sector_num not in sector_bests or sector_time < sector_bests[sector_num]:
                sector_bests[sector_num] = sector_time
        
        if sector_bests:
            return sum(sector_bests.values())
        return None
    
    def _analyze_sectors(self, metrics: SessionMetrics) -> Dict[str, Dict[str, Any]]:
        """Analyze each sector."""
        analysis = {}
        
        if not metrics.sectors:
            return analysis
        
        # Group by sector
        sector_data = {}
        for sector in metrics.sectors:
            sector_num = sector.get("sector", 0)
            if sector_num not in sector_data:
                sector_data[sector_num] = []
            sector_data[sector_num].append(sector.get("time", 0))
        
        for sector_num, times in sector_data.items():
            if times:
                analysis[f"sector_{sector_num}"] = {
                    "best": min(times),
                    "average": sum(times) / len(times),
                    "worst": max(times),
                    "variance": sum((t - sum(times)/len(times)) ** 2 for t in times) / len(times),
                    "samples": len(times)
                }
        
        return analysis
    
    def _generate_recommendations(self, metrics: SessionMetrics, analysis: SessionAnalysis) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Consistency recommendations
        if analysis.consistency_score < 0.7:
            recommendations.append("Focus on consistency: Aim for lap times within 0.5 seconds of each other")
        
        # Sector-specific recommendations
        for sector_key, sector_data in analysis.sector_analysis.items():
            variance = sector_data.get("variance", 0)
            if variance > 1.0:
                recommendations.append(f"Work on {sector_key} consistency - high variance indicates inconsistent technique")
        
        # Performance gap
        if analysis.performance_gap and analysis.performance_gap > 2.0:
            recommendations.append(f"Theoretical best lap is {analysis.performance_gap:.2f} seconds faster - focus on combining best sectors")
        
        # Incident reduction
        if len(metrics.incidents) > metrics.laps * 0.15:
            recommendations.append("Reduce incidents: Focus on car control and smooth inputs")
        
        return recommendations
    
    def _identify_improvement_areas(self, metrics: SessionMetrics, analysis: SessionAnalysis) -> List[str]:
        """Identify specific areas for improvement."""
        areas = []
        
        # Based on weaknesses
        if "Inconsistent" in str(analysis.weaknesses):
            areas.append("Lap time consistency")
        
        if "Sector" in str(analysis.weaknesses):
            areas.append("Sector-specific technique")
        
        if "incident" in str(analysis.weaknesses).lower():
            areas.append("Car control and incident avoidance")
        
        # Based on performance gap
        if analysis.performance_gap and analysis.performance_gap > 1.0:
            areas.append("Combining best sectors into single lap")
        
        return areas
    
    def generate_report(self, analysis: SessionAnalysis) -> str:
        """Generate a formatted report."""
        report = []
        report.append("=" * 60)
        report.append("SESSION ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"\nSession ID: {analysis.session_id}")
        
        # Strengths
        if analysis.strengths:
            report.append("\n✅ STRENGTHS:")
            for strength in analysis.strengths:
                report.append(f"  • {strength}")
        
        # Weaknesses
        if analysis.weaknesses:
            report.append("\n⚠️ WEAKNESSES:")
            for weakness in analysis.weaknesses:
                report.append(f"  • {weakness}")
        
        # Performance metrics
        report.append("\n📊 PERFORMANCE METRICS:")
        if analysis.theoretical_best_lap:
            report.append(f"  Theoretical Best Lap: {analysis.theoretical_best_lap:.3f}s")
        if analysis.performance_gap:
            report.append(f"  Performance Gap: {analysis.performance_gap:.2f}s")
        report.append(f"  Consistency Score: {analysis.consistency_score:.2%}")
        
        # Recommendations
        if analysis.recommendations:
            report.append("\n💡 RECOMMENDATIONS:")
            for rec in analysis.recommendations:
                report.append(f"  • {rec}")
        
        # Improvement areas
        if analysis.improvement_areas:
            report.append("\n🎯 IMPROVEMENT AREAS:")
            for area in analysis.improvement_areas:
                report.append(f"  • {area}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


__all__ = ["SessionReviewAnalyzer", "SessionMetrics", "SessionAnalysis"]



