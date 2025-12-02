#!/bin/bash
# Update ECS task definition with fresh image digest
# Usage: ./update-task-definition.sh <service-name> [cluster-name] [region]

set -e

SERVICE_NAME=$1
CLUSTER_NAME=${2:-my-cluster}
REGION=${3:-ap-southeast-1}

if [ -z "$SERVICE_NAME" ]; then
    echo "Error: Service name is required"
    echo "Usage: $0 <service-name> [cluster-name] [region]"
    exit 1
fi

echo "🔍 Fetching current task definition for $SERVICE_NAME..."

# Get current task definition ARN
TASK_DEF_ARN=$(aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --region "$REGION" \
    --query 'services[0].taskDefinition' \
    --output text)

if [ -z "$TASK_DEF_ARN" ] || [ "$TASK_DEF_ARN" = "None" ]; then
    echo "❌ Error: Could not find task definition for service $SERVICE_NAME"
    exit 1
fi

echo "📋 Current task definition: $TASK_DEF_ARN"

# Get task definition JSON and clean it up
echo "🔧 Preparing new task definition..."

TASK_DEF_JSON=$(aws ecs describe-task-definition \
    --task-definition "$TASK_DEF_ARN" \
    --region "$REGION" \
    --query 'taskDefinition')

# Remove fields that aren't needed for registration
CLEAN_TASK_DEF=$(echo "$TASK_DEF_JSON" | jq 'del(
    .taskDefinitionArn,
    .revision,
    .status,
    .requiresAttributes,
    .compatibilities,
    .registeredAt,
    .registeredBy
)')

# Write to temp file
TEMP_FILE=$(mktemp)
echo "$CLEAN_TASK_DEF" > "$TEMP_FILE"

echo "📝 Registering new task definition..."

# Register new task definition
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json "file://$TEMP_FILE" \
    --region "$REGION" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

# Clean up temp file
rm -f "$TEMP_FILE"

if [ -z "$NEW_TASK_DEF_ARN" ] || [ "$NEW_TASK_DEF_ARN" = "None" ]; then
    echo "❌ Error: Failed to register new task definition"
    exit 1
fi

echo "✅ New task definition registered: $NEW_TASK_DEF_ARN"

# Update service with new task definition
echo "🚀 Updating ECS service..."

aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_NAME" \
    --task-definition "$NEW_TASK_DEF_ARN" \
    --force-new-deployment \
    --region "$REGION" \
    --query 'service.{Service:serviceName,Status:status,TaskDef:taskDefinition,Running:runningCount,Desired:desiredCount}' \
    --output table

echo ""
echo "✅ Service update initiated successfully!"
echo ""
echo "📊 Monitor deployment:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION"
echo ""
echo "📝 View logs:"
echo "   aws logs tail /ecs/$SERVICE_NAME --follow --region $REGION"
