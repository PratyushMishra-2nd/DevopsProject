# Evidence manifest

Every artifact in `docs/evidence/` comes from a real run on 12–13 October
2026. Nothing was edited by hand or mocked up.

## How each kind of evidence was produced

| Kind | How | Location |
|------|-----|----------|
| **Transcripts** | [`scripts/record.sh`](../../scripts/record.sh) runs the command with `bash -c`, then appends a timestamp, a `pratyush-mishra@pantrypulse:~/DevopsProject$ <command>` line and the untouched stdout/stderr (ANSI colours stripped). The workstation is Windows 11 with Git Bash; the prompt string is a fixed label, not the machine's hostname | [`transcripts/`](transcripts/) |
| **Terminal screenshots** | Transcripts rendered to PNG by a Playwright script. Long outputs are cut with an explicit `... N lines omitted ...` marker. Filtered renders say so in their caption, and each image names its source transcript | `screenshots/m*-*.png` (dark terminal style) |
| **Browser screenshots** | Headless Chromium (Playwright 1.63) on the live system. The address bar above each image is drawn from the exact URL that was loaded | `screenshots/m*-*.png` (with URL bar) |
| **GitHub pages** | Public repository pages captured logged-out with the same tooling | `screenshots/m3-*`, `m5-*`, `m6-ci-build-scan-push-job.png` |

Two notes on hosts and ports:

- **Ports.** When some runs were recorded, other projects' containers held
  host ports 3000/8000, so those Compose runs used 3300/8800. The final
  Compose run and the `localhost:3000` screenshot use the default ports.
- **kind.** The kind cluster exposes its Ingress on host port **8088**,
  because Docker Desktop owns port 80 on this workstation.

## By rubric module

### M1 Application

| Evidence | Shows |
|----------|-------|
| `screenshots/m4-app-at-localhost-3000.png`, `m1-app-expiry-radar.png`, `m1-app-donors.png`, `m1-app-dispatch-log.png`, `m1-app-receive-stock-form.png`, `m1-app-mobile.png` | The UI rendering live API data via Compose (desktop and mobile widths) |
| `screenshots/m1-ui-crud-1..5-*.png` | Browser CRUD journey: create, dispatch, update, void, delete (`scripts/ui_smoke.py`, Compose on :3300) |
| `screenshots/m1-api-crud-curl.png` ← `transcripts/api-crud.txt` | GET/POST/PUT/DELETE through curl, including the 409/422 business rules |
| `screenshots/m1-alembic-migrations.png` ← `transcripts/alembic-migrations.txt` | Alembic `0001` → `0002` on PostgreSQL |
| `transcripts/api-health.txt` | `/health` and `/ready` |

### M2 Testing

| Evidence | Shows |
|----------|-------|
| `screenshots/m2-pytest-passing.png` ← `transcripts/backend-pytest.txt` | `pytest -v`: 33 passed, 2 skipped (the Postgres tests need `TEST_POSTGRES_URL`; they run in CI), 89% coverage |
| `screenshots/m2-frontend-vitest.png` ← `transcripts/frontend-tests.txt` | vitest: 15 passed |

### M3 Git and GitHub

| Evidence | Shows |
|----------|-------|
| `screenshots/m3-github-repo.png` | Public repository |
| `screenshots/m3-commit-history.png` | Commit history with descriptive messages |

### M4 Docker

| Evidence | Shows |
|----------|-------|
| `screenshots/m4-docker-compose-up.png` ← `transcripts/docker-compose-up-default-ports.txt` | `docker compose up --build`: 3 services healthy on 3000/8000 |
| `transcripts/docker-compose-up.txt`, `docker-compose-ps.txt` | First full build (ports 3300/8800) |
| `screenshots/m4-containers-non-root.png` ← `transcripts/docker-nonroot-users.txt` | Backend UID 10001, frontend UID 101 |
| `screenshots/m4-volume-persistence.png` ← `transcripts/docker-persistence.txt` | Data survives `down` and `up` |

### M5 CI/CD

| Evidence | Shows |
|----------|-------|
| `screenshots/m5-ci-run-all-jobs-green.png` | Run 38298132560: all 6 jobs green |
| `screenshots/m5-actions-runs.png` | Workflow history |
| `screenshots/m5-ghcr-packages.png`, `m5-ghcr-backend-package.png`, `m5-ghcr-frontend-package.png` | GHCR images tagged with full commit SHAs |

### M6 DevSecOps

| Evidence | Shows |
|----------|-------|
| `screenshots/m6-trivy-gate-ci-log.png` ← `transcripts/ci-trivy-gate.txt` | Trivy gate step output from CI run 38298132560 (fetched with `gh run view --log`): 0 HIGH/CRITICAL in both images, then the push |
| `screenshots/m6-ci-build-scan-push-job.png` | The job page on GitHub |

### M7 Terraform

| Evidence | Shows |
|----------|-------|
| `screenshots/m7-terraform-init.png`, `m7-terraform-validate.png`, `m7-terraform-test.png` | init / fmt + validate / `terraform test` (4 passed) |
| `screenshots/m7-terraform-plan.png` ← `transcripts/terraform-plan-offline.txt` | `Plan: 29 to add`, generated **without** AWS access (`offline_plan=true` and dummy credentials; nothing calls AWS) |
| **Not available** | AWS Console screenshots, `terraform apply`, `terraform destroy`: **PENDING EXTERNAL ACCESS** (see [ADR 0007](../adr/0007-local-kind-as-the-demo-cluster.md)) |

### M8 Kubernetes, Helm, GitOps

| Evidence | Shows |
|----------|-------|
| `screenshots/m8-kind-cluster-up.png` | kind cluster, Traefik, metrics-server |
| `screenshots/m8-kubectl-get-pods-svc-ingress-hpa.png` ← `transcripts/k8s-resources.txt` | All pods Running, ClusterIP Services, Ingress, HPA, PDB, NetworkPolicy, PVC, ServiceMonitor; pod UIDs |
| `screenshots/m8-helm-list-and-history.png` ← `transcripts/helm-upgrade-recovered.txt` | `helm upgrade --install` (revision 2, deployed) and `helm list` |
| `transcripts/helm-install.txt` | The first install, which timed out (see incident 1) |
| `screenshots/m8-ingress-curl.png`, `m8-app-through-ingress*.png`, `m8-ingress-ui-crud-*.png` | App reached through the Traefik Ingress; full browser CRUD journey through the Ingress |
| `screenshots/m8-hpa-autoscaling.png` ← `transcripts/hpa-autoscaling.txt` | HPA 2 → 3 → 5 at 357% CPU, back to 2 after the load |
| `screenshots/m8-argocd-app-tree.png`, `m8-argocd-app-list.png`, `m8-argocd-applications.png`, `m8-argocd-app-synced.png` | Argo CD application Synced/Healthy |
| `screenshots/m8-gitops-promotion.png`, `m8-gitops-rollback.png` | Promotion by commit and rollback by `git revert`, with Argo CD converging each time |
| `screenshots/m8-lab1..4-*.png`, `m8-lab3-4-fix.png` | Troubleshooting labs: broken, diagnosed, fixed |
| `screenshots/m8-incident1-dockerhub-dns.png`, `m8-incident2-traefik-hostport.png` | Real incidents during the build |

### M9 Observability

| Evidence | Shows |
|----------|-------|
| `screenshots/m9-backend-metrics-curl.png` ← `transcripts/backend-metrics.txt` | `/metrics` in Prometheus format, including the business counters |
| `screenshots/m9-prometheus-targets-up.png` | ServiceMonitor `pantrypulse-backend`: 5/5 UP (captured during the HPA scale-out) |
| `screenshots/m9-prometheus-query.png` | PromQL request rate by handler and status |
| `screenshots/m9-grafana-dashboard.png`, `m9-grafana-dashboards-list.png` | Provisioned "PantryPulse - API overview" dashboard with live data |
| `screenshots/m9-incident3-grafana-gc-thrash.png` | Grafana outage diagnosed and fixed |

### M10 Presentation and documentation

| Evidence | Shows |
|----------|-------|
| [`../../demo/`](../../demo/) | `presentation.mp4` (12 min, 1280×720, narrated slides, then a live walkthrough), `presentation.pptx`, `presentation.pdf`, `preview.gif`, `DEMO-SCRIPT.md` (narration plus how each segment was recorded) |
| Video, CI/CD segment | A live push of `78f8ecf` and GitHub Actions run [38302122963](https://github.com/PratyushMishra-2nd/DevopsProject/actions/runs/38302122963) through to success (the wait is sped up and captioned as such) |
| Video, Argo CD segment | A live GitOps promotion of that build (commit `23fdafe`); Argo CD syncs and `/api/info` reports `78f8ecf` |
| [`../../README.md`](../../README.md), [`../adr/`](../adr/), [`../engineering/`](../engineering/), [`../runbooks/`](../runbooks/) | Documentation |

## Full transcript index

| Transcript | Content |
|------------|---------|
| `alembic-migrations` | migrations on PostgreSQL |
| `api-crud` | curl CRUD |
| `api-health` | health and readiness |
| `argocd-synced` | `argocd app get` |
| `backend-metrics` | `/metrics` |
| `backend-pytest` | pytest |
| `ci-trivy-gate` | Trivy step from CI |
| `docker-*` | Compose up/ps/non-root/persistence |
| `frontend-tests` | vitest |
| `generate-traffic` | load generator |
| `gitops-promotion`, `gitops-rollback` | GitOps drill |
| `helm-install`, `helm-upgrade-recovered` | Helm |
| `hpa-autoscaling` | HPA |
| `incident-1..3` | real incidents |
| `ingress-smoke` | curl through the Ingress |
| `install-argocd`, `install-monitoring` | installs |
| `k8s-resources` | cluster state |
| `kind-cluster-up` | cluster |
| `lab-*` | troubleshooting labs |
| `seed-demo-k8s` | demo data in the cluster |
| `terraform-*` | init, validate, test, plan |
| `traefik-ingress-status` | Traefik upgrade (the first attempt failed, see incident 2) |
| `traffic-cleanup` | removal of the synthetic load-test lots before the screenshots |
| `ui-smoke-ingress` | Playwright CRUD journey through the Ingress |
