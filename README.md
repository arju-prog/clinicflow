# ClinicFlow — Clinic Appointment Scheduling, from laptop to Kubernetes

ClinicFlow is a small but realistic SaaS app for a family clinic's front desk. Receptionists **register patients**, manage **doctors**, and **book, check in and complete appointments**. The backend **refuses double-bookings**: a doctor can't see two patients at once, and a patient can't be in two rooms at once.

The app is the vehicle. The real subject is the DevOps path it travels: every commit is tested, containerised, security-scanned, published, and deployed with Helm to an autoscaling, monitored Kubernetes cluster on AWS that Terraform provisions.

![ClinicFlow dashboard](docs/screenshots/01-dashboard.png)

---

## Architecture

```text
 Developer ──git push──► GitHub ──► GitHub Actions
                                     ├─ ruff + pytest (36 tests)      ┐
                                     ├─ vitest + vite build           │ quality gates:
                                     ├─ helm lint + terraform validate│ any failure stops
                                     ├─ Trivy secret scan             ┘ the pipeline
                                     ├─ docker build ─► Trivy image scan (HIGH/CRITICAL = fail)
                                     ├─ push ghcr.io/<owner>/clinicflow-{backend,frontend}:<git-sha>
                                     └─ helm upgrade --install  (OIDC → AWS, no stored keys)
                                                    │
 Terraform ─► AWS ap-south-1                         ▼
              VPC 10.30.0.0/16 ── 2 public + 2 private subnets, NAT
              └── EKS 1.34 ── managed node group (m7i-flex.large ×2, AL2023)
                    │
                    ├── traefik (Ingress controller, NLB)
                    │      ├── /      ─► clinicflow-frontend  (React + Nginx, 2+ pods)
                    │      └── /api   ─► clinicflow-backend   (FastAPI, 2–6 pods, HPA on CPU)
                    │                          └──► clinicflow-postgres (StatefulSet + gp3 EBS PVC)
                    ├── metrics-server ─► HPA
                    └── kube-prometheus-stack
                           Prometheus ◄─ ServiceMonitor scrapes backend /metrics
                           Grafana    ◄─ "ClinicFlow · Service overview" dashboard (auto-provisioned)
```

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, responsive CSS; served by `nginx-unprivileged` |
| Backend | FastAPI, SQLAlchemy 2, Pydantic 2, Alembic, Uvicorn |
| Database | PostgreSQL 17 |
| Tests | Pytest (36 tests, in-memory SQLite), Vitest, Ruff |
| Containers | Multi-stage Dockerfiles, non-root, Docker Compose |
| CI/CD | GitHub Actions, GHCR, image tags = Git SHA |
| Security | Trivy (image CVEs, secrets, IaC misconfig), SARIF → GitHub Security tab, keyless OIDC deploys |
| Infrastructure | Terraform (AWS VPC + EKS + IAM), `terraform-aws-modules` |
| Kubernetes | Helm chart, Traefik Ingress, HPA, PDB, NetworkPolicy, Pod Security Admission |
| Observability | Prometheus Operator, Grafana, PrometheusRule alerts |

---

## Repository layout

```text
.
├── backend/                 FastAPI app
│   ├── app/                 main.py, models, schemas, routers/, services (booking rules), metrics, seed
│   ├── alembic/versions/    0001 doctors+patients, 0002 appointments
│   ├── tests/               conftest.py + 36 pytest tests
│   └── Dockerfile           multi-stage, non-root (uid 10001)
├── frontend/                React app (src/), nginx.conf.template, Dockerfile (Node build → Nginx runtime)
├── docker-compose.yml       postgres + backend + frontend
├── .github/workflows/       ci-cd.yml (test → scan → push → deploy)
├── terraform/               VPC, EKS, EBS CSI (Pod Identity), GitHub OIDC role, tfvars example
├── helm/clinicflow/         Helm chart (+ values-dev.yaml for kind, values-prod.yaml for EKS)
├── k8s/                     namespace, gp3 StorageClass, kind cluster config
├── monitoring/              kube-prometheus-stack, Traefik and metrics-server values
├── scripts/                 kind-up.sh, bootstrap-cluster.sh, load-test.sh
├── troubleshooting/         deliberately broken manifests for the live debugging lab
└── docs/                    SUBMISSION.md, AWS-DEPLOY.md, SECURITY.md, DEMO.md, screenshots/
```

---

## The application

### REST API

Interactive docs: `http://localhost:8000/docs` (Swagger) when running locally.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` (also `/api/health`) | Liveness: process is up (no DB call) |
| GET | `/ready` | Readiness: returns 503 until PostgreSQL answers |
| GET | `/metrics` | Prometheus metrics (HTTP + business counters) |
| GET / POST | `/api/doctors` | List (`?active=true`) / create doctors |
| GET / PUT / DELETE | `/api/doctors/{id}` | Read / update / delete (409 if the doctor has appointment history) |
| GET / POST | `/api/patients` | List (`?q=` search by name or phone) / register patients |
| GET / PUT / DELETE | `/api/patients/{id}` | Read / update / delete (cascades to their appointments) |
| GET / POST | `/api/appointments` | List (`?status=&doctor_id=&patient_id=&start=&end=`) / book |
| GET / PUT / DELETE | `/api/appointments/{id}` | Read / reschedule or change status / delete |
| GET | `/api/appointments/stats` | KPI numbers for the dashboard |

**Business rules enforced by the API** (all covered by tests):
- A booking that overlaps an existing one for the same doctor or patient returns **409 Conflict**. Back-to-back slots are fine, and cancelled/no-show appointments free their slot.
- Inactive doctors can't be booked. Doctors with history can't be deleted, only deactivated.
- Durations must be between 10 and 240 minutes; date of birth can't be in the future; phone and email are validated.

### Data model (Alembic-managed)

```text
doctors (id, full_name, specialty, email UNIQUE, phone, room, is_active, created_at)
patients (id, full_name, date_of_birth, gender, phone, email, notes, created_at)
appointments (id, patient_id → patients ON DELETE CASCADE, doctor_id → doctors ON DELETE RESTRICT,
              scheduled_at, duration_minutes CHECK 10–240, reason, status CHECK in (...), notes, created_at, updated_at)
```

Every backend container runs `alembic upgrade head` before starting. A **PostgreSQL advisory lock** (`backend/alembic/env.py`) makes replicas take turns, so two pods starting together can't race to create the same table.

### Frontend

A dashboard with KPI cards, today's schedule timeline, a status breakdown, and doctor workload. It also has an appointment table with status/doctor/date filters and one-click status transitions, a doctor directory, and a searchable patient register. The booking modal shows conflict errors, there are loading and backend-down states, and the sidebar shows the running **UI and API Git SHAs**, which makes it easy to show that a deploy happened. Below 680px, tables turn into stacked cards and the sidebar becomes an icon bar.

---

## Run it

### 1. Docker Compose (whole stack, one command)

```bash
docker compose up --build
```

| URL | What |
|---|---|
| http://localhost:3000 | ClinicFlow UI (demo data is seeded automatically) |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/metrics | Prometheus metrics |

Postgres is published on host port **5433**, so it doesn't clash with a local Postgres. Run `docker compose down -v` to also delete the database volume.

### 2. Backend directly (development)

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
docker compose up -d postgres                 # or any PostgreSQL
export DATABASE_URL='postgresql+psycopg://clinicflow:clinicflow@localhost:5433/clinicflow'
export SEED_DEMO_DATA=true
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# frontend, in another terminal (Vite proxies /api to :8000)
cd frontend && npm ci && npm run dev           # http://localhost:5173
```

### 3. Tests

```bash
cd backend && pytest -v          # 36 tests; each gets a fresh in-memory SQLite DB, never Postgres
cd frontend && npm test          # Vitest unit tests for date/format helpers
```

### 4. Kubernetes on your laptop (kind)

This rehearses the exact EKS deployment: a 3-node cluster with Traefik, metrics-server, Prometheus and Grafana.

```bash
./scripts/kind-up.sh             # then open http://clinicflow.localhost
./scripts/load-test.sh           # watch: kubectl get hpa -n clinicflow -w
kind delete cluster --name clinicflow
```

### 5. AWS (Terraform + EKS + CI/CD deploys)

See **[docs/AWS-DEPLOY.md](docs/AWS-DEPLOY.md)** for the step-by-step runbook (≈ 20 minutes, roughly $0.30/hour while running). The short version:

```bash
cd terraform && cp terraform.tfvars.example terraform.tfvars
terraform init && terraform plan -out tfplan && terraform apply tfplan
aws eks update-kubeconfig --region ap-south-1 --name clinicflow-eks
../scripts/bootstrap-cluster.sh eks
# set AWS_DEPLOY_ROLE_ARN / AWS_REGION / EKS_CLUSTER_NAME repo variables, then push to main
terraform destroy                # when finished
```

---

## CI/CD pipeline

`.github/workflows/ci-cd.yml` runs on every push and pull request to `main`:

1. **Test**: backend lint (`ruff`) and `pytest` with coverage, frontend `vitest` and `vite build`, `helm lint`, `terraform validate`, and a Trivy **secret scan** of the repository. If any of these fail, nothing below runs.
2. **Build → scan → push** (matrix: backend, frontend): Buildx builds the image, Trivy writes a full report as SARIF to the GitHub Security tab, then a **Trivy gate fails the job on any fixable HIGH/CRITICAL CVE**. Only after that does the *same scanned image* get pushed to `ghcr.io/<owner>/clinicflow-<component>:<full-git-sha>`. Pull requests build and scan but never push.
3. **Deploy** (main only, once the cluster exists): GitHub OIDC assumes an IAM role (no AWS keys stored anywhere), then `helm upgrade --install --wait --rollback-on-failure` with the new SHA, followed by a rollout check.

A failed Helm upgrade rolls itself back, so production stays on the last good release.

## Security highlights

- Both images run as **non-root** (backend uid 10001, frontend nginx uid 101 on port 8080). In Kubernetes they also get read-only root filesystems, dropped capabilities and `seccomp: RuntimeDefault`.
- pip is removed from the runtime image, which eliminated four HIGH CVEs in libraries pip vendors (see [docs/SECURITY.md](docs/SECURITY.md)).
- trivy-action is pinned to a commit SHA because its tags were hijacked in a March 2026 supply-chain attack.
- The Postgres password is generated by Helm and kept in a Secret, and only backend pods may reach Postgres (NetworkPolicy).
- No credentials live in Git: `.env` and `terraform.tfvars` are git-ignored, and CI deploys through short-lived OIDC credentials.

## Observability

- `/metrics` exposes `http_requests_total`, `http_request_duration_seconds` and ClinicFlow business counters (`clinicflow_appointments_booked_total{specialty}`, `clinicflow_booking_conflicts_total{kind}`, `clinicflow_appointment_status_changes_total{status}`).
- A **ServiceMonitor** tells Prometheus to scrape every backend pod. A **PrometheusRule** alerts on backend down, more than 5% 5xx responses, and p95 latency above 1s.
- The Grafana dashboard **ClinicFlow · Service overview** is provisioned from a ConfigMap. It shows request rate, error rate, latency percentiles, per-pod load balancing, bookings per specialty, blocked double-bookings, CPU vs. request, and HPA replicas.

![Grafana dashboard](docs/screenshots/10-grafana-dashboard.png)

## Troubleshooting lab

| Manifest | Symptom | Lesson |
|---|---|---|
| `troubleshooting/broken-image.yaml` | `ErrImagePull` → `ImagePullBackOff` | read `kubectl describe pod` Events |
| `troubleshooting/broken-service.yaml` | Service has a ClusterIP but no endpoints | Services find Pods only through labels |
| `troubleshooting/crashloop-bad-db.yaml` | pod never becomes Ready / restarts | liveness vs. readiness; read `kubectl logs` |

Each file's header comments list the investigation commands and the fix.

## Design decisions worth explaining

- **Why Traefik and not ingress-nginx?** The Kubernetes ingress-nginx project was retired in March 2026. Traefik implements the same standard `Ingress` resource, so the chart's Ingress is portable.
- **Postgres in the cluster vs. Amazon RDS:** in-cluster Postgres (StatefulSet + EBS) keeps the classroom setup self-contained and cheap. For real patient data, RDS gives automated backups, Multi-AZ failover and patching. The chart supports it with `postgres.enabled=false` and `externalDatabase.host=<rds-endpoint>`.
- **Why `/health` and `/ready` differ:** liveness must not depend on the DB. Otherwise a database blip would make Kubernetes restart every API pod at once. Readiness does check the DB, so traffic only reaches pods that can serve it.
- **Image tags are Git SHAs:** `kubectl get pods -o wide` and the UI footer show which commit is running; rollback means redeploying an older SHA.

---

Submission evidence (rubric → files → screenshots) is in **[docs/SUBMISSION.md](docs/SUBMISSION.md)**. The live demo script is in **[docs/DEMO.md](docs/DEMO.md)**.
