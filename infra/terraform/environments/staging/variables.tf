variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "chainfactor-ai"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "db_password" {
  description = "RDS PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "algorand_app_wallet_mnemonic" {
  description = "Algorand application wallet mnemonic"
  type        = string
  sensitive   = true
}
