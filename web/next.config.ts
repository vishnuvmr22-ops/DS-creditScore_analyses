import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Traced dependency set only — keeps the runtime image small (research R11).
  output: "standalone",
  reactStrictMode: true,
  // The scoring service address is resolved per request on the server
  // (lib/config.tsx), never inlined at build time — one image, any environment.
  env: {},
};

export default nextConfig;
