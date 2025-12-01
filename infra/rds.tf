resource "aws_db_subnet_group" "db_subnets" {
  name = "rds_subnet_group"
  subnet_ids = [
    aws_subnet.private_1.id,
    aws_subnet.private_2.id
  ]
}

resource "aws_security_group" "rds_sg" {
  name        = "rds_sg"
  description = "Security group for RDS instance"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port = 5432
    to_port   = 5432
    protocol  = "tcp"
    security_groups = [
      aws_security_group.lambda_sg.id,
      aws_security_group.service_sg.id
    ]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "postgres" {
  identifier        = "iot-postgres-db"
  allocated_storage = 20
  db_name           = "iotdb"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t3.micro"

  username = local.rds_credentials.username
  password = local.rds_credentials.password

  db_subnet_group_name   = aws_db_subnet_group.db_subnets.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  skip_final_snapshot = true
  apply_immediately   = true
}

/* IAM role for RDS Proxy to access Secrets Manager on your behalf */
resource "aws_iam_role" "rds_proxy_role" {
  name = "rds-proxy-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "rds.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "rds_proxy_policy" {
  name = "rds-proxy-secrets-policy"
  role = aws_iam_role.rds_proxy_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = data.aws_secretsmanager_secret.rds_credentials.arn
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "secretsmanager.${data.aws_region.current.id}.amazonaws.com"
          }
        }
      }
    ]
  })
}

data "aws_region" "current" {}

/* RDS Proxy */
resource "aws_db_proxy" "rds_proxy" {
  name                = "iot-rds-proxy"
  engine_family       = "POSTGRESQL"
  require_tls         = true
  idle_client_timeout = 1800
  role_arn            = aws_iam_role.rds_proxy_role.arn

  auth {
    auth_scheme = "SECRETS"
    secret_arn  = data.aws_secretsmanager_secret.rds_credentials.arn
    iam_auth    = "DISABLED"
  }

  vpc_subnet_ids         = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
}

/* Wait for RDS instance to be fully available */
resource "time_sleep" "wait_for_rds" {
  depends_on = [aws_db_instance.postgres]

  create_duration = "30s"
}

/* Register the RDS instance as a target for the proxy */
resource "aws_db_proxy_default_target_group" "rds_target" {
  db_proxy_name = aws_db_proxy.rds_proxy.name

  connection_pool_config {
    max_connections_percent      = 100
    max_idle_connections_percent = 50
  }
}

resource "aws_db_proxy_target" "rds_target" {
  db_proxy_name          = aws_db_proxy.rds_proxy.name
  target_group_name      = aws_db_proxy_default_target_group.rds_target.name
  db_instance_identifier = aws_db_instance.postgres.identifier

  depends_on = [
    time_sleep.wait_for_rds,
    aws_db_proxy.rds_proxy,
    aws_db_proxy_default_target_group.rds_target
  ]
}
