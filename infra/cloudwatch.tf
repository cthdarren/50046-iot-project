# CloudWatch Log Group for ECS Tasks - Availability Service
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/availability-service"
  retention_in_days = 7

  tags = {
    Name        = "availability-service-logs"
    Environment = "production"
  }
}

# Optional: Log group for application-specific logs - Availability Service
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ecs/availability-service-app"
  retention_in_days = 7

  tags = {
    Name        = "availability-service-app-logs"
    Environment = "production"
  }
}

# CloudWatch Log Group for ECS Tasks - Analytics Service
resource "aws_cloudwatch_log_group" "analytics_ecs_logs" {
  name              = "/ecs/analytics-service"
  retention_in_days = 7

  tags = {
    Name        = "analytics-service-logs"
    Environment = "production"
  }
}

# Optional: Log group for application-specific logs - Analytics Service
resource "aws_cloudwatch_log_group" "analytics_app_logs" {
  name              = "/aws/ecs/analytics-service-app"
  retention_in_days = 7

  tags = {
    Name        = "analytics-service-app-logs"
    Environment = "production"
  }
}

# CloudWatch Log Group for ECS Tasks - Frontend Service
resource "aws_cloudwatch_log_group" "frontend_ecs_logs" {
  name              = "/ecs/frontend-service"
  retention_in_days = 7

  tags = {
    Name        = "frontend-service-logs"
    Environment = "production"
  }
}

# Optional: Log group for application-specific logs - Frontend Service
resource "aws_cloudwatch_log_group" "frontend_app_logs" {
  name              = "/aws/ecs/frontend-service-app"
  retention_in_days = 7

  tags = {
    Name        = "frontend-service-app-logs"
    Environment = "production"
  }
}
