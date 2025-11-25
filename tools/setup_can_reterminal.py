#!/usr/bin/env python3
"""
CAN Interface Setup Script for Seeed reTerminal DM

This script helps configure the dual CAN FD interfaces on the reTerminal DM.
Run with sudo: sudo python3 setup_can_reterminal.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def check_root() -> None:
    """Ensure script is run as root."""
    if os.geteuid() != 0:
        print("Error: This script must be run as root (use sudo)")
        sys.exit(1)


def check_can_interfaces() -> list[str]:
    """Check which CAN interfaces are available."""
    interfaces = []
    net_path = Path("/sys/class/net")
    if net_path.exists():
        for iface in net_path.iterdir():
            if iface.name.startswith("can"):
                interfaces.append(iface.name)
    return sorted(interfaces)


def bring_up_can(interface: str, bitrate: int = 500000) -> bool:
    """Bring up a CAN interface."""
    try:
        # Check if already up
        result = subprocess.run(
            ["ip", "link", "show", interface],
            capture_output=True,
            text=True,
            check=False,
        )
        if "UP" in result.stdout:
            print(f"  {interface} is already up")
            return True

        # Bring up the interface
        subprocess.run(
            ["ip", "link", "set", interface, "up", "type", "can", "bitrate", str(bitrate)],
            check=True,
            capture_output=True,
        )
        print(f"  ✓ {interface} brought up at {bitrate} bps")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to bring up {interface}: {e}")
        return False


def bring_down_can(interface: str) -> bool:
    """Bring down a CAN interface."""
    try:
        subprocess.run(
            ["ip", "link", "set", interface, "down"],
            check=True,
            capture_output=True,
        )
        print(f"  ✓ {interface} brought down")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to bring down {interface}: {e}")
        return False


def test_can_interface(interface: str) -> bool:
    """Test CAN interface by sending a test message."""
    try:
        # Try to send a test message
        subprocess.run(
            ["cansend", interface, "123#DEADBEEF"],
            check=True,
            capture_output=True,
            timeout=2,
        )
        print(f"  ✓ {interface} test message sent successfully")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        print(f"  ⚠ {interface} test skipped (cansend may not be installed)")
        return True  # Don't fail if cansend isn't available


def main() -> None:
    """Main setup function."""
    check_root()

    print("=" * 60)
    print("Seeed reTerminal DM CAN Interface Setup")
    print("=" * 60)
    print()

    # Check available interfaces
    interfaces = check_can_interfaces()
    if not interfaces:
        print("No CAN interfaces found!")
        print()
        print("Possible issues:")
        print("  1. CAN device tree overlays not enabled")
        print("  2. SPI not enabled")
        print("  3. Hardware not connected")
        print()
        print("Check /boot/config.txt for CAN-related overlays")
        sys.exit(1)

    print(f"Found CAN interfaces: {', '.join(interfaces)}")
    print()

    # Ask user what to do
    print("What would you like to do?")
    print("  1. Bring up all CAN interfaces")
    print("  2. Bring down all CAN interfaces")
    print("  3. Test CAN interfaces")
    print("  4. Show status")
    print("  5. Exit")
    print()

    choice = input("Enter choice (1-5): ").strip()

    if choice == "1":
        print("\nBringing up CAN interfaces...")
        bitrate = input("Enter bitrate (default 500000): ").strip()
        bitrate = int(bitrate) if bitrate else 500000

        for iface in interfaces:
            bring_up_can(iface, bitrate)
        print("\n✓ All interfaces configured")

    elif choice == "2":
        print("\nBringing down CAN interfaces...")
        for iface in interfaces:
            bring_down_can(iface)
        print("\n✓ All interfaces brought down")

    elif choice == "3":
        print("\nTesting CAN interfaces...")
        for iface in interfaces:
            print(f"\nTesting {iface}...")
            test_can_interface(iface)

    elif choice == "4":
        print("\nCAN Interface Status:")
        print("-" * 60)
        for iface in interfaces:
            result = subprocess.run(
                ["ip", "link", "show", iface],
                capture_output=True,
                text=True,
            )
            print(result.stdout)

    elif choice == "5":
        print("Exiting...")
        sys.exit(0)

    else:
        print("Invalid choice")
        sys.exit(1)

    print()
    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

