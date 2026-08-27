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
      // Les statuts FSM doivent toujours être fraîches après une transition.
      dynamic: 0,
    },
  },
  async headers() {
    return [
      {
        // La Content-Security-Policy n'est PAS ici : elle a besoin d'un nonce
        // différent à chaque requête pour autoriser les scripts d'hydratation
        // que Next.js injecte lui-même (App Router), ce qu'une valeur statique
        // ne peut pas fournir. Elle est donc générée par requête dans proxy.ts
        // (voir buildCsp/withCsp/nextWithCsp).
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
