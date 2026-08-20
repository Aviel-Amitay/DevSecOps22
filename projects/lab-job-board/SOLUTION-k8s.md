#### 1.1 — Inspect all objects (5 pts)

Run each command and include the output in your `SOLUTION-k8s.md`:
1.
```bash
kubectl get all -n jobboard
```
- Output:
```text
NAME                                        READY   STATUS      RESTARTS   AGE
pod/applications-service-7d6c77665c-47pkl   1/1     Running     0          23h
pod/applications-service-7d6c77665c-8rrr7   1/1     Running     0          23h
pod/frontend-789c4886d8-mqvks               1/1     Running     0          23h
pod/frontend-789c4886d8-tlwxh               1/1     Running     0          23h
pod/jobs-service-8674bc4475-fnmjl           1/1     Running     0          23h
pod/jobs-service-8674bc4475-xkp7w           1/1     Running     0          23h
pod/postgres-564dbdc44c-wvzwt               1/1     Running     0          23h
pod/seed-database-c4hh2                     0/1     Completed   0          115s

NAME                           TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
service/applications-service   ClusterIP   10.109.3.111     <none>        3001/TCP   23h
service/frontend               ClusterIP   10.98.106.219    <none>        80/TCP     23h
service/jobs-service           ClusterIP   10.108.248.206   <none>        8000/TCP   23h
service/postgres               ClusterIP   10.105.56.21     <none>        5432/TCP   23h

NAME                                   READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/applications-service   2/2     2            2           23h
deployment.apps/frontend               2/2     2            2           23h
deployment.apps/jobs-service           2/2     2            2           23h
deployment.apps/postgres               1/1     1            1           23h

NAME                                              DESIRED   CURRENT   READY   AGE
replicaset.apps/applications-service-7d6c77665c   2         2         2       23h
replicaset.apps/frontend-789c4886d8               2         2         2       23h
replicaset.apps/jobs-service-8674bc4475           2         2         2       23h
replicaset.apps/postgres-564dbdc44c               1         1         1       23h

NAME                                                           REFERENCE                         TARGETS                        MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/applications-service-hpa   Deployment/applications-service   cpu: 2%/60%, memory: 17%/75%   2         6         2          23h
horizontalpodautoscaler.autoscaling/jobs-service-hpa           Deployment/jobs-service           cpu: 6%/60%, memory: 46%/75%   2         6         2          23h

NAME                      STATUS     COMPLETIONS   DURATION   AGE
job.batch/seed-database   Complete   1/1           4s         115s
```
2.
```bash
kubectl get pvc -n jobboard
```
  - Output:
  ```text
  NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
postgres-pvc   Bound    pvc-3a4eb529-204e-44b9-a835-c7f077853486   1Gi        RWO            standard       <unset>                 23h
  ```

3.
```bash
kubectl get ingress -n jobboard
```

 - Output:
    ```text
    NAME                   CLASS   HOSTS   ADDRESS        PORTS   AGE
    applications-ingress   nginx   *       192.168.49.2   80      23h
    frontend-ingress       nginx   *       192.168.49.2   80      23h
    jobs-ingress           nginx   *       192.168.49.2   80      23h
    ```

4.
```bash
kubectl get hpa -n jobboard
```
- Output
    ```text
    NAME                       REFERENCE                         TARGETS                        MINPODS   MAXPODS   REPLICAS   AGE
    applications-service-hpa   Deployment/applications-service   cpu: 2%/60%, memory: 17%/75%   2         6         2          23h
    jobs-service-hpa           Deployment/jobs-service           cpu: 6%/60%, memory: 46%/75%   2         6         2          23h
    ```
```bash
kubectl get secret -n jobboard
```

- Output
    ```text
    NAME              TYPE     DATA   AGE
    postgres-secret   Opaque   3      23h
    ```

For each resource type, answer in `SOLUTION-k8s.md`:

- What is the **READY** ratio for each Deployment?

| Deployment | READY ratio | Status |
|---|---:|---|
| applications-service | `2/2` | All replicas are ready |
| frontend | `2/2` | All replicas are ready |
| jobs-service | `2/2` | All replicas are ready |
| postgres | `1/1` | All replicas are ready |

- What is the **CLUSTER-IP** of each Service?

| Service | Cluster IP |
|---|---|
| applications-service | `10.109.3.111` |
| frontend | `10.98.106.219` |
| jobs-service | `10.108.248.206` |
| postgres | `10.105.56.21` |

- What storage class was assigned to `postgres-pvc`?

    - Standard
