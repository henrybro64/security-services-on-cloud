# CloudHostInspector

A security assessment tool that evaluates infrastructure security risks by analyzing host configurations, open ports, IP reputation, and providing actionable recommendations.

## Overview

CloudHostInspector consists of two main components:

- **Backend API** (FastAPI): Performs security risk evaluation, host scanning with nmap, and IP reputation checks using AbuseIPDB
- **Frontend UI** (Next.js): Web interface for submitting security checks and viewing results

The system uses Redis for caching assessment results to improve performance and reduce redundant computations.

## Features

- **Host Scanning**: Automated nmap-based port scanning and OS detection
- **Risk Assessment**: Evaluates security posture based on:
  - Operating system type
  - Open ports and protocols
  - Public vs private IP exposure
  - IP reputation (via AbuseIPDB)
- **Caching**: Redis-backed result caching to avoid redundant scans
- **Web Interface**: Modern UI built with Next.js and Carbon Design System
- **API Documentation**: Interactive Swagger/OpenAPI docs at `/docs`

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │ ──────> │   Backend    │ ──────> │    Redis    │
│  (Next.js)  │         │   (FastAPI)  │         │   (Cache)   │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │  AbuseIPDB   │
                        │  (External)  │
                        └──────────────┘
```

## Prerequisites

### For Local Deployment
- Docker and Docker Compose
- (Optional) AbuseIPDB API key for IP reputation checks

### For Azure Deployment
- Azure CLI installed and configured (`az login`)
- Terraform >= 1.5.0
- GitHub account with Actions enabled
- Azure subscription with permissions to create:
  - Resource Groups
  - Container Apps
  - Container Registry (ACR)
  - Redis Cache
  - Log Analytics Workspace

## Local Deployment

### Quick Start

1. **Start the backend service:**
   ```bash
   cd security-service
   docker compose up --build
   ```

   The API will be available at `http://localhost:8000`

2. **Start the frontend:**
   ```bash
   cd security-frontend
   npm install
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

### Configuration

#### Backend Environment Variables

Create a `.env` file in `security-service/` (optional):

```bash
ABUSEIPDB_API_KEY=your_api_key_here  # Optional, for IP reputation checks
API_KEY=your_api_key_here            # Optional, for API authentication
```

If `API_KEY` is not set, authentication is disabled (useful for local development).

#### Frontend Environment Variables

The frontend automatically connects to `http://localhost:8000` when running locally. To override:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your_api_key_here  # Optional
```

### Testing the API

1. **Health check:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Interactive API docs:**
   Open `http://localhost:8000/docs` in your browser

3. **Manual security check:**
   ```bash
   curl -X POST http://localhost:8000/check \
     -H "Content-Type: application/json" \
     -d '{
       "os": "ubuntu",
       "public_ip": true,
       "open_ports": [
         {"port": 22, "protocol": "tcp", "exposed_to_internet": true},
         {"port": 80, "protocol": "tcp", "exposed_to_internet": true}
       ]
     }'
   ```

4. **Host scan:**
   ```bash
   curl -X POST http://localhost:8000/scan \
     -H "Content-Type: application/json" \
     -d '{"target": "scanme.nmap.org"}'
   ```

## Azure Deployment

### Initial Setup

1. **Configure Terraform variables:**
   ```bash
   cd infra
   cp terraform.tfvars.example terraform.tfvars  # If example exists
   # Edit terraform.tfvars with your values
   ```

   Required variables:
   - `acr_name`: Globally unique Azure Container Registry name (lowercase, 5-50 chars)

   Optional variables (with defaults):
   - `project_name`: Resource name prefix (default: "securityproj")
   - `location`: Azure region (default: "japaneast")

2. **Deploy infrastructure:**
   ```bash
   cd infra
   ./deploy.sh init
   ./deploy.sh plan
   ./deploy.sh apply
   ```

   This creates:
   - Resource Group
   - Container App Environment
   - Azure Container Registry (ACR)
   - Azure Cache for Redis
   - Log Analytics Workspace
   - Backend and Frontend Container Apps (with placeholder images)

3. **Configure GitHub Secrets:**

   Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

   - `AZURE_CLIENT_ID`: Service principal client ID
   - `AZURE_TENANT_ID`: Azure tenant ID
   - `AZURE_SUBSCRIPTION_ID`: Azure subscription ID
   - `AZURE_CLIENT_SECRET`: Service principal client secret
   - `RESOURCE_GROUP`: Resource group name (e.g., `securityproj-rg`)
   - `AZURE_CONTAINER_REGISTRY`: ACR login server (e.g., `securityprojacr.azurecr.io`)
   - `ABUSEIPDB_API_KEY`: AbuseIPDB API key (for IP reputation checks)
   - `NEXT_PUBLIC_API_BASE_URL`: Backend URL (get from Terraform outputs after first deploy)

4. **Get the backend URL:**
   ```bash
   cd infra
   terraform output backend_url
   ```

   Update the `NEXT_PUBLIC_API_BASE_URL` GitHub secret with this value.

5. **Deploy applications via GitHub Actions:**

   - Push code to trigger workflows, or manually run:
     - `.github/workflows/backend-container-apps.yml`
     - `.github/workflows/frontend-container-apps.yml`

   These workflows will:
   - Build Docker images
   - Push to Azure Container Registry
   - Update Container Apps with the new images

6. **Get application URLs:**
   ```bash
   cd infra
   terraform output frontend_url
   terraform output backend_url
   ```

### Destroying Resources

To remove all Azure resources and stop costs:

```bash
cd infra
./deploy.sh destroy
```

Or manually:
```bash
cd infra
terraform destroy -var-file=terraform.tfvars
```

### Deployment Workflow

1. **Terraform** creates infrastructure with placeholder container images
2. **GitHub Actions** builds and pushes real application images to ACR
3. **GitHub Actions** updates Container Apps to use the new images
4. Applications are accessible via public URLs

This design allows you to:
- Deploy infrastructure once with Terraform
- Update applications independently via CI/CD
- Destroy and recreate infrastructure without manual intervention

## API Endpoints

### `GET /health`
Health check endpoint. Returns service status and Redis connectivity.

### `POST /check`
Evaluate security risk for a given asset configuration.

**Request:**
```json
{
  "os": "ubuntu",
  "public_ip": true,
  "open_ports": [
    {"port": 22, "protocol": "tcp", "exposed_to_internet": true}
  ]
}
```

**Response:**
```json
{
  "request_id": "...",
  "score": 75,
  "issues": ["SSH port 22 exposed to internet"],
  "recommendations": ["Use SSH key authentication", "Restrict SSH access by IP"]
}
```

### `GET /check/{request_id}`
Retrieve a previously computed result by request ID.

### `POST /scan`
Run nmap scan against a target host and evaluate risk.

**Request:**
```json
{
  "target": "scanme.nmap.org",
  "public_ip": true
}
```

**Response:**
```json
{
  "target": "scanme.nmap.org",
  "detected_os": "Linux",
  "asset": {...},
  "risk": {...},
  "raw_nmap_output": "..."
}
```

## Project Structure

```
.
├── infra/                    # Terraform infrastructure code
│   ├── main.tf              # Core resources (RG, ACR, Redis, etc.)
│   ├── container_apps.tf    # Container Apps definitions
│   ├── variables.tf         # Variable definitions
│   ├── outputs.tf           # Output values
│   ├── terraform.tfvars     # Variable values (not in git)
│   └── deploy.sh            # Helper script for Terraform
├── security-service/        # Backend API
│   ├── app/                 # FastAPI application code
│   ├── docker-compose.yml   # Local development setup
│   └── Dockerfile           # Container image definition
├── security-frontend/       # Frontend UI
│   ├── src/                 # Next.js application code
│   └── Dockerfile           # Container image definition
└── .github/workflows/       # GitHub Actions CI/CD
    ├── backend-container-apps.yml
    └── frontend-container-apps.yml
```

## Development

### Backend

```bash
cd security-service
# Install dependencies
pip install -r requirements.txt

# Run locally (without Docker)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd security-frontend
# Install dependencies
npm install

# Run development server
npm run dev
```

## Troubleshooting

### Frontend cannot connect to backend

1. Verify backend URL is correct in GitHub secret `NEXT_PUBLIC_API_BASE_URL`
2. Check CORS configuration in backend (should include frontend URL)
3. Verify both Container Apps are running: `az containerapp list`

### Redis connection errors

- **Local**: Ensure Redis container is running (`docker compose ps`)
- **Azure**: Check Redis connection string and firewall rules

### Container App not updating

- Verify GitHub Actions workflow completed successfully
- Check Container App revision: `az containerapp revision list`
- View logs: `az containerapp logs show`

