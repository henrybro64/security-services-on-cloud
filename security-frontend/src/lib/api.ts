export type PortInput = {
  port: number;
  protocol: string;
  exposed_to_internet: boolean;
};

export type CheckRequest = {
  os: string;
  public_ip: boolean;
  open_ports: PortInput[];
};

export type IpReputation = {
  score: number;
  is_malicious: boolean;
  categories: string[];
  source: string;
};

export type RiskResult = {
  request_id: string;
  score: number;
  issues: string[];
  recommendations: string[];
  ip_reputation?: IpReputation;
};

export type ScanHostRequest = {
  target: string;
  os_hint?: string | null;
  public_ip?: boolean;
};

export type ScanHostResponse = {
  target: string;
  detected_os: string;
  asset: {
    os: string;
    public_ip: boolean;
    open_ports: PortInput[];
  };
  risk: RiskResult;
  raw_nmap_output?: string | null;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function runSecurityCheck(
  payload: CheckRequest
): Promise<RiskResult> {
  const res = await fetch(`${API_BASE_URL}/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(
      `Backend error ${res.status}: ${text || res.statusText || "Unknown"}`
    );
  }

  return res.json();
}

export async function runHostScan(
  payload: ScanHostRequest
): Promise<ScanHostResponse> {
  const res = await fetch(`${API_BASE_URL}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(
      `Backend error ${res.status}: ${text || res.statusText || "Unknown"}`
    );
  }

  return res.json();
}
