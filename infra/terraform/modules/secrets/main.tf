# Secrets Module - AWS Secrets Manager
# Manages sensitive configuration for ChainFactor AI.

terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ---------------------------------------------------------------------------
# Database Password Secret
# ---------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "db_password" {
  name        = "${var.project_name}/${var.environment}/db-password"
  description = "RDS PostgreSQL database password for ${var.project_name} ${var.environment}"

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-db-password"
  })
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

# ---------------------------------------------------------------------------
# Algorand App Wallet Mnemonic Secret
# ---------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "algorand_mnemonic" {
  name        = "${var.project_name}/${var.environment}/algorand-mnemonic"
  description = "Algorand application wallet mnemonic for ${var.project_name} ${var.environment}"

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-algorand-mnemonic"
  })
}

resource "aws_secretsmanager_secret_version" "algorand_mnemonic" {
  secret_id     = aws_secretsmanager_secret.algorand_mnemonic.id
  secret_string = var.algorand_mnemonic
}

# ---------------------------------------------------------------------------
# General App Config Secret (JSON blob for additional config)
# ---------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "app_config" {
  name        = "${var.project_name}/${var.environment}/app-config"
  description = "General application configuration for ${var.project_name} ${var.environment}"

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-app-config"
  })
}

resource "aws_secretsmanager_secret_version" "app_config" {
  secret_id = aws_secretsmanager_secret.app_config.id
  secret_string = jsonencode({
    DEMO_MODE = "true"
  })
}
