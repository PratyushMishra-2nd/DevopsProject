#!/usr/bin/env bash
# Create the local kind cluster with Traefik (Ingress) and metrics-server (HPA).
#   scripts/cluster-up.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if ! kind get clusters | grep -qx pantrypulse; then
  kind create cluster --config k8s/kind-config.yaml --wait 120s
fi
kubectl config use-context kind-pantrypulse

helm repo add traefik https://traefik.github.io/charts >/dev/null
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null
helm repo update traefik metrics-server >/dev/null

helm upgrade --install traefik traefik/traefik --version 41.7.1 \
  -n traefik --create-namespace -f k8s/addons/traefik-kind-values.yaml --wait --timeout 5m

# kind kubelets use self-signed serving certs, hence --kubelet-insecure-tls (local only).
helm upgrade --install metrics-server metrics-server/metrics-server --version 3.14.0 \
  -n kube-system --set 'args={--kubelet-insecure-tls}' --wait --timeout 5m

kubectl apply -f k8s/namespace.yaml
kubectl get nodes -o wide
