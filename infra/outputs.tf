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
  value       = aws_ecr_repository.availability_service.repository_url
}

# =========================================================
# IoT Core Outputs
# =========================================================

output "iot_endpoint" {
  description = "AWS IoT Core endpoint for MQTT connections"
  value       = data.aws_iot_endpoint.iot_endpoint.endpoint_address
}

output "iot_thing_name" {
  description = "Name of the IoT Thing (device)"
  value       = aws_iot_thing.sensor_device.name
}

output "iot_thing_arn" {
  description = "ARN of the IoT Thing"
  value       = aws_iot_thing.sensor_device.arn
}

output "iot_certificate_arn" {
  description = "ARN of the IoT certificate"
  value       = aws_iot_certificate.sensor_cert.arn
}

output "iot_certificate_pem" {
  description = "Device certificate in PEM format (save this securely!)"
  value       = aws_iot_certificate.sensor_cert.certificate_pem
  sensitive   = true
}

output "iot_private_key" {
  description = "Private key for the device certificate (save this securely!)"
  value       = aws_iot_certificate.sensor_cert.private_key
  sensitive   = true
}

output "iot_public_key" {
  description = "Public key for the device certificate"
  value       = aws_iot_certificate.sensor_cert.public_key
  sensitive   = true
}

# =========================================================
# Shared ALB Outputs
# =========================================================

output "alb_dns" {
  description = "Public DNS name of the shared Application Load Balancer"
  value       = aws_lb.iot_alb.dns_name
}

output "alb_url" {
  description = "Public URL of the shared ALB"
  value       = "http://${aws_lb.iot_alb.dns_name}"
}

# =========================================================
# Availability Service Outputs
# =========================================================

output "availability_service_url" {
  description = "Public URL to access the availability service API"
  value       = "http://${aws_lb.iot_alb.dns_name}"
}

output "availability_service_target_group_arn" {
  description = "ARN of the target group for health check debugging"
  value       = aws_lb_target_group.availability_service_tg.arn
}
