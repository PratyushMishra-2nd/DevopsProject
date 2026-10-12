# ADR 0007: kind is the demonstrated cluster; EKS is delivered as code

- Status: accepted
- Date: 2026-10-13

## Context

The brief asks for an EKS cluster provisioned by Terraform. When this
submission was built:

- The AWS credentials on the workstation were invalid:
  `sts get-caller-identity` returned `InvalidClientTokenId`.
- No replacement account access was available.

Fabricating AWS console evidence is not an option.

## Decision

- Ship the full Terraform for VPC, EKS, the node group, IAM, the add-ons and
  EBS CSI, and verify everything that can be verified without an account:
  - `terraform fmt`
  - `terraform validate`
  - `terraform test` (4 plan-time assertions)
  - Trivy IaC scan
  - an offline `terraform plan` (29 resources to add)
- Run the complete platform on a local **kind** cluster:
  - Traefik Ingress
  - HPA with metrics-server
  - kube-prometheus-stack
  - Argo CD
- The same Helm chart is used everywhere: CI, local kind and (later) EKS.
  - `values-dev.yaml` is the kind profile.
  - `values-eks.yaml` is the EKS profile: gp3 storage and NLB-fronted
    Traefik.
- Mark AWS provisioning, the console screenshots and `terraform destroy` as
  **PENDING EXTERNAL ACCESS** in the checklist, and document the exact
  apply/verify/destroy steps in [the EKS runbook](../runbooks/aws-eks.md).

## Consequences

- Every claim in the evidence is reproducible on a laptop.
- The rubric items that need a live AWS account (console screenshots, a real
  `terraform apply`/`destroy`) are not met until the runbook is executed
  with valid credentials.
