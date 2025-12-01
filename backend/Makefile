.PHONY: help build push deploy ecr-login clean test run-local logs create-log-group check-logs

# Configuration
SERVICE_NAME = availability-service
REGION ?= ap-southeast-1
INFRA_DIR = ../infra

# Colors
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

build: ## Build Docker image locally
	@echo "$(YELLOW)Building $(SERVICE_NAME) Docker image...$(NC)"
	cd $(SERVICE_NAME) && docker build -t $(SERVICE_NAME):latest .
	@echo "$(GREEN)✓ Build complete$(NC)"

ecr-login: ## Authenticate Docker with ECR
	@echo "$(YELLOW)Authenticating with ECR...$(NC)"
	@AWS_ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text) && \
	aws ecr get-login-password --region $(REGION) | \
	docker login --username AWS --password-stdin $$AWS_ACCOUNT_ID.dkr.ecr.$(REGION).amazonaws.com
	@echo "$(GREEN)✓ Authenticated$(NC)"

push: ecr-login build ## Build and push Docker image to ECR
	@echo "$(YELLOW)Pushing image to ECR...$(NC)"
	@ECR_URI=$$(cd $(INFRA_DIR) && terraform output -raw ecr_repository_uri) && \
	TIMESTAMP=$$(date +%Y%m%d-%H%M%S) && \
	GIT_SHA=$$(git rev-parse --short HEAD 2>/dev/null || echo "local") && \
	echo "$(YELLOW)Tagging images...$(NC)" && \
	docker tag $(SERVICE_NAME):latest $${ECR_URI}:latest && \
	docker tag $(SERVICE_NAME):latest $${ECR_URI}:$${TIMESTAMP} && \
	docker tag $(SERVICE_NAME):latest $${ECR_URI}:$${GIT_SHA} && \
	echo "$(GREEN)✓ Tagged: latest$(NC)" && \
	echo "$(GREEN)✓ Tagged: $${TIMESTAMP}$(NC)" && \
	echo "$(GREEN)✓ Tagged: $${GIT_SHA}$(NC)" && \
	echo "$(YELLOW)Pushing to ECR...$(NC)" && \
	docker push $${ECR_URI}:latest && \
	docker push $${ECR_URI}:$${TIMESTAMP} && \
	docker push $${ECR_URI}:$${GIT_SHA} && \
	echo "" && \
	echo "$(GREEN)=== Push successful! ===$(NC)" && \
	echo "$(GREEN)Images pushed:$(NC)" && \
	echo "  - $${ECR_URI}:latest" && \
	echo "  - $${ECR_URI}:$${TIMESTAMP}" && \
	echo "  - $${ECR_URI}:$${GIT_SHA}"

deploy: push ## Build, push to ECR, and update ECS service
	@echo ""
	@echo "$(YELLOW)Updating ECS service...$(NC)"
	@aws ecs update-service \
		--cluster my-cluster \
		--service iot-backend-service \
		--force-new-deployment \
		--region $(REGION) \
		--output table \
		--query 'service.{Service:serviceName,Status:status,Running:runningCount,Desired:desiredCount}' && \
	echo "$(GREEN)✓ ECS service update initiated$(NC)" && \
	echo "" && \
	echo "$(YELLOW)Monitor deployment with:$(NC)" && \
	echo "  make watch-deployment" && \
	echo "" && \
	echo "$(YELLOW)View logs with:$(NC)" && \
	echo "  make logs"

watch-deployment: ## Watch ECS deployment status
	@watch -n 5 'aws ecs describe-services \
		--cluster my-cluster \
		--services iot-backend-service \
		--region $(REGION) \
		--query "services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployment:deployments[0].status}"'

wait-for-stable: ## Wait for ECS deployment to stabilize
	@echo "$(YELLOW)Waiting for deployment to stabilize...$(NC)"
	@aws ecs wait services-stable \
		--cluster my-cluster \
		--services iot-backend-service \
		--region $(REGION)
	@echo "$(GREEN)✓ Deployment complete!$(NC)"

list-images: ## List recent ECR images
	@aws ecr describe-images \
		--repository-name iot \
		--region $(REGION) \
		--query 'sort_by(imageDetails,&imagePushedAt)[-10:].{Tag:imageTags[0],Pushed:imagePushedAt,Size:imageSizeInBytes}' \
		--output table

test: ## Run tests locally
	@echo "$(YELLOW)Running tests...$(NC)"
	cd $(SERVICE_NAME) && docker build -t $(SERVICE_NAME):test --target test . || \
	echo "No test target defined in Dockerfile"

clean: ## Remove local Docker images
	@echo "$(YELLOW)Cleaning up local images...$(NC)"
	-docker rmi $(SERVICE_NAME):latest
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

run-local: ## Run the service locally
	@echo "$(YELLOW)Running $(SERVICE_NAME) locally on port 8001...$(NC)"
	cd $(SERVICE_NAME) && docker run -p 8001:8001 --env-file ../../.env $(SERVICE_NAME):latest

create-log-group: ## Create CloudWatch log group for ECS
	@echo "$(YELLOW)Creating CloudWatch log group...$(NC)"
	@aws logs create-log-group --log-group-name /ecs/iot-backend --region $(REGION) 2>/dev/null && \
		echo "$(GREEN)✓ Log group created: /ecs/iot-backend$(NC)" || \
		echo "$(YELLOW)Log group /ecs/iot-backend already exists$(NC)"
	@aws logs put-retention-policy --log-group-name /ecs/iot-backend --retention-in-days 7 --region $(REGION) 2>/dev/null && \
		echo "$(GREEN)✓ Set retention policy: 7 days$(NC)" || true

check-logs: ## Check if log group exists and show recent streams
	@echo "$(YELLOW)Checking log group status...$(NC)"
	@if aws logs describe-log-groups --log-group-name-prefix /ecs/iot-backend --region $(REGION) --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "/ecs/iot-backend"; then \
		echo "$(GREEN)✓ Log group exists: /ecs/iot-backend$(NC)"; \
		echo ""; \
		echo "$(YELLOW)Recent log streams:$(NC)"; \
		aws logs describe-log-streams --log-group-name /ecs/iot-backend --region $(REGION) --order-by LastEventTime --descending --max-items 5 --query 'logStreams[*].{Stream:logStreamName,LastEvent:lastEventTime}' --output table 2>/dev/null || echo "No streams yet"; \
	else \
		echo "$(RED)✗ Log group does not exist$(NC)"; \
		echo "$(YELLOW)Create it with: make create-log-group$(NC)"; \
		echo "$(YELLOW)Or apply Terraform: cd ../infra && terraform apply$(NC)"; \
	fi

logs: ## View ECS service logs (requires CloudWatch)
	@echo "$(YELLOW)Fetching recent logs...$(NC)"
	@LOG_GROUP="/ecs/iot-backend"; \
	if ! aws logs describe-log-groups --log-group-name-prefix $$LOG_GROUP --region $(REGION) --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$$LOG_GROUP"; then \
		echo "$(YELLOW)Log group $$LOG_GROUP does not exist yet.$(NC)"; \
		echo "$(YELLOW)This is normal if the service hasn't been deployed yet.$(NC)"; \
		echo ""; \
		echo "$(YELLOW)Available log groups:$(NC)"; \
		aws logs describe-log-groups --region $(REGION) --query 'logGroups[?contains(logGroupName, `ecs`) || contains(logGroupName, `iot`)].logGroupName' --output table || echo "No ECS/IoT log groups found"; \
		echo ""; \
		echo "$(YELLOW)To create the log group, run:$(NC)"; \
		echo "  cd ../infra && terraform apply"; \
		echo ""; \
		echo "$(YELLOW)Or create it manually:$(NC)"; \
		echo "  aws logs create-log-group --log-group-name /ecs/iot-backend --region $(REGION)"; \
		exit 1; \
	else \
		aws logs tail $$LOG_GROUP --follow --region $(REGION); \
	fi

status: ## Check ECS service status
	@aws ecs describe-services \
		--cluster my-cluster \
		--services iot-backend-service \
		--region $(REGION) \
		--query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployments:deployments[*].{Status:status,TaskDef:taskDefinition}}' \
		--output table
