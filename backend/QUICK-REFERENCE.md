# Backend Deployment Quick Reference

> **One-page cheat sheet for deploying to ECR/ECS**

---

## 🚀 Quick Commands

### Deploy Everything (Recommended)
```bash
cd backend
make deploy
```

### Just Push to ECR
```bash
cd backend
make push
```

### Deploy Specific Version
```bash
cd backend/scripts
./update-ecs.sh 20240315-143022
```

---

## 📋 Common Tasks

| Task | Command |
|------|---------|
| Build locally | `make build` |
| Run locally | `make run-local` |
| Login to ECR | `make ecr-login` |
| Push to ECR | `make push` |
| Full deployment | `make deploy` |
| Check service status | `make status` |
| List ECR images | `make list-images` |
| Watch deployment | `make watch-deployment` |
| Wait for stable | `make wait-for-stable` |
| View logs | `make logs` |
| View all commands | `make help` |
| Clean local images | `make clean` |

---

## 🔍 Troubleshooting Commands

### Check if image exists in ECR
```bash
aws ecr list-images --repository-name iot --region ap-southeast-1
```

### View recent images with timestamps
```bash
aws ecr describe-images \
  --repository-name iot \
  --region ap-southeast-1 \
  --query 'sort_by(imageDetails,&imagePushedAt)[-5:].{Tag:imageTags[0],Pushed:imagePushedAt}' \
  --output table
```

### Check ECS service status
```bash
aws ecs describe-services \
  --cluster my-cluster \
  --services iot-backend-service \
  --region ap-southeast-1 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
```

### View service logs
```bash
aws logs tail /ecs/iot-backend --follow --region ap-southeast-1
```

### Get ECR repository URI
```bash
cd infra && terraform output ecr_repository_uri
```

---

## 🔄 Rollback

### List available versions
```bash
aws ecr describe-images \
  --repository-name iot \
  --region ap-southeast-1 \
  --query 'sort_by(imageDetails,&imagePushedAt)[-10:].imageTags[0]'
```

### Deploy previous version
```bash
cd backend/scripts
./update-ecs.sh <TAG>
```

### Emergency: Scale down and redeploy
```bash
# Scale to 0
aws ecs update-service --cluster my-cluster --service iot-backend-service --desired-count 0 --region ap-southeast-1

# Deploy good version
cd backend/scripts && ./update-ecs.sh <GOOD_TAG>

# Scale back up
aws ecs update-service --cluster my-cluster --service iot-backend-service --desired-count 1 --region ap-southeast-1
```

---

## 🐛 Common Errors & Fixes

### Error: "no basic auth credentials"
```bash
make ecr-login
```

### Error: "repository does not exist"
```bash
cd infra && terraform apply -target=aws_ecr_repository.app
```

### Error: "cannot connect to Docker daemon"
```bash
sudo systemctl start docker
# or on macOS: open Docker Desktop
```

### Error: Build fails - wrong directory
```bash
cd backend/availability-service && docker build -t availability-service .
```

---

## 📊 Monitoring

### Watch deployment in real-time
```bash
watch -n 5 'aws ecs describe-services \
  --cluster my-cluster \
  --services iot-backend-service \
  --region ap-southeast-1 \
  --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}"'
```

### Wait for deployment to complete
```bash
aws ecs wait services-stable \
  --cluster my-cluster \
  --services iot-backend-service \
  --region ap-southeast-1
```

### View deployment events
```bash
aws ecs describe-services \
  --cluster my-cluster \
  --services iot-backend-service \
  --region ap-southeast-1 \
  --query 'services[0].events[0:5]'
```

---

## 🏗️ Manual Workflow (if needed)

```bash
# 1. Login to ECR
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-1.amazonaws.com

# 2. Get ECR URI
ECR_URI=$(cd infra && terraform output -raw ecr_repository_uri)

# 3. Build
cd backend/availability-service
docker build -t availability-service:latest .

# 4. Tag
docker tag availability-service:latest ${ECR_URI}:latest
docker tag availability-service:latest ${ECR_URI}:$(date +%Y%m%d-%H%M%S)

# 5. Push
docker push ${ECR_URI}:latest
docker push ${ECR_URI}:$(date +%Y%m%d-%H%M%S)

# 6. Update ECS
aws ecs update-service \
  --cluster my-cluster \
  --service iot-backend-service \
  --force-new-deployment \
  --region ap-southeast-1
```

---

## 🔐 Prerequisites Check

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Docker is running
docker info

# Check Terraform state
cd infra && terraform output

# Check region is set
echo $AWS_REGION  # Should be ap-southeast-1
```

---

## 📦 Image Tags

Every deployment creates 3 tags:

- `latest` - Always points to newest build
- `20240315-143022` - Timestamp for rollback
- `a3f2c1d` - Git commit SHA for tracking

---

## 🎯 Key Information

| Item | Value |
|------|-------|
| **Cluster** | `my-cluster` |
| **Service** | `iot-backend-service` |
| **ECR Repo** | `iot` |
| **Region** | `ap-southeast-1` |
| **Port** | `8001` |
| **Task Family** | `iot-backend` |
| **Container** | `web` |

---

## 📞 Need Help?

- Full guide: `backend/README.md`
- Detailed workflow: `backend/DEPLOYMENT.md`
- Make commands: `make help` (from backend/)
- AWS ECR docs: https://docs.aws.amazon.com/ecr/
- AWS ECS docs: https://docs.aws.amazon.com/ecs/

---

---

## 🆕 New Make Commands

```bash
# Check current service status
make status

# List recent images in ECR
make list-images

# Watch deployment in real-time
make watch-deployment

# Wait for deployment to complete
make wait-for-stable

# View service logs
make logs
```

---

**Pro Tip:** Bookmark this file! 🔖