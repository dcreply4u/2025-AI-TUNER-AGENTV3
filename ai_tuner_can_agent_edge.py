"""\
================================================================================
AI Tuner Edge Agent – CAN-to-cloud nerve center with built-in intelligence stack
================================================================================
This module stitches together CAN decoding, UDS diagnostics, local buffering,
analytics, MQTT publishing, and advanced advisory engines into one continuous loop.
Think of it as the mission control layer that feeds the UI, the cloud, and any
downstream ML models with curated intelligence.
"""

import os
import sys
import ssl
import json
import time
import sqlite3
import can
import cantools
import numpy as np
import paho.mqtt.client as mqtt
from datetime import datetime

# Import advanced capabilities from same directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from advanced_capabilities import (
    AdvancedSensorSuite,
    HealthScoringEngine,
    PredictiveMaintenanceAdvisor,
    suggest_advanced_features,
)
from ai.fault_analyzer import FaultAnalyzer
from ai.predictive_fault_detector import PredictiveFaultDetector
from data_logs import DataLogAutoParser

# Add parent directory to path for UDS modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
# Import UDS modules (handle folder name with spaces)
import importlib.util
uds_module_path = os.path.join(parent_dir, "CAN and UDS Communication", "uds_manager.py")
spec = importlib.util.spec_from_file_location("uds_manager", uds_module_path)
uds_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uds_module)
UDSManager = uds_module.UDSManager

# ---------------- Configuration ----------------
AWS_ENDPOINT = "your-iot-endpoint.amazonaws.com"
AWS_PORT = 8883
TOPIC = "ai-tuner/telemetry/car001"

CA_CERT = "AmazonRootCA1.pem"
DEVICE_CERT = "device-cert.pem"
PRIVATE_KEY = "private-key.pem"

CAN_CHANNEL = "can0"
CAN_BUSTYPE = "socketcan"
DBC_FILE = "vehicle.dbc"
PROJECT_NAME = "AI-Tuner"
ADVANCED_FEATURES = suggest_advanced_features()
DATA_LOG_FILE = os.environ.get("DATA_LOG_FILE")

# Canonical metric mapping to align sensor names with scoring rules
CANONICAL_METRICS = {
    "Lambda": "Lambda",
    "Wideband_AFR": "Lambda",
    "AFR": "Lambda",
    "Knock_Count": "Knock_Count",
    "Knock_Intensity": "Knock_Count",
    "Oil_Pressure": "Oil_Pressure",
    "OilPressure": "Oil_Pressure",
    "Coolant_Temp": "Coolant_Temp",
    "Engine_Coolant_Temp": "Coolant_Temp",
    "Boost_Pressure": "Boost_Pressure",
    "Manifold_Pressure": "Boost_Pressure",
    "Fuel_Pressure": "Fuel_Pressure",
    "FuelRail_Pressure": "Fuel_Pressure",
    "FlexFuel_Percent": "Ethanol_Content",
    "Fuel_EthanolPercent": "Ethanol_Content",
    "EthanolContent": "Ethanol_Content",
    "MethInjection_Duty": "Methanol_Flow",
    "Methanol_Flow": "Methanol_Flow",
    "Meth_Tank_Level": "Methanol_Level",
    "Nitrous_Bottle_Pressure": "Nitrous_Bottle_Pressure",
    "Nitrous_Pressure": "Nitrous_Bottle_Pressure",
    "Nitrous_Solenoid": "Nitrous_Solenoid_State",
    "Nitrous_Solenoid_State": "Nitrous_Solenoid_State",
    "NitroMethane_Percentage": "NitroMethanePercentage",
    "NitroMethanePercentage": "NitroMethanePercentage",
    "Nitro_Percentage": "NitroMethanePercentage",
    "NitroPercentage": "NitroMethanePercentage",
    "Nitro_Pressure": "NitroPressure",
    "NitroPressure": "NitroPressure",
    "MethInjection_Duty": "MethInjectionDuty",
    "MethInjectionDuty": "MethInjectionDuty",
    "Meth_Tank_Level": "MethTankLevel",
    "MethTankLevel": "MethTankLevel",
    "Meth_Flow_Rate": "MethFlowRate",
    "MethFlowRate": "MethFlowRate",
    "FlexFuel_Percent": "FlexFuelPercent",
    "FlexFuelPercent": "FlexFuelPercent",
    "Ethanol_Content": "FlexFuelPercent",
    "EthanolContent": "FlexFuelPercent",
    "TransBrake_Status": "TransBrake_State",
    "TransBrake": "TransBrake_State",
    # Diesel-specific metrics
    "FuelRail_Pressure": "FuelRailPressure",
    "RailPressure": "FuelRailPressure",
    "Injection_Timing": "InjectionTiming",
    "FuelTiming": "InjectionTiming",
    "Injection_Quantity": "InjectionQuantity",
    "EGT": "EGT",
    "ExhaustGasTemp": "EGT",
    "EGT_PreTurbo": "EGT_PreTurbo",
    "EGT_PostTurbo": "EGT_PostTurbo",
    "VGT_Position": "VGT_Position",
    "EGR_Position": "EGR_Position",
    "EGR_Flow": "EGR_Flow",
    "DPF_Pressure": "DPF_Pressure",
    "DPF_Regen_Status": "DPF_Regen_Status",
    "DEF_Level": "DEF_Level",
    "AdBlueLevel": "DEF_Level",
    "NOX_Sensor": "NOX_Sensor",
}


def canonical_metric(metric_name):
    """Normalize sensor names for downstream analytics."""
    return CANONICAL_METRICS.get(metric_name, metric_name)

# ---------------- DBC Loader ----------------
class DBCSignalMapper:
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
            0x18FF65E5: {"name": "FlexFuel_Percent", "scale": 0.1, "unit": "%"},
            0x18FF70E5: {"name": "MethInjection_Duty", "scale": 0.4, "unit": "%"},
            0x18FF75E5: {"name": "Meth_Tank_Level", "scale": 0.4, "unit": "%"},
            0x18EF12A0: {"name": "Nitrous_Bottle_Pressure", "scale": 0.5, "unit": "psi"},
            0x18EF12A1: {"name": "Nitrous_Solenoid", "scale": 1.0, "unit": "state"},
            0x18EF12A2: {"name": "TransBrake_Status", "scale": 1.0, "unit": "state"},
        }

    def decode(self, msg):
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

# ---------------- Local Buffer ----------------
class LocalBuffer:
    def __init__(self, db_path="telemetry_buffer.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS buffer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER,
        payload TEXT
        )
        """)

    def add(self, payload):
        self.conn.execute("INSERT INTO buffer (timestamp, payload) VALUES (?, ?)",
                         (int(time.time()), json.dumps(payload)))
        self.conn.commit()

    def flush(self, publisher):
        cursor = self.conn.execute("SELECT id, payload FROM buffer ORDER BY id ASC")
        rows = cursor.fetchall()
        for row_id, payload in rows:
            if publisher.publish(json.loads(payload)):
                self.conn.execute("DELETE FROM buffer WHERE id=?", (row_id,))
                self.conn.commit()

# ---------------- MQTT Publisher ----------------
class TelemetryPublisher:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.tls_set(
            ca_certs=CA_CERT,
            certfile=DEVICE_CERT,
            keyfile=PRIVATE_KEY,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.connected = False

        try:
            self.client.connect(AWS_ENDPOINT, AWS_PORT)
            self.client.loop_start()
        except Exception as e:
            print(f"[ERROR] MQTT connection failed: {e}")

    def on_connect(self, client, userdata, flags, rc):
        self.connected = True
        print("[MQTT] Connected to AWS IoT Core")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("[MQTT] Disconnected from AWS IoT Core")

    def publish(self, payload):
        if not self.connected:
            return False
        try:
            self.client.publish(TOPIC, json.dumps(payload), qos=1)
            return True
        except Exception as e:
            print(f"[ERROR] Publish failed: {e}")
            return False

# ---------------- Edge Analytics ----------------
class EdgeAnalytics:
    """
    Performs rolling averages, anomaly detection, and DTC decoding.
    """

    def __init__(self, window_size=20):
        self.window_size = window_size
        self.data = {}

    def update(self, metric, value):
        if metric not in self.data:
            self.data[metric] = []
        self.data[metric].append(value)
        if len(self.data[metric]) > self.window_size:
            self.data[metric].pop(0)

    def rolling_average(self, metric):
        if metric not in self.data or len(self.data[metric]) == 0:
            return None
        return float(np.mean(self.data[metric]))

    def detect_anomaly(self, metric, value, threshold=3.0):
        if metric not in self.data or len(self.data[metric]) < 5:
            return False
        mean = np.mean(self.data[metric])
        std = np.std(self.data[metric])
        if std == 0:
            return False
        z_score = abs((value - mean) / std)
        return z_score > threshold

    def decode_dtc(self, msg):
        """
        Example DTC decoding for OBD-II frames (PID 0x03).
        """
        if msg.arbitration_id == 0x7E8 and msg.data[1] == 0x43:
            dtc_bytes = msg.data[2:]
            dtcs = []
            for i in range(0, len(dtc_bytes), 2):
                if i+1 >= len(dtc_bytes):
                    break
                code = (dtc_bytes[i] << 8) | dtc_bytes[i+1]
                if code == 0:
                    continue
                prefix = ["P", "C", "B", "U"][(code >> 14) & 0x3]
                dtc = f"{prefix}{(code >> 12) & 0x3}{(code >> 8) & 0xF}{(code >> 4) & 0xF}{code & 0xF}"
                dtcs.append(dtc)
            return dtcs
        return []

# ---------------- CAN Reader ----------------
class CANReader:
    def __init__(self, channel, bustype, mapper):
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)
        self.mapper = mapper

    def read(self):
        msg = self.bus.recv(timeout=1)
        if msg:
            decoded_list = self.mapper.decode(msg)
            return msg, decoded_list
        return None, None


def replay_data_log_file(
    file_path,
    analytics,
    health_engine,
    maintenance_advisor,
    fault_predictor,
    publish_callback,
):
    """
    Parse historical data logs (Holley, Haltech, MoTeC, etc.), auto-detect the
    protocol, and feed normalized metrics through the live analytics pipeline.
    """

    parser = DataLogAutoParser()
    session = parser.parse(file_path)
    base_timestamp = int(time.time())
    last_health_publish = 0
    health_publish_interval = 5

    print(
        f"[Replay] Detected {session.vendor} log ({session.protocol.value}) "
        f"with {len(session.records)} records."
    )

    for idx, record in enumerate(session.records):
        current_ts = base_timestamp + idx
        predictor_sample = {}
        for metric, value in record.items():
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue

            canonical = canonical_metric(metric)
            analytics.update(canonical, numeric_value)
            avg = analytics.rolling_average(canonical)
            anomaly = analytics.detect_anomaly(canonical, numeric_value)
            health_engine.update(canonical, numeric_value)
            maintenance_advisor.update(canonical, numeric_value, current_ts)

            if canonical in fault_predictor.features:
                predictor_sample[canonical] = numeric_value

            payload = {
                "device_id": "car001",
                "timestamp": current_ts,
                "metric": canonical,
                "value": numeric_value,
                "source": "log_replay",
                "protocol": session.protocol.value,
                "vendor": session.vendor,
                "rolling_avg": avg,
                "anomaly": anomaly,
            }
            publish_callback(payload)

        ai_alert = fault_predictor.update(predictor_sample)
        if ai_alert:
            publish_callback(
                {
                    "device_id": "car001",
                    "timestamp": current_ts,
                    "alert_type": "AI_PREDICTIVE",
                    "message": ai_alert,
                    "severity": "warning",
                    "source": "Log_Replay_AI",
                    "sample": predictor_sample,
                }
            )

        if (current_ts - last_health_publish) >= health_publish_interval:
            health_summary = health_engine.score()
            if health_summary:
                publish_callback(
                    {
                        "device_id": "car001",
                        "timestamp": current_ts,
                        "metric": "Engine_Health_Score",
                        "value": health_summary.pop("score"),
                        "unit": "score",
                        "details": health_summary,
                        "source": "log_replay",
                    }
                )
            for alert in maintenance_advisor.generate_alerts():
                publish_callback(
                    {
                        "device_id": "car001",
                        "timestamp": current_ts,
                        "alert_type": "Predictive_Maintenance",
                        "metric": alert["metric"],
                        "message": alert["message"],
                        "severity": alert["severity"],
                        "source": "log_replay",
                    }
                )
            last_health_publish = current_ts

    print("[Replay] Completed log ingestion.")

# ---------------- UDS Diagnostic Handler ----------------
class UDSDiagnosticHandler:
    """
    UDS diagnostic handler for advanced ECU communication.
    Integrates UDSManager for diagnostic services.
    """
    
    def __init__(self, channel="can0", bitrate=500000, txid=0x7E0, rxid=0x7E8):
        """
        Initialize UDS diagnostic handler.
        
        Args:
            channel: CAN channel name
            bitrate: CAN bus bitrate
            txid: Transmit CAN ID
            rxid: Receive CAN ID
        """
        try:
            self.uds_manager = UDSManager(channel=channel, bitrate=bitrate, txid=txid, rxid=rxid)
            self.enabled = True
            print("[UDS] UDS Diagnostic Handler initialized")
        except Exception as e:
            print(f"[UDS] Failed to initialize UDS Manager: {e}")
            self.uds_manager = None
            self.enabled = False
    
    def read_dtcs(self):
        """
        Read Diagnostic Trouble Codes using UDS Service 0x19.
        
        Returns:
            List of DTCs or None if failed
        """
        if not self.enabled:
            return None
        try:
            response = self.uds_manager.read_dtc_information(0x01)
            if response and len(response) > 2:
                # Parse DTC response (simplified - actual parsing depends on response format)
                dtcs = []
                # Add DTC parsing logic here based on UDS response format
                return dtcs
        except Exception as e:
            print(f"[UDS] Error reading DTCs: {e}")
        return None
    
    def clear_dtcs(self):
        """
        Clear Diagnostic Trouble Codes using UDS Service 0x14.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        try:
            response = self.uds_manager.clear_diagnostic_information()
            return response is not None
        except Exception as e:
            print(f"[UDS] Error clearing DTCs: {e}")
        return False
    
    def read_data_by_id(self, did):
        """
        Read data by identifier using UDS Service 0x22.
        
        Args:
            did: Data Identifier (2 bytes)
            
        Returns:
            Response data or None if failed
        """
        if not self.enabled:
            return None
        try:
            response = self.uds_manager.read_data_by_identifier(did)
            return response
        except Exception as e:
            print(f"[UDS] Error reading data by ID {hex(did)}: {e}")
        return None
    
    def close(self):
        """Close UDS manager connection."""
        if self.uds_manager:
            self.uds_manager.close()

# ---------------- Main Loop ----------------
def main():
    mapper = DBCSignalMapper(DBC_FILE)
    analytics = EdgeAnalytics()
    buffer = LocalBuffer()
    publisher = TelemetryPublisher()
    sensor_suite = AdvancedSensorSuite()
    health_engine = HealthScoringEngine()
    maintenance_advisor = PredictiveMaintenanceAdvisor()
    reader = CANReader(CAN_CHANNEL, CAN_BUSTYPE, mapper)
    fault_analyzer = FaultAnalyzer()
    fault_predictor = PredictiveFaultDetector(
        features=("Engine_RPM", "Throttle_Position", "Coolant_Temp", "Vehicle_Speed")
    )
    
    # Initialize UDS diagnostic handler (optional)
    uds_handler = UDSDiagnosticHandler(channel=CAN_CHANNEL, bitrate=500000)
    
    # Periodic UDS diagnostic check (every 60 seconds)
    last_uds_check = 0
    uds_check_interval = 60

    last_health_publish = 0
    health_publish_interval = 5

    print(f"[{PROJECT_NAME}] Starting intelligent CAN → Cloud telemetry stream...")
    print(f"[{PROJECT_NAME}] Advanced sensor count: {len(sensor_suite.all())}")
    for feature in ADVANCED_FEATURES:
        print(f"[Roadmap] {feature}")

    def publish_or_buffer(payload):
        if not publisher.publish(payload):
            buffer.add(payload)
        else:
            buffer.flush(publisher)

    if DATA_LOG_FILE:
        try:
            replay_data_log_file(
                DATA_LOG_FILE,
                analytics,
                health_engine,
                maintenance_advisor,
                fault_predictor,
                publish_or_buffer,
            )
        except FileNotFoundError:
            print(f"[Replay] Log file not found: {DATA_LOG_FILE}")
        except Exception as exc:
            print(f"[Replay] Failed to ingest log file: {exc}")
        return

    while True:
        try:
            msg, decoded_signals = reader.read()
            if not decoded_signals:
                continue

            # Periodic UDS DTC check
            current_time = time.time()
            if uds_handler.enabled and (current_time - last_uds_check) >= uds_check_interval:
                dtcs = uds_handler.read_dtcs()
                if dtcs:
                    insights = fault_analyzer.analyze(
                        [(dtc, "UDS reported trouble code") for dtc in dtcs]
                    )
                    for dtc, insight in zip(dtcs, insights):
                        alert_payload = {
                            "device_id": "car001",
                            "timestamp": int(current_time),
                            "alert_type": "UDS_DTC",
                            "code": dtc,
                            "severity": "warning",
                            "source": "UDS",
                            "ai_insight": insight,
                        }
                        publish_or_buffer(alert_payload)
                        print(f"[UDS] Diagnostic Trouble Code detected: {insight}")
                last_uds_check = current_time

            # DTC detection from CAN messages
            dtcs = analytics.decode_dtc(msg)
            if dtcs:
                insights = fault_analyzer.analyze(
                    [(dtc, "CAN frame reported trouble code") for dtc in dtcs]
                )
                for dtc, insight in zip(dtcs, insights):
                    alert_payload = {
                        "device_id": "car001",
                        "timestamp": int(time.time()),
                        "alert_type": "DTC",
                        "code": dtc,
                        "severity": "warning",
                        "source": "CAN",
                        "ai_insight": insight,
                    }
                    publish_or_buffer(alert_payload)
                    print(f"[ALERT] Diagnostic Trouble Code detected: {insight}")

            predictor_sample = {}

            # Normal telemetry
            for signal in decoded_signals:
                metric = signal["metric"]
                value = signal["value"]
                unit = signal["unit"]

                analytics.update(metric, value)
                avg = analytics.rolling_average(metric)
                anomaly = analytics.detect_anomaly(metric, value)
                canonical = canonical_metric(metric)
                health_engine.update(canonical, value)
                maintenance_advisor.update(canonical, value, current_time)
                if metric in fault_predictor.features:
                    predictor_sample[metric] = value

                payload = {
                    "device_id": "car001",
                    "timestamp": int(time.time()),
                    "metric": metric,
                    "value": value,
                    "unit": unit,
                    "rolling_avg": avg,
                    "anomaly": anomaly
                }

                publish_or_buffer(payload)

                status = "⚠️ Anomaly" if anomaly else ""
                print(f"[{datetime.now()}] {metric}: {value} {unit} (avg={avg}) {status}")

            ai_alert = fault_predictor.update(predictor_sample)
            if ai_alert:
                alert_payload = {
                    "device_id": "car001",
                    "timestamp": int(time.time()),
                    "alert_type": "AI_PREDICTIVE",
                    "message": ai_alert,
                    "severity": "warning",
                    "source": "Edge_AI",
                    "sample": predictor_sample,
                }
                publish_or_buffer(alert_payload)
                print(f"[AI] {ai_alert} -> {predictor_sample}")

            if (current_time - last_health_publish) >= health_publish_interval:
                health_summary = health_engine.score()
                if health_summary:
                    health_payload = {
                        "device_id": "car001",
                        "timestamp": int(time.time()),
                        "metric": "Engine_Health_Score",
                        "value": health_summary.pop("score"),
                        "unit": "score",
                        "details": health_summary,
                    }
                    publish_or_buffer(health_payload)

                trend_alerts = maintenance_advisor.generate_alerts()
                for alert in trend_alerts:
                    alert_payload = {
                        "device_id": "car001",
                        "timestamp": int(time.time()),
                        "alert_type": "Predictive_Maintenance",
                        "metric": alert["metric"],
                        "message": alert["message"],
                        "severity": alert["severity"],
                    }
                    publish_or_buffer(alert_payload)
                    print(f"[PM] {alert['message']}")

                last_health_publish = current_time

        except KeyboardInterrupt:
            print("\n[INFO] Stopping telemetry stream.")
            if uds_handler.enabled:
                uds_handler.close()
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
