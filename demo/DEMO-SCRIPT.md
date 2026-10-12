# Demo script

Script for [`presentation.mp4`](presentation.mp4). The video follows the order the brief asks for:

1. Slides: what was built and the architecture.
2. A live walkthrough of:
   1. codebase
   2. CI/CD
   3. Terraform
   4. Argo CD
   5. Kubernetes
   6. Prometheus
   7. Grafana

How the video was made:

- **Narration:** the built-in Windows text-to-speech voice reads the lines below. Re-record with your own voice from this script if you prefer.
- **Recording:** the walkthrough was captured with headless Chromium (Playwright) against the running system.
- **Terminal panels:** these are a browser page streaming the output of commands executed live in the repository, at the moment of recording.
- **Speed-ups:** the long CI wait and the Argo CD sync wait are sped up, and the on-screen caption says so.
- **CI/CD segment:** recorded live on 13 Oct 2026: the push of commit `78f8ecf` and GitHub Actions run 38302122963 (success). The completed-run view and the GHCR page that follow the sped-up wait were captured right after the run finished.
- **Argo CD segment:** the promotion commit `23fdafe` was made and pushed live. The final Synced/Healthy view was recorded about a minute later. During the rollout the app showed *Degraded* for a few seconds, because the HPA had no CPU metrics yet for the new pods; the caption says so.

## Part 1 - Slides (`presentation.pptx` / `presentation.pdf`)

### Slide 1: PantryPulse

PantryPulse is a stock and expiry tracker for community food banks. This talk covers the application and the DevSecOps platform around it: tests, containers, a gated CI/CD pipeline, Terraform for AWS, Kubernetes with Helm, GitOps with Argo CD, and monitoring with Prometheus and Grafana.

### Slide 2: What PantryPulse does

Food banks receive donations with very different shelf lives. PantryPulse shows what is on the shelf, what expires soon, who donated it and where it went. The API enforces the rules that matter: no dispatching expired or held stock, never more than what is left, and no deleting a lot that has dispatch history.

### Slide 3: Three tiers, one chart, many gates

The browser reaches Traefik. Slash goes to the React frontend on unprivileged nginx; slash api goes to the FastAPI backend, which talks to PostgreSQL. Alembic migrations run once per release as a Job. Prometheus scrapes every API pod through a ServiceMonitor and Grafana visualises it. GitHub Actions builds and scans images and pushes them to GHCR tagged by commit SHA; Argo CD keeps the cluster in sync with Git.

### Slide 4: Stack and why

Each layer uses mainstream, current tooling. One notable decision: the course examples use ingress-nginx, but that project was retired upstream in March 2026, so I chose Traefik. Every decision like this is written down as an ADR in docs slash adr.

### Slide 5: Tests, quality and containers

The backend has 33 unit tests on an in-memory SQLite database through FastAPI dependency overrides, plus two integration tests that run Alembic and the API against real PostgreSQL in CI. The frontend has 15 vitest tests. Both images are multi-stage and run as non-root: UID 10001 for the API and UID 101 for nginx. Docker Compose starts all three services with health-gated ordering and a persistent volume.

### Slide 6: CI/CD: nothing ships unless every gate passes

Four gate jobs run in parallel: backend, frontend, secret scan and infrastructure checks. Only if all pass are the images built and scanned by Trivy, and only a clean scan is pushed to GHCR, tagged with the full commit SHA. The last job verifies the build provenance, deploys that exact SHA to a throwaway kind cluster and smoke-tests it through the Ingress.

### Slide 7: DevSecOps: a clean Trivy gate, and why it is clean

Trivy scans both images before they are pushed and fails the job on any fixable high or critical CVE. The current result is zero for both images. That is a consequence of choices: current minimal base images, a multi-stage build that leaves compilers out of the runtime image, and pinned dependencies kept current by Dependabot. The full report with all severities is still uploaded for visibility.

### Slide 8: Terraform: AWS VPC + EKS, as code

Terraform defines a VPC with two public and two private subnets, EKS 1.35 with a managed node group of two t3 medium nodes, IAM roles, add-ons and the EBS CSI driver. Costly extras like a NAT gateway are behind switches. It passes validate, four terraform tests and an offline plan of 29 resources. Honest status: it has not been applied, because no valid AWS credentials were available, so there are no AWS console screenshots. The runbook has the exact apply and destroy steps.

### Slide 9: Kubernetes + Helm on kind

The Helm chart deploys the frontend and backend with at least two replicas each, ClusterIP services, PostgreSQL as a StatefulSet, the migration job, an Ingress, autoscalers, disruption budgets, a network policy and a ServiceMonitor. Under load the backend autoscaler went from two to five replicas and back.

### Slide 10: Argo CD: Git is the source of truth

Argo CD watches the chart and an environment values file on main. Promoting a build is a commit that changes the image SHA, made by a script that refuses builds that are not in GHCR. Rolling back is a git revert. In the recorded drill, both converged in under a minute.

### Slide 11: Observability: Prometheus + Grafana

The API exposes Prometheus metrics: request counts and latency by endpoint, plus business counters for stock received and food dispatched. Prometheus discovers every API pod through the ServiceMonitor: five out of five were up during the scale-out. Grafana shows a provisioned dashboard with request rate, latency percentiles, error ratio, replicas and CPU.

### Slide 12: Failure labs and real incidents

Four labs break something on purpose in an isolated namespace, and each was diagnosed and fixed with kubectl. More valuable were the real incidents found while building: a Docker Hub DNS failure, a Traefik rollout deadlock caused by host ports, Grafana thrashing its garbage collector, and a schema error that the CI pipeline caught.

### Slide 13: How every claim is backed

Every terminal output in the evidence folder was recorded by a script that runs the real command and saves its output verbatim. Screenshots of terminals are renders of those transcripts and name their source; browser screenshots carry the URL they came from. Nothing about AWS is claimed beyond what ran offline.

### Slide 14: What I learned

The biggest lessons: gates only matter if they run before publishing; immutable SHA tags make rollbacks trivial; readiness probes and migration jobs turn data problems into visible, contained failures; and most of the real problems were in the platform, not the code, which is exactly what monitoring and runbooks are for.

### Slide 15: Thank you

Thank you. Next, the live walkthrough: the codebase, CI/CD, Terraform, Argo CD, Kubernetes, Prometheus and Grafana.

## Part 2 - Live walkthrough

### 1. Codebase

**On screen:** GitHub repository: root, backend/app, routers/dispatches.py, backend/tests, frontend/src, helm/pantrypulse/templates, terraform/

**Narration:** Now the live walkthrough, starting with the repository on GitHub. The backend folder holds the FastAPI application: models, schemas, and one router per resource. The dispatch router is where the business rules live. Dispatching more than is left returns 422, and dispatching expired or held stock returns 409. The tests run on an in-memory database. The frontend is React with Vite. One Helm chart serves CI, the local cluster and EKS, and the terraform folder defines the AWS network and cluster.

### 2. CI/CD

**On screen:** Live terminal: git push of a real commit to main; the GitHub Actions run page until all six jobs finish (waiting part sped up); job summary with Trivy results; GHCR package with the new SHA tag

**Narration:** Next, CI and CD. I push a real commit to main, and GitHub Actions starts the pipeline within seconds. Four gate jobs run in parallel: backend tests and security checks, frontend tests and build, a full history secret scan, and infrastructure checks. Then both images are built and scanned by Trivy, and only a clean scan is pushed to the GitHub container registry, tagged with the commit SHA. The last job deploys that exact SHA to a throwaway kind cluster and smoke tests it through the Ingress. The waiting is sped up. All six jobs pass, and the new images appear in the registry.

### 3. Terraform

**On screen:** Live terminal: terraform fmt/validate, terraform test, offline terraform plan (resource list + Plan: 29 to add); card stating the AWS Console status

**Narration:** Terraform. The code is formatted and valid, and four plan time tests pass without an AWS account. The offline plan lists the VPC, the subnets, the internet gateway and route tables, the EKS cluster, the node group, IAM roles and add-ons. Twenty nine resources in total. To be clear about the AWS console: this was not applied, because the AWS credentials available were invalid, and nothing is faked. The runbook documents the apply and destroy steps.

### 4. Argo CD

**On screen:** Live terminal: /api/info before; scripts/promote.sh <sha>; git push; Argo CD UI syncing to Synced/Healthy; pods running the promoted image; /api/info after

**Narration:** Argo CD. The cluster is currently running an older build. I promote the build that CI just published. Promotion is a Git commit that changes the image tag, made by a script that refuses any build that is not in the registry. After the push, Argo CD detects the new commit, runs the migration hook and rolls the deployments. It reports Synced and Healthy, and every pod now runs the promoted SHA.

### 5. Kubernetes

**On screen:** Live terminal: kubectl get nodes, pods, svc, ingress, hpa, pdb, networkpolicy, pvc, servicemonitor; the application through the Ingress

**Narration:** Kubernetes. All pods are running: two backend and two frontend replicas, and PostgreSQL as a stateful set. The services are cluster IP, Traefik serves the Ingress, and both deployments have autoscalers. There are disruption budgets, a network policy around the database, a persistent volume, and a service monitor. And this is the application, served through the Ingress.

### 6. Prometheus

**On screen:** Prometheus Targets page filtered to pantrypulse-backend (UP); PromQL graph of request rate per endpoint

**Narration:** Prometheus. The service monitor discovers every API pod, and all targets are up. This query shows the live request rate for each endpoint.

### 7. Grafana

**On screen:** Grafana dashboard PantryPulse - API overview with live data, 10 s refresh

**Narration:** Finally, Grafana. The provisioned PantryPulse dashboard shows the request rate, p95 latency, the error ratio and the number of healthy targets. Below are latency by endpoint, replicas and CPU from the autoscaler, and the business metric: food dispatched. Thank you for watching.

## Re-running the walkthrough yourself

```bash
scripts/cluster-up.sh && scripts/install-monitoring.sh && scripts/install-argocd.sh
git push origin main                      # CI: watch the run under Actions
scripts/promote.sh <green-sha> && git push # GitOps promotion; watch Argo CD
kubectl -n pantrypulse get pods,svc,ingress,hpa
scripts/generate-traffic.sh               # then open Prometheus targets and the Grafana dashboard
```
