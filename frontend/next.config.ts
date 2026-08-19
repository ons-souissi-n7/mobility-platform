import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Le navigateur Playwright accède au frontend via le nom de service Docker
  // "frontend" (réseau interne docker-compose.test.yml) plutôt que "localhost" —
  // sans ça, Next.js bloque les ressources dev (HMR, bootstrap client) et
  // l'hydratation de /login n'a jamais lieu (le redirect CAS ne se déclenche pas).
  allowedDevOrigins: ["frontend", "localhost", "127.0.0.1"],
  experimental: {
    staleTimes: {
      // 0 = pas de router cache côté client pour les pages dynamiques.
      // Les statuts FSM doivent toujours être frais après une transition.
      dynamic: 0,
    },
  },
};

export default nextConfig;
