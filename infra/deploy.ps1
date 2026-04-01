# ChainFactor AI - Full AWS Deployment Script (PowerShell)
# Deploys backend (ECS Fargate) + frontend (S3 + CloudFront) to AWS
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Terraform >= 1.5.0 installed
#   - Docker running
#   - Node.js 20+ installed
#
# Usage:
#   $env:TF_VAR_db_password = "your-db-password"
#   $env:TF_VAR_algorand_app_wallet_mnemonic = "your-mnemonic"
#   .\deploy.ps1 [-Step all|bootstrap|infra|backend|frontend]

param(
    [ValidateSet("all", "bootstrap", "infra", "backend", "frontend")]
    [string]$Step = "all"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $ProjectRoot) { $ProjectRoot = (Get-Location).Path | Split-Path -Parent }
# Fallback: use script location
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$ProjectRoot = Split-Path -Parent $ScriptDir

$AwsRegion = "ap-south-1"
$ProjectName = "chainfactor-ai"
$Environment = "staging"

function Write-Step($msg) { Write-Host "[STEP] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR]  $msg" -ForegroundColor Red }

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
function Test-Preflight {
    Write-Step "Running pre-flight checks..."

    foreach ($cmd in @("aws", "terraform", "docker", "node")) {
        if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
            Write-Err "$cmd not found in PATH"
            exit 1
        }
    }

    # Verify AWS credentials
    $script:AwsAccountId = aws sts get-caller-identity --query Account --output text 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Err "AWS credentials not configured. Run: aws configure"
        exit 1
    }
    Write-Ok "AWS Account: $script:AwsAccountId (Region: $AwsRegion)"

    # Check sensitive vars
    if (-not $env:TF_VAR_db_password) {
        Write-Err 'TF_VAR_db_password not set. Run: $env:TF_VAR_db_password = "your-password"'
        exit 1
    }
    if (-not $env:TF_VAR_algorand_app_wallet_mnemonic) {
        Write-Err 'TF_VAR_algorand_app_wallet_mnemonic not set. Run: $env:TF_VAR_algorand_app_wallet_mnemonic = "your mnemonic"'
        exit 1
    }

    Write-Ok "Pre-flight checks passed"
}

# ---------------------------------------------------------------------------
# Step 1: Bootstrap Terraform state backend
# ---------------------------------------------------------------------------
function Invoke-Bootstrap {
    Write-Step "Step 1: Bootstrapping Terraform state backend..."

    Push-Location "$ProjectRoot\infra\terraform\backends\bootstrap"
    try {
        terraform init -input=false
        if ($LASTEXITCODE -ne 0) { throw "terraform init failed" }

        terraform apply -auto-approve -input=false
        if ($LASTEXITCODE -ne 0) { throw "terraform apply failed" }

        Write-Ok "Terraform state backend ready"
    } finally {
        Pop-Location
    }
}

# ---------------------------------------------------------------------------
# Step 2: Apply Terraform infrastructure
# ---------------------------------------------------------------------------
function Invoke-Infra {
    Write-Step "Step 2: Applying Terraform infrastructure..."

    Push-Location "$ProjectRoot\infra\terraform\environments\staging"
    try {
        terraform init -input=false -reconfigure
        if ($LASTEXITCODE -ne 0) { throw "terraform init failed" }

        terraform plan -var-file=terraform.tfvars -out=tfplan -input=false
        if ($LASTEXITCODE -ne 0) { throw "terraform plan failed" }

        terraform apply -input=false tfplan
        if ($LASTEXITCODE -ne 0) { throw "terraform apply failed" }

        $script:EcrRepoUrl = terraform output -raw ecr_repository_url
        $script:AlbDns     = terraform output -raw alb_dns_name
        $script:CfDomain   = terraform output -raw cloudfront_domain
        $script:CfDistId   = terraform output -raw cloudfront_distribution_id

        Write-Ok "Infrastructure deployed"
        Write-Host "  ECR:      $script:EcrRepoUrl"
        Write-Host "  Backend:  http://$script:AlbDns"
        Write-Host "  Frontend: https://$script:CfDomain"
    } finally {
        Pop-Location
    }
}

# ---------------------------------------------------------------------------
# Step 3: Build and push backend Docker image
# ---------------------------------------------------------------------------
function Invoke-DeployBackend {
    Write-Step "Step 3: Building and pushing backend Docker image..."

    Push-Location "$ProjectRoot\infra\terraform\environments\staging"
    $EcrRepoUrl = terraform output -raw ecr_repository_url
    Pop-Location

    $AwsAccountId = aws sts get-caller-identity --query Account --output text

    # Login to ECR
    $ecrPassword = aws ecr get-login-password --region $AwsRegion
    $ecrPassword | docker login --username AWS --password-stdin "$AwsAccountId.dkr.ecr.$AwsRegion.amazonaws.com"
    if ($LASTEXITCODE -ne 0) { throw "ECR login failed" }

    # Build
    Push-Location "$ProjectRoot\backend"
    try {
        $gitHash = git rev-parse --short HEAD 2>$null
        if (-not $gitHash) { $gitHash = "dev" }

        docker build -t "${EcrRepoUrl}:latest" -t "${EcrRepoUrl}:$gitHash" .
        if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }

        # Push
        docker push "${EcrRepoUrl}:latest"
        if ($LASTEXITCODE -ne 0) { throw "Docker push (latest) failed" }

        docker push "${EcrRepoUrl}:$gitHash"
        if ($LASTEXITCODE -ne 0) { throw "Docker push ($gitHash) failed" }
    } finally {
        Pop-Location
    }

    # Force new ECS deployment
    $ecsCluster = "$ProjectName-$Environment-cluster"
    $ecsService = "$ProjectName-$Environment-backend"

    aws ecs update-service `
        --cluster $ecsCluster `
        --service $ecsService `
        --force-new-deployment `
        --region $AwsRegion `
        --no-cli-pager
    if ($LASTEXITCODE -ne 0) { throw "ECS update-service failed" }

    Write-Ok "Backend image pushed and ECS deployment triggered"

    # Wait for service to stabilize
    Write-Step "Waiting for ECS service to stabilize (2-5 minutes)..."
    aws ecs wait services-stable `
        --cluster $ecsCluster `
        --services $ecsService `
        --region $AwsRegion 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Ok "ECS service stable"
    } else {
        Write-Warn "Service may still be deploying. Check AWS console."
    }
}

# ---------------------------------------------------------------------------
# Step 4: Build and deploy frontend
# ---------------------------------------------------------------------------
function Invoke-DeployFrontend {
    Write-Step "Step 4: Building and deploying frontend..."

    Push-Location "$ProjectRoot\infra\terraform\environments\staging"
    $AlbDns = terraform output -raw alb_dns_name
    $CfDomain = terraform output -raw cloudfront_domain
    $CfDistId = terraform output -raw cloudfront_distribution_id
    Pop-Location

    $FrontendBucket = "$ProjectName-$Environment-frontend"

    Push-Location "$ProjectRoot\frontend"
    try {
        npm ci --ignore-scripts

        # Build with API URL pointing to ALB
        $env:NEXT_PUBLIC_API_URL = "http://$AlbDns"
        $env:NEXT_PUBLIC_WS_URL = "ws://$AlbDns"
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }

        # Sync to S3
        aws s3 sync out/ "s3://$FrontendBucket" `
            --delete `
            --region $AwsRegion `
            --cache-control "public, max-age=3600"
        if ($LASTEXITCODE -ne 0) { throw "S3 sync failed" }

        # Longer cache for _next/ static assets
        aws s3 cp "s3://$FrontendBucket/_next/" "s3://$FrontendBucket/_next/" `
            --recursive `
            --metadata-directive REPLACE `
            --cache-control "public, max-age=31536000, immutable" `
            --region $AwsRegion 2>$null

        # Invalidate CloudFront
        aws cloudfront create-invalidation `
            --distribution-id $CfDistId `
            --paths "/*" `
            --region us-east-1 `
            --no-cli-pager
        if ($LASTEXITCODE -ne 0) { throw "CloudFront invalidation failed" }

    } finally {
        # Clean up env vars
        Remove-Item Env:\NEXT_PUBLIC_API_URL -ErrorAction SilentlyContinue
        Remove-Item Env:\NEXT_PUBLIC_WS_URL -ErrorAction SilentlyContinue
        Pop-Location
    }

    Write-Ok "Frontend deployed to https://$CfDomain"
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
function Show-Summary {
    Push-Location "$ProjectRoot\infra\terraform\environments\staging"
    $AlbDns   = terraform output -raw alb_dns_name 2>$null
    $CfDomain = terraform output -raw cloudfront_domain 2>$null
    Pop-Location

    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "  ChainFactor AI - Deployment Complete" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Backend API:  http://$AlbDns"
    Write-Host "  Health Check: http://$AlbDns/health"
    Write-Host "  Frontend:     https://$CfDomain"
    Write-Host "  API Docs:     http://$AlbDns/docs"
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
Test-Preflight

switch ($Step) {
    "bootstrap" { Invoke-Bootstrap }
    "infra"     { Invoke-Infra }
    "backend"   { Invoke-DeployBackend }
    "frontend"  { Invoke-DeployFrontend }
    "all"       {
        Invoke-Bootstrap
        Invoke-Infra
        Invoke-DeployBackend
        Invoke-DeployFrontend
        Show-Summary
    }
}
