output "db_password_secret_arn" {
  description = "ARN of the database password secret"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "algorand_mnemonic_secret_arn" {
  description = "ARN of the Algorand mnemonic secret"
  value       = aws_secretsmanager_secret.algorand_mnemonic.arn
}

output "app_config_secret_arn" {
  description = "ARN of the general app config secret"
  value       = aws_secretsmanager_secret.app_config.arn
}
