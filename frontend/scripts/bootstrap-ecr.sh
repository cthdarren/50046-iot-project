#!/bin/bash

# Bootstrap script for frontend ECR image
# This script pushes an initial frontend image to ECR before Terraform can reference it

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Frontend ECR Bootstrap ===${NC}"
echo ""

# Configuration
REGION=${AWS_REGION:-ap-southeast-1}
INFRA_DIR="../infra"
IMAGE_NAME="toilet-frontend"

# Check if we're in the frontend directory
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile not found. Please run this script from the frontend directory.${NC}"
    exit 1
fi

# Check if infra directory exists
if [ ! -d "$INFRA_DIR" ]; then
    echo -e "${RED}Error: Infrastructure directory not found at $INFRA_DIR${NC}"
    exit 1
fi

# Get ECR repository URI from Terraform
echo -e "${YELLOW}Getting ECR repository URI from Terraform...${NC}"
ECR_URI=$(cd $INFRA_DIR && terraform output -raw ecr_repository_uri 2>/dev/null)

if [ -z "$ECR_URI" ]; then
    echo -e "${RED}Error: Could not get ECR repository URI from Terraform.${NC}"
    echo -e "${YELLOW}Make sure you have run 'terraform apply' in the infra directory first.${NC}"
    echo -e "${YELLOW}Note: The ECR repository should exist even if the frontend service doesn't yet.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ ECR Repository: $ECR_URI${NC}"
echo ""

# Authenticate with ECR
echo -e "${YELLOW}Authenticating with ECR...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo -e "${GREEN}✓ Authenticated${NC}"
echo ""

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t $IMAGE_NAME:latest .

echo -e "${GREEN}✓ Build complete${NC}"
echo ""

# Tag the image
echo -e "${YELLOW}Tagging image for ECR...${NC}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "initial")

docker tag $IMAGE_NAME:latest $ECR_URI:frontend-latest
docker tag $IMAGE_NAME:latest $ECR_URI:frontend-$TIMESTAMP
docker tag $IMAGE_NAME:latest $ECR_URI:frontend-$GIT_SHA

echo -e "${GREEN}✓ Tagged: frontend-latest${NC}"
echo -e "${GREEN}✓ Tagged: frontend-$TIMESTAMP${NC}"
echo -e "${GREEN}✓ Tagged: frontend-$GIT_SHA${NC}"
echo ""

# Push to ECR
echo -e "${YELLOW}Pushing images to ECR...${NC}"
docker push $ECR_URI:frontend-latest
docker push $ECR_URI:frontend-$TIMESTAMP
docker push $ECR_URI:frontend-$GIT_SHA

echo ""
echo -e "${GREEN}=== Bootstrap successful! ===${NC}"
echo ""
echo -e "${GREEN}Images pushed:${NC}"
echo -e "  - $ECR_URI:frontend-latest"
echo -e "  - $ECR_URI:frontend-$TIMESTAMP"
echo -e "  - $ECR_URI:frontend-$GIT_SHA"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Go to infra directory: ${BLUE}cd ../infra${NC}"
echo -e "  2. Apply Terraform: ${BLUE}terraform apply${NC}"
echo -e "  3. Deploy frontend updates: ${BLUE}cd ../frontend && make deploy${NC}"
echo ""
