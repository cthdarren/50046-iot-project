# Backend Deployment Workflow

Complete guide for deploying the availability-service backend to AWS ECR and ECS.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Deployment](#quick-deployment)
3. [Detailed Workflow](#detailed-workflow)
4. [Deployment Methods](#deployment-methods)
5. [Rollback Procedures](#rollback-procedures)
6. [Troubleshooting](#troubleshooting)
7. [CI/CD Integration](#cicd-integration)

---

## Prerequisites

### Required Tools

- **AWS CLI** (v2.x recommended)
  ```bash
  aws --version
  ```

- **Docker** (v20.x or higher)
  ```bash
  docker --version
  ```

- **Terraform** (already applied)
  ```bash
  cd ../infra && terraform output ecr_repository_uri
  ```

### AWS Permissions Required

Your IAM user/role needs the following permissions:

- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:GetDownloadUrlForLayer`
- `ecr:PutImage`
- `ecr:InitiateLayerUpload`
- `ecr:UploadLayerPart`
- `ecr:CompleteLayerUpload`
- `ecr:DescribeImages`
- `ecr:ListImages`
- `ecs:RegisterTaskDefinition`
- `ecs:UpdateService`
- `ecs:DescribeServices`
- `ecs:DescribeTaskDefinition`

### AWS Configuration

Ensure your AWS credentials are configured:

```bash
aws configure list
# or
cat ~/.aws/credentials
```

Set the correct region (default: ap-southeast-1):

```bash
export AWS_REGION=ap-southeast-1
```

---

## Quick Deployment

### One-Command Deployment

From the `backend` directory:

```bash
# Build, push to ECR, and update ECS service
make deploy
```

This will:
1. Authenticate Docker with ECR
2. Build the Docker image
3. Tag with latest, timestamp, and git SHA
4. Push all tags to ECR
5. Update the ECS service with the new image

### View Available Commands

```bash
make help
```

---

## Detailed Workflow

### Step 1: Build the Docker Image

```bash
cd backend/availability-service
docker build -t availability-service:latest .
```

**What happens:**
- Uses multi-stage Dockerfile
- Installs Python 3.14 and dependencies
- Copies application code
- Exposes port 8001
- Sets uvicorn as entrypoint

**Build time:** ~2-5 minutes (first build), ~30 seconds (cached)

### Step 2: Authenticate with ECR

```bash
# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Login to ECR
aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-1.amazonaws.com
```

**Authentication validity:** 12 hours

### Step 3: Tag the Image

```bash
# Get ECR repository URI from Terraform
ECR_URI=$(cd ../infra && terraform output -raw ecr_repository_uri)

# Tag with multiple tags for versioning
docker tag availability-service:latest ${ECR_URI}:latest
docker tag availability-service:latest ${ECR_URI}:$(date +%Y%m%d-%H%M%S)
docker tag availability-service:latest ${ECR_URI}:$(git rev-parse --short HEAD)
```

**Tags created:**
- `latest` - Always points to most recent
- `20240315-143022` - Timestamp for rollback
- `a3f2c1d` - Git commit SHA for tracking

### Step 4: Push to ECR

```bash
docker push ${ECR_URI}:latest
docker push ${ECR_URI}:$(date +%Y%m%d-%H%M%S)
docker push ${ECR_URI}:$(git rev-parse --short HEAD)
```

**Upload time:** 
- First push: ~5-10 minutes (depends on connection)
- Subsequent pushes: ~1-3 minutes (only changed layers)

**Image size:** ~300-500 MB (compressed layers)

### Step 5: Update ECS Service

```bash
aws ecs update-service \
  --cluster my-cluster \
  --service iot-backend-service \
  --force-new-deployment \
  --region ap-southeast-1
```

**Deployment time:** ~3-5 minutes

**What happens:**
1. ECS creates new task with updated image
2. New task starts and passes health checks
3. Old task is gracefully stopped
4. Service reaches stable state

### Step 6: Verify Deployment

```bash
# Check service status
aws ecs describe-services \
  --cluster my-cluster \
  --services iot-backend-service \
  --region ap-southeast-1 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'

# View recent logs
aws logs tail /ecs/iot-backend --follow --region ap-southeast-1
```

---

## Deployment Methods

### Method 1: Make Commands (Recommended)

Simplest approach using the Makefile:

```bash
cd backend

# Just build locally
make build

# Build and push to ECR
make push

# Build, push, and update ECS
make deploy

# Run locally for testing
make run-local
```

### Method 2: Deployment Script

Using the automated bash script:

```bash
cd backend/scripts
./deploy-to-ecr.sh
```

Features:
- ✅ Colored output for readability
- ✅ Error checking at each step
- ✅ Automatic tagging with timestamp and git SHA
- ✅ Verification of image existence
- ✅ Summary of deployment

### Method 3: Update ECS Script

Deploy a specific image tag to ECS:

```bash
cd backend/scripts

# Deploy latest
./update-ecs.sh latest

# Deploy specific timestamp
./update-ecs.sh 20240315-143022

# Deploy specific git commit
./update-ecs.sh a3f2c1d
```

### Method 4: Manual Commands

Complete control with individual commands:

```bash
# 1. Login
make ecr-login

# 2. Build
cd availability-service
docker build -t availability-service:latest .

# 3. Tag
ECR_URI=$(cd ../../infra && terraform output -raw ecr_repository_uri)
docker tag availability-service:latest ${ECR_URI}:latest

# 4. Push
docker push ${ECR_URI}:latest

# 5. Update service
aws ecs update-service \
  --cluster my-cluster \
  --service iot-backend-service \
  --force-new-deployment \
  --region ap-southeast-1
```

---

## Rollback Procedures

### Quick Rollback to Previous Version

```bash
# List recent images with timestamps
aws ecr describe-images \
  --repository-name iot \
  --region ap-southeast-1 \
  --query 'sort_by(imageDetails,&imagePushedAt)[-10:].{Tag:imageTags[0],Pushed:imagePushedAt}' \
  --output table

# Deploy specific version
cd backend/scripts
./update-ecs.sh 20240315-140000

# Wait for deployment to stabilize
WAIT_FOR_DEPLOYMENT=true ./update-ecs.sh 20240315-140000
```

### Rollback Using Previous Task Definition

```bash
# List recent task definitions
aws ecs list-task-definitions \
  --family-prefix iot-backend \
  --sort DESC \
  --max-items 10 \
  --region ap-southeast-1

# Update service to specific task definition revision
aws ecs update-service \
  --cluster my-cluster \
  --service iot-backend-service \
  --task-definition iot-backend:5 \
  --region ap-southeast-1
```

### Emergency Rollback

If the service is failing:

```bash
# Scale down to 0
aws ecs update-service \
  --cluster my-cluster \
  --service iot-backend-service \
  --desired-count 0 \
  --region ap-southeast-1

# Deploy known good version
cd backend/scripts
./update-ecs.sh <KNOWN_GOOD_TAG>

# Scale back up
aws ecs update-service \
  --cluster my-cluster \
  --service iot-backend-service \
  --desired-count 1 \
  --region ap-southeast-1
```

---

## Troubleshooting

### Issue: "no basic auth credentials"

**Cause:** Docker not authenticated with ECR

**Solution:**
```bash
make ecr-login
# or
aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-southeast-1.amazonaws.com
```

### Issue: "repository does not exist"

**Cause:** ECR repository not created yet

**Solution:**
```bash
cd ../infra
terraform apply -target=aws_ecr_repository.app
```

### Issue: Build fails with "cannot find requirements.txt"

**Cause:** Running build from wrong directory

**Solution:**
```bash
cd backend/availability-service
docker build -t availability-service .
```

### Issue: Push is very slow

**Causes:**
- Slow internet connection
- Large image size
- No layer caching

**Solutions:**
```bash
# Use multi-stage builds (already configured)
# Push from EC2 instance in same region
# Use AWS VPN for faster connection

# Check image size
docker images availability-service:latest
```

### Issue: ECS task fails to start

**Debugging steps:**

```bash
# 1. Check service events
aws ecs describe-services \
  --cluster my-cluster \
  --services iot-backend-service \
  --region ap-southeast-1 \
  --query 'services[0].events[0:5]'

# 2. Check task logs
aws logs tail /ecs/iot-backend --follow --region ap-southeast-1

# 3. Verify task definition
aws ecs describe-task-definition \
  --task-definition iot-backend \
  --region ap-southeast-1

# 4. Check security group rules
aws ec2 describe-security-groups \
  --group-names service-sg \
  --region ap-southeast-1
```

### Issue: "Task failed to start" - Cannot pull image

**Cause:** ECS task role lacks ECR permissions

**Solution:**
```bash
# Verify IAM role in infra/iam.tf has ECR permissions
cd ../infra
terraform plan -target=aws_iam_role.ecs_task_exec
terraform apply -target=aws_iam_role.ecs_task_exec
```

### Issue: Environment variables not loading

**Cause:** Secrets not configured in task definition

**Solution:**
Update task definition to include secrets from AWS Secrets Manager (see `infra/task_definition.tf`)

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Backend to ECR

on:
  push:
    branches: [main]
    paths:
      - 'backend/availability-service/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-southeast-1
      
      - name: Login to ECR
        run: |
          aws ecr get-login-password --region ap-southeast-1 | \
          docker login --username AWS --password-stdin \
          ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-southeast-1.amazonaws.com
      
      - name: Build and Push
        run: |
          cd backend
          make push
      
      - name: Update ECS
        run: |
          cd backend/scripts
          ./update-ecs.sh latest
```

### GitLab CI Example

```yaml
deploy-backend:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - apk add --no-cache python3 py3-pip aws-cli
    - aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-1.amazonaws.com
  script:
    - cd backend
    - make push
    - cd scripts
    - ./update-ecs.sh latest
  only:
    - main
  environment:
    name: production
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    environment {
        AWS_REGION = 'ap-southeast-1'
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'cd backend && make build'
            }
        }
        
        stage('Push to ECR') {
            steps {
                withAWS(credentials: 'aws-credentials', region: "${AWS_REGION}") {
                    sh 'cd backend && make push'
                }
            }
        }
        
        stage('Deploy to ECS') {
            steps {
                withAWS(credentials: 'aws-credentials', region: "${AWS_REGION}") {
                    sh 'cd backend/scripts && ./update-ecs.sh latest'
                }
            }
        }
    }
}
```

---

## Best Practices

### 1. Always Tag Images Properly

```bash
# ✅ Good - Multiple tags for flexibility
docker tag app:latest ${ECR_URI}:latest
docker tag app:latest ${ECR_URI}:v1.2.3
docker tag app:latest ${ECR_URI}:$(git rev-parse --short HEAD)

# ❌ Bad - Only latest
docker tag app:latest ${ECR_URI}:latest
```

### 2. Test Locally Before Pushing

```bash
# Build and run locally first
make build
make run-local

# Test endpoints
curl http://localhost:8001/health
```

### 3. Use Image Scanning

```bash
# Enable ECR image scanning in Terraform
# See infra/ecr.tf

# View scan results
aws ecr describe-image-scan-findings \
  --repository-name iot \
  --image-id imageTag=latest \
  --region ap-southeast-1
```

### 4. Monitor Deployments

```bash
# Watch deployment progress
watch -n 5 'aws ecs describe-services --cluster my-cluster --services iot-backend-service --region ap-southeast-1 --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}"'

# Or use the wait command
aws ecs wait services-stable \
  --cluster my-cluster \
  --services iot-backend-service \
  --region ap-southeast-1
```

### 5. Keep Images Small

- Use multi-stage builds ✅ (already configured)
- Remove unnecessary dependencies
- Use `.dockerignore` file
- Combine RUN commands

### 6. Secure Your Images

- Don't hardcode secrets in Dockerfile
- Use AWS Secrets Manager for sensitive data
- Run containers as non-root user (if possible)
- Keep base images updated

---

## Deployment Checklist

Before deploying to production:

- [ ] Code reviewed and approved
- [ ] Tests passing locally
- [ ] Environment variables configured in Secrets Manager
- [ ] Database migrations prepared (if needed)
- [ ] Docker image builds successfully
- [ ] Image scanned for vulnerabilities
- [ ] Rollback plan prepared
- [ ] Monitoring/alerting configured
- [ ] Team notified of deployment

---

## Additional Resources

- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

**Last Updated:** 2024
**Maintained By:** IoT Project Team