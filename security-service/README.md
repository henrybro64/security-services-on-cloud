# Security Service API

FastAPI backend for infrastructure security evaluation. Uses Redis for caching results.

## Local Development

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`. Swagger docs at `/docs`.

## Deployment

Deployed to Azure Container Apps via Terraform and GitHub Actions. See `infra/DEPLOYMENT_WORKFLOW.md` for details.

The `k8s/` directory contains Kubernetes manifests for reference (not currently used).
