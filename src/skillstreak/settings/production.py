"""Secure deployment settings for Cloud Run."""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import (
    MIDDLEWARE,
    cloud_sql_database_configuration,
    database_configuration,
    required_environment_value,
)

DEBUG = False
SECRET_KEY = required_environment_value("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = [host.strip() for host in required_environment_value("ALLOWED_HOSTS").split(",")]
if not ALLOWED_HOSTS or any(not host or host == "*" for host in ALLOWED_HOSTS):
    raise ImproperlyConfigured("ALLOWED_HOSTS must contain specific hostnames.")

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS", ",".join(f"https://{host}" for host in ALLOWED_HOSTS)
    ).split(",")
    if origin.strip()
]
if not CSRF_TRUSTED_ORIGINS or any(
    not origin.startswith("https://") for origin in CSRF_TRUSTED_ORIGINS
):
    raise ImproperlyConfigured("CSRF_TRUSTED_ORIGINS must contain https:// origins.")

if os.getenv("CLOUD_SQL_CONNECTION_NAME"):
    DATABASES = cloud_sql_database_configuration(
        required_environment_value("CLOUD_SQL_CONNECTION_NAME"),
        required_environment_value("CLOUD_SQL_DATABASE"),
        required_environment_value("CLOUD_SQL_USER"),
        required_environment_value("CLOUD_SQL_PASSWORD"),
    )
else:
    DATABASES = database_configuration(required_environment_value("DATABASE_URL"))

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MIDDLEWARE = [MIDDLEWARE[0], "whitenoise.middleware.WhiteNoiseMiddleware", *MIDDLEWARE[1:]]
