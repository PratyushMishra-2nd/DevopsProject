# Runbook: rolling back a bad release

Images are immutable and tagged with commit SHAs
([ADR 0002](../adr/0002-immutable-sha-image-tags.md)), so a rollback always
means "run an older SHA that is still in GHCR".

## Environment managed by Argo CD (default)

```bash
git log --oneline -- gitops/values-local.yaml      # find the promotion commit
git revert <promotion-commit>
git push origin main
kubectl -n argocd get application pantrypulse -w   # Synced / Healthy on the revert commit
curl -s http://pantrypulse.127.0.0.1.nip.io:8088/api/info   # git_sha = previous build
```

- A real run is recorded in
  [gitops-rollback.txt](../evidence/transcripts/gitops-rollback.txt).
- Don't use `helm rollback` or `kubectl set image` here. Argo CD self-heal
  reverts any change that is not in Git.
- For an emergency where Git is unavailable: disable auto-sync in the
  Argo CD UI, then use **History and rollback**. Re-enable auto-sync after
  committing the same change to Git.

## Release installed with plain Helm

```bash
helm history pantrypulse -n pantrypulse
helm rollback pantrypulse <revision> -n pantrypulse --wait
kubectl -n pantrypulse rollout status deploy/pantrypulse-backend
```

Each revision renders its own migration Job (`pantrypulse-migrate-<rev>`).
Alembic migrations are written to be backward compatible (expand, then
contract), so an older API version runs against the newer schema.

## Database

A rollback never downgrades the schema automatically. If a migration itself
was the problem:

1. Restore from backup, or run `alembic downgrade <rev>` from a backend pod.
2. Then roll back the application.

Take a `pg_dump` before any risky migration:

```bash
kubectl -n pantrypulse exec pantrypulse-postgres-0 -- sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup.sql
```
