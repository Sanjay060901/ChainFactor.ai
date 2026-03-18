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

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs of the private subnets for ECS tasks"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks (created externally to avoid circular deps)"
  type        = string
}

variable "alb_target_group_arn" {
  description = "ARN of the ALB target group to register ECS tasks with"
  type        = string
}

variable "alb_security_group_id" {
  description = "Security group ID of the ALB (for reference only)"
  type        = string
}

variable "task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "container_image" {
  description = "Docker image URI for the backend container (e.g., ECR URI)"
  type        = string
  default     = "public.ecr.aws/docker/library/python:3.11-slim"
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}

variable "environment_variables" {
  description = "Map of environment variables to pass to the container"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Map of secret name to Secrets Manager ARN for container secrets"
  type        = map(string)
  default     = {}
}
