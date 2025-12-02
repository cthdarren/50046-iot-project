#!/usr/bin/env python3
"""
IoT Device Simulator for AWS IoT Core - Restroom Analytics

This script simulates a restroom cubicle sensor that publishes occupancy
and toilet roll data to AWS IoT Core, which triggers a Lambda function
to store the data in RDS PostgreSQL.

The Lambda function expects events with:
- cubicle_id: int (cubicle identifier)
- occupied: boolean (whether cubicle is occupied)
- toilet_roll_percentage: int (0-100, toilet paper remaining)

Requirements:
    pip install paho-mqtt

Usage:
    1. Extract certificates: cd infra && make save-iot-certs
    2. Update IOT_ENDPOINT and THING_NAME below (or use terraform output)
    3. Run: python3 infra/scripts/example-iot-device.py
"""

import json
import os
import random
import ssl
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

# ============================================
# Configuration - UPDATE THESE VALUES
# ============================================
IOT_ENDPOINT = "a1bbfu51vx9kob-ats.iot.ap-southeast-1.amazonaws.com"  # Get from: terraform output iot_endpoint
THING_NAME = "sensor-device-001"  # Get from: terraform output iot_thing_name
CUBICLE_ID = 1  # Cubicle identifier (must exist in cubicles table)

# Certificate paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CERT_DIR = os.path.join(PROJECT_ROOT, "iot-certificates")

ROOT_CA = os.path.join(CERT_DIR, "AmazonRootCA1.pem")
CERT_FILE = os.path.join(CERT_DIR, "device-certificate.pem.crt")
KEY_FILE = os.path.join(CERT_DIR, "private.pem.key")

# MQTT Topic - IoT Rule should route this to Lambda
TOPIC_CUBICLE_EVENTS = f"cubicle/{CUBICLE_ID}/events"

# Publishing interval (seconds)
PUBLISH_INTERVAL = 30

# Simulation settings
SIMULATE_USAGE_PATTERNS = True  # Simulate realistic usage patterns
USAGE_DURATION_MIN = 2  # Minimum time occupied (minutes)
USAGE_DURATION_MAX = 10  # Maximum time occupied (minutes)


# ============================================
# Cubicle State Simulator
# ============================================


class CubicleSimulator:
    """Simulates realistic cubicle usage patterns"""

    def __init__(self, cubicle_id):
        self.cubicle_id = cubicle_id
        self.occupied = False
        self.toilet_roll_percentage = 100
        self.occupancy_start_time = None
        self.occupancy_duration = None
        self.usage_count = 0

    def update_state(self):
        """Update cubicle state based on time and usage"""
        current_time = time.time()

        if not self.occupied:
            # Randomly occupy the cubicle (20% chance per cycle)
            if random.random() < 0.2:
                self.occupied = True
                self.occupancy_start_time = current_time
                # Random usage duration between 2-10 minutes
                self.occupancy_duration = random.randint(
                    USAGE_DURATION_MIN * 60, USAGE_DURATION_MAX * 60
                )
                print(
                    f"  🚹 Cubicle {self.cubicle_id} OCCUPIED (duration: {self.occupancy_duration // 60}min)"
                )
        else:
            # Check if occupancy duration has elapsed
            if (
                self.occupancy_start_time
                and current_time - self.occupancy_start_time >= self.occupancy_duration
            ):
                self.occupied = False
                self.occupancy_start_time = None
                self.occupancy_duration = None
                self.usage_count += 1

                # Decrease toilet roll after each use
                decrease = random.randint(5, 15)
                self.toilet_roll_percentage = max(
                    0, self.toilet_roll_percentage - decrease
                )

                # Randomly refill toilet roll (10% chance when below 30%)
                if self.toilet_roll_percentage < 30 and random.random() < 0.1:
                    self.toilet_roll_percentage = 100
                    print(f"  🧻 Toilet roll REFILLED to 100%")

                print(
                    f"  🚪 Cubicle {self.cubicle_id} VACANT (uses: {self.usage_count}, roll: {self.toilet_roll_percentage}%)"
                )

    def get_state(self):
        """Get current cubicle state"""
        return {
            "cubicle_id": self.cubicle_id,
            "occupied": self.occupied,
            "toilet_roll_percentage": self.toilet_roll_percentage,
        }


# ============================================
# MQTT Callbacks
# ============================================


def on_connect(client, userdata, flags, rc):
    """Callback when connection is established"""
    if rc == 0:
        print(f"✓ Connected to AWS IoT Core successfully!")
        print(f"  Thing Name: {THING_NAME}")
        print(f"  Cubicle ID: {CUBICLE_ID}")
        print(f"  Publishing to: {TOPIC_CUBICLE_EVENTS}")
        print(f"  IoT Endpoint: {IOT_ENDPOINT}")
        print()

        # Optionally subscribe to commands topic
        # client.subscribe(f"commands/cubicle/{CUBICLE_ID}/#")

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
    pass  # Silent to reduce noise


def on_message(client, userdata, msg):
    """Callback when message is received (for subscriptions)"""
    print(f"← Received message on {msg.topic}:")
    try:
        payload = json.loads(msg.payload.decode())
        print(f"  {json.dumps(payload, indent=2)}")
    except:
        print(f"  {msg.payload.decode()}")


def on_log(client, userdata, level, buf):
    """Callback for MQTT client logs (for debugging)"""
    # Uncomment for detailed debugging
    # print(f"[LOG] {buf}")
    pass


# ============================================
# Publishing Functions
# ============================================


def publish_cubicle_state(client, state):
    """
    Publish cubicle state to IoT Core

    Payload format matches Lambda handler expectations:
    {
        "cubicle_id": int,
        "occupied": boolean,
        "toilet_roll_percentage": int
    }
    """
    payload = {
        "cubicle_id": state["cubicle_id"],
        "occupied": state["occupied"],
        "toilet_roll_percentage": state["toilet_roll_percentage"],
    }

    # Add timestamp for logging (Lambda doesn't use this)
    timestamp = datetime.utcnow().isoformat() + "Z"

    try:
        result = client.publish(TOPIC_CUBICLE_EVENTS, json.dumps(payload), qos=1)

        status = "🚹 OCCUPIED" if state["occupied"] else "🚪 VACANT"
        print(
            f"→ [{timestamp}] Published: {status} | Roll: {state['toilet_roll_percentage']}% | Cubicle: {state['cubicle_id']}"
        )

        return result
    except Exception as e:
        print(f"✗ Publish failed: {e}")
        return None


# ============================================
# Main Function
# ============================================


def main():
    """Main function to run the IoT device simulator"""

    print("=" * 70)
    print("AWS IoT Core - Restroom Cubicle Sensor Simulator")
    print("=" * 70)
    print()

    # Validate configuration
    if "your-endpoint" in IOT_ENDPOINT:
        print("✗ ERROR: Please update IOT_ENDPOINT in the script!")
        print("  Get it from: cd infra/ && terraform output iot_endpoint")
        sys.exit(1)

    # Check if certificate files exist
    missing_files = []
    for file_path in [ROOT_CA, CERT_FILE, KEY_FILE]:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"✗ ERROR: Certificate files not found:")
        for f in missing_files:
            print(f"  - {f}")
        print()
        print("  Run: cd infra && make save-iot-certs")
        sys.exit(1)

    # Verify cubicle_id is set
    if CUBICLE_ID <= 0:
        print("✗ ERROR: Invalid CUBICLE_ID. Must be a positive integer.")
        print("  Make sure the cubicle exists in the database (cubicles table).")
        sys.exit(1)

    # Create cubicle simulator
    simulator = CubicleSimulator(CUBICLE_ID)

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
    print("=" * 70)
    print(f"Simulating cubicle sensor (ID: {CUBICLE_ID})")
    print(f"Publishing every {PUBLISH_INTERVAL} seconds...")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    try:
        message_count = 0
        while True:
            message_count += 1

            # Update simulator state
            if SIMULATE_USAGE_PATTERNS:
                simulator.update_state()

            # Get current state
            state = simulator.get_state()

            # Publish to IoT Core -> Lambda -> RDS
            publish_cubicle_state(client, state)

            # Wait before next publish cycle
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("Shutting down gracefully...")

        # Publish final state (vacant) before disconnecting
        final_state = simulator.get_state()
        final_state["occupied"] = False
        publish_cubicle_state(client, final_state)
        time.sleep(1)

        # Disconnect
        client.loop_stop()
        client.disconnect()

        print("✓ Disconnected successfully")
        print(f"✓ Total messages published: {message_count}")
        print("=" * 70)


# ============================================
# CLI Entry Point
# ============================================

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print(__doc__)
            print("\nConfiguration:")
            print(f"  IOT_ENDPOINT: {IOT_ENDPOINT}")
            print(f"  THING_NAME: {THING_NAME}")
            print(f"  CUBICLE_ID: {CUBICLE_ID}")
            print(f"  PUBLISH_INTERVAL: {PUBLISH_INTERVAL}s")
            print()
            print("Lambda Handler Expects:")
            print("  - cubicle_id (int)")
            print("  - occupied (boolean)")
            print("  - toilet_roll_percentage (int, 0-100)")
            print()
            print("Data Flow:")
            print("  IoT Device → IoT Core → IoT Rule → Lambda → RDS")
            print()
            print("Database Tables:")
            print("  - cubicles: Must contain a row with id matching CUBICLE_ID")
            print("  - cubicle_events: Stores historical event log")
            print("  - cubicle_states: Stores current state (upserted)")
            sys.exit(0)
        elif sys.argv[1] == "--test":
            # Test mode: publish one message and exit
            print("Test mode: Publishing single message...")
            PUBLISH_INTERVAL = 0
            SIMULATE_USAGE_PATTERNS = False

    main()
