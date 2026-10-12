# Security controls

Security is enforced by gates in the pipeline and by defaults in the
platform. It does not depend on a checklist someone has to remember. Each
control below names where it lives and how it is verified.

## Supply chain and pipeline

| Control | Where | Verified by |
|---------|-------|-------------|
| Secret scanning of **every commit** in history | `secret-scan` job (gitleaks 8.30.1, checksum-verified download) | CI; local `gitleaks git .` → "no leaks found" |
| SAST on the API | `bandit -ll -ii` in the `backend` job | CI |
| Dependency CVEs | `pip-audit` (backend), `npm audit --omit=dev --audit-level=high` (frontend) | CI |
| IaC misconfiguration | `trivy config` on Terraform and on the rendered Helm chart; MEDIUM/HIGH/CRITICAL fail unless listed in [`security/trivy-iac-accepted.yaml`](../../security/trivy-iac-accepted.yaml) with a reason | CI `iac` job |
| Image vulnerabilities **gate** | `trivy image --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed --scanners vuln,secret` runs **before** the images are pushed | CI; [screenshot](../evidence/screenshots/m6-trivy-gate-ci-log.png): 0 findings for both images |
| Full vulnerability report | Trivy JSON, all severities, uploaded as the `trivy-reports` artifact (informational) | CI artifacts |
| SBOM | SPDX per image (`anchore/sbom-action`) | CI artifacts |
| Provenance | `actions/attest-build-provenance`; the deploy job runs `gh attestation verify --signer-workflow` before installing | CI `deploy-kind` job |
| Immutable releases | images tagged only with the commit SHA; no `latest` ([ADR 0002](../adr/0002-immutable-sha-image-tags.md)) | Helm `required` on the tag |
| Least-privilege tokens | workflow default `contents: read`; only `build-scan-push` gets `packages: write`, `id-token: write`, `attestations: write` | workflow file |
| Pinned actions | every third-party action is pinned to a full commit SHA; Dependabot (`github-actions`) proposes updates | workflow file, `.github/dependabot.yml` |
| Dependency updates | Dependabot for pip, npm, GitHub Actions, Docker base images and Terraform providers | open Dependabot PRs |

## Containers

- Both images run as non-root:
  - backend as UID 10001
  - frontend as `nginx-unprivileged`, UID 101 on port 8080.
  - Evidence: [non-root transcript](../evidence/transcripts/docker-nonroot-users.txt)
- Both use minimal, pinned bases:
  - backend: `python:3.12-slim-trixie`, two-stage build, no compilers in
    the runtime image
  - frontend: `nginx-unprivileged:1.30-alpine3.24`
- nginx hardening:
  - `server_tokens off`
  - a strict CSP (`default-src 'self'`, no inline script or style, and
    Vite's `assetsInlineLimit: 0` keeps it that way)
  - `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`
- The API is reachable from the browser only through the same-origin `/api`
  proxy.

## Kubernetes

- **Namespace:** the `pantrypulse` namespace enforces Pod Security
  Admission **restricted**.
- **Pod defaults:** every pod gets:
  - `runAsNonRoot`
  - `seccompProfile: RuntimeDefault`
  - `allowPrivilegeEscalation: false`
  - all capabilities dropped
  - `readOnlyRootFilesystem: true`, with `emptyDir` for the paths that must
    be writable
  - `automountServiceAccountToken: false`
- **NetworkPolicy:** only the API pods and the migration Job can reach
  PostgreSQL on 5432.
- **Resources and disruption:** resource requests and limits on every
  container; PodDisruptionBudgets for the API and UI.
- **Secrets:** the database password is never in Git or in values files.
  - Under Argo CD it is a pre-created Secret (`database.existingSecret`).
  - For ad-hoc Helm installs it must be supplied with `--set-string`; the
    chart refuses to render without one.
  - The Grafana admin password is generated once into a Secret by
    `scripts/install-monitoring.sh`.

## Infrastructure (AWS, code only)

The low-cost demo profile is a set of deliberate trade-offs, recorded in
[ADR 0003](../adr/0003-eks-without-nat.md) and in the Trivy accept-list:

- The public EKS API endpoint is restricted to `api_allowed_cidrs`;
  `0.0.0.0/0` is rejected by validation.
- No NAT gateway by default.
- Optional KMS envelope encryption of Secrets.
- Optional control-plane logs.

Each trade-off is undone by setting one variable.

## What is not covered

- No runtime threat detection (e.g. Falco) and no admission policy engine
  (Kyverno/Gatekeeper) beyond Pod Security Admission.
- TLS ends at Traefik only on EKS, with a certificate to be added. The local
  kind cluster serves plain HTTP on `127.0.0.1` only.
- Trivy runs with `--ignore-unfixed`, so unfixed CVEs are reported but do not
  block a release.
