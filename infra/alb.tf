# =========================================================
# Shared Application Load Balancer for IoT Services
# =========================================================

# Security Group for ALB - allows HTTP/HTTPS from internet
resource "aws_security_group" "alb_sg" {
  name        = "alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  # Allow HTTP from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP traffic from internet"
  }

  # Allow HTTPS from anywhere (optional, for future SSL setup)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS traffic from internet"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "alb-security-group"
  }
}

# Application Load Balancer
resource "aws_lb" "iot_alb" {
  name               = "iot-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets = [
    aws_subnet.public_1.id,
    aws_subnet.public_2.id
  ]

  enable_deletion_protection = false
  enable_http2               = true

  tags = {
    Name        = "iot-alb"
    Description = "Shared ALB for all IoT services"
  }
}

# Target Group for ECS Service
resource "aws_lb_target_group" "availability_service_tg" {
  name        = "availability-service-tg"
  port        = 8001
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/availability/health"
    protocol            = "HTTP"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name = "availability-service-target-group"
  }
}

# HTTP Listener - redirect to HTTPS if SSL is configured, otherwise show 404
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.iot_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = var.domain_name != "" ? "redirect" : "fixed-response"

    dynamic "redirect" {
      for_each = var.domain_name != "" ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    dynamic "fixed_response" {
      for_each = var.domain_name == "" ? [1] : []
      content {
        content_type = "text/plain"
        message_body = "IoT Platform - No route configured for this path"
        status_code  = "404"
      }
    }
  }
}

# Listener Rule - forward /availability/* to availability service
resource "aws_lb_listener_rule" "availability_service" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.availability_service_tg.arn
  }

  condition {
    path_pattern {
      values = ["/availability", "/availability/*"]
    }
  }

  tags = {
    Name = "availability-service-rule"
  }
}

# HTTPS Listener - enabled when domain_name is configured
resource "aws_lb_listener" "https" {
  count             = var.domain_name != "" ? 1 : 0
  load_balancer_arn = aws_lb.iot_alb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main[0].arn

  # Automatically wait for certificate validation when using Route53
  depends_on = [aws_acm_certificate_validation.main]

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "IoT Platform - No route configured for this path"
      status_code  = "404"
    }
  }
}

# HTTPS Listener Rule - forward /availability/* to availability service
resource "aws_lb_listener_rule" "availability_service_https" {
  count        = var.domain_name != "" ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.availability_service_tg.arn
  }

  condition {
    path_pattern {
      values = ["/availability", "/availability/*"]
    }
  }

  tags = {
    Name = "availability-service-https-rule"
  }
}

# HTTPS Listener Rule - forward /analytics/* to analytics service
resource "aws_lb_listener_rule" "analytics_service_https" {
  count        = var.domain_name != "" ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.analytics_service_tg.arn
  }

  condition {
    path_pattern {
      values = ["/analytics", "/analytics/*"]
    }
  }

  tags = {
    Name = "analytics-service-https-rule"
  }
}

# Target Group for Analytics Service
resource "aws_lb_target_group" "analytics_service_tg" {
  name        = "analytics-service-tg"
  port        = 8002
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/analytics/health"
    protocol            = "HTTP"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name = "analytics-service-target-group"
  }
}

# Listener Rule - forward /analytics/* to analytics service
resource "aws_lb_listener_rule" "analytics_service" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.analytics_service_tg.arn
  }

  condition {
    path_pattern {
      values = ["/analytics", "/analytics/*"]
    }
  }

  tags = {
    Name = "analytics-service-rule"
  }
}

# =========================================================
# Frontend Service
# =========================================================

# Target Group for Frontend Service
resource "aws_lb_target_group" "frontend_service_tg" {
  name        = "frontend-service-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name = "frontend-service-target-group"
  }
}

# HTTP Listener Rule - forward root path to frontend service (lowest priority)
resource "aws_lb_listener_rule" "frontend_service" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 300

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_service_tg.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }

  tags = {
    Name = "frontend-service-rule"
  }
}

# HTTPS Listener Rule - forward root path to frontend service (lowest priority)
resource "aws_lb_listener_rule" "frontend_service_https" {
  count        = var.domain_name != "" ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 300

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_service_tg.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }

  tags = {
    Name = "frontend-service-https-rule"
  }
}
