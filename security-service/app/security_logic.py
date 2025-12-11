import hashlib
import json
from typing import List, Tuple

from .models import AssetInfo

def compute_request_id(asset: AssetInfo) -> str:
    """
    Compute a deterministic ID based on the request content.
    This is used as the Redis key so identical requests hit the cache.
    """
    # Sort keys to ensure stable JSON output
    data_dict = asset.model_dump()
    data = json.dumps(data_dict, sort_keys=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def evaluate_risk(asset: AssetInfo) -> Tuple[int, List[str], List[str]]:
    """
    Very simple, rule-based risk engine.


    Returns:
        score (int): 0–100 where 100 is best.
        issues (List[str]): human-readable problems.
        recommendations (List[str]): suggested remediations.
    """
    issues: List[str] = []
    recs: List[str] = []
    # -----------------------------
    # Example rules (you can expand)
    # -----------------------------

    # Rule 1: Public IP
    if asset.public_ip:
        issues.append("Asset has a public IP address.")
        recs.append("Place asset behind a firewall, reverse proxy, or VPN if possible.")

    # Rule 2: Dangerous ports exposed to the internet
    sensitive_ports = {22: "SSH", 3389: "RDP", 5900: "VNC"}

    for p in asset.open_ports:
        if p.port in sensitive_ports and p.exposed_to_internet:
            svc = sensitive_ports[p.port]
            issues.append(f"{svc} port {p.port} is exposed to the internet.")
            recs.append(
                f"Restrict external access to {svc} (port {p.port}) via VPN, jump host, "
                "or IP-based allowlists."
            )

        # Example: HTTP without TLS and public
        if p.port == 80 and p.exposed_to_internet:
            issues.append("HTTP (port 80) is exposed without TLS.")
            recs.append("Prefer HTTPS (port 443) with a valid TLS certificate.")

    # Rule 3: OS hints (very naive – just for demo)
    os_lower = asset.os.lower()
    if "windows" in os_lower:
        recs.append("Ensure regular patching and enable Windows Defender / EDR.")
    elif "ubuntu" in os_lower or "linux" in os_lower:
        recs.append("Keep packages updated and disable unnecessary services.")

    # -----------------------------
    # Score calculation (simple)
    # -----------------------------
    base_score = 100

    # Each issue reduces score by 15 points, up to a minimum of 0
    penalty_per_issue = 15
    score = max(0, base_score - penalty_per_issue * len(issues))

    return score, issues, recs

