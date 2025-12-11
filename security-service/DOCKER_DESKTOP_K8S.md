# Deploying to Kubernetes on Docker Desktop

This guide is specifically for deploying to the Kubernetes cluster built into Docker Desktop.

## Prerequisites

1. **Docker Desktop installed** and running
2. **Kubernetes enabled** in Docker Desktop:
   - Open Docker Desktop
   - Go to Settings → Kubernetes
   - Check "Enable Kubernetes"
   - Click "Apply & Restart"
   - Wait for Kubernetes to start (green indicator)

3. **Verify Kubernetes is running:**
   ```bash
   kubectl get nodes
   # Should show: docker-desktop
   ```

## Step-by-Step Deployment

### Step 1: Build the Docker Image Locally

Since we're using Docker Desktop, we can use a local image without pushing to a registry:

```bash
cd security-service

# Build the image with a local tag
docker build -t security-service:local .
```

**Verify the image was created:**
```bash
docker images | grep security-service
```

### Step 2: Update Kubernetes Manifest for Local Image

We need to update `k8s/api.yaml` to use the local image and set `imagePullPolicy: Never`:

```bash
# Update the image reference
sed -i.bak "s|image: ghcr.io/example/security-service:latest|image: security-service:local|g" k8s/api.yaml

# Set imagePullPolicy to Never (so it uses local image)
sed -i.bak "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Never|g" k8s/api.yaml
```

**Or manually edit `k8s/api.yaml`:**
- Change line 18: `image: security-service:local`
- Change line 19: `imagePullPolicy: Never`

### Step 3: Configure Secrets (Optional)

If you have an AbuseIPDB API key:

```bash
# Copy the example
cp k8s/secret-example.yaml k8s/secret.yaml

# Edit k8s/secret.yaml and replace "replace-with-real-key" with your actual key
# Then apply:
kubectl apply -f k8s/secret.yaml
```

**If you don't have a key:**
- The service will work fine, just skip IP reputation checks
- You can remove the `secretRef` section from `k8s/api.yaml` (lines 25-26) if you want

### Step 4: Deploy to Kubernetes

Deploy all components in order:

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create ConfigMap
kubectl apply -f k8s/configmap.yaml

# 3. Deploy Redis (includes PVC, Deployment, and Service)
kubectl apply -f k8s/redis.yaml

# 4. Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis -n security-service --timeout=60s

# 5. Deploy the API
kubectl apply -f k8s/api.yaml

# 6. Wait for API pods to be ready
kubectl wait --for=condition=ready pod -l app=security-service-api -n security-service --timeout=120s
```

### Step 5: Verify Deployment

Check that everything is running:

```bash
# Check all pods
kubectl get pods -n security-service

# Expected output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# redis-xxxxxxxxxx-xxxxx                  1/1     Running   0          30s
# security-service-api-xxxxxxxxxx-xxxxx   1/1     Running   0          20s
# security-service-api-xxxxxxxxxx-xxxxx   1/1     Running   0          20s

# Check services
kubectl get svc -n security-service

# Check API logs
kubectl logs -l app=security-service-api -n security-service --tail=50

# Check Redis logs
kubectl logs -l app=redis -n security-service --tail=20
```

### Step 6: Test the Service

**Set up port forwarding:**
```bash
# This forwards local port 8000 to the service
kubectl -n security-service port-forward svc/security-service-api 8000:80
```

**In another terminal, test the API:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Or with pretty JSON output (if you have jq)
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

# Test the scan endpoint (requires nmap)
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "scanme.nmap.org"
  }' | jq
```

**Access Swagger UI:**
```bash
# With port forwarding active, open in browser:
open http://localhost:8000/docs
# or
# http://localhost:8000/docs
```

## Complete One-Liner Script

Here's a complete script you can run:

```bash
#!/bin/bash
set -e

cd security-service

echo "🔨 Building Docker image..."
docker build -t security-service:local .

echo "📝 Updating Kubernetes manifests..."
sed -i.bak "s|image: ghcr.io/example/security-service:latest|image: security-service:local|g" k8s/api.yaml
sed -i.bak "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Never|g" k8s/api.yaml

echo "🚀 Deploying to Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis.yaml

echo "⏳ Waiting for Redis..."
kubectl wait --for=condition=ready pod -l app=redis -n security-service --timeout=60s

echo "🚀 Deploying API..."
kubectl apply -f k8s/api.yaml

echo "⏳ Waiting for API pods..."
kubectl wait --for=condition=ready pod -l app=security-service-api -n security-service --timeout=120s

echo "✅ Deployment complete!"
echo ""
echo "📊 Check status:"
kubectl get pods -n security-service
echo ""
echo "🔗 Port forward:"
echo "kubectl -n security-service port-forward svc/security-service-api 8000:80"
echo ""
echo "🧪 Test:"
echo "curl http://localhost:8000/health"
```

Save this as `deploy-local.sh`, make it executable, and run:
```bash
chmod +x deploy-local.sh
./deploy-local.sh
```

## Troubleshooting

### Issue: "ImagePullBackOff" error

**Solution:** Make sure you:
1. Built the image: `docker build -t security-service:local .`
2. Set `imagePullPolicy: Never` in `k8s/api.yaml`
3. Verified image exists: `docker images | grep security-service`

### Issue: Pods stuck in "Pending"

**Solution:** Check resource availability:
```bash
kubectl describe pod <pod-name> -n security-service
# Look for resource constraints or node issues
```

### Issue: Redis connection errors

**Solution:** 
```bash
# Check Redis is running
kubectl get pods -l app=redis -n security-service

# Check Redis logs
kubectl logs -l app=redis -n security-service

# Test connectivity from API pod
kubectl exec -it $(kubectl get pod -l app=security-service-api -n security-service -o jsonpath='{.items[0].metadata.name}') -n security-service -- python -c "import redis; r=redis.Redis(host='redis', port=6379); print(r.ping())"
```

### Issue: Port forwarding fails

**Solution:**
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Use a different port
kubectl -n security-service port-forward svc/security-service-api 8080:80
# Then access at http://localhost:8080
```

### Issue: Health check fails

**Solution:**
```bash
# Check pod logs
kubectl logs -l app=security-service-api -n security-service

# Check if the app is listening
kubectl exec -it $(kubectl get pod -l app=security-service-api -n security-service -o jsonpath='{.items[0].metadata.name}') -n security-service -- curl http://localhost:8000/health
```

## Viewing Resources in Docker Desktop

Docker Desktop provides a nice UI for viewing Kubernetes resources:

1. Open Docker Desktop
2. Go to the "Kubernetes" tab
3. You can see:
   - Namespaces
   - Pods
   - Services
   - Deployments
   - Logs

## Updating the Deployment

After making code changes:

```bash
# 1. Rebuild the image
docker build -t security-service:local .

# 2. Restart the deployment
kubectl rollout restart deployment security-service-api -n security-service

# 3. Watch the rollout
kubectl rollout status deployment security-service-api -n security-service
```

## Cleanup

To remove everything:

```bash
# Delete the entire namespace (removes everything)
kubectl delete namespace security-service

# Or delete resources individually
kubectl delete -f k8s/api.yaml
kubectl delete -f k8s/redis.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/namespace.yaml
```

## Next Steps

Once you have it working locally:

1. **Test all endpoints** - Use the Swagger UI at `http://localhost:8000/docs`
2. **Monitor logs** - Watch logs in real-time: `kubectl logs -f -l app=security-service-api -n security-service`
3. **Scale the deployment** - Test scaling: `kubectl scale deployment security-service-api --replicas=3 -n security-service`
4. **Deploy to cloud** - When ready, follow the cloud deployment guide in `DEPLOYMENT_GUIDE.md`

