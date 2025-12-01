# Create ECR repo

resource "aws_ecr_repository" "availability_service" {
  name = "iot"
}
