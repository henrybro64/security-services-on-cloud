import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1", "127.94.0.1", "localhost"],
  // Enable standalone output for Docker
  output: "standalone",
};

export default nextConfig;
