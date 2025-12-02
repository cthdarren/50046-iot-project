# =========================================================
# AWS Cloud Map - Service Discovery
# =========================================================

# Private DNS namespace for service discovery
resource "aws_service_discovery_private_dns_namespace" "iot_services" {
  name        = "iot.local"
  description = "Private DNS namespace for IoT services"
  vpc         = aws_vpc.main.id

  tags = {
    Name = "iot-services-namespace"
  }
}

# Service discovery for availability service
resource "aws_service_discovery_service" "availability_service" {
  name = "availability-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.iot_services.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  tags = {
    Name = "availability-service-discovery"
  }

  lifecycle {
    create_before_destroy = false
  }
}

# Service discovery for analytics service
resource "aws_service_discovery_service" "analytics_service" {
  name = "analytics-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.iot_services.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  tags = {
    Name = "analytics-service-discovery"
  }

  lifecycle {
    create_before_destroy = false
  }
}

# Service discovery for frontend service
resource "aws_service_discovery_service" "frontend_service" {
  name = "frontend-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.iot_services.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  tags = {
    Name = "frontend-service-discovery"
  }

  lifecycle {
    create_before_destroy = false
  }
}
