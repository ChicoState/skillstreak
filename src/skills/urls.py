"""Routes for authenticated skill and progression mutations."""

from django.urls import path

from . import views

urlpatterns = [
    path("skills/create", views.create_skill, name="skill-create"),
    path(
        "skills/<int:skill_id>/completion",
        views.toggle_skill_completion,
        name="skill-toggle-completion",
    ),
    path("account/timezone", views.sync_timezone, name="account-timezone-sync"),
]
