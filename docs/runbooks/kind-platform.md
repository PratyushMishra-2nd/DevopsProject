# Runbook: the full platform on a local kind cluster

Builds the whole platform from zero: Kubernetes with Traefik Ingress, an HPA
backed by metrics-server, Prometheus and Grafana, and Argo CD GitOps.
Tested on Windows 11 with Docker Desktop (about 8 GB of memory for Docker)
and Git Bash.

## Tools

| Tool | Version used |
|------|--------------|
| kind | 0.33 (node image v1.37.0) |
| kubectl | — |
| helm | v4.3 |
| argocd CLI | 3.5, optional |
| openssl, curl | — |

## 1. Cluster, Ingress controller, metrics-server

```bash
scripts/cluster-up.sh
```

- Creates the `pantrypulse` kind cluster from
  [`k8s/kind-config.yaml`](../../k8s/kind-config.yaml). The node's ports
  80/443 map to **127.0.0.1:8088/8443**.
- Installs Traefik ([ADR 0004](../adr/0004-traefik-ingress-controller.md))
  and metrics-server.
- Applies the `pantrypulse` namespace with Pod Security `restricted`.

## 2. Monitoring

```bash
scripts/install-monitoring.sh
```

Installs kube-prometheus-stack and the PantryPulse dashboard.

| UI | URL |
|----|-----|
| Grafana | http://grafana.127.0.0.1.nip.io:8088 |
| Prometheus | http://prometheus.127.0.0.1.nip.io:8088 |

The Grafana admin password is in Secret `monitoring/grafana-admin-bootstrap`.

## 3. Application

Pick one of the two options.

**a) GitOps (recommended).** Argo CD deploys whatever
`gitops/values-local.yaml` on `main` says:

```bash
scripts/install-argocd.sh
kubectl -n argocd get application pantrypulse -w     # wait for Synced / Healthy
```

- Argo CD UI: http://argocd.127.0.0.1.nip.io:8088
- User `admin`. Password:
  `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d`

**b) Plain Helm.** This installs a specific CI build:

```bash
scripts/deploy-local.sh <full-commit-sha>
```

Then open http://pantrypulse.127.0.0.1.nip.io:8088. `nip.io` resolves to
127.0.0.1, so no hosts-file edit is needed.

Demo data is not seeded in Kubernetes by default. To load it once:

```bash
kubectl -n pantrypulse exec deploy/pantrypulse-backend -- python -m app.seed
```

## 4. Verify

```bash
kubectl -n pantrypulse get pods,svc,ingress,hpa
helm list -n pantrypulse                                   # plain Helm installs only
curl -s http://pantrypulse.127.0.0.1.nip.io:8088/api/info  # shows git_sha
python scripts/ui_smoke.py http://pantrypulse.127.0.0.1.nip.io:8088
```

## 5. Exercise it

```bash
scripts/generate-traffic.sh                 # data for Grafana
scripts/hpa-load.sh <sha> 240               # watch: kubectl -n pantrypulse get hpa -w
scripts/troubleshoot.sh apply 1 <sha>       # failure labs, see troubleshooting/README.md
```

## Stop or remove

```bash
docker stop pantrypulse-control-plane        # pause; docker start ... resumes it
kind delete cluster --name pantrypulse       # remove everything
```

## Known issues on this setup

| Issue | Cause / fix |
|-------|-------------|
| Chromium hangs on `localhost` | Use `127.0.0.1` or the `*.127.0.0.1.nip.io` hosts |
| Image pulls fail with `lookup ... server misbehaving` | Docker Desktop's DNS resolver; retry. Recorded in [incident 1](../evidence/transcripts/incident-1-postgres-image-pull.txt) |
| After restarting the node container, the frontend pods crash-loop briefly | nginx starts before cluster DNS can resolve the backend Service; they recover on their own within a minute |
