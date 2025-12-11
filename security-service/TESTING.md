# Testing Guide for Security Service

## Quick Start

1. **Start the service:**
   ```bash
   docker-compose up -d
   ```

2. **Check service status:**
   ```bash
   docker-compose ps
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f api
   ```

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Test:**
```bash
curl http://localhost:8000/health | python3 -m json.tool
```

**Expected Response:**
```json
{
    "status": "ok",
    "redis": "up",
    "version": "0.1.0"
}
```

### 2. Security Check (POST)

**Endpoint:** `POST /check`

**Test Cases:**

#### Test Case 1: High Risk Asset
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
  }' | python3 -m json.tool
```

**Expected:** Score < 100, multiple issues detected

#### Test Case 2: Low Risk Asset (Private)
```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{
    "os": "ubuntu",
    "public_ip": false,
    "open_ports": [
      {"port": 443, "protocol": "tcp", "exposed_to_internet": false}
    ]
  }' | python3 -m json.tool
```

**Expected:** Score = 100, no issues

#### Test Case 3: Windows Server with RDP
```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{
    "os": "windows",
    "public_ip": true,
    "open_ports": [
      {"port": 3389, "protocol": "tcp", "exposed_to_internet": true}
    ]
  }' | python3 -m json.tool
```

**Expected:** Score < 100, RDP exposure issue detected

#### Test Case 4: Test Caching
Run the same request twice and verify the `request_id` is identical:
```bash
# First request
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{
    "os": "ubuntu",
    "public_ip": true,
    "open_ports": [{"port": 22, "protocol": "tcp", "exposed_to_internet": true}]
  }' | python3 -m json.tool

# Second request (should be cached)
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{
    "os": "ubuntu",
    "public_ip": true,
    "open_ports": [{"port": 22, "protocol": "tcp", "exposed_to_internet": true}]
  }' | python3 -m json.tool
```

**Expected:** Both return the same `request_id` (cache hit on second request)

### 3. Retrieve Cached Result (GET)

**Endpoint:** `GET /check/{request_id}`

**Test:**
```bash
# First, get a request_id from a POST request
REQUEST_ID=$(curl -s -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{
    "os": "ubuntu",
    "public_ip": true,
    "open_ports": [{"port": 22, "protocol": "tcp", "exposed_to_internet": true}]
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['request_id'])")

# Then retrieve it
curl http://localhost:8000/check/$REQUEST_ID | python3 -m json.tool
```

**Expected:** Returns the same result as the original POST

**Test Non-existent ID:**
```bash
curl http://localhost:8000/check/nonexistent123
```

**Expected:** 404 error

## Using HTTPie (Alternative to curl)

If you have `httpie` installed:

```bash
# Health check
http GET http://localhost:8000/health

# Security check
http POST http://localhost:8000/check \
  os=ubuntu \
  public_ip:=true \
  open_ports:='[{"port": 22, "protocol": "tcp", "exposed_to_internet": true}]'
```

## Using Python Requests

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Security check
payload = {
    "os": "ubuntu",
    "public_ip": True,
    "open_ports": [
        {"port": 22, "protocol": "tcp", "exposed_to_internet": True},
        {"port": 80, "protocol": "tcp", "exposed_to_internet": True}
    ]
}
response = requests.post("http://localhost:8000/check", json=payload)
print(response.json())

# Get cached result
request_id = response.json()["request_id"]
cached_response = requests.get(f"http://localhost:8000/check/{request_id}")
print(cached_response.json())
```

## Using the Interactive API Docs

FastAPI provides automatic interactive documentation:

1. **Swagger UI:** http://localhost:8000/docs
2. **ReDoc:** http://localhost:8000/redoc

You can test all endpoints directly from your browser!

## Testing Redis Cache

Verify Redis is working:

```bash
# Connect to Redis container
docker-compose exec redis redis-cli

# Inside Redis CLI:
KEYS *
GET <request_id_from_previous_test>
TTL <request_id>
```

## Common Test Scenarios

### Scenario 1: Secure Configuration
- Private IP
- Only HTTPS (443) exposed
- Modern OS

**Expected:** High score (100), minimal issues

### Scenario 2: Insecure Configuration
- Public IP
- SSH (22) exposed to internet
- RDP (3389) exposed to internet
- HTTP (80) without TLS

**Expected:** Low score (< 40), multiple issues and recommendations

### Scenario 3: Mixed Configuration
- Public IP
- HTTPS (443) only
- No dangerous ports

**Expected:** Medium score (~85), public IP warning

## Troubleshooting

1. **Service not responding:**
   ```bash
   docker-compose logs api
   docker-compose ps
   ```

2. **Redis connection issues:**
   ```bash
   docker-compose logs redis
   docker-compose exec redis redis-cli ping
   ```

3. **Rebuild after code changes:**
   ```bash
   docker-compose up -d --build
   ```

4. **Clear Redis cache:**
   ```bash
   docker-compose exec redis redis-cli FLUSHDB
   ```


