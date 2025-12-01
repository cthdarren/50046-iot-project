# Monitoring Quick Reference Card

## 🚀 Most Important Commands

### Watch Lambda Logs in Real-Time (START HERE!)
```bash
aws logs tail /aws/lambda/iot_ts_handler --follow
```
👆 **Use this to see IoT messages being processed live!**

### Check All Services at Once
```bash
./scripts/check-all-services.sh
```

---

## 📊 Individual Service Status

### RDS Database
```bash
# Check status
aws rds describe-db-instances --db-instance-identifier iot-postgres-db \
  --query 'DBInstances[0].DBInstanceStatus' --output text

# Expected: "available"
```

### RDS Proxy
```bash
# Check status
aws rds describe-db-proxies --db-proxy-name iot-rds-proxy \
  --query 'DBProxies[0].Status' --output text

# Expected: "available"
```

### Lambda Function
```bash
# Check status
aws lambda get-function --function-name iot_ts_handler \
  --query 'Configuration.State' --output text

# Expected: "Active"
```

### ECS Service
```bash
# Check status and task count
aws ecs describe-services --cluster iot-cluster --services backend-service \
  --query 'services[0].[status,desiredCount,runningCount]' --output table

# Expected: ACTIVE, 1, 1
```

### IoT Thing & Certificate
```bash
# Check Thing
aws iot describe-thing --thing-name sensor-device-001

# Check Topic Rule
aws iot get-topic-rule --rule-name iot_to_lambda \
  --query 'rule.ruleDisabled' --output text

# Expected: "false" (rule is enabled)
```

---

## 📝 View Logs

### Lambda Logs (MOST USEFUL!)
```bash
# Last hour
aws logs tail /aws/lambda/iot_ts_handler --since 1h

# Live stream
aws logs tail /aws/lambda/iot_ts_handler --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/iot_ts_handler \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000
```

### RDS Logs
```bash
# PostgreSQL logs (if CloudWatch enabled)
aws logs tail /aws/rds/instance/iot-postgres-db/postgresql --follow
```

### ECS Logs
```bash
# Container logs
aws logs tail /ecs/backend-service --follow
```

### IoT Core Logs
```bash
# Requires logging to be enabled first
aws logs tail AWSIotLogsV2 --follow
```

---

## 🧪 Testing Commands

### Test IoT Message Flow
```bash
# Terminal 1: Watch Lambda logs
aws logs tail /aws/lambda/iot_ts_handler --follow

# Terminal 2: Publish test message from IoT Console
# Go to: https://console.aws.amazon.com/iot/
# Test → MQTT test client
# Topic: sensors/test
# Message: {"temperature":23.5,"humidity":45,"occupied":true}
```

### Test with MQTT Client
```bash
cd iot-certificates/
mosquitto_pub \
  --cafile AmazonRootCA1.pem \
  --cert device-certificate.pem.crt \
  --key private.pem.key \
  -h YOUR_IOT_ENDPOINT \
  -p 8883 \
  -t sensors/test \
  -m '{"temperature":23.5,"humidity":45,"occupied":true}'
```

### Test Lambda Directly
```bash
aws lambda invoke \
  --function-name iot_ts_handler \
  --payload '{"test":true,"temperature":23.5}' \
  response.json && cat response.json
```

---

## 🔍 Check Database Data

### Connect to Database
```bash
# Get proxy endpoint
PROXY_ENDPOINT=$(cd infra && terraform output -raw rds_proxy_endpoint)

# Connect
psql -h $PROXY_ENDPOINT -U iot_master -d iotdb
```

### Quick Queries
```bash
# Count sensor data
psql -h $PROXY_ENDPOINT -U iot_master -d iotdb \
  -c "SELECT count(*) FROM sensor_data;"

# View latest data
psql -h $PROXY_ENDPOINT -U iot_master -d iotdb \
  -c "SELECT * FROM sensor_data ORDER BY created_at DESC LIMIT 10;"
```

---

## 📈 CloudWatch Metrics

### Lambda Invocations (Last Hour)
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=iot_ts_handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Lambda Errors
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=iot_ts_handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### RDS Connections
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=iot-postgres-db \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

---

## 🐛 Troubleshooting

### Lambda Not Being Invoked?
```bash
# 1. Check Topic Rule
aws iot get-topic-rule --rule-name iot_to_lambda

# 2. Check Lambda permission
aws lambda get-policy --function-name iot_ts_handler

# 3. Check Lambda logs
aws logs tail /aws/lambda/iot_ts_handler --since 1h
```

### Lambda Errors?
```bash
# 1. Check VPC configuration
aws lambda get-function-configuration --function-name iot_ts_handler \
  --query 'VpcConfig'

# 2. Check environment variables
aws lambda get-function-configuration --function-name iot_ts_handler \
  --query 'Environment'

# 3. Search error logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/iot_ts_handler \
  --filter-pattern "ERROR"
```

### Can't Connect to Database?
```bash
# 1. Check RDS status
aws rds describe-db-instances --db-instance-identifier iot-postgres-db

# 2. Check RDS Proxy status
aws rds describe-db-proxies --db-proxy-name iot-rds-proxy

# 3. Check security groups
aws ec2 describe-security-groups --group-names rds_sg lambda_sg
```

### ECS Task Not Running?
```bash
# 1. Check service
aws ecs describe-services --cluster iot-cluster --services backend-service

# 2. List tasks
aws ecs list-tasks --cluster iot-cluster --service-name backend-service

# 3. Check task logs
aws logs tail /ecs/backend-service --since 30m
```

---

## 🌐 Web Console Links

### CloudWatch Console
https://console.aws.amazon.com/cloudwatch/

### IoT Core MQTT Test Client
https://console.aws.amazon.com/iot/ → Test → MQTT test client

### Lambda Console
https://console.aws.amazon.com/lambda/

### RDS Console
https://console.aws.amazon.com/rds/

### ECS Console
https://console.aws.amazon.com/ecs/

---

## 📋 Health Check Script

Run this to check all services:
```bash
./scripts/check-all-services.sh
```

Output shows:
- ✓ Green = Healthy
- ✗ Red = Problem
- ⚠ Yellow = Warning

---

## 🎯 Common Monitoring Workflows

### Daily Health Check
```bash
# 1. Run automated check
./scripts/check-all-services.sh

# 2. Check Lambda invocations
aws logs tail /aws/lambda/iot_ts_handler --since 24h | grep -c "START"

# 3. Check for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/iot_ts_handler \
  --filter-pattern "ERROR" \
  --start-time $(date -d '24 hours ago' +%s)000
```

### Debugging New IoT Device
```bash
# Terminal 1: Watch logs
aws logs tail /aws/lambda/iot_ts_handler --follow

# Terminal 2: Watch IoT Core (if logging enabled)
aws logs tail AWSIotLogsV2 --follow

# Terminal 3: Test device connection
# (device publishes to sensors/device_id)
```

### Performance Monitoring
```bash
# Lambda duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=iot_ts_handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# RDS CPU
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=iot-postgres-db \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

---

## 💡 Pro Tips

1. **Always start with Lambda logs** - They show you everything happening
2. **Use `--follow` flag** - Real-time monitoring is best for debugging
3. **Check CloudWatch Console** - Visual dashboards are easier to read
4. **Set up alarms** - Get notified of issues automatically
5. **Save common queries** - Create aliases in your `.bashrc`

### Useful Aliases
```bash
# Add to ~/.bashrc or ~/.zshrc
alias iot-logs='aws logs tail /aws/lambda/iot_ts_handler --follow'
alias iot-status='./scripts/check-all-services.sh'
alias iot-db='psql -h $(cd infra && terraform output -raw rds_proxy_endpoint) -U iot_master -d iotdb'
```

---

## 📚 Full Documentation

For detailed information, see:
- **Full monitoring guide:** `MONITORING_GUIDE.md`
- **Deployment guide:** `DEPLOYMENT_CHECKLIST.md`
- **IoT setup:** `IOT_QUICKSTART.md`
- **Architecture:** `infra/ARCHITECTURE.md`

---

**Remember:** The most important command is:
```bash
aws logs tail /aws/lambda/iot_ts_handler --follow
```

This shows you every IoT message being processed in real-time! 🎉