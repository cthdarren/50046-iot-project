# Security Group for ECS Service
resource "aws_security_group" "service_sg" {
  name        = "service-sg"
  description = "Managed by Terraform"
  vpc_id      = aws_vpc.main.id

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]

  }

  tags = {
    Name = "services-security-group"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Separate ingress rule to allow traffic from ALB
resource "aws_security_group_rule" "service_from_alb" {
  type                     = "ingress"
  from_port                = 8001
  to_port                  = 8001
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb_sg.id
  security_group_id        = aws_security_group.service_sg.id
  description              = "Allow traffic from ALB to availability service"
}

# Separate ingress rule to allow traffic from ALB to analytics service
resource "aws_security_group_rule" "analytics_from_alb" {
  type                     = "ingress"
  from_port                = 8002
  to_port                  = 8002
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb_sg.id
  security_group_id        = aws_security_group.service_sg.id
  description              = "Allow traffic from ALB to analytics service"
}

# Security group rule to allow analytics service to call availability service
resource "aws_security_group_rule" "analytics_to_availability" {
  type                     = "ingress"
  from_port                = 8001
  to_port                  = 8001
  protocol                 = "tcp"
  security_group_id        = aws_security_group.service_sg.id
  source_security_group_id = aws_security_group.service_sg.id
  description              = "Allow analytics service to call availability service"
}

# Separate ingress rule to allow traffic from ALB to frontend service
resource "aws_security_group_rule" "frontend_from_alb" {
  type                     = "ingress"
  from_port                = 3000
  to_port                  = 3000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb_sg.id
  security_group_id        = aws_security_group.service_sg.id
  description              = "Allow traffic from ALB to frontend service"
}

# Fargate ECS Service
resource "aws_ecs_service" "availability_service" {
  name            = "availability-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.availability_service.arn
  launch_type     = "FARGATE"
  desired_count   = 2

  network_configuration {
    subnets = [
      aws_subnet.private_1.id,
      aws_subnet.private_2.id
    ]
    security_groups  = [aws_security_group.service_sg.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.availability_service_tg.arn
    container_name   = "web"
    container_port   = 8001
  }

  service_registries {
    registry_arn = aws_service_discovery_service.availability_service.arn
  }

  depends_on = [
    aws_lb_listener.http
  ]

  tags = {
    Name = "availability-service"
  }
}

# =========================================================
# Analytics Service
# =========================================================

# Fargate ECS Service for Analytics
resource "aws_ecs_service" "analytics_service" {
  name            = "analytics-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.analytics_service.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets = [
      aws_subnet.private_1.id,
      aws_subnet.private_2.id
    ]
    security_groups  = [aws_security_group.service_sg.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.analytics_service_tg.arn
    container_name   = "web"
    container_port   = 8002
  }

  service_registries {
    registry_arn = aws_service_discovery_service.analytics_service.arn
  }

  depends_on = [
    aws_lb_listener.http
  ]

  tags = {
    Name = "analytics-service"
  }
}

# =========================================================
# Frontend Service
# =========================================================

# Fargate ECS Service for Frontend
resource "aws_ecs_service" "frontend_service" {
  name            = "frontend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend_service.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets = [
      aws_subnet.private_1.id,
      aws_subnet.private_2.id
    ]
    security_groups  = [aws_security_group.service_sg.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend_service_tg.arn
    container_name   = "web"
    container_port   = 3000
  }

  service_registries {
    registry_arn = aws_service_discovery_service.frontend_service.arn
  }

  depends_on = [
    aws_lb_listener.http
  ]

  tags = {
    Name = "frontend-service"
  }
}
