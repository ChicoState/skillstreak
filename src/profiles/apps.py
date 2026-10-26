"""Profile settings application configuration."""

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """Configure the authenticated profile settings UI."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"
