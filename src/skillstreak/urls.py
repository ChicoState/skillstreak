"""Top-level URL configuration for project-level endpoints."""

from django.urls import include, path

from dashboard.views import preview

from .health import health_check

urlpatterns = [
    path("", include("accounts.urls")),
    path("", preview, name="dashboard-preview"),
    path("healthz", health_check, name="health-check"),
]
