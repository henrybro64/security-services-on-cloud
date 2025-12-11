# Quick Start Checklist

> **For Docker Desktop users:** See [DOCKER_DESKTOP_K8S.md](./DOCKER_DESKTOP_K8S.md) for a simplified guide, or just run `./deploy-local.sh`

Follow these steps in order to deploy to Kubernetes:

## ✅ Pre-Deployment Checklist

- [ ] Docker is installed and running
- [ ] Kubernetes cluster is accessible (`kubectl get nodes` should work)
- [ ] Container registry account (Docker Hub, GHCR, ACR, etc.) OR using local/minikube
- [ ] (Optional) AbuseIPDB API key if you want IP reputation checks

## 🚀 Deployment Steps

### 1. Set Your Image Configuration
```bash
# Choose ONE option:

# Option A: Docker Hub
export FULL_IMAGE="docker.io/your-username/security-service:v1.0.0"

# Option B: GitHub Container Registry
export FULL_IMAGE="ghcr.io/your-username/security-service:v1.0.0"

# Option C: Azure Container Registry
export FULL_IMAGE="your-registry.azurecr.io/security-service:v1.0.0"

# Option D: Local/Minikube (for testing)
eval $(minikube docker-env)  # if using minikube
export FULL_IMAGE="security-service:local"
```

### 2. Build the Image
```bash
cd security-service
docker build -t ${FULL_IMAGE} .
```

### 3. Push Image (skip if using local/minikube)
```bash
# Docker Hub
docker login
docker push ${FULL_IMAGE}

# GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker push ${FULL_IMAGE}

# Azure Container Registry
az acr login --name your-registry
docker push ${FULL_IMAGE}
```

### 4. Update Kubernetes Manifest
```bash
# Update the image in api.yaml
sed -i.bak "s|image: ghcr.io/example/security-service:latest|image: ${FULL_IMAGE}|g" k8s/api.yaml

# If using local/minikube, also change imagePullPolicy
sed -i.bak "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Never|g" k8s/api.yaml
```

### 5. Configure Secrets (Optional)
```bash
# If you have AbuseIPDB API key:
cp k8s/secret-example.yaml k8s/secret.yaml
# Edit k8s/secret.yaml with your real key
kubectl apply -f k8s/secret.yaml

# If you DON'T have a key, remove secretRef from k8s/api.yaml (lines 25-26)
```

### 6. Configure CORS (Optional)
```bash
# If frontend is NOT on localhost:3000, add to k8s/configmap.yaml:
#   CORS_ORIGINS: "https://your-frontend.com"
```

### 7. Deploy to Kubernetes
```bash
# Deploy in order:
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis.yaml
kubectl wait --for=condition=ready pod -l app=redis -n security-service --timeout=60s
kubectl apply -f k8s/api.yaml
kubectl wait --for=condition=ready pod -l app=security-service-api -n security-service --timeout=120s
```

### 8. Verify Deployment
```bash
# Check pods are running
kubectl get pods -n security-service

# Check logs
kubectl logs -l app=security-service-api -n security-service --tail=50
```

### 9. Test the Service
```bash
# Port forward
kubectl -n security-service port-forward svc/security-service-api 8000:80

# In another terminal, test:
curl http://localhost:8000/health | jq
```

## 🐛 Troubleshooting

**Pods not starting?**
```bash
kubectl describe pod <pod-name> -n security-service
kubectl logs <pod-name> -n security-service
```

**Can't connect to Redis?**
```bash
kubectl get pods -l app=redis -n security-service
kubectl logs -l app=redis -n security-service
```

**Image pull errors?**
- Verify image exists: `docker pull ${FULL_IMAGE}`
- For minikube: `eval $(minikube docker-env)` then rebuild

## 📚 More Details

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed explanations and advanced configurations.

