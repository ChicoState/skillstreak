"""Secure deployment settings for Cloud Run."""

from .base import *  # noqa: F403
from .base import database_configuration, required_environment_value

DEBUG = False
SECRET_KEY = required_environment_value("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = [
    host.strip() for host in required_environment_value("ALLOWED_HOSTS").split(",") if host.strip()
]
DATABASES = database_configuration(required_environment_value("DATABASE_URL"))

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
