import os
from typing import Optional

import httpx

from .models import IpReputation

ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY")


async def check_ip_reputation(ip: str) -> Optional[IpReputation]:
    """
    Look up IP reputation using AbuseIPDB.
    Returns IpReputation or None if lookup fails / key not set.
    """
    if not ABUSEIPDB_API_KEY:
        return None

    url = "https://api.abuseipdb.com/api/v2/check"
    params = {
        "ipAddress": ip,
        "maxAgeInDays": 90,
    }
    headers = {
        "Key": ABUSEIPDB_API_KEY,
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()["data"]
    except Exception as exc:
        # Don't break scan if reputation lookup fails
        print(f"[ip_reputation] lookup failed for {ip}: {exc}")
        return None

    abuse_score = int(data.get("abuseConfidenceScore", 0))
    is_malicious = abuse_score >= 50

    usage_type = data.get("usageType") or ""
    categories = [usage_type] if usage_type else []

    return IpReputation(
        score=abuse_score,
        is_malicious=is_malicious,
        categories=categories,
        source="AbuseIPDB",
        raw=data,
    )
