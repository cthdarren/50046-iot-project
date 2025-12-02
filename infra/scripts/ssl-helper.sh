#!/bin/bash

# =========================================================
# SSL Certificate Setup Helper Script
# =========================================================
# This script helps you set up SSL/TLS certificates for your custom domain

set -e

COLOR_RESET="\033[0m"
COLOR_GREEN="\033[0;32m"
COLOR_YELLOW="\033[0;33m"
COLOR_RED="\033[0;31m"
COLOR_BLUE="\033[0;34m"

echo -e "${COLOR_BLUE}"
echo "=========================================="
echo "   SSL Certificate Setup Helper"
echo "=========================================="
echo -e "${COLOR_RESET}"

# Check if we're in the right directory
if [ ! -f "acm.tf" ]; then
    echo -e "${COLOR_RED}Error: Must be run from the infra/ directory${COLOR_RESET}"
    exit 1
fi

# Function to show DNS validation records
show_dns_records() {
    echo -e "${COLOR_GREEN}==> Getting DNS Validation Records...${COLOR_RESET}"
    echo ""

    if ! terraform output acm_certificate_dns_validation_records 2>/dev/null; then
        echo -e "${COLOR_RED}Error: Could not get DNS validation records${COLOR_RESET}"
        echo "Make sure you've run 'terraform apply' with domain_name set"
        exit 1
    fi

    echo ""
    echo -e "${COLOR_YELLOW}==> Add these DNS records to your domain provider${COLOR_RESET}"
    echo "   (GoDaddy, Namecheap, Cloudflare, etc.)"
    echo ""
}

# Function to check certificate status
check_cert_status() {
    echo -e "${COLOR_GREEN}==> Checking Certificate Status...${COLOR_RESET}"
    echo ""

    CERT_ARN=$(terraform output -raw acm_certificate_arn 2>/dev/null || echo "")

    if [ -z "$CERT_ARN" ]; then
        echo -e "${COLOR_RED}No certificate found. Set domain_name in terraform.tfvars${COLOR_RESET}"
        exit 1
    fi

    echo "Certificate ARN: $CERT_ARN"
    echo ""

    aws acm describe-certificate --certificate-arn "$CERT_ARN" --query 'Certificate.Status' --output text
}

# Function to show ALB DNS
show_alb_dns() {
    echo -e "${COLOR_GREEN}==> Load Balancer DNS Name${COLOR_RESET}"
    echo ""

    ALB_DNS=$(terraform output -raw alb_dns 2>/dev/null || echo "")

    if [ -z "$ALB_DNS" ]; then
        echo -e "${COLOR_RED}Could not get ALB DNS${COLOR_RESET}"
        exit 1
    fi

    echo "ALB DNS: $ALB_DNS"
    echo ""
    echo -e "${COLOR_YELLOW}==> Point your domain to this address:${COLOR_RESET}"
    echo "   Add a CNAME record:"
    echo "   Type:  CNAME"
    echo "   Name:  <your-subdomain> (e.g., 'api')"
    echo "   Value: $ALB_DNS"
    echo ""
}

# Function to test HTTPS endpoint
test_https() {
    DOMAIN=$(terraform output -raw alb_https_url 2>/dev/null | sed 's|https://||' | sed 's|/.*||' || echo "")

    if [ -z "$DOMAIN" ] || [ "$DOMAIN" == "Not configured - set domain_name variable" ]; then
        echo -e "${COLOR_RED}Domain not configured${COLOR_RESET}"
        exit 1
    fi

    echo -e "${COLOR_GREEN}==> Testing HTTPS Endpoint: $DOMAIN${COLOR_RESET}"
    echo ""

    echo "1. DNS Resolution:"
    nslookup "$DOMAIN" || echo "   DNS not resolved yet"
    echo ""

    echo "2. HTTPS Connection Test:"
    curl -v --max-time 5 "https://$DOMAIN/availability/health" 2>&1 | grep -E "(Connected|SSL|certificate|HTTP)" || echo "   Connection failed"
    echo ""

    echo "3. Certificate Info:"
    echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "   Could not retrieve certificate"
}

# Function to check DNS propagation
check_dns() {
    DOMAIN=$(terraform output -raw alb_https_url 2>/dev/null | sed 's|https://||' | sed 's|/.*||' || echo "")

    if [ -z "$DOMAIN" ] || [ "$DOMAIN" == "Not configured - set domain_name variable" ]; then
        echo -e "${COLOR_RED}Domain not configured${COLOR_RESET}"
        exit 1
    fi

    echo -e "${COLOR_GREEN}==> Checking DNS Propagation for: $DOMAIN${COLOR_RESET}"
    echo ""
    echo "Use online tools for global propagation check:"
    echo "  https://dnschecker.org/#A/$DOMAIN"
    echo "  https://dnschecker.org/#CNAME/$DOMAIN"
    echo ""

    echo "Local DNS lookup:"
    dig "$DOMAIN" +short || nslookup "$DOMAIN" || echo "DNS not resolved"
}

# Function to show full setup summary
show_summary() {
    echo -e "${COLOR_BLUE}=========================================="
    echo "   SSL Setup Summary"
    echo "==========================================${COLOR_RESET}"
    echo ""

    echo -e "${COLOR_GREEN}Certificate Status:${COLOR_RESET}"
    check_cert_status 2>/dev/null || echo "Not configured"
    echo ""

    echo -e "${COLOR_GREEN}URLs:${COLOR_RESET}"
    terraform output alb_https_url 2>/dev/null || echo "Not configured"
    terraform output availability_service_url 2>/dev/null || echo "Not configured"
    terraform output analytics_service_url 2>/dev/null || echo "Not configured"
    echo ""
}

# Main menu
case "${1:-}" in
    "dns-records"|"dns")
        show_dns_records
        ;;
    "cert-status"|"status")
        check_cert_status
        ;;
    "alb-dns"|"alb")
        show_alb_dns
        ;;
    "test")
        test_https
        ;;
    "check-dns")
        check_dns
        ;;
    "summary")
        show_summary
        ;;
    *)
        echo "Usage: $0 {dns-records|cert-status|alb-dns|test|check-dns|summary}"
        echo ""
        echo "Commands:"
        echo "  dns-records   - Show DNS validation records to add to your provider"
        echo "  cert-status   - Check ACM certificate validation status"
        echo "  alb-dns       - Show ALB DNS name for CNAME record"
        echo "  test          - Test HTTPS endpoint and certificate"
        echo "  check-dns     - Check DNS propagation status"
        echo "  summary       - Show complete SSL setup summary"
        echo ""
        echo "Example workflow:"
        echo "  1. Set domain_name in terraform.tfvars"
        echo "  2. terraform apply"
        echo "  3. $0 dns-records     (add these to your DNS provider)"
        echo "  4. $0 cert-status     (wait for ISSUED status)"
        echo "  5. $0 alb-dns         (add CNAME to your DNS provider)"
        echo "  6. $0 check-dns       (verify DNS propagation)"
        echo "  7. $0 test            (test HTTPS endpoint)"
        exit 1
        ;;
esac
