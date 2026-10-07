from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configure the internal team account application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
