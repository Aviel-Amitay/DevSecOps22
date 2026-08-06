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

- Explain what condition: service_healthy does vs condition: service_started

	- service_healthy -> Mean that the container is alive with all of the services, while service_started wait until all his dependacy start.

## Task 3

### 3.1 – Verify persistence across restarts

- Create a new job via the UI or API:
	- Fix curl code:

```bash
curl -s -X POST http://localhost/api/jobs   -H Content-Type: application/json   -d '{title:Persistence Test Job,description:Testing Docker volumes,company:Lab Inc,location:Docker}'   | python3 -m json.tool
```

- Stop and restart the containers
Done

- Verify your job still exists:
	- Remove the last backslash from the jobs/ which cause the command to failed.

```bash
curl -s http://localhost/api/jobs | python3 -m json.tool
```

- Explain the difference between docker compose down, docker compose down -v, and docker compose stop. When would you use each?
	- `docker compose down` - Mean that I'm termibate and delete the container and the network interface associate with this continers.
	- `docker compose down -v` - This is a new flag for me, after searching is to include also delete volumes.
	- `docker compose stop` - Stop the container process, NOT delete.

### 3.2 Volume inspection

- Inspect the named volume:




```bash
docker volume inspect jobboard-postgres-data
```

- **Output**

```text
[
    {
        "CreatedAt": "2026-08-06T13:00:00Z",
        "Driver": "local",
        "Labels": {
            "com.docker.compose.config-hash": "51cb1b890dca508cb1c6e869d49a43bf77eb2b579d8769998c61578da7750fb3",
            "com.docker.compose.project": "lab-job-board",
            "com.docker.compose.version": "5.2.0",
            "com.docker.compose.volume": "postgres-data"
        },
        "Mountpoint": "/var/lib/docker/volumes/jobboard-postgres-data/_data",
        "Name": "jobboard-postgres-data",
        "Options": null,
        "Scope": "local"
    }
]
```
---

```bash
docker volume ls
```

- **Output**

```text
DRIVER    VOLUME NAME
local     87fa306356983684681d90159ec692922f76ff37b071c8cbfb9f87bd57561053
local     6449742c10e189576da26c63ddb2a8ec686c4dbaa659f8c6d36babcdb837bd66
local     jenkins_home
local     jobboard-postgres-data
local     minikube
```

- Where on the host machine is the data actually stored?
	- On MacOS, volume is stored under the `~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw`.

- What is the difference between a named volume (postgres-data:) and a bind mount (./data:/var/lib/postgresql/data)?
	- named volume (postgres-data:) - Is a block volume
	- bind mount (./data:/var/lib/postgresql/data) - Used when I need to share data between the host <-> Container.

- When would you prefer each approach in production?
	- Depend on the container type. For example if I want to build a docker image part of a Jenkins process, I will share my docker.socket with the container.  

### 3.3 – Database backup and restore  

- Database backup

```bash
docker exec jobboard-db pg_dump \
  -U postgres \
  -d jobboard \
  --no-owner \
  --no-acl \
  -F plain > backup_$(date +%Y%m%d_%H%M%S).sql
```

- **Result**
```text
total 80
-rw-r--r--   1 aviela  staff    22K Aug  3 17:27 README.md
drwxr-xr-x   6 aviela  staff   192B Aug  3 20:43 applications-service
-rw-r--r--   1 aviela  staff   4.9K Aug  7 00:08 backup_20260807_000855.sql
-rw-r--r--@  1 aviela  staff   4.1K Aug  6 17:02 docker-compose.yml
drwxr-xr-x  12 aviela  staff   384B Aug  3 21:04 frontend
drwxr-xr-x   3 aviela  staff    96B Aug  3 17:27 init-db
drwxr-xr-x   6 aviela  staff   192B Aug  3 17:27 jobs-service
drwxr-xr-x  13 aviela  staff   416B Aug  3 17:27 k8s
drwxr-xr-x   5 aviela  staff   160B Aug  6 16:53 nginx
drwxr-xr-x   5 aviela  staff   160B Aug  7 00:08 results
```


