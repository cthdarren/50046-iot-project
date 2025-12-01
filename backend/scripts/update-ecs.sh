#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="my-cluster"
SERVICE_NAME="iot-backend-service"
REGION="${AWS_REGION:-ap-southeast-1}"
INFRA_DIR="../../infra"

echo -e "${GREEN}=== Updating ECS Service ===${NC}\n"

# Check if required tools are installed
command -v aws >/dev/null 2>&1 || { echo -e "${RED}Error: aws-cli is not installed${NC}"; exit 1; }

# Verify AWS credentials
echo -e "${YELLOW}Verifying AWS credentials...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: Could not get AWS account ID. Is AWS CLI configured?${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS Account ID: ${AWS_ACCOUNT_ID}${NC}\n"

# Get current task definition
echo -e "${YELLOW}Getting current task definition...${NC}"
TASK_DEF_ARN=$(aws ecs describe-services \
    --cluster ${CLUSTER_NAME} \
    --services ${SERVICE_NAME} \
    --region ${REGION} \
    --query 'services[0].taskDefinition' \
    --output text 2>/dev/null)

if [ -z "$TASK_DEF_ARN" ] || [ "$TASK_DEF_ARN" = "None" ]; then
    echo -e "${RED}Error: Could not find ECS service ${SERVICE_NAME} in cluster ${CLUSTER_NAME}${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Current task definition: ${TASK_DEF_ARN}${NC}\n"

# Get ECR repository URI
echo -e "${YELLOW}Getting ECR repository URI...${NC}"
if [ ! -d "${INFRA_DIR}" ]; then
    echo -e "${RED}Error: Terraform infra directory not found at ${INFRA_DIR}${NC}"
    exit 1
fi

ECR_URI=$(cd "${INFRA_DIR}" && terraform output -raw ecr_repository_uri 2>/dev/null)
if [ -z "$ECR_URI" ]; then
    echo -e "${RED}Error: Could not get ECR URI from Terraform outputs${NC}"
    exit 1
fi
echo -e "${GREEN}✓ ECR URI: ${ECR_URI}${NC}\n"

# Allow user to specify image tag
IMAGE_TAG="${1:-latest}"
FULL_IMAGE_URI="${ECR_URI}:${IMAGE_TAG}"

echo -e "${YELLOW}Image to deploy: ${FULL_IMAGE_URI}${NC}"
echo -e "${YELLOW}Verifying image exists in ECR...${NC}"

# Verify the image exists
IMAGE_EXISTS=$(aws ecr describe-images \
    --repository-name iot \
    --image-ids imageTag=${IMAGE_TAG} \
    --region ${REGION} \
    --query 'imageDetails[0].imageTags[0]' \
    --output text 2>/dev/null || echo "")

if [ -z "$IMAGE_EXISTS" ] || [ "$IMAGE_EXISTS" = "None" ]; then
    echo -e "${RED}Error: Image with tag '${IMAGE_TAG}' not found in ECR${NC}"
    echo -e "${YELLOW}Available tags:${NC}"
    aws ecr describe-images \
        --repository-name iot \
        --region ${REGION} \
        --query 'sort_by(imageDetails,&imagePushedAt)[-5:].imageTags[0]' \
        --output table
    exit 1
fi
echo -e "${GREEN}✓ Image verified in ECR${NC}\n"

# Get current task definition JSON
echo -e "${YELLOW}Creating new task definition revision...${NC}"
TASK_DEF_JSON=$(aws ecs describe-task-definition \
    --task-definition ${TASK_DEF_ARN} \
    --region ${REGION} \
    --query 'taskDefinition')

# Update the image in the task definition
NEW_TASK_DEF=$(echo ${TASK_DEF_JSON} | jq --arg IMAGE "${FULL_IMAGE_URI}" '
    .containerDefinitions[0].image = $IMAGE |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)
')

# Register new task definition
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --region ${REGION} \
    --cli-input-json "${NEW_TASK_DEF}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

if [ -z "$NEW_TASK_DEF_ARN" ]; then
    echo -e "${RED}Error: Failed to register new task definition${NC}"
    exit 1
fi
echo -e "${GREEN}✓ New task definition: ${NEW_TASK_DEF_ARN}${NC}\n"

# Update the service
echo -e "${YELLOW}Updating ECS service...${NC}"
aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --task-definition ${NEW_TASK_DEF_ARN} \
    --force-new-deployment \
    --region ${REGION} \
    --output table \
    --query 'service.{Service:serviceName,Status:status,Running:runningCount,Desired:desiredCount}'

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}=== ECS Service Update Initiated ===${NC}"
    echo -e "${GREEN}✓ Cluster: ${CLUSTER_NAME}${NC}"
    echo -e "${GREEN}✓ Service: ${SERVICE_NAME}${NC}"
    echo -e "${GREEN}✓ Image: ${FULL_IMAGE_URI}${NC}"
    echo -e "${GREEN}✓ Task Definition: ${NEW_TASK_DEF_ARN}${NC}"

    echo -e "\n${YELLOW}Deployment in progress...${NC}"
    echo -e "${YELLOW}Monitor the deployment with:${NC}"
    echo -e "  aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${SERVICE_NAME} --region ${REGION}"
    echo -e "\n${YELLOW}View logs with:${NC}"
    echo -e "  aws logs tail /ecs/iot-backend --follow --region ${REGION}"

    # Optional: Wait for deployment to complete
    if [ "${WAIT_FOR_DEPLOYMENT}" = "true" ]; then
        echo -e "\n${YELLOW}Waiting for deployment to stabilize...${NC}"
        aws ecs wait services-stable \
            --cluster ${CLUSTER_NAME} \
            --services ${SERVICE_NAME} \
            --region ${REGION}
        echo -e "${GREEN}✓ Deployment complete!${NC}"
    fi
else
    echo -e "\n${RED}=== ECS Service Update Failed ===${NC}"
    exit 1
fi
