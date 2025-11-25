"""
Intelligent Auto-Detection Engine

Advanced algorithms for enhancing auto-detection across all modules:
- Machine learning-based pattern recognition
- Multi-signal correlation analysis
- Confidence scoring with uncertainty quantification
- Adaptive learning from historical detections
- Fuzzy matching for partial signatures
- Behavioral analysis
- Context-aware detection
- Ensemble detection methods
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class DetectionMethod(Enum):
    """Detection methods."""

    SIGNATURE = "signature"  # Exact signature match
    PATTERN = "pattern"  # Pattern matching
    BEHAVIORAL = "behavioral"  # Behavioral analysis
    ML = "ml"  # Machine learning
    ENSEMBLE = "ensemble"  # Multiple methods combined
    FUZZY = "fuzzy"  # Fuzzy matching


class DetectionConfidence(Enum):
    """Confidence levels."""

    VERY_HIGH = 0.95  # 95-100%
    HIGH = 0.80  # 80-95%
    MEDIUM = 0.60  # 60-80%
    LOW = 0.40  # 40-60%
    VERY_LOW = 0.20  # 20-40%


@dataclass
class DetectionSignature:
    """Device/component signature for matching."""

    name: str
    signature_type: str  # "CAN_ID", "VID_PID", "Serial", "Behavioral", etc.
    primary_signals: Dict[str, Any]  # Primary identifying signals
    secondary_signals: Dict[str, Any] = field(default_factory=dict)  # Supporting signals
    behavioral_patterns: List[Dict[str, Any]] = field(default_factory=list)  # Behavioral patterns
    frequency_patterns: Dict[str, float] = field(default_factory=dict)  # Message frequencies
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence_weight: float = 1.0  # Weight for this signature


@dataclass
class DetectionResult:
    """Detection result with confidence scoring."""

    detected_item: str
    detection_method: DetectionMethod
    confidence: float  # 0.0 - 1.0
    confidence_level: DetectionConfidence
    signals_matched: List[str] = field(default_factory=list)
    signals_missing: List[str] = field(default_factory=list)
    correlation_score: float = 0.0  # Multi-signal correlation
    behavioral_score: float = 0.0  # Behavioral pattern match
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    alternative_matches: List[Tuple[str, float]] = field(default_factory=list)  # Other possibilities


@dataclass
class DetectionContext:
    """Context for detection."""

    hardware_platform: Optional[str] = None
    detected_ecus: List[str] = field(default_factory=list)
    detected_sensors: List[str] = field(default_factory=list)
    detected_adapters: List[str] = field(default_factory=list)
    vehicle_profile: Optional[Dict[str, Any]] = None
    historical_detections: List[DetectionResult] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)


class PatternMatcher:
    """Advanced pattern matching with fuzzy logic."""

    def __init__(self, similarity_threshold: float = 0.7):
        """Initialize pattern matcher."""
        self.similarity_threshold = similarity_threshold

    def fuzzy_match(
        self, pattern: Dict[str, Any], target: Dict[str, Any], weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate fuzzy match score between pattern and target.

        Args:
            pattern: Pattern to match
            target: Target to match against
            weights: Optional weights for each field

        Returns:
            Similarity score 0.0-1.0
        """
        if not pattern or not target:
            return 0.0

        if weights is None:
            weights = {key: 1.0 for key in pattern.keys()}

        total_score = 0.0
        total_weight = 0.0

        for key, pattern_value in pattern.items():
            if key not in target:
                continue

            target_value = target[key]
            weight = weights.get(key, 1.0)

            # Calculate similarity based on type
            if isinstance(pattern_value, (int, float)) and isinstance(target_value, (int, float)):
                # Numeric similarity
                similarity = self._numeric_similarity(pattern_value, target_value)
            elif isinstance(pattern_value, str) and isinstance(target_value, str):
                # String similarity
                similarity = self._string_similarity(pattern_value, target_value)
            elif isinstance(pattern_value, (list, set)) and isinstance(target_value, (list, set)):
                # Set similarity
                similarity = self._set_similarity(pattern_value, target_value)
            elif isinstance(pattern_value, dict) and isinstance(target_value, dict):
                # Recursive dict similarity
                similarity = self.fuzzy_match(pattern_value, target_value, weights.get(key, {}))
            else:
                # Type mismatch
                similarity = 0.0

            total_score += similarity * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _numeric_similarity(self, a: float, b: float, tolerance: float = 0.1) -> float:
        """Calculate numeric similarity."""
        if a == 0 and b == 0:
            return 1.0
        if a == 0 or b == 0:
            return 0.0
        diff = abs(a - b) / max(abs(a), abs(b))
        return max(0.0, 1.0 - diff / tolerance)

    def _string_similarity(self, a: str, b: str) -> float:
        """Calculate string similarity using Levenshtein-like approach."""
        a_lower = a.lower()
        b_lower = b.lower()

        # Exact match
        if a_lower == b_lower:
            return 1.0

        # Substring match
        if a_lower in b_lower or b_lower in a_lower:
            return 0.8

        # Character overlap
        a_chars = set(a_lower)
        b_chars = set(b_lower)
        if not a_chars or not b_chars:
            return 0.0

        intersection = len(a_chars & b_chars)
        union = len(a_chars | b_chars)
        return intersection / union if union > 0 else 0.0

    def _set_similarity(self, a: set | list, b: set | list) -> float:
        """Calculate set similarity (Jaccard)."""
        a_set = set(a) if not isinstance(a, set) else a
        b_set = set(b) if not isinstance(b, set) else b

        if not a_set and not b_set:
            return 1.0
        if not a_set or not b_set:
            return 0.0

        intersection = len(a_set & b_set)
        union = len(a_set | b_set)
        return intersection / union if union > 0 else 0.0


class BehavioralAnalyzer:
    """Analyzes behavioral patterns for detection."""

    def __init__(self, window_size: int = 100):
        """Initialize behavioral analyzer."""
        self.window_size = window_size
        self.pattern_history: deque = deque(maxlen=window_size)

    def analyze_behavior(self, signals: List[Dict[str, Any]], signature: DetectionSignature) -> float:
        """
        Analyze behavioral patterns.

        Args:
            signals: Signal history
            signature: Signature to match against

        Returns:
            Behavioral match score 0.0-1.0
        """
        if not signature.behavioral_patterns:
            return 0.5  # Neutral if no behavioral patterns

        if not signals:
            return 0.0

        scores = []
        for pattern in signature.behavioral_patterns:
            score = self._match_behavioral_pattern(signals, pattern)
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def _match_behavioral_pattern(self, signals: List[Dict[str, Any]], pattern: Dict[str, Any]) -> float:
        """Match a single behavioral pattern."""
        # Extract pattern requirements
        required_signals = pattern.get("required_signals", [])
        timing_pattern = pattern.get("timing", {})
        value_pattern = pattern.get("values", {})

        # Check required signals
        signal_names = [s.get("name", "") for s in signals]
        missing_signals = set(required_signals) - set(signal_names)
        if missing_signals:
            return 0.0

        # Check timing patterns
        timing_score = 1.0
        if timing_pattern:
            timing_score = self._check_timing_pattern(signals, timing_pattern)

        # Check value patterns
        value_score = 1.0
        if value_pattern:
            value_score = self._check_value_pattern(signals, value_pattern)

        return (timing_score + value_score) / 2.0

    def _check_timing_pattern(self, signals: List[Dict[str, Any]], pattern: Dict[str, Any]) -> float:
        """Check timing pattern match."""
        # Simplified timing check
        if "frequency" in pattern:
            expected_freq = pattern["frequency"]
            # Calculate actual frequency from signals
            if len(signals) >= 2:
                time_span = signals[-1].get("timestamp", 0) - signals[0].get("timestamp", 0)
                if time_span > 0:
                    actual_freq = len(signals) / time_span
                    diff = abs(actual_freq - expected_freq) / expected_freq
                    return max(0.0, 1.0 - diff)
        return 0.5

    def _check_value_pattern(self, signals: List[Dict[str, Any]], pattern: Dict[str, Any]) -> float:
        """Check value pattern match."""
        # Simplified value pattern check
        if "range" in pattern:
            range_min, range_max = pattern["range"]
            values = [s.get("value", 0) for s in signals if "value" in s]
            if values:
                avg_value = sum(values) / len(values)
                if range_min <= avg_value <= range_max:
                    return 1.0
                return 0.0
        return 0.5


class CorrelationAnalyzer:
    """Analyzes multi-signal correlations."""

    def __init__(self):
        """Initialize correlation analyzer."""
        self.correlation_cache: Dict[Tuple[str, str], float] = {}

    def calculate_correlation(
        self, signals: Dict[str, List[float]], signature: DetectionSignature
    ) -> float:
        """
        Calculate multi-signal correlation score.

        Args:
            signals: Signal data (name -> values)
            signature: Signature to match

        Returns:
            Correlation score 0.0-1.0
        """
        if not signals or not signature.primary_signals:
            return 0.0

        if not NUMPY_AVAILABLE:
            # Fallback to simple matching
            return self._simple_correlation(signals, signature)

        # Calculate correlations between signals
        correlations = []
        signal_names = list(signals.keys())
        primary_names = list(signature.primary_signals.keys())

        for i, name1 in enumerate(signal_names):
            for name2 in signal_names[i + 1 :]:
                if name1 in primary_names or name2 in primary_names:
                    corr = self._calculate_signal_correlation(signals[name1], signals[name2])
                    correlations.append(abs(corr))

        # Expected correlations from signature
        expected_correlations = signature.metadata.get("expected_correlations", {})
        if expected_correlations:
            # Compare with expected
            return self._compare_correlations(correlations, expected_correlations)

        # Return average correlation
        return sum(correlations) / len(correlations) if correlations else 0.0

    def _calculate_signal_correlation(self, signal1: List[float], signal2: List[float]) -> float:
        """Calculate correlation between two signals."""
        if not NUMPY_AVAILABLE or len(signal1) != len(signal2) or len(signal1) < 2:
            return 0.0

        try:
            arr1 = np.array(signal1)
            arr2 = np.array(signal2)
            corr_matrix = np.corrcoef(arr1, arr2)
            return float(corr_matrix[0, 1])
        except Exception:
            return 0.0

    def _simple_correlation(self, signals: Dict[str, List[float]], signature: DetectionSignature) -> float:
        """Simple correlation without numpy."""
        if not signals:
            return 0.0

        # Check if primary signals are present
        primary_present = sum(1 for name in signature.primary_signals.keys() if name in signals)
        primary_ratio = primary_present / len(signature.primary_signals) if signature.primary_signals else 0.0

        return primary_ratio

    def _compare_correlations(self, actual: List[float], expected: Dict[str, float]) -> float:
        """Compare actual correlations with expected."""
        # Simplified comparison
        if not actual:
            return 0.0

        avg_actual = sum(actual) / len(actual)
        avg_expected = sum(expected.values()) / len(expected) if expected else 0.5

        diff = abs(avg_actual - avg_expected)
        return max(0.0, 1.0 - diff)


class IntelligentDetector:
    """Intelligent auto-detection engine."""

    def __init__(self, learning_enabled: bool = True, confidence_threshold: float = 0.6):
        """
        Initialize intelligent detector.

        Args:
            learning_enabled: Enable adaptive learning
            confidence_threshold: Minimum confidence for detection
        """
        self.learning_enabled = learning_enabled
        self.confidence_threshold = confidence_threshold

        # Signature database
        self.signatures: Dict[str, DetectionSignature] = {}
        self.signature_index: Dict[str, List[str]] = defaultdict(list)  # Type -> signature names

        # Pattern matcher
        self.pattern_matcher = PatternMatcher()

        # Behavioral analyzer
        self.behavioral_analyzer = BehavioralAnalyzer()

        # Correlation analyzer
        self.correlation_analyzer = CorrelationAnalyzer()

        # Learning data
        self.detection_history: deque = deque(maxlen=1000)
        self.successful_detections: Dict[str, int] = defaultdict(int)
        self.failed_detections: Dict[str, int] = defaultdict(int)

        # Thread safety
        self._lock = Lock()

        # Statistics
        self.stats = {
            "total_detections": 0,
            "successful_detections": 0,
            "failed_detections": 0,
            "average_confidence": 0.0,
        }

    def register_signature(self, signature: DetectionSignature) -> None:
        """Register a detection signature."""
        with self._lock:
            self.signatures[signature.name] = signature
            self.signature_index[signature.signature_type].append(signature.name)

    def detect(
        self,
        signals: Dict[str, Any],
        context: Optional[DetectionContext] = None,
        method: DetectionMethod = DetectionMethod.ENSEMBLE,
    ) -> List[DetectionResult]:
        """
        Detect items from signals.

        Args:
            signals: Detection signals
            context: Detection context
            method: Detection method to use

        Returns:
            List of detection results sorted by confidence
        """
        with self._lock:
            self.stats["total_detections"] += 1

            if method == DetectionMethod.ENSEMBLE:
                results = self._ensemble_detect(signals, context)
            elif method == DetectionMethod.SIGNATURE:
                results = self._signature_detect(signals, context)
            elif method == DetectionMethod.PATTERN:
                results = self._pattern_detect(signals, context)
            elif method == DetectionMethod.BEHAVIORAL:
                results = self._behavioral_detect(signals, context)
            elif method == DetectionMethod.FUZZY:
                results = self._fuzzy_detect(signals, context)
            else:
                results = []

            # Filter by confidence threshold
            results = [r for r in results if r.confidence >= self.confidence_threshold]

            # Sort by confidence
            results.sort(key=lambda x: x.confidence, reverse=True)

            # Update statistics
            if results:
                self.stats["successful_detections"] += 1
                self.stats["average_confidence"] = (
                    (self.stats["average_confidence"] * (self.stats["successful_detections"] - 1) + results[0].confidence)
                    / self.stats["successful_detections"]
                )
            else:
                self.stats["failed_detections"] += 1

            # Learn from detection
            if self.learning_enabled and results:
                self._learn_from_detection(signals, results[0])

            return results

    def _ensemble_detect(
        self, signals: Dict[str, Any], context: Optional[DetectionContext]
    ) -> List[DetectionResult]:
        """Ensemble detection using multiple methods."""
        all_results = []

        # Try all methods
        for method in [
            DetectionMethod.SIGNATURE,
            DetectionMethod.PATTERN,
            DetectionMethod.BEHAVIORAL,
            DetectionMethod.FUZZY,
        ]:
            try:
                if method == DetectionMethod.SIGNATURE:
                    results = self._signature_detect(signals, context)
                elif method == DetectionMethod.PATTERN:
                    results = self._pattern_detect(signals, context)
                elif method == DetectionMethod.BEHAVIORAL:
                    results = self._behavioral_detect(signals, context)
                else:
                    results = self._fuzzy_detect(signals, context)

                all_results.extend(results)
            except Exception as e:
                LOGGER.warning("Detection method %s failed: %s", method.value, e)

        # Combine results by item name
        combined: Dict[str, DetectionResult] = {}
        for result in all_results:
            if result.detected_item not in combined:
                combined[result.detected_item] = result
            else:
                # Combine confidences (weighted average)
                existing = combined[result.detected_item]
                combined_confidence = (existing.confidence * 0.6 + result.confidence * 0.4)
                existing.confidence = combined_confidence
                existing.signals_matched.extend(result.signals_matched)
                existing.alternative_matches.extend(result.alternative_matches)

        return list(combined.values())

    def _signature_detect(
        self, signals: Dict[str, Any], context: Optional[DetectionContext]
    ) -> List[DetectionResult]:
        """Signature-based detection."""
        results = []

        for name, signature in self.signatures.items():
            # Check primary signals
            primary_matched = []
            primary_missing = []

            for sig_name, sig_value in signature.primary_signals.items():
                if sig_name in signals:
                    if self._match_signal(signals[sig_name], sig_value):
                        primary_matched.append(sig_name)
                    else:
                        primary_missing.append(sig_name)
                else:
                    primary_missing.append(sig_name)

            # Calculate confidence
            if not primary_matched:
                continue

            match_ratio = len(primary_matched) / len(signature.primary_signals) if signature.primary_signals else 0.0
            confidence = match_ratio * signature.confidence_weight

            # Check secondary signals
            secondary_matched = sum(
                1 for sig_name in signature.secondary_signals.keys() if sig_name in signals
            )
            if signature.secondary_signals:
                secondary_boost = (secondary_matched / len(signature.secondary_signals)) * 0.2
                confidence = min(1.0, confidence + secondary_boost)

            # Calculate correlation
            signal_data = {name: [signals.get(name, 0)] for name in signature.primary_signals.keys()}
            correlation = self.correlation_analyzer.calculate_correlation(signal_data, signature)

            # Final confidence
            confidence = (confidence * 0.7 + correlation * 0.3)

            if confidence >= self.confidence_threshold:
                result = DetectionResult(
                    detected_item=name,
                    detection_method=DetectionMethod.SIGNATURE,
                    confidence=confidence,
                    confidence_level=self._get_confidence_level(confidence),
                    signals_matched=primary_matched,
                    signals_missing=primary_missing,
                    correlation_score=correlation,
                )
                results.append(result)

        return results

    def _pattern_detect(
        self, signals: Dict[str, Any], context: Optional[DetectionContext]
    ) -> List[DetectionResult]:
        """Pattern-based detection."""
        results = []

        for name, signature in self.signatures.items():
            # Use fuzzy matching
            similarity = self.pattern_matcher.fuzzy_match(signature.primary_signals, signals)

            if similarity >= self.pattern_matcher.similarity_threshold:
                result = DetectionResult(
                    detected_item=name,
                    detection_method=DetectionMethod.PATTERN,
                    confidence=similarity,
                    confidence_level=self._get_confidence_level(similarity),
                    signals_matched=list(signature.primary_signals.keys()),
                )
                results.append(result)

        return results

    def _behavioral_detect(
        self, signals: Dict[str, Any], context: Optional[DetectionContext]
    ) -> List[DetectionResult]:
        """Behavioral pattern detection."""
        results = []

        # Convert signals to list format for behavioral analysis
        signal_list = [{"name": k, "value": v, "timestamp": time.time()} for k, v in signals.items()]

        for name, signature in self.signatures.items():
            if not signature.behavioral_patterns:
                continue

            behavioral_score = self.behavioral_analyzer.analyze_behavior(signal_list, signature)

            if behavioral_score >= 0.5:
                result = DetectionResult(
                    detected_item=name,
                    detection_method=DetectionMethod.BEHAVIORAL,
                    confidence=behavioral_score,
                    confidence_level=self._get_confidence_level(behavioral_score),
                    behavioral_score=behavioral_score,
                )
                results.append(result)

        return results

    def _fuzzy_detect(
        self, signals: Dict[str, Any], context: Optional[DetectionContext]
    ) -> List[DetectionResult]:
        """Fuzzy matching detection."""
        results = []

        for name, signature in self.signatures.items():
            similarity = self.pattern_matcher.fuzzy_match(signature.primary_signals, signals)

            if similarity >= self.pattern_matcher.similarity_threshold * 0.8:  # Lower threshold for fuzzy
                result = DetectionResult(
                    detected_item=name,
                    detection_method=DetectionMethod.FUZZY,
                    confidence=similarity * 0.9,  # Slightly lower confidence for fuzzy
                    confidence_level=self._get_confidence_level(similarity * 0.9),
                    signals_matched=list(signature.primary_signals.keys()),
                )
                results.append(result)

        return results

    def _match_signal(self, actual: Any, expected: Any) -> bool:
        """Match a signal value."""
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            # Allow 5% tolerance for numeric values
            tolerance = abs(expected) * 0.05
            return abs(actual - expected) <= tolerance
        elif isinstance(expected, str) and isinstance(actual, str):
            return actual.lower() == expected.lower()
        elif isinstance(expected, (list, set)) and isinstance(actual, (list, set)):
            return set(expected) == set(actual)
        else:
            return actual == expected

    def _get_confidence_level(self, confidence: float) -> DetectionConfidence:
        """Get confidence level from score."""
        if confidence >= 0.95:
            return DetectionConfidence.VERY_HIGH
        elif confidence >= 0.80:
            return DetectionConfidence.HIGH
        elif confidence >= 0.60:
            return DetectionConfidence.MEDIUM
        elif confidence >= 0.40:
            return DetectionConfidence.LOW
        else:
            return DetectionConfidence.VERY_LOW

    def _learn_from_detection(self, signals: Dict[str, Any], result: DetectionResult) -> None:
        """Learn from successful detection."""
        if result.confidence < 0.8:
            return  # Only learn from high-confidence detections

        # Update signature weights based on success
        if result.detected_item in self.signatures:
            signature = self.signatures[result.detected_item]
            # Increase weight for successful detections
            signature.confidence_weight = min(2.0, signature.confidence_weight * 1.01)

        # Store in history
        self.detection_history.append((signals, result))
        self.successful_detections[result.detected_item] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        with self._lock:
            success_rate = (
                self.stats["successful_detections"] / self.stats["total_detections"]
                if self.stats["total_detections"] > 0
                else 0.0
            )
            return {
                **self.stats,
                "success_rate": success_rate,
                "registered_signatures": len(self.signatures),
                "signature_types": len(self.signature_index),
            }


__all__ = [
    "IntelligentDetector",
    "DetectionSignature",
    "DetectionResult",
    "DetectionContext",
    "DetectionMethod",
    "DetectionConfidence",
    "PatternMatcher",
    "BehavioralAnalyzer",
    "CorrelationAnalyzer",
]



