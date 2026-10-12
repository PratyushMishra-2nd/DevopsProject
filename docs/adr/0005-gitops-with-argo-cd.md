# ADR 0005: Continuous delivery by GitOps with Argo CD

- Status: accepted
- Date: 2026-10-13

## Context

CI can prove that a commit builds, passes tests, is free of fixable
HIGH/CRITICAL CVEs, and deploys. That proof comes from an ephemeral kind
cluster in the `deploy-kind` job.

A long-lived environment needs more than that:

- Every change is reviewed.
- The cluster can be rebuilt from Git alone.
- Drift is corrected automatically.
- A rollback is as easy as a revert.

## Decision

- An Argo CD `Application`
  ([`gitops/application.yaml`](../../gitops/application.yaml)) tracks
  `helm/pantrypulse` on `main` with two value files:
  - `values-dev.yaml`: the environment profile.
  - [`gitops/values-local.yaml`](../../gitops/values-local.yaml): the
    desired image tags, the database Secret name, and migrations as a Sync
    hook.
- Sync is automated, with `prune` and `selfHeal`. HPA-managed
  `spec.replicas` is ignored, so Argo CD and the autoscaler don't fight.
- **Promotion** is a commit made by `scripts/promote.sh <sha>`. The script
  checks that the images exist in GHCR first.
- **Rollback** is `git revert` of that commit.
- The database password is never in Git. It is created once as the
  `pantrypulse-db` Secret and referenced through `database.existingSecret`.

Full flow: [docs/engineering/gitops.md](../engineering/gitops.md).

## Consequences

- The recorded drill:
  - Promotion of `8be415d` (commit 7038d15).
  - Rollback via revert (commit c1fc74c) back to `161f84e`.
  - Argo CD converged each change within about 40 seconds.
  - Transcripts:
    [promotion](../evidence/transcripts/gitops-promotion.txt),
    [rollback](../evidence/transcripts/gitops-rollback.txt).
- Argo CD adopted an existing Helm release. Two things needed fixing for a
  clean `Synced/Healthy`:
  - The StatefulSet `volumeClaimTemplates` now spell out the API server
    defaults.
  - Traefik now publishes an Ingress status address. See
    [ADR 0004](0004-traefik-ingress-controller.md).
- Promotion commits trigger a full CI run. That costs a few CI minutes but
  re-proves the whole pipeline on every environment change.
