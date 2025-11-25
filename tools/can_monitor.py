"""
CAN Bus Monitor Tool

Real-time CAN bus monitoring and analysis tool with filtering and statistics.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from collections import Counter

from interfaces.can_interface import CAN_ID_DATABASE, OptimizedCANInterface


class CANMonitor:
    """Interactive CAN bus monitor."""

    def __init__(self, channel: str = "can0", bitrate: int = 500000, filter_ids: set[int] | None = None) -> None:
        """Initialize CAN monitor."""
        self.interface = OptimizedCANInterface(
            channel=channel,
            bitrate=bitrate,
            filter_ids=filter_ids,
            message_callback=self._on_message,
        )
        self.running = True
        self.message_count = 0
        self.start_time = time.time()

        # Statistics
        self.id_counter = Counter()
        self.last_stats_time = time.time()

    def _on_message(self, msg) -> None:
        """Handle received CAN message."""
        self.message_count += 1
        self.id_counter[msg.arbitration_id] += 1

        # Get ID info
        id_info = self.interface.get_id_info(msg.arbitration_id)
        name = id_info["name"] if id_info else f"Unknown_0x{msg.arbitration_id:X}"

        # Print message
        data_hex = " ".join(f"{b:02X}" for b in msg.data[:8])
        print(f"[{msg.timestamp:.3f}] {msg.channel} 0x{msg.arbitration_id:03X} [{name}] {data_hex}")

    def start(self) -> None:
        """Start monitoring."""
        if not self.interface.connect():
            print("Failed to connect to CAN bus")
            return

        if not self.interface.start_monitoring():
            print("Failed to start monitoring")
            return

        print(f"Monitoring CAN bus: {self.interface.channel} @ {self.interface.bitrate} bps")
        print("Press Ctrl+C to stop\n")

        try:
            while self.running:
                time.sleep(1)
                self._print_statistics()
        except KeyboardInterrupt:
            print("\nStopping monitor...")
        finally:
            self.interface.stop_monitoring()
            self.interface.disconnect()

    def _print_statistics(self) -> None:
        """Print statistics."""
        now = time.time()
        elapsed = now - self.start_time
        mps = self.message_count / elapsed if elapsed > 0 else 0

        stats = self.interface.get_statistics()
        print(
            f"\n--- Statistics ---\n"
            f"Total Messages: {self.message_count}\n"
            f"Messages/sec: {mps:.1f}\n"
            f"Unique IDs: {len(stats.unique_ids)}\n"
            f"Error Frames: {stats.error_frames}\n"
        )

        # Top 10 most frequent IDs
        if self.id_counter:
            print("Top 10 CAN IDs:")
            for can_id, count in self.id_counter.most_common(10):
                id_info = self.interface.get_id_info(can_id)
                name = id_info["name"] if id_info else f"Unknown_0x{can_id:X}"
                percentage = (count / self.message_count) * 100
                print(f"  0x{can_id:03X} [{name}]: {count} ({percentage:.1f}%)")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CAN Bus Monitor")
    parser.add_argument("--channel", default="can0", help="CAN channel (default: can0)")
    parser.add_argument("--bitrate", type=int, default=500000, help="CAN bitrate (default: 500000)")
    parser.add_argument("--filter", nargs="+", type=lambda x: int(x, 0), help="Filter CAN IDs (hex format: 0x180)")
    parser.add_argument("--list-ids", action="store_true", help="List known CAN IDs and exit")

    args = parser.parse_args()

    if args.list_ids:
        print("Known CAN IDs by Vendor:\n")
        for vendor, ids in CAN_ID_DATABASE.items():
            print(f"{vendor.upper()}:")
            for can_id, info in ids.items():
                print(f"  0x{can_id:03X} - {info['name']}: {info['description']}")
            print()
        return

    filter_ids = set(args.filter) if args.filter else None

    monitor = CANMonitor(channel=args.channel, bitrate=args.bitrate, filter_ids=filter_ids)
    monitor.start()


if __name__ == "__main__":
    main()

