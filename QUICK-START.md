# 50046 IoT Project - Quick Start Guide

> **Complete reference for deploying and managing the IoT restroom analytics system**

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Backend Deployment](#backend-deployment)
5. [Health Checks](#health-checks)
6. [Common Tasks](#common-tasks)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

An IoT analytics system for restroom occupancy tracking in high-traffic areas.

**System Components:**
- **IoT Sensors**: Publish occupancy data via MQTT
- **Lambda**: Processes sensor messages and stores in RDS
- **Availability Service**: REST API for current occupancy data
- **Analytics Service**: REST API for usage analytics and reporting
- **RDS PostgreSQL**: Central data store
- **Application Load Balancer**: Public HTTPS/HTTP endpoint

---

## ✅ Prerequisites

### Required Tools

```bash
# AWS CLI v2
aws --version

# Docker
docker --version

# Terraform
terraform --version

# Make (usually pre-installed on Linux/Mac)
make --version
```

### AWS Configuration

```bash
# Configure AWS credentials
aws configure

# Verify setup
aws sts get-caller-identity

# Set default region (if needed)
export AWS_REGION=ap-southeast-1
```

---

## 🏗️ Infrastructure Setup

### 1. Create RDS Credentials Secret

**Important**: Do this FIRST before running Terraform!

```bash
aws secretsmanager create-secret \
  --name rds_credentials \
  --secret-string '{"username":"iot_master","password":"YourSecurePassword123!"}'
```

### 2. Initialize and Deploy Infrastructure

```bash
cd infra

# Initialize Terraform
make init

# Preview changes
make plan

# Deploy infrastructure
make apply
```

**Deployment time**: ~10-15 minutes (RDS takes the longest)

### 3. Verify Infrastructure

```bash
# Show all outputs
make output

# Show key outputs
make output-summary

# Check infrastructure status
make status

# Verify AWS resources
make check-aws
```

### 4. Save IoT Certificates

```bash
# Save certificates to files
make save-iot-certs

# Certificates will be saved to: ../iot-certificates/
```

---

## 🚀 Backend Deployment

### Deploy Availability Service

```bash
cd backend

# View available commands
make help

# Deploy availability service (builds, pushes to ECR, updates ECS)
make deploy-availability
```

**Deployment time**: ~5-8 minutes

### Deploy Analytics Service

```bash
cd backend

# Deploy analytics service
make deploy-analytics
```

### Deploy Both Services

```bash
cd backend

# Deploy everything
make deploy-all
```

---

## 🏥 Health Checks

### Check Service Health

```bash
# From backend directory
make health-check

# Or manually
curl http://<ALB-DNS>/availability/health
```

**Expected response:**
```json
{"status":"healthy"}
```

### Get ALB URL

```bash
# From infra directory
cd infra
terraform output availability_service_url

# From backend directory
cd backend
make info
```

### Check Service Status

```bash
cd backend

# Check availability service
make status-availability

# Check analytics service
make status-analytics

# Check both
make status-all
```

---

## 📝 Common Tasks

### View Logs

```bash
cd backend

# Availability service logs
make logs-availability

# Analytics service logs
make logs-analytics
```

### List ECR Images

```bash
cd backend

# List recent images with timestamps
make list-images
```

### Run Services Locally

```bash
cd backend

# Run availability service locally
make run-availability

# Run analytics service locally
make run-analytics
```

**Note**: Update `.env` file with local database credentials first.

### Watch Deployment

```bash
cd backend

# Watch availability service deployment
make watch-deployment-availability

# Wait for deployment to stabilize
make wait-for-stable-availability
```

### Rebuild and Redeploy

```bash
cd backend

# Just rebuild
make build-availability

# Just push to ECR
make push-availability

# Full deployment
make deploy-availability
```

---

## 🔄 Rollback Procedure

### List Available Versions

```bash
cd backend
make list-images
```

### Deploy Specific Version

```bash
# Update task definition to use specific tag
aws ecs update-service \
  --cluster my-cluster \
  --service availability-service \
  --task-definition availability-service:<revision-number> \
  --region ap-southeast-1
```

### Emergency Rollback

```bash
# Scale down
aws ecs update-service \
  --cluster my-cluster \
  --service availability-service \
  --desired-count 0 \
  --region ap-southeast-1

# Wait 30 seconds
sleep 30

# Scale back up with previous version
aws ecs update-service \
  --cluster my-cluster \
  --service availability-service \
  --desired-count 1 \
  --region ap-southeast-1
```

---

## 🛠️ Troubleshooting

### Service Won't Start

**Check logs:**
```bash
cd backend
make logs-availability
```

**Check ECS events:**
```bash
aws ecs describe-services \
  --cluster my-cluster \
  --services availability-service \
  --region ap-southeast-1 \
  --query 'services[0].events[0:5]'
```

**Check task definition:**
```bash
aws ecs describe-task-definition \
  --task-definition availability-service \
  --region ap-southeast-1
```

### Cannot Push to ECR

**Re-authenticate:**
```bash
cd backend
make ecr-login
```

### Health Check Failing

**Common causes:**
1. Service hasn't finished deploying (wait 3-5 minutes)
2. FastAPI app doesn't have `root_path="/availability"` configured
3. ALB target group unhealthy (check target group in AWS Console)

**Check ALB target health:**
```bash
aws elbv2 describe-target-health \
  --target-group-arn $(cd infra && terraform output -raw availability_service_target_group_arn)
```

### Database Connection Issues

**Check RDS status:**
```bash
cd infra
make status
```

**Verify secrets:**
```bash
aws secretsmanager get-secret-value \
  --secret-id rds_credentials \
  --region ap-southeast-1
```

**Check security groups:**
```bash
# Ensure ECS service can reach RDS
aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=service-sg" \
  --region ap-southeast-1
```

### Terraform State Locked

```bash
cd infra

# Get lock ID from error message, then:
make unlock LOCK_ID=<lock-id-from-error>
```

### "Repository Does Not Exist"

```bash
cd infra

# Create ECR repository
terraform apply -target=aws_ecr_repository.availability_service
```

---

## 📊 Monitoring

### View CloudWatch Logs

```bash
# Availability service
aws logs tail /ecs/availability-service --follow --region ap-southeast-1

# Analytics service
aws logs tail /ecs/analytics-service --follow --region ap-southeast-1

# Lambda function
cd infra && make logs-lambda
```

### Check Resource Usage

```bash
# ECS task metrics
aws ecs describe-services \
  --cluster my-cluster \
  --services availability-service \
  --region ap-southeast-1
```

### Set Up Alarms (Optional)

```bash
# Add to infra/cloudwatch.tf and apply
cd infra
make apply
```

---

## 🔐 Security Best Practices

1. **Never commit secrets to Git**
   - Use AWS Secrets Manager
   - Add `.env` to `.gitignore`

2. **Rotate credentials regularly**
   ```bash
   aws secretsmanager update-secret \
     --secret-id rds_credentials \
     --secret-string '{"username":"iot_master","password":"NewPassword123!"}'
   ```

3. **Review security groups**
   ```bash
   cd infra
   # Check alb.tf and service.tf for security group rules
   ```

4. **Enable CloudTrail**
   - Track API calls and changes

5. **Use IAM roles, not access keys**
   - Already configured in `infra/iam.tf`

---

## 📦 Project Structure

```
50046-iot-project/
├── backend/
│   ├── availability-service/    # REST API for occupancy data
│   ├── analytics-service/       # REST API for analytics
│   ├── shared/                  # Shared Python code
│   ├── Makefile                 # Backend deployment commands
│   └── README.md
├── infra/
│   ├── *.tf                     # Terraform configuration
│   ├── Makefile                 # Infrastructure commands
│   └── outputs.tf               # Terraform outputs
├── lambda/
│   └── handler.js               # IoT message processor
├── frontend/                    # (Future: React app)
├── docker-compose.yml           # Local development
└── readme.md                    # Project overview
```

---

## 🎯 Key Information

| Component | Value |
|-----------|-------|
| **AWS Region** | ap-southeast-1 |
| **ECS Cluster** | my-cluster |
| **ECR Repository** | iot |
| **Services** | availability-service, analytics-service |
| **Load Balancer** | iot-alb |
| **Database** | PostgreSQL on RDS |

---

## 🔗 Quick Links

### Backend Commands
```bash
cd backend
make help                    # Show all commands
make deploy-availability     # Deploy availability service
make deploy-analytics        # Deploy analytics service
make status-all             # Check service status
make logs-availability      # View logs
make health-check           # Test endpoints
```

### Infrastructure Commands
```bash
cd infra
make help                   # Show all commands
make plan                   # Preview changes
make apply                  # Deploy infrastructure
make output-summary         # Show key outputs
make status                 # Check infrastructure
make check-health          # Health check services
```

---

## 📚 Additional Resources

- **Detailed Backend Guide**: `backend/README.md`
- **Deployment Guide**: `backend/DEPLOYMENT.md`
- **Quick Reference**: `backend/QUICK-REFERENCE.md`
- **Infrastructure Docs**: `infra/ADDING-SERVICES-TO-ALB.md`
- **AWS ECS Docs**: https://docs.aws.amazon.com/ecs/
- **AWS ECR Docs**: https://docs.aws.amazon.com/ecr/
- **Terraform AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/

---

## 🆘 Getting Help

### Check Service Status
```bash
cd backend && make status-all
```

### View Recent Logs
```bash
cd backend && make logs-availability
```

### Verify Infrastructure
```bash
cd infra && make status
```

### Common Issues
- **404 Not Found**: Service needs `root_path="/availability"` in FastAPI config
- **Can't push to ECR**: Run `make ecr-login`
- **Service won't start**: Check logs with `make logs-availability`
- **Health check fails**: Wait 5 minutes for deployment, then check target group

---

## 🚀 Typical Workflow

**First Time Setup:**
```bash
# 1. Create RDS secret
aws secretsmanager create-secret --name rds_credentials --secret-string '{"username":"iot_master","password":"SecurePass123!"}'

# 2. Deploy infrastructure
cd infra && make apply

# 3. Deploy services
cd ../backend && make deploy-all

# 4. Verify
make health-check
```

**Regular Updates:**
```bash
# 1. Make code changes
vim backend/availability-service/app/main.py

# 2. Deploy
cd backend && make deploy-availability

# 3. Monitor
make watch-deployment-availability

# 4. Check health
make health-check
```

**Rollback:**
```bash
# 1. List versions
make list-images

# 2. Update service to previous version
aws ecs update-service --cluster my-cluster --service availability-service --task-definition availability-service:5 --region ap-southeast-1
```

---

**Last Updated**: January 2025  
**Project**: 50046 Cloud Computing and IoT Final Project  
**Team**: IoT Restroom Analytics

---

**Pro Tip**: Bookmark this file and keep it open while working! 🔖