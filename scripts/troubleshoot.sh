#!/usr/bin/env bash
# Apply / reset the troubleshooting labs in the isolated pp-lab namespace.
#   scripts/troubleshoot.sh apply <1|2|3|4> [<sha>]   break something
#   scripts/troubleshoot.sh reset                      delete the lab namespace
# Labs that need a working image use the given commit SHA (default origin/main).
set -euo pipefail
cd "$(dirname "$0")/.."

cmd="${1:?usage: troubleshoot.sh apply <lab> [sha] | reset}"
case "$cmd" in
  apply)
    lab="${2:?lab number 1-4}"
    sha="${3:-$(git rev-parse origin/main)}"
    file=$(ls troubleshooting/0"$lab"-*.yaml)
    kubectl apply -f troubleshooting/00-lab-namespace.yaml
    sed "s/__SHA__/$sha/g" "$file" | kubectl apply -f -
    ;;
  reset)
    kubectl delete namespace pp-lab --ignore-not-found --wait=true
    ;;
  *)
    echo "unknown command $cmd" >&2; exit 1 ;;
esac
