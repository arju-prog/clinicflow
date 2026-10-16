terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Optional but recommended for teams: keep state in S3 instead of on one laptop.
  # Create the bucket once, then uncomment and run `terraform init -migrate-state`.
  # backend "s3" {
  #   bucket       = "clinicflow-tfstate-<your-account-id>"
  #   key          = "eks/terraform.tfstate"
  #   region       = "ap-south-1"
  #   use_lockfile = true
  # }
}

provider "aws" {
  region = var.aws_region

  # Every resource Terraform creates gets these tags, which makes cost tracking and
  # "what did I forget to destroy?" checks in the AWS console easy.
  default_tags {
    tags = local.tags
  }
}
