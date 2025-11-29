# Create ECR repo

resource "aws_ecr_repository" "app" {
  name = "iot"
}
