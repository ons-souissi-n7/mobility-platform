from .base import *  # noqa: F403

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
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
]

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
]
CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

NINJA_PAGINATION_CLASS = "ninja.pagination.LimitOffsetPagination"
