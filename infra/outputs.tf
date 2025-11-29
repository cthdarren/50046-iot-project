output "lambda_name" {
  value = aws_lambda_function.iot_handler.function_name
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "rds_proxy_endpoint" {
  value = aws_db_proxy.rds_proxy.endpoint
}

output "ecr_repository_uri" {
  description = "URI of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}
