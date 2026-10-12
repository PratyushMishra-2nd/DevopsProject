# ADR 0006: Database migrations run once per release, as a Job

- Status: accepted
- Date: 2026-10-12

## Context

Running `alembic upgrade head` in every backend container's entrypoint is
simple. With two or more replicas plus an HPA, though, several pods race to
migrate. A failed migration also turns into a crash-looping API instead of
one clear failure.

## Decision

- The Helm chart renders a Job, `<release>-migrate-<revision>`, that runs
  `alembic upgrade head` with the backend image of the same SHA.
- Under Argo CD the Job is a `Sync` hook (`migrations.argocdHook: true`)
  with `BeforeHookCreation` delete policy, so it re-runs on every sync.
- Backend pods do not migrate in Kubernetes.
  - `RUN_MIGRATIONS` is only used by Docker Compose, where there is a
    single replica.
- The readiness probe (`/ready`) checks the `alembic_version` table. A pod
  whose schema is missing never receives traffic.

## Consequences

- One migration per release, with logs in one place
  (`kubectl logs job/...`).
- If the database is unreachable, the Job fails visibly (troubleshooting
  [lab 3](../../troubleshooting/README.md)). The API pods stay `0/1 Ready`
  instead of serving errors (lab 4).
- Migrations must stay backward compatible with the previous release,
  because old pods keep serving while the Job runs (expand, then contract).
