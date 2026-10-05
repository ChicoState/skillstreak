"""Shared Django settings for every SkillStreak environment."""

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parents[3]

INSTALLED_APPS = [
    "accounts.apps.AccountsConfig",
    "dashboard.apps.DashboardConfig",
    "tracking.apps.TrackingConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "skillstreak.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "skillstreak.wsgi.application"
ASGI_APPLICATION = "skillstreak.asgi.application"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEMO_ACCOUNT_1_EMAIL = os.getenv("DEMO_ACCOUNT_1_EMAIL", "")
DEMO_ACCOUNT_1_PASSWORD = os.getenv("DEMO_ACCOUNT_1_PASSWORD", "")
DEMO_ACCOUNT_2_EMAIL = os.getenv("DEMO_ACCOUNT_2_EMAIL", "")
DEMO_ACCOUNT_2_PASSWORD = os.getenv("DEMO_ACCOUNT_2_PASSWORD", "")

# The local MVP uses Django-authenticated accounts while keeping session state
# in signed cookies instead of adding a server-side session table.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
LOGIN_URL = "dashboard-preview"


def database_configuration(database_url: str) -> dict[str, dict[str, str | int]]:
    """Convert a PostgreSQL URL into Django's database configuration."""
    parsed_url = urlparse(database_url)
    if parsed_url.scheme not in {"postgres", "postgresql"} or not parsed_url.path:
        message = "DATABASE_URL must be a PostgreSQL connection URL."
        raise ImproperlyConfigured(message)

    return {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed_url.path.lstrip("/")),
            "USER": unquote(parsed_url.username or ""),
            "PASSWORD": unquote(parsed_url.password or ""),
            "HOST": parsed_url.hostname or "",
            "PORT": parsed_url.port or "",
        },
    }


def required_environment_value(name: str) -> str:
    """Return a required deployment setting without exposing its value."""
    value = os.getenv(name)
    if value:
        return value

    raise ImproperlyConfigured(f"{name} must be set.")
