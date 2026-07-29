# ── Build stage — full install + Next.js build ────────────────────────────────
FROM node:22-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN mkdir -p /app/public && npm run build

# ── Runtime stage — production deps only, no root ─────────────────────────────
FROM node:22-slim

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 3000

CMD ["npm", "start"]
