# Free-tier alternative to the EKS stack in ../ : one EC2 instance running
# k3s (single-node Kubernetes). The same Helm chart and the same CI-built,
# SHA-tagged images are deployed onto it. See docs/adr/0008-free-tier-ec2-k3s.md.

locals {
  name      = "${var.project}-k3s"
  web_cidrs = length(var.web_cidrs) > 0 ? var.web_cidrs : var.admin_cidrs
  tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
    Repository  = "github.com/PratyushMishra-2nd/DevopsProject"
  }
}

# Latest Canonical Ubuntu 24.04 LTS (amd64, gp3). Looked up with
# ec2:DescribeImages, which plain EC2 permissions already include.
data "aws_ami" "ubuntu" {
  count       = var.ami_id == "" ? 1 : 0
  owners      = ["099720109477"] # Canonical
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
  filter {
    name   = "state"
    values = ["available"]
  }
}

# ---------------------------------------------------------------- network

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${local.name}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name}-igw" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true # one node with a public IP instead of a paid NAT gateway and load balancer

  tags = { Name = "${local.name}-public-${var.availability_zone}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name}-public-rt" }
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Strip all rules from the VPC's default security group so nothing uses it by accident.
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name}-default-unused" }
}

# --------------------------------------------------------------- security

resource "aws_security_group" "node" {
  name        = "${local.name}-node"
  description = "k3s node: SSH and Kubernetes API from admin CIDRs, HTTP from web CIDRs"
  vpc_id      = aws_vpc.main.id
  tags        = { Name = "${local.name}-node" }
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  for_each          = toset(var.admin_cidrs)
  security_group_id = aws_security_group.node.id
  description       = "SSH from admin"
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "aws_vpc_security_group_ingress_rule" "kube_api" {
  for_each          = toset(var.admin_cidrs)
  security_group_id = aws_security_group.node.id
  description       = "Kubernetes API from admin"
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 6443
  to_port           = 6443
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  for_each          = toset(local.web_cidrs)
  security_group_id = aws_security_group.node.id
  description       = "HTTP to the Traefik ingress"
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

# Outbound is limited to web ports: apt (80/443), the k3s download and GHCR
# image pulls (443). DNS and NTP go to the VPC's link-local resolvers, which
# security groups do not filter.
resource "aws_vpc_security_group_egress_rule" "web" {
  for_each          = toset(["80", "443"])
  security_group_id = aws_security_group.node.id
  description       = "Outbound TCP ${each.value} for packages and image pulls"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = tonumber(each.value)
  to_port           = tonumber(each.value)
}

resource "aws_key_pair" "admin" {
  key_name   = "${local.name}-admin"
  public_key = var.ssh_public_key
}

# ---------------------------------------------------------------- compute

resource "aws_instance" "node" {
  ami                    = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu[0].id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.node.id]
  key_name               = aws_key_pair.admin.key_name

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    k3s_version = var.k3s_version
    swap_gb     = var.swap_gb
  })
  user_data_replace_on_change = true

  # Burstable types: standard credit mode, so the instance can never run up
  # unlimited-mode CPU charges.
  credit_specification {
    cpu_credits = "standard"
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 only
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_gb
    encrypted             = true
    delete_on_termination = true
  }

  tags = { Name = "${local.name}-node" }

  lifecycle {
    ignore_changes = [ami] # a newer Ubuntu image must not replace a running demo node
  }
}
