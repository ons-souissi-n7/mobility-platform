# ── Build stage — compile dependencies with gcc ───────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && /venv/bin/pip install -r requirements.txt

# ── Runtime stage — no build tools, no root ───────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PATH="/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && pip uninstall -y pip setuptools \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY --from=builder /venv /venv

# Copie explicite (pas de COPY . .) : seuls les fichiers/dossiers nécessaires
# à l'exécution entrent dans l'image — ni tests/, ni pyproject.toml, ni
# .env* éventuels non listés dans .dockerignore. Ajouter une ligne ici si un
# nouveau dossier applicatif au premier niveau de backend/ est créé.
COPY manage.py docker-entrypoint.prod.sh ./
COPY app/ ./app/
COPY config/ ./config/

RUN SECRET_KEY=build-time-secret \
    JWT_SECRET_KEY=build-time-secret \
    PGCRYPTO_KEY=build-time-secret-32-characters-x \
    DATABASE_URL=sqlite:////tmp/build.sqlite3 \
    python manage.py collectstatic --noinput \
    && chown -R appuser:appgroup /app \
    && chmod +x docker-entrypoint.prod.sh

USER appuser

EXPOSE 8000

CMD ["./docker-entrypoint.prod.sh"]
