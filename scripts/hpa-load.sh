#!/usr/bin/env bash
# Drive enough CPU into the API to make the HorizontalPodAutoscaler scale out,
# then watch it scale back in.
#   scripts/hpa-load.sh [<sha>] [seconds]
# The load generator reuses the backend image (already on the node, no extra
# pull) and runs as a Job in its own namespace, hitting the Service directly.
set -euo pipefail
cd "$(dirname "$0")/.."

SHA="${1:-$(git rev-parse origin/main)}"
SECONDS_OF_LOAD="${2:-240}"

kubectl create namespace pp-load --dry-run=client -o yaml | kubectl apply -f -
kubectl -n pp-load delete job hpa-load --ignore-not-found --wait=true
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: hpa-load
  namespace: pp-load
spec:
  parallelism: 4
  completions: 4
  backoffLimit: 0
  ttlSecondsAfterFinished: 600
  template:
    spec:
      restartPolicy: Never
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: load
          image: ghcr.io/pratyushmishra-2nd/pantrypulse-backend:${SHA}
          command: ["python", "-c"]
          args:
            - |
              import time, urllib.request, concurrent.futures as cf
              url = "http://pantrypulse-backend.pantrypulse.svc:8000/api/lots/summary"
              end = time.time() + ${SECONDS_OF_LOAD}
              def worker(_):
                  n = 0
                  while time.time() < end:
                      try:
                          urllib.request.urlopen(url, timeout=5).read(); n += 1
                      except Exception:
                          pass
                  return n
              with cf.ThreadPoolExecutor(8) as pool:
                  print("requests sent:", sum(pool.map(worker, range(8))))
          resources:
            requests: { cpu: 50m, memory: 64Mi }
            limits: { cpu: 500m, memory: 128Mi }
          securityContext:
            allowPrivilegeEscalation: false
            capabilities: { drop: ["ALL"] }
EOF
echo "Load running for ${SECONDS_OF_LOAD}s. Watch: kubectl -n pantrypulse get hpa -w"
