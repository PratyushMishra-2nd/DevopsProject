#!/usr/bin/env bash
# Realistic API traffic through the Ingress so Grafana panels have data:
# reads, creates, dispatches, the odd validation error (422) and missing
# record (404).
#   scripts/generate-traffic.sh [base_url] [iterations]
# The "Traffic test rice" lots it creates can be removed afterwards, see
# docs/evidence/transcripts/traffic-cleanup.txt.
set -uo pipefail
BASE="${1:-http://pantrypulse.127.0.0.1.nip.io:8088}"
N="${2:-200}"
today=$(date +%F)
later=$(date -d '+20 days' +%F 2>/dev/null || date -v+20d +%F)

for i in $(seq 1 "$N"); do
  curl -s -o /dev/null "$BASE/api/lots"
  curl -s -o /dev/null "$BASE/api/lots/summary"
  curl -s -o /dev/null "$BASE/api/donors"
  curl -s -o /dev/null "$BASE/api/lots?category=dairy"
  if (( i % 5 == 0 )); then
    id=$(curl -s -H 'Content-Type: application/json' -X POST "$BASE/api/lots" \
      -d "{\"item_name\":\"Traffic test rice $i\",\"category\":\"grains\",\"quantity\":10,\"unit\":\"kg\",\"storage\":\"ambient\",\"received_on\":\"$today\",\"expires_on\":\"$later\"}" \
      | sed -n 's/.*"id":\([0-9]*\).*/\1/p')
    if [ -n "$id" ]; then
      curl -s -o /dev/null -H 'Content-Type: application/json' -X POST "$BASE/api/dispatches" \
        -d "{\"lot_id\":$id,\"partner\":\"Traffic test shelter\",\"quantity\":4}"
    fi
  fi
  (( i % 7 == 0 )) && curl -s -o /dev/null "$BASE/api/lots/999999"                       # 404
  (( i % 11 == 0 )) && curl -s -o /dev/null -X POST -H 'Content-Type: application/json' \
    "$BASE/api/lots" -d '{"item_name":"x","quantity":-1}'                                  # 422
  (( i % 50 == 0 )) && echo "sent $i rounds"
done
echo "done: $N rounds against $BASE"
