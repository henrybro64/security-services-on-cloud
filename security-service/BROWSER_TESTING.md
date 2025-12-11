# Browser Testing Guide

## Quick Start

Your security service is running and accessible at **http://localhost:8000**

## Method 1: Swagger UI (Recommended - Easiest)

### Step 1: Open Swagger UI
1. Open your web browser (Chrome, Firefox, Safari, etc.)
2. Navigate to: **http://localhost:8000/docs**

### Step 2: Explore the API
You'll see a page with all available endpoints:
- **GET /health** - Health check endpoint
- **POST /check** - Security evaluation endpoint
- **GET /check/{request_id}** - Retrieve cached result

### Step 3: Test the Health Endpoint
1. Find the **GET /health** endpoint
2. Click on it to expand
3. Click the **"Try it out"** button
4. Click the **"Execute"** button
5. Scroll down to see the response

**Expected Response:**
```json
{
  "status": "ok",
  "redis": "up",
  "version": "0.1.0"
}
```

### Step 4: Test the Security Check Endpoint
1. Find the **POST /check** endpoint
2. Click on it to expand
3. Click the **"Try it out"** button
4. You'll see a request body editor with example JSON
5. Replace the example with this test case:

```json
{
  "os": "ubuntu",
  "public_ip": true,
  "open_ports": [
    {
      "port": 22,
      "protocol": "tcp",
      "exposed_to_internet": true
    },
    {
      "port": 80,
      "protocol": "tcp",
      "exposed_to_internet": true
    }
  ]
}
```

6. Click the **"Execute"** button
7. Scroll down to see the response with:
   - `request_id`: A unique hash
   - `score`: Security score (0-100)
   - `issues`: List of security problems found
   - `recommendations`: Suggested fixes

### Step 5: Test Different Scenarios

**Scenario A: High Risk (Public IP + Dangerous Ports)**
```json
{
  "os": "windows",
  "public_ip": true,
  "open_ports": [
    {
      "port": 3389,
      "protocol": "tcp",
      "exposed_to_internet": true
    },
    {
      "port": 22,
      "protocol": "tcp",
      "exposed_to_internet": true
    }
  ]
}
```

**Scenario B: Low Risk (Private, Secure)**
```json
{
  "os": "ubuntu",
  "public_ip": false,
  "open_ports": [
    {
      "port": 443,
      "protocol": "tcp",
      "exposed_to_internet": false
    }
  ]
}
```

**Scenario C: Medium Risk (Public but HTTPS only)**
```json
{
  "os": "ubuntu",
  "public_ip": true,
  "open_ports": [
    {
      "port": 443,
      "protocol": "tcp",
      "exposed_to_internet": true
    }
  ]
}
```

### Step 6: Test Caching
1. Run the same POST /check request twice
2. Notice that both responses have the same `request_id`
3. Copy the `request_id` from the response
4. Find the **GET /check/{request_id}** endpoint
5. Click **"Try it out"**
6. Paste the `request_id` into the `request_id` field
7. Click **"Execute"**
8. You should get the same result (cached from Redis)

## Method 2: ReDoc (Alternative Documentation)

1. Navigate to: **http://localhost:8000/redoc**
2. This provides a cleaner, more readable documentation view
3. You can read the API documentation, but you'll need to use Swagger UI or another tool to actually make requests

## Method 3: Direct Browser Testing (GET requests only)

### Health Check
Simply open in your browser:
**http://localhost:8000/health**

You'll see the JSON response directly in your browser.

### Get Cached Result
1. First, make a POST request using Swagger UI to get a `request_id`
2. Then open in your browser:
   **http://localhost:8000/check/{request_id}**
   
   Replace `{request_id}` with the actual ID from step 1.

## Tips

1. **Swagger UI is interactive** - You can test all endpoints without leaving your browser
2. **Request/Response examples** - Swagger shows example requests and responses
3. **Schema validation** - Swagger validates your JSON before sending
4. **Copy responses** - You can copy the response JSON for further analysis
5. **Try different combinations** - Experiment with different OS types, ports, and configurations

## Troubleshooting

**If you see "This site can't be reached":**
- Make sure Docker containers are running: `docker-compose ps`
- Check if port 8000 is available: `lsof -i :8000`
- Restart the service: `docker-compose restart api`

**If you see errors in Swagger UI:**
- Check the browser console (F12) for errors
- Check service logs: `docker-compose logs api`
- Verify Redis is running: `docker-compose ps`

**If responses are slow:**
- Check Redis connection in the health endpoint
- View logs: `docker-compose logs -f api`

## Visual Guide

```
Browser → http://localhost:8000/docs
         ↓
    Swagger UI Page
         ↓
    [GET /health] ← Click to expand
         ↓
    [Try it out] ← Click button
         ↓
    [Execute] ← Click button
         ↓
    View Response ← Scroll down
```

Enjoy testing your security service! 🚀

