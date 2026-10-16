import type { NextConfig } from "next";

const backend = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
// Extra hostnames allowed to load the dev server (phone on LAN, tunnels). Comma-separated.
const devOrigins = (process.env.DEV_ORIGINS ?? "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

const nextConfig: NextConfig = {
  // Photo scanning and copy calls can take over a minute on a busy laptop; the default 30 s proxy limit turned those into a bare 500.
  experimental: { proxyTimeout: 300_000 },
  turbopack: {
    root: __dirname,
    rules: { "*.css": { loaders: ["@tailwindcss/turbopack"], as: "*.css" } },
  },
  allowedDevOrigins: ["*.local", "*.trycloudflare.com", ...devOrigins],
  async redirects() {
    return process.env.NEXT_PUBLIC_DEMO_ONLY === "1"
      ? [{ source: "/create", destination: "/", permanent: false }, { source: "/connections", destination: "/", permanent: false }, { source: "/jobs/:id", destination: "/", permanent: false }]
      : [];
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
