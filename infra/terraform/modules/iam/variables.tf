variable "project_name" {
  description = "Project name used in resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., staging, production)"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for invoice storage"
  type        = string
}

variable "secrets_arns" {
  description = "List of Secrets Manager secret ARNs the tasks need access to"
  type        = list(string)
}
