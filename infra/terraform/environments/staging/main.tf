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

# Modules will be wired here in Feature 1.6
# module "networking" { ... }
# module "iam" { ... }
# module "auth" { ... }
# module "secrets" { ... }
# module "database" { ... }
# module "cache" { ... }
# module "storage" { ... }
# module "compute" { ... }
# module "load_balancer" { ... }
# module "cdn" { ... }
# module "monitoring" { ... }
