import type { NextConfig } from "next";

// The browser only ever talks to this frontend. Calls to /api/* are forwarded to the backend,
// so the session cookie stays first-party and the backend never needs to be exposed.
const backend = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
