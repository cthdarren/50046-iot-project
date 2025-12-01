#!/bin/bash

# Script to create AWS service-linked roles required for the infrastructure
# This script creates service-linked roles that are needed before running terraform apply

set -e

echo "=============================================="
echo "AWS Service-Linked Roles Setup"
echo "=============================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials are not configured"
    echo "Run: aws configure"
    exit 1
fi

echo "AWS Account Information:"
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
echo "  Account ID: $AWS_ACCOUNT"
echo "  Region: $AWS_REGION"
echo ""

echo "=============================================="
echo "Creating Service-Linked Roles"
echo "=============================================="
echo ""

# Create RDS service-linked role
echo "1. Checking RDS service-linked role..."
if aws iam get-role --role-name AWSServiceRoleForRDS &> /dev/null; then
    echo "   ✓ RDS service-linked role already exists"
else
    echo "   Creating RDS service-linked role..."
    if aws iam create-service-linked-role --aws-service-name rds.amazonaws.com &> /dev/null; then
        echo "   ✓ RDS service-linked role created successfully"
    else
        echo "   ⚠️  Warning: Could not create RDS service-linked role"
        echo "   This might already exist or you may lack permissions"
        echo "   The role will be created automatically by AWS when needed"
    fi
fi

echo ""

# Create ECS service-linked role
echo "2. Checking ECS service-linked role..."
if aws iam get-role --role-name AWSServiceRoleForECS &> /dev/null; then
    echo "   ✓ ECS service-linked role already exists"
else
    echo "   Creating ECS service-linked role..."
    if aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com &> /dev/null; then
        echo "   ✓ ECS service-linked role created successfully"
    else
        echo "   ⚠️  Warning: Could not create ECS service-linked role"
        echo "   This might already exist or you may lack permissions"
    fi
fi

echo ""

# Create ElastiCache service-linked role (if using caching in future)
echo "3. Checking ElastiCache service-linked role..."
if aws iam get-role --role-name AWSServiceRoleForElastiCache &> /dev/null; then
    echo "   ✓ ElastiCache service-linked role already exists"
else
    echo "   ⚠️  ElastiCache service-linked role not found (optional)"
fi

echo ""
echo "=============================================="
echo "Summary"
echo "=============================================="
echo ""
echo "Service-linked roles setup complete!"
echo ""
echo "Next steps:"
echo "  1. Create RDS credentials secret: ./setup-secrets.sh"
echo "  2. Validate setup: ./pre-deploy.sh"
echo "  3. Deploy infrastructure: terraform apply"
echo ""
echo "=============================================="
echo ""
