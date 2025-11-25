"""
DBC Signal Mapper Module
Handles decoding of CAN messages using DBC files or static fallback mapping
"""

import os
import cantools


class DBCSignalMapper:
    """Maps CAN messages to decoded signals using DBC files or static mapping"""
    
    def __init__(self, dbc_path=None):
        self.db = None
        if dbc_path and os.path.exists(dbc_path):
            try:
                self.db = cantools.database.load_file(dbc_path)
                print(f"[DBC] Loaded DBC file: {dbc_path}")
            except Exception as e:
                print(f"[ERROR] Failed to load DBC file: {e}")
        else:
            print("[WARN] No DBC file found, using static fallback mapping.")
        
        self.static_map = {
            0x0CFF050A: {"name": "Engine_RPM", "scale": 0.125, "unit": "rpm"},
            0x0CF00400: {"name": "Vehicle_Speed", "scale": 0.01, "unit": "km/h"},
            0x18FEF600: {"name": "Throttle_Position", "scale": 0.4, "unit": "%"},
        }

    def decode(self, msg):
        """Decode a CAN message into signal values"""
        if self.db:
            try:
                message = self.db.get_message_by_frame_id(msg.arbitration_id)
                decoded_signals = message.decode(msg.data)
                results = []
                for name, value in decoded_signals.items():
                    signal = message.get_signal_by_name(name)
                    results.append({
                        "metric": name,
                        "value": round(value, 2),
                        "unit": signal.unit or ""
                    })
                return results
            except Exception:
                return None
        elif msg.arbitration_id in self.static_map:
            mapping = self.static_map[msg.arbitration_id]
            raw_value = int.from_bytes(msg.data[:2], byteorder="little", signed=False)
            scaled_value = raw_value * mapping["scale"]
            return [{
                "metric": mapping["name"],
                "value": round(scaled_value, 2),
                "unit": mapping["unit"]
            }]
        else:
            return None

