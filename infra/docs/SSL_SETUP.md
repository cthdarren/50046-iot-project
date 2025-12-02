# SSL Certificate Setup Guide

This guide explains how to add an SSL certificate for your custom domain (not managed by Route53) to the IoT Platform.

## Overview

The infrastructure uses AWS Certificate Manager (ACM) to provision a free SSL/TLS certificate for your domain. Since your domain is not hosted in Route53, you'll need to manually add DNS validation records to your domain provider (GoDaddy, Namecheap, Cloudflare, etc.).

## Quick Start

```bash
# 1. Configure your domain
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars and set: domain_name = "api.yourdomain.com"

# 2. Apply Terraform
terraform apply

# 3. Get DNS validation records
./scripts/ssl-helper.sh dns-records

# 4. Add the CNAME record to your DNS provider

# 5. Wait for validation (5-30 minutes)
./scripts/ssl-helper.sh cert-status

# 6. Point your domain to the ALB
./scripts/ssl-helper.sh alb-dns

# 7. Test your HTTPS endpoint
./scripts/ssl-helper.sh test
```

## Prerequisites

- A domain name you own (e.g., `yourdomain.com`)
- Access to your domain's DNS management console
- Terraform already initialized in the `infra/` directory

## Step-by-Step Setup

### Step 1: Configure Your Domain Name

Create a `terraform.tfvars` file in the `infra/` directory:

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set your domain:

```hcl
domain_name = "api.yourdomain.com"
```

**Note:** Use a subdomain like `api.yourdomain.com` or `iot.yourdomain.com` rather than the root domain.

### Step 2: Apply Terraform Configuration

Run terraform to create the certificate request:

```bash
terraform plan
terraform apply
```

Terraform will create the ACM certificate but will wait for DNS validation.

### Step 3: Get DNS Validation Records

After applying, get the DNS validation records:

```bash
terraform output acm_certificate_dns_validation_records
```

You'll see output like:

```json
[
  {
    "domain" = "api.yourdomain.com"
    "name" = "_abc123def456.api.yourdomain.com."
    "type" = "CNAME"
    "value" = "_xyz789ghi012.acm-validations.aws."
  }
]
```

### Step 4: Add DNS Records to Your Domain Provider

Log into your domain provider (GoDaddy, Namecheap, Cloudflare, etc.) and add a new DNS record:

**Record Details:**
- **Type:** CNAME
- **Name/Host:** `_abc123def456.api.yourdomain.com` (or just `_abc123def456.api` if your provider auto-adds the domain)
- **Value/Points To:** `_xyz789ghi012.acm-validations.aws.`
- **TTL:** 300 (or default)

**Important:** Some DNS providers automatically append your domain name. If so, only use the subdomain part before your domain.

### Step 5: Wait for Validation

ACM will check for the DNS record and validate your certificate. This typically takes:
- **5-30 minutes** for most providers
- Up to **72 hours** in rare cases

You can check the status in the AWS Console:
- Go to **Certificate Manager** → **Certificates**
- Look for your certificate and check its status

Terraform will automatically wait for validation (timeout: 45 minutes). If it times out, just run `terraform apply` again after the DNS propagates.

### Step 6: Point Your Domain to the Load Balancer

Once validated, get your ALB DNS name:

```bash
terraform output alb_dns
```

Add an **A record (with Alias)** or **CNAME record** in your DNS provider:

**Option A: CNAME Record (easier, works for subdomains)**
- **Type:** CNAME
- **Name/Host:** `api` (or your subdomain)
- **Value:** `<alb-dns-name>` (from terraform output)
- **TTL:** 300

**Option B: A Record (requires provider support for ALIAS/ANAME)**
- Some providers (like Cloudflare) support ALIAS/ANAME records
- **Type:** A or ALIAS
- **Name/Host:** `api`
- **Value:** `<alb-dns-name>`

### Step 7: Test Your HTTPS Endpoint

After DNS propagates (5-30 minutes), test your endpoint:

```bash
curl https://api.yourdomain.com/availability/health
```

You should get a response over HTTPS with a valid certificate!

## Verification

Check all outputs:

```bash
# View all SSL-related outputs
terraform output

# Specific checks
terraform output alb_https_url
terraform output availability_service_url
```

## Troubleshooting

### Certificate Stuck in "Pending Validation"

**Cause:** DNS record not found or incorrect

**Solutions:**
1. Verify DNS record was added correctly (check for typos)
2. Use online DNS checker: https://dnschecker.org
3. Check if your provider requires you to exclude the domain suffix
4. Wait longer - some DNS providers take time to propagate

### Terraform Times Out During Validation

**Cause:** DNS hasn't propagated yet

**Solution:**
1. Add DNS records manually in AWS Console or wait
2. Remove the `aws_acm_certificate_validation` resource temporarily
3. Re-run `terraform apply` after DNS propagates

### "Certificate ARN not found" Error

**Cause:** Certificate not created or validation failed

**Solution:**
```bash
# Check if certificate exists
aws acm list-certificates

# Check certificate status
aws acm describe-certificate --certificate-arn <arn>
```

### HTTP Still Works After HTTPS Setup

**Cause:** This is intentional - HTTP redirects to HTTPS

**Test:**
```bash
# Should redirect to HTTPS
curl -L http://api.yourdomain.com/availability/health
```

## Security Best Practices

1. ✅ Use TLS 1.3 (configured via `ELBSecurityPolicy-TLS13-1-2-2021-06`)
2. ✅ HTTP automatically redirects to HTTPS
3. ✅ Certificate auto-renews before expiration
4. ✅ Private keys never leave AWS

## Disabling SSL

To disable SSL and remove the certificate:

1. Set `domain_name = ""` in `terraform.tfvars`
2. Run `terraform apply`
3. Remove DNS records from your provider

## AWS CLI Commands

```bash
# List all certificates
aws acm list-certificates

# Get certificate details
aws acm describe-certificate --certificate-arn <arn>

# Check load balancer listeners
aws elbv2 describe-listeners --load-balancer-arn <alb-arn>

# View HTTPS listener details
aws elbv2 describe-listener-certificates --listener-arn <listener-arn>
```

## Cost

AWS Certificate Manager (ACM) certificates are **free** when used with AWS services like Application Load Balancers.

## Additional Resources

- [AWS ACM Documentation](https://docs.aws.amazon.com/acm/)
- [DNS Validation Guide](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)
- [DNS Checker Tool](https://dnschecker.org)

## Support

If you encounter issues:
1. Check CloudWatch Logs for ALB access logs
2. Verify security groups allow port 443
3. Test with `openssl s_client -connect api.yourdomain.com:443`
