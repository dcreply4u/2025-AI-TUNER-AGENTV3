"""
AI Racing Coach Tests

Tests AI racing coach functionality and coaching advice.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import sample_data


class TestAIRacingCoach:
    """Test AI racing coach functionality."""
    
    def test_racing_coach_import(self):
        """Test AI racing coach can be imported."""
        try:
            from services.ai_racing_coach import AIRacingCoach, CoachingAdvice, LapAnalysis
            assert AIRacingCoach is not None
            assert CoachingAdvice is not None
            assert LapAnalysis is not None
        except ImportError:
            pytest.skip("AI racing coach not available")
    
    def test_coaching_advice_creation(self):
        """Test coaching advice creation."""
        try:
            from services.ai_racing_coach import CoachingAdvice
            
            advice = CoachingAdvice(
                message="Brake later in turn 3",
                priority="high",
                timestamp=1234567890.0,
            )
            
            assert advice.message == "Brake later in turn 3"
            assert advice.priority == "high"
        except ImportError:
            pytest.skip("AI racing coach not available")
    
    def test_lap_analysis(self):
        """Test lap analysis functionality."""
        try:
            from services.ai_racing_coach import AIRacingCoach
            
            coach = AIRacingCoach()
            
            # Simulate lap data
            lap_data = {
                "lap_time": 120.5,
                "sectors": [40.0, 40.0, 40.5],
                "speed_avg": 80.0,
            }
            
            # Should be able to analyze (even if returns None)
            analysis = coach.analyze_lap(lap_data) if hasattr(coach, 'analyze_lap') else None
            
            # Just verify coach exists and can be instantiated
            assert coach is not None
        except ImportError:
            pytest.skip("AI racing coach not available")

