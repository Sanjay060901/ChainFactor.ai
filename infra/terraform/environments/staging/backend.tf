terraform {
  backend "s3" {
    bucket         = "chainfactor-ai-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "chainfactor-ai-terraform-locks"
    encrypt        = true
  }
}
