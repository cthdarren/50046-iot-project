resource "aws_lambda_function" "iot_handler" {
    function_name = "iot_ts_handler"
    role = aws_iam_role.lambda_exec.arn
    handler = "index.handler"
    runtime = "nodejs20.x"

    filename = "lambda.zip"
    source_code_hash = filebase64sha256("lambda.zip")

    vpc_config {
        subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
        security_group_ids = [aws_security_group.lambda_sg.id]
    }

    environment {
        variables = {
            DB_HOST       = aws_db_proxy.rds_proxy.endpoint
            DB_PORT       = "5432"
            DB_NAME       = "iotdb"
            DB_USER       = local.rds_credentials.username
            DB_SECRET_ARN = data.aws_secretsmanager_secret.rds_credentials.arn
        }
    }
}