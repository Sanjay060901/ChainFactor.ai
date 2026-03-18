# IAM Module - ECS Task Execution and Task Roles
# Provides least-privilege IAM roles for ECS Fargate tasks.

terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# ---------------------------------------------------------------------------
# ECS Task Execution Role
# Used by ECS agent to pull images, write logs, and read secrets.
# ---------------------------------------------------------------------------

resource "aws_iam_role" "task_execution" {
  name = "${var.project_name}-${var.environment}-ecs-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-ecs-exec-role"
  })
}

# Attach the AWS-managed ECS task execution policy (ECR pull + CloudWatch logs)
resource "aws_iam_role_policy_attachment" "task_execution_managed" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow reading secrets from Secrets Manager (for container secrets injection)
resource "aws_iam_role_policy" "task_execution_secrets" {
  name = "${var.project_name}-${var.environment}-exec-secrets"
  role = aws_iam_role.task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.secrets_arns
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# ECS Task Role
# Used by the application container for runtime AWS API access.
# ---------------------------------------------------------------------------

resource "aws_iam_role" "task" {
  name = "${var.project_name}-${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-ecs-task-role"
  })
}

# S3 access for invoice uploads and retrieval
resource "aws_iam_role_policy" "task_s3" {
  name = "${var.project_name}-${var.environment}-task-s3"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

# Bedrock access for AI model invocation (Strands Agents SDK)
resource "aws_iam_role_policy" "task_bedrock" {
  name = "${var.project_name}-${var.environment}-task-bedrock"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-sonnet-4-6-20250514",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-haiku-4-5-20250514",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-opus-4-6-20250514"
        ]
      }
    ]
  })
}

# Textract access for invoice OCR
resource "aws_iam_role_policy" "task_textract" {
  name = "${var.project_name}-${var.environment}-task-textract"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "textract:AnalyzeDocument",
          "textract:DetectDocumentText",
          "textract:AnalyzeExpense"
        ]
        Resource = "*"
      }
    ]
  })
}

# Secrets Manager read access for runtime secret retrieval
resource "aws_iam_role_policy" "task_secrets" {
  name = "${var.project_name}-${var.environment}-task-secrets"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.secrets_arns
      }
    ]
  })
}

# Cognito access for user management and token verification
resource "aws_iam_role_policy" "task_cognito" {
  name = "${var.project_name}-${var.environment}-task-cognito"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminCreateUser",
          "cognito-idp:AdminSetUserPassword",
          "cognito-idp:AdminInitiateAuth",
          "cognito-idp:AdminRespondToAuthChallenge"
        ]
        Resource = "arn:aws:cognito-idp:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:userpool/*"
      }
    ]
  })
}

# CloudWatch Logs access for application logging
resource "aws_iam_role_policy" "task_logs" {
  name = "${var.project_name}-${var.environment}-task-logs"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/${var.project_name}-${var.environment}*:*"
      }
    ]
  })
}
