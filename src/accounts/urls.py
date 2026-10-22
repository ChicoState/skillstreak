"""Routes for internal team account access."""

from django.urls import path

from . import views

urlpatterns = [
    path("register", views.register, name="account-register"),
    path("sign-in", views.sign_in, name="account-sign-in"),
    path("logout", views.sign_out, name="account-sign-out"),
]
