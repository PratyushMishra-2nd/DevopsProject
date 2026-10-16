# Runbook: free-tier AWS deployment (EC2 + k3s)

> **Status: applied once on 2026-10-16 and destroyed.** The node came up
> (`Ready`, k3s v1.35.9+k3s1), but the Helm install timed out: the new
> t3.micro had a CPU credit balance of 0 (55-60 % steal) and 1 GiB of RAM,
> so the app pods never became ready.
> See [ADR 0008](../adr/0008-free-tier-ec2-k3s.md) for why this exists next to
> the [EKS runbook](aws-eks.md), and for the outcome.

## What Terraform creates

`terraform/ec2-k3s/` (plain `aws_*` resources, region `ap-south-1`):

- **Network:** VPC `10.43.0.0/16`, one public subnet in `ap-south-1a`, an
  internet gateway and a route table. The VPC's default security group is
  emptied.
- **Security group:** SSH (22) and the Kubernetes API (6443) from
  `admin_cidrs` only; HTTP (80) from `web_cidrs` (defaults to `admin_cidrs`);
  outbound TCP 80/443 only.
- **EC2:** one `t3.micro` (free-tier), Ubuntu 24.04, encrypted 30 GB gp3,
  IMDSv2 required, standard CPU credits. The boot script adds 2 GB of swap and
  installs **k3s v1.35.9+k3s1** (bundled Traefik, local-path storage,
  metrics-server).

## Cost

| Item | Free tier | Outside the free tier |
|------|-----------|-----------------------|
| t3.micro | 750 h/month | ~US$0.011/h |
| 30 GB gp3 | 30 GB-month | ~US$0.0024/h |
| Public IPv4 | 750 h/month (first 12 months) | US$0.005/h |
| VPC, subnet, IGW, SG | free | free |

No NAT gateway, load balancer or EKS control plane, so nothing here bills by
default on a free-tier account. Destroy it after the walkthrough anyway.

## 1. Apply

```bash
aws sts get-caller-identity                          # must succeed first
cd terraform/ec2-k3s
cp terraform.tfvars.example terraform.tfvars         # admin_cidrs = your IP/32, ssh_public_key = ~/.ssh/id_ed25519.pub
terraform init
terraform plan -out tfplan
terraform apply tfplan                               # ~1 min; k3s finishes ~2-3 min later
terraform output
```

## 2. Deploy the application

```bash
scripts/deploy-ec2.sh <full-git-sha>     # waits for k3s, fetches the kubeconfig over SSH, helm install
```

The script writes `~/.kube/pantrypulse-ec2.yaml`, installs the chart with
[`values-ec2.yaml`](../../helm/pantrypulse/values-ec2.yaml) (1 replica each,
trimmed requests, `local-path` PVC) and ends with `curl http://<ip>/api/info`.

## 3. Evidence to capture

```bash
export KUBECONFIG=~/.kube/pantrypulse-ec2.yaml
kubectl get nodes -o wide
kubectl get pods,svc,ingress,hpa,pvc -A
```

- AWS Console, `ap-south-1`: VPC `pantrypulse-k3s-vpc` with its subnet, EC2
  instance `pantrypulse-k3s-node` (Running, t3.micro), its security group.
- Browser on `http://<public-ip>/`.

## 4. Destroy (do not skip)

```bash
helm uninstall pantrypulse -n pantrypulse --kubeconfig ~/.kube/pantrypulse-ec2.yaml   # optional: the disk goes with the instance
cd terraform/ec2-k3s && terraform destroy
aws ec2 describe-instances --region ap-south-1 --filters Name=tag:Project,Values=pantrypulse \
  --query "Reservations[].Instances[].State.Name"                  # expect [] or "terminated"
aws ec2 describe-vpcs --region ap-south-1 --filters Name=tag:Project,Values=pantrypulse
```

Unlike EKS, nothing is created outside Terraform's state (ServiceLB uses the
node's own port 80, not an AWS load balancer), so `terraform destroy` removes
everything.
