#!/bin/bash

# Pre-deployment validation script for AWS IoT Project
# This script checks prerequisites and sets up required AWS resources
# before running terraform apply

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=============================================="
echo "AWS IoT Project - Pre-Deployment Validation"
echo "=============================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any checks fail
CHECKS_FAILED=0

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    CHECKS_FAILED=1
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo "  $1"
}

echo "Step 1: Checking prerequisites..."
echo "-------------------------------------------"

# Check if AWS CLI is installed
if command -v aws &> /dev/null; then
    print_success "AWS CLI is installed"
    AWS_VERSION=$(aws --version 2>&1 | cut -d' ' -f1)
    print_info "$AWS_VERSION"
else
    print_error "AWS CLI is not installed"
    print_info "Install: https://aws.amazon.com/cli/"
fi

# Check if Terraform is installed
if command -v terraform &> /dev/null; then
    print_success "Terraform is installed"
    TF_VERSION=$(terraform version -json 2>/dev/null | grep -o '"terraform_version":"[^"]*"' | cut -d'"' -f4 || terraform version | head -n1)
    print_info "$TF_VERSION"
else
    print_error "Terraform is not installed"
    print_info "Install: https://www.terraform.io/downloads"
fi

echo ""
echo "Step 2: Validating AWS credentials..."
echo "-------------------------------------------"

# Check if AWS credentials are configured
if aws sts get-caller-identity &> /dev/null; then
    print_success "AWS credentials are configured"
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    AWS_USER=$(aws sts get-caller-identity --query Arn --output text 2>/dev/null)
    print_info "Account ID: $AWS_ACCOUNT"
    print_info "Identity: $AWS_USER"
else
    print_error "AWS credentials are not configured"
    print_info "Run: aws configure"
    print_info "Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
fi

echo ""
echo "Step 3: Checking RDS credentials secret..."
echo "-------------------------------------------"

# Check if RDS credentials secret exists
if aws secretsmanager describe-secret --secret-id rds_credentials &> /dev/null; then
    print_success "RDS credentials secret exists in AWS Secrets Manager"

    # Try to get the secret value to verify it's valid JSON
    if SECRET_VALUE=$(aws secretsmanager get-secret-value --secret-id rds_credentials --query SecretString --output text 2>/dev/null); then
        if echo "$SECRET_VALUE" | jq -e '.username and .password' &> /dev/null 2>&1; then
            USERNAME=$(echo "$SECRET_VALUE" | jq -r '.username' 2>/dev/null)
            print_success "Secret contains valid username and password"
            print_info "Username: $USERNAME"
        else
            print_error "Secret exists but does not contain 'username' and 'password' fields"
            print_info "Expected format: {\"username\":\"...\",\"password\":\"...\"}"
        fi
    fi
else
    print_error "RDS credentials secret NOT found in AWS Secrets Manager"
    echo ""
    print_info "You must create this secret before running terraform apply."
    print_info "Run the following command:"
    echo ""
    echo -e "${YELLOW}aws secretsmanager create-secret \\${NC}"
    echo -e "${YELLOW}  --name rds_credentials \\${NC}"
    echo -e "${YELLOW}  --secret-string '{\"username\":\"iot_master\",\"password\":\"CHANGE_THIS_PASSWORD\"}'${NC}"
    echo ""
    print_warning "Remember to change the password to a secure one!"
    echo ""
fi

echo ""
echo "Step 4: Checking AWS service-linked roles..."
echo "-------------------------------------------"

# Check if RDS service-linked role exists
if aws iam get-role --role-name AWSServiceRoleForRDS &> /dev/null; then
    print_success "RDS service-linked role exists"
else
    print_warning "RDS service-linked role not found"
    print_info "Run: ./setup-service-linked-roles.sh"
    print_info "Or AWS will create it automatically during deployment"
fi

# Check if ECS service-linked role exists
if aws iam get-role --role-name AWSServiceRoleForECS &> /dev/null; then
    print_success "ECS service-linked role exists"
else
    print_warning "ECS service-linked role not found (will be created automatically)"
fi

echo ""
echo "Step 5: Checking Terraform state..."
echo "-------------------------------------------"

cd "$SCRIPT_DIR"

# Check if Terraform has been initialized
if [ -d ".terraform" ]; then
    print_success "Terraform has been initialized"
else
    print_warning "Terraform has not been initialized"
    print_info "Run: terraform init"
fi

# Check if lambda.zip exists (required for Lambda function)
if [ -f "lambda.zip" ]; then
    print_success "lambda.zip exists"
    LAMBDA_SIZE=$(du -h lambda.zip | cut -f1)
    print_info "Size: $LAMBDA_SIZE"
else
    print_warning "lambda.zip does not exist"
    print_info "Lambda function deployment will fail without this file"
    print_info "Create a placeholder: cd ../lambda && zip -r ../infra/lambda.zip ."
fi

echo ""
echo "Step 6: Validating Terraform configuration..."
echo "-------------------------------------------"

# Run terraform validate (only if initialized)
if [ -d ".terraform" ]; then
    if terraform validate &> /dev/null; then
        print_success "Terraform configuration is valid"
    else
        print_error "Terraform configuration has errors"
        echo ""
        terraform validate
        echo ""
    fi
else
    print_warning "Skipping validation (run 'terraform init' first)"
fi

echo ""
echo "=============================================="
echo "Summary"
echo "=============================================="
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    echo ""
    echo "You are ready to deploy. Run the following commands:"
    echo ""
    echo "  cd $SCRIPT_DIR"

    if [ ! -d ".terraform" ]; then
        echo "  terraform init"
    fi

    echo "  ./setup-service-linked-roles.sh  # Optional: Create service-linked roles"
    echo "  terraform plan                    # Review the deployment plan"
    echo "  terraform apply                   # Deploy to AWS"
    echo ""
else
    echo -e "${RED}Some checks failed!${NC}"
    echo ""
    echo "Please resolve the issues above before running terraform apply."
    echo ""
    exit 1
fi

echo "=============================================="
echo ""
