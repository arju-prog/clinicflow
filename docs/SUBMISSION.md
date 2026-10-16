# Submission evidence map

Every grading criterion from `GRADING.md`, with the file that satisfies it and the evidence to submit.
Legend: ✅ verified locally (Docker / kind) · ☁️ needs AWS or GitHub (follow `docs/AWS-DEPLOY.md`) · 📸 screenshot to capture

## M1 — Application (10)

| Criterion | Where | Status |
|---|---|---|
| FastAPI responds to `/health` | `backend/app/main.py` | ✅ |
| ≥ 4 REST endpoints (GET/POST/PUT/DELETE) | `backend/app/routers/` (3 resources × full CRUD + stats) | ✅ |
| PostgreSQL table managed by Alembic | `backend/alembic/versions/0001_*.py`, `0002_*.py` | ✅ |
| Frontend renders and calls the API | `frontend/src/` | ✅ |
| Responsive, usable UI | `frontend/src/styles.css` (breakpoints at 1200/960/680px) | ✅ |

📸 `docs/screenshots/01-dashboard.png`, `02-booking-modal.png`, `03-conflict.png`, `04-mobile-appointments.png` (already captured)

## M2 — Testing (10)

| Criterion | Where | Status |
|---|---|---|
| `pytest` runs without errors | `backend/tests/` (36 tests) | ✅ |
| ≥ 5 tests over ≥ 3 endpoints | health, doctors, patients, appointments, stats, metrics | ✅ |
| Test DB, not production | `backend/tests/conftest.py`: in-memory SQLite per test via `dependency_overrides` | ✅ |
| `pytest.ini` / `conftest.py` | `backend/pytest.ini`, `backend/tests/conftest.py` | ✅ |

📸 `cd backend && pytest -v`

## M3 — Git & GitHub (5)

| Criterion | Status |
|---|---|
| Public repository | ☁️ |
| Meaningful commit messages, ≥ 10 commits | ☁️ (history is built feature-by-feature) |
| `.gitignore` covers `.env`, `__pycache__`, `node_modules`, `.venv` | ✅ `.gitignore` |

📸 `git log --oneline` or the GitHub *Commits* page

## M4 — Docker (10)

| Criterion | Where | Status |
|---|---|---|
| `backend/Dockerfile` builds | multi-stage (builder venv → slim runtime) | ✅ |
| Frontend multi-stage Node → Nginx | `frontend/Dockerfile` | ✅ |
| Non-root images | backend `USER 10001`, frontend `USER 101` (`id` verified in both containers) | ✅ |
| `docker compose up --build` starts all 3 services | `docker-compose.yml` (with healthchecks) | ✅ |

📸 terminal running `docker compose up --build`; browser at `http://localhost:3000`

## M5 — CI/CD (15)

| Criterion | Where | Status |
|---|---|---|
| Workflow file | `.github/workflows/ci-cd.yml` | ✅ |
| Triggers on push to `main` | `on.push.branches: [main]` | ✅ |
| pytest job fails the build | `test-backend` → `needs:` blocks image jobs | ✅ |
| Frontend built | `test-frontend` (`npm run build`) | ✅ |
| Images for both | `build-scan-push` matrix | ☁️ |
| Pushed to GHCR | `docker push ghcr.io/...` | ☁️ |
| SHA tags, not `latest` | `type=sha,format=long` | ✅ (config) |

📸 a green Actions run URL; the GHCR package page showing SHA tags

## M6 — DevSecOps (5)

| Criterion | Where | Status |
|---|---|---|
| Trivy on both images in CI | `Trivy gate` step (matrix) | ✅ locally, ☁️ in CI |
| Fails on HIGH/CRITICAL | `severity: HIGH,CRITICAL`, `exit-code: '1'` | ✅ |
| Explain a CVE / clean result | `docs/SECURITY.md` (urllib3 CVE-2026-97687, fixed by removing pip) | ✅ |

📸 the Trivy gate step output from a pipeline run

## M7 — Terraform (15)

| Criterion | Where | Status |
|---|---|---|
| Valid HCL in `terraform/` | `terraform validate` passes (also run in CI) | ✅ |
| `terraform init` | | ✅ |
| `terraform plan` non-empty | needs AWS credentials | ☁️ 📸 |
| VPC with ≥ 2 public subnets | `main.tf` (2 public + 2 private) | ☁️ 📸 |
| EKS with a node group | `eks.tf` (`default` managed node group) | ☁️ 📸 |
| `terraform destroy` clean | `docs/AWS-DEPLOY.md` step 6 | ☁️ 📸 |
| `terraform.tfvars.example`, no creds | `terraform/terraform.tfvars.example` | ✅ |

## M8 — Kubernetes + Helm (15)

| Criterion | Where | Status |
|---|---|---|
| `k8s/namespace.yaml` | | ✅ |
| Chart with Chart.yaml / values / templates | `helm/clinicflow/` | ✅ (`helm lint` clean) |
| `helm upgrade --install` succeeds | | ✅ kind, ☁️ EKS |
| Backend + frontend ≥ 2 replicas | `replicaCount: 2`, HPA `minReplicas: 2` | ✅ |
| ClusterIP Services | `templates/services.yaml` | ✅ |
| Ingress `/` → frontend, `/api` → backend | `templates/ingress.yaml` (Traefik) | ✅ verified via `http://clinicflow.localhost` |
| All pods Running | | ✅ kind |

📸 `kubectl get pods -n clinicflow`, `kubectl get svc -n clinicflow`, `helm list -n clinicflow`, the app in a browser via the Ingress/LB hostname

## M9 — Observability (10)

| Criterion | Where | Status |
|---|---|---|
| `/metrics` in Prometheus format | prometheus-fastapi-instrumentator + custom counters | ✅ |
| Prometheus scraping the app | `templates/servicemonitor.yaml` | ✅ (6/6 targets UP on kind) |
| Grafana accessible | `monitoring/kube-prometheus-stack-values.yaml` | ✅ |
| Panel with live app metrics | `helm/clinicflow/files/grafana-dashboard.json` | ✅ |

📸 `curl .../metrics`; `docs/screenshots/09-prometheus-targets.png` and `10-grafana-dashboard.png` (kind versions captured; retake on EKS)

## M10 — Presentation + docs (5)

| Criterion | Where |
|---|---|
| Root `README.md` | `README.md` |
| Live demo: commit → pipeline → deployment updates | `docs/DEMO.md` (the UI footer shows the deployed Git SHA) |
