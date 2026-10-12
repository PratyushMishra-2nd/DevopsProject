#!/bin/sh
# Optional start-up work for single-container setups (Docker Compose).
# In Kubernetes, migrations run once in a Helm hook Job instead, so every
# replica does not race to migrate the schema.
set -eu

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  attempt=1
  until alembic upgrade head; do
    if [ "$attempt" -ge 15 ]; then
      echo '{"level":"error","msg":"migrations failed after 15 attempts"}'
      exit 1
    fi
    echo "{\"level\":\"warning\",\"msg\":\"database not ready, retrying migrations\",\"attempt\":$attempt}"
    attempt=$((attempt + 1))
    sleep 2
  done
fi

if [ "${SEED_DEMO:-false}" = "true" ]; then
  python -m app.seed
fi

exec "$@"
