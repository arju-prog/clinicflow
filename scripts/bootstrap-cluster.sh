#!/usr/bin/env bash
# Install the cluster add-ons ClinicFlow relies on:
#   - Traefik         (Ingress controller: implements the Ingress resource)
#   - metrics-server  (CPU/memory metrics for `kubectl top` and the HPA)
#   - kube-prometheus-stack (Prometheus Operator + Prometheus + Grafana + kube-state-metrics)
#
# Usage: scripts/bootstrap-cluster.sh kind|eks
set -euo pipefail

TARGET="${1:?usage: $0 kind|eks}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

helm repo add traefik https://traefik.github.io/charts >/dev/null
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo update >/dev/null

kubectl apply -f "$ROOT/k8s/namespace.yaml"

if [[ "$TARGET" == "eks" ]]; then
  echo "==> gp3 StorageClass (EBS CSI)"
  kubectl apply -f "$ROOT/k8s/storageclass-gp3.yaml"
  # Older clusters ship a default gp2 class; make gp3 the only default.
  kubectl annotate storageclass gp2 storageclass.kubernetes.io/is-default-class=false --overwrite 2>/dev/null || true
fi

echo "==> Traefik ingress controller"
helm upgrade --install traefik traefik/traefik --version 42.0.0 \
  -n traefik --create-namespace \
  -f "$ROOT/monitoring/traefik-values-$TARGET.yaml" --wait

echo "==> metrics-server"
METRICS_ARGS=()
[[ "$TARGET" == "kind" ]] && METRICS_ARGS=(-f "$ROOT/monitoring/metrics-server-values-kind.yaml")
helm upgrade --install metrics-server metrics-server/metrics-server --version 3.14.0 \
  -n kube-system ${METRICS_ARGS[@]+"${METRICS_ARGS[@]}"} --wait

echo "==> kube-prometheus-stack"
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack --version 92.9.0 \
  -n monitoring --create-namespace \
  -f "$ROOT/monitoring/kube-prometheus-stack-values.yaml" --wait --timeout 10m

echo
echo "Add-ons ready. Grafana admin password:"
kubectl -n monitoring get secret kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo
