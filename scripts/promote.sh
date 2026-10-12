#!/usr/bin/env bash
# GitOps promotion: point the local environment at an image build that CI has
# already tested, scanned and published, and commit that change. Argo CD picks
# the commit up and rolls the cluster forward; `git revert` rolls it back.
#   scripts/promote.sh <full-git-sha>
set -euo pipefail
cd "$(dirname "$0")/.."

SHA="${1:?usage: scripts/promote.sh <full-git-sha>}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "need a full 40-character commit SHA" >&2; exit 1; }

repo="ghcr.io/pratyushmishra-2nd/pantrypulse"
for c in backend frontend; do
  if ! docker manifest inspect "$repo-$c:$SHA" >/dev/null 2>&1; then
    echo "image $repo-$c:$SHA is not in GHCR - did the CI run for $SHA pass?" >&2
    exit 1
  fi
done

sed -i.bak -E "s/^(    tag: ).*/\1\"$SHA\"/" gitops/values-local.yaml && rm -f gitops/values-local.yaml.bak
git add gitops/values-local.yaml
git commit -m "Promote build ${SHA:0:7} to the local GitOps environment"
echo "Committed. Push to main and Argo CD will sync within its reconciliation interval."
