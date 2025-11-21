resource "aws_vpc" "main" {
    cidr_block = "10.0.0.0/16"
    enable_dns_support   = true
    enable_dns_hostnames = true
    tags = { Name = "main_vpc" }
}

resource "aws_subnet" "private_1" {
    vpc_id = aws_vpc.main.id
    cidr_block = "10.0.1.0/24"
    availability_zone = "${var.region}a"
    map_public_ip_on_launch = false
    tags = { Name = "private_a" }
}

resource "aws_subnet" "private_2" {
    vpc_id = aws_vpc.main.id
    cidr_block = "10.0.2.0/24"
    availability_zone = "${var.region}b"
    map_public_ip_on_launch = false
    tags = { Name = "private_b" }
}

resource "aws_security_group" "lambda_sg" {
    name = "lambda_sg"
    vpc_id = aws_vpc.main.id
    /* No ingress required for Lambda to initiate outbound connections to RDS.
       Keep ingress on the RDS security group (aws_security_group.rds_sg) which
       should allow traffic from this Lambda SG. Removing the mutual ingress
       breaks the circular dependency. */
    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}  