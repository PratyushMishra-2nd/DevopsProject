# Runbook: provision, deploy and destroy on AWS EKS

> **Status: PENDING EXTERNAL ACCESS.** This runbook has **not** been run
> against AWS for this submission: no valid AWS credentials were available
> (`aws sts get-caller-identity` → `InvalidClientTokenId`). Everything
> below is verified only up to `terraform plan` without an account. See
> [ADR 0007](../adr/0007-local-kind-as-the-demo-cluster.md).

## What Terraform creates

`terraform/` uses plain `aws_*` resources, not community modules, so every
object is visible in review. Region `ap-south-1`.

- **Network:**
  - VPC `10.42.0.0/16`, with public and private subnets in
    `ap-south-1a/b`.
  - Internet gateway and route tables.
  - Optional NAT gateway (`enable_nat_gateway`).
- **IAM:** a cluster role, a node role, and a role for the EBS CSI driver
  (via EKS Pod Identity).
- **EKS:**
  - EKS 1.35 with API access limited to `api_allowed_cidrs`.
  - Managed node group: `t3.medium` × 2 (min 1, max 3), 20 GB disks.
  - Add-ons: vpc-cni, kube-proxy, coredns, eks-pod-identity-agent,
    metrics-server (for the HPA), aws-ebs-csi-driver.

Plan size: **29 resources to add**
([offline plan transcript](../evidence/transcripts/terraform-plan-offline.txt)).

## Cost

| Item | Rate |
|------|------|
| Control plane | ~US$0.10/h |
| 2 × t3.medium in ap-south-1 | ~US$0.09/h |
| NLB | ~US$0.0225/h |
| Total, as configured | **≈ US$0.22/h** |
| Total with `enable_nat_gateway=true` | add ~US$0.056/h |

Destroy the stack as soon as the evidence is captured.

## 1. Plan and apply

```bash
aws sts get-caller-identity                    # must succeed first
cd terraform
cp terraform.tfvars.example terraform.tfvars   # set api_allowed_cidrs to your IP/32
terraform init
terraform plan -out tfplan
terraform apply tfplan                         # ~15 min
$(terraform output -raw configure_kubectl)     # aws eks update-kubeconfig ...
kubectl get nodes
```

## 2. Platform add-ons

```bash
kubectl apply -f k8s/storageclass-gp3.yaml
helm upgrade --install traefik traefik/traefik --version 41.7.1 -n traefik --create-namespace \
  -f k8s/addons/traefik-eks-values.yaml --wait
scripts/install-monitoring.sh          # Grafana/Prometheus Ingress hosts in the values are for kind; use port-forward on EKS
kubectl apply -f k8s/namespace.yaml
```

## 3. Application

```bash
kubectl -n pantrypulse create secret generic pantrypulse-db --from-literal=password="$(openssl rand -hex 16)"
helm upgrade --install pantrypulse ./helm/pantrypulse -n pantrypulse \
  -f helm/pantrypulse/values-eks.yaml \
  --set database.existingSecret=pantrypulse-db \
  --set backend.image.tag=<sha> --set frontend.image.tag=<sha> \
  --wait --wait-for-jobs --timeout 10m
kubectl -n traefik get svc traefik     # EXTERNAL-IP = NLB DNS name
curl http://<nlb-dns-name>/api/info
```

## 4. Evidence to capture

- AWS Console, `ap-south-1`:
  - VPC `pantrypulse-vpc` with its subnets
  - EKS cluster `pantrypulse-eks`, status Active, with its node group
  - EC2 instances
- `kubectl get nodes,pods -A`
- The browser on the NLB address.

## 5. Destroy (do not skip)

```bash
helm uninstall pantrypulse -n pantrypulse
helm uninstall traefik -n traefik        # deletes the NLB; otherwise the VPC cannot be deleted
helm uninstall monitoring -n monitoring
kubectl delete pvc --all -n pantrypulse  # releases the EBS volumes
cd terraform && terraform destroy
aws eks list-clusters --region ap-south-1          # expect []
aws ec2 describe-vpcs --region ap-south-1 --filters Name=tag:Project,Values=pantrypulse
```

Uninstall Traefik first. A LoadBalancer Service creates an NLB and ENIs
that Terraform does not own. Left in place, they block deletion of the
subnets and the VPC.
