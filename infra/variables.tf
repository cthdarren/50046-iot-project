variable "region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "ap-southeast-1"
}

# =========================================================
# Route53 Configuration Variables
# =========================================================

variable "create_hosted_zone" {
  description = "Whether to create a new Route53 hosted zone. Set to false if you already have one."
  type        = bool
  default     = true
}

variable "auto_validate_certificate" {
  description = "Automatically validate ACM certificate using Route53 DNS records"
  type        = bool
  default     = true
}

variable "enable_ipv6" {
  description = "Enable IPv6 AAAA record for the domain"
  type        = bool
  default     = false
}
