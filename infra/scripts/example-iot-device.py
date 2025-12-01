#!/usr/bin/env python3
"""
Example IoT Device Script for AWS IoT Core

This script demonstrates how to connect an IoT device to AWS IoT Core
and publish sensor data to the MQTT topic.

Requirements:
    pip install paho-mqtt

Usage:
    1. Extract certificates using: ./scripts/save-iot-certs.sh
    2. Update the IOT_ENDPOINT and THING_NAME variables below
    3. Run: python3 scripts/example-iot-device.py
"""

import json
import random
import ssl
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

# ============================================
# Configuration - UPDATE THESE VALUES
# ============================================
IOT_ENDPOINT = "your-endpoint.iot.us-east-1.amazonaws.com"  # Get from: terraform output iot_endpoint
THING_NAME = "sensor-device-001"  # Get from: terraform output iot_thing_name
DEVICE_ID = "restroom_unit_1"  # Unique identifier for this sensor

# Certificate paths (relative to iot-certificates directory)
CERT_DIR = "../iot-certificates"
ROOT_CA = f"{CERT_DIR}/AmazonRootCA1.pem"
CERT_FILE = f"{CERT_DIR}/device-certificate.pem.crt"
KEY_FILE = f"{CERT_DIR}/private.pem.key"

# MQTT Topics
TOPIC_BASE = f"sensors/{DEVICE_ID}"
TOPIC_OCCUPANCY = f"{TOPIC_BASE}/occupancy"
TOPIC_ENVIRONMENT = f"{TOPIC_BASE}/environment"
TOPIC_STATUS = f"{TOPIC_BASE}/status"

# Publishing interval (seconds)
PUBLISH_INTERVAL = 30


# ============================================
# MQTT Callbacks
# ============================================


def on_connect(client, userdata, flags, rc):
    """Callback when connection is established"""
    if rc == 0:
        print(f"✓ Connected to AWS IoT Core successfully!")
        print(f"  Thing Name: {THING_NAME}")
        print(f"  Device ID: {DEVICE_ID}")
        print(f"  Publishing to: {TOPIC_BASE}/*")
        print()

        # Subscribe to a topic if you want to receive commands (optional)
        # client.subscribe(f"commands/{DEVICE_ID}/#")

        # Publish initial status
        publish_status(client, "online")
    else:
        error_messages = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized",
        }
        error_msg = error_messages.get(rc, f"Unknown error code {rc}")
        print(f"✗ Connection failed: {error_msg}")
        sys.exit(1)


def on_disconnect(client, userdata, rc):
    """Callback when disconnected"""
    if rc != 0:
        print(f"✗ Unexpected disconnection (code: {rc}). Attempting to reconnect...")
    else:
        print("✓ Disconnected cleanly")


def on_publish(client, userdata, mid):
    """Callback when message is published"""
    print(f"  Message {mid} published successfully")


def on_message(client, userdata, msg):
    """Callback when message is received (for subscriptions)"""
    print(f"← Received message on {msg.topic}:")
    print(f"  {msg.payload.decode()}")


def on_log(client, userdata, level, buf):
    """Callback for MQTT client logs (for debugging)"""
    # Uncomment for detailed debugging
    # print(f"[LOG] {buf}")
    pass


# ============================================
# Publishing Functions
# ============================================


def publish_occupancy_data(client):
    """Publish occupancy sensor data"""
    # Simulate occupancy sensor (True/False)
    is_occupied = random.choice([True, False])

    payload = {
        "device_id": DEVICE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "occupied": is_occupied,
        "confidence": round(random.uniform(0.85, 1.0), 2),  # Sensor confidence
    }

    result = client.publish(TOPIC_OCCUPANCY, json.dumps(payload), qos=1)

    status = "🚹 OCCUPIED" if is_occupied else "🚪 VACANT"
    print(f"→ Published occupancy: {status}")

    return result


def publish_environment_data(client):
    """Publish environmental sensor data"""
    # Simulate temperature, humidity, and air quality sensors
    payload = {
        "device_id": DEVICE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "temperature": round(random.uniform(20.0, 26.0), 1),  # Celsius
        "humidity": round(random.uniform(40.0, 70.0), 1),  # Percentage
        "air_quality_index": random.randint(30, 100),  # 0-500 scale
        "ammonia_level": round(random.uniform(0.1, 5.0), 2),  # ppm
    }

    result = client.publish(TOPIC_ENVIRONMENT, json.dumps(payload), qos=1)

    print(
        f"→ Published environment: {payload['temperature']}°C, {payload['humidity']}% humidity"
    )

    return result


def publish_status(client, status):
    """Publish device status"""
    payload = {
        "device_id": DEVICE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": status,
        "battery_level": round(random.uniform(80, 100), 1)
        if status == "online"
        else None,
        "signal_strength": random.randint(-70, -40),  # dBm
    }

    result = client.publish(TOPIC_STATUS, json.dumps(payload), qos=1)

    print(f"→ Published status: {status}")

    return result


# ============================================
# Main Function
# ============================================


def main():
    """Main function to run the IoT device simulator"""

    print("=" * 60)
    print("AWS IoT Core - Example Device Simulator")
    print("=" * 60)
    print()

    # Validate configuration
    if IOT_ENDPOINT == "your-endpoint.iot.us-east-1.amazonaws.com":
        print("✗ ERROR: Please update IOT_ENDPOINT in the script!")
        print("  Get it from: cd infra/ && terraform output iot_endpoint")
        sys.exit(1)

    # Check if certificate files exist
    import os

    for file_path in [ROOT_CA, CERT_FILE, KEY_FILE]:
        if not os.path.exists(file_path):
            print(f"✗ ERROR: Certificate file not found: {file_path}")
            print("  Run: ./scripts/save-iot-certs.sh")
            sys.exit(1)

    # Create MQTT client
    print(f"Creating MQTT client...")
    client = mqtt.Client(client_id=THING_NAME, protocol=mqtt.MQTTv311)

    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    client.on_message = on_message
    client.on_log = on_log

    # Configure TLS/SSL
    print(f"Configuring TLS...")
    try:
        client.tls_set(
            ca_certs=ROOT_CA,
            certfile=CERT_FILE,
            keyfile=KEY_FILE,
            tls_version=ssl.PROTOCOL_TLSv1_2,
        )
        client.tls_insecure_set(False)  # Verify server certificate
    except Exception as e:
        print(f"✗ TLS configuration failed: {e}")
        sys.exit(1)

    # Connect to AWS IoT Core
    print(f"Connecting to {IOT_ENDPOINT}:8883...")
    try:
        client.connect(IOT_ENDPOINT, 8883, 60)
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)

    # Start network loop in background
    client.loop_start()

    # Give it a moment to connect
    time.sleep(2)

    # Main publishing loop
    print()
    print("=" * 60)
    print(f"Publishing sensor data every {PUBLISH_INTERVAL} seconds...")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        message_count = 0
        while True:
            message_count += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Message #{message_count}")

            # Publish different types of sensor data
            publish_occupancy_data(client)
            time.sleep(0.5)  # Small delay between messages

            publish_environment_data(client)
            time.sleep(0.5)

            # Publish status every 10 messages
            if message_count % 10 == 0:
                publish_status(client, "online")

            print()

            # Wait before next publish cycle
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("Shutting down gracefully...")

        # Publish offline status before disconnecting
        publish_status(client, "offline")
        time.sleep(1)

        # Disconnect
        client.loop_stop()
        client.disconnect()

        print("✓ Disconnected successfully")
        print("=" * 60)


if __name__ == "__main__":
    main()
