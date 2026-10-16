# ADR 0008: Free-tier AWS deployment on EC2 + k3s alongside the EKS stack

- Status: accepted
- Date: 2026-10-16

## Context

AWS credentials became available after [ADR 0007](0007-local-kind-as-the-demo-cluster.md).
Two facts then shaped the AWS deployment:

- **Cost.** The EKS stack costs about US$0.22/h; the EKS control plane is
  never covered by the AWS free tier.
- **Account guardrails.** The IAM user is bound by a policy
  (`PratyushMishraGuardrails`) that, by `ec2:RunInstances` dry runs on
  2026-10-16, allows only `t3.micro` and `t2.micro`. `t3.medium` (the EKS
  node group type), `t3.small`, `m7i-flex.large`, `c7i-flex.large` and the
  Graviton types are explicitly denied, so the EKS node group could not
  launch on this account as written.

## Decision

Add a second, independent Terraform stack, `terraform/ec2-k3s/`:

- one free-tier `t3.micro` in a dedicated VPC (`10.43.0.0/16`) running a
  pinned **k3s** release (Kubernetes 1.35, the same minor as the EKS stack);
- 2 GB of swap and `values-ec2.yaml` (1 replica each, trimmed requests) so
  k3s and the app fit in 1 GiB;
- the **same Helm chart and the same CI-built, SHA-tagged GHCR images** as
  kind and EKS, deployed by `scripts/deploy-ec2.sh`.

The EKS stack stays in `terraform/` as the production-shaped design.

## Consequences

- A real AWS deployment (VPC, subnet, security group, EC2, Kubernetes, the
  app on a public IP) at ~US$0/h on a free-tier account.
- Single node: no high availability, HPA tops out at 2 replicas, no
  Prometheus stack. Monitoring stays demonstrated on kind.
- k3s, not EKS: the cluster is self-managed. The EKS code is still verified by
  `terraform validate`, `terraform test`, Trivy and a real `terraform plan`.
- The same CI gates run on both stacks (`terraform fmt`, `validate`,
  `test`, Trivy IaC). Accepted Trivy finding AWS-0104 (outbound TCP 80/443
  to any address) is documented in `security/trivy-iac-accepted.yaml`.

## Outcome (2026-10-16)

- The stack was applied (15 resources) and k3s reached `Ready`, but
  `scripts/deploy-ec2.sh` timed out after 10 minutes: CloudWatch showed a
  `CPUCreditBalance` of 0 and the node ran at 55-60 % CPU steal with 500+ MB
  in swap. Running the app would have required unlimited CPU credits (paid),
  so the stack was destroyed instead.
- The account also has **no EKS permissions at all**
  (`eks:ListClusters` → `AccessDeniedException`), so the EKS stack cannot be
  applied from it regardless of instance type.
- What *was* proven on AWS: the network part of `terraform/` (VPC with 2
  public and 2 private subnets) was applied with `-target` and destroyed;
  see `docs/evidence/transcripts/aws-vpc-*.txt`.
