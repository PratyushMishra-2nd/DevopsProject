# Offline tests: a mocked AWS provider lets `terraform test` evaluate the plan
# without credentials or cost. They prove the shape of the infrastructure,
# not that AWS accepts it (only a real apply can do that).

mock_provider "aws" {}

variables {
  api_allowed_cidrs = ["203.0.113.10/32"]
}

run "vpc_has_two_public_and_two_private_subnets" {
  command = plan

  assert {
    condition     = length(aws_subnet.public) == 2 && length(aws_subnet.private) == 2
    error_message = "Expected 2 public and 2 private subnets"
  }
  assert {
    condition     = alltrue([for s in aws_subnet.public : s.map_public_ip_on_launch])
    error_message = "Public subnets must assign public IPs so nodes can join without NAT"
  }
  assert {
    condition     = aws_subnet.public[0].tags["kubernetes.io/role/elb"] == "1"
    error_message = "Public subnets need the ELB role tag for load balancers"
  }
}

run "eks_cluster_and_node_group" {
  command = plan

  assert {
    condition     = aws_eks_cluster.main.name == "pantrypulse-eks" && aws_eks_cluster.main.version == "1.35"
    error_message = "Unexpected cluster name or version"
  }
  assert {
    condition     = aws_eks_node_group.main.scaling_config[0].desired_size == 2
    error_message = "Node group should start with 2 nodes"
  }
  assert {
    condition     = length(aws_nat_gateway.main) == 0
    error_message = "Demo profile must not create a NAT gateway"
  }
}

run "nat_profile_moves_nodes_private" {
  command = plan

  variables {
    enable_nat_gateway = true
  }

  assert {
    condition     = length(aws_nat_gateway.main) == 1 && length(aws_route.private_nat) == 1
    error_message = "NAT profile should create one NAT gateway and a private default route"
  }
}

run "rejects_world_open_api" {
  command = plan

  variables {
    api_allowed_cidrs = ["0.0.0.0/0"]
  }

  expect_failures = [var.api_allowed_cidrs]
}
