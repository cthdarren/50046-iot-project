#!/bin/bash

# Script to create AWS Secrets Manager secret for RDS credentials
# This must be run BEFORE terraform apply

set -e

echo "=============================================="
echo "AWS Secrets Manager - RDS Credentials Setup"
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

# Check if secret already exists
if aws secretsmanager describe-secret --secret-id rds_credentials &> /dev/null; then
    echo "⚠️  WARNING: Secret 'rds_credentials' already exists!"
    echo ""
    read -p "Do you want to update it? (yes/no): " UPDATE_CONFIRM

    if [ "$UPDATE_CONFIRM" != "yes" ]; then
        echo "Aborted. No changes made."
        exit 0
    fi

    UPDATE_MODE=true
else
    UPDATE_MODE=false
fi

echo ""
echo "=============================================="
echo "RDS Database Credentials"
echo "=============================================="
echo ""
echo "Please enter the credentials for your RDS PostgreSQL database."
echo "These will be stored securely in AWS Secrets Manager."
echo ""

# Get username
read -p "Enter database username [default: iot_master]: " DB_USERNAME
DB_USERNAME=${DB_USERNAME:-iot_master}

# Get password
while true; do
    echo ""
    read -sp "Enter database password (min 8 characters): " DB_PASSWORD
    echo ""

    if [ ${#DB_PASSWORD} -lt 8 ]; then
        echo "❌ Password must be at least 8 characters long"
        continue
    fi

    read -sp "Confirm password: " DB_PASSWORD_CONFIRM
    echo ""

    if [ "$DB_PASSWORD" != "$DB_PASSWORD_CONFIRM" ]; then
        echo "❌ Passwords do not match. Try again."
        continue
    fi

    break
done

echo ""
echo "=============================================="
echo "Creating Secret"
echo "=============================================="
echo ""

# Create JSON secret string
SECRET_STRING=$(cat <<EOF
{
  "username": "$DB_USERNAME",
  "password": "$DB_PASSWORD"
}
EOF
)

# Create or update the secret
if [ "$UPDATE_MODE" = true ]; then
    echo "Updating existing secret..."

    aws secretsmanager update-secret \
        --secret-id rds_credentials \
        --secret-string "$SECRET_STRING" \
        > /dev/null

    echo "✅ Secret 'rds_credentials' updated successfully!"
else
    echo "Creating new secret..."

    aws secretsmanager create-secret \
        --name rds_credentials \
        --description "RDS PostgreSQL credentials for IoT project" \
        --secret-string "$SECRET_STRING" \
        > /dev/null

    echo "✅ Secret 'rds_credentials' created successfully!"
fi

echo ""
echo "Secret Details:"
echo "  Name: rds_credentials"
echo "  Region: $AWS_REGION"
echo "  Username: $DB_USERNAME"
echo ""

echo "=============================================="
echo "Next Steps"
echo "=============================================="
echo ""
echo "1. Run Terraform to deploy infrastructure:"
echo "   cd infra/"
echo "   terraform init"
echo "   terraform plan"
echo "   terraform apply"
echo ""
echo "2. After deployment, extract IoT certificates:"
echo "   cd .."
echo "   ./scripts/save-iot-certs.sh"
echo ""
echo "⚠️  IMPORTANT: Keep your database password secure!"
echo "   Do not commit it to version control."
echo ""
echo "=============================================="
echo ""

# Verify the secret was created correctly
if aws secretsmanager get-secret-value --secret-id rds_credentials --query SecretString --output text | jq -e '.username and .password' &> /dev/null; then
    echo "✅ Secret validation passed - credentials are correctly formatted"
else
    echo "⚠️  Warning: Could not verify secret format (jq might not be installed)"
fi

echo ""
