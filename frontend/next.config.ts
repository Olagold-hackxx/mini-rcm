import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Image optimization
  images: {
    unoptimized: false,
    remotePatterns: [],
  },
  
  // TypeScript configuration
  typescript: {
    // Allow build to proceed even with TypeScript errors (set to false in production)
    ignoreBuildErrors: false,
  },
  
  // Turbopack configuration for Next.js 16
  // Empty config means use default Turbopack settings
  turbopack: {},
  
  // Webpack configuration (for fallback if needed)
  // Note: Next.js 16 uses Turbopack by default, webpack config is optional
  webpack: (config, { isServer }) => {
    // Optimize for client-side only modules
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        crypto: false,
      };
    }
    return config;
  },
};

export default nextConfig;
