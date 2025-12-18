import os
import re

import pytest
from playwright.sync_api import Browser, Page, Playwright, expect, sync_playwright


FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")


def _launch_browser(playwright_sync: Playwright) -> Browser:
    """
    Launch Chromium with sensible defaults and fallbacks.

    macOS (especially newer releases) can be picky about the bundled
    Chromium build Playwright downloads. We first honor an explicit
    channel via PLAYWRIGHT_CHANNEL, then try the system Chrome build,
    and finally fall back to the bundled Chromium. Headless can be
    toggled with HEADLESS=false for local debugging.
    """

    headless = os.getenv("HEADLESS", "true").lower() == "true"
    preferred_channel = os.getenv("PLAYWRIGHT_CHANNEL")

    launch_kwargs = {
        "headless": headless,
        # Explicitly disable the sandbox to avoid macOS hardening issues.
        "chromium_sandbox": False,
    }

    channels_to_try = []
    if preferred_channel:
        channels_to_try.append(preferred_channel)
    # System Chrome tends to be more stable on macOS; fall back to bundled.
    channels_to_try.extend(["chrome", None])

    last_error: Exception | None = None
    for channel in channels_to_try:
        try:
            if channel:
                return playwright_sync.chromium.launch(channel=channel, **launch_kwargs)
            return playwright_sync.chromium.launch(**launch_kwargs)
        except Exception as exc:  # pragma: no cover - defensive fallback
            last_error = exc
            continue

    raise RuntimeError("Unable to launch Chromium via Playwright") from last_error


@pytest.fixture(scope="session")
def playwright_sync() -> Playwright:
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_sync: Playwright) -> Browser:
    browser = _launch_browser(playwright_sync)
    yield browser
    browser.close()


@pytest.fixture()
def page(browser: Browser) -> Page:
    context = browser.new_context(base_url=FRONTEND_BASE_URL)
    page = context.new_page()
    yield page
    context.close()


def test_manual_config_flow(page: Page):
    page.goto("/", wait_until="networkidle")

    expect(page.get_by_text("CloudHostInspector")).to_be_visible()
    expect(page.get_by_text("Current Result")).to_be_visible()

    page.get_by_label("Operating system").fill("ubuntu")
    page.get_by_label("Host has a public IP").check()
    page.get_by_label("Open ports (one per line, port/protocol/exposure)").fill(
        "22/tcp/public\n443/tcp/public"
    )

    page.get_by_role("button", name="Run config check").click()

    # Wait for the current result to render with a score and request_id
    expect(page.get_by_text("/ 100")).to_be_visible(timeout=15_000)
    expect(page.get_by_text("request_id")).to_be_visible(timeout=15_000)

    # Recent scans section should list the newly created entry
    expect(page.get_by_text("Recent Scans")).to_be_visible()
    # Use the heading to avoid strict-mode multiple matches on "Manual config".
    expect(
        page.get_by_role("heading", name="Manual config")
    ).to_be_visible(timeout=15_000)


def test_scan_host_flow(page: Page):
    """
    Run a real scan against scanme.nmap.org and validate key UI outputs.
    This test depends on the backend being up and able to reach the internet.
    """

    page.goto("/", wait_until="networkidle")

    # Scan host (nmap) form
    page.get_by_label("Target (IP or hostname)").fill("scanme.nmap.org")
    page.get_by_label("Assume host is public-facing").check()
    page.get_by_role("button", name="Run scan").click()

    # Nmap scan plus reputation lookup can take some time; allow up to 2 minutes.
    expect(page.get_by_text("/ 100")).to_be_visible(timeout=120_000)

    expect(page.get_by_text(re.compile(r"request_id:", re.I))).to_be_visible(
        timeout=120_000
    )
    expect(page.get_by_text("Target: scanme.nmap.org")).to_be_visible(timeout=120_000)
    expect(page.get_by_text(re.compile(r"Detected OS:", re.I))).to_be_visible(
        timeout=120_000
    )

    # Risk badge can vary; accept any of the known labels.
    # Use .first() to handle cases where multiple risk badges are present (e.g., "Low risk" and "Clean / Low risk").
    expect(
        page.get_by_text(re.compile(r"(High risk|Medium risk|Low risk)", re.I)).first
    ).to_be_visible(timeout=120_000)

    expect(page.get_by_text("Issues")).to_be_visible(timeout=120_000)

    # IP reputation details
    expect(page.get_by_text("Reputation score: 1/100")).to_be_visible(timeout=120_000)
    expect(page.get_by_text("Clean / Low risk")).to_be_visible(timeout=120_000)
    expect(
        page.get_by_text(re.compile(r"Categories:.*Data Center/Web Hosting/Tran", re.I))
    ).to_be_visible(timeout=120_000)

