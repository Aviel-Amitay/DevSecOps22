## Task 1
- Result How many CVE found with a CRITICAL -> 5

lab-job-board-applications-service.txt:Total: 28 (UNKNOWN: 0, LOW: 2, MEDIUM: 8, HIGH: 17, CRITICAL: 1)
lab-job-board-jobs-service.txt:Total: 173 (UNKNOWN: 28, LOW: 66, MEDIUM: 56, HIGH: 19, CRITICAL: 4)
lab-job-board-jobs-service.txt:Total: 13 (UNKNOWN: 0, LOW: 2, MEDIUM: 8, HIGH: 3, CRITICAL: 0)

- The image with the most vulnerabilities is "lab-job-board-jobs-service:latest"

CVE-2026-59873
-  is a critical denial-of-service (DoS) vulnerability in node-tar, the popular tar archive manipulation library for Node.js. Versions prior to 7.5.19 fail to limit decompression ratios or track total output size, allowing a small gzip bomb to crash applications via CPU and disk exhaustion.

Aviel note - The tar tool is a popular tool that use in a lot of indstury to help and reduce size, and from that why that is critical.


## Task 1.2
1. Ensure the final image runs as a non-root user 
 - docker run --rm lab-job-board-jobs-service:latest whoami
appuser

 - docker run --rm lab-job-board-applications-service:latest whoami
appuser

2. Pin all FROM tags to an exact digest
- for u in `docker image ls | grep board | awk {print }` ; do docker inspect --format={{index .RepoDigests 0}}  $u  ; done

lab-job-board-applications-service@sha256:703ea01e9aaf0f0c9ef48a0ec2fde27e7ed69ef287c92857a3883c9463b1d9cb
lab-job-board-frontend@sha256:ba87f060dfd9812915007e482710c08bb705eefecc8ab0494f22fe14062cd400
lab-job-board-jobs-service@sha256:8afb15ecaa023197fcfad9acfa495ae53f7fb328f8a4f80d7b08a7709b744aaf
lab-job-board-nginx@sha256:ef19a27dbecde3ce99bbbfd9f18ac17b858eae7f2bb3d0372d259f03fe4755c8

3. Add a .dockerignore file if one is missing 
- Added a `.dockerignore` file on the `nginx` directory

4. Add a HEALTHCHECK instruction to any Dockerfile that lacks one 
- HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:80/api/jobs/ || exit 1
	- I've replaced from `localhost` to `127.0.0.1`

5. Reduce the final image layer count using && chaining in RUN statements
- All `Dockerfile` files verified manually.


## Task 2

### 2.1 – Logging configuration

- docker compose logs -f jobs-service | tee -a

### 2.2 Environment variable isolation
- Done  
	- Why? Beacuse env file contain a sensitve information like password, API keys, and when pushing it into GitHub or other provider, it expose to everyone.

### 2.3 Service restart policy and dependency ordering
-docker compose up --build 2>&1 | grep -iE "healthy|started|Starting" 
 > Container jobboard-db Starting   
 Container jobboard-db Started   
jobboard-db  | 2026-08-06 14:29:08.154 UTC [1] LOG:  starting PostgreSQL 16.14 on aarch64-unknown-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit  
 Container jobboard-db Healthy   
 Container jobboard-db Healthy   
 Container applications-service Starting  
 Container jobs-service Starting   
 Container jobs-service Started   
 Container applications-service Started   
jobs-service          | INFO:     Started server process [1]  
 Container applications-service Healthy   
 Container jobs-service Healthy   
 Container jobboard-frontend Starting   
 Container jobboard-frontend Started   
 Container nginx-proxy Starting   
 Container nginx-proxy Started   

```text
postgres
├── jobs-service
│   └── frontend
└── applications-service
    └── frontend

frontend ─────────────┐
jobs-service ─────────┼──► nginx-proxy
applications-service ┘
```
