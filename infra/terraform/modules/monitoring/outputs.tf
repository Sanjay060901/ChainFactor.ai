output "ecs_log_group_name" {
  description = "Name of the ECS CloudWatch log group (passthrough from compute module)"
  value       = var.ecs_log_group_name
}

output "ecs_log_group_arn" {
  description = "ARN of the ECS CloudWatch log group (passthrough from compute module)"
  value       = var.ecs_log_group_arn
}
