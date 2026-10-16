#!/usr/bin/env bash
# Generate CPU load on the backend from *inside* the cluster to demonstrate the HPA.
#
#   scripts/load-test.sh                         # 8 workers for 3 minutes
#   WORKERS=12 DURATION=300 scripts/load-test.sh
#
# Watch it scale in another terminal:   kubectl get hpa -n clinicflow -w
set -euo pipefail

NAMESPACE="${NAMESPACE:-clinicflow}"
WORKERS="${WORKERS:-8}"
DURATION="${DURATION:-180}"
TARGET="${TARGET:-http://clinicflow-backend:8000}"

kubectl -n "$NAMESPACE" delete pod load-generator --ignore-not-found --wait=true >/dev/null

# The appointment list + stats endpoints join three tables and serialise every row:
# a realistic, CPU-heavy read path.
kubectl -n "$NAMESPACE" apply -f - <<YAML
apiVersion: v1
kind: Pod
metadata:
  name: load-generator
  labels: { app: load-generator }
spec:
  restartPolicy: Never
  activeDeadlineSeconds: $((DURATION + 60))
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
    seccompProfile: { type: RuntimeDefault }
  containers:
    - name: load
      image: busybox:1.37
      securityContext:
        allowPrivilegeEscalation: false
        capabilities: { drop: ["ALL"] }
      command:
        - sh
        - -c
        - |
          end=\$((\$(date +%s) + $DURATION))
          for i in \$(seq 1 $WORKERS); do
            ( while [ \$(date +%s) -lt \$end ]; do
                wget -q -O /dev/null $TARGET/api/appointments
                wget -q -O /dev/null $TARGET/api/appointments/stats
              done ) &
          done
          wait
          echo "load test finished"
YAML

echo "Load generator started: $WORKERS workers for ${DURATION}s against $TARGET"
echo "Watch:  kubectl get hpa -n $NAMESPACE -w"
echo "Stop:   kubectl -n $NAMESPACE delete pod load-generator"
