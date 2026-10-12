# Submission checklist

This is the instructor's checklist from `GRADING.md`, mapped to this
repository. Status values:

- **Done**: verified with the linked evidence.
- **PENDING EXTERNAL ACCESS**: needs an AWS account that was not available.
- **Owner action**: only the repository owner can do it.

Deadline: **Sunday 19 October 2026, 11:59 PM IST**.

## Application

| Item | Status | Evidence |
|------|--------|----------|
| GitHub repository URL submitted | **Owner action**: submit https://github.com/PratyushMishra-2nd/DevopsProject through the course form | — |
| Application runs via `docker compose up --build` | Done | [m4-docker-compose-up](evidence/screenshots/m4-docker-compose-up.png), [localhost:3000](evidence/screenshots/m4-app-at-localhost-3000.png) |
| At least 4 REST API endpoints | Done: 14 API routes (GET/POST/PUT/DELETE on lots, donors, dispatches) plus `/health`, `/ready`, `/metrics`, `/api/info` | [README API table](../README.md#application-and-api), [m1-api-crud-curl](evidence/screenshots/m1-api-crud-curl.png) |
| Alembic migration file present | Done: `backend/alembic/versions/0001_*`, `0002_*` | [m1-alembic-migrations](evidence/screenshots/m1-alembic-migrations.png) |

## Testing

| Item | Status | Evidence |
|------|--------|----------|
| pytest passes (screenshot) | Done: 33 passed | [m2-pytest-passing](evidence/screenshots/m2-pytest-passing.png) |
| At least 5 test cases | Done: 35 backend (33 + 2 Postgres), 15 frontend | `backend/tests/`, `frontend/src/**/*.test.js(x)` |
| Test DB / mock, not production | Done: in-memory SQLite via dependency override | `backend/tests/conftest.py` |
| `pytest.ini` / `conftest.py` | Done | `backend/pytest.ini`, `backend/tests/conftest.py` |

## Git

| Item | Status | Evidence |
|------|--------|----------|
| Public repository | Done | [m3-github-repo](evidence/screenshots/m3-github-repo.png) |
| Meaningful commit messages, ≥ 10 commits | Done | [m3-commit-history](evidence/screenshots/m3-commit-history.png), `git log` |
| `.gitignore` covers `.env`, `__pycache__`, `node_modules`, `.venv` | Done | [`.gitignore`](../.gitignore) |

## Docker

| Item | Status | Evidence |
|------|--------|----------|
| `backend/Dockerfile` builds | Done: also built in CI | [m4-docker-compose-up](evidence/screenshots/m4-docker-compose-up.png) |
| `frontend/Dockerfile` multi-stage (Node build + nginx runtime) | Done | `frontend/Dockerfile` |
| Non-root user in both images | Done: UID 10001 / UID 101 | [m4-containers-non-root](evidence/screenshots/m4-containers-non-root.png) |

## CI/CD

| Item | Status | Evidence |
|------|--------|----------|
| GitHub Actions workflow present | Done | `.github/workflows/ci-cd.yml` |
| Runs on push to `main` | Done | [m5-actions-runs](evidence/screenshots/m5-actions-runs.png) |
| pytest runs in the pipeline and fails the build on failure | Done | `backend` job |
| Frontend built in the pipeline | Done | `frontend` job (`vite build`) |
| Both images built | Done | `build-scan-push` |
| Images pushed to GHCR with SHA tags (not `latest`) | Done | [m5-ghcr-backend-package](evidence/screenshots/m5-ghcr-backend-package.png), [m5-ghcr-frontend-package](evidence/screenshots/m5-ghcr-frontend-package.png) |

## Security

| Item | Status | Evidence |
|------|--------|----------|
| Trivy scan on both images in the pipeline | Done | [m6-trivy-gate-ci-log](evidence/screenshots/m6-trivy-gate-ci-log.png) |
| Fails on HIGH/CRITICAL | Done: `--exit-code 1 --severity HIGH,CRITICAL`, run before the push | workflow |
| Can explain a CVE or a clean result | Done | [README → DevSecOps](../README.md#devsecops) |
| No secrets committed | Done: gitleaks over the full history in CI and locally ("no leaks found") | `secret-scan` job |

## Terraform

| Item | Status | Evidence |
|------|--------|----------|
| `terraform/` with valid HCL | Done | [m7-terraform-validate](evidence/screenshots/m7-terraform-validate.png) |
| `terraform init` | Done | [m7-terraform-init](evidence/screenshots/m7-terraform-init.png) |
| `terraform plan` output | Done: offline plan, 29 to add, no AWS calls | [m7-terraform-plan](evidence/screenshots/m7-terraform-plan.png) |
| VPC (≥ 2 public subnets) + EKS (node group) provisioned, AWS Console screenshot | **PENDING EXTERNAL ACCESS**: code complete, not applied (no valid AWS credentials) | [runbook](runbooks/aws-eks.md), [ADR 0007](adr/0007-local-kind-as-the-demo-cluster.md) |
| `terraform destroy` output | **PENDING EXTERNAL ACCESS** | [runbook § Destroy](runbooks/aws-eks.md#5-destroy-do-not-skip) |
| `terraform.tfvars.example`, no real credentials | Done | `terraform/terraform.tfvars.example` |

## Kubernetes and Helm

The cluster is local kind; EKS is pending (see above).

| Item | Status | Evidence |
|------|--------|----------|
| `k8s/namespace.yaml` applies | Done | [m8-kind-cluster-up](evidence/screenshots/m8-kind-cluster-up.png) |
| Helm chart: `Chart.yaml`, `values.yaml`, templates | Done | `helm/pantrypulse/` |
| `helm upgrade --install` succeeds | Done | [m8-helm-list-and-history](evidence/screenshots/m8-helm-list-and-history.png) |
| Backend and frontend ≥ 2 replicas | Done: HPA minimum 2 each | [m8-kubectl-get-pods-svc-ingress-hpa](evidence/screenshots/m8-kubectl-get-pods-svc-ingress-hpa.png) |
| ClusterIP Services | Done | same |
| Ingress `/` → frontend, `/api` → backend | Done | [m8-ingress-curl](evidence/screenshots/m8-ingress-curl.png), [m8-app-through-ingress](evidence/screenshots/m8-app-through-ingress.png) |
| All pods Running (screenshot) | Done | [m8-kubectl-get-pods-svc-ingress-hpa](evidence/screenshots/m8-kubectl-get-pods-svc-ingress-hpa.png) |
| `helm list` screenshot | Done | [m8-helm-list-and-history](evidence/screenshots/m8-helm-list-and-history.png) |

## Observability

| Item | Status | Evidence |
|------|--------|----------|
| `/metrics` screenshot | Done | [m9-backend-metrics-curl](evidence/screenshots/m9-backend-metrics-curl.png) |
| Prometheus Targets UP | Done | [m9-prometheus-targets-up](evidence/screenshots/m9-prometheus-targets-up.png) |
| Grafana dashboard with live panels | Done | [m9-grafana-dashboard](evidence/screenshots/m9-grafana-dashboard.png) |

## Documentation and demo

| Item | Status | Evidence |
|------|--------|----------|
| README with all technical sections | Done | [README](../README.md) |
| Presentation video in `demo/` (MANDATORY) | Done | [`demo/presentation.mp4`](../demo/presentation.mp4) |
| Slides PPT/PDF in `demo/` (MANDATORY) | Done | [`demo/presentation.pptx`](../demo/presentation.pptx), [`demo/presentation.pdf`](../demo/presentation.pdf) |

## Owner actions before the deadline

1. **Submit the form.** Submit the repository URL through the course form
   (https://forms.gle/XWAP1vAumDJgAPM1A). This was deliberately not
   submitted for you.
2. **AWS, optional.** If AWS access becomes available, follow
   [docs/runbooks/aws-eks.md](runbooks/aws-eks.md). It covers apply, the
   Console screenshots, deploy, and destroy. Add the screenshots to
   `docs/evidence/screenshots/` as `m7-aws-*.png`.
3. **Video narration.** `demo/presentation.mp4` is a recorded walkthrough
   with on-screen captions; it has no voice-over. Record your own narration
   over it if the course expects one (`demo/DEMO-SCRIPT.md` has the
   script).
