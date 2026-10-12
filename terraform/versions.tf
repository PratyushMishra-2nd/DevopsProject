terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }

  # State stays local for this single-person capstone (and is git-ignored).
  # A team would use an S3 backend with native lockfile locking, e.g.:
  # backend "s3" {
  #   bucket       = "pantrypulse-tfstate-<account-id>"
  #   key          = "eks/terraform.tfstate"
  #   region       = "ap-south-1"
  #   use_lockfile = true
  # }
}

provider "aws" {
  region = var.aws_region

  # offline_plan=true lets `terraform plan` render the full change set on a
  # machine without AWS credentials (no API calls are needed to plan new
  # resources here). It must stay false for apply/destroy.
  skip_credentials_validation = var.offline_plan
  skip_requesting_account_id  = var.offline_plan
  skip_metadata_api_check     = var.offline_plan

  default_tags {
    tags = local.tags
  }
}
