#!/bin/sh
# --workers défaut = 2*cœurs+1 (recommandation gunicorn standard), surchageable
# via GUNICORN_WORKERS. Un seul worker (ou une valeur fixe trop basse comme 2)
# sature immédiatement sous charge concurrente (cf. BNF04 : 50 utilisateurs
# simultanés) : les requêtes s'empilent derrière les workers disponibles au
# lieu d'être traitées en parallèle, ce qui fait exploser le p95 sans qu'aucune
# requête n'échoue individuellement.
set -e

workers="${GUNICORN_WORKERS:-$(( $(nproc) * 2 + 1 ))}"

exec gunicorn config.asgi:application \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --workers "$workers"
