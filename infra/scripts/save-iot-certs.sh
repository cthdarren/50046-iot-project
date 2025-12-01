#!/bin/bash

# Script to extract and save IoT certificates from Terraform outputs
# Run this after applying Terraform to get the credentials for your IoT devices

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/../../infra"
CERTS_DIR="$SCRIPT_DIR/../../iot-certificates"

echo "======================================"
echo "IoT Certificate Extraction Script"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -d "$INFRA_DIR" ]; then
    echo "Error: infra directory not found at $INFRA_DIR"
    exit 1
fi

# Create certificates directory
mkdir -p "$CERTS_DIR"

cd "$INFRA_DIR"

echo "Extracting IoT certificates from Terraform outputs..."
echo ""

# Extract the IoT endpoint
IOT_ENDPOINT=$(terraform output -raw iot_endpoint 2>/dev/null || echo "")
if [ -z "$IOT_ENDPOINT" ]; then
    echo "Error: Could not retrieve IoT endpoint. Have you run 'terraform apply'?"
    exit 1
fi

# Extract Thing name
THING_NAME=$(terraform output -raw iot_thing_name 2>/dev/null || echo "sensor-device-001")

# Save the certificate
echo "Saving device certificate..."
terraform output -raw iot_certificate_pem > "$CERTS_DIR/device-certificate.pem.crt"

# Save the private key
echo "Saving private key..."
terraform output -raw iot_private_key > "$CERTS_DIR/private.pem.key"

# Save the public key
echo "Saving public key..."
terraform output -raw iot_public_key > "$CERTS_DIR/public.pem.key"

# Download Amazon Root CA certificate
echo "Downloading Amazon Root CA certificate..."
curl -s https://www.amazontrust.com/repository/AmazonRootCA1.pem -o "$CERTS_DIR/AmazonRootCA1.pem"

# Set appropriate permissions (private key should be read-only by owner)
chmod 600 "$CERTS_DIR/private.pem.key"
chmod 644 "$CERTS_DIR/device-certificate.pem.crt"
chmod 644 "$CERTS_DIR/public.pem.key"
chmod 644 "$CERTS_DIR/AmazonRootCA1.pem"

# Create a connection info file
cat > "$CERTS_DIR/connection-info.txt" << EOF
AWS IoT Core Connection Information
====================================

IoT Endpoint: $IOT_ENDPOINT
Thing Name: $THING_NAME
Port (MQTT over TLS): 8883
Port (MQTT over WebSocket): 443

Certificate Files:
- Device Certificate: device-certificate.pem.crt
- Private Key: private.pem.key
- Root CA: AmazonRootCA1.pem

MQTT Topics:
- Publish to: sensors/<device-id>
- Subscribe to: sensors/<device-id> (if needed)

Example mosquitto_pub command:
------------------------------
mosquitto_pub \\
  --cafile AmazonRootCA1.pem \\
  --cert device-certificate.pem.crt \\
  --key private.pem.key \\
  -h $IOT_ENDPOINT \\
  -p 8883 \\
  -t sensors/device123 \\
  -m '{"temperature":23.5,"humidity":45}'

Python Example (paho-mqtt):
---------------------------
import paho.mqtt.client as mqtt
import ssl
import json

client = mqtt.Client(client_id="$THING_NAME")
client.tls_set(
    ca_certs="AmazonRootCA1.pem",
    certfile="device-certificate.pem.crt",
    keyfile="private.pem.key",
    tls_version=ssl.PROTOCOL_TLSv1_2
)
client.connect("$IOT_ENDPOINT", 8883, 60)

# Publish a message
payload = {"temperature": 23.5, "humidity": 45}
client.publish("sensors/device123", json.dumps(payload))
client.disconnect()

EOF

echo ""
echo "======================================"
echo "SUCCESS! Certificates saved to:"
echo "$CERTS_DIR"
echo "======================================"
echo ""
echo "Files created:"
echo "  - device-certificate.pem.crt"
echo "  - private.pem.key (permissions: 600)"
echo "  - public.pem.key"
echo "  - AmazonRootCA1.pem"
echo "  - connection-info.txt"
echo ""
echo "⚠️  IMPORTANT: Keep these files secure!"
echo "The private key should NEVER be committed to version control."
echo ""
echo "See connection-info.txt for usage examples."
echo ""
