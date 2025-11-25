from __future__ import annotations

import glob
import os
import socket
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Sequence


def _run_command(args: Sequence[str]) -> str:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return result.stdout.strip()
    except Exception:
        return ""


@dataclass
class ConnectivityStatus:
    wifi_connected: bool = False
    wifi_ssid: Optional[str] = None
    lte_connected: bool = False
    lte_interface: Optional[str] = None
    bluetooth_devices: List[str] = field(default_factory=list)
    serial_ports: List[str] = field(default_factory=list)
    usb_devices: List[str] = field(default_factory=list)
    gateway_reachable: bool = False
    last_updated: float = field(default_factory=time.time)

    def summary(self) -> str:
        wifi = f"Wi-Fi {'✅' if self.wifi_connected else '❌'}"
        if self.wifi_ssid:
            wifi += f" ({self.wifi_ssid})"
        lte = f"LTE {'✅' if self.lte_connected else '❌'}"
        if self.lte_interface:
            lte += f" ({self.lte_interface})"
        ble = f"BT {len(self.bluetooth_devices)}"
        serial = f"Serial {len(self.serial_ports)}"
        usb = f"USB {len(self.usb_devices)}"
        return " | ".join([wifi, lte, ble, serial, usb])

    def primary_link_ok(self, preference: str) -> bool:
        pref = (preference or "auto").lower()
        if pref == "lte":
            return self.lte_connected
        if pref in {"wifi", "wi-fi"}:
            return self.wifi_connected
        # Auto: either Wi-Fi or LTE is acceptable
        return self.wifi_connected or self.lte_connected


class ConnectivityManager:
    """Background worker that samples radio / port status for UI + automation."""

    def __init__(
        self,
        wifi_interface: str = "wlan0",
        lte_interface: str = "wwan0",
        poll_interval: float = 5.0,
    ) -> None:
        self.wifi_interface = wifi_interface
        self.lte_interface = lte_interface
        self.poll_interval = poll_interval
        self.status = ConnectivityStatus()
        self._callbacks: List[Callable[[ConnectivityStatus], None]] = []
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def configure(self, *, wifi_interface: Optional[str] = None, lte_interface: Optional[str] = None) -> None:
        if wifi_interface:
            self.wifi_interface = wifi_interface
        if lte_interface:
            self.lte_interface = lte_interface

    def register_callback(self, callback: Callable[[ConnectivityStatus], None]) -> None:
        self._callbacks.append(callback)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _run(self) -> None:
        while not self._stop.is_set():
            status = self._sample()
            self.status = status
            for callback in list(self._callbacks):
                try:
                    callback(status)
                except Exception:
                    continue
            time.sleep(self.poll_interval)

    def _sample(self) -> ConnectivityStatus:
        wifi_connected, wifi_ssid = self._check_wifi()
        lte_connected = self._interface_up(self.lte_interface)
        bluetooth_devices = self._list_bluetooth_connections()
        serial_ports = self._list_serial_ports()
        usb_devices = self._list_usb_devices()
        gateway_reachable = self._check_gateway()
        return ConnectivityStatus(
            wifi_connected=wifi_connected,
            wifi_ssid=wifi_ssid,
            lte_connected=lte_connected,
            lte_interface=self.lte_interface if lte_connected else None,
            bluetooth_devices=bluetooth_devices,
            serial_ports=serial_ports,
            usb_devices=usb_devices,
            gateway_reachable=gateway_reachable,
            last_updated=time.time(),
        )

    def _check_wifi(self) -> tuple[bool, Optional[str]]:
        ssid = _run_command(["iwgetid", "-r"]).strip()
        if ssid:
            return True, ssid
        # Fallback: check interface state
        return self._interface_up(self.wifi_interface), None

    def _interface_up(self, interface: Optional[str]) -> bool:
        if not interface:
            return False
        path = f"/sys/class/net/{interface}/operstate"
        try:
            return Path(path).read_text().strip() == "up"  # type: ignore[name-defined]
        except Exception:
            # fallback to ip link
            output = _run_command(["ip", "link", "show", interface])
            return "state UP" in output

    def _list_bluetooth_connections(self) -> List[str]:
        output = _run_command(["bluetoothctl", "devices", "Connected"])
        devices = []
        for line in output.splitlines():
            parts = line.strip().split(" ", 2)
            if len(parts) == 3:
                devices.append(parts[2])
        return devices

    def _list_serial_ports(self) -> List[str]:
        ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
        # Include Raspberry Pi UART if enabled
        if os.path.exists("/dev/serial0"):
            ports.append("/dev/serial0")
        return sorted(set(ports))

    def _list_usb_devices(self) -> List[str]:
        output = _run_command(["lsusb"])
        if not output:
            return []
        devices = []
        for line in output.splitlines():
            line = line.strip()
            if line:
                devices.append(line)
        return devices

    def _check_gateway(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.0).close()
            return True
        except OSError:
            return False


__all__ = ["ConnectivityManager", "ConnectivityStatus"]

