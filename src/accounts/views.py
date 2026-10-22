"""Browser views for team registration, sign-in, and sign-out."""

from django.contrib.auth import login, logout
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import ACCOUNT_CREATION_ERROR, RegistrationForm, SignInForm


@require_http_methods(["GET", "POST"])
def register(request: HttpRequest) -> HttpResponse:
    """Create and authenticate an internal team account."""
    if request.user.is_authenticated:
        return redirect("dashboard-preview")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            form.add_error(None, ACCOUNT_CREATION_ERROR)
        else:
            login(request, user)
            return redirect("dashboard-preview")

    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def sign_in(request: HttpRequest) -> HttpResponse:
    """Authenticate a registered team member and create a server-side session."""
    if request.user.is_authenticated:
        return redirect("dashboard-preview")

    form = SignInForm(request, request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard-preview")

    return render(request, "accounts/sign_in.html", {"form": form})


@require_POST
def sign_out(request: HttpRequest) -> HttpResponse:
    """End the authenticated session and return to sign-in."""
    logout(request)
    return redirect("account-sign-in")
