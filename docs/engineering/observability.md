# Observability

## Signals the application emits

| Signal | Endpoint / source | Notes |
|--------|-------------------|-------|
| Liveness | `GET /health` → `{"status":"UP"}` | process is alive; no dependency checks |
| Readiness | `GET /ready` → `{"status":"READY"}` or `503 {"status":"NOT_READY","reason":...}` | checks DB connectivity **and** that Alembic migrations ran |
| Metrics | `GET /metrics` (Prometheus text format) | `http_requests_total{handler,method,status}`, `http_request_duration_seconds` histogram, process/GC metrics, plus the business counters `pantrypulse_lots_created_total` and `pantrypulse_dispatched_quantity_total{category,unit}` |
| Version | `GET /api/info` → `git_sha` | shows which build is serving; the UI header shows it too |
| Logs | stdout, one JSON object per line | collected by the container runtime (`kubectl logs`) |

## Monitoring stack (local kind cluster)

- **Stack:** `kube-prometheus-stack` 92.3.0, installed by
  [`scripts/install-monitoring.sh`](../../scripts/install-monitoring.sh)
  with [`monitoring/kube-prometheus-stack-values.yaml`](../../monitoring/kube-prometheus-stack-values.yaml).
- **Scraping:** the chart's `ServiceMonitor` (`serviceMonitor.enabled: true`
  in `values-dev.yaml`) makes Prometheus scrape every API pod. Pods that
  the HPA adds are discovered automatically: during the load test the
  target count went from 2 to 5, all `UP`
  ([screenshot](../evidence/screenshots/m9-prometheus-targets-up.png)).
- **Dashboard:** "PantryPulse - API overview"
  ([`monitoring/dashboards/pantrypulse-overview.json`](../../monitoring/dashboards/pantrypulse-overview.json))
  is provisioned through the Grafana sidecar, from a ConfigMap labelled
  `grafana_dashboard=1`. Panels:
  - requests/s
  - p95 latency
  - 5xx ratio
  - backend targets UP
  - request rate by endpoint
  - responses by status
  - latency percentiles
  - p95 by endpoint
  - HPA replicas and pod CPU
  - food dispatched (business metric)
  - [Screenshot](../evidence/screenshots/m9-grafana-dashboard.png)

| UI | URL |
|----|-----|
| Grafana | `http://grafana.127.0.0.1.nip.io:8088` (user `admin`, password in Secret `monitoring/grafana-admin-bootstrap`) |
| Prometheus | `http://prometheus.127.0.0.1.nip.io:8088` |

## Generating data

```bash
scripts/generate-traffic.sh http://pantrypulse.127.0.0.1.nip.io:8088 300   # mixed reads/writes, 404s, 422s
scripts/hpa-load.sh <sha> 240                                             # CPU load to trigger the HPA
```

## Autoscaling

Both the backend and the frontend have an HPA on CPU:

| Component | Target CPU | Replicas |
|-----------|------------|----------|
| backend | 70% | 2–5 |
| frontend | 75% | 2–4 |

metrics-server supplies the CPU metrics. In the recorded run
([transcript](../evidence/transcripts/hpa-autoscaling.txt)), the backend
went 2 → 3 → 5 replicas at 357% of its CPU request, and back to 2 about
5 minutes after the load stopped (the default scale-down stabilisation
window).

## Incident found through monitoring

Grafana itself became unavailable:

- symptoms: 503 on `/api/health`, more than 20 CPU cores used, liveness
  restarts
- cause: its memory limit (384Mi) produced `GOMEMLIMIT=345MiB` against
  ~344Mi of usage, so the Go GC ran continuously
- fix: a 768Mi limit plus a CPU cap of 1 core
- [transcript](../evidence/transcripts/incident-3-grafana-gc-thrash.txt)
