variable "aws_region" {
  description = "AWS region for every resource."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Name prefix for resources and the EKS cluster."
  type        = string
  default     = "pantrypulse"
}

variable "environment" {
  description = "Environment label added to tags."
  type        = string
  default     = "demo"
}

variable "owner" {
  description = "Owner tag value."
  type        = string
  default     = "Pratyush Mishra"
}

variable "availability_zones" {
  description = "Two (or more) AZs in the region. Listed explicitly so planning needs no API lookup."
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "EKS needs subnets in at least two availability zones."
  }
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "One public subnet per AZ (load balancers, and worker nodes when NAT is off)."
  type        = list(string)
  default     = ["10.42.0.0/20", "10.42.16.0/20"]
}

variable "private_subnet_cidrs" {
  description = "One private subnet per AZ (EKS control-plane ENIs, and worker nodes when NAT is on)."
  type        = list(string)
  default     = ["10.42.128.0/20", "10.42.144.0/20"]
}

variable "enable_nat_gateway" {
  description = "Put worker nodes in private subnets behind one NAT gateway (~US$0.056/h + data). Off for the low-cost demo."
  type        = bool
  default     = false
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version (keep inside standard support to avoid extended-support pricing)."
  type        = string
  default     = "1.35"
}

variable "api_allowed_cidrs" {
  description = "CIDRs allowed to reach the public Kubernetes API endpoint, e.g. [\"<your-ip>/32\"]."
  type        = list(string)

  validation {
    condition     = length(var.api_allowed_cidrs) > 0 && !contains(var.api_allowed_cidrs, "0.0.0.0/0")
    error_message = "Restrict the API endpoint to known CIDRs; 0.0.0.0/0 is not allowed."
  }
}

variable "node_instance_types" {
  description = "Instance types for the managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 1
}

variable "node_max_size" {
  type    = number
  default = 3
}

variable "node_disk_size_gb" {
  type    = number
  default = 20
}

variable "enable_control_plane_logs" {
  description = "Ship API/audit/authenticator logs to CloudWatch (adds CloudWatch cost)."
  type        = bool
  default     = false
}

variable "enable_secrets_encryption" {
  description = "Envelope-encrypt Kubernetes Secrets with a customer-managed KMS key (US$1/month per key)."
  type        = bool
  default     = false
}

variable "offline_plan" {
  description = "Skip AWS credential checks so `terraform plan` works without an account. Never use for apply."
  type        = bool
  default     = false
}
