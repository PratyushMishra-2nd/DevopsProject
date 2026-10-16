variable "aws_region" {
  description = "AWS region for every resource."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Name prefix for resources."
  type        = string
  default     = "pantrypulse"
}

variable "environment" {
  description = "Environment label added to tags."
  type        = string
  default     = "demo-free-tier"
}

variable "owner" {
  description = "Owner tag value."
  type        = string
  default     = "Pratyush Mishra"
}

variable "availability_zone" {
  description = "AZ of the single public subnet."
  type        = string
  default     = "ap-south-1a"
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC (differs from the EKS stack's 10.42.0.0/16 so both can coexist)."
  type        = string
  default     = "10.43.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block of the public subnet."
  type        = string
  default     = "10.43.0.0/24"
}

variable "instance_type" {
  description = "Free-tier eligible instance type. t3.micro (2 vCPU, 1 GiB) is free-tier eligible on every account; larger free-tier types such as m7i-flex.large are smoother if your account allows them."
  type        = string
  default     = "t3.micro"
}

variable "swap_gb" {
  description = "Swap file size created at boot, so k3s and the app fit on a 1 GiB instance."
  type        = number
  default     = 2
}

variable "root_volume_gb" {
  description = "Root EBS volume size. The free tier covers 30 GB of EBS."
  type        = number
  default     = 30

  validation {
    condition     = var.root_volume_gb >= 20 && var.root_volume_gb <= 30
    error_message = "Keep the root volume between 20 and 30 GB to stay inside the free tier."
  }
}

variable "k3s_version" {
  description = "Pinned k3s release (Kubernetes 1.35, matching the EKS stack)."
  type        = string
  default     = "v1.35.9+k3s1"
}

variable "ami_id" {
  description = "Optional AMI override. Empty = latest Canonical Ubuntu 24.04 LTS (amd64) image."
  type        = string
  default     = ""
}

variable "ssh_public_key" {
  description = "OpenSSH public key for the ubuntu user (contents of ~/.ssh/id_ed25519.pub)."
  type        = string
}

variable "admin_cidrs" {
  description = "CIDRs allowed to reach SSH (22) and the Kubernetes API (6443). Use your own IP/32."
  type        = list(string)

  validation {
    condition     = length(var.admin_cidrs) > 0 && alltrue([for c in var.admin_cidrs : c != "0.0.0.0/0"])
    error_message = "admin_cidrs must be set and must not contain 0.0.0.0/0."
  }
}

variable "web_cidrs" {
  description = "CIDRs allowed to reach the app on HTTP port 80. Empty = same as admin_cidrs; add 0.0.0.0/0 only while someone else needs to open the app."
  type        = list(string)
  default     = []
}
