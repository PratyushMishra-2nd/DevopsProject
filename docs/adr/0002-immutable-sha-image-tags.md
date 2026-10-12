# ADR 0002: Images are tagged only with the full commit SHA, after a Trivy gate

- Status: accepted
- Date: 2026-10-12

## Context

A deployment should always answer "which commit is running?" and must never
silently change underneath us. `latest` and other mutable tags break both
properties. A vulnerable image must also never reach the registry.

## Decision

- CI builds `ghcr.io/pratyushmishra-2nd/pantrypulse-{backend,frontend}` and
  tags each image **only** with the 40-character `GITHUB_SHA`. There is no
  `latest`.
- The images are scanned with Trivy **before** the push. HIGH and CRITICAL
  findings that have a fix fail the job (`--exit-code 1 --ignore-unfixed`),
  and nothing is pushed.
- After the push, CI generates SPDX SBOMs and a build-provenance
  attestation.
  - The `deploy-kind` job runs `gh attestation verify` before deploying.
- The Helm chart has empty image tags and refuses to render without one
  (`required "backend.image.tag must be set to the Git commit SHA"`). Every
  install names a SHA: `--set backend.image.tag=<sha>` in CI, or
  `gitops/values-local.yaml` under Argo CD.
- `scripts/promote.sh` refuses any SHA whose images are not in GHCR, so
  only builds that passed every gate can be promoted.
- The backend reports its SHA at `/api/info`, and the UI shows it in the
  header badge.

## Consequences

- A rollback is just "deploy an older SHA". It is fully reproducible, and
  the old image is still in GHCR.
- Pull requests build and scan images but never publish them.
- `--ignore-unfixed` means a CVE without an upstream fix does not block a
  release. The informational full report (all severities) is uploaded as a
  CI artifact, so these stay visible.
