"""Development settings for the Docker Compose environment."""

import os

from .base import *  # noqa: F403
from .base import database_configuration

DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-local-development-only")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

DATABASES = database_configuration(
    os.getenv(
        "DATABASE_URL",
        "postgresql://skillstreak:change-me-for-local-development@db:5432/skillstreak",
    )
)
