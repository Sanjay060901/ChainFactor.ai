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

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster (for CloudWatch alarm dimensions)"
  type        = string
}

variable "ecs_service_name" {
  description = "Name of the ECS service (for CloudWatch alarm dimensions)"
  type        = string
}

variable "ecs_log_group_name" {
  description = "Name of the ECS CloudWatch log group (created by compute module)"
  type        = string
}

variable "ecs_log_group_arn" {
  description = "ARN of the ECS CloudWatch log group (created by compute module)"
  type        = string
}
