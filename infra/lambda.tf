resource "aws_lambda_function" "iot_handler" {
  function_name = "iot_ts_handler"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "dist/index.handler"
  runtime       = "nodejs20.x"

  filename         = "lambda.zip"
  source_code_hash = filebase64sha256("lambda.zip")

  # Performance optimizations
  memory_size = 512 # More memory = faster CPU, better for DB operations
  timeout     = 30  # Reasonable timeout for DB operations

  # Connection reuse optimization
  # reserved_concurrent_executions = 10 # Commented out due to account concurrency limits
  # Note: Monitor RDS connections. If you see "too many connections" errors,
  # reduce this value or increase RDS max_connections parameter

  vpc_config {
    subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }

  environment {
    variables = {
      DB_HOST       = aws_db_instance.postgres.address
      DB_PORT       = "5432"
      DB_NAME       = "iotdb"
      DB_USER       = local.rds_credentials.username
      DB_PASSWORD   = local.rds_credentials.password
      DB_SECRET_ARN = data.aws_secretsmanager_secret.rds_credentials.arn
      # Node.js optimization for Lambda
      NODE_OPTIONS = "--enable-source-maps"
    }
  }

  tags = {
    Name        = "iot-ts-handler"
    Environment = "production"
  }
}

# Import existing log group
data "aws_cloudwatch_log_group" "lambda_logs" {
  name = "/aws/lambda/iot_ts_handler"
}
