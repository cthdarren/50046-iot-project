# Fargate ECS Service
resource "aws_security_group" "service_sg" {
  name = "service-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port = 8001
    to_port = 8001
    protocol = "tcp"
    security_groups = []
  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_service" "app" {
  name            = "iot-backend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets = [
      aws_subnet.private_1.id,
      aws_subnet.private_2.id
    ]
    security_groups = [aws_security_group.service_sg.id]
    assign_public_ip = false
  }
}
