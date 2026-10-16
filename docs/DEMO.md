# Final presentation: live demo script (~12 minutes)

Before the session: the EKS cluster is up (or kind via `./scripts/kind-up.sh`), and these tabs are open: the app via Ingress, GitHub Actions, GHCR packages, Grafana, and Prometheus targets. Have two terminals ready.

| # | Step | Show / say |
|---|---|---|
| 1 | **Application** | Open the app through the Ingress hostname. Book an appointment, then try the *same slot* again → red "already has appointment" toast (409). Check a patient in. |
| 2 | **API** | `/docs` (port-forward the backend if on EKS): run `POST /api/appointments` and `PUT` (status → COMPLETED), then `DELETE`. |
| 3 | **Database** | `kubectl -n clinicflow exec -it clinicflow-postgres-0 -- psql -U clinicflow -c 'select id, status, scheduled_at from appointments order by id desc limit 5;'` and `\dt` (shows `alembic_version`). |
| 4 | **Git** | Make a visible change, e.g. in `frontend/src/App.jsx` change `'Sunrise Family Clinic'` to `'Sunrise Family Clinic · Koramangala'`. Then `git commit -am "Show branch location in sidebar"` and `git push`. |
| 5 | **CI** | Actions tab: tests → IaC lint → secret scan → image builds. Open the pytest step and show 36 passing tests. |
| 6 | **Docker** | Show both Dockerfiles: multi-stage, `USER 10001` / `USER 101`. |
| 7 | **Security** | Open the Trivy gate step log: 0 HIGH/CRITICAL. Explain the urllib3 CVE that pip vendored and how removing pip fixed it (`docs/SECURITY.md`). |
| 8 | **Registry** | GHCR package page: the tag equals the commit SHA you just pushed. |
| 9 | **Terraform** | Walk through `terraform/main.tf` (VPC, subnets), `eks.tf` (node group, addons), `github-oidc.tf` (keyless deploys). |
| 10 | **Kubernetes** | `kubectl get pods,svc -n clinicflow -o wide`: 2 backend + 2 frontend + postgres, spread across nodes. |
| 11 | **Helm** | `helm list -n clinicflow` and `helm history clinicflow -n clinicflow`: a new revision from the pipeline. Refresh the app: the sidebar shows the new text and the new UI/API SHA. |
| 12 | **Ingress** | `kubectl get ingress -n clinicflow`: `/api` → backend, `/` → frontend. |
| 13 | **HPA** | `./scripts/load-test.sh` then `kubectl get hpa -n clinicflow -w`: replicas 2 → 4 → 6. |
| 14 | **Monitoring** | Grafana dashboard: request rate jumps, the per-pod panel shows the new pods taking traffic, HPA replicas rise. Prometheus targets: every backend pod UP. |
| 15 | **Failure simulation** | `kubectl apply -f troubleshooting/broken-service.yaml`, then `kubectl -n clinicflow get endpointslices -l kubernetes.io/service-name=clinicflow-api-broken` (empty) and `get pods --show-labels`. Spot the `backnd` typo, patch it, and the endpoints appear. Optionally run `broken-image.yaml` → ImagePullBackOff → `describe pod`. |

## Rollback (if asked "what if the deploy is bad?")

```bash
helm history clinicflow -n clinicflow
helm rollback clinicflow <previous-revision> -n clinicflow
```

The pipeline also uses `--rollback-on-failure`, so a release whose pods never become ready is rolled back automatically.
