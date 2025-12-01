#!/bin/bash

# Automated AWS IoT Infrastructure Status Checker
# Checks the status of all deployed services

set -e

echo "======================================"
echo "AWS IoT Infrastructure Status Check"
echo "======================================"
echo ""
date
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check status
check_status() {
    local actual="$1"
    local expected="$2"
    local service="$3"

    if [ "$actual" == "$expected" ]; then
        echo -e "${GREEN}✓${NC} $service: $actual"
        return 0
    else
        echo -e "${RED}✗${NC} $service: $actual (expected: $expected)"
        return 1
    fi
}

# Function to show info
show_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

# Track overall status
ALL_GOOD=0

# 1. RDS PostgreSQL Database
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "1. RDS PostgreSQL Database"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

RDS_STATUS=$(aws rds describe-db-instances \
  --db-instance-identifier iot-postgres-db \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text 2>/dev/null || echo "NOT_FOUND")

if check_status "$RDS_STATUS" "available" "Status"; then
    RDS_ENDPOINT=$(aws rds describe-db-instances \
      --db-instance-identifier iot-postgres-db \
      --query 'DBInstances[0].Endpoint.Address' \
      --output text 2>/dev/null)
    show_info "Endpoint: $RDS_ENDPOINT"

    RDS_ENGINE=$(aws rds describe-db-instances \
      --db-instance-identifier iot-postgres-db \
      --query 'DBInstances[0].EngineVersion' \
      --output text 2>/dev/null)
    show_info "Engine: PostgreSQL $RDS_ENGINE"
else
    ALL_GOOD=1
fi
echo ""

# 2. RDS Proxy
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "2. RDS Proxy"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

PROXY_STATUS=$(aws rds describe-db-proxies \
  --db-proxy-name iot-rds-proxy \
  --query 'DBProxies[0].Status' \
  --output text 2>/dev/null || echo "NOT_FOUND")

if check_status "$PROXY_STATUS" "available" "Status"; then
    PROXY_ENDPOINT=$(aws rds describe-db-proxies \
      --db-proxy-name iot-rds-proxy \
      --query 'DBProxies[0].Endpoint' \
      --output text 2>/dev/null)
    show_info "Endpoint: $PROXY_ENDPOINT"

    # Check proxy targets
    TARGET_STATUS=$(aws rds describe-db-proxy-targets \
      --db-proxy-name iot-rds-proxy \
      --query 'Targets[0].TargetHealth.State' \
      --output text 2>/dev/null || echo "UNKNOWN")

    if [ "$TARGET_STATUS" == "AVAILABLE" ]; then
        echo -e "${GREEN}✓${NC} Target: $TARGET_STATUS"
    else
        echo -e "${RED}✗${NC} Target: $TARGET_STATUS"
        ALL_GOOD=1
    fi
else
    ALL_GOOD=1
fi
echo ""

# 3. Lambda Function
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "3. Lambda Function"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

LAMBDA_STATE=$(aws lambda get-function \
  --function-name iot_ts_handler \
  --query 'Configuration.State' \
  --output text 2>/dev/null || echo "NOT_FOUND")

if check_status "$LAMBDA_STATE" "Active" "State"; then
    LAMBDA_RUNTIME=$(aws lambda get-function \
      --function-name iot_ts_handler \
      --query 'Configuration.Runtime' \
      --output text 2>/dev/null)
    show_info "Runtime: $LAMBDA_RUNTIME"

    LAMBDA_UPDATED=$(aws lambda get-function \
      --function-name iot_ts_handler \
      --query 'Configuration.LastModified' \
      --output text 2>/dev/null)
    show_info "Last updated: $LAMBDA_UPDATED"

    # Check invocations in last hour
    LAMBDA_INVOCATIONS=$(aws cloudwatch get-metric-statistics \
      --namespace AWS/Lambda \
      --metric-name Invocations \
      --dimensions Name=FunctionName,Value=iot_ts_handler \
      --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
      --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
      --period 3600 \
      --statistics Sum \
      --query 'Datapoints[0].Sum' \
      --output text 2>/dev/null || echo "0")

    if [ "$LAMBDA_INVOCATIONS" == "None" ] || [ -z "$LAMBDA_INVOCATIONS" ]; then
        LAMBDA_INVOCATIONS="0"
    fi

    show_info "Invocations (last hour): $LAMBDA_INVOCATIONS"

    # Check errors
    LAMBDA_ERRORS=$(aws cloudwatch get-metric-statistics \
      --namespace AWS/Lambda \
      --metric-name Errors \
      --dimensions Name=FunctionName,Value=iot_ts_handler \
      --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
      --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
      --period 3600 \
      --statistics Sum \
      --query 'Datapoints[0].Sum' \
      --output text 2>/dev/null || echo "0")

    if [ "$LAMBDA_ERRORS" == "None" ] || [ -z "$LAMBDA_ERRORS" ]; then
        LAMBDA_ERRORS="0"
    fi

    if [ "$LAMBDA_ERRORS" == "0" ] || [ "$LAMBDA_ERRORS" == "0.0" ]; then
        echo -e "${GREEN}✓${NC} Errors (last hour): $LAMBDA_ERRORS"
    else
        echo -e "${RED}✗${NC} Errors (last hour): $LAMBDA_ERRORS"
        ALL_GOOD=1
    fi
else
    ALL_GOOD=1
fi
echo ""

# 4. ECS Fargate Service
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "4. ECS Fargate Service"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

ECS_STATUS=$(aws ecs describe-services \
  --cluster iot-cluster \
  --services backend-service \
  --query 'services[0].status' \
  --output text 2>/dev/null || echo "NOT_FOUND")

if check_status "$ECS_STATUS" "ACTIVE" "Status"; then
    ECS_DESIRED=$(aws ecs describe-services \
      --cluster iot-cluster \
      --services backend-service \
      --query 'services[0].desiredCount' \
      --output text 2>/dev/null)

    ECS_RUNNING=$(aws ecs describe-services \
      --cluster iot-cluster \
      --services backend-service \
      --query 'services[0].runningCount' \
      --output text 2>/dev/null)

    show_info "Desired tasks: $ECS_DESIRED"

    if [ "$ECS_RUNNING" == "$ECS_DESIRED" ]; then
        echo -e "${GREEN}✓${NC} Running tasks: $ECS_RUNNING"
    else
        echo -e "${YELLOW}⚠${NC} Running tasks: $ECS_RUNNING (desired: $ECS_DESIRED)"
        ALL_GOOD=1
    fi
else
    ALL_GOOD=1
fi
echo ""

# 5. IoT Core
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "5. IoT Core"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

IOT_THING=$(aws iot describe-thing \
  --thing-name sensor-device-001 \
  --query 'thingName' \
  --output text 2>/dev/null || echo "NOT_FOUND")

check_status "$IOT_THING" "sensor-device-001" "Thing" || ALL_GOOD=1

# Check certificate
cd "$(dirname "$0")/../infra" 2>/dev/null || cd infra 2>/dev/null || true
if [ -f "terraform.tfstate" ] || command -v terraform &> /dev/null; then
    CERT_ARN=$(terraform output -raw iot_certificate_arn 2>/dev/null || echo "")
    if [ -n "$CERT_ARN" ]; then
        CERT_ID=$(echo "$CERT_ARN" | cut -d'/' -f2)
        CERT_STATUS=$(aws iot describe-certificate \
          --certificate-id "$CERT_ID" \
          --query 'certificateDescription.status' \
          --output text 2>/dev/null || echo "UNKNOWN")

        if [ "$CERT_STATUS" == "ACTIVE" ]; then
            echo -e "${GREEN}✓${NC} Certificate: $CERT_STATUS"
        else
            echo -e "${RED}✗${NC} Certificate: $CERT_STATUS"
            ALL_GOOD=1
        fi
    fi
fi
cd - > /dev/null 2>&1 || true

# Check Topic Rule
IOT_RULE_DISABLED=$(aws iot get-topic-rule \
  --rule-name iot_to_lambda \
  --query 'rule.ruleDisabled' \
  --output text 2>/dev/null || echo "UNKNOWN")

if [ "$IOT_RULE_DISABLED" == "False" ] || [ "$IOT_RULE_DISABLED" == "false" ]; then
    echo -e "${GREEN}✓${NC} Topic Rule: Enabled"
else
    echo -e "${RED}✗${NC} Topic Rule: Disabled or not found"
    ALL_GOOD=1
fi

# Get IoT endpoint
IOT_ENDPOINT=$(cd "$(dirname "$0")/../infra" 2>/dev/null && terraform output -raw iot_endpoint 2>/dev/null || \
               cd infra 2>/dev/null && terraform output -raw iot_endpoint 2>/dev/null || \
               aws iot describe-endpoint --endpoint-type iot:Data-ATS --query 'endpointAddress' --output text 2>/dev/null)

if [ -n "$IOT_ENDPOINT" ] && [ "$IOT_ENDPOINT" != "null" ]; then
    show_info "Endpoint: $IOT_ENDPOINT"
fi
echo ""

# 6. VPC & Networking
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "6. VPC & Networking"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Get VPC ID
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=main_vpc" \
  --query 'Vpcs[0].VpcId' \
  --output text 2>/dev/null || echo "")

if [ -n "$VPC_ID" ] && [ "$VPC_ID" != "None" ]; then
    echo -e "${GREEN}✓${NC} VPC ID: $VPC_ID"

    # Check NAT Gateway
    NAT_STATE=$(aws ec2 describe-nat-gateways \
      --filter "Name=vpc-id,Values=$VPC_ID" \
      --query 'NatGateways[0].State' \
      --output text 2>/dev/null || echo "NOT_FOUND")

    if [ "$NAT_STATE" == "available" ]; then
        echo -e "${GREEN}✓${NC} NAT Gateway: $NAT_STATE"
    else
        echo -e "${RED}✗${NC} NAT Gateway: $NAT_STATE"
        ALL_GOOD=1
    fi
else
    echo -e "${RED}✗${NC} VPC: Not found"
    ALL_GOOD=1
fi
echo ""

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Summary"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $ALL_GOOD -eq 0 ]; then
    echo -e "${GREEN}✓ All services are running normally!${NC}"
    echo ""
    echo "Next steps:"
    echo "  • View Lambda logs: aws logs tail /aws/lambda/iot_ts_handler --follow"
    echo "  • Test IoT: Publish to 'sensors/test' topic in AWS Console"
    echo "  • Monitor metrics: https://console.aws.amazon.com/cloudwatch/"
else
    echo -e "${YELLOW}⚠ Some services need attention${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  • Check detailed logs: aws logs tail /aws/lambda/iot_ts_handler --follow"
    echo "  • Review deployment: cd infra/ && terraform plan"
    echo "  • See monitoring guide: MONITORING_GUIDE.md"
fi

echo ""
echo "======================================"
echo "Status check completed at $(date)"
echo "======================================"

exit $ALL_GOOD
