# CloudWatch Log Group for ECS Tasks
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/iot-backend"
  retention_in_days = 7

  tags = {
    Name        = "iot-backend-logs"
    Environment = "production"
  }
}

# Optional: Log group for application-specific logs
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ecs/iot-backend-app"
  retention_in_days = 7

  tags = {
    Name        = "iot-backend-app-logs"
    Environment = "production"
  }
}
