#!/usr/bin/env bash
# One command to rehearse the whole Kubernetes deployment on a laptop:
#   kind cluster -> add-ons -> build images -> load into kind -> helm install
# Afterwards open http://clinicflow.localhost
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLUSTER=clinicflow

if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --config "$ROOT/k8s/kind/cluster.yaml"
fi
kubectl config use-context "kind-$CLUSTER"

"$ROOT/scripts/bootstrap-cluster.sh" kind

echo "==> Building images"
docker build -t clinicflow-backend:local --build-arg APP_VERSION=local "$ROOT/backend"
docker build -t clinicflow-frontend:local --build-arg APP_VERSION=local "$ROOT/frontend"
kind load docker-image clinicflow-backend:local clinicflow-frontend:local --name "$CLUSTER"

echo "==> Deploying ClinicFlow with Helm"
helm upgrade --install clinicflow "$ROOT/helm/clinicflow" \
  -n clinicflow --create-namespace \
  -f "$ROOT/helm/clinicflow/values-dev.yaml" \
  --wait --timeout 5m

# Pods are not restarted when a :local image is rebuilt with the same tag; force it.
kubectl -n clinicflow rollout restart deploy/clinicflow-backend deploy/clinicflow-frontend
kubectl -n clinicflow rollout status deploy/clinicflow-backend --timeout=180s
kubectl -n clinicflow rollout status deploy/clinicflow-frontend --timeout=120s

kubectl -n clinicflow get pods,svc,ingress,hpa
echo
echo "ClinicFlow:  http://clinicflow.localhost"
echo "Grafana:     kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80"
echo "Prometheus:  kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090"
