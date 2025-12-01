# Backend Deployment Guide

This directory contains the backend services for the IoT Restroom Analytics System.

## Services

- **availability-service**: FastAPI service that provides REST API endpoints for restroom availability data

## Quick Start

### Local Development

1. **Start all services with Docker Compose:**
   ```bash
   # From project root
   docker compose up -d
   ```

2. **Run backend service locally:**
   ```bash
   cd backend
   make run-local
   ```

### Production Deployment to AWS ECR

#### Prerequisites

- AWS CLI installed and configured (`aws configure`)
- Docker installed and running
- Terraform infrastructure deployed (`cd infra && terraform apply`)
- Appropriate AWS IAM permissions for ECR

#### Method 1: Using Make (Recommended)

```bash
cd backend

# Build and push to ECR
make push

# Build, push, and update ECS service
make deploy

# View all available commands
make help
```

#### Method 2: Using the Deployment Script

```bash
cd backend/scripts
./deploy-to-ecr.sh
```

#### Method 3: Manual Steps

1. **Get your AWS account ID:**
   ```bash
   aws sts get-caller-identity --query Account --output text
   ```

2. **Authenticate Docker with ECR:**
   ```bash
   aws ecr get-login-password --region ap-southeast-1 | \
     docker login --username AWS --password-stdin \
     <ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com
   ```

3. **Get ECR repository URI:**
   ```bash
   cd ../infra
   terraform output ecr_repository_uri
   ```

4. **Build, tag, and push:**
   ```bash
   cd ../backend/availability-service
   
   # Build
   docker build -t availability-service .
   
   # Tag (replace <ECR_URI> with actual URI from step 3)
   docker tag availability-service:latest <ECR_URI>:latest
   docker tag availability-service:latest <ECR_URI>:$(date +%Y%m%d-%H%M%S)
   
   # Push
   docker push <ECR_URI>:latest
   docker push <ECR_URI>:$(date +%Y%m%d-%H%M%S)
   ```

5. **Update ECS service (optional):**
   ```bash
   aws ecs update-service \
     --cluster my-cluster \
     --service my-service \
     --force-new-deployment \
     --region ap-southeast-1
   ```

## Image Tagging Strategy

The deployment process creates three tags for each build:

- `latest` - Always points to the most recent build
- `<timestamp>` - Formatted as `YYYYMMDD-HHMMSS` for easy rollback
- `<git-sha>` - Short git commit hash for version tracking

## Environment Variables

The backend service requires the following environment variables:

- `DB_HOST` - PostgreSQL database host
- `DB_PORT` - PostgreSQL database port (default: 5432)
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password

In production, these are injected from AWS Secrets Manager via ECS task definition.

## Troubleshooting

### Docker login fails
```bash
# Verify AWS credentials are configured
aws sts get-caller-identity

# Ensure you have ECR permissions
aws ecr describe-repositories
```

### Cannot get ECR URI from Terraform
```bash
cd infra
terraform refresh
terraform output ecr_repository_uri
```

### Build fails
```bash
# Check Docker daemon is running
docker info

# View detailed build logs
cd availability-service
docker build --no-cache --progress=plain -t availability-service .
```

### Image push is slow
- ECR transfer speeds depend on your internet connection
- Consider using AWS VPN or running from an EC2 instance for faster uploads
- Each layer is cached, so subsequent pushes will be faster

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make build` | Build Docker image locally |
| `make ecr-login` | Authenticate Docker with ECR |
| `make push` | Build and push image to ECR |
| `make deploy` | Push image and update ECS service |
| `make run-local` | Run service locally on port 8001 |
| `make clean` | Remove local Docker images |
| `make test` | Run tests (if configured) |
| `make logs` | View ECS service logs |

## Architecture

```
backend/
├── availability-service/      # FastAPI service
│   ├── app/                   # Application code
│   ├── Dockerfile            # Multi-stage Docker build
│   └── requirements.txt      # Python dependencies
├── scripts/
│   └── deploy-to-ecr.sh      # Automated deployment script
├── Makefile                   # Build and deploy automation
└── README.md                  # This file
```

## Next Steps

After deploying to ECR:

1. Verify the image in ECR console or via CLI:
   ```bash
   aws ecr list-images --repository-name iot --region ap-southeast-1
   ```

2. Update your ECS task definition to use the new image URI

3. Deploy the task definition to your ECS service

4. Monitor the deployment:
   ```bash
   aws ecs describe-services --cluster my-cluster --services my-service
   ```

## Related Documentation

- [Project Root README](../readme.md) - Overall project setup
- [Infrastructure README](../infra/README.md) - Terraform configuration
- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)