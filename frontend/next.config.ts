import type { NextConfig } from "next";

const apiRewriteTarget = process.env.API_REWRITE_TARGET || "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  // SWC WASM 回退在 Windows 上的 TS 类型检查有兼容问题，跳过构建时检查
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiRewriteTarget}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

