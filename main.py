"""
Main Application Entry Point
AI-Tuner Agent: CAN → Cloud telemetry stream with edge ML
"""

import time
from datetime import datetime

from config import (
    CAN_CHANNEL, CAN_BUSTYPE, DBC_FILE, MODEL_FILE, PROJECT_NAME
)
from dbc_mapper import DBCSignalMapper
from edge_analytics import EdgeAnalytics
from edge_ml_model import EdgeMLModel
from local_buffer import LocalBuffer
from telemetry_publisher import TelemetryPublisher
from can_reader import CANReader


def main():
    """Main application loop"""
    mapper = DBCSignalMapper(DBC_FILE)
    analytics = EdgeAnalytics()
    ml_model = EdgeMLModel(MODEL_FILE)
    buffer = LocalBuffer()
    publisher = TelemetryPublisher()
    reader = CANReader(CAN_CHANNEL, CAN_BUSTYPE, mapper)

    print(f"[{PROJECT_NAME}] Starting AI‑enhanced CAN → Cloud telemetry stream...")
    
    while True:
        try:
            msg, decoded_signals = reader.read()
            if not decoded_signals:
                continue

            # Build feature vector for ML model
            feature_vector = []
            for signal in decoded_signals:
                analytics.update(signal["metric"], signal["value"])
                feature_vector.append(signal["value"])

            # Run ML inference
            ml_score = ml_model.predict(feature_vector) if ml_model.model else None
            ml_anomaly = ml_score is not None and ml_score > 0.8

            # Publish each signal
            for signal in decoded_signals:
                metric = signal["metric"]
                value = signal["value"]
                unit = signal["unit"]
                avg = analytics.rolling_average(metric)

                payload = {
                    "device_id": "car001",
                    "timestamp": int(time.time()),
                    "metric": metric,
                    "value": value,
                    "unit": unit,
                    "rolling_avg": avg,
                    "ml_score": ml_score,
                    "ml_anomaly": ml_anomaly
                }

                if not publisher.publish(payload):
                    buffer.add(payload)
                else:
                    buffer.flush(publisher)

                status = "⚠️ ML Anomaly" if ml_anomaly else ""
                print(f"[{datetime.now()}] {metric}: {value} {unit} (avg={avg}) {status}")

        except KeyboardInterrupt:
            print("\n[INFO] Stopping telemetry stream.")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()

