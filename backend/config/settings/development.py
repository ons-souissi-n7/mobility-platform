from .base import *  # noqa: F403

# Ce module n'est JAMAIS utilisé en production (production.py, importé par
# staging.py, définit ses propres origines et force SECURE_SSL_REDIRECT=True /
# SESSION_COOKIE_SECURE=True / CSRF_COOKIE_SECURE=True). Les URLs http://
# ci-dessous ne visent que localhost et le réseau Docker interne de dev — sans
# objet pour le hotspot Sonar "Using http protocol is insecure" (S5332).

DEBUG = True

INSTALLED_APPS += ["django_extensions", "corsheaders"]  # noqa: F405
MIDDLEWARE.insert(1, "corsheaders.middleware.CorsMiddleware")  # noqa: F405

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "backend",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",  # NOSONAR
    "http://127.0.0.1:3000",  # NOSONAR
    "http://localhost:3003",  # NOSONAR
    "http://127.0.0.1:3003",  # NOSONAR
    "http://localhost:3004",  # NOSONAR
    "http://127.0.0.1:3004",  # NOSONAR
    # Réseau Docker interne (docker-compose.test.yml) — le navigateur Playwright
    # accède au frontend via le nom de service "frontend", pas "localhost".
    "http://frontend:3000",  # NOSONAR
]

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # NOSONAR
    "http://127.0.0.1:3000",  # NOSONAR
    "http://localhost:3003",  # NOSONAR
    "http://127.0.0.1:3003",  # NOSONAR
    "http://localhost:3004",  # NOSONAR
    "http://127.0.0.1:3004",  # NOSONAR
    "http://frontend:3000",  # NOSONAR
]
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ["Content-Disposition"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

NINJA_PAGINATION_CLASS = "ninja.pagination.LimitOffsetPagination"

# Sentry est normalement branché par production.py uniquement. On l'active aussi
# en dev SI un DSN est fourni (sinon no-op total) — utile pour tester/illustrer
# la remontée d'exceptions sans passer par un déploiement.
SENTRY_DSN = config("SENTRY_DSN", default="")  # noqa: F405
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="development",
    )
