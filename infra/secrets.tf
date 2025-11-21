data "aws_secretsmanager_secret" "rds_credentials" {
    name = "rds_credentials"
}

data "aws_secretsmanager_secret_version" "rds_credentials_version" {
    secret_id = data.aws_secretsmanager_secret.rds_credentials.id
}

locals {
    rds_credentials = jsondecode(data.aws_secretsmanager_secret_version.rds_credentials_version.secret_string)
}