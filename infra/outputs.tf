output "lambda_name" {
    value = aws_lambda_function.iot_handler.function_name
}

output "rds_endpoint" {
    value = aws_db_instance.postgres.address
}