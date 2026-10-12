#!/usr/bin/env bash
# Deploy a CI-built release (images from GHCR, tagged with the commit SHA) to the
# local kind cluster with Helm. Without Argo CD this is the manual CD path.
#   scripts/deploy-local.sh [<full-git-sha>]      (default: origin/main)
set -euo pipefail
cd "$(dirname "$0")/.."

SHA="${1:-$(git rev-parse origin/main)}"
NS=pantrypulse
kubectl apply -f k8s/namespace.yaml

# Keep the database password stable across upgrades; generate it once.
if ! kubectl -n "$NS" get secret pantrypulse-db >/dev/null 2>&1; then
  kubectl -n "$NS" create secret generic pantrypulse-db --from-literal=password="$(openssl rand -hex 16)"
fi

helm upgrade --install pantrypulse ./helm/pantrypulse -n "$NS" \
  -f helm/pantrypulse/values-dev.yaml \
  --set database.existingSecret=pantrypulse-db \
  --set backend.image.tag="$SHA" --set frontend.image.tag="$SHA" \
  --wait --wait-for-jobs --timeout 8m

kubectl get pods,svc,ingress,hpa -n "$NS"
echo "Open http://pantrypulse.127.0.0.1.nip.io:8088"
