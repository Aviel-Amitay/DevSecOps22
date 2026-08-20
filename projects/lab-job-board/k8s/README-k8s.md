# DevSecOps Lab — Kubernetes Extension

> **Difficulty:** Hard  
> **Total Points:** 100  
> **Estimated Time:** 6–10 hours  
> **Prerequisite:** Complete the Docker Compose lab (Part 1) first

---

## Overview

In this lab you migrate the Job Board application from Docker Compose to **production-grade Kubernetes**. You will work with Deployments, Services, PersistentVolumeClaims, Secrets, ConfigMaps, Ingress, HorizontalPodAutoscalers, and Kubernetes Jobs.

All Kubernetes manifests are provided in the `k8s/` directory. Your job is to **deploy, verify, extend, and troubleshoot** them — not to write them from scratch.

---

## Architecture on Kubernetes

```
  External Traffic
       │ :80
       ▼
  ┌─────────────────────────────────────────────────────────┐
  │            NGINX Ingress Controller (Pod)               │
  │  /api/jobs(/|$)(.*)      → jobs-service:8000            │
  │  /api/applications(/|$)(.*) → applications-service:3001 │
  │  /                       → frontend:80                  │
  └────────────┬──────────────────┬─────────────────────────┘
               │                  │
  ┌────────────▼───┐   ┌──────────▼───────────┐
  │  jobs-service  │   │ applications-service  │
  │  Deployment    │   │  Deployment           │
  │  replicas: 2   │   │  replicas: 2          │
  │  HPA: 2-6      │   │  HPA: 2-6             │
  └────────┬───────┘   └────────────┬──────────┘
           │                        │
  ┌────────▼────────────────────────▼──────────┐
  │              postgres Service               │
  │              (ClusterIP :5432)              │
  └────────────────────┬───────────────────────┘
                       │
              ┌────────▼────────┐
              │ postgres Pod     │
              │ Deployment       │
              │ PVC: 1Gi         │
              └─────────────────┘
```

### Kubernetes Objects Summary

| Object | Name | Kind |
|--------|------|------|
| Namespace | `jobboard` | Namespace |
| DB credentials | `postgres-secret` | Secret |
| Database storage | `postgres-pvc` | PersistentVolumeClaim |
| Database | `postgres` | Deployment + Service |
| Jobs API | `jobs-service` | Deployment + Service |
| Applications API | `applications-service` | Deployment + Service |
| React UI | `frontend` | Deployment + Service |
| API routing | `jobs-ingress`, `applications-ingress`, `frontend-ingress` | Ingress ×3 |
| Autoscaling | `jobs-service-hpa`, `applications-service-hpa` | HorizontalPodAutoscaler ×2 |
| Seed data | `seed-database` | Job |

---

## Prerequisites

| Tool | Min Version | Install |
|------|-------------|---------|
| `minikube` | 1.33 | [minikube.sigs.k8s.io](https://minikube.sigs.k8s.io/docs/start/) |
| `kubectl` | 1.29 | [kubernetes.io/docs](https://kubernetes.io/docs/tasks/tools/) |
| `Docker` | 24 | Already installed from Part 1 |
| `helm` | 3.14 (optional) | [helm.sh](https://helm.sh/docs/intro/install/) |

Verify:
```bash
minikube version
kubectl version --client
docker version
```

---

## Setup — Step by Step

### Step 1 — Start minikube

```bash
minikube start \
  --cpus=4 \
  --memory=4096 \
  --driver=docker \
  --addons=ingress,metrics-server

# Verify addons are enabled
minikube addons list | grep -E "ingress|metrics-server"
```

Wait until the ingress controller is ready:
```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

### Step 2 — Build images inside minikube's Docker daemon

This avoids pushing to a registry:
```bash
# Point your shell's Docker to minikube's daemon
eval $(minikube docker-env)

# Build all images (from the repo root)
docker build -t jobs-service:latest         ./jobs-service
docker build -t applications-service:latest ./applications-service
docker build -t frontend:latest             ./frontend

# Verify images are visible inside minikube
docker images | grep -E "jobs-service|applications-service|frontend"
```

> **Important:** Every new terminal needs `eval $(minikube docker-env)` to target minikube's daemon.

### Step 3 — Create the Kubernetes Secret

```bash
# Copy the template
cp k8s/01-secret.yaml.example k8s/01-secret.yaml

# Generate a strong password and base64-encode it
PASS=$(openssl rand -base64 20)
echo "Password: $PASS"
PASS_B64=$(echo -n "$PASS" | base64)

# Patch the secret file
sed -i "s|REPLACE_WITH_BASE64_ENCODED_PASSWORD|$PASS_B64|" k8s/01-secret.yaml

# Verify it looks correct (should NOT be the placeholder)
grep POSTGRES_PASSWORD k8s/01-secret.yaml
```

> **Never commit `k8s/01-secret.yaml`** — it is already in `.gitignore`.

### Step 4 — Deploy everything

```bash
# Option A: Apply with Kustomize (recommended)
kubectl apply -k k8s/

# Option B: Apply files in order manually
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-secret.yaml
kubectl apply -f k8s/02-postgres.yaml
kubectl apply -f k8s/03-jobs-service.yaml
kubectl apply -f k8s/04-applications-service.yaml
kubectl apply -f k8s/05-frontend.yaml
kubectl apply -f k8s/06-ingress.yaml
kubectl apply -f k8s/07-hpa.yaml
```

### Step 5 — Wait for all pods to be ready

```bash
kubectl get pods -n jobboard -w
# Wait until all STATUS = Running and READY = N/N

# All at once:
kubectl wait --for=condition=ready pod \
  --selector=app.kubernetes.io/part-of=jobboard \
  -n jobboard \
  --timeout=180s
```

### Step 6 — Seed initial data

```bash
# Uncomment the seed job in kustomization.yaml, then:
kubectl apply -f k8s/08-seed-job.yaml

# Watch it run
kubectl logs -f job/seed-database -n jobboard
```

### Step 7 — Open the application

With Minikube's Docker driver, the address returned by `minikube ip` (commonly
`192.168.49.2`) may not be reachable directly from a macOS or Windows host.
Forward the ingress controller to a local port instead.

  - [Windows](#windows-powershell)
  - [MacOS](#macos)  

--- 
#### MacOS

In the first Terminal window, run this command and leave it running:

```bash
kubectl port-forward \
  -n ingress-nginx \
  service/ingress-nginx-controller \
  8081:80
```

Expected output:

```text
Forwarding from 127.0.0.1:8081 -> 80
Forwarding from [::1]:8081 -> 80
```

This confirms that `kubectl` is listening on local port `8081` and forwarding
traffic to port `80` of the Kubernetes ingress controller. Keep this Terminal
window open. Each time the browser or `curl` sends a request through the
forward, another message appears:

```text
Handling connection for 8081
```

Seeing this message confirms that a client connected through the Kubernetes
port-forward. Multiple messages are normal because a browser requests the HTML,
JavaScript, CSS, API data, and other resources separately.

In a second Terminal window, verify the API:

```bash
curl --max-time 10 -sS http://127.0.0.1:8081/api/jobs \
  | python3 -m json.tool \
  | head -20
```

`json.tool` is part of Python. It reads the JSON produced by `curl` from
standard input and formats it; it is not a file in this repository or in a
pod. Running `python3 -m json.tool` without input waits for input.

Open the application in a browser:

```bash
open http://127.0.0.1:8081
```

Verify that Kubernetes, rather than Docker Compose, owns the local port:

```bash
lsof -nP -iTCP:8081 -sTCP:LISTEN
```

The `COMMAND` column should show `kubectl`. Docker Compose can be ruled out by
checking its published ports:

```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}'
```

No Docker container should publish port `8081`.

#### Windows (PowerShell)

In the first PowerShell window, run this command and leave it running:

```powershell
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8081:80
```

In a second PowerShell window, verify the API. Use `curl.exe` because
Windows PowerShell may use `curl` as an alias for `Invoke-WebRequest`:

```powershell
curl.exe --max-time 10 -sS http://127.0.0.1:8081/api/jobs |
  python -m json.tool |
  Select-Object -First 20
```

Open the application in the default browser:

```powershell
Start-Process http://127.0.0.1:8081
```

Verify that `kubectl` owns port `8081`:

```powershell
$Connection = Get-NetTCPConnection -LocalPort 8081 -State Listen
Get-Process -Id $Connection.OwningProcess
```

The process name should be `kubectl`. The port-forward window also prints
`Handling connection for 8081` when the browser or `curl.exe` connects.

Check that Docker Compose does not publish port `8081`:

```powershell
docker ps --format 'table {{.Names}}\t{{.Ports}}'
docker compose ps
```

No Docker container should show a mapping such as `0.0.0.0:8081->80/tcp`.

If `Get-NetTCPConnection` is unavailable, use these commands instead:

```powershell
netstat -ano | findstr :8081
tasklist /FI "PID eq <PID_FROM_NETSTAT>"
```

The final column from `netstat` is the process ID. Replace
`<PID_FROM_NETSTAT>` with that number; `tasklist` should identify `kubectl.exe`.

#### Issue summary and resolution

The workloads were healthy, but the application initially failed in the
browser for two separate reasons:

1. The Minikube IP was not directly reachable from the macOS/Windows host when
   using the Docker driver. Requests to `http://$MINIKUBE_IP` therefore waited
   until they timed out. Forwarding ingress to `127.0.0.1:8081` provides a
   reachable local address.
2. The frontend called `/api/jobs/` with a trailing slash. FastAPI redirected
   `/jobs/` to `/jobs`, and that redirect escaped the `/api` ingress prefix.
   The request then reached the React catch-all and returned HTML instead of
   JSON. The frontend now calls `/api/jobs`, and the ingress rewrite rules keep
   requests under the correct API route.

Successful verification should return HTTP 200 and JSON:

```bash
curl -i --max-time 10 http://127.0.0.1:8081/api/jobs
curl -sS http://127.0.0.1:8081/api/applications \
  | python3 -m json.tool
kubectl get pods -n jobboard
```

If port `8081` is already occupied, find its owner before selecting another
local port. On macOS:

```bash
lsof -nP -iTCP:8081 -sTCP:LISTEN
```

On Windows PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8081 -State Listen
```

For example, `8082:80` exposes the same Kubernetes ingress at
`http://127.0.0.1:8082`; no manifest change is required.

---

## Lab Tasks

---

### Task 1 — Cluster Exploration (15 pts)

#### 1.1 — Inspect all objects (5 pts)

Run each command and include the output in your `SOLUTION-k8s.md`:

```bash
kubectl get all -n jobboard
kubectl get pvc -n jobboard
kubectl get ingress -n jobboard
kubectl get hpa -n jobboard
kubectl get secret -n jobboard
```

For each resource type, answer in `SOLUTION-k8s.md`:
- What is the **READY** ratio for each Deployment?
- What is the **CLUSTER-IP** of each Service?
- What storage class was assigned to `postgres-pvc`?

#### 1.2 — Describe a Pod (5 pts)

Pick any running `jobs-service` pod and describe it:

```bash
POD=$(kubectl get pods -n jobboard -l app=jobs-service -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod $POD -n jobboard
```

In `SOLUTION-k8s.md`, explain:
- What `initContainer` runs first and why?
- What do the `readinessProbe` and `livenessProbe` check?
- What is the difference between them? What happens if readiness fails vs liveness fails?

#### 1.3 — Exec into a pod (5 pts)

```bash
# Exec into the jobs-service pod
kubectl exec -it $POD -n jobboard -- sh

# Inside the container, verify the database connection:
python3 -c "
import os, urllib.request
resp = urllib.request.urlopen('http://localhost:8000/health')
print(resp.read().decode())
"

# Verify DNS resolution to postgres:
nslookup postgres
exit
```

In `SOLUTION-k8s.md`, explain:
- What is the full DNS name of the `postgres` service? (format: `<svc>.<ns>.svc.cluster.local`)
- Why can pods use the short name `postgres` instead of the FQDN?

---

### Task 2 — Kubernetes Networking & Ingress (20 pts)

#### 2.1 — Trace an Ingress request (8 pts)

In `SOLUTION-k8s.md`, draw the full request journey for:

```
POST http://<minikube-ip>/api/applications/
```

Show each hop:
1. Which Ingress resource matches?
2. What does the `rewrite-target` annotation transform the path to?
3. Which Service receives the request? On which port?
4. Which Pod is selected? How (label selector)?
5. What does the Node.js handler return?

Verify with:
```bash
MINIKUBE_IP=$(minikube ip)

# Check which ingress rules exist
kubectl get ingress -n jobboard -o wide

# Test the full path
curl -sv -X POST http://$MINIKUBE_IP/api/applications/ \
  -H "Content-Type: application/json" \
  -d '{"job_id":"job-001","applicant_name":"Test User","applicant_email":"test@lab.com"}' \
  2>&1 | grep -E "< HTTP|Location|{" 
```

#### 2.2 — Why three Ingress objects? (4 pts)

The API routes use two separate Ingress objects (`jobs-ingress` and `applications-ingress`) instead of one.

In `SOLUTION-k8s.md`:
- Explain the nginx ingress annotation `nginx.ingress.kubernetes.io/rewrite-target` and why you can only have one value per Ingress object.
- What would break if you put both paths in a single Ingress with one `rewrite-target`?
- What alternative architecture would allow a single Ingress? (Hint: think about URL path prefixes in the services themselves.)

#### 2.3 — NodePort vs ClusterIP vs LoadBalancer (4 pts)

All Services in this lab use `ClusterIP`. In `SOLUTION-k8s.md`, fill in this table:

| Type | Reachable from | Use case | Example in this lab |
|------|---------------|----------|---------------------|
| ClusterIP | ... | ... | ... |
| NodePort | ... | ... | ... |
| LoadBalancer | ... | ... | ... |
| Ingress | ... | ... | ... |

Then change the `frontend` Service type to `NodePort` and verify you can reach it directly:
```bash
kubectl patch svc frontend -n jobboard -p '{"spec":{"type":"NodePort"}}'
kubectl get svc frontend -n jobboard
minikube service frontend -n jobboard --url
```
Restore it to `ClusterIP` afterwards.

#### 2.4 — Network Policies (4 pts) *(Hard)*

Write a NetworkPolicy manifest (`k8s/09-network-policy.yaml`) that:
- **Allows** `jobs-service` pods to connect to `postgres` on port 5432
- **Allows** `applications-service` pods to connect to `postgres` on port 5432
- **Denies** all other ingress traffic to `postgres`

```yaml
# Starter template
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: postgres-network-policy
  namespace: jobboard
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
    - Ingress
  ingress:
    # TODO: complete this
```

Apply and verify:
```bash
kubectl apply -f k8s/09-network-policy.yaml

# This should FAIL (blocked by NetworkPolicy):
kubectl run test-block --rm -it --image=busybox -n jobboard -- \
  nc -zv postgres 5432

# This should SUCCEED (from jobs-service pod):
kubectl exec -it $POD -n jobboard -- \
  python3 -c "import socket; s=socket.create_connection(('postgres',5432)); print('Connected')"
```

> **Note:** NetworkPolicy enforcement requires a CNI plugin that supports it (Calico, Cilium, etc.). Minikube's default CNI may not enforce them. Document what you observe.

---

### Task 3 — Persistent Storage & Data Lifecycle (15 pts)

#### 3.1 — Inspect the PersistentVolumeClaim (5 pts)

```bash
kubectl describe pvc postgres-pvc -n jobboard
kubectl get pv
```

In `SOLUTION-k8s.md`:
- What is the `Reclaim Policy` of the bound PersistentVolume?
- What does `Retain` vs `Delete` mean for data when the PVC is deleted?
- What is the `Access Mode` and why can't postgres use `ReadWriteMany`?

#### 3.2 — Verify data persistence across pod restarts (5 pts)

```bash
# 1. Create a job via the API
MINIKUBE_IP=$(minikube ip)
curl -s -X POST http://$MINIKUBE_IP/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"title":"K8s Persistence Test","description":"This job must survive a pod restart","company":"Lab Inc","location":"Kubernetes"}' \
  | python3 -m json.tool

# 2. Delete the postgres pod (Deployment will recreate it)
kubectl delete pod -l app=postgres -n jobboard

# 3. Wait for the new pod to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n jobboard --timeout=60s

# 4. Verify the job still exists
curl -s http://$MINIKUBE_IP/api/jobs/ | python3 -m json.tool | grep "K8s Persistence"
```

Document the result and explain *why* the data survived (the role of the PVC and the Deployment's `Recreate` strategy).

#### 3.3 — Manual database backup from Kubernetes (5 pts)

Back up the PostgreSQL database from the running pod:

```bash
# Get the postgres pod name
PG_POD=$(kubectl get pods -n jobboard -l app=postgres -o jsonpath='{.items[0].metadata.name}')

# Run pg_dump inside the pod and save locally
kubectl exec -n jobboard $PG_POD -- \
  sh -c 'PGPASSWORD=$POSTGRES_PASSWORD pg_dump -U $POSTGRES_USER -d $POSTGRES_DB --no-owner' \
  > k8s-backup-$(date +%Y%m%d_%H%M%S).sql

# Verify the backup
head -30 k8s-backup-*.sql
wc -l k8s-backup-*.sql
```

In `SOLUTION-k8s.md`, write the **restore procedure** — the exact `kubectl exec` commands to restore this backup to a fresh postgres pod.

---

### Task 4 — Scaling & Rolling Updates (25 pts)

#### 4.1 — Manual scaling (5 pts)

```bash
# Scale jobs-service to 4 replicas
kubectl scale deployment jobs-service --replicas=4 -n jobboard

# Watch pods come up
kubectl get pods -n jobboard -l app=jobs-service -w

# Verify all 4 are ready
kubectl rollout status deployment/jobs-service -n jobboard
```

In `SOLUTION-k8s.md`:
- How does the Ingress distribute traffic across 4 replicas?
- What load-balancing algorithm does the nginx ingress use by default?
- Scale back to 2 replicas. What happens to in-flight requests?

#### 4.2 — Rolling update with zero downtime (10 pts)

Simulate an application update by changing the image tag:

```bash
# Re-build with a v2 tag (add a response header to verify)
eval $(minikube docker-env)
docker build -t jobs-service:v2 ./jobs-service

# Trigger a rolling update
kubectl set image deployment/jobs-service \
  jobs-service=jobs-service:v2 \
  -n jobboard

# Watch the rollout in real time
kubectl rollout status deployment/jobs-service -n jobboard -w

# While it rolls, continuously probe the API (run in another terminal):
while true; do
  curl -s http://$(minikube ip)/api/jobs/health | grep -oE '"status":"[^"]*"'
  sleep 0.5
done
```

You should see **zero downtime** — the health endpoint keeps responding throughout.

In `SOLUTION-k8s.md`:
- What does `maxSurge: 1, maxUnavailable: 0` mean?
- Draw a timeline of what happens during a rolling update for `replicas: 2, maxSurge: 1, maxUnavailable: 0`.
- How would you rollback if the new version was broken?

```bash
# Rollback command:
kubectl rollout undo deployment/jobs-service -n jobboard

# View rollout history:
kubectl rollout history deployment/jobs-service -n jobboard
```

#### 4.3 — HorizontalPodAutoscaler (10 pts)

```bash
# Verify the HPA is working
kubectl get hpa -n jobboard -w

# Generate load to trigger scale-up (run for 2 minutes)
kubectl run load-gen --rm -it --image=busybox -n jobboard -- \
  sh -c "while true; do wget -qO- http://jobs-service:8000/jobs > /dev/null; done"

# In another terminal, watch scaling happen
watch kubectl get pods -n jobboard -l app=jobs-service
```

In `SOLUTION-k8s.md`:
- What is the formula the HPA uses to calculate desired replicas?
- What is `stabilizationWindowSeconds` and why is it important for scale-down?
- What happens if `metrics-server` is not installed? How would you diagnose this?

```bash
# Diagnose HPA:
kubectl describe hpa jobs-service-hpa -n jobboard
kubectl top pods -n jobboard
```

---

### Task 5 — Secrets & ConfigMaps (10 pts)

#### 5.1 — Inspect the Secret (4 pts)

```bash
# View the secret (values are base64-encoded, not encrypted!)
kubectl get secret postgres-secret -n jobboard -o yaml

# Decode the password
kubectl get secret postgres-secret -n jobboard \
  -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
```

In `SOLUTION-k8s.md`:
- Kubernetes Secrets are base64-encoded, not encrypted. What does this mean for security?
- Name **two** production solutions that provide real secret encryption in Kubernetes:
  1. A Kubernetes-native solution
  2. An external secrets manager
- What is **Sealed Secrets** and how does it work?

#### 5.2 — Add a ConfigMap for app configuration (6 pts)

Create `k8s/10-configmap.yaml` that stores non-sensitive application configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: jobboard-config
  namespace: jobboard
data:
  LOG_LEVEL:    "info"
  MAX_JOBS:     "100"
  ALLOWED_ORIGINS: "http://localhost,http://jobboard.local"
```

Then patch `03-jobs-service.yaml` to consume it:
```yaml
envFrom:
  - configMapRef:
      name: jobboard-config
```

Apply and verify the env vars appear inside the pod:
```bash
kubectl exec -it $POD -n jobboard -- env | grep -E "LOG_LEVEL|MAX_JOBS"
```

In `SOLUTION-k8s.md`:
- What is the difference between `env` (individual key) and `envFrom` (all keys)?
- When would you use a ConfigMap vs a Secret?
- What happens to running pods when you update a ConfigMap? (Hint: it depends...)

---

### Task 6 — Kubernetes CI/CD Integration (15 pts)

#### 6.1 — Update the GitHub Actions pipeline (10 pts)

Add a new job to `.github/workflows/ci.yml` called `deploy-to-k8s` that:

1. Installs `kubectl` and sets up a `kubeconfig` from a GitHub Secret (`KUBECONFIG_BASE64`)
2. Builds and pushes images to Docker Hub (reuse the existing `push-to-registry` job)
3. Updates each Deployment with the new image tag using `kubectl set image`
4. Verifies the rollout with `kubectl rollout status`

```yaml
deploy-to-k8s:
  name: Deploy to Kubernetes
  runs-on: ubuntu-latest
  needs: push-to-registry
  if: github.ref == 'refs/heads/main'
  steps:
    - uses: actions/checkout@v4

    - name: Set up kubectl
      uses: azure/setup-kubectl@v3

    - name: Configure kubeconfig
      run: |
        echo "${{ secrets.KUBECONFIG_BASE64 }}" | base64 -d > kubeconfig.yml
        export KUBECONFIG=kubeconfig.yml

    - name: Update jobs-service image
      run: |
        export KUBECONFIG=kubeconfig.yml
        kubectl set image deployment/jobs-service \
          jobs-service=${{ secrets.DOCKERHUB_USERNAME }}/jobboard-jobs:${{ github.sha }} \
          -n jobboard
        kubectl rollout status deployment/jobs-service -n jobboard --timeout=120s

    # TODO: add similar steps for applications-service and frontend
```

#### 6.2 — Add a Kubernetes smoke test step (5 pts)

After deployment, add a step that:
- Calls `kubectl get pods -n jobboard` and fails if any pod is not Running
- Calls the `/health` endpoints of both API services and fails if they return non-200

Document in `SOLUTION-k8s.md` how you would set up the `KUBECONFIG_BASE64` secret for a real cluster (e.g., from a cloud provider or self-hosted K8s).

---

## Quick Reference Commands

```bash
# ── Status ─────────────────────────────────────────────────
kubectl get all -n jobboard
kubectl get events -n jobboard --sort-by=.lastTimestamp
kubectl top pods -n jobboard

# ── Logs ───────────────────────────────────────────────────
kubectl logs -f deployment/jobs-service -n jobboard
kubectl logs -f deployment/applications-service -n jobboard
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f

# ── Debug ──────────────────────────────────────────────────
kubectl describe pod <pod-name> -n jobboard
kubectl exec -it <pod-name> -n jobboard -- sh
kubectl port-forward svc/jobs-service 8000:8000 -n jobboard

# ── Scaling ────────────────────────────────────────────────
kubectl scale deployment jobs-service --replicas=4 -n jobboard
kubectl rollout restart deployment/jobs-service -n jobboard

# ── Cleanup ────────────────────────────────────────────────
kubectl delete -k k8s/           # delete everything (keeps PVC data)
kubectl delete pvc postgres-pvc -n jobboard  # WARNING: deletes data
minikube stop
minikube delete
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Pod stuck in `Pending` | No nodes with enough resources | `kubectl describe pod <name>` → Events |
| Pod stuck in `Init:0/1` | `wait-for-postgres` initContainer | Postgres not ready; check `kubectl logs <pod> -c wait-for-postgres` |
| `ImagePullBackOff` | Image not found in minikube | Re-run `eval $(minikube docker-env)` then rebuild |
| `CrashLoopBackOff` | App crashes on startup | `kubectl logs <pod> --previous` |
| Ingress returns 404 | Wrong path / missing rewrite | Check `kubectl describe ingress -n jobboard` |
| Ingress returns 503 | Upstream pod not ready | Check readiness probe: `kubectl get endpoints -n jobboard` |
| Request to `$MINIKUBE_IP` waits or times out on macOS/Windows | Minikube Docker-driver IP is not directly reachable | Port-forward ingress: `kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8081:80` |
| `json.tool` reports `Expecting value` | The response was empty or HTML instead of JSON | Inspect it first with `curl -i --max-time 10 http://127.0.0.1:8081/api/jobs` |
| Port-forward reports `address already in use` | Another process owns the selected local port | Check with `lsof` (macOS) or `Get-NetTCPConnection` (Windows), or use another port such as `8082:80` |
| HPA shows `<unknown>` CPU | metrics-server not running | `minikube addons enable metrics-server` |
| Secret decode error | Wrong base64 padding | Use `echo -n "value" | base64` (the `-n` flag is required) |

---

## Submission Requirements

Create `SOLUTION-k8s.md` in the repository root containing all task answers.

- [ ] All manifests applied — `kubectl get all -n jobboard` screenshot
- [ ] All pods Running and Ready — `kubectl get pods -n jobboard` screenshot
- [ ] Application accessible via minikube IP — browser screenshot
- [ ] Rolling update demonstrated — `kubectl rollout history` output
- [ ] HPA scaling event — `kubectl describe hpa` output showing a scale event
- [ ] NetworkPolicy manifest `k8s/09-network-policy.yaml` committed
- [ ] ConfigMap manifest `k8s/10-configmap.yaml` committed
- [ ] Updated GitHub Actions pipeline with `deploy-to-k8s` job
- [ ] `SOLUTION-k8s.md` with all task answers and explanations

## Grading Rubric

| Task | Points | Criteria |
|------|--------|----------|
| Task 1 — Cluster Exploration | 15 | All commands run, outputs documented, questions answered |
| Task 2 — Networking & Ingress | 20 | Request trace correct, NetworkPolicy written, table complete |
| Task 3 — Storage & Backup | 15 | Persistence verified, backup captured, restore procedure documented |
| Task 4 — Scaling & Rolling Updates | 25 | Manual scale, zero-downtime rollout, HPA trigger observed |
| Task 5 — Secrets & ConfigMaps | 10 | Security implications explained, ConfigMap created and consumed |
| Task 6 — CI/CD Integration | 15 | Pipeline updated, deploy job implemented, smoke test added |
| **Total** | **100** | |
