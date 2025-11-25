"""
Telemetry Publisher Module
Handles MQTT publishing to AWS IoT Core
"""

import json
import ssl
import paho.mqtt.client as mqtt
from config import AWS_ENDPOINT, AWS_PORT, TOPIC, CA_CERT, DEVICE_CERT, PRIVATE_KEY


class TelemetryPublisher:
    """MQTT publisher for AWS IoT Core"""
    
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
        """Callback for successful MQTT connection"""
        self.connected = True
        print("[MQTT] Connected to AWS IoT Core")

    def on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False
        print("[MQTT] Disconnected from AWS IoT Core")

    def publish(self, payload):
        """Publish payload to MQTT topic"""
        if not self.connected:
            return False
        try:
            self.client.publish(TOPIC, json.dumps(payload), qos=1)
            return True
        except Exception as e:
            print(f"[ERROR] Publish failed: {e}")
            return False

