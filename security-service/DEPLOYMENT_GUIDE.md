# Kubernetes Deployment Guide

This guide walks you through deploying the security-service to Kubernetes step by step.

## Prerequisites

- Docker installed and running
- Kubernetes cluster access (local or cloud)
- `kubectl` configured and connected to your cluster
- (Optional) Container registry account (Docker Hub, GitHub Container Registry, Azure Container Registry, etc.)

## Step-by-Step Deployment

### Step 1: Choose Your Container Registry

You have several options:

**Option A: Docker Hub**
```bash
export REGISTRY="docker.io"
export IMAGE_NAME="your-username/security-service"
export IMAGE_TAG="v1.0.0"
export FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
```

**Option B: GitHub Container Registry (ghcr.io)**
```bash
export REGISTRY="ghcr.io"
export IMAGE_NAME="your-username/security-service"
export IMAGE_TAG="v1.0.0"
export FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
```

**Option C: Azure Container Registry**
```bash
export REGISTRY="your-registry.azurecr.io"
export IMAGE_NAME="security-service"
export IMAGE_TAG="v1.0.0"
export FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
```

**Option D: Local/Minikube (for testing)**
```bash
# For minikube, use local image
eval $(minikube docker-env)
export FULL_IMAGE="security-service:local"
```

### Step 2: Build the Docker Image

Navigate to the security-service directory and build:

```bash
cd security-service
docker build -t ${FULL_IMAGE} .
```

**For local/minikube testing:**
```bash
# If using minikube, ensure you're using minikube's Docker
eval $(minikube docker-env)
docker build -t security-service:local .
```

### Step 3: Push the Image (if using remote registry)

**For Docker Hub:**
```bash
docker login
docker push ${FULL_IMAGE}
```

**For GitHub Container Registry:**
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker push ${FULL_IMAGE}
```

**For Azure Container Registry:**
```bash
az acr login --name your-registry
docker push ${FULL_IMAGE}
```

**For local/minikube:** Skip this step - image is already available locally.

### Step 4: Update Kubernetes Manifests

Update the image reference in `k8s/api.yaml`:

```bash
# Replace the image line in api.yaml
# Change: image: ghcr.io/example/security-service:latest
# To:     image: ${FULL_IMAGE}
```

Or use sed:
```bash
sed -i.bak "s|image: ghcr.io/example/security-service:latest|image: ${FULL_IMAGE}|g" k8s/api.yaml
```

**For local/minikube:**
```bash
sed -i.bak "s|image: ghcr.io/example/security-service:latest|image: security-service:local|g" k8s/api.yaml
sed -i.bak "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Never|g" k8s/api.yaml
```

### Step 5: Configure Secrets (Optional)

If you're using AbuseIPDB for IP reputation checks:

```bash
# Copy the example secret
cp k8s/secret-example.yaml k8s/secret.yaml

# Edit the file and add your real API key
# Then apply it:
kubectl apply -f k8s/secret.yaml
```

**If you don't have an AbuseIPDB key:**
- The service will still work, but IP reputation checks will be skipped
- You can remove the `secretRef` section from `k8s/api.yaml` (lines 25-26)

### Step 6: Configure CORS (Optional)

If your frontend is not on `localhost:3000`, update the ConfigMap:

```bash
# Edit k8s/configmap.yaml and add:
#   CORS_ORIGINS: "https://your-frontend.com,https://www.your-frontend.com"
```

Or apply it directly:
```bash
kubectl create configmap security-service-config \
  --from-literal=PORT=8000 \
  --from-literal=REDIS_HOST=redis \
  --from-literal=REDIS_PORT=6379 \
  --from-literal=REDIS_SSL=false \
  --from-literal=CORS_ORIGINS="https://your-frontend.com" \
  --namespace=security-service \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Step 7: Deploy to Kubernetes

Deploy in order:

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create ConfigMap
kubectl apply -f k8s/configmap.yaml

# 3. Deploy Redis (includes PVC, Deployment, and Service)
kubectl apply -f k8s/redis.yaml

# 4. Wait for Redis to be ready (optional but recommended)
kubectl wait --for=condition=ready pod -l app=redis -n security-service --timeout=60s

# 5. Deploy the API
kubectl apply -f k8s/api.yaml

# 6. Wait for API pods to be ready
kubectl wait --for=condition=ready pod -l app=security-service-api -n security-service --timeout=120s
```

### Step 8: Verify Deployment

Check that everything is running:

```bash
# Check pods
kubectl get pods -n security-service

# Expected output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# redis-xxxxxxxxxx-xxxxx                  1/1     Running   0          2m
# security-service-api-xxxxxxxxxx-xxxxx   1/1     Running   0          1m
# security-service-api-xxxxxxxxxx-xxxxx   1/1     Running   0          1m

# Check services
kubectl get svc -n security-service

# Check logs
kubectl logs -l app=security-service-api -n security-service --tail=50

# Check Redis logs
kubectl logs -l app=redis -n security-service --tail=20
```

### Step 9: Test the Service

**Option A: Port Forward (for local testing)**
```bash
# In one terminal, set up port forwarding
kubectl -n security-service port-forward svc/security-service-api 8000:80

# In another terminal, test the API
curl http://localhost:8000/health | jq

# Test the check endpoint
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{
    "public_ip": "1.2.3.4",
    "open_ports": [
      {"port": 22, "exposed_to_internet": true},
      {"port": 80, "exposed_to_internet": true}
    ]
  }' | jq
```

**Option B: Access via Service (from within cluster)**
```bash
# Get the service IP
kubectl get svc security-service-api -n security-service

# From another pod in the cluster:
curl http://security-service-api.security-service.svc.cluster.local/health
```

**Option C: Create Ingress (for production)**
```yaml
# Create k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: security-service-ingress
  namespace: security-service
spec:
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: security-service-api
            port:
              number: 80
```

### Step 10: Monitor and Troubleshoot

**Common issues and solutions:**

1. **Pods not starting:**
   ```bash
   kubectl describe pod <pod-name> -n security-service
   kubectl logs <pod-name> -n security-service
   ```

2. **Redis connection issues:**
   ```bash
   # Check if Redis is running
   kubectl get pods -l app=redis -n security-service
   
   # Test Redis connectivity from API pod
   kubectl exec -it <api-pod-name> -n security-service -- python -c "import redis; r=redis.Redis(host='redis', port=6379); print(r.ping())"
   ```

3. **Image pull errors:**
   ```bash
   # Check if image exists and is accessible
   docker pull ${FULL_IMAGE}
   
   # For minikube, ensure you're using minikube's Docker
   eval $(minikube docker-env)
   ```

4. **Health check failures:**
   ```bash
   # Check health endpoint directly
   kubectl exec -it <api-pod-name> -n security-service -- curl http://localhost:8000/health
   ```

## Quick Start Script

Here's a complete script you can customize and run:

```bash
#!/bin/bash
set -e

# Configuration
export REGISTRY="ghcr.io"  # Change to your registry
export IMAGE_NAME="your-username/security-service"
export IMAGE_TAG="v1.0.0"
export FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

# Build
echo "Building image..."
docker build -t ${FULL_IMAGE} .

# Push (uncomment if using remote registry)
# echo "Pushing image..."
# docker push ${FULL_IMAGE}

# Update manifests
echo "Updating manifests..."
sed -i.bak "s|image: ghcr.io/example/security-service:latest|image: ${FULL_IMAGE}|g" k8s/api.yaml

# Deploy
echo "Deploying to Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis.yaml
kubectl wait --for=condition=ready pod -l app=redis -n security-service --timeout=60s
kubectl apply -f k8s/api.yaml

echo "Waiting for API pods..."
kubectl wait --for=condition=ready pod -l app=security-service-api -n security-service --timeout=120s

echo "Deployment complete!"
echo "Check status with: kubectl get pods -n security-service"
echo "Port forward with: kubectl -n security-service port-forward svc/security-service-api 8000:80"
```

## Next Steps

1. **Set up CI/CD** - Automate building and deploying on code changes
2. **Configure monitoring** - Add Prometheus metrics and Grafana dashboards
3. **Set up logging** - Configure centralized logging (e.g., ELK stack, Loki)
4. **Add Ingress** - Expose the service via Ingress controller
5. **Configure autoscaling** - Set up HorizontalPodAutoscaler based on CPU/memory
6. **Add network policies** - Restrict network traffic for better security
7. **Set up backup** - Configure Redis backup strategy

## Cleanup

To remove everything:

```bash
kubectl delete namespace security-service
```

Or delete resources individually:

```bash
kubectl delete -f k8s/api.yaml
kubectl delete -f k8s/redis.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/namespace.yaml
```

