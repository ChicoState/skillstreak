"""Top-level URL configuration for project-level endpoints."""

from django.urls import path

from dashboard.views import preview, sign_in, sign_out

from .health import health_check

urlpatterns = [
    path("", preview, name="dashboard-preview"),
    path("sign-in", sign_in, name="dashboard-sign-in"),
    path("logout", sign_out, name="dashboard-sign-out"),
    path("healthz", health_check, name="health-check"),
]
