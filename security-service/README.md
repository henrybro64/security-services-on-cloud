# Security Service API

FastAPI backend that evaluates infrastructure risk and caches results in Redis. The repo ships with a Dockerfile and docker-compose setup for local work. The manifests in `k8s/` let you run the same stack (API + Redis) on any Kubernetes cluster.

## Deploying to Kubernetes

1. **Build and push the image**
   ```bash
   export IMAGE=ghcr.io/<org>/security-service:latest
   docker build -t "$IMAGE" .
   docker push "$IMAGE"
   ```
   Update the `image` field in `k8s/api.yaml` to match the tag you pushed.

2. **Create the namespace**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

3. **Create the AbuseIPDB secret**
   ```bash
   cp k8s/secret-example.yaml k8s/secret.yaml
   # edit k8s/secret.yaml and set ABUSEIPDB_API_KEY to your real key
   kubectl apply -f k8s/secret.yaml
   ```
   (If you do not have a key, skip the secret and remove the `secretRef` block from `k8s/api.yaml`.)

4. **Apply the shared config, Redis, and API deployments**
   ```bash
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/redis.yaml
   kubectl apply -f k8s/api.yaml
   ```
   This creates:
   - `ConfigMap` with Redis host/port config used by the API
   - `PersistentVolumeClaim` + Redis `Deployment` + `Service`
   - FastAPI `Deployment` (2 replicas) and `ClusterIP` service `security-service-api`

5. **Verify**
   ```bash
   kubectl get pods -n security-service
   kubectl logs deploy/security-service-api -n security-service
   ```

6. **Expose the API** – In dev clusters you can port-forward:
   ```bash
   kubectl -n security-service port-forward svc/security-service-api 8000:80
   ```
   For production, front the service with an Ingress or change it to a `LoadBalancer` service type.

### Optional: Clean up
```bash
kubectl delete namespace security-service
```

## Local docker-compose (still available)
```bash
docker compose up --build
```
