"""Routes for authenticated profile settings."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.settings, name="profile-settings"),
    path(
        "reminders/dismiss/",
        views.dismiss_reminder_digest,
        name="dismiss-profile-reminder-digest",
    ),
]
