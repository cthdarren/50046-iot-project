# Backend Deployment Quick Reference

> **One-page cheat sheet for deploying backend services to ECR/ECS**

---

## 🚀 Quick Commands

### Deploy Everything (Recommended)
```bash
cd backend
make deploy-all
```

### Deploy Individual Services
```bash
cd backend
make deploy-availability    # Availability service
make deploy-analytics       # Analytics service
```

### Just Build Locally
```bash
make build-availability
make build-analytics
```

### Just Push to ECR
```bash
make push-availability
make push-analytics
```

---

## 📋 Common Tasks

| Task | Command |
|------|---------|
| **View all commands** | `make help` |
| **Deploy availability** | `make deploy-availability` |
| **Deploy analytics** | `make deploy-analytics` |
| **Deploy both** | `make deploy-all` |
| **Build availability** | `make build-availability` |
| **Build analytics** | `make build-analytics` |
| **Run availability locally** | `make run-availability` |
| **Run analytics locally** | `make run-analytics` |
| **Check status** | `make status-all` |
| **View logs (availability)** | `make logs-availability` |
| **View logs (analytics)** | `make logs-analytics` |
| **List ECR images** | `make list-images` |
| **Health check** | `make health-check` |
| **Login to ECR** | `make ecr-login` |
| **Clean local images** | `make clean` |
| **Show project info** | `make info` |

---

## 🔍 Monitoring & Status

### Check Service Status
```bash
# Both services
make status-all

# Individual services
make status-availability
make status-analytics
```

### Watch Deployment
```bash
# Watch availability deployment
make watch-deployment-availability

# Watch analytics deployment
make watch-deployment-analytics
```

### Wait for Deployment
```bash
# Wait for availability to stabilize
make wait-for-stable-availability

# Wait for analytics to stabilize
make wait-for-stable-analytics
```

### View Logs
```bash
# Availability service logs (streaming)
make logs-availability

# Analytics service logs (streaming)
make logs-analytics
```

### Health Check
```bash
# Check both services via public URLs
make health-check

# Or manually
curl $(cd ../infra && terraform output -raw alb_url)/availability/health
```

---

## 🔄 Troubleshooting Commands

### Authentication Issues
```bash
# Re-login to ECR
make ecr-login
```

### Check AWS Configuration
```bash
# Verify AWS credentials and region
make check-aws
```

### List ECR Images
```bash
# Show recent images with timestamps
make list-images

# Or with AWS CLI
aws ecr describe-images \
  --repository-name iot \
  --region ap-southeast-1 \
  --query 'sort_by(imageDetails,&imagePushedAt)[-10:].{Tag:imageTags[0],Pushed:imagePushedAt}' \
  --output table
```

### Check ECS Service Status
```bash
# Using make
make status-availability

# Or directly with AWS CLI
aws ecs describe-services \
  --cluster my-cluster \
  --services availability-service \
  --region ap-southeast-1 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
```

### View Service Events
```bash
aws ecs describe-services \
  --cluster my-cluster \
  --services availability-service \
  --region ap-southeast-1 \
  --query 'services[0].events[0:5]'
```

### Check Target Group Health
```bash
aws elbv2 describe-target-health \
  --target-group-arn $(cd ../infra && terraform output -raw availability_service_target_group_arn)
```

### View All Logs
```bash
# Using AWS CLI directly
aws logs tail /ecs/availability-service --follow --region ap-southeast-1
aws logs tail /ecs/analytics-service --follow --region ap-southeast-1
```

---

## 🔄 Rollback

### List Available Versions
```bash
make list-images
```

Output shows tags like:
- `availability-latest`
- `availability-20240315-143022`
- `availability-a3f2c1d`
- `analytics-latest`
- `analytics-20240315-143022`
- `analytics-a3f2c1d`

### Deploy Specific Version
```bash
# Update task definition to use specific revision
aws ecs update-service \
  --cluster my-cluster \
  --service availability-service \
  --task-definition availability-service:5 \
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

# Scale back up (will use previous task definition)
aws ecs update-service \
  --cluster my-cluster \
  --service availability-service \
  --desired-count 1 \
  --region ap-southeast-1
```

---

## 🏗️ Manual Workflow (if needed)

### Availability Service
```bash
# 1. Login to ECR
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.ap-southeast-1.amazonaws.com

# 2. Get ECR URI
ECR_URI=$(cd ../infra && terraform output -raw ecr_repository_uri)

# 3. Build
cd availability-service
docker build -t availability-service:latest .

# 4. Tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
GIT_SHA=$(git rev-parse --short HEAD)
docker tag availability-service:latest ${ECR_URI}:availability-latest
docker tag availability-service:latest ${ECR_URI}:availability-${TIMESTAMP}
docker tag availability-service:latest ${ECR_URI}:availability-${GIT_SHA}

# 5. Push
docker push ${ECR_URI}:availability-latest
docker push ${ECR_URI}:availability-${TIMESTAMP}
docker push ${ECR_URI}:availability-${GIT_SHA}

# 6. Update ECS
aws ecs update-service \
  --cluster my-cluster \
  --service availability-service \
  --force-new-deployment \
  --region ap-southeast-1
```

### Analytics Service
```bash
# Same steps as above, but replace:
# - availability-service -> analytics-service
# - availability- -> analytics-
```

---

## 🐛 Common Errors & Fixes

### Error: "no basic auth credentials"
**Cause:** Docker not authenticated with ECR

**Solution:**
```bash
make ecr-login
```

### Error: "repository does not exist"
**Cause:** ECR repository not created yet

**Solution:**
```bash
cd ../infra
terraform apply -target=aws_ecr_repository.availability_service
```

### Error: "cannot connect to Docker daemon"
**Cause:** Docker not running

**Solution:**
```bash
# Linux
sudo systemctl start docker

# macOS
open /Applications/Docker.app
```

### Error: Build fails - wrong directory
**Cause:** Running build from wrong directory

**Solution:**
```bash
cd backend/availability-service
docker build -t availability-service .
```

### Error: "Task failed to start"
**Debugging steps:**

```bash
# 1. Check service events
aws ecs describe-services \
  --cluster my-cluster \
  --services availability-service \
  --region ap-southeast-1 \
  --query 'services[0].events[0:5]'

# 2. Check task logs
make logs-availability

# 3. Verify task definition
aws ecs describe-task-definition \
  --task-definition availability-service \
  --region ap-southeast-1
```

### Error: Health check returns 404
**Cause:** FastAPI app missing `root_path` configuration

**Solution:**
Ensure `main.py` has:
```python
app = FastAPI(
    title="Availability Service",
    lifespan=lifespan,
    root_path="/availability"  # This is required!
)
```

---

## 📊 Image Tags

Every deployment creates 3 tags per service:

**Availability Service:**
- `availability-latest` - Always points to newest build
- `availability-20240315-143022` - Timestamp for rollback
- `availability-a3f2c1d` - Git commit SHA for tracking

**Analytics Service:**
- `analytics-latest` - Always points to newest build
- `analytics-20240315-143022` - Timestamp for rollback
- `analytics-a3f2c1d` - Git commit SHA for tracking

---

## 🎯 Key Information

| Item | Value |
|------|-------|
| **Cluster** | `my-cluster` |
| **ECR Repo** | `iot` |
| **Region** | `ap-southeast-1` |
| **Services** | `availability-service`, `analytics-service` |
| **Ports** | 8001 (availability), 8002 (analytics) |
| **Task Family** | `availability-service`, `analytics-service` |
| **Container Name** | `web` |

---

## 📞 Need Help?

- **Full guide**: `backend/README.md`
- **Detailed workflow**: `backend/DEPLOYMENT.md`
- **Infrastructure**: `../infra/Makefile`
- **Quick start**: `../QUICK-START.md`
- **Make commands**: `make help`
- **AWS ECS docs**: https://docs.aws.amazon.com/ecs/
- **AWS ECR docs**: https://docs.aws.amazon.com/ecr/

---

## 🔥 Pro Tips

1. **Always check status after deploy**
   ```bash
   make deploy-availability && make status-availability
   ```

2. **Monitor logs during deployment**
   ```bash
   make logs-availability
   ```

3. **Test locally before pushing**
   ```bash
   make build-availability
   make run-availability
   curl http://localhost:8001/health
   ```

4. **Check health after deployment**
   ```bash
   make health-check
   ```

5. **Use watch for real-time monitoring**
   ```bash
   make watch-deployment-availability
   ```

---

**Last Updated:** January 2025  
**Project:** 50046 Cloud Computing and IoT  
**Pro Tip:** Run `make help` to see all available commands! 🔖