"""
reTerminal DM Optimizations

Platform-specific optimizations for Seeed reTerminal DM hardware.
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Optional

LOGGER = logging.getLogger(__name__)


class ReTerminalOptimizer:
    """Optimizations specific to reTerminal DM."""

    @staticmethod
    def optimize_display() -> bool:
        """Optimize display settings for reTerminal DM."""
        try:
            # Set display brightness (if supported)
            # Adjust for automotive visibility
            brightness = os.getenv("RETERMINAL_BRIGHTNESS", "80")
            try:
                subprocess.run(
                    ["sudo", "tee", "/sys/class/backlight/*/brightness"],
                    input=f"{brightness}\n",
                    text=True,
                    check=False,
                    timeout=2,
                )
            except Exception:
                pass  # May not have write access or file doesn't exist

            # Disable screen blanking for automotive use
            try:
                subprocess.run(
                    ["xset", "s", "off"],
                    check=False,
                    timeout=2,
                )
                subprocess.run(
                    ["xset", "-dpms"],
                    check=False,
                    timeout=2,
                )
            except Exception:
                pass  # X11 may not be available

            LOGGER.info("Display optimizations applied")
            return True
        except Exception as e:
            LOGGER.warning("Failed to optimize display: %s", e)
            return False

    @staticmethod
    def optimize_cpu_governor() -> bool:
        """Set CPU governor to performance mode for low latency."""
        try:
            # Try to set performance governor
            governors = ["/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"]
            for gov_path in governors:
                if os.path.exists(gov_path):
                    try:
                        with open(gov_path, "w") as f:
                            f.write("performance\n")
                        LOGGER.info("CPU governor set to performance mode")
                        return True
                    except PermissionError:
                        LOGGER.warning("Permission denied setting CPU governor (requires sudo)")
                        return False
        except Exception as e:
            LOGGER.warning("Failed to optimize CPU governor: %s", e)
            return False

    @staticmethod
    def optimize_network() -> bool:
        """Optimize network settings for low latency."""
        try:
            # Increase network buffer sizes for better throughput
            commands = [
                "sysctl -w net.core.rmem_max=16777216",
                "sysctl -w net.core.wmem_max=16777216",
                "sysctl -w net.ipv4.tcp_rmem='4096 87380 16777216'",
                "sysctl -w net.ipv4.tcp_wmem='4096 65536 16777216'",
            ]

            for cmd in commands:
                try:
                    subprocess.run(
                        cmd.split(),
                        check=False,
                        timeout=2,
                        capture_output=True,
                    )
                except Exception:
                    pass

            LOGGER.info("Network optimizations applied")
            return True
        except Exception as e:
            LOGGER.warning("Failed to optimize network: %s", e)
            return False

    @staticmethod
    def setup_can_interfaces() -> bool:
        """Ensure CAN interfaces are properly configured."""
        try:
            # Check if can0 exists
            result = subprocess.run(
                ["ip", "link", "show", "can0"],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode != 0:
                LOGGER.warning("can0 interface not found. Run setup_can_reterminal.py first.")
                return False

            # Check if can0 is up
            if "UP" not in result.stdout:
                LOGGER.info("Bringing up can0...")
                subprocess.run(
                    ["sudo", "ip", "link", "set", "can0", "up", "type", "can", "bitrate", "500000"],
                    check=False,
                    timeout=2,
                )

            # Check can1 if available
            result = subprocess.run(
                ["ip", "link", "show", "can1"],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode == 0 and "UP" not in result.stdout:
                LOGGER.info("Bringing up can1...")
                subprocess.run(
                    ["sudo", "ip", "link", "set", "can1", "up", "type", "can", "bitrate", "500000"],
                    check=False,
                    timeout=2,
                )

            LOGGER.info("CAN interfaces configured")
            return True
        except Exception as e:
            LOGGER.warning("Failed to setup CAN interfaces: %s", e)
            return False

    @staticmethod
    def optimize_memory() -> bool:
        """Optimize memory settings for embedded use."""
        try:
            # Reduce swappiness for embedded systems
            try:
                with open("/proc/sys/vm/swappiness", "w") as f:
                    f.write("10\n")  # Lower swappiness
            except (PermissionError, FileNotFoundError):
                pass

            LOGGER.info("Memory optimizations applied")
            return True
        except Exception as e:
            LOGGER.warning("Failed to optimize memory: %s", e)
            return False

    @staticmethod
    def apply_all_optimizations() -> dict[str, bool]:
        """Apply all available optimizations."""
        results = {
            "display": ReTerminalOptimizer.optimize_display(),
            "cpu": ReTerminalOptimizer.optimize_cpu_governor(),
            "network": ReTerminalOptimizer.optimize_network(),
            "can": ReTerminalOptimizer.setup_can_interfaces(),
            "memory": ReTerminalOptimizer.optimize_memory(),
        }
        return results

    @staticmethod
    def check_platform() -> bool:
        """Check if running on reTerminal DM."""
        try:
            if os.path.exists("/proc/device-tree/model"):
                with open("/proc/device-tree/model") as f:
                    model = f.read()
                    if "reTerminal" in model or "reTerminal DM" in model:
                        return True
        except Exception:
            pass
        return False


def optimize_for_reterminal() -> dict[str, bool]:
    """
    Apply reTerminal DM optimizations if platform is detected.

    Returns:
        Dictionary of optimization results
    """
    if not ReTerminalOptimizer.check_platform():
        LOGGER.info("Not running on reTerminal DM, skipping optimizations")
        return {}

    LOGGER.info("Detected reTerminal DM, applying optimizations...")
    return ReTerminalOptimizer.apply_all_optimizations()


__all__ = ["ReTerminalOptimizer", "optimize_for_reterminal"]

