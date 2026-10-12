#!/usr/bin/env bash
# Install Argo CD and register the PantryPulse Application (GitOps).
#   scripts/install-argocd.sh
# The database Secret is created here, outside Git, and referenced by
# gitops/values-local.yaml through database.existingSecret.
set -euo pipefail
cd "$(dirname "$0")/.."

helm repo add argo https://argoproj.github.io/argo-helm >/dev/null
helm repo update argo >/dev/null
helm upgrade --install argocd argo/argo-cd --version 10.10.3 -n argocd --create-namespace \
  -f gitops/argocd-values.yaml --wait --timeout 10m

kubectl apply -f k8s/namespace.yaml
if ! kubectl -n pantrypulse get secret pantrypulse-db >/dev/null 2>&1; then
  kubectl -n pantrypulse create secret generic pantrypulse-db --from-literal=password="$(openssl rand -hex 16)"
fi

kubectl apply -f gitops/application.yaml
echo "Argo CD UI: http://argocd.127.0.0.1.nip.io:8088  (user admin)"
echo "Initial admin password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
