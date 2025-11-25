"""
AI Module - Intelligent Analysis and Prediction

This module contains all AI/ML algorithms for:
- Predictive fault detection
- Tuning recommendations
- Conversational AI
- Intelligent analysis
"""

from .conversational_agent import AgentContext, ConversationalAgent
from .fault_analyzer import FaultAnalyzer
from .intelligent_advisor import IntelligentAdvisor
from .predictive_fault_detector import PredictiveFaultDetector
from .tuning_advisor import TuningAdvisor

# Optimized versions (if available)
try:
    from .optimized_fault_detector import FeatureEngineer, LSTMAutoencoder, OptimizedFaultDetector
    from .adaptive_tuning_advisor import AdaptiveTuningAdvisor, TuningRecommendation
    from .model_optimizer import InferenceCache, ModelOptimizer
except ImportError:
    OptimizedFaultDetector = None  # type: ignore
    AdaptiveTuningAdvisor = None  # type: ignore
    ModelOptimizer = None  # type: ignore
    InferenceCache = None  # type: ignore
    FeatureEngineer = None  # type: ignore
    LSTMAutoencoder = None  # type: ignore
    TuningRecommendation = None  # type: ignore

__all__ = [
    "AgentContext",
    "ConversationalAgent",
    "FaultAnalyzer",
    "IntelligentAdvisor",
    "PredictiveFaultDetector",
    "TuningAdvisor",
    # Optimized versions
    "OptimizedFaultDetector",
    "AdaptiveTuningAdvisor",
    "ModelOptimizer",
    "InferenceCache",
    "FeatureEngineer",
    "LSTMAutoencoder",
    "TuningRecommendation",
]
