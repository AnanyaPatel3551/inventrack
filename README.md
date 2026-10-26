# InvenTrack – Inventory Management

**DevOps Final Capstone (Session 21)**
**Name:** Ananya Patel  **Roll no:** 24bcs10019
**GitHub:** [AnanyaPatel3551/inventrack](https://github.com/AnanyaPatel3551/inventrack)
**Images:** `ghcr.io/ananyapatel3551/inventrack-backend`, `ghcr.io/ananyapatel3551/inventrack-frontend`

**Presentation_Video:**`https://drive.google.com/file/d/1XYYvMJOZYt3n2_AyT2WbUlIR_0o-c4eT/view?usp=sharing`

---

## 1. What the app does

InvenTrack is a small inventory management web app. I built it to have a real application to take through the full DevOps pipeline, from my laptop to a monitored Kubernetes cluster.

With InvenTrack you can:

- add products with a name, unique SKU, category, quantity, price and supplier
- see every product in a table and filter by stock status
- change a product's status between **In stock**, **Low stock** and **Out of stock** with one click
- delete products
- see KPI cards with the total number of products and how many are in / low / out of stock
- see a "Needs attention" list of products that are low or out of stock

The UI is a dark-sidebar dashboard that also works on a phone screen.

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List all products |
| GET | `/api/products/{id}` | Get one product (404 if missing) |
| POST | `/api/products` | Create a product (409 if the SKU already exists, 422 on invalid data) |
| PUT | `/api/products/{id}` | Update any fields of a product |
| DELETE | `/api/products/{id}` | Delete a product |
| GET | `/api/products/stats` | Counts: `total`, `inStock`, `lowStock`, `outOfStock` |
| GET | `/health` | Liveness check – the process is up |
| GET | `/ready` | Readiness check – the database is reachable |
| GET | `/metrics` | Prometheus metrics |

Swagger docs are at `/docs` when the backend is running.

---

## 2. Architecture

```text
                Developer (git push)
                        |
                        v
                 GitHub repository
                        |
                        v
     GitHub Actions  ───────────────────────────────────────────
     | test:   pytest -v, npm run build                         |
     | build-scan-push: docker build -> Trivy scan -> push      |
      ──────────────────────────┬───────────────────────────────
                                v
              GitHub Container Registry (GHCR)
        inventrack-backend:<sha>   inventrack-frontend:<sha>
                                |
                                v  helm upgrade --install
   ┌─────────────────────── minikube (namespace: inventrack) ───────────────────────┐
   │                                                                                 │
   │   Browser ──> Ingress (nginx)  host: inventrack.local                           │
   │                 |                         |                                     │
   │                 | /                       | /api                                │
   │                 v                         v                                     │
   │     inventrack-frontend (x2)     inventrack-backend (x2..6, HPA on CPU)         │
   │     React build on nginx         FastAPI + SQLAlchemy                           │
   │     non-root, port 8080          non-root, port 8000                            │
   │                                           |                                     │
   │                                           v                                     │
   │                              inventrack-postgres (PVC)                          │
   │                                                                                 │
   └──────────────────────────────────────────┬──────────────────────────────────────┘
                                              | /metrics (ServiceMonitor)
                                              v
                namespace: monitoring – Prometheus ──> Grafana dashboard

   Terraform (terraform/): AWS VPC + EKS defined as code (validated, not applied – see section 9)
```

---

## 3. Tech stack

| Layer | Tools |
|-------|-------|
| Frontend | React 19, Vite 8, plain CSS (responsive) |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.1, Pydantic |
| Database | PostgreSQL 16, Alembic migrations |
| Testing | pytest (10 tests, SQLite test database) |
| Containers | Docker (multi-stage frontend build, non-root images), Docker Compose |
| CI/CD | GitHub Actions |
| Security | Trivy image scanning |
| Registry | GitHub Container Registry (GHCR) |
| Infrastructure as Code | Terraform – AWS VPC + EKS modules |
| Kubernetes | minikube, Helm chart, nginx Ingress, HPA |
| Monitoring | kube-prometheus-stack (Prometheus + Grafana), prometheus-fastapi-instrumentator |

### Repository layout

```text
inventrack/
├── backend/                 FastAPI app, Alembic migrations, pytest tests, Dockerfile
├── frontend/                React app, nginx config template, Dockerfile
├── docker-compose.yml       postgres + backend + frontend for local runs
├── .github/workflows/       CI/CD pipeline
├── terraform/               AWS VPC + EKS (see terraform/README.md)
├── k8s/namespace.yaml       inventrack namespace
├── helm/inventrack/         Helm chart (values-dev.yaml for minikube)
├── monitoring/              Prometheus/Grafana values and the Grafana dashboard
├── scripts/load-test.sh     parallel requests to trigger the HPA
├── troubleshooting/         broken manifests and their fixes
└── screenshots/             evidence for each phase
```

---

## 4. Running it locally (without Docker)

**Backend** (needs Python 3.12+ and a PostgreSQL database):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

export DATABASE_URL='postgresql+psycopg://inventrack:inventrack@localhost:5432/inventrack'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Then open http://localhost:8000/docs.

**Frontend** (needs Node 22):

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173. The Vite dev server forwards `/api` calls to the backend on port 8000.

### Tests

```bash
cd backend
pytest -v
```

The tests use a temporary SQLite file (`test.db`) instead of PostgreSQL, so they don't need a database server. `tests/conftest.py` sets `DATABASE_URL` before the app is imported and starts one `TestClient` for the whole session. There are 10 tests covering health, root, ready, create, validation (empty name → 422, duplicate SKU → 409), list/get/404, update + stats, delete and `/metrics`.

---

## 5. Running it with Docker Compose

```bash
docker compose up --build
```

| URL | What |
|-----|------|
| http://localhost:3000 | InvenTrack UI |
| http://localhost:8000/docs | Swagger |
| http://localhost:8000/metrics | Prometheus metrics |

Things I set up in the Docker part:

- **Backend image:** `python:3.12-slim`, runs as user `10001`, and runs `alembic upgrade head` before starting Uvicorn.
- **Frontend image:** multi-stage. Node builds the React app, and the final image is `nginx-unprivileged`, which runs as user `101` on port 8080 (Compose maps `3000 → 8080`).
- **nginx config:** it's a template (`default.conf.template`). The backend address comes from the `BACKEND_URL` environment variable, so the same image works in Compose (`http://backend:8000`) and in Kubernetes.
- **Postgres healthcheck:** Postgres has a `pg_isready` healthcheck and the backend waits for `service_healthy`. Without this the backend started before Postgres was ready and crashed.

Stop with `docker compose down` (add `-v` to delete the database volume).

> If port 5432 is already used on your machine, change the postgres port mapping to `"5433:5432"`. The backend talks to Postgres over the Compose network, so only tools on the host are affected.

---

## 6. CI/CD with GitHub Actions

File: `.github/workflows/ci-cd.yml`. It runs on every push and pull request to `main`.

```text
test  ──>  build-scan-push
```

**test job**
1. set up Python 3.12, `pip install -r requirements.txt`
2. `pytest -v` – if any test fails, the pipeline stops here
3. set up Node 22, `npm install && npm run build`

**build-scan-push job** (only runs if `test` passed)
1. lowercase the GitHub owner name (GHCR image names must be lowercase)
2. build `ghcr.io/ananyapatel3551/inventrack-backend:<commit sha>` and `...-frontend:<commit sha>`
3. scan both images with Trivy (HIGH and CRITICAL, fail the job if something is found)
4. log in to GHCR and push both images – **only on push events**, so pull requests are tested and scanned but never published

Every image is tagged with the Git commit SHA instead of `latest`, so I can always tell exactly which commit is running.

All dependency versions are pinned in `requirements.txt` and `package.json` (plus `package-lock.json`), and the Trivy action is pinned to a full commit SHA instead of a tag.

---

## 7. Security scanning with Trivy

Trivy scans each container image for known vulnerabilities in its operating-system packages (Debian for the backend, Alpine for the frontend) and in the language packages inside it, such as the Python libraries installed in the backend image. In my pipeline it reports only HIGH and CRITICAL vulnerabilities that already have a fixed version available, and it fails the build if it finds any. A clean result means no known, fixable HIGH or CRITICAL CVEs at the time of the scan – it does not mean the image is secure forever, which is why the scan runs on every push.

When I first added the scan, the frontend failed with 41 fixable HIGH/CRITICAL CVEs (mostly OpenSSL) because `nginx-unprivileged:1.27-alpine` was built on an old Alpine release. Moving to `nginx-unprivileged:1.30.6-alpine` brought it to 0.

---

## 8. Kubernetes on minikube with Helm

The Helm chart is in `helm/inventrack/`. With release name `inventrack` it creates:

| Resource | Name | Notes |
|----------|------|-------|
| Deployment + Service | `inventrack-backend` | 2 replicas (HPA min 2, max 6), port `http` 8000, probes on `/ready` and `/health` |
| Deployment + Service | `inventrack-frontend` | 2 replicas, port `http` 8080 |
| Deployment + Service + PVC | `inventrack-postgres` | 5Gi volume |
| Secret | `inventrack-db` | Postgres user/password and `DATABASE_URL` |
| ConfigMap | `inventrack-config` | `BACKEND_URL` for the frontend nginx |
| Ingress | `inventrack` | `inventrack.local`: `/api` → backend:8000, `/` → frontend:8080 |
| HPA | `inventrack-backend` | scales on 60% CPU |
| ServiceMonitor | `inventrack-backend` | only created when the Prometheus Operator is installed |

### Steps

```bash
minikube start --cpus 4 --memory 8192
minikube addons enable ingress
minikube addons enable metrics-server

kubectl apply -f k8s/namespace.yaml

# use a commit whose pipeline pushed images to GHCR
SHA=$(git rev-parse HEAD)

helm upgrade --install inventrack ./helm/inventrack \
  -n inventrack \
  -f helm/inventrack/values-dev.yaml \
  --set backend.image.tag=$SHA \
  --set frontend.image.tag=$SHA

kubectl get pods,svc -n inventrack
helm list -n inventrack
```

To open the app through the Ingress:

1. Run `minikube tunnel` in a separate terminal and leave it open.
2. Add this line to the hosts file (`C:\Windows\System32\drivers\etc\hosts` on Windows, `/etc/hosts` on Linux/macOS):
   ```text
   127.0.0.1 inventrack.local
   ```
3. Open http://inventrack.local.

My GHCR packages are public, so minikube can pull the images without a pull secret.

### Autoscaling (HPA)

```bash
kubectl get hpa -n inventrack -w                 # terminal 1
CONCURRENCY=50 ./scripts/load-test.sh            # terminal 2
```

`load-test.sh` sends parallel requests to `http://inventrack.local/api/products` (2000 requests, 20 at a time by default; `TOTAL`, `CONCURRENCY` and `URL` can be changed). Each request queries the database, so the backend CPU goes up and the HPA adds pods. After the load stops, it scales back down to 2 after a few minutes.

---

## 9. Terraform (AWS VPC + EKS)

The `terraform/` folder defines the production-style AWS setup:

- **VPC** `inventrack-vpc` (10.20.0.0/16): 2 public and 2 private subnets in two availability zones, one NAT gateway, and the `kubernetes.io/role/elb` / `internal-elb` subnet tags
- **EKS** `inventrack-eks` (Kubernetes 1.36): a managed node group of `t3.medium` nodes, min 2 / max 4
- typed variables with descriptions, `default_tags` on every resource, and outputs including a ready-made `configure_kubectl` command
- `terraform.tfvars.example` with no credentials

```bash
cd terraform
terraform init
terraform fmt -check
terraform validate
```

> **Note:** I defined the EKS cluster in Terraform, but I did **not** run `terraform apply`, because I had no AWS budget for this project. An EKS control plane, two t3.medium nodes and a NAT gateway are charged by the hour. `terraform init`, `fmt` and `validate` all pass, and the code is ready to apply with an AWS account. To still show a working Kubernetes deployment, I ran the same Helm chart on **minikube** on my laptop.

More details are in [terraform/README.md](terraform/README.md).

---

## 10. Monitoring (Prometheus + Grafana)

The backend exposes Prometheus metrics at `/metrics` using `prometheus-fastapi-instrumentator` (request counts by route and status class, and a request-duration histogram).

```bash
helm install kube-prometheus-stack \
  oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml

kubectl apply -f monitoring/inventrack-dashboard.yaml

# run the app chart again so the ServiceMonitor gets created now that the CRD exists
helm upgrade --install inventrack ./helm/inventrack -n inventrack -f helm/inventrack/values-dev.yaml \
  --set backend.image.tag=$SHA --set frontend.image.tag=$SHA
```

- `monitoring/prometheus-values.yaml`: Grafana is enabled, the dashboard sidecar loads every ConfigMap labelled `grafana_dashboard: "1"`, and Prometheus picks up ServiceMonitors from all namespaces.
- `monitoring/inventrack-dashboard.yaml`: the **InvenTrack – Backend Overview** dashboard with four panels: request rate, p95 latency, 5xx error rate and pod count (including the HPA's desired replicas).

Open Prometheus and Grafana:

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
# http://localhost:9090/targets – inventrack-backend should be UP

kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80
# http://localhost:3001 – user admin, password:
kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 -d
```

---

## 11. Troubleshooting cases

Each case in `troubleshooting/` is a small Deployment + Service in the `inventrack` namespace with exactly one mistake. The corrected version is in `troubleshooting/fixes/`.

| Case | What is wrong | What I saw | How I found it | Fix |
|------|---------------|------------|----------------|-----|
| `broken-image.yaml` | image tag `1.30.66-alpine` does not exist | pods in `ErrImagePull` → `ImagePullBackOff` | `kubectl describe pod` → Events: image not found | correct tag `1.30.6-alpine` |
| `broken-service.yaml` | Service selector `app: inventrack-lab-website` does not match the pod label `app: inventrack-lab-web` | pods Running and Ready, but endpoints `<none>` | `kubectl get endpoints` and `kubectl get pods --show-labels` | fix the selector |
| `broken-readiness.yaml` | readiness probe calls `/healthz`, which returns 404 | pods Running but `0/1` Ready, 0 restarts, endpoints `<none>` | `kubectl describe pod` → `Readiness probe failed: ... statuscode: 404` | probe path `/` |

```bash
kubectl apply -f troubleshooting/broken-readiness.yaml
kubectl get pods,endpoints -n inventrack
kubectl describe pod -n inventrack -l scenario=broken-readiness
kubectl apply -f troubleshooting/fixes/broken-readiness.yaml

# clean up all labs
kubectl delete -f troubleshooting/fixes/
```

What I learned: all three cases end up with "the Service has no endpoints", but the cause is in a different place each time – the image, the labels, or the probe. `kubectl get pods` already tells them apart (no container / Ready / not Ready).

---

## 12. Screenshots

All screenshots are in [`screenshots/`](screenshots/), numbered in the order of the phases above.

| # | Phase | Screenshot |
|---|-------|------------|
| 01 | Git | [01-git-commit-history.png](screenshots/01-git-commit-history.png) – commit history |
| 02 | Testing | [02-pytest-passing.png](screenshots/02-pytest-passing.png) – `pytest -v`, all tests passing |
| 03 | Docker | [03-docker-compose-up.png](screenshots/03-docker-compose-up.png) – `docker compose up --build` with all three services |
| 04 | Application | [04-app-localhost.png](screenshots/04-app-localhost.png) – InvenTrack at http://localhost:3000 |
| 05 | API | [05-swagger-docs.png](screenshots/05-swagger-docs.png) – Swagger docs at `/docs` |
| 06 | CI/CD | [06-actions-workflow-runs.png](screenshots/06-actions-workflow-runs.png) – GitHub Actions workflow runs |
| 07 | CI/CD | [07-actions-pipeline-green.png](screenshots/07-actions-pipeline-green.png) – green pipeline: `test` → `build-scan-push` |
| 08 | Security | [08-trivy-scan.png](screenshots/08-trivy-scan.png) – Trivy scan output |
| 09 | Registry | [09-ghcr-packages.png](screenshots/09-ghcr-packages.png) – both packages in GHCR |
| 10 | Registry | [10-ghcr-image-tags.png](screenshots/10-ghcr-image-tags.png) – image versions tagged with commit SHAs |
| 11 | Terraform | [11-terraform-init-validate.png](screenshots/11-terraform-init-validate.png) – `terraform init`, `fmt` and `validate` |
| 12 | Kubernetes | [12-kubectl-get-pods.png](screenshots/12-kubectl-get-pods.png) – all pods Running |
| 13 | Kubernetes | [13-kubectl-get-svc.png](screenshots/13-kubectl-get-svc.png) – ClusterIP services |
| 14 | Helm | [14-helm-list.png](screenshots/14-helm-list.png) – `helm list -n inventrack` |
| 15 | Ingress | [15-app-via-ingress.png](screenshots/15-app-via-ingress.png) – app at http://inventrack.local |
| 16 | HPA | [16-hpa-scaling.png](screenshots/16-hpa-scaling.png) – HPA scaling under load |
| 17 | Monitoring | [17-metrics-endpoint.png](screenshots/17-metrics-endpoint.png) – `/metrics` output |
| 18 | Monitoring | [18-prometheus-targets.png](screenshots/18-prometheus-targets.png) – Prometheus target UP |
| 19 | Monitoring | [19-grafana-dashboard.png](screenshots/19-grafana-dashboard.png) – Grafana dashboard with live data |
| 20 | Troubleshooting | [20-troubleshoot-image-broken.png](screenshots/20-troubleshoot-image-broken.png) – ImagePullBackOff |
| 21 | Troubleshooting | [21-troubleshoot-image-fixed.png](screenshots/21-troubleshoot-image-fixed.png) – pods Running after the fix |
| 22 | Troubleshooting | [22-troubleshoot-service-broken.png](screenshots/22-troubleshoot-service-broken.png) – endpoints `<none>` |
| 23 | Troubleshooting | [23-troubleshoot-service-fixed.png](screenshots/23-troubleshoot-service-fixed.png) – endpoints filled |
| 24 | Troubleshooting | [24-troubleshoot-readiness-broken.png](screenshots/24-troubleshoot-readiness-broken.png) – pods 0/1 Ready |
| 25 | Troubleshooting | [25-troubleshoot-readiness-fixed.png](screenshots/25-troubleshoot-readiness-fixed.png) – pods 1/1 Ready |

---

## 13. Problems I ran into

- **Backend crashed on `docker compose up`.** `depends_on` only waits for the Postgres container to start, not for Postgres to accept connections. I added a `pg_isready` healthcheck and `condition: service_healthy`.
- **Port 5432 already in use** on my laptop, so the postgres container could not publish its port. The app itself does not need that port mapping because the services talk over the Compose network.
- **GHCR image names must be lowercase**, but my GitHub username has capital letters, so using `github.repository_owner` directly would make `docker build -t` fail. The pipeline lowercases the owner before tagging.
- **Trivy failed the frontend image** with 41 HIGH/CRITICAL CVEs from the old nginx base image. Updating to `nginx-unprivileged:1.30.6-alpine` fixed it.
- **The nginx config had `backend:8000` hard-coded.** That hostname only exists in Docker Compose, so in Kubernetes nginx would fail at startup. I changed it to read `BACKEND_URL`, which Helm sets from a ConfigMap.
