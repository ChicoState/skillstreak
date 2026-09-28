"""Development settings for the Docker Compose environment."""

import os
from urllib.parse import unquote, urlparse

from .base import *  # noqa: F403

DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-local-development-only")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

database_url = urlparse(
    os.getenv(
        "DATABASE_URL",
        "postgresql://skillstreak:change-me-for-local-development@db:5432/skillstreak",
    )
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(database_url.path.lstrip("/")),
        "USER": unquote(database_url.username or ""),
        "PASSWORD": unquote(database_url.password or ""),
        "HOST": database_url.hostname or "",
        "PORT": database_url.port or "",
    },
}
