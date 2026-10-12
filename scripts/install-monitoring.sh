#!/usr/bin/env bash
# Install Prometheus + Grafana (kube-prometheus-stack) and the PantryPulse dashboard.
#   scripts/install-monitoring.sh
# The Grafana admin password is generated once and kept in a Secret, not in Git.
set -euo pipefail
cd "$(dirname "$0")/.."

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo update prometheus-community >/dev/null
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

if ! kubectl -n monitoring get secret grafana-admin-bootstrap >/dev/null 2>&1; then
  kubectl -n monitoring create secret generic grafana-admin-bootstrap \
    --from-literal=password="$(openssl rand -hex 12)"
fi
GRAFANA_PASSWORD=$(kubectl -n monitoring get secret grafana-admin-bootstrap -o jsonpath='{.data.password}' | base64 -d)

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack --version 92.3.0 \
  -n monitoring -f monitoring/kube-prometheus-stack-values.yaml \
  --set-string grafana.adminPassword="$GRAFANA_PASSWORD" --wait --timeout 10m

kubectl -n monitoring create configmap pantrypulse-dashboard \
  --from-file=monitoring/dashboards/pantrypulse-overview.json \
  --dry-run=client -o yaml | kubectl label --local -f - grafana_dashboard=1 -o yaml | kubectl apply -f -

echo "Grafana:    http://grafana.127.0.0.1.nip.io:8088   (user admin, password in secret monitoring/grafana-admin-bootstrap)"
echo "Prometheus: http://prometheus.127.0.0.1.nip.io:8088/targets"
