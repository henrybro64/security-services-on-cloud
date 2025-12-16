# Security Service API

FastAPI-based backend service for infrastructure security assessment. Evaluates security risks by analyzing host configurations, performing port scans, and checking IP reputation.

## Features

- **Security Risk Assessment**: Evaluates infrastructure security based on OS, open ports, and network exposure
- **Host Scanning**: Automated nmap-based port scanning and OS detection
- **IP Reputation**: Integration with AbuseIPDB for IP reputation checks
- **Result Caching**: Redis-backed caching to avoid redundant computations
- **RESTful API**: FastAPI with automatic OpenAPI/Swagger documentation
- **Authentication**: Optional API key-based authentication

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- Redis (included in docker-compose.yml)
- nmap (installed in Docker image, required for host scanning)
- (Optional) AbuseIPDB API key for IP reputation checks

## Local Development

### Using Docker Compose (Recommended)

The easiest way to run the service locally:

```bash
# Start API and Redis
docker compose up --build

# Or run in detached mode
docker compose up -d --build
```

The API will be available at `http://localhost:8000`

### Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Redis:**
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:7-alpine
   ```

3. **Configure environment variables:**
   Create a `.env` file (optional):
   ```bash
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_SSL=false
   ABUSEIPDB_API_KEY=your_api_key_here
   API_KEY=your_api_key_here
   ```

4. **Run the service:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_HOST` | Redis server hostname | `localhost` | No |
| `REDIS_PORT` | Redis server port | `6379` | No |
| `REDIS_SSL` | Enable SSL for Redis | `false` | No |
| `REDIS_PASSWORD` | Redis password (if required) | - | No |
| `ABUSEIPDB_API_KEY` | AbuseIPDB API key for IP reputation | - | No |
| `API_KEY` | API key for authentication (disables auth if not set) | - | No |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:3000` | No |
| `PORT` | Server port | `8000` | No |

### Redis Configuration

For local development, Redis runs in Docker Compose without authentication.

For Azure deployment, Redis uses SSL and requires a password. These are automatically configured by Terraform.

## API Endpoints

### `GET /health`
Health check endpoint. Returns service status and Redis connectivity.

**Response:**
```json
{
  "status": "ok",
  "redis": "up",
  "version": "0.1.0"
}
```

### `POST /check`
Evaluate security risk for a given asset configuration.

**Request:**
```json
{
  "os": "ubuntu",
  "public_ip": true,
  "open_ports": [
    {
      "port": 22,
      "protocol": "tcp",
      "exposed_to_internet": true
    }
  ]
}
```

**Response:**
```json
{
  "request_id": "abc123...",
  "score": 75,
  "issues": [
    "SSH port 22 exposed to internet"
  ],
  "recommendations": [
    "Use SSH key authentication",
    "Restrict SSH access by IP"
  ]
}
```

### `GET /check/{request_id}`
Retrieve a previously computed result by request ID. Results are cached in Redis for 1 hour.

### `POST /scan`
Run nmap scan against a target host and evaluate risk.

**Request:**
```json
{
  "target": "scanme.nmap.org",
  "public_ip": true,
  "os_hint": "linux"
}
```

**Response:**
```json
{
  "target": "scanme.nmap.org",
  "detected_os": "Linux",
  "asset": {
    "os": "linux",
    "public_ip": true,
    "open_ports": [...]
  },
  "risk": {
    "request_id": "...",
    "score": 80,
    "issues": [...],
    "recommendations": [...],
    "ip_reputation": {...}
  },
  "raw_nmap_output": "..."
}
```

### Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## Project Structure

```
security-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and routes
│   ├── models.py             # Pydantic models for requests/responses
│   ├── security_logic.py     # Risk evaluation engine
│   ├── redis_client.py       # Redis connection and caching
│   ├── nmap_adapter.py       # nmap scanning integration
│   └── ip_reputation.py      # AbuseIPDB integration
├── docker-compose.yml        # Local development setup
├── Dockerfile                # Container image definition
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Building the Docker Image

```bash
docker build -t security-service:latest .
```

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Manual Security Check
```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{
    "os": "ubuntu",
    "public_ip": true,
    "open_ports": [
      {"port": 22, "protocol": "tcp", "exposed_to_internet": true}
    ]
  }'
```

### Host Scan
```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "scanme.nmap.org"}'
```

### With API Key (if configured)
```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{...}'
```

## Deployment

### Azure Container Apps

The service is deployed to Azure Container Apps via Terraform and GitHub Actions.

1. **Infrastructure**: Terraform creates the Container App with placeholder image
2. **CI/CD**: GitHub Actions builds the Docker image and pushes to Azure Container Registry
3. **Update**: GitHub Actions updates the Container App with the new image

See the root `README.md` for complete deployment instructions.

### Environment Variables in Azure

The following environment variables are automatically configured by Terraform:
- `REDIS_HOST`: Azure Redis Cache hostname
- `REDIS_PORT`: Azure Redis Cache SSL port
- `REDIS_SSL`: Set to `true`
- `REDIS_PASSWORD`: Retrieved from Azure Key Vault/Redis
- `CORS_ORIGINS`: Frontend Container App URL

You must manually configure:
- `ABUSEIPDB_API_KEY`: Set via Azure Portal or `az containerapp update`

## Caching Strategy

Results are cached in Redis using a deterministic `request_id` based on the asset configuration:
- Same configuration → same `request_id` → cached result
- Cache TTL: 1 hour (3600 seconds)
- Cache key: `request_id` (SHA256 hash of asset config)

## Security Considerations

- API key authentication is optional (disabled if `API_KEY` not set)
- CORS is configured to allow requests from the frontend
- Redis connections use SSL in production (Azure)
- nmap scans run in isolated threads to prevent blocking

## Troubleshooting

### Redis Connection Errors

**Local:**
```bash
# Check if Redis is running
docker compose ps

# View Redis logs
docker compose logs redis
```

**Azure:**
- Verify Redis connection string in Container App environment variables
- Check Redis firewall rules allow Container App subnet
- Verify Redis password is correctly set

### nmap Not Found

nmap is installed in the Docker image. If running manually, install:
```bash
# Ubuntu/Debian
sudo apt-get install nmap

# macOS
brew install nmap
```

### API Key Authentication Not Working

- Verify `API_KEY` environment variable is set
- Check request includes `X-API-Key` header
- If `API_KEY` is not set, authentication is disabled
