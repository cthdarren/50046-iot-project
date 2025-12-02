# Data source to get the latest image digest from ECR
data "aws_ecr_image" "availability_latest" {
  repository_name = aws_ecr_repository.availability_service.name
  image_tag       = "availability-latest"
}

data "aws_ecr_image" "analytics_latest" {
  repository_name = aws_ecr_repository.availability_service.name
  image_tag       = "analytics-latest"
}

data "aws_ecr_image" "frontend_latest" {
  repository_name = aws_ecr_repository.availability_service.name
  image_tag       = "frontend-latest"
}

resource "aws_ecs_task_definition" "availability_service" {
  family                   = "availability-service"
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  requires_compatibilities = ["FARGATE"]

  execution_role_arn = aws_iam_role.ecs_task_exec.arn
  task_role_arn      = aws_iam_role.ecs_task_exec.arn

  container_definitions = jsonencode([
    {
      name  = "web"
      image = "${aws_ecr_repository.availability_service.repository_url}@${data.aws_ecr_image.availability_latest.image_digest}"

      portMappings = [
        {
          containerPort = 8001
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = "ap-southeast-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }

      environment = [
        {
          name  = "PORT"
          value = "8001"
        },
        {
          name  = "DB_HOST"
          value = aws_db_instance.postgres.address
        },
        {
          name  = "DB_PORT"
          value = "5432"
        },
        {
          name  = "DB_NAME"
          value = aws_db_instance.postgres.db_name
        }
      ]

      secrets = [
        {
          name      = "DB_USER"
          valueFrom = "${data.aws_secretsmanager_secret.rds_credentials.arn}:username::"
        },
        {
          name      = "DB_PASSWORD"
          valueFrom = "${data.aws_secretsmanager_secret.rds_credentials.arn}:password::"
        }
      ]

      # Health check (optional but recommended)
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

# =========================================================
# Analytics Service Task Definition
# =========================================================

resource "aws_ecs_task_definition" "analytics_service" {
  family                   = "analytics-service"
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  requires_compatibilities = ["FARGATE"]

  execution_role_arn = aws_iam_role.ecs_task_exec.arn
  task_role_arn      = aws_iam_role.ecs_task_exec.arn

  container_definitions = jsonencode([
    {
      name  = "web"
      image = "${aws_ecr_repository.availability_service.repository_url}@${data.aws_ecr_image.analytics_latest.image_digest}"

      portMappings = [
        {
          containerPort = 8002
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.analytics_ecs_logs.name
          "awslogs-region"        = "ap-southeast-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }

      environment = [
        {
          name  = "PORT"
          value = "8002"
        },
        {
          name  = "DB_HOST"
          value = aws_db_instance.postgres.address
        },
        {
          name  = "DB_PORT"
          value = "5432"
        },
        {
          name  = "DB_NAME"
          value = aws_db_instance.postgres.db_name
        },
        {
          name  = "AVAILABILITY_SERVICE_URL"
          value = "http://availability-service.iot.local"
        },
        {
          name  = "AVAILABILITY_SERVICE_PORT"
          value = "8001"
        }
      ]

      secrets = [
        {
          name      = "DB_USER"
          valueFrom = "${data.aws_secretsmanager_secret.rds_credentials.arn}:username::"
        },
        {
          name      = "DB_PASSWORD"
          valueFrom = "${data.aws_secretsmanager_secret.rds_credentials.arn}:password::"
        }
      ]

      # Health check (optional but recommended)
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8002/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

# =========================================================
# Frontend Service Task Definition
# =========================================================

resource "aws_ecs_task_definition" "frontend_service" {
  family                   = "frontend-service"
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  requires_compatibilities = ["FARGATE"]

  execution_role_arn = aws_iam_role.ecs_task_exec.arn
  task_role_arn      = aws_iam_role.ecs_task_exec.arn

  container_definitions = jsonencode([
    {
      name  = "web"
      image = "${aws_ecr_repository.availability_service.repository_url}@${data.aws_ecr_image.frontend_latest.image_digest}"

      portMappings = [
        {
          containerPort = 3000
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend_ecs_logs.name
          "awslogs-region"        = "ap-southeast-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }

      environment = [
        {
          name  = "PORT"
          value = "3000"
        },
        {
          name  = "NEXT_PUBLIC_API_URL"
          value = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_lb.iot_alb.dns_name}"
        }
      ]

      # Health check removed - ALB health check is sufficient
      # Container health check was failing due to curl not being available in node:20-slim
    }
  ])
}
