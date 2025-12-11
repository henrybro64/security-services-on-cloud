"use client";

import React, {
  FormEvent,
  useState,
  ChangeEvent,
  useEffect,
} from "react";
import {
  runSecurityCheck,
  runHostScan,
  CheckRequest,
  RiskResult,
  PortInput,
} from "../lib/api";

import {
  Grid,
  Column,
  TextInput,
  Checkbox,
  TextArea,
  Button,
  InlineLoading,
  Tile,
  Tag,
} from "@carbon/react";

type RecentItem = {
  source: "scan" | "manual";
  createdAt: string;
  risk: RiskResult;
  target?: string;
  detectedOs?: string;
};

export default function HomePage() {
  // --- Shared result state ---
  const [riskResult, setRiskResult] = useState<RiskResult | null>(null);
  const [currentTarget, setCurrentTarget] = useState<string | null>(null);
  const [currentDetectedOs, setCurrentDetectedOs] = useState<string | null>(
    null
  );
  const [recent, setRecent] = useState<RecentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // --- Scan host form state ---
  const [scanTarget, setScanTarget] = useState("scanme.nmap.org");
  const [scanPublicIp, setScanPublicIp] = useState(true);

  // --- Manual config form state ---
  const [os, setOs] = useState("ubuntu");
  const [publicIp, setPublicIp] = useState(true);
  const [portsText, setPortsText] = useState("22/tcp/public\n80/tcp/public");

  // Debug: watch riskResult updates
  useEffect(() => {
    console.log("riskResult state changed:", riskResult);
  }, [riskResult]);

  const parsePorts = (text: string): PortInput[] => {
    return text
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [portStr, protocol, exposure] = line.split("/");
        const port = Number(portStr);
        const prot = protocol || "tcp";
        const exposed = (exposure || "public").toLowerCase() === "public";
        return {
          port,
          protocol: prot,
          exposed_to_internet: exposed,
        };
      });
  };

  // ------------------------------------------------------------------
  // Handlers
  // ------------------------------------------------------------------

  const handleScanHost = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setRiskResult(null);
    setCurrentTarget(null);
    setCurrentDetectedOs(null);

    try {
      const res: any = await runHostScan({
        target: scanTarget,
        public_ip: scanPublicIp,
      });

      console.log("scan handler got:", res);

      const risk: RiskResult | undefined = res.risk;
      if (!risk || typeof risk.score !== "number") {
        setError("Scan completed, but backend did not return a risk score.");
        return;
      }

      setRiskResult(risk);
      setCurrentTarget(res.target ?? scanTarget);
      setCurrentDetectedOs(res.detected_os || res.asset?.os || "unknown");

      const item: RecentItem = {
        source: "scan",
        createdAt: new Date().toISOString(),
        risk,
        target: res.target ?? scanTarget,
        detectedOs: res.detected_os || res.asset?.os || "unknown",
      };
      setRecent((prev) => [item, ...prev].slice(0, 10));
    } catch (err: any) {
      console.error(err);
      setError(err.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setRiskResult(null);
    setCurrentTarget(null);
    setCurrentDetectedOs(os);

    try {
      const payload: CheckRequest = {
        os,
        public_ip: publicIp,
        open_ports: parsePorts(portsText),
      };

      const res: any = await runSecurityCheck(payload);
      console.log("manual check response:", res);

      const risk: RiskResult | undefined = res.risk ?? res;
      if (!risk || typeof risk.score !== "number") {
        setError("Config check completed, but backend did not return a risk score.");
        return;
      }

      setRiskResult(risk);

      const item: RecentItem = {
        source: "manual",
        createdAt: new Date().toISOString(),
        risk,
        detectedOs: os,
      };
      setRecent((prev) => [item, ...prev].slice(0, 10));
    } catch (err: any) {
      console.error(err);
      setError(err.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------

  const renderRiskCard = () => {
    if (!riskResult) {
      return (
        <p style={{ fontSize: "0.9rem", color: "#c6c6c6" }}>
          Run a scan or submit a configuration to see the security score and
          findings.
        </p>
      );
    }

    const r = riskResult;

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <div style={{ fontSize: "2.5rem", fontWeight: 600 }}>
              {r.score}
              <span
                style={{
                  fontSize: "1rem",
                  fontWeight: 400,
                  color: "#c6c6c6",
                  marginLeft: 4,
                }}
              >
                / 100
              </span>
            </div>
            <div
              style={{
                fontSize: "0.75rem",
                color: "#a8a8a8",
                wordBreak: "break-all",
              }}
            >
              request_id: {r.request_id}
            </div>
            {currentTarget && (
              <div
                style={{
                  fontSize: "0.8rem",
                  color: "#c6c6c6",
                  marginTop: 4,
                }}
              >
                Target: {currentTarget}
              </div>
            )}
            {currentDetectedOs && (
              <div
                style={{
                  fontSize: "0.8rem",
                  color: "#c6c6c6",
                  marginTop: 2,
                }}
              >
                Detected OS: {currentDetectedOs}
              </div>
            )}
          </div>
          <div>
            {r.score >= 80 ? (
              <Tag type="green">Low risk</Tag>
            ) : r.score >= 50 ? (
              <Tag type="yellow">Medium risk</Tag>
            ) : (
              <Tag type="red">High risk</Tag>
            )}
          </div>
        </div>

        <div>
          <h3 style={{ fontSize: "0.95rem", marginBottom: 4 }}>Issues</h3>
          {r.issues.length === 0 ? (
            <p style={{ color: "#42be65", fontSize: "0.9rem" }}>
              No issues detected.
            </p>
          ) : (
            <ul style={{ paddingLeft: "1.2rem", margin: 0 }}>
              {r.issues.map((issue: string, idx: number) => (
                <li key={idx} style={{ fontSize: "0.9rem" }}>
                  {issue}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3 style={{ fontSize: "0.95rem", marginBottom: 4 }}>
            Recommendations
          </h3>
          <div>
          <h3 style={{ fontSize: "0.95rem", marginBottom: 4 }}>
            IP reputation
          </h3>
          {!r.ip_reputation ? (
            <p style={{ color: "#c6c6c6", fontSize: "0.9rem" }}>
              No IP reputation data available.
            </p>
          ) : (
            <div style={{ fontSize: "0.9rem" }}>
              <div style={{ marginBottom: 4 }}>
                Source: {r.ip_reputation.source}
              </div>
              <div style={{ marginBottom: 4 }}>
                Reputation score: {r.ip_reputation.score}/100{" "}
                {r.ip_reputation.is_malicious ? (
                  <Tag type="red" style={{ marginLeft: 8 }}>
                    Suspicious
                  </Tag>
                ) : (
                  <Tag type="green" style={{ marginLeft: 8 }}>
                    Clean / Low risk
                  </Tag>
                )}
              </div>
              {r.ip_reputation.categories?.length > 0 && (
                <div>
                  Categories:{" "}
                  {r.ip_reputation.categories.join(", ")}
                </div>
              )}
            </div>
          )}
        </div>

          {r.recommendations.length === 0 ? (
            <p style={{ color: "#c6c6c6", fontSize: "0.9rem" }}>
              No recommendations.
            </p>
          ) : (
            <ul style={{ paddingLeft: "1.2rem", margin: 0 }}>
              {r.recommendations.map((rec: string, idx: number) => (
                <li key={idx} style={{ fontSize: "0.9rem" }}>
                  {rec}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="cds--g100">
      <header
        style={{
          padding: "1rem 2rem",
          borderBottom: "1px solid #393939",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: "1.4rem" }}>
            Cloud Security Config Checker
          </h1>
          <p style={{ margin: 0, fontSize: "0.8rem", color: "#c6c6c6" }}>
            Active host scanning · Nmap + FastAPI + Redis · Carbon Design
            System
          </p>
        </div>
      </header>

      <main style={{ padding: "2rem 2rem 3rem 2rem" }}>
        <Grid condensed fullWidth>
          {/* Left column: scan + manual config */}
          <Column lg={6} md={8} sm={4}>
            <Tile style={{ marginBottom: "1.5rem" }}>
              {/* Scan host (nmap) */}
              <h2 className="text-2xl font-semibold mb-2">Scan host (nmap)</h2>
              <p className="text-sm mb-4">
                Run an active scan using nmap against a target host. Results
                will be analyzed for security risks.
              </p>

              <form
                onSubmit={handleScanHost}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "1rem",
                  marginBottom: "2rem",
                }}
              >
                <TextInput
                  id="scan-target"
                  labelText="Target (IP or hostname)"
                  value={scanTarget}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setScanTarget(e.target.value)
                  }
                  helperText='Example: "scanme.nmap.org" or "203.0.113.5"'
                />

                <Checkbox
                  id="scan-public-ip"
                  labelText="Assume host is public-facing"
                  checked={scanPublicIp}
                  onChange={(checked: boolean) => setScanPublicIp(!!checked)}
                />

                {error && (
                  <p
                    style={{
                      color: "#fa4d56",
                      fontSize: "0.85rem",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Error: {error}
                  </p>
                )}

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                  }}
                >
                  <Button type="submit" disabled={loading}>
                    {loading ? "Scanning..." : "Run scan"}
                  </Button>
                  {loading && (
                    <InlineLoading description="Running nmap scan…" />
                  )}
                </div>
              </form>

              {/* Manual config */}
              <h2 className="text-2xl font-semibold mb-2">Manual config</h2>
              <p className="text-sm mb-4">
                Paste configuration details (OS and open ports) to evaluate the
                security posture without running an active scan.
              </p>

              <form
                onSubmit={handleManualSubmit}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "1rem",
                }}
              >
                <TextInput
                  id="os-input"
                  labelText="Operating system"
                  value={os}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setOs(e.target.value)
                  }
                  helperText='Examples: "ubuntu", "windows", "linux"'
                />

                <Checkbox
                  id="manual-public-ip"
                  labelText="Host has a public IP"
                  checked={publicIp}
                  onChange={(checked: boolean) => setPublicIp(!!checked)}
                />

                <TextArea
                  id="ports-input"
                  labelText="Open ports (one per line, port/protocol/exposure)"
                  value={portsText}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                    setPortsText(e.target.value)
                  }
                  rows={6}
                  helperText='Example: "22/tcp/public", "3389/tcp/private"'
                />

                {error && (
                  <p
                    style={{
                      color: "#fa4d56",
                      fontSize: "0.85rem",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Error: {error}
                  </p>
                )}

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                  }}
                >
                  <Button kind="secondary" type="submit" disabled={loading}>
                    {loading ? "Submitting..." : "Run config check"}
                  </Button>
                  {loading && (
                    <InlineLoading description="Evaluating config…" />
                  )}
                </div>
              </form>
            </Tile>
          </Column>

          {/* Right column: current result + recent scans */}
          <Column lg={10} md={8} sm={4}>
            <Tile style={{ marginBottom: "1.5rem" }}>
              <h2 style={{ marginBottom: "1rem" }}>Current Result</h2>
              {renderRiskCard()}
            </Tile>

            <Tile>
              <h2 style={{ marginBottom: "1rem" }}>Recent Scans</h2>
              {recent.length === 0 && (
                <p style={{ fontSize: "0.9rem", color: "#c6c6c6" }}>
                  No scans yet. Run one in the left panel.
                </p>
              )}
              {recent.length > 0 && (
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {recent.map((item) => (
                    <li
                      key={item.risk.request_id + item.createdAt}
                      style={{
                        borderBottom: "1px solid #393939",
                        padding: "0.5rem 0",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: 16,
                      }}
                    >
                      <div>
                        <div
                          style={{
                            fontSize: "0.95rem",
                            fontWeight: 500,
                          }}
                        >
                          {item.source === "scan"
                            ? `Scan: ${item.target}`
                            : "Manual config"}
                        </div>
                        <div
                          style={{
                            fontSize: "0.75rem",
                            color: "#a8a8a8",
                          }}
                        >
                          {new Date(item.createdAt).toLocaleString()}
                        </div>
                        {item.detectedOs && (
                          <div
                            style={{
                              fontSize: "0.75rem",
                              color: "#c6c6c6",
                            }}
                          >
                            OS: {item.detectedOs}
                          </div>
                        )}
                      </div>
                      <div
                        style={{
                          fontSize: "0.75rem",
                          color: "#c6c6c6",
                          maxWidth: 260,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          textAlign: "right",
                        }}
                      >
                        Score: {item.risk.score}/100 ·{" "}
                        {item.risk.issues[0] || "No issues"}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Tile>
          </Column>
        </Grid>
      </main>
    </div>
  );
}
