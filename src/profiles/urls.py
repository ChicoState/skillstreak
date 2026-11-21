"""Routes for authenticated profile settings."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.settings, name="profile-settings"),
    path("password/", views.change_password, name="profile-change-password"),
    path(
        "reminders/dismiss/",
        views.dismiss_reminder_digest,
        name="dismiss-profile-reminder-digest",
    ),
]
