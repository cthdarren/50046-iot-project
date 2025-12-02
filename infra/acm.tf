# =========================================================
# ACM Certificate for Custom Domain (External DNS)
# =========================================================

# Variable for your domain name
variable "domain_name" {
  description = "Your custom domain name (e.g., api.yourdomain.com)"
  type        = string
  default     = "" # Set this via terraform.tfvars or -var flag
}

# ACM Certificate - SSL/TLS certificate for your domain
resource "aws_acm_certificate" "main" {
  count             = var.domain_name != "" ? 1 : 0
  domain_name       = var.domain_name
  validation_method = "DNS"

  # Optional: Add Subject Alternative Names (SANs) for multiple subdomains
  # subject_alternative_names = [
  #   "www.${var.domain_name}",
  #   "*.${var.domain_name}"
  # ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "iot-platform-cert"
    Environment = "production"
  }
}

# Output the DNS validation records
# You'll need to add these records to your DNS provider manually
output "acm_certificate_dns_validation_records" {
  description = "DNS records to add to your domain provider for certificate validation"
  value = var.domain_name != "" ? [
    for dvo in aws_acm_certificate.main[0].domain_validation_options : {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      value  = dvo.resource_record_value
      domain = dvo.domain_name
    }
  ] : []
}

# Wait for certificate validation to complete
# This will timeout if DNS records are not added
# COMMENTED OUT: Uncomment after DNS records are added and propagated
# resource "aws_acm_certificate_validation" "main" {
#   count                   = var.domain_name != "" ? 1 : 0
#   certificate_arn         = aws_acm_certificate.main[0].arn
#
#   # Optional: Add a timeout to prevent indefinite waiting
#   timeouts {
#     create = "45m"
#   }
# }

# Output the certificate ARN for use in ALB
output "acm_certificate_arn" {
  description = "ARN of the validated ACM certificate"
  value       = var.domain_name != "" ? aws_acm_certificate.main[0].arn : ""
}
