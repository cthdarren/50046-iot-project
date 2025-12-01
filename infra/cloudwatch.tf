# CloudWatch Log Group for ECS Tasks
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/availability-service"
  retention_in_days = 7

  tags = {
    Name        = "availability-service-logs"
    Environment = "production"
  }
}

# Optional: Log group for application-specific logs
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ecs/availability-service-app"
  retention_in_days = 7

  tags = {
    Name        = "availability-service-app-logs"
    Environment = "production"
  }
}
