import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    staleTimes: {
      // Pages visited once are served from router cache for 30s without a network round-trip.
      // Covers the most common back-navigation pattern (e.g. list → detail → back).
      dynamic: 30,
    },
  },
};

export default nextConfig;
