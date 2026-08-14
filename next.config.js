const brand = require("./config/brand.json")

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Performance optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production', // Remove console.log in production
  },

  // Image CDN hosts come from config/brand.json so that forking the repo means
  // editing one file, not hunting for hostnames buried in the build config.
  images: {
    remotePatterns: brand.imageHosts.map((hostname) => ({
      protocol: 'https',
      hostname,
      pathname: '/**',
    })),
  },

  rewrites: async () => {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/api/:path*"
            : "/api/",
      },
      {
        source: "/docs",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/docs"
            : "/api/docs",
      },
      {
        source: "/openapi.json",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/openapi.json"
            : "/api/openapi.json",
      },
    ];
  },

  // Reduce bundle size
  productionBrowserSourceMaps: false,
};

module.exports = nextConfig;
