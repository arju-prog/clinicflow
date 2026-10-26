# ClinicFlow — Demo Video Script

**Format:** 4K (3840 × 2160) narrated walkthrough, about 8 minutes.
**Voice:** first person, conversational. Read it the way you'd explain the project to a friend who knows a bit of tech.
**Rule:** everything said here really happened in this project. The opening clinic scene is a scenario, and is framed as one ("Picture…").

Each scene lists what is on screen and what is said.

---

### 1 · Cold open
**On screen:** ClinicFlow dashboard, live.

> Picture a small clinic on a Monday morning. The phone is ringing, three patients are waiting at the desk, and the receptionist books two people into the same doctor’s ten-thirty slot. Nobody notices until both of them are sitting in the waiting room. That small, very real problem is where this project started.

### 2 · Title
**On screen:** Slide 1, title.

> I’m Arjun, and this is ClinicFlow, my DevOps final capstone. The app is a clinic front-desk system. But honestly, the app is only half the story. The other half is the journey: how a change I make on my laptop ends up running on a Kubernetes cluster in AWS, tested, scanned, autoscaling and monitored, without me logging into a single server.

### 3 · What the app does
**On screen:** Slide 2, then the live dashboard and the booking form.

> Let me show you the app first. This is what the receptionist sees: today’s appointments, who has checked in, and how busy each doctor is. Booking is a simple form. Pick a patient, pick a doctor, pick a time.

### 4 · The double-booking guard
**On screen:** Live: a second booking into the same slot, the red conflict message, then the phone layout.

> Now here’s the part I care about. If I try to book the same doctor into a slot that’s already taken, the backend refuses. It returns a 409 conflict, and the receptionist sees exactly which appointment is in the way. The same rule protects patients, so nobody can be in two rooms at once. And because front desks use whatever device is nearby, it works on a phone too.

### 5 · The route every change takes
**On screen:** Slide 3, the thirteen stages.

> So that’s the what. Now the how. This is the route every change takes: thirteen stages, from the app itself all the way to troubleshooting it in production. I’ll walk through them in order, and I’ll stick to what actually happened, including the things that broke.

### 6 · Stage 1, the application
**On screen:** Slide 4.

> Stage one is the application. A FastAPI backend with full create, read, update and delete for doctors, patients and appointments, on PostgreSQL. The schema is managed with Alembic migrations, so the database structure lives in Git like everything else. There are two health endpoints, and they do different jobs. Health only answers, “is the process alive?” Ready also checks the database. That difference matters later, because Kubernetes only sends traffic to pods that are ready.

### 7 · Stage 2, Git
**On screen:** Slide 5, then the real `git log`.

> Stage two is Git. Every change is a commit with a message that says what it does, and there are more than twenty of them in this repository. The gitignore keeps secrets, environment files and caches out of the history, because once a secret is in Git, you should treat it as public.

### 8 · Stage 3, the CI pipeline
**On screen:** Slide 6, the green GitHub Actions run, then `pytest -v`.

> Stage three is the pipeline, in GitHub Actions. The moment I push to main, it runs the linter and thirty-six automated tests. This is the first gate. If a single test fails, nothing gets built and nothing gets deployed. A broken commit simply stops here.

### 9 · Stage 4, Docker
**On screen:** Slide 7, then `docker compose up --build`.

> Stage four is Docker. The frontend and the backend are each packaged as an image. The frontend uses a multi-stage build: Node compiles the React app, and only the finished files are copied into a small Nginx image. Both containers run as a non-root user. And for local work, one command, docker compose up, brings up the frontend, the backend and Postgres together.

### 10 · Stage 5, security
**On screen:** Slide 8, then the Trivy gate output from CI.

> Stage five is security, and this is my favourite part of the story. The pipeline scans every image with Trivy and fails the build on any serious vulnerability that has a fix. The first time I ran it, it failed. Four high-severity CVEs, in urllib3, msgpack and setuptools. The strange thing was, my app doesn’t use any of them. They came bundled inside pip, which is only needed while the image is being built. So instead of patching them, I removed pip from the final image, and all four findings disappeared. Sometimes the best fix is deleting something.

### 11 · Stage 6, the registry
**On screen:** Slide 9, then the GHCR package page.

> Stage six is the registry. Once the scan passes, the exact image that was scanned is pushed to GitHub’s container registry. It’s tagged with the Git commit hash, never “latest”. That means any running container traces back to the exact code that produced it, and rolling back is just deploying an older hash.

### 12 · Stage 7, Terraform
**On screen:** Slide 10, the AWS Console (VPC, subnets, EKS cluster), then the destroy result.

> Stage seven is Terraform. Instead of clicking around the AWS console, the infrastructure is code: a VPC with public and private subnets across two availability zones, a NAT gateway, an EKS cluster with two worker nodes in the Mumbai region, and an IAM role that lets GitHub deploy without any stored AWS keys. My AWS account is on the free plan, which blocked the usual instance type, so I switched the nodes to one that’s free-tier eligible. And when I was done, terraform destroy removed all sixty-five resources. A real cluster costs money every hour, so tearing it down is part of the job.

### 13 · Stage 8, Kubernetes
**On screen:** Slide 11, then `kubectl get pods` from EKS.

> Stage eight is Kubernetes. Here’s the app running on EKS: two backend pods, two frontend pods, and Postgres with its own storage volume, spread across both nodes. If a pod dies, its deployment replaces it, and services give the pods a stable address, so it doesn’t matter which one answers.

### 14 · Stage 9, Helm
**On screen:** Slide 12, then `helm list`.

> Stage nine is Helm. Rather than hand-editing a pile of YAML files, the whole deployment is one chart: deployments, services, ingress, the autoscaler, a network policy and monitoring. The pipeline runs one helm upgrade with the new commit’s tag, and if the new pods never become healthy, it rolls back on its own.

### 15 · Stage 10, Ingress
**On screen:** Slide 13, then the app served through the ingress on EKS.

> Stage ten is the ingress. One entry point, two routes: the root path goes to the React frontend, and slash-api goes to FastAPI. I used Traefik as the ingress controller, because the old ingress-nginx project was retired this year. One honest caveat: the AWS free plan also blocks public load balancers, so for this demo I reached the ingress through a port-forward. The routing is exactly the same.

### 16 · Stage 11, autoscaling
**On screen:** Slide 14, then the recorded HPA output.

> Stage eleven is autoscaling, and here I wanted proof, not just configuration. So I ran a load generator inside the cluster. CPU on the backend climbed to more than three times what each pod had requested, and the horizontal pod autoscaler responded: two pods, then three, four, five, six, in about ninety seconds.

### 17 · Stage 12, monitoring
**On screen:** Slide 15, Prometheus targets, the Grafana dashboard.

> Stage twelve is monitoring. The backend exposes Prometheus metrics, including a couple I added myself, like how many double-bookings were blocked. Prometheus scraped all six pods during that test, and every target was up. Grafana showed it live: around three hundred and ninety requests a second, zero errors, and a ninety-fifth percentile latency of about ninety-five milliseconds.

### 18 · Stage 13, troubleshooting
**On screen:** Slide 16.

> Stage thirteen is troubleshooting, because things will break. I wrote three deliberately broken setups. A wrong image tag, which shows up as an image pull back-off. A service whose label selector has a typo, so it has no endpoints and quietly drops every request. And a wrong database password, which leaves a pod stuck in a crash loop. Each one is a small lesson in reading the events, the endpoints and the logs before guessing.

### 19 · What I learned
**On screen:** Slide 17.

> Looking back, the most useful moments weren’t the ones that worked first time. Pinning the Trivy action to an exact commit, after its version tags were hijacked earlier this year. Working around the limits of the AWS free plan. Figuring out why GitHub’s new identity tokens didn’t match my AWS trust policy. That’s the part that felt like real engineering.

### 20 · Close
**On screen:** Slide 18.

> So that’s ClinicFlow. One commit sets off tests, a security scan, an image build, a registry push and a Helm deploy to a cluster that scales itself and reports on its own health. Every running pod traces back to a commit. Thanks for watching.
