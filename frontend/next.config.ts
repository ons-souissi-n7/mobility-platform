import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    staleTimes: {
      // 0 = pas de router cache côté client pour les pages dynamiques.
      // Les statuts FSM doivent toujours être frais après une transition.
      dynamic: 0,
    },
  },
};

export default nextConfig;
