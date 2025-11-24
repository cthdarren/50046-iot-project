resource "aws_iam_role" "lambda_exec" {
    name = "lambda_exec_role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17",
        Statement = [{
            Action    = "sts:AssumeRole",
            Effect    = "Allow",
            Principal = { Service = "lambda.amazonaws.com" }
        }]
    })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
    role       = aws_iam_role.lambda_exec.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
    role       = aws_iam_role.lambda_exec.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_policy" "lambda_secretsmanager" {
  name        = "lambda_secretsmanager_policy"
  description = "Allow Lambda to get secret value from Secrets Manager for RDS credentials"
  policy      = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue"
        ],
        Resource = data.aws_secretsmanager_secret.rds_credentials.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_secretsmanager" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_secretsmanager.arn
}
