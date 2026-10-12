# Troubleshooting labs

Four failure drills in an isolated namespace (`pp-lab`), so the real
`pantrypulse` release is never touched. Each one was broken, diagnosed and
fixed on the local kind cluster; the transcripts linked below are the
verbatim terminal output of those runs.

```bash
scripts/troubleshoot.sh apply <1|2|3|4> [<commit-sha>]   # break it
scripts/troubleshoot.sh reset                            # delete pp-lab
```

Labs that need a working image take a commit SHA whose images CI has
published to GHCR (default: `origin/main`).

| Lab | Symptom | Root cause | Fix | Transcript |
|-----|---------|-----------|-----|------------|
| 1 | Pod `ErrImagePull` → `ImagePullBackOff` | Tag `v9.9.9-does-not-exist` was never built (CI only publishes commit SHAs) | `kubectl set image` to a published SHA | [lab-1](../docs/evidence/transcripts/lab-1-image-pull-backoff.txt) |
| 2 | Pods Ready, but `wget http://lab-web/healthz` → *Connection refused* | Service selector `app: lab-webb` matches no pod → EndpointSlice empty | Patch the selector to `app: lab-web` | [lab-2](../docs/evidence/transcripts/lab-2-service-no-endpoints.txt) |
| 3 | Migration Job pods in `Error`, Job never completes | `DATABASE_URL` points at host `pantrypulse-postgres-typo` → `OperationalError: failed to resolve host` | Re-create the Job with the right URL (Job templates are immutable) | [lab-3](../docs/evidence/transcripts/lab-3-database-failure.txt), [fix](../docs/evidence/transcripts/lab-3-4-fix.txt) |
| 4 | API pod `Running` but `0/1` Ready; endpoint `ready=false` | `/ready` returns `503 {"status":"NOT_READY"}`: the schema was never migrated | Run the migrations (the corrected Lab 3 Job); pod turns Ready on its own | [lab-4](../docs/evidence/transcripts/lab-4-readiness-failure.txt), [fix](../docs/evidence/transcripts/lab-3-4-fix.txt) |

## Lab 1: ImagePullBackOff

```bash
kubectl -n pp-lab get pods -l app=lab-broken-image          # ErrImagePull
kubectl -n pp-lab describe pod -l app=lab-broken-image       # Events: "...: not found"
kubectl -n pp-lab set image deploy/lab-broken-image web=ghcr.io/pratyushmishra-2nd/pantrypulse-frontend:<sha>
kubectl -n pp-lab rollout status deploy/lab-broken-image
```

Read the *last* pull error. In the recorded run the first attempt failed on
DNS (`lookup ghcr.io ... server misbehaving`, the same flaky resolver as
[incident 1](../docs/evidence/transcripts/incident-1-postgres-image-pull.txt)),
and only the retry reached GHCR and returned the real cause, `not found`.

## Lab 2: Service with no endpoints

```bash
kubectl -n pp-lab get endpointslices -l kubernetes.io/service-name=lab-web   # ENDPOINTS <unset>
kubectl -n pp-lab get svc lab-web -o jsonpath='{.spec.selector}'             # {"app":"lab-webb"}
kubectl -n pp-lab get pods --show-labels                                     # app=lab-web
kubectl -n pp-lab patch svc lab-web --type merge -p '{"spec":{"selector":{"app":"lab-web"}}}'
```

Healthy pods with an empty EndpointSlice nearly always mean a selector or
`targetPort` mismatch.

## Labs 3 and 4: database failure, then a pod that is never Ready

```bash
kubectl -n pp-lab logs -l app=lab-migrate --tail=4            # failed to resolve host 'pantrypulse-postgres-typo'
kubectl -n pp-lab describe pod -l app=lab-api | grep Unhealthy # Readiness probe failed: statuscode: 503
kubectl -n pp-lab get endpointslices -l kubernetes.io/service-name=lab-api \
  -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]} ready={.conditions.ready}{"\n"}{end}'
```

`kubectl get endpointslices` still lists a not-ready pod's IP; the
`conditions.ready` field shows that the Service does not route to it.
The fix is to delete the Job, re-create it with the correct `DATABASE_URL`,
wait for `condition=complete`, and then the API pod turns Ready without a restart,
because `/ready` checks both the database connection and the
`alembic_version` table.

In the real chart this failure is prevented by design: migrations run once
per release as a Job (an Argo CD Sync hook under GitOps), the password comes
from a Secret, and the backend's readiness probe keeps a half-migrated API
out of the Service.

## Incidents found while building the platform (not staged)

These were real failures on the way, recorded as they happened:

| # | What broke | Diagnosis | Fix | Transcript |
|---|------------|-----------|-----|------------|
| 1 | First `helm install` timed out, postgres `ImagePullBackOff` | Docker Hub DNS lookup failed inside the kind node | Pulled once DNS recovered; `helm upgrade` → revision 2 deployed | [incident-1](../docs/evidence/transcripts/incident-1-postgres-image-pull.txt), [recovery](../docs/evidence/transcripts/helm-upgrade-recovered.txt) |
| 2 | Traefik upgrade hung, new pod `Pending` | `didn't have free ports`: surge pod needs the hostPort the old pod holds | `maxSurge: 0, maxUnavailable: 1` | [incident-2](../docs/evidence/transcripts/incident-2-traefik-hostport.txt) |
| 3 | Grafana `/api/health` 503, liveness restarts, 20+ CPU cores | `GOMEMLIMIT=345MiB` derived from a 384Mi limit, usage 344Mi → GC ran non-stop | Limit 768Mi, CPU cap 1 core | [incident-3](../docs/evidence/transcripts/incident-3-grafana-gc-thrash.txt) |
| 4 | CI `deploy-kind` job failed | Traefik chart schema: `additional properties 'logs' not allowed` | Removed the keys (commit 54a966e) | CI run 38282550447 |
