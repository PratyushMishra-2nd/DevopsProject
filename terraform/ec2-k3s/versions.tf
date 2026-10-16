terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }

  # Local, git-ignored state, as for the EKS stack in ../
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.tags
  }
}
