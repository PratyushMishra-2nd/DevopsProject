#!/usr/bin/env bash
# Deploy a CI-built release to the free-tier k3s node created by
# terraform/ec2-k3s. Fetches the kubeconfig over SSH, then installs the same
# Helm chart and SHA-tagged GHCR images as every other environment.
#   scripts/deploy-ec2.sh [<full-git-sha>]      (default: origin/main)
set -euo pipefail
cd "$(dirname "$0")/.."

SHA="${1:-$(git rev-parse origin/main)}"
NS=pantrypulse
IP="$(terraform -chdir=terraform/ec2-k3s output -raw public_ip)"
export KUBECONFIG="${KUBECONFIG_EC2:-$HOME/.kube/pantrypulse-ec2.yaml}"
mkdir -p "$(dirname "$KUBECONFIG")"

echo "Waiting for k3s on $IP ..."
SSH=(ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 "ubuntu@$IP")
until "${SSH[@]}" test -f /var/lib/pantrypulse-k3s-ready 2>/dev/null; do sleep 10; done

# k3s writes the kubeconfig for 127.0.0.1; point it at the public IP, which
# the boot script added to the API server certificate (--tls-san).
"${SSH[@]}" sudo cat /etc/rancher/k3s/k3s.yaml | sed "s#https://127.0.0.1:6443#https://$IP:6443#" > "$KUBECONFIG"
chmod 600 "$KUBECONFIG"
kubectl get nodes -o wide

kubectl apply -f k8s/namespace.yaml
if ! kubectl -n "$NS" get secret pantrypulse-db >/dev/null 2>&1; then
  kubectl -n "$NS" create secret generic pantrypulse-db --from-literal=password="$(openssl rand -hex 16)"
fi

helm upgrade --install pantrypulse ./helm/pantrypulse -n "$NS" \
  -f helm/pantrypulse/values-ec2.yaml \
  --set database.existingSecret=pantrypulse-db \
  --set backend.image.tag="$SHA" --set frontend.image.tag="$SHA" \
  --wait --wait-for-jobs --timeout 10m

kubectl get pods,svc,ingress,hpa,pvc -n "$NS"
curl -fsS "http://$IP/api/info"; echo
echo "Open http://$IP/   (KUBECONFIG=$KUBECONFIG)"
