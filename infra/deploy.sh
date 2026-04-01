#!/usr/bin/env bash
# ChainFactor AI - Full AWS Deployment Script
# Deploys backend (ECS Fargate) + frontend (S3 + CloudFront) to AWS
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Terraform >= 1.5.0 installed
#   - Docker running
#   - Node.js 20+ installed
#
# Usage:
#   export TF_VAR_db_password="your-db-password"
#   export TF_VAR_algorand_app_wallet_mnemonic="your-mnemonic"
#   chmod +x deploy.sh
#   ./deploy.sh [bootstrap|infra|backend|frontend|all]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AWS_REGION="ap-south-1"
PROJECT_NAME="chainfactor-ai"
ENVIRONMENT="staging"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
preflight() {
    log_info "Running pre-flight checks..."

    command -v aws >/dev/null 2>&1 || { log_error "AWS CLI not found"; exit 1; }
    command -v terraform >/dev/null 2>&1 || { log_error "Terraform not found"; exit 1; }
    command -v docker >/dev/null 2>&1 || { log_error "Docker not found"; exit 1; }
    command -v node >/dev/null 2>&1 || { log_error "Node.js not found"; exit 1; }

    # Verify AWS credentials
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) || {
        log_error "AWS credentials not configured. Run: aws configure"
        exit 1
    }
    log_ok "AWS Account: $AWS_ACCOUNT_ID (Region: $AWS_REGION)"

    # Check sensitive vars
    if [[ -z "${TF_VAR_db_password:-}" ]]; then
        log_error "TF_VAR_db_password not set. Export it first:"
        echo "  export TF_VAR_db_password=\"your-secure-password\""
        exit 1
    fi
    if [[ -z "${TF_VAR_algorand_app_wallet_mnemonic:-}" ]]; then
        log_error "TF_VAR_algorand_app_wallet_mnemonic not set. Export it first:"
        echo "  export TF_VAR_algorand_app_wallet_mnemonic=\"your 25 word mnemonic\""
        exit 1
    fi

    log_ok "Pre-flight checks passed"
}

# ---------------------------------------------------------------------------
# Step 1: Bootstrap Terraform state backend
# ---------------------------------------------------------------------------
bootstrap() {
    log_info "Step 1: Bootstrapping Terraform state backend..."

    cd "$PROJECT_ROOT/infra/terraform/backends/bootstrap"

    terraform init -input=false
    terraform apply -auto-approve -input=false

    log_ok "Terraform state backend ready"
}

# ---------------------------------------------------------------------------
# Step 2: Apply infrastructure with Terraform
# ---------------------------------------------------------------------------
infra() {
    log_info "Step 2: Applying Terraform infrastructure..."

    cd "$PROJECT_ROOT/infra/terraform/environments/staging"

    terraform init -input=false -reconfigure
    terraform plan -var-file=terraform.tfvars -out=tfplan -input=false
    terraform apply -input=false tfplan

    # Capture outputs
    ECR_REPO_URL=$(terraform output -raw ecr_repository_url)
    ALB_DNS=$(terraform output -raw alb_dns_name)
    CF_DOMAIN=$(terraform output -raw cloudfront_domain)
    CF_DIST_ID=$(terraform output -raw cloudfront_distribution_id)
    FRONTEND_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-frontend"

    log_ok "Infrastructure deployed"
    log_info "  ECR:        $ECR_REPO_URL"
    log_info "  Backend:    http://$ALB_DNS"
    log_info "  Frontend:   https://$CF_DOMAIN"
}

# ---------------------------------------------------------------------------
# Step 3: Build and push backend Docker image to ECR
# ---------------------------------------------------------------------------
deploy_backend() {
    log_info "Step 3: Building and pushing backend Docker image..."

    cd "$PROJECT_ROOT/infra/terraform/environments/staging"
    ECR_REPO_URL=$(terraform output -raw ecr_repository_url)
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    # Build the image
    cd "$PROJECT_ROOT/backend"
    docker build -t "${ECR_REPO_URL}:latest" -t "${ECR_REPO_URL}:$(git rev-parse --short HEAD 2>/dev/null || echo 'dev')" .

    # Push to ECR
    docker push "${ECR_REPO_URL}:latest"
    docker push "${ECR_REPO_URL}:$(git rev-parse --short HEAD 2>/dev/null || echo 'dev')"

    # Force new ECS deployment with the latest image
    ECS_CLUSTER="${PROJECT_NAME}-${ENVIRONMENT}-cluster"
    ECS_SERVICE="${PROJECT_NAME}-${ENVIRONMENT}-backend"

    aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$ECS_SERVICE" \
        --force-new-deployment \
        --region "$AWS_REGION" \
        --no-cli-pager

    log_ok "Backend image pushed and ECS deployment triggered"
    log_info "  Image: ${ECR_REPO_URL}:latest"

    # Wait for service to stabilize
    log_info "Waiting for ECS service to stabilize (this may take 2-5 minutes)..."
    aws ecs wait services-stable \
        --cluster "$ECS_CLUSTER" \
        --services "$ECS_SERVICE" \
        --region "$AWS_REGION" 2>/dev/null || log_warn "Service may still be deploying. Check AWS console."

    log_ok "ECS service stable"
}

# ---------------------------------------------------------------------------
# Step 4: Build and deploy frontend to S3 + CloudFront
# ---------------------------------------------------------------------------
deploy_frontend() {
    log_info "Step 4: Building and deploying frontend..."

    cd "$PROJECT_ROOT/infra/terraform/environments/staging"
    ALB_DNS=$(terraform output -raw alb_dns_name)
    CF_DOMAIN=$(terraform output -raw cloudfront_domain)
    CF_DIST_ID=$(terraform output -raw cloudfront_distribution_id)
    FRONTEND_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-frontend"

    # Build frontend with API URL pointing to ALB
    cd "$PROJECT_ROOT/frontend"
    npm ci --ignore-scripts

    NEXT_PUBLIC_API_URL="http://${ALB_DNS}" \
    NEXT_PUBLIC_WS_URL="ws://${ALB_DNS}" \
        npm run build

    # Sync to S3
    aws s3 sync out/ "s3://${FRONTEND_BUCKET}" \
        --delete \
        --region "$AWS_REGION" \
        --cache-control "public, max-age=3600"

    # Set cache headers for static assets (longer cache)
    aws s3 cp "s3://${FRONTEND_BUCKET}/_next/" "s3://${FRONTEND_BUCKET}/_next/" \
        --recursive \
        --metadata-directive REPLACE \
        --cache-control "public, max-age=31536000, immutable" \
        --region "$AWS_REGION" 2>/dev/null || true

    # Invalidate CloudFront cache
    aws cloudfront create-invalidation \
        --distribution-id "$CF_DIST_ID" \
        --paths "/*" \
        --region us-east-1 \
        --no-cli-pager

    log_ok "Frontend deployed"
    log_info "  URL: https://$CF_DOMAIN"
}

# ---------------------------------------------------------------------------
# Print deployment summary
# ---------------------------------------------------------------------------
summary() {
    cd "$PROJECT_ROOT/infra/terraform/environments/staging"
    ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "N/A")
    CF_DOMAIN=$(terraform output -raw cloudfront_domain 2>/dev/null || echo "N/A")

    echo ""
    echo "=========================================="
    echo "  ChainFactor AI - Deployment Complete"
    echo "=========================================="
    echo ""
    echo "  Backend API:  http://$ALB_DNS"
    echo "  Health Check: http://$ALB_DNS/health"
    echo "  Frontend:     https://$CF_DOMAIN"
    echo "  API Docs:     http://$ALB_DNS/docs"
    echo ""
    echo "=========================================="
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    local cmd="${1:-all}"

    preflight

    case "$cmd" in
        bootstrap)
            bootstrap
            ;;
        infra)
            infra
            ;;
        backend)
            deploy_backend
            ;;
        frontend)
            deploy_frontend
            ;;
        all)
            bootstrap
            infra
            deploy_backend
            deploy_frontend
            summary
            ;;
        *)
            echo "Usage: $0 [bootstrap|infra|backend|frontend|all]"
            exit 1
            ;;
    esac
}

main "$@"
