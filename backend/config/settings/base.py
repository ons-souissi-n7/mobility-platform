from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost", cast=Csv())

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "django_prometheus",
    "ninja",
    "django_fsm",
    "auditlog",
    "django_q",
]

LOCAL_APPS = [
    "app.auth.apps.AuthConfig",
    "app.reference",
    "app.students",
    "app.academic",
    "app.institutions",
    "app.mobility",
    "app.audit",
    "app.alerts",
    "app.outgoing",
    "app.internships",
    "app.complementary",
    "app.incoming",
    "app.cti",
    "app.imports",
    "app.rag",
    "app.analytics",
    "app.recommendation",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    # Doit être la toute première : marque l'heure de début de requête pour
    # les métriques de latence (django_prometheus_http_request_duration_seconds).
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Promotes request.user from JWT Bearer token so AuditlogMiddleware sees real users
    "app.auth.middleware.JWTMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Doit être la toute dernière : calcule la durée totale de la requête.
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=config("CONN_MAX_AGE", default=600, cast=int),
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

Q_CLUSTER = {
    "name": "mobility",
    "workers": 2,
    "recycle": 500,
    "timeout": 300,
    "retry": 360,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",
}

AUDITLOG_INCLUDE_ALL_MODELS = False

# Clé de chiffrement pgcrypto (AES symétrique) — jamais stockée dans le code.
# Obligatoire (comme SECRET_KEY) : un oubli en production doit faire échouer
# le démarrage plutôt que de chiffrer silencieusement avec une clé connue.
# Fournir via la variable d'environnement PGCRYPTO_KEY (min. 32 caractères).
PGCRYPTO_KEY = config("PGCRYPTO_KEY")
# Délai de conservation des justificatifs après validation (Art. 5(1)(e) RGPD)
DOCUMENT_RETENTION_DAYS = config("DOCUMENT_RETENTION_DAYS", default=5 * 365, cast=int)

MINIO_ENDPOINT = config("MINIO_ENDPOINT", default="minio:9000")
MINIO_PUBLIC_ENDPOINT = config("MINIO_PUBLIC_ENDPOINT", default="localhost:9000")
MINIO_ACCESS_KEY = config("MINIO_ROOT_USER", default="minio_admin")
MINIO_SECRET_KEY = config("MINIO_ROOT_PASSWORD", default="minio_secret")
MINIO_BUCKET_NAME = "mobility-documents"
MINIO_USE_HTTPS = config("MINIO_USE_HTTPS", default=False, cast=bool)

# ── Authentification CAS / JWT (rapport §3.4.7) ───────────────────────────────
# Les valeurs par défaut ci-dessous ne servent qu'en local (dev-compose, sans
# TLS) — un déploiement réel fournit toujours ces variables en https:// (voir
# .env.example) ; production.py force par ailleurs SECURE_SSL_REDIRECT=True.
# Sans objet pour le hotspot Sonar "Using http protocol is insecure" (S5332).
#
# URL publique du serveur CAS (utilisée par le navigateur pour les redirections)
CAS_SERVER_PUBLIC_URL = config(
    "CAS_SERVER_PUBLIC_URL", default="http://localhost:8380"
)  # NOSONAR
# URL interne du serveur CAS (utilisée par le backend pour valider les tickets)
CAS_SERVER_INTERNAL_URL = config(
    "CAS_SERVER_INTERNAL_URL",
    default="http://fake-cas:8380",  # NOSONAR
)
# URL publique du backend Django (doit correspondre à ce que le navigateur voit)
BACKEND_PUBLIC_URL = config(
    "BACKEND_PUBLIC_URL", default="http://localhost:8000"
)  # NOSONAR
# URL publique du frontend Next.js
FRONTEND_PUBLIC_URL = config(
    "FRONTEND_PUBLIC_URL", default="http://localhost:3000"
)  # NOSONAR
# Clé secrète HS256 pour signer les JWT — obligatoire (comme SECRET_KEY) : un
# oubli en production doit faire échouer le démarrage plutôt que de signer
# silencieusement avec une clé connue publiquement (code source).
JWT_SECRET_KEY = config("JWT_SECRET_KEY")
JWT_EXPIRY_MINUTES = config("JWT_EXPIRY_MINUTES", default=15, cast=int)

# Sécurité des cookies de session
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

MOVEON_API_URL = config("MOVEON_API_URL", default="")
MOVEON_API_KEY = config("MOVEON_API_KEY", default="")
PEGASE_API_URL = config("PEGASE_API_URL", default="")
PEGASE_API_KEY = config("PEGASE_API_KEY", default="")
EUDONET_API_URL = config("EUDONET_API_URL", default="")
EUDONET_API_KEY = config("EUDONET_API_KEY", default="")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "app": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}
