import type { NextConfig } from "next";

const backend = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
// Extra hostnames allowed to load the dev server (phone on LAN, tunnels). Comma-separated.
const devOrigins = (process.env.DEV_ORIGINS ?? "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
    rules: { "*.css": { loaders: ["@tailwindcss/turbopack"], as: "*.css" } },
  },
  allowedDevOrigins: ["*.local", "*.trycloudflare.com", ...devOrigins],
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
