# ---------------------------------------------------------------------------
# ECR
# ---------------------------------------------------------------------------

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.ecr.repository_url
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

# ---------------------------------------------------------------------------
# Load Balancer
# ---------------------------------------------------------------------------

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer (backend API endpoint)"
  value       = module.load_balancer.alb_dns_name
}

# ---------------------------------------------------------------------------
# CDN
# ---------------------------------------------------------------------------

output "cloudfront_domain" {
  description = "Domain name of the CloudFront distribution (frontend URL)"
  value       = module.cdn.distribution_domain_name
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution (for cache invalidation)"
  value       = module.cdn.distribution_id
}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.database.endpoint
}

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.cache.endpoint
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.auth.user_pool_id
}

output "cognito_app_client_id" {
  description = "Cognito App Client ID"
  value       = module.auth.app_client_id
}

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

output "invoice_bucket_name" {
  description = "Name of the invoice storage S3 bucket"
  value       = module.storage.invoice_bucket_name
}

output "frontend_bucket_name" {
  description = "Name of the frontend hosting S3 bucket"
  value       = module.storage.frontend_bucket_name
}

# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.compute.cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.compute.service_name
}

# ---------------------------------------------------------------------------
# Monitoring
# ---------------------------------------------------------------------------

output "ecs_log_group_name" {
  description = "Name of the ECS CloudWatch log group"
  value       = module.monitoring.ecs_log_group_name
}
