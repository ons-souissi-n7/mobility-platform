"""
Validation locale du seuil de performance BNF04 contre le serveur applicatif
réel (gunicorn + workers uvicorn), jamais contre `manage.py runserver`.

Identique à production.py, sauf la redirection HTTPS forcée : sans certificat
TLS local, SECURE_SSL_REDIRECT=True renverrait k6 en boucle de 301 vers une
URL https:// qui n'écoute pas. Ce module n'est utilisé que via
docker-compose.perf.yml, jamais en déploiement réel.
"""

from .production import *  # noqa: F403  # NOSONAR (S2208) — pattern standard des modules settings Django  # noqa: F403

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
