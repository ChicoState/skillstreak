"""Top-level URL configuration for project-level endpoints."""

from django.urls import path

from .health import health_check

urlpatterns = [
    path("healthz", health_check, name="health-check"),
]
