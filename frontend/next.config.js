/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // SWC 二进制在 Windows 上有兼容问题，用 webpack 模式（已在 package.json 中配置）
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
