# ADR 0003: Low-cost EKS profile — no NAT gateway by default

- Status: accepted
- Date: 2026-10-12

## Context

The AWS target is a short-lived demo cluster in `ap-south-1`: up for about
an hour, then destroyed. Production-grade defaults cost money every hour
whether or not anyone uses them:

| Item | Approx. cost |
|------|--------------|
| NAT gateway | ~US$0.056/h + data processing (~US$41/month) |
| KMS key for Secrets envelope encryption | US$1/month |
| Control-plane logs | CloudWatch ingestion |

The EKS control plane (~US$0.10/h) and two `t3.medium` nodes are
unavoidable.

## Decision

`terraform/` creates the following:

- A VPC `10.42.0.0/16` with two public and two private subnets across
  `ap-south-1a/b`.
- EKS 1.35 with a managed node group (`t3.medium`: desired 2, min 1, max 3).
- The core add-ons, and the EBS CSI driver using EKS Pod Identity.

The cost items above sit behind feature flags, all defaulting to `false`:

- `enable_nat_gateway`
  - Off: the nodes run in public subnets with public IPs, so they can pull
    images.
  - On: the nodes move to private subnets behind one NAT gateway.
- `enable_secrets_encryption`: customer-managed KMS key.
- `enable_control_plane_logs`: CloudWatch logs.

The public EKS API endpoint is limited to `api_allowed_cidrs`. A validation
rule rejects `0.0.0.0/0`.

The Trivy findings these trade-offs cause are listed one by one, with a
reason for each, in
[`security/trivy-iac-accepted.yaml`](../../security/trivy-iac-accepted.yaml).
Any other MEDIUM, HIGH or CRITICAL finding fails CI.

## Consequences

- The demo is cheap enough to run, and each saving can be turned off with a
  single variable.
- Nodes with public IPs are a weaker posture. Node security groups only
  allow EKS-managed traffic, but production should set
  `enable_nat_gateway=true`.
- **Status:** `terraform validate`, `terraform test` (4 plan-time tests) and
  an offline `terraform plan` (29 resources) are verified. Apply and destroy
  against a real AWS account have **not** been run: no AWS credentials were
  available for this submission. See
  [the EKS runbook](../runbooks/aws-eks.md).
