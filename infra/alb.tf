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

# HTTP Listener - default action returns fixed response (no frontend yet)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.iot_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "IoT Platform - No route configured for this path"
      status_code  = "404"
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

# HTTPS Listener (optional - uncomment when you have an SSL certificate)
# resource "aws_lb_listener" "https" {
#   load_balancer_arn = aws_lb.iot_alb.arn
#   port              = 443
#   protocol          = "HTTPS"
#   ssl_policy        = "ELBSecurityPolicy-2016-08"
#   certificate_arn   = "arn:aws:acm:region:account-id:certificate/certificate-id"
#
#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.availability_service_tg.arn
#   }
# }

# HTTP to HTTPS redirect (optional - uncomment when SSL is configured)
# resource "aws_lb_listener" "http_redirect" {
#   load_balancer_arn = aws_lb.iot_alb.arn
#   port              = 80
#   protocol          = "HTTP"
#
#   default_action {
#     type = "redirect"
#
#     redirect {
#       port        = "443"
#       protocol    = "HTTPS"
#       status_code = "HTTP_301"
#     }
#   }
# }
