# Runbook: local development with Docker Compose

## Prerequisites

- Docker Desktop (or Docker Engine) with Compose v2
- For running the tests outside containers:
  - Python 3.12
  - Node 22+

## Start the stack

```bash
docker compose up --build --detach --wait
docker compose ps
```

| Service | Address | Notes |
|---------|---------|-------|
| UI | http://localhost:3000 | nginx serves the React build and proxies `/api` to the API |
| API | http://localhost:8000 | Swagger UI at `/docs`, plus `/health`, `/ready`, `/metrics` |
| PostgreSQL | none | not published to the host; reachable only on the Compose network |

Start-up order and data:

- Postgres must be healthy before the API starts, and the API must be
  healthy before the UI starts.
- The API container runs `alembic upgrade head` (`RUN_MIGRATIONS=true`) and
  seeds demo data on an empty database (`SEED_DEMO=true`).
- Data lives in the named volume `pgdata` and survives
  `docker compose down`
  ([transcript](../evidence/transcripts/docker-persistence.txt)).
- `docker compose down -v` deletes the volume and the data with it.

If ports 3000/8000 are taken, override them:

```bash
FRONTEND_PORT=3300 BACKEND_PORT=8800 docker compose up --build --detach --wait
```

## Tests and linters

Backend:

```bash
cd backend
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
ruff check . && ruff format --check .
bandit -r app -ll -ii
pytest -v
```

To also run the Postgres integration tests, point them at any PostgreSQL
instance:

```bash
TEST_POSTGRES_URL=postgresql+psycopg://user:pass@localhost:5432/pantrypulse_test pytest -v -m postgres
```

Frontend:

```bash
cd frontend
npm ci
npm run lint
npx vitest run
npm run build
```

## Browser smoke test

```bash
python scripts/ui_smoke.py http://127.0.0.1:3000
```

It drives the full journey in a real browser: receive a lot, dispatch from
it, edit it, void the dispatch, delete the lot. It needs Playwright
(`pip install playwright && playwright install chromium`).

## Troubleshooting

| Symptom | Check |
|---------|-------|
| UI shows "Cannot reach the PantryPulse API. Is the backend running?" | `docker compose logs backend`; `curl localhost:8000/ready` |
| `/ready` returns 503 | Migrations have not run, or the DB is down. Check `docker compose logs backend` for `alembic` lines |
| Port already in use | Override `FRONTEND_PORT` / `BACKEND_PORT` as shown above |
