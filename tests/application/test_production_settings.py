import importlib

import pytest
from django.core.exceptions import ImproperlyConfigured


def test_production_settings_require_a_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)

    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        importlib.import_module("skillstreak.settings.production")


def test_production_settings_load_secure_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-only-secret-key")
    monkeypatch.setenv("ALLOWED_HOSTS", "example.com,api.example.com")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@db:5432/skillstreak")

    production = importlib.import_module("skillstreak.settings.production")

    assert production.DEBUG is False
    assert production.ALLOWED_HOSTS == ["example.com", "api.example.com"]
    assert production.SESSION_COOKIE_SECURE is True
    assert production.DATABASES["default"]["HOST"] == "db"
