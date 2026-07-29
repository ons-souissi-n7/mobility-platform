# ── Build stage — full install + Next.js build ────────────────────────────────
FROM node:22-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN mkdir -p /app/public && npm run build

# ── Runtime stage — standalone output, npm supprimé ──────────────────────────
FROM node:22-slim

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

# Standalone output embarque ses propres node_modules minimaux
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
COPY --from=builder --chown=appuser:appgroup /app/public ./public

# Supprimer npm de l'image de production :
# npm n'est pas utilisé au runtime (CMD node server.js).
# Ses modules internes (brace-expansion, tar, sigstore…) génèrent des CVEs
# qui ne peuvent pas être corrigés via npm overrides. Les supprimer élimine
# ces CVEs définitivement sans compromettre le fonctionnement de l'application.
RUN rm -rf \
    /usr/local/lib/node_modules/npm \
    /usr/local/bin/npm \
    /usr/local/bin/npx

USER appuser

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
