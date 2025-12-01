# AWS IoT Project - Deployment Checklist

## Pre-Deployment Checklist

### Prerequisites
- [ ] AWS CLI installed and configured
- [ ] Terraform installed (v1.0+)
- [ ] AWS account with appropriate permissions
- [ ] AWS region selected (default: us-east-1)

### Validate Setup
```bash
cd infra/
./pre-deploy.sh
```

---

## Step-by-Step Deployment Guide

### Step 1: Create RDS Credentials Secret ⚠️ REQUIRED

**Option A: Interactive Script (Recommended)**
```bash
cd infra/
./setup-secrets.sh
```

**Option B: Manual AWS CLI**
```bash
aws secretsmanager create-secret \
  --name rds_credentials \
  --secret-string '{"username":"iot_master","password":"YOUR_SECURE_PASSWORD"}'
```

✅ Verification:
```bash
aws secretsmanager describe-secret --secret-id rds_credentials
```

---

### Step 2: Initialize Terraform

```bash
cd infra/
terraform init
```

Expected output:
- Downloads AWS provider
- Initializes backend
- Creates `.terraform/` directory

---

### Step 3: Create Lambda Package (if needed)

If `lambda.zip` doesn't exist:

```bash
cd lambda/
# Build your Lambda function
npm install
npm run build
# Or create a simple placeholder
echo 'exports.handler = async (event) => { console.log(event); return { statusCode: 200 }; };' > index.js
zip -r ../infra/lambda.zip index.js node_modules/
cd ../infra/
```

---

### Step 4: Review Terraform Plan

```bash
terraform plan
```

Review the resources to be created:
- [ ] VPC with public/private subnets
- [ ] NAT Gateway and Internet Gateway
- [ ] RDS PostgreSQL instance and proxy
- [ ] Lambda function (iot_handler)
- [ ] ECS Fargate service
- [ ] IoT Core resources (Thing, Certificate, Policy)
- [ ] IAM roles and policies
- [ ] Security groups
- [ ] ECR repository

Expected: **No errors**, only resource creation messages

---

### Step 5: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted.

⏱️ Estimated time: 10-15 minutes

Key resources that take time:
- RDS instance: ~5-8 minutes
- NAT Gateway: ~2-3 minutes
- RDS Proxy: ~2-3 minutes

---

### Step 6: Extract IoT Certificates

After successful deployment:

```bash
cd ..  # Back to project root
./scripts/save-iot-certs.sh
```

This creates `iot-certificates/` directory with:
- [ ] device-certificate.pem.crt
- [ ] private.pem.key
- [ ] public.pem.key
- [ ] AmazonRootCA1.pem
- [ ] connection-info.txt

⚠️ **IMPORTANT**: These files contain secrets! Never commit to Git.

---

### Step 7: Get Important Outputs

```bash
cd infra/

# IoT Core endpoint
terraform output iot_endpoint

# RDS Proxy endpoint (for backend)
terraform output rds_proxy_endpoint

# Lambda function name
terraform output lambda_name

# ECR repository URL
terraform output ecr_repository_uri

# Thing name
terraform output iot_thing_name
```

Save these values - you'll need them for configuration.

---

## Post-Deployment Testing

### Test 1: IoT Message via AWS Console

1. Go to [AWS IoT Console](https://console.aws.amazon.com/iot/)
2. Navigate to **Test** → **MQTT test client**
3. Click **Publish to a topic**
4. Topic: `sensors/test`
5. Message payload:
   ```json
   {
     "device_id": "test-device",
     "temperature": 23.5,
     "humidity": 45,
     "occupied": true,
     "timestamp": "2024-01-15T10:30:00Z"
   }
   ```
6. Click **Publish**

✅ Success indicators:
- [ ] No errors in console
- [ ] Lambda invoked (check CloudWatch Logs)
- [ ] Data appears in PostgreSQL

---

### Test 2: Check Lambda Execution

```bash
aws logs tail /aws/lambda/iot_ts_handler --follow
```

You should see log entries for the message processing.

---

### Test 3: Verify Database Connection

**Local Development:**
```bash
docker compose exec postgres psql -U iotuser -d iotdb \
  -c 'SELECT * FROM sensor_data ORDER BY id DESC LIMIT 5;'
```

**Production (via RDS):**
Use your PostgreSQL client with the RDS proxy endpoint and credentials.

---

### Test 4: IoT Device Simulator

```bash
# Edit the script first with your IoT endpoint
cd scripts/
# Update IOT_ENDPOINT in example-iot-device.py
python3 example-iot-device.py
```

✅ Success indicators:
- [ ] Connection successful
- [ ] Messages published
- [ ] Lambda processes messages
- [ ] Data appears in database

---

## Backend Deployment (ECS)

### Push Docker Image to ECR

```bash
# Get ECR URL
cd infra/
ECR_URL=$(terraform output -raw ecr_repository_uri)
AWS_REGION=$(aws configure get region)

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_URL

# Build and push
cd ../backend/
docker build -t backend .
docker tag backend:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

### Update ECS Service

```bash
cd ../infra/
terraform apply  # Updates ECS to use new image
```

Or force new deployment:
```bash
aws ecs update-service \
  --cluster iot-cluster \
  --service backend-service \
  --force-new-deployment
```

---

## Verification Checklist

### Infrastructure
- [ ] VPC created with correct CIDR
- [ ] NAT Gateway operational
- [ ] RDS instance running
- [ ] RDS Proxy accessible
- [ ] Lambda function deployed
- [ ] ECS service running (desired count: 1)

### IoT Core
- [ ] IoT Thing created (`sensor-device-001`)
- [ ] Certificate active
- [ ] Policy attached to certificate
- [ ] Certificate attached to Thing
- [ ] Topic Rule enabled (`iot_to_lambda`)

### Security
- [ ] IAM roles created with correct permissions
- [ ] Security groups properly configured
- [ ] RDS credentials stored in Secrets Manager
- [ ] IoT certificates saved locally (NOT in Git)

### Testing
- [ ] MQTT message published successfully
- [ ] Lambda invoked by IoT Core
- [ ] Data stored in PostgreSQL
- [ ] CloudWatch Logs showing activity
- [ ] No errors in any service

---

## Monitoring Setup

### Enable CloudWatch Logs for IoT Core

```bash
# Create IAM role for IoT logging (if not automated)
aws iot set-v2-logging-options \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/IoTLoggingRole \
  --default-log-level INFO
```

### View Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/iot_ts_handler --follow

# IoT Core logs
aws logs tail AWSIotLogsV2 --follow

# ECS task logs
aws logs tail /ecs/backend-service --follow
```

---

## Troubleshooting Common Issues

### Issue: Terraform apply fails with "secret not found"
**Fix:** Create RDS credentials secret first
```bash
cd infra/
./setup-secrets.sh
```

### Issue: Lambda can't connect to database
**Check:**
- [ ] Lambda in correct VPC subnets
- [ ] Security group allows Lambda → RDS
- [ ] RDS proxy endpoint correct
- [ ] Secrets Manager accessible from Lambda

### Issue: IoT messages not triggering Lambda
**Check:**
- [ ] Topic matches pattern `sensors/#`
- [ ] Topic Rule enabled
- [ ] Lambda permission exists
- [ ] Certificate active and attached

### Issue: ECS task keeps restarting
**Check:**
- [ ] Docker image pushed to ECR
- [ ] Task role has ECR pull permissions
- [ ] Environment variables correct
- [ ] Health check configured properly

---

## Scaling Considerations

### Add More IoT Devices

Edit `infra/iot.tf` and duplicate resources:
```hcl
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
# ... attach policy and certificate
```

Then:
```bash
terraform apply
./scripts/save-iot-certs.sh  # Extract new certificates
```

### Increase ECS Tasks

Edit `infra/service.tf`:
```hcl
desired_count = 2  # Change from 1 to 2
```

Then:
```bash
terraform apply
```

---

## Cost Management

### Daily Cost Estimate
- NAT Gateway: ~$1.08/day
- RDS db.t3.micro: ~$0.37/day
- ECS Fargate (256 CPU, 512 MB): ~$0.29/day
- Lambda: <$0.01/day (low volume)
- IoT Core: Free tier (first 1M messages/month)

**Total: ~$2-3/day or $60-90/month**

### Cost Optimization Tips
- [ ] Stop environment when not in use
- [ ] Use smaller RDS instance for dev/test
- [ ] Delete NAT Gateway if not needed
- [ ] Use S3 Gateway endpoint (free)
- [ ] Monitor with AWS Cost Explorer

---

## Cleanup (Destroy Infrastructure)

⚠️ **WARNING:** This will delete all resources!

```bash
cd infra/

# Review what will be deleted
terraform plan -destroy

# Destroy all resources
terraform destroy
```

Type `yes` to confirm.

### Manual Cleanup Required

Some resources may need manual deletion:
- [ ] CloudWatch Log Groups (retained by default)
- [ ] Secrets Manager secret (if you want to delete it)
- [ ] ECR images (if repository deletion fails)

```bash
# Delete secret
aws secretsmanager delete-secret \
  --secret-id rds_credentials \
  --force-delete-without-recovery

# Empty ECR repository
aws ecr batch-delete-image \
  --repository-name backend-app \
  --image-ids imageTag=latest
```

---

## Quick Reference Commands

```bash
# Deploy
cd infra/ && terraform apply

# Get IoT endpoint
terraform output iot_endpoint

# Extract certificates
cd .. && ./scripts/save-iot-certs.sh

# Test MQTT
mosquitto_pub \
  --cafile iot-certificates/AmazonRootCA1.pem \
  --cert iot-certificates/device-certificate.pem.crt \
  --key iot-certificates/private.pem.key \
  -h $(cd infra && terraform output -raw iot_endpoint) \
  -p 8883 \
  -t sensors/test \
  -m '{"test":true}'

# View Lambda logs
aws logs tail /aws/lambda/iot_ts_handler --follow

# Update ECS service
aws ecs update-service \
  --cluster iot-cluster \
  --service backend-service \
  --force-new-deployment

# Destroy everything
cd infra/ && terraform destroy
```

---

## Documentation Links

- **Quick Start:** `IOT_QUICKSTART.md`
- **Terraform Fixes:** `TERRAFORM_FIXES.md`
- **IoT Setup Guide:** `infra/IOT_SETUP.md`
- **Architecture:** `infra/ARCHITECTURE.md`
- **Main README:** `readme.md`

---

## Support Checklist

Before asking for help, verify:
- [ ] Ran `./infra/pre-deploy.sh` successfully
- [ ] Created RDS credentials secret
- [ ] Terraform plan shows no errors
- [ ] Checked CloudWatch Logs for errors
- [ ] Reviewed security group rules
- [ ] Verified IAM permissions
- [ ] Checked AWS service quotas

---

**🎉 Congratulations!** Your AWS IoT infrastructure is deployed and ready to use!