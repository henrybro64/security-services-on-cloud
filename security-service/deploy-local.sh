#!/bin/bash
set -e

echo "🚀 Deploying security-service to Docker Desktop Kubernetes"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl."
    exit 1
fi

# Check if Kubernetes is running
if ! kubectl get nodes &> /dev/null; then
    echo "❌ Kubernetes not accessible. Please enable Kubernetes in Docker Desktop:"
    echo "   Settings → Kubernetes → Enable Kubernetes"
    exit 1
fi

echo "✅ Kubernetes is running"
echo ""

# Navigate to security-service directory
cd "$(dirname "$0")"

# Load environment variables from .env if present (e.g., ABUSEIPDB_API_KEY)
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

echo "🔨 Step 1: Building Docker image..."
docker build -t security-service:local . || {
    echo "❌ Docker build failed"
    exit 1
}

echo "✅ Image built successfully"
echo ""

echo "📝 Step 2: Updating Kubernetes manifests for local image..."
# Create backup and update image
sed -i.bak "s|image: ghcr.io/example/security-service:latest|image: security-service:local|g" k8s/api.yaml
sed -i.bak "s|imagePullPolicy: IfNotPresent|imagePullPolicy: Never|g" k8s/api.yaml

echo "✅ Manifests updated"
echo ""

echo "🚀 Step 3: Deploying to Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml

# Create secret if it doesn't exist (required by deployment)
if ! kubectl get secret security-service-secrets -n security-service &>/dev/null; then
    if [ -z "${ABUSEIPDB_API_KEY:-}" ]; then
        echo "❌ ABUSEIPDB_API_KEY is not set. Export it before running this script to create the secret."
        echo "   Example: export ABUSEIPDB_API_KEY=\"<your-api-key>\""
        exit 1
    fi

    echo "📝 Creating secret from ABUSEIPDB_API_KEY environment variable..."
    kubectl create secret generic security-service-secrets \
        --from-literal=ABUSEIPDB_API_KEY="${ABUSEIPDB_API_KEY}" \
        --namespace=security-service \
        --dry-run=client -o yaml | kubectl apply -f -
else
    echo "✅ Secret already exists"
fi

kubectl apply -f k8s/redis.yaml

echo "⏳ Waiting for Redis to be ready..."
if kubectl wait --for=condition=ready pod -l app=redis -n security-service --timeout=60s 2>/dev/null; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis may still be starting. Continuing..."
fi
echo ""

echo "🚀 Step 4: Deploying API..."
kubectl apply -f k8s/api.yaml

echo "⏳ Waiting for API pods to be ready..."
if kubectl wait --for=condition=ready pod -l app=security-service-api -n security-service --timeout=120s 2>/dev/null; then
    echo "✅ API pods are ready"
else
    echo "⚠️  API pods may still be starting. Check status with: kubectl get pods -n security-service"
fi
echo ""

echo "📊 Deployment Status:"
kubectl get pods -n security-service
echo ""

echo "✅ Deployment complete!"
echo ""
echo "🔗 Next steps:"
echo "   1. Port forward: kubectl -n security-service port-forward svc/security-service-api 8000:80"
echo "   2. Test health: curl http://localhost:8000/health"
echo "   3. Open Swagger UI: http://localhost:8000/docs"
echo ""
echo "📝 To view logs:"
echo "   kubectl logs -l app=security-service-api -n security-service -f"
echo ""
echo "🧹 To cleanup:"
echo "   kubectl delete namespace security-service"

