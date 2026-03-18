output "invoice_bucket_name" {
  description = "Name of the invoice storage S3 bucket"
  value       = aws_s3_bucket.invoices.id
}

output "invoice_bucket_arn" {
  description = "ARN of the invoice storage S3 bucket"
  value       = aws_s3_bucket.invoices.arn
}

output "frontend_bucket_name" {
  description = "Name of the frontend hosting S3 bucket"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_bucket_arn" {
  description = "ARN of the frontend hosting S3 bucket"
  value       = aws_s3_bucket.frontend.arn
}

output "frontend_bucket_regional_domain_name" {
  description = "Regional domain name of the frontend S3 bucket (for CloudFront origin)"
  value       = aws_s3_bucket.frontend.bucket_regional_domain_name
}
