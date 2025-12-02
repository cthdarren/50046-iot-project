.PHONY: help build push deploy ecr-login status watch-deployment wait-for-stable logs run clean

# Configuration
VERSION := $(shell cat VERSION)
IMAGE_NAME := toilet-frontend
CLUSTER_NAME = my-cluster
ECR_REPO_NAME = iot
FRONTEND_SERVICE = frontend-service
REGION ?= ap-southeast-1
INFRA_DIR = ../infra

# Colors
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m

help: ## Show this help message
	@echo "$(BLUE)=== Frontend Service Deployment ===$(NC)"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make deploy    # Deploy frontend service"

build: ## Build frontend Docker image
	@echo "$(YELLOW)Building $(FRONTEND_SERVICE) Docker image...$(NC)"
	docker build -t $(IMAGE_NAME):$(VERSION) .
	docker tag $(IMAGE_NAME):$(VERSION) $(IMAGE_NAME):latest
	@echo "$(GREEN)✓ Build complete$(NC)"

push: ecr-login build ## Build and push frontend to ECR
	@echo "$(YELLOW)Pushing $(FRONTEND_SERVICE) to ECR...$(NC)"
	@ECR_URI=$$(cd $(INFRA_DIR) && terraform output -raw ecr_repository_uri) && \
	TIMESTAMP=$$(date +%Y%m%d-%H%M%S) && \
	GIT_SHA=$$(git rev-parse --short HEAD 2>/dev/null || echo "local") && \
	echo "$(YELLOW)Tagging images...$(NC)" && \
	docker tag $(IMAGE_NAME):latest $${ECR_URI}:frontend-latest && \
	docker tag $(IMAGE_NAME):latest $${ECR_URI}:frontend-$${TIMESTAMP} && \
	docker tag $(IMAGE_NAME):latest $${ECR_URI}:frontend-$${GIT_SHA} && \
	echo "$(GREEN)✓ Tagged: frontend-latest$(NC)" && \
	echo "$(GREEN)✓ Tagged: frontend-$${TIMESTAMP}$(NC)" && \
	echo "$(GREEN)✓ Tagged: frontend-$${GIT_SHA}$(NC)" && \
	echo "$(YELLOW)Pushing to ECR...$(NC)" && \
	docker push $${ECR_URI}:frontend-latest && \
	docker push $${ECR_URI}:frontend-$${TIMESTAMP} && \
	docker push $${ECR_URI}:frontend-$${GIT_SHA} && \
	echo "" && \
	echo "$(GREEN)=== Push successful! ===$(NC)" && \
	echo "$(GREEN)Images pushed:$(NC)" && \
	echo "  - $${ECR_URI}:frontend-latest" && \
	echo "  - $${ECR_URI}:frontend-$${TIMESTAMP}" && \
	echo "  - $${ECR_URI}:frontend-$${GIT_SHA}"

deploy: push ## Build, push, and deploy frontend service
	@echo ""
	@../backend/scripts/update-task-definition.sh $(FRONTEND_SERVICE) $(CLUSTER_NAME) $(REGION)
	@echo ""
	@echo "$(YELLOW)Monitor deployment with:$(NC)"
	@echo "  make watch-deployment"
	@echo ""
	@echo "$(YELLOW)View logs with:$(NC)"
	@echo "  make logs"
	@echo ""
	@echo "$(YELLOW)Check service URL:$(NC)"
	@ALB_URL=$$(cd $(INFRA_DIR) && terraform output -raw alb_url 2>/dev/null) && \
	echo "  curl $$ALB_URL/"

ecr-login: ## Authenticate Docker with ECR
	@echo "$(YELLOW)Authenticating with ECR...$(NC)"
	@AWS_ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text) && \
	aws ecr get-login-password --region $(REGION) | \
	docker login --username AWS --password-stdin $$AWS_ACCOUNT_ID.dkr.ecr.$(REGION).amazonaws.com
	@echo "$(GREEN)✓ Authenticated$(NC)"

status: ## Check frontend service status
	@echo "$(YELLOW)Checking $(FRONTEND_SERVICE) status...$(NC)"
	@aws ecs describe-services \
		--cluster $(CLUSTER_NAME) \
		--services $(FRONTEND_SERVICE) \
		--region $(REGION) \
		--query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployments:deployments[*].{Status:status,TaskDef:taskDefinition}}' \
		--output table

watch-deployment: ## Watch frontend service deployment
	@watch -n 5 'aws ecs describe-services \
		--cluster $(CLUSTER_NAME) \
		--services $(FRONTEND_SERVICE) \
		--region $(REGION) \
		--query "services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployment:deployments[0].status}"'

wait-for-stable: ## Wait for frontend service deployment to stabilize
	@echo "$(YELLOW)Waiting for $(FRONTEND_SERVICE) deployment to stabilize...$(NC)"
	@aws ecs wait services-stable \
		--cluster $(CLUSTER_NAME) \
		--services $(FRONTEND_SERVICE) \
		--region $(REGION)
	@echo "$(GREEN)✓ Deployment complete!$(NC)"

logs: ## View frontend service logs
	@echo "$(YELLOW)Fetching $(FRONTEND_SERVICE) logs...$(NC)"
	@LOG_GROUP="/ecs/$(FRONTEND_SERVICE)"; \
	if ! aws logs describe-log-groups --log-group-name-prefix $$LOG_GROUP --region $(REGION) --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$$LOG_GROUP"; then \
		echo "$(YELLOW)Log group $$LOG_GROUP does not exist yet.$(NC)"; \
		echo "$(YELLOW)Check if service has been deployed.$(NC)"; \
		exit 1; \
	else \
		aws logs tail $$LOG_GROUP --follow --region $(REGION); \
	fi

run: build ## Run frontend service locally
	@echo "$(YELLOW)Running $(FRONTEND_SERVICE) locally on port 3000...$(NC)"
	docker run -p 3000:3000 --rm -it $(IMAGE_NAME):latest

clean: ## Remove local Docker images
	@echo "$(YELLOW)Cleaning up local images...$(NC)"
	-docker rmi $(IMAGE_NAME):$(VERSION)
	-docker rmi $(IMAGE_NAME):latest
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

docker-build: build ## Alias for build (backward compatibility)

docker-run: run ## Alias for run (backward compatibility)
