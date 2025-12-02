# =========================================================
# Route 53 DNS Configuration for Custom Domain
# =========================================================

# Data source to check if hosted zone already exists (only when not creating new one)
data "aws_route53_zone" "existing" {
  count        = var.domain_name != "" && !var.create_hosted_zone ? 1 : 0
  name         = local.root_domain
  private_zone = false
}

# Local variable to extract root domain from subdomain
locals {
  # Extract root domain (e.g., "tingtangwalawalabingbang.com" from "iot.tingtangwalawalabingbang.com")
  domain_parts = var.domain_name != "" ? split(".", var.domain_name) : []
  root_domain  = var.domain_name != "" ? join(".", slice(local.domain_parts, length(local.domain_parts) - 2, length(local.domain_parts))) : ""
}

# Create Route53 Hosted Zone (only if it doesn't exist)
resource "aws_route53_zone" "main" {
  count = var.domain_name != "" && var.create_hosted_zone ? 1 : 0
  name  = local.root_domain

  tags = {
    Name        = "iot-platform-hosted-zone"
    Environment = "production"
    ManagedBy   = "terraform"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Use existing or newly created hosted zone
locals {
  hosted_zone_id = var.domain_name != "" ? (
    var.create_hosted_zone ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.existing[0].zone_id
  ) : ""
}

# A Record (Alias) pointing to the ALB
resource "aws_route53_record" "alb_alias" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = local.hosted_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.iot_alb.dns_name
    zone_id                = aws_lb.iot_alb.zone_id
    evaluate_target_health = true
  }

  depends_on = [aws_lb.iot_alb]
}

# Optional: AAAA Record for IPv6 support
resource "aws_route53_record" "alb_alias_ipv6" {
  count   = var.domain_name != "" && var.enable_ipv6 ? 1 : 0
  zone_id = local.hosted_zone_id
  name    = var.domain_name
  type    = "AAAA"

  alias {
    name                   = aws_lb.iot_alb.dns_name
    zone_id                = aws_lb.iot_alb.zone_id
    evaluate_target_health = true
  }

  depends_on = [aws_lb.iot_alb]
}

# DNS validation record for ACM certificate
resource "aws_route53_record" "cert_validation" {
  count = var.domain_name != "" && var.auto_validate_certificate ? 1 : 0

  allow_overwrite = true
  name            = tolist(aws_acm_certificate.main[0].domain_validation_options)[0].resource_record_name
  records         = [tolist(aws_acm_certificate.main[0].domain_validation_options)[0].resource_record_value]
  ttl             = 60
  type            = tolist(aws_acm_certificate.main[0].domain_validation_options)[0].resource_record_type
  zone_id         = local.hosted_zone_id
}

# Enable automatic certificate validation when using Route53
resource "aws_acm_certificate_validation" "main" {
  count                   = var.domain_name != "" && var.auto_validate_certificate ? 1 : 0
  certificate_arn         = aws_acm_certificate.main[0].arn
  validation_record_fqdns = [aws_route53_record.cert_validation[0].fqdn]

  timeouts {
    create = "45m"
  }

  depends_on = [aws_route53_record.cert_validation]
}

# =========================================================
# Outputs
# =========================================================

output "route53_zone_id" {
  description = "The Route53 hosted zone ID"
  value       = var.domain_name != "" ? local.hosted_zone_id : ""
}

output "route53_nameservers" {
  description = "Nameservers to configure at your domain registrar"
  value = var.domain_name != "" ? (
    var.create_hosted_zone ? aws_route53_zone.main[0].name_servers : data.aws_route53_zone.existing[0].name_servers
  ) : []
}

output "route53_domain_record" {
  description = "The DNS A record created for the domain"
  value       = var.domain_name != "" ? aws_route53_record.alb_alias[0].fqdn : ""
}

output "dns_configured" {
  description = "Whether DNS is fully configured and ready"
  value       = var.domain_name != "" ? "Yes - Domain ${var.domain_name} points to ALB" : "No - Set domain_name variable to configure"
}
