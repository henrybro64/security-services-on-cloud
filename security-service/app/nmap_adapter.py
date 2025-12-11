import subprocess
import logging
from typing import List, Tuple

from .models import Port, AssetInfo, ScanRequest

logger = logging.getLogger("security-service.nmap")


def run_nmap_scan(scan_req: ScanRequest) -> Tuple[AssetInfo, str, str]:
    """
    Run nmap against the given target and convert the result into AssetInfo.

    Returns:
        asset: AssetInfo with open ports + OS guess
        detected_os: our best guess at OS (string)
        raw_output: full nmap stdout (for debugging)
    """
    target = scan_req.target

    # -Pn : no host discovery (treat host as up)
    # -F  : fast scan (top ports)
    # -O  : try OS detection (may need elevated privileges in some environments)
    cmd = ["nmap", "-Pn", "-F", "-O", target]

    logger.info("Running nmap: %s", " ".join(cmd))

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if proc.returncode not in (0, 1):  # 1 often means "some info" but not fatal
        logger.error(
            "nmap failed (rc=%s): stderr=%s", proc.returncode, proc.stderr.strip()
        )
        raise RuntimeError(
            f"nmap scan failed: {proc.stderr.strip() or proc.stdout.strip()}"
        )

    raw_output = proc.stdout
    ports: List[Port] = []
    detected_os = scan_req.os_hint or "unknown"

    # ------------------------------------------------------------------
    # Parse ports from standard nmap output
    # Example lines:
    # PORT   STATE SERVICE
    # 22/tcp open  ssh
    # 80/tcp open  http
    # ------------------------------------------------------------------
    in_port_section = False
    for line in raw_output.splitlines():
        line = line.strip()

        if line.startswith("PORT"):
            in_port_section = True
            continue

        if in_port_section:
            if not line or line.startswith("Nmap done:"):
                break

            parts = line.split()
            # Expect something like ["22/tcp", "open", "ssh"]
            if len(parts) < 2:
                continue

            port_proto, state = parts[0], parts[1]
            if "/tcp" in port_proto:
                proto = "tcp"
                port_str = port_proto.split("/")[0]
            elif "/udp" in port_proto:
                proto = "udp"
                port_str = port_proto.split("/")[0]
            else:
                continue

            if state != "open":
                continue

            try:
                port_num = int(port_str)
            except ValueError:
                continue

            ports.append(
                Port(
                    port=port_num,
                    protocol=proto,
                    exposed_to_internet=True,  # by definition: remote scan
                )
            )

    # ------------------------------------------------------------------
    # Very naive OS fingerprint parsing:
    # look for "OS details:" or "Running:" lines
    # ------------------------------------------------------------------
    for line in raw_output.splitlines():
        line = line.strip()
        if line.startswith("OS details:"):
            detected_os = line.replace("OS details:", "").strip()
            break
        if line.startswith("Running:") and detected_os == "unknown":
            detected_os = line.replace("Running:", "").strip()

    if detected_os == "unknown" and scan_req.os_hint:
        detected_os = scan_req.os_hint

    if detected_os == "unknown":
        logger.info("Could not fingerprint OS for target=%s", target)
    else:
        logger.info("Detected OS for target=%s: %s", target, detected_os)

    asset = AssetInfo(
        os=detected_os,
        public_ip=scan_req.public_ip,
        open_ports=ports,
    )

    logger.info(
        "nmap scan parsed: target=%s, open_ports=%s",
        target,
        [p.port for p in ports],
    )

    return asset, detected_os, raw_output
