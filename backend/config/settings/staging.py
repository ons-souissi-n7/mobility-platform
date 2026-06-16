from decouple import Csv, config

from .production import *  # noqa: F403

# Staging mirrors production settings (security headers, Sentry, etc.).
# Override only what differs in staging.
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost", cast=Csv())
