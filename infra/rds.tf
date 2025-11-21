resource "aws_db_subnet_group" "db_subnets" {
    name       = "rds_subnet_group"
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
        from_port   = 5432
        to_port     = 5432
        protocol    = "tcp"
        security_groups = [aws_security_group.lambda_sg.id]
    }
}

resource "aws_db_instance" "postgres" {
    allocated_storage  = 20
    db_name               = "iotdb"
    engine             = "postgres"
    engine_version     = "15"
    instance_class     = "db.t3.micro"

    username           = var.db_username
    password           = var.db_password

    db_subnet_group_name = aws_db_subnet_group.db_subnets.name
    vpc_security_group_ids = [aws_security_group.rds_sg.id]

    skip_final_snapshot = true
}