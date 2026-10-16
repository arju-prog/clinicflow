# Evidence screenshots

| Rubric | File | What it shows |
|---|---|---|
| M1 | `01-dashboard.png`, `02-booking-modal.png`, `03-conflict.png`, `04-mobile-appointments.png` | UI, booking form, double-booking rejected (409), phone layout |
| M2 | `05-pytest.png` | `pytest -v`: 36 passed |
| M3 | `06-git-log.png` | commit history |
| M4 | `07-docker-compose.png`, `07b-compose-localhost-3000.png` | `docker compose up --build`, all 3 services healthy, non-root `id`, app on :3000 |
| M5 | `ci-01-pipeline-green.png`, `ci-03-ghcr-backend.png` | green pipeline incl. EKS deploy; GHCR tags = Git SHA |
| M6 | `ci-02-trivy-gate.png` | Trivy gate output from the CI run: 0 HIGH/CRITICAL in both images |
| M7 | `tf-01-plan.png`, `tf-02-aws-vpc-subnets.png`, `tf-03-aws-eks.png` | terraform plan/apply, VPC with 2 public + 2 private subnets, EKS cluster + node group (AWS CLI) |
| M7 | `aws-console-01-vpc.png`, `aws-console-02-subnets.png` | AWS Console (Mumbai): `clinicflow-vpc` available; 2 public + 2 private `clinicflow-vpc-*` subnets in ap-south-1a/1b |
| M7 | `aws-console-03-eks-clusters.png`, `aws-console-04-eks-cluster.png`, `aws-console-05-eks-compute.png` | AWS Console: `clinicflow-eks` Active (1.34), node group Active with 2 nodes |
| M7 | `tf-04-destroy.png` | `terraform destroy`: 65 resources destroyed, state empty, 0 clusters/VPCs/NATs/instances/EIPs/LBs/volumes left |
| M8 | `eks-01-kubectl-get-pods.png`, `eks-02-kubectl-get-svc.png`, `eks-03-helm-list.png`, `eks-04-app-via-ingress.png` | pods Running on 2 nodes, ClusterIP services, Ingress, HPA, PVC, Helm release, app through the Ingress controller |
| M8/M9 | `eks-05-hpa-scaling.png` | HPA scaling 2 → 6 under load on EKS |
| M9 | `08-metrics-endpoint.png`, `eks-06-prometheus-targets.png`, `eks-07-grafana-dashboard.png` | `/metrics`, Prometheus targets UP, Grafana with live traffic |
| kind rehearsal | `09-prometheus-targets.png`, `10-grafana-dashboard.png` | same checks on the local kind cluster |

Terminal screenshots are real command output rendered in a terminal-style frame.
