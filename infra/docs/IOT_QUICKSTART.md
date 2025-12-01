# AWS IoT Core - Quick Start Guide

This is a quick reference for getting your IoT devices connected to AWS IoT Core.

## Prerequisites

- ✅ Terraform applied (`cd infra/ && terraform apply`)
- ✅ AWS CLI configured with appropriate credentials
- ✅ `mosquitto_pub` installed (for testing) OR Python 3 with `paho-mqtt`

## Step 1: Extract Certificates (One-Time Setup)

After deploying infrastructure with Terraform, extract the device certificates:

```bash
./scripts/save-iot-certs.sh
```

This creates `iot-certificates/` directory with:
- Device certificate (`.pem.crt`)
- Private key (`.pem.key`)
- Root CA certificate
- Connection information

**⚠️ IMPORTANT:** These files contain secrets! Never commit them to Git.

## Step 2: Get Your IoT Endpoint

```bash
cd infra/
terraform output iot_endpoint
```

You'll get something like: `a3example123.iot.us-east-1.amazonaws.com`

## Step 3: Test Connection

### Option A: Quick Test with AWS Console

1. Go to [AWS IoT Console](https://console.aws.amazon.com/iot/)
2. Navigate to **Test** → **MQTT test client**
3. Click **Publish to a topic**
4. Topic: `sensors/test`
5. Message:
   ```json
   {
     "device_id": "test",
     "temperature": 23.5,
     "humidity": 45,
     "occupied": true
   }
   ```
6. Click **Publish**
7. Check Lambda logs to verify it was processed

### Option B: Test with mosquitto_pub

```bash
cd iot-certificates/

mosquitto_pub \
  --cafile AmazonRootCA1.pem \
  --cert device-certificate.pem.crt \
  --key private.pem.key \
  -h YOUR_IOT_ENDPOINT \
  -p 8883 \
  -t sensors/device123 \
  -m '{"temperature":23.5,"humidity":45,"occupied":true}'
```

Replace `YOUR_IOT_ENDPOINT` with your actual endpoint.

### Option C: Test with Python Simulator

1. Edit `scripts/example-iot-device.py`:
   - Update `IOT_ENDPOINT` with your endpoint
   - Update `THING_NAME` (default: `sensor-device-001`)
   - Update `DEVICE_ID` (e.g., `restroom_unit_1`)

2. Install dependencies:
   ```bash
   pip install paho-mqtt
   ```

3. Run the simulator:
   ```bash
   python3 scripts/example-iot-device.py
   ```

4. The script will publish sensor data every 30 seconds

## Step 4: Verify Data in Database

Check if messages are being stored in PostgreSQL:

```bash
# For local development
docker compose exec postgres psql -U iotuser -d iotdb -c 'SELECT * FROM sensor_data ORDER BY id DESC LIMIT 5;'

# For production (via AWS RDS)
# Connect using your preferred PostgreSQL client with RDS credentials
```

## MQTT Topic Structure

All topics must match the pattern: `sensors/#`

Recommended structure:
```
sensors/{device_id}/{metric_type}
```

Examples:
- `sensors/restroom1/occupancy` - Occupancy status
- `sensors/restroom1/environment` - Temperature, humidity
- `sensors/restroom2/status` - Device health
- `sensors/device123/alert` - Alerts/notifications

## Message Payload Format

Send JSON payloads with at least these fields:

```json
{
  "device_id": "restroom_unit_1",
  "timestamp": "2024-01-15T10:30:00Z",
  "occupied": true,
  "temperature": 23.5,
  "humidity": 45
}
```

Additional fields are preserved and stored as JSONB in PostgreSQL.

## Monitoring

### Check Lambda Execution

```bash
# View Lambda logs
aws logs tail /aws/lambda/iot_ts_handler --follow

# Check Lambda metrics
cd infra/
terraform output lambda_name
# Then check in CloudWatch Console
```

### Check IoT Core Metrics

In AWS Console:
1. Go to IoT Core → Message routing → Rules
2. Click on `iot_to_lambda`
3. View metrics tab for message counts and errors

### Check IoT Rule Status

```bash
aws iot get-topic-rule --rule-name iot_to_lambda
```

## Troubleshooting

### ❌ "Connection refused" or "Connection timeout"

**Fix:**
- Verify IoT endpoint is correct
- Check that port 8883 is not blocked by firewall
- Ensure device time is accurate (within 15 minutes of actual time)

### ❌ "Certificate verify failed"

**Fix:**
- Ensure you have all three certificate files:
  - Root CA (`AmazonRootCA1.pem`)
  - Device certificate (`.pem.crt`)
  - Private key (`.pem.key`)
- Check certificate permissions: `chmod 600 private.pem.key`
- Verify certificate is active in AWS Console

### ❌ "Not authorized"

**Fix:**
- Ensure IoT policy allows:
  - `iot:Connect` for your Thing
  - `iot:Publish` to `sensors/*` topics
- Verify certificate is attached to Thing
- Verify policy is attached to certificate

### ❌ Messages published but Lambda not invoked

**Fix:**
- Check topic matches pattern `sensors/#`
- Verify Topic Rule is enabled
- Check Lambda has permission for IoT to invoke it
- Review CloudWatch Logs for IoT Core errors

### ❌ Lambda invoked but data not in database

**Fix:**
- Check Lambda CloudWatch logs for errors
- Verify Lambda has VPC access
- Verify database table exists
- Check RDS security group allows Lambda access

## Next Steps

1. **Add More Devices:**
   - See `infra/IOT_SETUP.md` for instructions on adding more Things

2. **Implement Device Code:**
   - Use `scripts/example-iot-device.py` as a template
   - Adapt for your hardware platform (ESP32, Raspberry Pi, etc.)

3. **Set Up Bidirectional Communication:**
   - Subscribe to command topics
   - Implement device shadows for state management

4. **Add Device Fleet Management:**
   - Use AWS IoT Device Management
   - Implement OTA firmware updates
   - Set up fleet metrics and alarms

## Useful Commands Reference

```bash
# Get IoT endpoint
terraform output iot_endpoint

# Get Thing name
terraform output iot_thing_name

# List all certificates
aws iot list-certificates

# Describe certificate
aws iot describe-certificate --certificate-id CERT_ID

# List all Things
aws iot list-things

# Check Topic Rule
aws iot get-topic-rule --rule-name iot_to_lambda

# View Lambda logs
aws logs tail /aws/lambda/iot_ts_handler --follow

# Test publish via AWS CLI
aws iot-data publish \
  --topic sensors/test \
  --payload '{"test":true}' \
  --cli-binary-format raw-in-base64-out
```

## Security Checklist

- [ ] Certificates stored securely (not in version control)
- [ ] Private keys have restrictive permissions (600)
- [ ] IoT Policy follows least-privilege principle
- [ ] CloudWatch Logs enabled for audit trail
- [ ] Certificate rotation plan in place
- [ ] Devices use unique client IDs (Thing Names)
- [ ] TLS/SSL verification enabled (not `tls_insecure_set`)

## Resources

- 📖 [Detailed Setup Guide](infra/IOT_SETUP.md)
- 📖 [Architecture Documentation](infra/ARCHITECTURE.md)
- 🔗 [AWS IoT Core Documentation](https://docs.aws.amazon.com/iot/)
- 🔗 [MQTT Protocol Specification](https://mqtt.org/)
- 🐍 [Paho MQTT Python Client](https://pypi.org/project/paho-mqtt/)

---

**Need Help?** Check the detailed documentation in `infra/IOT_SETUP.md`
