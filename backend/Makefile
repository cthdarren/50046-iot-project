.PHONY: help build-availability build-analytics push-availability push-analytics deploy-availability deploy-analytics ecr-login clean test-availability test-analytics run-availability run-analytics logs-availability logs-analytics create-log-group check-logs status-availability status-analytics list-images watch-deployment-availability watch-deployment-analytics wait-for-stable-availability wait-for-stable-analytics

# Configuration
CLUSTER_NAME = my-cluster
ECR_REPO_NAME = iot
AVAILABILITY_SERVICE = availability-service
ANALYTICS_SERVICE = analytics-service
REGION ?= ap-southeast-1
INFRA_DIR = ../infra

# Colors
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m

help: ## Show this help message
	@echo "$(BLUE)=== 50046 IoT Project - Backend Deployment ===$(NC)"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make deploy-availability    # Deploy availability service"
	@echo "  make deploy-analytics        # Deploy analytics service"
	@echo "  make deploy-all              # Deploy both services"

# =========================================================
# Availability Service
# =========================================================

build-availability: ## Build availability-service Docker image
	@echo "$(YELLOW)Building $(AVAILABILITY_SERVICE) Docker image...$(NC)"
	docker build -f $(AVAILABILITY_SERVICE)/Dockerfile -t $(AVAILABILITY_SERVICE):latest .
	@echo "$(GREEN)✓ Build complete$(NC)"

push-availability: ecr-login build-availability ## Build and push availability-service to ECR
	@echo "$(YELLOW)Pushing $(AVAILABILITY_SERVICE) to ECR...$(NC)"
	@ECR_URI=$$(cd $(INFRA_DIR) && terraform output -raw ecr_repository_uri) && \
	TIMESTAMP=$$(date +%Y%m%d-%H%M%S) && \
	GIT_SHA=$$(git rev-parse --short HEAD 2>/dev/null || echo "local") && \
	echo "$(YELLOW)Tagging images...$(NC)" && \
	docker tag $(AVAILABILITY_SERVICE):latest $${ECR_URI}:latest && \
	docker tag $(AVAILABILITY_SERVICE):latest $${ECR_URI}:availability-latest && \
	docker tag $(AVAILABILITY_SERVICE):latest $${ECR_URI}:availability-$${TIMESTAMP} && \
	docker tag $(AVAILABILITY_SERVICE):latest $${ECR_URI}:availability-$${GIT_SHA} && \
	echo "$(GREEN)✓ Tagged: latest$(NC)" && \
	echo "$(GREEN)✓ Tagged: availability-latest$(NC)" && \
	echo "$(GREEN)✓ Tagged: availability-$${TIMESTAMP}$(NC)" && \
	echo "$(GREEN)✓ Tagged: availability-$${GIT_SHA}$(NC)" && \
	echo "$(YELLOW)Pushing to ECR...$(NC)" && \
	docker push $${ECR_URI}:latest && \
	docker push $${ECR_URI}:availability-latest && \
	docker push $${ECR_URI}:availability-$${TIMESTAMP} && \
	docker push $${ECR_URI}:availability-$${GIT_SHA} && \
	echo "" && \
	echo "$(GREEN)=== Push successful! ===$(NC)" && \
	echo "$(GREEN)Images pushed:$(NC)" && \
	echo "  - $${ECR_URI}:latest" && \
	echo "  - $${ECR_URI}:availability-latest" && \
	echo "  - $${ECR_URI}:availability-$${TIMESTAMP}" && \
	echo "  - $${ECR_URI}:availability-$${GIT_SHA}"

deploy-availability: push-availability ## Build, push, and deploy availability-service
	@echo ""
	@echo "$(YELLOW)Updating ECS service: $(AVAILABILITY_SERVICE)...$(NC)"
	@aws ecs update-service \
		--cluster $(CLUSTER_NAME) \
		--service $(AVAILABILITY_SERVICE) \
		--force-new-deployment \
		--region $(REGION) \
		--output table \
		--query 'service.{Service:serviceName,Status:status,Running:runningCount,Desired:desiredCount}' && \
	echo "$(GREEN)✓ ECS service update initiated$(NC)" && \
	echo "" && \
	echo "$(YELLOW)Monitor deployment with:$(NC)" && \
	echo "  make watch-deployment-availability" && \
	echo "" && \
	echo "$(YELLOW)View logs with:$(NC)" && \
	echo "  make logs-availability" && \
	echo "" && \
	echo "$(YELLOW)Check service URL:$(NC)" && \
	echo "  curl \$$(cd $(INFRA_DIR) && terraform output -raw availability_service_url)/availability/health"

status-availability: ## Check availability-service status
	@echo "$(YELLOW)Checking $(AVAILABILITY_SERVICE) status...$(NC)"
	@aws ecs describe-services \
		--cluster $(CLUSTER_NAME) \
		--services $(AVAILABILITY_SERVICE) \
		--region $(REGION) \
		--query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployments:deployments[*].{Status:status,TaskDef:taskDefinition}}' \
		--output table

watch-deployment-availability: ## Watch availability-service deployment
	@watch -n 5 'aws ecs describe-services \
		--cluster $(CLUSTER_NAME) \
		--services $(AVAILABILITY_SERVICE) \
		--region $(REGION) \
		--query "services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployment:deployments[0].status}"'

wait-for-stable-availability: ## Wait for availability-service deployment to stabilize
	@echo "$(YELLOW)Waiting for $(AVAILABILITY_SERVICE) deployment to stabilize...$(NC)"
	@aws ecs wait services-stable \
		--cluster $(CLUSTER_NAME) \
		--services $(AVAILABILITY_SERVICE) \
		--region $(REGION)
	@echo "$(GREEN)✓ Deployment complete!$(NC)"

logs-availability: ## View availability-service logs
	@echo "$(YELLOW)Fetching $(AVAILABILITY_SERVICE) logs...$(NC)"
	@LOG_GROUP="/ecs/$(AVAILABILITY_SERVICE)"; \
	if ! aws logs describe-log-groups --log-group-name-prefix $$LOG_GROUP --region $(REGION) --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$$LOG_GROUP"; then \
		echo "$(YELLOW)Log group $$LOG_GROUP does not exist yet.$(NC)"; \
		echo "$(YELLOW)Check if service has been deployed.$(NC)"; \
		exit 1; \
	else \
		aws logs tail $$LOG_GROUP --follow --region $(REGION); \
	fi

run-availability: ## Run availability-service locally
	@echo "$(YELLOW)Running $(AVAILABILITY_SERVICE) locally on port 8001...$(NC)"
	docker run -p 8001:8001 --env-file ../.env $(AVAILABILITY_SERVICE):latest

test-availability: ## Run availability-service tests
	@echo "$(YELLOW)Running tests for $(AVAILABILITY_SERVICE)...$(NC)"
	docker build -f $(AVAILABILITY_SERVICE)/Dockerfile -t $(AVAILABILITY_SERVICE):test --target test . || \
	echo "$(YELLOW)No test target defined in Dockerfile$(NC)"

# =========================================================
# Analytics Service
# =========================================================

build-analytics: ## Build analytics-service Docker image
	@echo "$(YELLOW)Building $(ANALYTICS_SERVICE) Docker image...$(NC)"
	docker build -f $(ANALYTICS_SERVICE)/Dockerfile -t $(ANALYTICS_SERVICE):latest .
	@echo "$(GREEN)✓ Build complete$(NC)"

push-analytics: ecr-login build-analytics ## Build and push analytics-service to ECR
	@echo "$(YELLOW)Pushing $(ANALYTICS_SERVICE) to ECR...$(NC)"
	@ECR_URI=$$(cd $(INFRA_DIR) && terraform output -raw ecr_repository_uri) && \
	TIMESTAMP=$$(date +%Y%m%d-%H%M%S) && \
	GIT_SHA=$$(git rev-parse --short HEAD 2>/dev/null || echo "local") && \
	echo "$(YELLOW)Tagging images...$(NC)" && \
	docker tag $(ANALYTICS_SERVICE):latest $${ECR_URI}:analytics-latest && \
	docker tag $(ANALYTICS_SERVICE):latest $${ECR_URI}:analytics-$${TIMESTAMP} && \
	docker tag $(ANALYTICS_SERVICE):latest $${ECR_URI}:analytics-$${GIT_SHA} && \
	echo "$(GREEN)✓ Tagged: analytics-latest$(NC)" && \
	echo "$(GREEN)✓ Tagged: analytics-$${TIMESTAMP}$(NC)" && \
	echo "$(GREEN)✓ Tagged: analytics-$${GIT_SHA}$(NC)" && \
	echo "$(YELLOW)Pushing to ECR...$(NC)" && \
	docker push $${ECR_URI}:analytics-latest && \
	docker push $${ECR_URI}:analytics-$${TIMESTAMP} && \
	docker push $${ECR_URI}:analytics-$${GIT_SHA} && \
	echo "" && \
	echo "$(GREEN)=== Push successful! ===$(NC)" && \
	echo "$(GREEN)Images pushed:$(NC)" && \
	echo "  - $${ECR_URI}:analytics-latest" && \
	echo "  - $${ECR_URI}:analytics-$${TIMESTAMP}" && \
	echo "  - $${ECR_URI}:analytics-$${GIT_SHA}"

deploy-analytics: push-analytics ## Build, push, and deploy analytics-service
	@echo ""
	@echo "$(YELLOW)Updating ECS service: $(ANALYTICS_SERVICE)...$(NC)"
	@aws ecs update-service \
		--cluster $(CLUSTER_NAME) \
		--service $(ANALYTICS_SERVICE) \
		--force-new-deployment \
		--region $(REGION) \
		--output table \
		--query 'service.{Service:serviceName,Status:status,Running:runningCount,Desired:desiredCount}' && \
	echo "$(GREEN)✓ ECS service update initiated$(NC)" && \
	echo "" && \
	echo "$(YELLOW)Monitor deployment with:$(NC)" && \
	echo "  make watch-deployment-analytics" && \
	echo "" && \
	echo "$(YELLOW)View logs with:$(NC)" && \
	echo "  make logs-analytics"

status-analytics: ## Check analytics-service status
	@echo "$(YELLOW)Checking $(ANALYTICS_SERVICE) status...$(NC)"
	@aws ecs describe-services \
		--cluster $(CLUSTER_NAME) \
		--services $(ANALYTICS_SERVICE) \
		--region $(REGION) \
		--query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployments:deployments[*].{Status:status,TaskDef:taskDefinition}}' \
		--output table

watch-deployment-analytics: ## Watch analytics-service deployment
	@watch -n 5 'aws ecs describe-services \
		--cluster $(CLUSTER_NAME) \
		--services $(ANALYTICS_SERVICE) \
		--region $(REGION) \
		--query "services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployment:deployments[0].status}"'

wait-for-stable-analytics: ## Wait for analytics-service deployment to stabilize
	@echo "$(YELLOW)Waiting for $(ANALYTICS_SERVICE) deployment to stabilize...$(NC)"
	@aws ecs wait services-stable \
		--cluster $(CLUSTER_NAME) \
		--services $(ANALYTICS_SERVICE) \
		--region $(REGION)
	@echo "$(GREEN)✓ Deployment complete!$(NC)"

logs-analytics: ## View analytics-service logs
	@echo "$(YELLOW)Fetching $(ANALYTICS_SERVICE) logs...$(NC)"
	@LOG_GROUP="/ecs/$(ANALYTICS_SERVICE)"; \
	if ! aws logs describe-log-groups --log-group-name-prefix $$LOG_GROUP --region $(REGION) --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$$LOG_GROUP"; then \
		echo "$(YELLOW)Log group $$LOG_GROUP does not exist yet.$(NC)"; \
		echo "$(YELLOW)Check if service has been deployed.$(NC)"; \
		exit 1; \
	else \
		aws logs tail $$LOG_GROUP --follow --region $(REGION); \
	fi

run-analytics: ## Run analytics-service locally
	@echo "$(YELLOW)Running $(ANALYTICS_SERVICE) locally on port 8002...$(NC)"
	docker run -p 8002:8002 --env-file ../.env $(ANALYTICS_SERVICE):latest

test-analytics: ## Run analytics-service tests
	@echo "$(YELLOW)Running tests for $(ANALYTICS_SERVICE)...$(NC)"
	docker build -f $(ANALYTICS_SERVICE)/Dockerfile -t $(ANALYTICS_SERVICE):test --target test . || \
	echo "$(YELLOW)No test target defined in Dockerfile$(NC)"

# =========================================================
# Shared Commands
# =========================================================

ecr-login: ## Authenticate Docker with ECR
	@echo "$(YELLOW)Authenticating with ECR...$(NC)"
	@AWS_ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text) && \
	aws ecr get-login-password --region $(REGION) | \
	docker login --username AWS --password-stdin $$AWS_ACCOUNT_ID.dkr.ecr.$(REGION).amazonaws.com
	@echo "$(GREEN)✓ Authenticated$(NC)"

list-images: ## List recent ECR images
	@echo "$(YELLOW)Fetching recent ECR images...$(NC)"
	@aws ecr describe-images \
		--repository-name $(ECR_REPO_NAME) \
		--region $(REGION) \
		--query 'sort_by(imageDetails,&imagePushedAt)[-20:].{Tag:imageTags[0],Pushed:imagePushedAt,Size:imageSizeInBytes}' \
		--output table

deploy-all: deploy-availability deploy-analytics ## Deploy both services

build-all: build-availability build-analytics ## Build both services

clean: ## Remove local Docker images
	@echo "$(YELLOW)Cleaning up local images...$(NC)"
	-docker rmi $(AVAILABILITY_SERVICE):latest
	-docker rmi $(ANALYTICS_SERVICE):latest
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

create-log-group: ## Create CloudWatch log groups for ECS services
	@echo "$(YELLOW)Creating CloudWatch log groups...$(NC)"
	@aws logs create-log-group --log-group-name /ecs/$(AVAILABILITY_SERVICE) --region $(REGION) 2>/dev/null && \
		echo "$(GREEN)✓ Log group created: /ecs/$(AVAILABILITY_SERVICE)$(NC)" || \
		echo "$(YELLOW)Log group /ecs/$(AVAILABILITY_SERVICE) already exists$(NC)"
	@aws logs create-log-group --log-group-name /ecs/$(ANALYTICS_SERVICE) --region $(REGION) 2>/dev/null && \
		echo "$(GREEN)✓ Log group created: /ecs/$(ANALYTICS_SERVICE)$(NC)" || \
		echo "$(YELLOW)Log group /ecs/$(ANALYTICS_SERVICE) already exists$(NC)"
	@aws logs put-retention-policy --log-group-name /ecs/$(AVAILABILITY_SERVICE) --retention-in-days 7 --region $(REGION) 2>/dev/null && \
		echo "$(GREEN)✓ Set retention policy: 7 days (availability)$(NC)" || true
	@aws logs put-retention-policy --log-group-name /ecs/$(ANALYTICS_SERVICE) --retention-in-days 7 --region $(REGION) 2>/dev/null && \
		echo "$(GREEN)✓ Set retention policy: 7 days (analytics)$(NC)" || true

check-logs: ## Check if log groups exist
	@echo "$(YELLOW)Checking log group status...$(NC)"
	@echo ""
	@echo "$(BLUE)Availability Service:$(NC)"
	@if aws logs describe-log-groups --log-group-name-prefix /ecs/$(AVAILABILITY_SERVICE) --region $(REGION) --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "/ecs/$(AVAILABILITY_SERVICE)"; then \
		echo "  $(GREEN)✓ Log group exists$(NC)"; \
	else \
		echo "  $(RED)✗ Log group does not exist$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)Analytics Service:$(NC)"
	@if aws logs describe-log-groups --log-group-name-prefix /ecs/$(ANALYTICS_SERVICE) --region $(REGION) --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "/ecs/$(ANALYTICS_SERVICE)"; then \
		echo "  $(GREEN)✓ Log group exists$(NC)"; \
	else \
		echo "  $(RED)✗ Log group does not exist$(NC)"; \
	fi

status-all: status-availability status-analytics ## Check status of all services

health-check: ## Health check both services via public URLs
	@echo "$(YELLOW)Health checking services...$(NC)"
	@echo ""
	@ALB_URL=$$(cd $(INFRA_DIR) && terraform output -raw alb_url) && \
	echo "$(BLUE)Availability Service:$(NC)" && \
	curl -s -w "\n  Status: %{http_code}\n" $$ALB_URL/availability/health || echo "  $(RED)Failed$(NC)" && \
	echo ""

check-aws: ## Verify AWS configuration
	@echo "$(YELLOW)Checking AWS configuration...$(NC)"
	@echo ""
	@echo "$(BLUE)AWS Identity:$(NC)"
	@aws sts get-caller-identity --output table
	@echo ""
	@echo "$(BLUE)Region:$(NC) $(REGION)"
	@echo ""
	@echo "$(BLUE)ECR Repository:$(NC)"
	@cd $(INFRA_DIR) && terraform output ecr_repository_uri
	@echo ""
	@echo "$(BLUE)ALB URL:$(NC)"
	@cd $(INFRA_DIR) && terraform output availability_service_url

info: ## Display project information
	@echo "$(BLUE)=== 50046 IoT Project - Backend Configuration ===$(NC)"
	@echo ""
	@echo "$(YELLOW)Cluster:$(NC)          $(CLUSTER_NAME)"
	@echo "$(YELLOW)ECR Repository:$(NC)   $(ECR_REPO_NAME)"
	@echo "$(YELLOW)Region:$(NC)           $(REGION)"
	@echo ""
	@echo "$(YELLOW)Services:$(NC)"
	@echo "  - $(AVAILABILITY_SERVICE) (port 8001)"
	@echo "  - $(ANALYTICS_SERVICE) (port 8002)"
	@echo ""
	@echo "$(YELLOW)Common Commands:$(NC)"
	@echo "  make deploy-availability    # Deploy availability service"
	@echo "  make deploy-analytics       # Deploy analytics service"
	@echo "  make deploy-all             # Deploy both services"
	@echo "  make status-all             # Check all service statuses"
	@echo "  make health-check           # Test service endpoints"
	@echo ""
	@echo "For more commands, run: make help"
