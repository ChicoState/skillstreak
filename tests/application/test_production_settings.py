import importlib

import pytest
from django.core.exceptions import ImproperlyConfigured

from skillstreak.settings.base import cloud_sql_database_configuration, database_configuration


def test_database_url_supports_cloud_sql_unix_socket() -> None:
    database = database_configuration(
        "postgresql://user:password@/skillstreak_prod?host=/cloudsql/skillstreak-512318:us-west1:skillstreak-db"
    )

    assert database["default"]["HOST"] == "/cloudsql/skillstreak-512318:us-west1:skillstreak-db"
    assert database["default"]["NAME"] == "skillstreak_prod"


def test_cloud_sql_database_configuration_validates_connection_name() -> None:
    with pytest.raises(ImproperlyConfigured, match="project:region:instance"):
        cloud_sql_database_configuration("not-a-connection-name", "db", "user", "password")


def test_production_settings_require_a_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)

    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        importlib.import_module("skillstreak.settings.production")


def test_production_settings_load_secure_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-only-secret-key")
    monkeypatch.setenv("ALLOWED_HOSTS", "example.com,api.example.com")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "https://example.com,https://api.example.com")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@db:5432/skillstreak")

    production = importlib.import_module("skillstreak.settings.production")

    assert production.DEBUG is False
    assert production.ALLOWED_HOSTS == ["example.com", "api.example.com"]
    assert production.SESSION_COOKIE_SECURE is True
    assert production.DATABASES["default"]["HOST"] == "db"
    assert production.CSRF_TRUSTED_ORIGINS == ["https://example.com", "https://api.example.com"]


def test_production_settings_use_cloud_sql_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-only-secret-key")
    monkeypatch.setenv("ALLOWED_HOSTS", "skill-streak.com")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "https://skill-streak.com")
    monkeypatch.setenv("CLOUD_SQL_CONNECTION_NAME", "skillstreak-512318:us-west1:skillstreak-db")
    monkeypatch.setenv("CLOUD_SQL_DATABASE", "skillstreak_prod")
    monkeypatch.setenv("CLOUD_SQL_USER", "skillstreak_prod_user")
    monkeypatch.setenv("CLOUD_SQL_PASSWORD", "test-only-password")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    production = importlib.reload(importlib.import_module("skillstreak.settings.production"))

    assert production.DATABASES["default"]["HOST"] == (
        "/cloudsql/skillstreak-512318:us-west1:skillstreak-db"
    )
