resource "aws_ecs_task_definition" "app" {
  family                   = "iot-backend"
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  requires_compatibilities = ["FARGATE"]

  execution_role_arn = aws_iam_role.ecs_task_exec.arn
  task_role_arn      = aws_iam_role.ecs_task_exec.arn

  container_definitions = jsonencode([
    {
      name  = "web"
      image = aws_ecr_repository.app.repository_url
      portMappings = [
        {
          containerPort = 8001
          protocol      = "tcp"
        }
      ]
    }
  ])

}
