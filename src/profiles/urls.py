"""Routes for authenticated profile settings."""

from django.urls import path

from . import views

urlpatterns = [path("", views.settings, name="profile-settings")]
