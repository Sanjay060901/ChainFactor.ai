terraform {
  backend "s3" {
    bucket         = "chainfactor-ai-terraform-state-404290032126"
    key            = "staging/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "chainfactor-ai-terraform-locks"
    encrypt        = true
  }
}
