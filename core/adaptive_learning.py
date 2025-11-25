"""
Adaptive Learning System for Auto-Detection

Learns from detection history to improve accuracy:
- Pattern recognition from successful detections
- Signature refinement
- Confidence calibration
- False positive/negative learning
- Context-aware adaptation
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


@dataclass
class LearningExample:
    """Learning example from detection."""

    signals: Dict[str, Any]
    correct_item: str
    detected_item: str
    confidence: float
    timestamp: float = field(default_factory=time.time)
    context: Optional[Dict[str, Any]] = None
    verified: bool = False  # User verified correct


@dataclass
class LearnedPattern:
    """Learned pattern from examples."""

    pattern_id: str
    item_name: str
    signal_patterns: Dict[str, Any]
    frequency: int = 0
    success_rate: float = 0.0
    confidence_boost: float = 0.0
    context_hints: List[str] = field(default_factory=list)
    learned_at: float = field(default_factory=time.time)


class AdaptiveLearner:
    """Adaptive learning system for detection improvement."""

    def __init__(self, learning_data_path: Optional[Path] = None, min_examples: int = 5):
        """
        Initialize adaptive learner.

        Args:
            learning_data_path: Path to save/load learning data
            min_examples: Minimum examples before learning
        """
        self.learning_data_path = learning_data_path or Path("data/learning")
        self.learning_data_path.mkdir(parents=True, exist_ok=True)
        self.min_examples = min_examples

        # Learning data
        self.examples: deque[LearningExample] = deque(maxlen=1000)
        self.learned_patterns: Dict[str, LearnedPattern] = {}
        self.item_statistics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_detections": 0,
            "correct_detections": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "average_confidence": 0.0,
        })

        # Thread safety
        self._lock = Lock()

        # Load existing learning data
        self._load_learning_data()

    def record_detection(
        self,
        signals: Dict[str, Any],
        detected_item: str,
        confidence: float,
        correct_item: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        verified: bool = False,
    ) -> None:
        """
        Record a detection for learning.

        Args:
            signals: Detection signals
            detected_item: Detected item name
            confidence: Detection confidence
            correct_item: Correct item (if known)
            context: Detection context
            verified: Whether user verified the detection
        """
        with self._lock:
            example = LearningExample(
                signals=signals,
                correct_item=correct_item or detected_item,
                detected_item=detected_item,
                confidence=confidence,
                context=context,
                verified=verified,
            )
            self.examples.append(example)

            # Update statistics
            stats = self.item_statistics[detected_item]
            stats["total_detections"] += 1
            stats["average_confidence"] = (
                (stats["average_confidence"] * (stats["total_detections"] - 1) + confidence)
                / stats["total_detections"]
            )

            if correct_item and detected_item == correct_item:
                stats["correct_detections"] += 1
            elif correct_item and detected_item != correct_item:
                stats["false_positives"] += 1
                # Also record false negative for correct item
                correct_stats = self.item_statistics[correct_item]
                correct_stats["false_negatives"] += 1

            # Learn if enough examples
            if len(self.examples) >= self.min_examples:
                self._learn_patterns()

    def _learn_patterns(self) -> None:
        """Learn patterns from examples."""
        # Group examples by item
        examples_by_item: Dict[str, List[LearningExample]] = defaultdict(list)
        for example in self.examples:
            if example.verified or example.detected_item == example.correct_item:
                examples_by_item[example.correct_item].append(example)

        # Learn patterns for each item
        for item_name, item_examples in examples_by_item.items():
            if len(item_examples) < self.min_examples:
                continue

            # Extract common signal patterns
            common_signals = self._extract_common_signals(item_examples)

            # Calculate success rate
            success_rate = sum(1 for ex in item_examples if ex.detected_item == ex.correct_item) / len(item_examples)

            # Create or update learned pattern
            pattern_id = f"{item_name}_{int(time.time())}"
            if item_name in self.learned_patterns:
                pattern = self.learned_patterns[item_name]
                # Update existing pattern
                pattern.signal_patterns.update(common_signals)
                pattern.frequency += len(item_examples)
                pattern.success_rate = (
                    (pattern.success_rate * (pattern.frequency - len(item_examples)) + success_rate * len(item_examples))
                    / pattern.frequency
                )
            else:
                pattern = LearnedPattern(
                    pattern_id=pattern_id,
                    item_name=item_name,
                    signal_patterns=common_signals,
                    frequency=len(item_examples),
                    success_rate=success_rate,
                )
                self.learned_patterns[item_name] = pattern

            # Calculate confidence boost based on success rate
            if success_rate > 0.8:
                pattern.confidence_boost = min(0.2, (success_rate - 0.8) * 0.5)
            elif success_rate < 0.5:
                pattern.confidence_boost = -0.1  # Penalty for low success rate

            # Extract context hints
            context_hints = self._extract_context_hints(item_examples)
            pattern.context_hints = context_hints

            LOGGER.debug("Learned pattern for %s: success_rate=%.2f, boost=%.2f", item_name, success_rate, pattern.confidence_boost)

    def _extract_common_signals(self, examples: List[LearningExample]) -> Dict[str, Any]:
        """Extract common signal patterns from examples."""
        if not examples:
            return {}

        # Get all signal names
        all_signal_names = set()
        for example in examples:
            all_signal_names.update(example.signals.keys())

        common_signals = {}
        for signal_name in all_signal_names:
            values = [ex.signals.get(signal_name) for ex in examples if signal_name in ex.signals]
            if not values:
                continue

            # Calculate statistics
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if numeric_values:
                avg_value = sum(numeric_values) / len(numeric_values)
                min_value = min(numeric_values)
                max_value = max(numeric_values)
                common_signals[signal_name] = {
                    "average": avg_value,
                    "min": min_value,
                    "max": max_value,
                    "range": (min_value, max_value),
                }
            else:
                # String/categorical values
                value_counts = {}
                for v in values:
                    value_counts[v] = value_counts.get(v, 0) + 1
                most_common = max(value_counts.items(), key=lambda x: x[1])[0]
                common_signals[signal_name] = {
                    "most_common": most_common,
                    "frequency": value_counts[most_common] / len(values),
                }

        return common_signals

    def _extract_context_hints(self, examples: List[LearningExample]) -> List[str]:
        """Extract context hints from examples."""
        if not examples:
            return []

        context_keys = set()
        for example in examples:
            if example.context:
                context_keys.update(example.context.keys())

        hints = []
        for key in context_keys:
            values = [ex.context.get(key) for ex in examples if ex.context and key in ex.context]
            if values:
                # Most common value
                value_counts = {}
                for v in values:
                    value_counts[v] = value_counts.get(v, 0) + 1
                most_common = max(value_counts.items(), key=lambda x: x[1])[0]
                frequency = value_counts[most_common] / len(values)
                if frequency > 0.7:  # Strong hint
                    hints.append(f"{key}={most_common}")

        return hints

    def get_confidence_boost(self, item_name: str) -> float:
        """Get confidence boost for an item based on learned patterns."""
        with self._lock:
            if item_name in self.learned_patterns:
                return self.learned_patterns[item_name].confidence_boost
            return 0.0

    def get_learned_pattern(self, item_name: str) -> Optional[LearnedPattern]:
        """Get learned pattern for an item."""
        with self._lock:
            return self.learned_patterns.get(item_name)

    def get_statistics(self) -> Dict[str, Any]:
        """Get learning statistics."""
        with self._lock:
            total_examples = len(self.examples)
            verified_examples = sum(1 for ex in self.examples if ex.verified)
            learned_items = len(self.learned_patterns)

            return {
                "total_examples": total_examples,
                "verified_examples": verified_examples,
                "learned_patterns": learned_items,
                "item_statistics": dict(self.item_statistics),
                "learned_items": list(self.learned_patterns.keys()),
            }

    def _load_learning_data(self) -> None:
        """Load learning data from disk."""
        learning_file = self.learning_data_path / "learned_patterns.json"
        if not learning_file.exists():
            return

        try:
            with open(learning_file, "r") as f:
                data = json.load(f)

            for item_name, pattern_data in data.get("patterns", {}).items():
                pattern = LearnedPattern(
                    pattern_id=pattern_data.get("pattern_id", ""),
                    item_name=item_name,
                    signal_patterns=pattern_data.get("signal_patterns", {}),
                    frequency=pattern_data.get("frequency", 0),
                    success_rate=pattern_data.get("success_rate", 0.0),
                    confidence_boost=pattern_data.get("confidence_boost", 0.0),
                    context_hints=pattern_data.get("context_hints", []),
                    learned_at=pattern_data.get("learned_at", time.time()),
                )
                self.learned_patterns[item_name] = pattern

            LOGGER.info("Loaded %d learned patterns", len(self.learned_patterns))
        except Exception as e:
            LOGGER.warning("Failed to load learning data: %s", e)

    def save_learning_data(self) -> None:
        """Save learning data to disk."""
        learning_file = self.learning_data_path / "learned_patterns.json"
        try:
            with self._lock:
                data = {
                    "patterns": {
                        item_name: {
                            "pattern_id": pattern.pattern_id,
                            "signal_patterns": pattern.signal_patterns,
                            "frequency": pattern.frequency,
                            "success_rate": pattern.success_rate,
                            "confidence_boost": pattern.confidence_boost,
                            "context_hints": pattern.context_hints,
                            "learned_at": pattern.learned_at,
                        }
                        for item_name, pattern in self.learned_patterns.items()
                    }
                }

            with open(learning_file, "w") as f:
                json.dump(data, f, indent=2)

            LOGGER.info("Saved %d learned patterns", len(self.learned_patterns))
        except Exception as e:
            LOGGER.warning("Failed to save learning data: %s", e)

    def clear_learning_data(self) -> None:
        """Clear all learning data."""
        with self._lock:
            self.examples.clear()
            self.learned_patterns.clear()
            self.item_statistics.clear()

        # Delete learning file
        learning_file = self.learning_data_path / "learned_patterns.json"
        if learning_file.exists():
            learning_file.unlink()


__all__ = ["AdaptiveLearner", "LearningExample", "LearnedPattern"]



