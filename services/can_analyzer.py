"""
CAN Bus Analyzer

Provides deep analysis of CAN bus traffic including:
- Message pattern analysis
- Anomaly detection
- Bus load analysis
- Timing analysis
- Protocol compliance checking
"""

from __future__ import annotations

import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from interfaces.can_interface import CANMessage

LOGGER = logging.getLogger(__name__)


@dataclass
class CANAnalysis:
    """CAN bus analysis results."""

    bus_load_percent: float
    average_message_rate: float
    peak_message_rate: float
    most_active_ids: List[tuple[int, int]]  # (can_id, count)
    timing_analysis: Dict[int, Dict[str, float]]  # can_id -> {min, max, avg, std_dev}
    anomalies: List[str]
    protocol_violations: List[str]


class CANAnalyzer:
    """Analyzes CAN bus traffic for patterns and anomalies."""

    def __init__(self, window_size: int = 1000, analysis_interval: float = 5.0) -> None:
        """
        Initialize CAN analyzer.

        Args:
            window_size: Number of messages to keep in analysis window
            analysis_interval: Interval for periodic analysis (seconds)
        """
        self.window_size = window_size
        self.analysis_interval = analysis_interval

        # Message history
        self.message_history: deque = deque(maxlen=window_size)
        self.id_timestamps: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))

        # Statistics
        self.message_counts: Dict[int, int] = defaultdict(int)
        self.timing_stats: Dict[int, List[float]] = defaultdict(list)

        # Analysis state
        self.last_analysis_time = time.time()
        self.last_message_times: Dict[int, float] = {}

    def add_message(self, message: CANMessage) -> None:
        """
        Add a message for analysis.

        Args:
            message: CAN message to analyze
        """
        self.message_history.append(message)
        can_id = message.arbitration_id

        # Update message count
        self.message_counts[can_id] += 1

        # Track timing
        if can_id in self.last_message_times:
            interval = message.timestamp - self.last_message_times[can_id]
            self.timing_stats[can_id].append(interval)
            if len(self.timing_stats[can_id]) > 100:
                self.timing_stats[can_id].pop(0)

        self.last_message_times[can_id] = message.timestamp
        self.id_timestamps[can_id].append(message.timestamp)

    def analyze(self) -> CANAnalysis:
        """
        Perform comprehensive CAN bus analysis.

        Returns:
            Analysis results
        """
        now = time.time()
        window_start = now - self.analysis_interval

        # Filter messages in analysis window
        window_messages = [msg for msg in self.message_history if msg.timestamp >= window_start]

        if not window_messages:
            return CANAnalysis(
                bus_load_percent=0.0,
                average_message_rate=0.0,
                peak_message_rate=0.0,
                most_active_ids=[],
                timing_analysis={},
                anomalies=[],
                protocol_violations=[],
            )

        # Calculate message rates
        total_messages = len(window_messages)
        time_span = window_messages[-1].timestamp - window_messages[0].timestamp if len(window_messages) > 1 else 1.0
        average_rate = total_messages / time_span if time_span > 0 else 0.0

        # Calculate peak rate (messages in 1 second windows)
        peak_rate = self._calculate_peak_rate(window_messages)

        # Calculate bus load (assuming 8 bytes average, 500kbps)
        # CAN frame overhead + data
        bits_per_frame = 111  # Standard CAN frame overhead
        total_bits = sum(bits_per_frame + (len(msg.data) * 8) for msg in window_messages)
        bus_load = (total_bits / time_span) / 500000.0 * 100 if time_span > 0 else 0.0

        # Most active IDs
        id_counts = defaultdict(int)
        for msg in window_messages:
            id_counts[msg.arbitration_id] += 1
        most_active = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Timing analysis
        timing_analysis = {}
        for can_id, intervals in self.timing_stats.items():
            if len(intervals) >= 3:
                timing_analysis[can_id] = {
                    "min": min(intervals),
                    "max": max(intervals),
                    "avg": statistics.mean(intervals),
                    "std_dev": statistics.stdev(intervals) if len(intervals) > 1 else 0.0,
                }

        # Detect anomalies
        anomalies = self._detect_anomalies(window_messages, timing_analysis)

        # Protocol violations
        violations = self._check_protocol_compliance(window_messages)

        return CANAnalysis(
            bus_load_percent=min(100.0, bus_load),
            average_message_rate=average_rate,
            peak_message_rate=peak_rate,
            most_active_ids=most_active,
            timing_analysis=timing_analysis,
            anomalies=anomalies,
            protocol_violations=violations,
        )

    def _calculate_peak_rate(self, messages: List[CANMessage]) -> float:
        """Calculate peak message rate in 1-second windows."""
        if not messages:
            return 0.0

        window_size = 1.0  # 1 second
        peak = 0.0
        start_idx = 0

        for i, msg in enumerate(messages):
            window_start = msg.timestamp - window_size
            # Move start_idx forward to exclude messages outside window
            while start_idx < i and messages[start_idx].timestamp < window_start:
                start_idx += 1
            window_count = i - start_idx + 1
            peak = max(peak, window_count)

        return peak

    def _detect_anomalies(self, messages: List[CANMessage], timing_analysis: Dict) -> List[str]:
        """Detect anomalies in CAN traffic."""
        anomalies = []

        # Check for missing periodic messages
        for can_id, timing in timing_analysis.items():
            avg_interval = timing.get("avg", 0)
            std_dev = timing.get("std_dev", 0)

            if avg_interval > 0 and std_dev > avg_interval * 2:
                anomalies.append(f"CAN ID 0x{can_id:X}: High timing variance (possible missing messages)")

        # Check for error frames
        error_count = sum(1 for msg in messages if msg.is_error_frame)
        if error_count > 0:
            anomalies.append(f"Detected {error_count} error frames")

        # Check for unusual message rates
        id_rates = defaultdict(int)
        time_span = messages[-1].timestamp - messages[0].timestamp if len(messages) > 1 else 1.0
        for msg in messages:
            id_rates[msg.arbitration_id] += 1

        for can_id, count in id_rates.items():
            rate = count / time_span if time_span > 0 else 0
            if rate > 1000:  # More than 1000 messages/second
                anomalies.append(f"CAN ID 0x{can_id:X}: Extremely high rate ({rate:.0f} msg/s)")

        return anomalies

    def _check_protocol_compliance(self, messages: List[CANMessage]) -> List[str]:
        """Check for CAN protocol violations."""
        violations = []

        for msg in messages:
            # Check DLC
            if msg.dlc > 8:
                violations.append(f"CAN ID 0x{msg.arbitration_id:X}: Invalid DLC {msg.dlc}")

            # Check data length matches DLC
            if len(msg.data) != msg.dlc:
                violations.append(
                    f"CAN ID 0x{msg.arbitration_id:X}: Data length ({len(msg.data)}) doesn't match DLC ({msg.dlc})"
                )

        return violations

    def get_id_statistics(self, can_id: int) -> Optional[Dict]:
        """Get statistics for a specific CAN ID."""
        if can_id not in self.message_counts:
            return None

        timing = self.timing_stats.get(can_id, [])
        timestamps = list(self.id_timestamps.get(can_id, []))

        stats = {
            "total_messages": self.message_counts[can_id],
            "message_count": len(timestamps),
        }

        if timing:
            stats.update(
                {
                    "min_interval": min(timing),
                    "max_interval": max(timing),
                    "avg_interval": statistics.mean(timing),
                    "std_dev_interval": statistics.stdev(timing) if len(timing) > 1 else 0.0,
                }
            )

        if len(timestamps) >= 2:
            time_span = timestamps[-1] - timestamps[0]
            stats["message_rate"] = len(timestamps) / time_span if time_span > 0 else 0.0

        return stats

    def reset(self) -> None:
        """Reset analyzer state."""
        self.message_history.clear()
        self.id_timestamps.clear()
        self.message_counts.clear()
        self.timing_stats.clear()
        self.last_message_times.clear()


__all__ = ["CANAnalyzer", "CANAnalysis"]

