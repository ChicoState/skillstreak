"""Django application configuration for the dashboard prototype."""

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Configure the dashboard prototype without persistence."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
