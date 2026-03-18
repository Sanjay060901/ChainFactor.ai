# ChainFactor AI - Staging Environment
# Composes all modules for the AWS staging (hackathon production) environment.
#
# Usage:
#   cd infra/terraform/environments/staging
#   terraform init
#   terraform plan -var-file=terraform.tfvars
#   terraform apply -var-file=terraform.tfvars

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ChainFactor-AI"
      Environment = "staging"
      ManagedBy   = "terraform"
      Owner       = "manoj"
    }
  }
}

# ---------------------------------------------------------------------------
# Local values
# ---------------------------------------------------------------------------

locals {
  common_tags = {
    Project     = "ChainFactor-AI"
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = "manoj"
  }
}

# ---------------------------------------------------------------------------
# 1. Networking - VPC, Subnets, NAT Gateway, Internet Gateway
# ---------------------------------------------------------------------------

module "networking" {
  source = "../../modules/networking"

  project_name         = var.project_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  tags                 = local.common_tags
}

# ---------------------------------------------------------------------------
# ECS Security Group (root-level to break circular dependency)
# Compute needs DB/Redis endpoints -> DB/Redis need ECS SG ID.
# Creating the SG here allows all three modules to reference it.
# ---------------------------------------------------------------------------

resource "aws_security_group" "ecs" {
  name        = "${var.project_name}-${var.environment}-ecs-sg"
  description = "Security group for ECS Fargate tasks"
  vpc_id      = module.networking.vpc_id

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-ecs-sg"
  })
}

resource "aws_security_group_rule" "ecs_ingress_alb" {
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = module.load_balancer.alb_security_group_id
  security_group_id        = aws_security_group.ecs.id
  description              = "Allow traffic from ALB on container port"
}

resource "aws_security_group_rule" "ecs_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.ecs.id
  description       = "Allow all outbound (ECR, Bedrock, Secrets Manager, etc.)"
}

# ---------------------------------------------------------------------------
# 3. Auth - Cognito User Pool + App Client
# ---------------------------------------------------------------------------

module "auth" {
  source = "../../modules/auth"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
}

# ---------------------------------------------------------------------------
# 4. Secrets - Secrets Manager
# ---------------------------------------------------------------------------

module "secrets" {
  source = "../../modules/secrets"

  project_name      = var.project_name
  environment       = var.environment
  db_password       = var.db_password
  algorand_mnemonic = var.algorand_app_wallet_mnemonic
  tags              = local.common_tags
}

# ---------------------------------------------------------------------------
# 7. Storage - S3 Buckets (invoices + frontend)
# ---------------------------------------------------------------------------

module "storage" {
  source = "../../modules/storage"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
}

# ---------------------------------------------------------------------------
# 9. Load Balancer - ALB
# ---------------------------------------------------------------------------

module "load_balancer" {
  source = "../../modules/load_balancer"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  tags              = local.common_tags
}

# ---------------------------------------------------------------------------
# 2. IAM - ECS Roles and Policies
# ---------------------------------------------------------------------------

module "iam" {
  source = "../../modules/iam"

  project_name  = var.project_name
  environment   = var.environment
  s3_bucket_arn = module.storage.invoice_bucket_arn
  secrets_arns = [
    module.secrets.db_password_secret_arn,
    module.secrets.algorand_mnemonic_secret_arn,
    module.secrets.app_config_secret_arn,
  ]
  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# 5. Database - RDS PostgreSQL
# ---------------------------------------------------------------------------

module "database" {
  source = "../../modules/database"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  private_subnet_ids    = module.networking.private_subnet_ids
  ecs_security_group_id = aws_security_group.ecs.id
  db_password           = var.db_password
  db_name               = var.db_name
  db_username           = var.db_username
  tags                  = local.common_tags
}

# ---------------------------------------------------------------------------
# 6. Cache - ElastiCache Redis
# ---------------------------------------------------------------------------

module "cache" {
  source = "../../modules/cache"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  private_subnet_ids    = module.networking.private_subnet_ids
  ecs_security_group_id = aws_security_group.ecs.id
  tags                  = local.common_tags
}

# ---------------------------------------------------------------------------
# 8. Compute - ECS Fargate Cluster, Service, Task Definition
# ---------------------------------------------------------------------------

module "compute" {
  source = "../../modules/compute"

  project_name           = var.project_name
  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  ecs_security_group_id  = aws_security_group.ecs.id
  alb_target_group_arn   = module.load_balancer.target_group_arn
  alb_security_group_id  = module.load_balancer.alb_security_group_id
  task_execution_role_arn = module.iam.task_execution_role_arn
  task_role_arn          = module.iam.task_role_arn
  container_image        = var.container_image
  container_port         = 8000
  tags                   = local.common_tags

  environment_variables = {
    ENVIRONMENT           = var.environment
    PROJECT_NAME          = var.project_name
    AWS_REGION            = var.aws_region
    DATABASE_HOST         = module.database.endpoint
    DATABASE_PORT         = tostring(module.database.port)
    DATABASE_NAME         = module.database.db_name
    DATABASE_USERNAME     = var.db_username
    REDIS_HOST            = module.cache.endpoint
    REDIS_PORT            = tostring(module.cache.port)
    S3_BUCKET_NAME        = module.storage.invoice_bucket_name
    COGNITO_USER_POOL_ID  = module.auth.user_pool_id
    COGNITO_APP_CLIENT_ID = module.auth.app_client_id
    ALGORAND_ALGOD_URL    = "https://testnet-api.algonode.cloud"
    ALGORAND_INDEXER_URL  = "https://testnet-idx.algonode.cloud"
    DEMO_MODE             = "true"
  }

  secrets = {
    DB_PASSWORD                  = module.secrets.db_password_secret_arn
    ALGORAND_APP_WALLET_MNEMONIC = module.secrets.algorand_mnemonic_secret_arn
    APP_CONFIG                   = module.secrets.app_config_secret_arn
  }
}

# ---------------------------------------------------------------------------
# 10. CDN - CloudFront Distribution
# ---------------------------------------------------------------------------

module "cdn" {
  source = "../../modules/cdn"

  project_name                         = var.project_name
  environment                          = var.environment
  frontend_bucket_regional_domain_name = module.storage.frontend_bucket_regional_domain_name
  frontend_bucket_arn                  = module.storage.frontend_bucket_arn
  frontend_bucket_name                 = module.storage.frontend_bucket_name
  tags                                 = local.common_tags
}

# ---------------------------------------------------------------------------
# 11. Monitoring - CloudWatch Alarms
# ---------------------------------------------------------------------------

module "monitoring" {
  source = "../../modules/monitoring"

  project_name       = var.project_name
  environment        = var.environment
  ecs_cluster_name   = module.compute.cluster_name
  ecs_service_name   = module.compute.service_name
  ecs_log_group_name = module.compute.ecs_log_group_name
  ecs_log_group_arn  = module.compute.ecs_log_group_arn
  tags               = local.common_tags
}
