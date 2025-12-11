from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import json
import logging
import os

from .models import AssetInfo, RiskResult, ScanRequest, ScanResponse
from .security_logic import compute_request_id, evaluate_risk
from .redis_client import get_redis_client
from .nmap_adapter import run_nmap_scan
from .ip_reputation import check_ip_reputation


# -----------------------------------------------------------------------------

# App & Logging Setup

# -----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("security-service")

app = FastAPI(
title="Security Config Checker",
description="Prototype security service using FastAPI + Redis, deployable on Azure.",
version="0.1.0",
)

# CORS configuration - supports environment variable for allowed origins
# Defaults to localhost:3000 for local dev, but can be overridden via CORS_ORIGINS env var
# For K8s, set CORS_ORIGINS to your frontend URL(s), e.g., "https://example.com,https://www.example.com"
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Root redirect to docs
# -----------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect bare / to interactive API docs."""
    return RedirectResponse(url="/docs")

# Single Redis client instance for the whole app process

redis_client = get_redis_client()

# -----------------------------------------------------------------------------

# Basic Endpoints

# -----------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """
    Simple health endpoint to verify the API is running.
    Useful for Azure health probes and debugging.
    """
    try:
        # Optional: ping Redis as part of health
        redis_client.ping()
        redis_status = "up"
    except Exception as e:
        logger.warning("Redis health check failed: %s", e)
        redis_status = "down"
    
    return {
        "status": "ok",
        "redis": redis_status,
        "version": "0.1.0",
    }
    

# -----------------------------------------------------------------------------

# Security Check Endpoints

# -----------------------------------------------------------------------------

@app.post("/check", response_model=RiskResult)
def check_security(asset: AssetInfo):
    """
    Evaluate risk for a given asset configuration.

    - Generates a deterministic request_id based on the request body.
    - Tries to return cached result from Redis if available.
    - Otherwise, computes a fresh result, stores it in Redis, and returns it.
    """
    request_id = compute_request_id(asset)
    logger.info("Received /check request_id=%s", request_id)

    # 1. Attempt to fetch from Redis cache
    try:
        cached = redis_client.get(request_id)
    except Exception as e:
        logger.error("Error talking to Redis: %s", e)
        cached = None

    if cached:
        logger.info("Cache hit for request_id=%s", request_id)
        data = json.loads(cached)
        return RiskResult(**data)

    # 2. No cache → compute fresh
    score, issues, recs = evaluate_risk(asset)
    result = RiskResult(
        request_id=request_id,
        score=score,
        issues=issues,
        recommendations=recs,
    )

    # 3. Store result in Redis with TTL (e.g., 1 hour)
    try:
        redis_client.setex(request_id, 3600, result.model_dump_json())
        logger.info("Stored result in Redis for request_id=%s", request_id)
    except Exception as e:
        logger.error("Failed to store result in Redis: %s", e)

    return result


@app.get("/check/{request_id}", response_model=RiskResult)
def get_check_result(request_id: str):
    """
    Retrieve a previously computed result by request_id from Redis.
    """
    try:
        cached = redis_client.get(request_id)
    except Exception as e:
        logger.error("Error talking to Redis: %s", e)
        raise HTTPException(status_code=500, detail="Error accessing cache")
    
    if not cached:
        raise HTTPException(status_code=404, detail="Result not found or expired")

    return RiskResult(**json.loads(cached))



@app.post("/scan", response_model=ScanResponse)
async def scan_and_check(scan_req: ScanRequest):
    """
    Run nmap against the target, derive AssetInfo, and evaluate risk.
    Uses the existing rule engine, so you don't have to manually enter ports.
    """
    try:
        # run_nmap_scan returns (AssetInfo, detected_os, raw_output)
        asset, detected_os, raw_output = run_nmap_scan(scan_req)
    except Exception as e:
        logger.error("nmap scan failed: %s", e)
        raise HTTPException(status_code=500, detail=f"nmap scan failed: {e}")

    # Reuse your existing logic
    request_id = compute_request_id(asset)
    score, issues, recs = evaluate_risk(asset)
    
    # Check IP reputation
    ip_rep = await check_ip_reputation(scan_req.target)
    
    # Adjust risk based on IP reputation
    if ip_rep:
        if ip_rep.is_malicious:
            # Reduce score for malicious IPs
            score = max(0, score - 15)
            issues.append(
                f"IP reputation service flags this IP as risky (score {ip_rep.score})."
            )
            recs.append(
                "Investigate this IP in your SIEM/EDR and restrict access if not expected."
            )
    
    risk = RiskResult(
        request_id=request_id,
        score=score,
        issues=issues,
        recommendations=recs,
        ip_reputation=ip_rep.model_dump() if ip_rep else None,
    )

    return ScanResponse(
        target=scan_req.target,
        detected_os=detected_os,
        asset=asset,
        risk=risk,
        raw_nmap_output=raw_output,
    )
