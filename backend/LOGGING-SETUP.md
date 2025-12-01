# ECS Logging Setup Guide

## Problem
When running `make logs`, you get:
```
An error occurred (ResourceNotFoundException) when calling the FilterLogEvents operation: 
The specified log group does not exist.
```

## Why This Happens
The CloudWatch log group `/ecs/iot-backend` doesn't exist yet because:
1. It's defined in Terraform but hasn't been applied yet, OR
2. The ECS task hasn't started yet (logs are created on first run)

## Quick Fix Options

### Option 1: Apply Terraform (Recommended)

This creates the log group properly with all configurations:

```bash
cd infra
terraform apply
```

This will create:
- CloudWatch log group: `/ecs/iot-backend`
- Retention policy: 7 days
- Proper IAM permissions
- Updated ECS task definition with logging enabled

### Option 2: Create Log Group Manually

If you just want to create the log group quickly:

```bash
cd backend
make create-log-group
```

Or manually:
```bash
aws logs create-log-group --log-group-name /ecs/iot-backend --region ap-southeast-1
aws logs put-retention-policy --log-group-name /ecs/iot-backend --retention-in-days 7 --region ap-southeast-1
```

### Option 3: Let ECS Create It

Deploy your service and ECS will automatically create the log group:

```bash
cd backend
make deploy
```

The log group will be created when the first task starts.

## Verify Logging Setup

### Check if log group exists

```bash
cd backend
make check-logs
```

This will show:
- ✓ If log group exists
- Recent log streams
- Instructions if it doesn't exist

### Manual verification

```bash
# List all ECS/IoT related log groups
aws logs describe-log-groups \
  --region ap-southeast-1 \
  --query 'logGroups[?contains(logGroupName, `ecs`) || contains(logGroupName, `iot`)].logGroupName'

# Check specific log group
aws logs describe-log-groups \
  --log-group-name-prefix /ecs/iot-backend \
  --region ap-southeast-1
```

## View Logs

Once the log group exists and your service is running:

```bash
cd backend
make logs
```

This will tail logs in real-time. Press `Ctrl+C` to stop.

### Alternative log viewing methods

```bash
# View last 10 minutes
aws logs tail /ecs/iot-backend --since 10m --region ap-southeast-1

# View last 100 lines
aws logs tail /ecs/iot-backend --follow --region ap-southeast-1 | tail -n 100

# Filter by pattern
aws logs tail /ecs/iot-backend --follow --filter-pattern "ERROR" --region ap-southeast-1

# View specific time range
aws logs tail /ecs/iot-backend \
  --since "2024-03-15T10:00:00" \
  --until "2024-03-15T11:00:00" \
  --region ap-southeast-1
```

## What Changed in Infrastructure

### New Files Created

1. **`infra/cloudwatch.tf`** - CloudWatch log group definitions
   ```hcl
   resource "aws_cloudwatch_log_group" "ecs_logs" {
     name              = "/ecs/iot-backend"
     retention_in_days = 7
   }
   ```

2. **Updated `infra/task_definition.tf`** - Added logging configuration
   ```json
   "logConfiguration": {
     "logDriver": "awslogs",
     "options": {
       "awslogs-group": "/ecs/iot-backend",
       "awslogs-region": "ap-southeast-1",
       "awslogs-stream-prefix": "ecs"
     }
   }
   ```

### Log Stream Naming

Logs will appear in streams named:
```
ecs/web/<task-id>
```

Where:
- `ecs` = prefix from task definition
- `web` = container name
- `<task-id>` = unique ECS task ID

Example: `ecs/web/a1b2c3d4e5f6`

## New Make Commands

```bash
make check-logs        # Check if log group exists
make create-log-group  # Create log group manually
make logs              # Tail logs in real-time
```

## Troubleshooting

### "Log group does not exist"

**Solution:**
```bash
# Option A: Apply Terraform
cd infra && terraform apply

# Option B: Create manually
cd backend && make create-log-group
```

### "No log streams found"

**Cause:** Service hasn't started yet or no logs generated

**Solution:**
```bash
# Check service status
make status

# Deploy service
make deploy

# Wait a moment for task to start, then try logs again
make logs
```

### "Access Denied" when viewing logs

**Cause:** IAM user lacks CloudWatch Logs permissions

**Solution:** Add these permissions to your IAM user/role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents"
      ],
      "Resource": "arn:aws:logs:ap-southeast-1:*:log-group:/ecs/*"
    }
  ]
}
```

### Logs are empty or missing

**Possible causes:**
1. Application isn't writing to stdout/stderr
2. Task crashed before logging
3. Wrong log group name

**Debug:**
```bash
# Check task definition
aws ecs describe-task-definition \
  --task-definition iot-backend \
  --region ap-southeast-1 \
  --query 'taskDefinition.containerDefinitions[0].logConfiguration'

# Check service events
make status

# Check recent tasks
aws ecs list-tasks \
  --cluster my-cluster \
  --service-name iot-backend-service \
  --region ap-southeast-1

# Describe a specific task
aws ecs describe-tasks \
  --cluster my-cluster \
  --tasks <task-arn> \
  --region ap-southeast-1
```

## Best Practices

### 1. Always Apply Terraform First

Before deploying, ensure infrastructure is up to date:
```bash
cd infra
terraform plan
terraform apply
```

### 2. Set Appropriate Retention

The default is 7 days. Adjust in `infra/cloudwatch.tf`:
```hcl
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/iot-backend"
  retention_in_days = 14  # Change to 14, 30, 60, 90, etc.
}
```

### 3. Use Log Filters

For production, set up metric filters for errors:
```bash
aws logs put-metric-filter \
  --log-group-name /ecs/iot-backend \
  --filter-name ErrorCount \
  --filter-pattern "ERROR" \
  --metric-transformations \
    metricName=ApplicationErrors,metricNamespace=IoTBackend,metricValue=1
```

### 4. Monitor Costs

CloudWatch Logs pricing:
- Ingestion: ~$0.50/GB
- Storage: ~$0.03/GB/month
- With 7-day retention, costs are minimal for most applications

View current usage:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Logs \
  --metric-name IncomingBytes \
  --dimensions Name=LogGroupName,Value=/ecs/iot-backend \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Sum \
  --region ap-southeast-1
```

## Complete Deployment Workflow

Here's the complete workflow including logging:

```bash
# 1. Apply Terraform (creates log group)
cd infra
terraform apply

# 2. Build and deploy
cd ../backend
make deploy

# 3. Check deployment status
make status

# 4. View logs
make logs

# 5. If issues, check log streams
make check-logs
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `make check-logs` | Check if log group exists |
| `make create-log-group` | Create log group manually |
| `make logs` | Tail logs in real-time |
| `make status` | Check service status |
| `make deploy` | Deploy service |

## Additional Resources

- [AWS CloudWatch Logs Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)
- [ECS Task Definition Logging](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_awslogs.html)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)

---

**Status:** 📝 Documentation Complete  
**Last Updated:** 2024  
**Next Step:** Run `cd infra && terraform apply` or `make create-log-group`
