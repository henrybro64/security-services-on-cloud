from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Port(BaseModel):
    """Represents an open port on an asset."""
    port: int                   # e.g., 22, 3389, 80
    protocol: str               # e.g., "tcp" or "udp"
    exposed_to_internet: bool   # whether it's publicly accessible

class AssetInfo(BaseModel):
    """Request body for a security evaluation."""
    os: str                     # e.g., "ubuntu", "windows"
    public_ip: bool             # does the asset have a public IP?
    open_ports: List[Port]      # list of network ports


class IpReputation(BaseModel):
    score: int                     # 0–100 from provider
    is_malicious: bool
    categories: List[str] = []
    source: str = "AbuseIPDB"
    raw: Optional[Dict[str, Any]] = None  # raw provider payload

class RiskResult(BaseModel):
    """Response object representing a security evaluation result."""
    request_id: str             # unique hash based on request body
    score: int                  # 0-100 security score
    issues: List[str]           # list of discovered problems
    recommendations: List[str]  # remediation suggestions
    ip_reputation: Optional[IpReputation] = None






# ... existing Port, AssetInfo, RiskResult ...

class ScanRequest(BaseModel):
    """
    Input for an active scan.
    - target: IP or hostname
    - os_hint: optional hint if we can't fingerprint OS reliably
    """
    target: str
    os_hint: Optional[str] = None
    public_ip: bool = True  # assume public-facing by default


class ScanResponse(BaseModel):
    """
    Output of an active scan:
    - detected_os: what we think it is (best effort)
    - asset: derived AssetInfo (OS + public_ip + open_ports)
    - risk: RiskResult from your rule engine
    """
    target: str
    detected_os: str
    asset: AssetInfo
    risk: RiskResult
    raw_nmap_output: Optional[str] = None