import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // output: "export" removed — Clerk requires SSR, and Vercel handles this natively.
  // For local dev: run `npm run dev` (port 3000) alongside `python server.py --dev` (port 8000).
  // server.py's static serving (DIST_DIR) is unused once deployed to Vercel + Render.
};

export default nextConfig;
