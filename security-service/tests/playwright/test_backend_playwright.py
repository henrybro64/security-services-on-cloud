import os
import time
from typing import Dict

import pytest
from playwright.sync_api import Playwright, APIRequestContext, sync_playwright, expect


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")  # optional auth header


def _headers() -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


@pytest.fixture(scope="session")
def playwright_api() -> Playwright:
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def api_client(playwright_api: Playwright) -> APIRequestContext:
    context = playwright_api.request.new_context(base_url=API_BASE_URL, extra_http_headers=_headers())
    yield context
    context.dispose()


def test_health(api_client: APIRequestContext):
    resp = api_client.get("/health")
    assert resp.ok, f"Health check failed: {resp.status} {resp.text()}"
    data = resp.json()
    assert data.get("status") == "ok"
    assert "version" in data


def test_check_and_fetch_by_id(api_client: APIRequestContext):
    payload = {
        "os": "ubuntu",
        "public_ip": True,
        "open_ports": [
            {"port": 22, "protocol": "tcp", "exposed_to_internet": True},
            {"port": 443, "protocol": "tcp", "exposed_to_internet": True},
        ],
    }

    create = api_client.post("/check", data=payload)
    assert create.ok, f"/check failed: {create.status} {create.text()}"
    result = create.json()
    request_id = result.get("request_id")
    assert request_id, "request_id missing from /check response"

    # Fetch by id and ensure same request_id and score present
    fetch = api_client.get(f"/check/{request_id}")
    assert fetch.ok, f"/check/{{id}} failed: {fetch.status} {fetch.text()}"
    fetched = fetch.json()
    assert fetched.get("request_id") == request_id
    assert isinstance(fetched.get("score"), (int, float))

    # Calling /check again with same payload should hit cache and return same id
    repeat = api_client.post("/check", data=payload)
    assert repeat.ok, f"repeat /check failed: {repeat.status} {repeat.text()}"
    repeat_id = repeat.json().get("request_id")
    assert repeat_id == request_id


@pytest.mark.timeout(90)
def test_scan_endpoint(api_client: APIRequestContext):
    """
    Exercises /scan which runs nmap. Uses a well-known scan target.
    """
    scan_body = {
        "target": "scanme.nmap.org",
        "public_ip": True,
    }

    start = time.time()
    resp = api_client.post("/scan", data=scan_body, timeout=80_000)
    duration = time.time() - start
    assert resp.ok, f"/scan failed in {duration:.1f}s: {resp.status} {resp.text()}"

    data = resp.json()
    assert data.get("target"), "target missing in /scan response"
    risk = data.get("risk")
    assert risk and isinstance(risk.get("score"), (int, float)), "risk score missing from /scan response"
    assert "request_id" in risk


