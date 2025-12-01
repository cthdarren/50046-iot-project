.PHONY: help init plan apply destroy validate fmt output clean check-drift logs status

# Configuration
REGION ?= ap-southeast-1

# Colors
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m

help: ## Show this help message
	@echo "$(BLUE)=== 50046 IoT Project - Infrastructure Management ===$(NC)"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make init        # Initialize Terraform"
	@echo "  make plan        # Preview changes"
	@echo "  make apply       # Apply infrastructure"
	@echo "  make output      # Show all outputs"

init: ## Initialize Terraform
	@echo "$(YELLOW)Initializing Terraform...$(NC)"
	terraform init
	@echo "$(GREEN)✓ Initialization complete$(NC)"

validate: ## Validate Terraform configuration
	@echo "$(YELLOW)Validating Terraform configuration...$(NC)"
	terraform validate
	@echo "$(GREEN)✓ Configuration is valid$(NC)"

fmt: ## Format Terraform files
	@echo "$(YELLOW)Formatting Terraform files...$(NC)"
	terraform fmt -recursive
	@echo "$(GREEN)✓ Formatting complete$(NC)"

plan: ## Show execution plan
	@echo "$(YELLOW)Creating execution plan...$(NC)"
	terraform plan
	@echo "$(GREEN)✓ Plan complete$(NC)"

apply: ## Apply infrastructure changes
	@echo "$(YELLOW)Applying infrastructure changes...$(NC)"
	terraform apply
	@echo "$(GREEN)✓ Apply complete$(NC)"
	@echo ""
	@echo "$(YELLOW)Important outputs:$(NC)"
	@$(MAKE) output-summary

destroy: ## Destroy all infrastructure (WARNING: Destructive)
	@echo "$(RED)WARNING: This will destroy all infrastructure!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel, or wait 5 seconds to continue...$(NC)"
	@sleep 5
	terraform destroy

output: ## Show all Terraform outputs
	@terraform output

output-json: ## Show all outputs in JSON format
	@terraform output -json

output-summary: ## Show summary of key outputs
	@echo ""
	@echo "$(BLUE)=== Key Infrastructure Outputs ===$(NC)"
	@echo ""
	@echo "$(YELLOW)ALB URL:$(NC)"
	@terraform output -raw alb_url 2>/dev/null || echo "  Not available"
	@echo ""
	@echo "$(YELLOW)Availability Service:$(NC)"
	@terraform output -raw availability_service_url 2>/dev/null || echo "  Not available"
	@echo ""
	@echo "$(YELLOW)ECR Repository:$(NC)"
	@terraform output -raw ecr_repository_uri 2>/dev/null || echo "  Not available"
	@echo ""
	@echo "$(YELLOW)RDS Endpoint:$(NC)"
	@terraform output -raw rds_proxy_endpoint 2>/dev/null || echo "  Not available"
	@echo ""
	@echo "$(YELLOW)IoT Endpoint:$(NC)"
	@terraform output -raw iot_endpoint 2>/dev/null || echo "  Not available"
	@echo ""

check-drift: ## Check for configuration drift
	@echo "$(YELLOW)Checking for infrastructure drift...$(NC)"
	@terraform plan -detailed-exitcode > /dev/null 2>&1; \
	EXIT_CODE=$$?; \
	if [ $$EXIT_CODE -eq 0 ]; then \
		echo "$(GREEN)✓ No drift detected$(NC)"; \
	elif [ $$EXIT_CODE -eq 2 ]; then \
		echo "$(YELLOW)⚠ Drift detected - run 'make plan' to see details$(NC)"; \
	else \
		echo "$(RED)✗ Error checking drift$(NC)"; \
	fi

status: ## Show infrastructure status
	@echo "$(BLUE)=== Infrastructure Status ===$(NC)"
	@echo ""
	@echo "$(YELLOW)ECS Cluster:$(NC)"
	@aws ecs describe-clusters --clusters my-cluster --region $(REGION) \
		--query 'clusters[0].{Name:clusterName,Status:status,Services:registeredContainerInstancesCount,Tasks:runningTasksCount}' \
		--output table 2>/dev/null || echo "  Not found"
	@echo ""
	@echo "$(YELLOW)ECS Services:$(NC)"
	@aws ecs list-services --cluster my-cluster --region $(REGION) \
		--query 'serviceArns' --output table 2>/dev/null || echo "  Not found"
	@echo ""
	@echo "$(YELLOW)ALB Status:$(NC)"
	@aws elbv2 describe-load-balancers --region $(REGION) \
		--query 'LoadBalancers[?LoadBalancerName==`iot-alb`].{Name:LoadBalancerName,DNS:DNSName,State:State.Code}' \
		--output table 2>/dev/null || echo "  Not found"
	@echo ""
	@echo "$(YELLOW)RDS Status:$(NC)"
	@aws rds describe-db-instances --region $(REGION) \
		--query 'DBInstances[0].{Name:DBInstanceIdentifier,Status:DBInstanceStatus,Endpoint:Endpoint.Address}' \
		--output table 2>/dev/null || echo "  Not found"

logs-lambda: ## View Lambda function logs
	@echo "$(YELLOW)Fetching Lambda logs...$(NC)"
	@LAMBDA_NAME=$$(terraform output -raw lambda_name 2>/dev/null) && \
	LOG_GROUP="/aws/lambda/$$LAMBDA_NAME" && \
	aws logs tail $$LOG_GROUP --follow --region $(REGION)

list-resources: ## List all managed resources
	@echo "$(YELLOW)Listing Terraform-managed resources...$(NC)"
	@terraform state list

show-resource: ## Show details of a resource (usage: make show-resource RESOURCE=aws_ecs_cluster.main)
	@if [ -z "$(RESOURCE)" ]; then \
		echo "$(RED)Error: RESOURCE parameter required$(NC)"; \
		echo "Usage: make show-resource RESOURCE=aws_ecs_cluster.main"; \
		exit 1; \
	fi
	@terraform state show $(RESOURCE)

graph: ## Generate dependency graph (requires graphviz)
	@echo "$(YELLOW)Generating dependency graph...$(NC)"
	@terraform graph | dot -Tpng > infrastructure-graph.png && \
	echo "$(GREEN)✓ Graph saved to infrastructure-graph.png$(NC)" || \
	echo "$(RED)✗ Failed (install graphviz: brew install graphviz)$(NC)"

clean: ## Clean Terraform cache and state backups
	@echo "$(YELLOW)Cleaning Terraform cache...$(NC)"
	@rm -rf .terraform/
	@rm -f terraform.tfstate.*.backup
	@rm -f infrastructure-graph.png
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

get-iot-certs: ## Display IoT certificates (use carefully)
	@echo "$(YELLOW)IoT Device Certificates$(NC)"
	@echo ""
	@echo "$(RED)WARNING: These are sensitive values!$(NC)"
	@echo ""
	@echo "$(YELLOW)Certificate PEM:$(NC)"
	@terraform output -raw iot_certificate_pem
	@echo ""
	@echo ""
	@echo "$(YELLOW)Private Key:$(NC)"
	@terraform output -raw iot_private_key
	@echo ""

save-iot-certs: ## Save IoT certificates to files
	@echo "$(YELLOW)Saving IoT certificates...$(NC)"
	@mkdir -p ../iot-certificates
	@terraform output -raw iot_certificate_pem > ../iot-certificates/device-cert.pem
	@terraform output -raw iot_private_key > ../iot-certificates/device-private.key
	@terraform output -raw iot_public_key > ../iot-certificates/device-public.key
	@chmod 600 ../iot-certificates/device-private.key
	@echo "$(GREEN)✓ Certificates saved to ../iot-certificates/$(NC)"
	@echo ""
	@echo "$(YELLOW)Files created:$(NC)"
	@echo "  - device-cert.pem"
	@echo "  - device-private.key"
	@echo "  - device-public.key"

check-health: ## Health check all services
	@echo "$(YELLOW)Running health checks...$(NC)"
	@echo ""
	@echo "$(BLUE)Availability Service:$(NC)"
	@ALB_URL=$$(terraform output -raw alb_url 2>/dev/null) && \
	curl -s -w "  Status: %{http_code}\n" $$ALB_URL/availability/health || echo "  $(RED)Failed$(NC)"
	@echo ""

cost-estimate: ## Rough cost estimate (requires terraform-cost-estimation)
	@echo "$(YELLOW)Generating cost estimate...$(NC)"
	@terraform plan -out=tfplan.binary > /dev/null 2>&1
	@terraform show -json tfplan.binary > plan.json
	@echo "$(YELLOW)Plan saved to plan.json - upload to https://cost.modules.tf for estimate$(NC)"
	@rm -f tfplan.binary

backup-state: ## Backup Terraform state file
	@echo "$(YELLOW)Backing up Terraform state...$(NC)"
	@cp terraform.tfstate terraform.tfstate.backup.$$(date +%Y%m%d-%H%M%S)
	@echo "$(GREEN)✓ State backed up$(NC)"

check-aws: ## Verify AWS credentials and configuration
	@echo "$(YELLOW)Checking AWS configuration...$(NC)"
	@echo ""
	@echo "$(BLUE)AWS Identity:$(NC)"
	@aws sts get-caller-identity --output table
	@echo ""
	@echo "$(BLUE)Region:$(NC) $(REGION)"
	@echo ""
	@echo "$(BLUE)Default Region:$(NC)"
	@aws configure get region

import: ## Import existing AWS resource (usage: make import RESOURCE=aws_ecs_cluster.main ID=my-cluster)
	@if [ -z "$(RESOURCE)" ] || [ -z "$(ID)" ]; then \
		echo "$(RED)Error: RESOURCE and ID parameters required$(NC)"; \
		echo "Usage: make import RESOURCE=aws_ecs_cluster.main ID=my-cluster"; \
		exit 1; \
	fi
	@terraform import $(RESOURCE) $(ID)

refresh: ## Refresh Terraform state
	@echo "$(YELLOW)Refreshing Terraform state...$(NC)"
	@terraform refresh
	@echo "$(GREEN)✓ State refreshed$(NC)"

unlock: ## Force unlock Terraform state (use with caution)
	@if [ -z "$(LOCK_ID)" ]; then \
		echo "$(RED)Error: LOCK_ID parameter required$(NC)"; \
		echo "Usage: make unlock LOCK_ID=<lock-id>"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Force unlocking state...$(NC)"
	@terraform force-unlock $(LOCK_ID)

taint: ## Mark resource for recreation (usage: make taint RESOURCE=aws_ecs_service.availability_service)
	@if [ -z "$(RESOURCE)" ]; then \
		echo "$(RED)Error: RESOURCE parameter required$(NC)"; \
		echo "Usage: make taint RESOURCE=aws_ecs_service.availability_service"; \
		exit 1; \
	fi
	@terraform taint $(RESOURCE)

untaint: ## Remove taint from resource (usage: make untaint RESOURCE=aws_ecs_service.availability_service)
	@if [ -z "$(RESOURCE)" ]; then \
		echo "$(RED)Error: RESOURCE parameter required$(NC)"; \
		echo "Usage: make untaint RESOURCE=aws_ecs_service.availability_service"; \
		exit 1; \
	fi
	@terraform untaint $(RESOURCE)

info: ## Display project information
	@echo "$(BLUE)=== 50046 IoT Project - Infrastructure ===$(NC)"
	@echo ""
	@echo "$(YELLOW)Terraform Version:$(NC)"
	@terraform version | head -n 1
	@echo ""
	@echo "$(YELLOW)AWS Region:$(NC) $(REGION)"
	@echo ""
	@echo "$(YELLOW)Key Resources:$(NC)"
	@echo "  - ECS Cluster: my-cluster"
	@echo "  - ECR Repository: iot"
	@echo "  - Application Load Balancer: iot-alb"
	@echo "  - RDS Database: PostgreSQL"
	@echo "  - Lambda: IoT message handler"
	@echo ""
	@echo "$(YELLOW)Services:$(NC)"
	@echo "  - availability-service"
	@echo "  - analytics-service"
	@echo ""
	@echo "For more commands, run: make help
