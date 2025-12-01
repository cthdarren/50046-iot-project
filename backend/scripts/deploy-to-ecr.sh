#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="availability-service"
REGION="${AWS_REGION:-ap-southeast-1}"
INFRA_DIR="../../infra"

echo -e "${GREEN}=== Deploying ${SERVICE_NAME} to ECR ===${NC}\n"

# Determine the script's directory and navigate to backend root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Check if we're in the right directory structure
if [ ! -f "${BACKEND_DIR}/${SERVICE_NAME}/Dockerfile" ]; then
    echo -e "${RED}Error: Could not find Dockerfile at ${BACKEND_DIR}/${SERVICE_NAME}/Dockerfile${NC}"
    echo "Current directory: $(pwd)"
    echo "Backend directory: ${BACKEND_DIR}"
    exit 1
fi

# Change to backend directory
cd "${BACKEND_DIR}"
echo -e "${GREEN}✓ Working directory: ${BACKEND_DIR}${NC}\n"

# Check if required tools are installed
command -v aws >/dev/null 2>&1 || { echo -e "${RED}Error: aws-cli is not installed${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: docker is not installed${NC}"; exit 1; }

# Get AWS Account ID
echo -e "${YELLOW}Getting AWS account ID...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: Could not get AWS account ID. Is AWS CLI configured?${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS Account ID: ${AWS_ACCOUNT_ID}${NC}\n"

# Get ECR repository URI from Terraform outputs
echo -e "${YELLOW}Getting ECR repository URI from Terraform...${NC}"
INFRA_PATH="${BACKEND_DIR}/${INFRA_DIR}"
if [ ! -d "${INFRA_PATH}" ]; then
    echo -e "${RED}Error: Terraform infra directory not found at ${INFRA_PATH}${NC}"
    exit 1
fi

ECR_URI=$(cd "${INFRA_PATH}" && terraform output -raw ecr_repository_uri 2>/dev/null)
if [ -z "$ECR_URI" ]; then
    echo -e "${RED}Error: Could not get ECR URI from Terraform outputs${NC}"
    echo "Make sure you have run 'terraform apply' in the infra directory"
    exit 1
fi
echo -e "${GREEN}✓ ECR URI: ${ECR_URI}${NC}\n"

# Authenticate Docker to ECR
echo -e "${YELLOW}Authenticating Docker to ECR...${NC}"
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to authenticate with ECR${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker authenticated${NC}\n"

# Generate image tags
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
IMAGE_TAG_LATEST="${ECR_URI}:latest"
IMAGE_TAG_TIMESTAMP="${ECR_URI}:${TIMESTAMP}"
IMAGE_TAG_GIT="${ECR_URI}:${GIT_SHA}"

# Build the Docker image
echo -e "${YELLOW}Building Docker image for ${SERVICE_NAME}...${NC}"
cd "${BACKEND_DIR}/${SERVICE_NAME}"
docker build -t ${SERVICE_NAME} .
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker image built${NC}\n"

# Tag the image
echo -e "${YELLOW}Tagging images...${NC}"
docker tag ${SERVICE_NAME}:latest ${IMAGE_TAG_LATEST}
docker tag ${SERVICE_NAME}:latest ${IMAGE_TAG_TIMESTAMP}
docker tag ${SERVICE_NAME}:latest ${IMAGE_TAG_GIT}
echo -e "${GREEN}✓ Tagged: latest${NC}"
echo -e "${GREEN}✓ Tagged: ${TIMESTAMP}${NC}"
echo -e "${GREEN}✓ Tagged: ${GIT_SHA}${NC}\n"

# Push images to ECR
echo -e "${YELLOW}Pushing images to ECR...${NC}"
docker push ${IMAGE_TAG_LATEST}
docker push ${IMAGE_TAG_TIMESTAMP}
docker push ${IMAGE_TAG_GIT}

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}=== Deployment successful! ===${NC}"
    echo -e "${GREEN}Images pushed:${NC}"
    echo -e "  - ${IMAGE_TAG_LATEST}"
    echo -e "  - ${IMAGE_TAG_TIMESTAMP}"
    echo -e "  - ${IMAGE_TAG_GIT}"
    echo -e "\n${YELLOW}Next steps:${NC}"
    echo -e "  1. Update your ECS task definition to use the new image"
    echo -e "  2. Deploy the updated task definition to your ECS service"
else
    echo -e "\n${RED}=== Deployment failed! ===${NC}"
    exit 1
fi
