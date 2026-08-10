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

RUN apt-get update && apt-get install -y libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && pip uninstall -y pip setuptools \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY --from=builder /venv /venv
COPY . .

RUN SECRET_KEY=build-time-secret \
    DATABASE_URL=sqlite:////tmp/build.sqlite3 \
    python manage.py collectstatic --noinput \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["gunicorn", "config.asgi:application", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2"]
