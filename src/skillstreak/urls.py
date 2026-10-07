"""Top-level URL configuration."""

from django.urls import include, path

from dashboard.views import preview
from tracking.views import toggle_completion, toggle_selection

from .health import health_check

urlpatterns = [
    path("", include("accounts.urls")),
    path("", preview, name="dashboard-preview"),
    path("skills/<int:skill_id>/selection", toggle_selection, name="toggle-selection"),
    path(
        "user-skills/<int:user_skill_id>/completion",
        toggle_completion,
        name="toggle-completion",
    ),
    path("healthz", health_check, name="health-check"),
]
