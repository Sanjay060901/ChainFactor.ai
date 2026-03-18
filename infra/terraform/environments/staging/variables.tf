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

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

variable "db_password" {
  description = "RDS PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Name of the default database"
  type        = string
  default     = "chainfactor"
}

variable "db_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "chainfactor_admin"
}

# ---------------------------------------------------------------------------
# Algorand
# ---------------------------------------------------------------------------

variable "algorand_app_wallet_mnemonic" {
  description = "Algorand application wallet mnemonic"
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------

variable "container_image" {
  description = "Docker image URI for the backend container"
  type        = string
  default     = "public.ecr.aws/docker/library/python:3.11-slim"
}
