# AWS IoT Core Setup Guide

This guide explains how to deploy and use AWS IoT Core infrastructure for connecting IoT devices to your cloud backend.

## Architecture Overview

```
IoT Device (with certificate)
    ↓ MQTT over TLS (port 8883)
AWS IoT Core Endpoint
    ↓ Topic Rule (sensors/#)
Lambda Function (iot_handler)
    ↓
RDS Proxy → PostgreSQL Database
```

## What's Included

The Terraform configuration creates:

1. **IoT Topic Rule** (`iot_to_lambda`)
   - Subscribes to all topics matching `sensors/#`
   - Routes messages to Lambda function
   - SQL: `SELECT * FROM 'sensors/#'`

2. **IoT Policy** (`sensor_device_policy`)
   - Allows devices to connect
   - Allows publishing to `sensors/*` topics
   - Allows subscribing to `sensors/*` topics (for bidirectional communication)

3. **IoT Certificate**
   - X.509 certificate for device authentication
   - Private/public key pair generated automatically

4. **IoT Thing** (`sensor-device-001`)
   - Represents a physical device
   - Can have attributes (device_type, location, etc.)

## Deployment Steps

### 1. Apply Terraform

From the `infra/` directory:

```bash
terraform apply
```

Review the plan and type `yes` to create the IoT resources.

### 2. Extract Certificates

After Terraform completes, run the certificate extraction script:

```bash
cd ..  # Go back to project root
./scripts/save-iot-certs.sh
```

This will create an `iot-certificates/` directory with:
- `device-certificate.pem.crt` - Device certificate
- `private.pem.key` - Private key (keep this secure!)
- `public.pem.key` - Public key
- `AmazonRootCA1.pem` - Amazon Root CA certificate
- `connection-info.txt` - Connection details and examples

### 3. View Connection Information

```bash
cat iot-certificates/connection-info.txt
```

Or get individual outputs from Terraform:

```bash
cd infra/
terraform output iot_endpoint
terraform output iot_thing_name
```

## Testing Your IoT Setup

### Option 1: AWS IoT Console (Quick Test)

1. Go to [AWS IoT Console](https://console.aws.amazon.com/iot/)
2. Navigate to **Test** → **MQTT test client**
3. Click **Publish to a topic**
4. Topic name: `sensors/test`
5. Message payload:
   ```json
   {
     "temperature": 23.5,
     "humidity": 45,
     "device_id": "test-device"
   }
   ```
6. Click **Publish**

Your Lambda function should be invoked and the data stored in PostgreSQL.

### Option 2: mosquitto_pub (Command Line)

Using the extracted certificates:

```bash
cd iot-certificates/

mosquitto_pub \
  --cafile AmazonRootCA1.pem \
  --cert device-certificate.pem.crt \
  --key private.pem.key \
  -h YOUR_IOT_ENDPOINT \
  -p 8883 \
  -t sensors/device123 \
  -m '{"temperature":23.5,"humidity":45}'
```

Replace `YOUR_IOT_ENDPOINT` with the output from `terraform output iot_endpoint`.

### Option 3: Python Script

```python
import paho.mqtt.client as mqtt
import ssl
import json
import time

# Connection settings (get these from terraform output)
IOT_ENDPOINT = "your-endpoint.iot.us-east-1.amazonaws.com"
THING_NAME = "sensor-device-001"
TOPIC = "sensors/device123"

# Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully!")
        
        # Publish a test message
        payload = {
            "temperature": 23.5,
            "humidity": 45,
            "device_id": "device123",
            "timestamp": int(time.time())
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f"Published: {payload}")
    else:
        print(f"Connection failed with code {rc}")

def on_publish(client, userdata, mid):
    print("Message published successfully")
    client.disconnect()

# Create MQTT client
client = mqtt.Client(client_id=THING_NAME)
client.on_connect = on_connect
client.on_publish = on_publish

# Configure TLS
client.tls_set(
    ca_certs="AmazonRootCA1.pem",
    certfile="device-certificate.pem.crt",
    keyfile="private.pem.key",
    tls_version=ssl.PROTOCOL_TLSv1_2
)

# Connect and publish
print(f"Connecting to {IOT_ENDPOINT}...")
client.connect(IOT_ENDPOINT, 8883, 60)
client.loop_forever()
```

Install dependencies:
```bash
pip install paho-mqtt
```

## Adding More Devices

### Option 1: Duplicate Resources (Simple)

In `infra/iot.tf`, duplicate the Thing, Certificate, and attachment resources:

```hcl
# Device 2
resource "aws_iot_certificate" "sensor_cert_2" {
  active = true
}

resource "aws_iot_thing" "sensor_device_2" {
  name = "sensor-device-002"
  
  attributes = {
    device_type = "occupancy_sensor"
    location    = "restroom_unit_2"
  }
}

resource "aws_iot_policy_attachment" "sensor_policy_attach_2" {
  policy = aws_iot_policy.sensor_policy.name
  target = aws_iot_certificate.sensor_cert_2.arn
}

resource "aws_iot_thing_principal_attachment" "sensor_thing_attach_2" {
  principal = aws_iot_certificate.sensor_cert_2.arn
  thing     = aws_iot_thing.sensor_device_2.name
}
```

### Option 2: Use a Module (Recommended for many devices)

Create `infra/modules/iot-device/main.tf`:

```hcl
resource "aws_iot_certificate" "cert" {
  active = true
}

resource "aws_iot_thing" "thing" {
  name       = var.device_name
  attributes = var.attributes
}

resource "aws_iot_policy_attachment" "attach" {
  policy = var.policy_name
  target = aws_iot_certificate.cert.arn
}

resource "aws_iot_thing_principal_attachment" "thing_attach" {
  principal = aws_iot_certificate.cert.arn
  thing     = aws_iot_thing.thing.name
}
```

Then in `iot.tf`:

```hcl
module "sensor_device_1" {
  source      = "./modules/iot-device"
  device_name = "sensor-device-001"
  policy_name = aws_iot_policy.sensor_policy.name
  attributes  = {
    device_type = "occupancy_sensor"
    location    = "restroom_unit_1"
  }
}

module "sensor_device_2" {
  source      = "./modules/iot-device"
  device_name = "sensor-device-002"
  policy_name = aws_iot_policy.sensor_policy.name
  attributes  = {
    device_type = "occupancy_sensor"
    location    = "restroom_unit_2"
  }
}
```

## Topic Naming Convention

Follow this pattern for your MQTT topics:

```
sensors/{device_id}/{metric_type}
```

Examples:
- `sensors/restroom1/occupancy`
- `sensors/restroom1/temperature`
- `sensors/restroom2/humidity`
- `sensors/device123/status`

All of these will be matched by the Topic Rule `sensors/#` and routed to Lambda.

## Security Best Practices

1. **Never commit certificates to Git**
   - The `.gitignore` is already configured to exclude `iot-certificates/`
   - Store certificates securely on devices only

2. **Rotate certificates regularly**
   - AWS IoT supports certificate rotation
   - Create new certificates and deactivate old ones

3. **Use Thing Groups for better organization**
   - Group devices by location or type
   - Apply policies at the group level

4. **Enable CloudWatch Logs**
   - Monitor IoT Core activity
   - Debug connection issues

5. **Use device-specific client IDs**
   - Each device should use its Thing Name as client ID
   - Prevents conflicts and aids in troubleshooting

## Monitoring & Debugging

### Check Lambda Invocations

```bash
aws logs tail /aws/lambda/iot_ts_handler --follow
```

### Check IoT Core Logs

Enable logging in AWS Console:
1. Go to IoT Core → Settings
2. Enable CloudWatch Logs
3. Set role with appropriate permissions

View logs:
```bash
aws logs tail AWSIotLogsV2 --follow
```

### Test Topic Rule

In AWS Console:
1. Go to IoT Core → Message routing → Rules
2. Click on `iot_to_lambda`
3. View metrics and recent invocations

### Verify Certificate Status

```bash
aws iot describe-certificate --certificate-id <certificate-id>
```

Get certificate ID from Terraform:
```bash
terraform output iot_certificate_arn | cut -d'/' -f2
```

## Troubleshooting

### Device Can't Connect

1. **Check certificate is active**
   ```bash
   aws iot list-certificates
   ```

2. **Verify endpoint is correct**
   ```bash
   terraform output iot_endpoint
   ```

3. **Ensure policy allows connection**
   - Policy must allow `iot:Connect` with correct Resource ARN

4. **Check time sync on device**
   - TLS requires accurate time (within 15 minutes)

### Messages Not Reaching Lambda

1. **Verify topic matches rule**
   - Rule subscribes to `sensors/#`
   - Your topic must start with `sensors/`

2. **Check Lambda execution role**
   - Lambda needs VPC access permissions
   - Lambda needs RDS access permissions

3. **View CloudWatch metrics**
   - IoT Core → Message routing → Rules → Metrics

### Certificate Errors

1. **Ensure all certificate files are present**
   - Device certificate
   - Private key
   - Root CA

2. **Check file permissions**
   - Private key should be `600` (read-only by owner)

3. **Verify certificate format**
   - Must be PEM format
   - No extra whitespace or characters

## Cost Considerations

- **IoT Core**: $1.00 per 1M messages (first 1M/month free)
- **Lambda Invocations**: $0.20 per 1M requests (first 1M/month free)
- **Data Transfer**: $0.09/GB after 1GB free tier
- **Certificate Storage**: Free

For a restroom monitoring system with 10 sensors sending data every 30 seconds:
- Messages per month: 10 × 2 × 60 × 24 × 30 = 864,000 messages
- Cost: ~$0 (within free tier)

## Next Steps

1. **Set up device firmware**
   - Use the certificate files in your IoT device code
   - Implement MQTT connection logic
   - Handle reconnection on network failures

2. **Implement data validation in Lambda**
   - Validate message format
   - Handle malformed data gracefully

3. **Add device shadows** (optional)
   - Store device state in AWS IoT
   - Enable bidirectional communication

4. **Set up fleet provisioning** (for production)
   - Automate certificate generation for new devices
   - Use claim certificates for initial setup

## References

- [AWS IoT Core Documentation](https://docs.aws.amazon.com/iot/)
- [MQTT Protocol](https://mqtt.org/)
- [Terraform AWS IoT Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iot_thing)