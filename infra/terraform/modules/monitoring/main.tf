# Monitoring Module - CloudWatch Log Groups and Alarms
# Provides observability for ChainFactor AI ECS backend.
# Note: The ECS log group is created by the compute module (tightly coupled to task definition).
# This module receives the log group name/ARN as inputs for reference and creates additional
# monitoring resources (alarms, ALB log group).

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
# CloudWatch Log Group for ALB Access Logs (optional)
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "alb" {
  name              = "/alb/${var.project_name}-${var.environment}"
  retention_in_days = 7

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-alb-logs"
  })
}

# ---------------------------------------------------------------------------
# CloudWatch Alarm - ECS CPU Utilization > 80% for 5 minutes
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-ecs-cpu-high"
  alarm_description   = "ECS CPU utilization exceeds 80% for 5 minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-cpu-alarm"
  })
}

# ---------------------------------------------------------------------------
# CloudWatch Alarm - ECS Memory Utilization > 85% for 5 minutes
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "ecs_memory_high" {
  alarm_name          = "${var.project_name}-${var.environment}-ecs-memory-high"
  alarm_description   = "ECS memory utilization exceeds 85% for 5 minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-memory-alarm"
  })
}
