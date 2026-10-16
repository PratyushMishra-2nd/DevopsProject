# Offline tests with a mocked AWS provider: they check the shape of the stack,
# not that AWS accepts it (only a real apply can do that).

mock_provider "aws" {}

variables {
  admin_cidrs    = ["203.0.113.10/32"]
  ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExampleOnlyKeyForTests test"
  ami_id         = "ami-0123456789abcdef0"
}

run "single_free_tier_node" {
  command = plan

  assert {
    condition     = aws_instance.node.instance_type == "t3.micro"
    error_message = "Default instance type should be the free-tier t3.micro"
  }
  assert {
    condition     = aws_instance.node.root_block_device[0].volume_size <= 30 && aws_instance.node.root_block_device[0].encrypted
    error_message = "Root volume must be encrypted and within the 30 GB free tier"
  }
  assert {
    condition     = aws_instance.node.metadata_options[0].http_tokens == "required"
    error_message = "IMDSv2 must be enforced"
  }
  assert {
    condition     = aws_instance.node.credit_specification[0].cpu_credits == "standard"
    error_message = "Standard CPU credits avoid unlimited-mode charges"
  }
}

run "admin_ports_only_from_admin_cidrs" {
  command = plan

  assert {
    condition     = alltrue([for r in aws_vpc_security_group_ingress_rule.ssh : r.cidr_ipv4 == "203.0.113.10/32"])
    error_message = "SSH must only be open to admin_cidrs"
  }
  assert {
    condition     = alltrue([for r in aws_vpc_security_group_ingress_rule.kube_api : r.cidr_ipv4 == "203.0.113.10/32"])
    error_message = "The Kubernetes API must only be open to admin_cidrs"
  }
  assert {
    condition     = alltrue([for r in aws_vpc_security_group_ingress_rule.http : r.cidr_ipv4 == "203.0.113.10/32"])
    error_message = "HTTP should default to admin_cidrs"
  }
}

run "k3s_version_is_pinned" {
  command = plan

  assert {
    condition     = strcontains(aws_instance.node.user_data, "INSTALL_K3S_VERSION=\"v1.35.9+k3s1\"")
    error_message = "User data must install the pinned k3s release"
  }
  assert {
    condition     = strcontains(aws_instance.node.user_data, "fallocate -l 2G /swapfile") && strcontains(aws_instance.node.user_data, "fail-swap-on=false")
    error_message = "User data must add swap and let the kubelet run with it"
  }
}

run "rejects_world_open_admin_cidr" {
  command = plan

  variables {
    admin_cidrs = ["0.0.0.0/0"]
  }

  expect_failures = [var.admin_cidrs]
}
