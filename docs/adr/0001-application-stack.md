# ADR 0001: Application stack — FastAPI, React, PostgreSQL

- Status: accepted
- Date: 2026-10-12

## Context

PantryPulse tracks donated food for a community food bank: donors, stock
lots with expiry dates, and dispatches to partner organisations. The
capstone needs a real three-tier application (UI, API, database) that every
DevOps layer can wrap: containers, CI/CD, Kubernetes, GitOps, monitoring.

Requirements that shaped the choice:

- A relational model with real constraints: a dispatch cannot exceed the
  remaining quantity, expired or held lots cannot be dispatched, and a lot
  with dispatch history cannot be deleted.
- First-class health, readiness and Prometheus metrics.
- Fast, deterministic tests that do not need Docker.
- Small, non-root container images.

## Decision

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, psycopg 3, and
  `prometheus-fastapi-instrumentator`.
  - `/health` is liveness. `/ready` is readiness: it checks the DB and the
    `alembic_version` table, and returns 503 otherwise.
  - `/metrics` exposes the metrics; `/api/info` reports the deployed git SHA.
- **Frontend:** React 19 built with Vite and served by
  `nginx-unprivileged`. nginx proxies `/api` to the backend, so the browser
  only ever talks to one origin and the CSP stays strict.
- **Database:** PostgreSQL 17, with the schema owned by Alembic migrations.
- **Tests:**
  - pytest uses an in-memory SQLite engine (StaticPool plus a dependency
    override) for unit tests.
  - Postgres-marked integration tests run in CI against a real PostgreSQL
    service.
  - The UI is covered by vitest.

## Consequences

- One language per tier with mature tooling: ruff, bandit and pip-audit;
  eslint, prettier and npm audit.
- SQLite in unit tests is fast but differs from Postgres. The integration
  tests and the Alembic upgrade in CI cover that gap.
- Migrations are a separate step, not run by every API replica at start-up.
  See [ADR 0006](0006-migrations-as-a-job.md).
