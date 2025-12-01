# AWS IoT Project - Monitoring & Logging Guide

Complete guide for checking service statuses, viewing logs, and troubleshooting your AWS IoT infrastructure.

---

## Quick Status Check Commands

### All Services at a Glance

```bash
# Check all core services
cd infra/

echo "=== RDS Instance ==="
aws rds describe-db-instances --db-instance-identifier iot-postgres-db --query 'DBInstances[0].DBInstanceStatus' --output text

echo "=== RDS Proxy ==="
aws rds describe-db-proxies --db-proxy-name iot-rds-proxy --query 'DBProxies[0].Status' --output text

echo "=== Lambda Function ==="
aws lambda get-function --function-name iot_ts_handler --query 'Configuration.State' --output text

echo "=== ECS Service ==="
aws ecs describe-services --cluster iot-cluster --services backend-service --query 'services[0].status' --output text

echo "=== IoT Thing ==="
aws iot describe-thing --thing-name sensor-device-001 --query 'thingName' --output text

echo "=== IoT Topic Rule ==="
aws iot get-topic-rule --rule-name iot_to_lambda --query 'rule.ruleDisabled' --output text
```

---

## 1. RDS PostgreSQL Database

### Check Database Status

```bash
# Basic status
aws rds describe-db-instances \
  --db-instance-identifier iot-postgres-db \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text

# Detailed information
aws rds describe-db-instances \
  --db-instance-identifier iot-postgres-db \
  --query 'DBInstances[0].[DBInstanceIdentifier,DBInstanceStatus,Endpoint.Address,EngineVersion]' \
  --output table
```

**Expected status:** `available`

**Other possible statuses:**
- `creating` - Database is being created (takes 5-10 minutes)
- `backing-up` - Automated backup in progress
- `modifying` - Configuration change in progress
- `storage-optimization` - Storage being optimized

### View RDS Logs

```bash
# List available log files
aws rds describe-db-log-files \
  --db-instance-identifier iot-postgres-db

# Download and view latest PostgreSQL log
aws rds download-db-log-file-portion \
  --db-instance-identifier iot-postgres-db \
  --log-file-name error/postgresql.log.2024-12-01-00 \
  --output text

# Stream logs in real-time (requires CloudWatch Logs enabled)
aws logs tail /aws/rds/instance/iot-postgres-db/postgresql --follow
```

### Check Database Connections

```bash
# Connect to database (requires network access)
psql -h $(cd infra && terraform output -raw rds_proxy_endpoint) \
     -U iot_master \
     -d iotdb \
     -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
```

---

## 2. RDS Proxy

### Check Proxy Status

```bash
# Basic status
aws rds describe-db-proxies \
  --db-proxy-name iot-rds-proxy \
  --query 'DBProxies[0].Status' \
  --output text

# Detailed information
aws rds describe-db-proxies \
  --db-proxy-name iot-rds-proxy \
  --query 'DBProxies[0].[DBProxyName,Status,Endpoint,VpcId]' \
  --output table
```

**Expected status:** `available`

### Check Proxy Targets

```bash
# List targets attached to proxy
aws rds describe-db-proxy-targets \
  --db-proxy-name iot-rds-proxy

# Check target health
aws rds describe-db-proxy-targets \
  --db-proxy-name iot-rds-proxy \
  --query 'Targets[*].[TargetArn,TargetHealth.State,TargetHealth.Description]' \
  --output table
```

**Expected target state:** `AVAILABLE`

### View Proxy Metrics

```bash
# CloudWatch metrics for proxy
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBProxyName,Value=iot-rds-proxy \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --output table
```

---

## 3. Lambda Function

### Check Lambda Status

```bash
# Function configuration
aws lambda get-function \
  --function-name iot_ts_handler \
  --query 'Configuration.[FunctionName,State,LastUpdateStatus,Runtime]' \
  --output table

# Function state details
aws lambda get-function \
  --function-name iot_ts_handler \
  --query 'Configuration.State' \
  --output text
```

**Expected state:** `Active`
**Expected update status:** `Successful`

### View Lambda Logs (MOST IMPORTANT!)

```bash
# View recent logs
aws logs tail /aws/lambda/iot_ts_handler --since 1h

# Follow logs in real-time (best for testing)
aws logs tail /aws/lambda/iot_ts_handler --follow

# View logs from specific time
aws logs tail /aws/lambda/iot_ts_handler --since 2024-12-01T10:00:00

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/iot_ts_handler \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# Get latest 20 log events
aws logs tail /aws/lambda/iot_ts_handler --since 30m | head -20
```

### Check Lambda Invocations

```bash
# Recent invocations (via CloudWatch Metrics)
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=iot_ts_handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --output table

# Error rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=iot_ts_handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --output table
```

### Test Lambda Manually

```bash
# Invoke Lambda with test event
aws lambda invoke \
  --function-name iot_ts_handler \
  --payload '{"test": true, "temperature": 23.5}' \
  response.json

# View response
cat response.json
```

---

## 4. ECS Fargate Service

### Check ECS Service Status

```bash
# Service status
aws ecs describe-services \
  --cluster iot-cluster \
  --services backend-service \
  --query 'services[0].[serviceName,status,desiredCount,runningCount,pendingCount]' \
  --output table

# Detailed service info
aws ecs describe-services \
  --cluster iot-cluster \
  --services backend-service
```

**Expected status:** `ACTIVE`
**Expected counts:** desiredCount = runningCount = 1

### Check ECS Tasks

```bash
# List running tasks
aws ecs list-tasks \
  --cluster iot-cluster \
  --service-name backend-service

# Get task details
TASK_ARN=$(aws ecs list-tasks --cluster iot-cluster --service-name backend-service --query 'taskArns[0]' --output text)

aws ecs describe-tasks \
  --cluster iot-cluster \
  --tasks $TASK_ARN \
  --query 'tasks[0].[taskArn,lastStatus,healthStatus,containers[0].name]' \
  --output table
```

**Expected lastStatus:** `RUNNING`

### View ECS Logs

```bash
# View service logs (if CloudWatch Logs configured)
aws logs tail /ecs/backend-service --follow

# If you need to find the log group name
aws logs describe-log-groups --query 'logGroups[?contains(logGroupName, `ecs`)].logGroupName'

# View specific task logs
aws logs tail /ecs/backend-service --since 1h
```

### Check ECS Task Health

```bash
# Get task ARN
TASK_ARN=$(aws ecs list-tasks --cluster iot-cluster --service-name backend-service --query 'taskArns[0]' --output text)

# Check container health
aws ecs describe-tasks \
  --cluster iot-cluster \
  --tasks $TASK_ARN \
  --query 'tasks[0].containers[*].[name,lastStatus,healthStatus,exitCode]' \
  --output table
```

---

## 5. IoT Core

### Check IoT Thing

```bash
# Thing details
aws iot describe-thing \
  --thing-name sensor-device-001

# List all things
aws iot list-things

# Check thing attributes
aws iot describe-thing \
  --thing-name sensor-device-001 \
  --query 'attributes' \
  --output table
```

### Check IoT Certificate

```bash
# Get certificate ID from Terraform output
cd infra/
CERT_ARN=$(terraform output -raw iot_certificate_arn)
CERT_ID=$(echo $CERT_ARN | cut -d'/' -f2)

# Describe certificate
aws iot describe-certificate \
  --certificate-id $CERT_ID \
  --query '[certificateId,status,certificateArn]' \
  --output table
```

**Expected status:** `ACTIVE`

### Check IoT Topic Rule

```bash
# Get rule details
aws iot get-topic-rule \
  --rule-name iot_to_lambda

# Check if rule is enabled
aws iot get-topic-rule \
  --rule-name iot_to_lambda \
  --query 'rule.ruleDisabled' \
  --output text
```

**Expected output:** `false` (rule is enabled)

### View IoT Core Metrics

```bash
# Messages published to IoT Core
aws cloudwatch get-metric-statistics \
  --namespace AWS/IoT \
  --metric-name PublishIn.Success \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --output table

# Rule execution metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/IoT \
  --metric-name RuleMessageThrottled \
  --dimensions Name=RuleName,Value=iot_to_lambda \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --output table
```

### Enable IoT Core Logging

If you need detailed IoT Core logs:

```bash
# Create logging role (if not exists)
aws iam create-role \
  --role-name IoTLoggingRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "iot.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach logging policy
aws iam attach-role-policy \
  --role-name IoTLoggingRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSIoTLogging

# Enable logging
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws iot set-v2-logging-options \
  --role-arn arn:aws:iam::$ACCOUNT_ID:role/IoTLoggingRole \
  --default-log-level INFO

# View IoT Core logs
aws logs tail AWSIotLogsV2 --follow
```

---

## 6. VPC & Networking

### Check VPC Status

```bash
# Get VPC ID
cd infra/
VPC_ID=$(terraform output -raw vpc_id 2>/dev/null || aws ec2 describe-vpcs --filters "Name=tag:Name,Values=main_vpc" --query 'Vpcs[0].VpcId' --output text)

# VPC details
aws ec2 describe-vpcs \
  --vpc-ids $VPC_ID \
  --query 'Vpcs[0].[VpcId,CidrBlock,State]' \
  --output table
```

### Check NAT Gateway

```bash
# NAT Gateway status
aws ec2 describe-nat-gateways \
  --filter "Name=vpc-id,Values=$VPC_ID" \
  --query 'NatGateways[*].[NatGatewayId,State,SubnetId]' \
  --output table
```

**Expected state:** `available`

### Check Security Groups

```bash
# Lambda security group
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=lambda_sg" \
  --query 'SecurityGroups[0].[GroupId,GroupName,Description]' \
  --output table

# RDS security group
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=rds_sg" \
  --query 'SecurityGroups[0].[GroupId,GroupName,Description]' \
  --output table
```

---

## 7. CloudWatch Dashboard (Web Console)

### Access CloudWatch Console

1. Go to: https://console.aws.amazon.com/cloudwatch/
2. Select your region (top-right)

### Key Metrics to Monitor

#### Lambda Metrics
- **Invocations** - How many times Lambda was called
- **Duration** - How long each invocation took
- **Errors** - Failed invocations
- **Throttles** - Rejected due to concurrency limits

#### RDS Metrics
- **DatabaseConnections** - Active connections
- **CPUUtilization** - Database CPU usage
- **FreeableMemory** - Available memory
- **ReadLatency/WriteLatency** - Database performance

#### IoT Core Metrics
- **PublishIn.Success** - Messages received
- **RulesExecuted** - How many times your rule ran
- **RuleNotFound** - Messages that didn't match any rule

---

## 8. Common Monitoring Scenarios

### Scenario 1: Testing IoT Message Flow

```bash
# Terminal 1: Watch Lambda logs
aws logs tail /aws/lambda/iot_ts_handler --follow

# Terminal 2: Publish test message (from IoT certificates directory)
cd iot-certificates/
mosquitto_pub \
  --cafile AmazonRootCA1.pem \
  --cert device-certificate.pem.crt \
  --key private.pem.key \
  -h $(cd ../infra && terraform output -raw iot_endpoint) \
  -p 8883 \
  -t sensors/test \
  -m '{"temperature":23.5,"humidity":45,"occupied":true}'

# You should see the Lambda log in Terminal 1
```

### Scenario 2: Debugging Lambda Errors

```bash
# 1. Check recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/iot_ts_handler \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# 2. Check Lambda configuration
aws lambda get-function-configuration \
  --function-name iot_ts_handler

# 3. Check Lambda has VPC access
aws lambda get-function-configuration \
  --function-name iot_ts_handler \
  --query 'VpcConfig' \
  --output json

# 4. Test database connection from Lambda
aws lambda invoke \
  --function-name iot_ts_handler \
  --payload '{"test_db": true}' \
  response.json && cat response.json
```

### Scenario 3: Checking Database Data

```bash
# Connect to database via RDS Proxy
PROXY_ENDPOINT=$(cd infra && terraform output -raw rds_proxy_endpoint)

# Connect with psql
psql -h $PROXY_ENDPOINT -U iot_master -d iotdb

# Or run a quick query
psql -h $PROXY_ENDPOINT -U iot_master -d iotdb -c "SELECT count(*) FROM sensor_data;"

# View latest sensor data
psql -h $PROXY_ENDPOINT -U iot_master -d iotdb -c "SELECT * FROM sensor_data ORDER BY created_at DESC LIMIT 10;"
```

### Scenario 4: Monitoring ECS Task

```bash
# Get task ID
TASK_ARN=$(aws ecs list-tasks --cluster iot-cluster --service-name backend-service --query 'taskArns[0]' --output text)

# Watch task status
watch -n 5 "aws ecs describe-tasks --cluster iot-cluster --tasks $TASK_ARN --query 'tasks[0].[lastStatus,healthStatus,containers[0].lastStatus]' --output table"

# View task logs
aws logs tail /ecs/backend-service --follow
```

---

## 9. Automated Monitoring Script

Save this as `scripts/check-all-services.sh`:

```bash
#!/bin/bash

echo "======================================"
echo "AWS IoT Infrastructure Status Check"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_status() {
    if [ "$1" == "$2" ]; then
        echo -e "${GREEN}✓${NC} $3: $1"
    else
        echo -e "${RED}✗${NC} $3: $1 (expected: $2)"
    fi
}

# RDS Instance
echo "1. RDS PostgreSQL Database"
RDS_STATUS=$(aws rds describe-db-instances --db-instance-identifier iot-postgres-db --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null)
check_status "$RDS_STATUS" "available" "Status"
echo ""

# RDS Proxy
echo "2. RDS Proxy"
PROXY_STATUS=$(aws rds describe-db-proxies --db-proxy-name iot-rds-proxy --query 'DBProxies[0].Status' --output text 2>/dev/null)
check_status "$PROXY_STATUS" "available" "Status"
echo ""

# Lambda
echo "3. Lambda Function"
LAMBDA_STATE=$(aws lambda get-function --function-name iot_ts_handler --query 'Configuration.State' --output text 2>/dev/null)
check_status "$LAMBDA_STATE" "Active" "State"

LAMBDA_INVOCATIONS=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=iot_ts_handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --query 'Datapoints[0].Sum' \
  --output text 2>/dev/null)
echo -e "  Invocations (last hour): ${LAMBDA_INVOCATIONS:-0}"
echo ""

# ECS Service
echo "4. ECS Fargate Service"
ECS_STATUS=$(aws ecs describe-services --cluster iot-cluster --services backend-service --query 'services[0].status' --output text 2>/dev/null)
check_status "$ECS_STATUS" "ACTIVE" "Status"

ECS_RUNNING=$(aws ecs describe-services --cluster iot-cluster --services backend-service --query 'services[0].runningCount' --output text 2>/dev/null)
echo -e "  Running tasks: $ECS_RUNNING"
echo ""

# IoT Thing
echo "5. IoT Core"
IOT_THING=$(aws iot describe-thing --thing-name sensor-device-001 --query 'thingName' --output text 2>/dev/null)
check_status "$IOT_THING" "sensor-device-001" "Thing"

IOT_RULE=$(aws iot get-topic-rule --rule-name iot_to_lambda --query 'rule.ruleDisabled' --output text 2>/dev/null)
if [ "$IOT_RULE" == "False" ]; then
    echo -e "${GREEN}✓${NC} Topic Rule: Enabled"
else
    echo -e "${RED}✗${NC} Topic Rule: Disabled"
fi
echo ""

echo "======================================"
echo "Status check complete!"
echo "======================================"
```

Make it executable:
```bash
chmod +x scripts/check-all-services.sh
./scripts/check-all-services.sh
```

---

## 10. Troubleshooting Checklist

### Lambda Not Being Invoked?

- [ ] Check IoT Topic Rule is enabled: `aws iot get-topic-rule --rule-name iot_to_lambda`
- [ ] Verify topic pattern matches: Rule uses `sensors/#`, your topic should be `sensors/something`
- [ ] Check Lambda logs for errors: `aws logs tail /aws/lambda/iot_ts_handler --follow`
- [ ] Verify Lambda permission: `aws lambda get-policy --function-name iot_ts_handler`

### Lambda Timing Out or Failing?

- [ ] Check Lambda is in correct VPC subnets
- [ ] Verify security groups allow Lambda → RDS
- [ ] Check RDS Proxy is available
- [ ] Verify Secrets Manager access
- [ ] Check Lambda timeout setting (should be > 30 seconds)

### Can't Connect to Database?

- [ ] RDS instance status: `available`
- [ ] RDS Proxy status: `available`
- [ ] Security group allows connections
- [ ] Correct credentials in Secrets Manager
- [ ] Network connectivity from Lambda to RDS

### IoT Messages Not Arriving?

- [ ] Certificate is active
- [ ] Device is publishing to correct topic
- [ ] Topic Rule is enabled
- [ ] Check IoT Core logs (if enabled)
- [ ] Verify MQTT connection successful

---

## 11. Setting Up Alarms

Create CloudWatch alarms for critical issues:

```bash
# Lambda errors alarm
aws cloudwatch put-metric-alarm \
  --alarm-name iot-lambda-errors \
  --alarm-description "Alert when Lambda has errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=iot_ts_handler

# RDS high CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name iot-rds-high-cpu \
  --alarm-description "Alert when RDS CPU is high" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=DBInstanceIdentifier,Value=iot-postgres-db
```

---

## 12. Quick Reference

| Service | Status Command | Logs Command |
|---------|---------------|--------------|
| **RDS** | `aws rds describe-db-instances --db-instance-identifier iot-postgres-db` | `aws logs tail /aws/rds/instance/iot-postgres-db/postgresql --follow` |
| **Lambda** | `aws lambda get-function --function-name iot_ts_handler` | `aws logs tail /aws/lambda/iot_ts_handler --follow` |
| **ECS** | `aws ecs describe-services --cluster iot-cluster --services backend-service` | `aws logs tail /ecs/backend-service --follow` |
| **IoT Thing** | `aws iot describe-thing --thing-name sensor-device-001` | `aws logs tail AWSIotLogsV2 --follow` |

---

## Summary

✅ **Always start with:** `aws logs tail /aws/lambda/iot_ts_handler --follow` - This shows you what's happening!  
✅ **Check service health:** Use the automated script `./scripts/check-all-services.sh`  
✅ **Monitor in real-time:** Use CloudWatch Console for visual dashboards  
✅ **Debug issues:** Check logs, then status, then configurations  

**Most Important Command:**
```bash
aws logs tail /aws/lambda/iot_ts_handler --follow
```
This shows you every IoT message being processed in real-time! 🎉
