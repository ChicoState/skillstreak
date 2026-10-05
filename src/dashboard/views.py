"""Views for the fixed-demo dashboard MVP."""

from hmac import compare_digest

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

DEMO_SESSION_KEY = "demo_signed_in"


def preview(request: HttpRequest) -> HttpResponse:
    """Render the sign-in form or the static dashboard for a verified session."""
    return render(
        request,
        "dashboard/preview.html",
        {"authenticated": request.session.get(DEMO_SESSION_KEY, False)},
    )


@require_POST
def sign_in(request: HttpRequest) -> HttpResponse:
    """Allow only the runtime-configured demo identity to create a session."""
    submitted_email = request.POST.get("email", "")
    submitted_password = request.POST.get("password", "")
    credentials_configured = bool(settings.DEMO_LOGIN_EMAIL and settings.DEMO_LOGIN_PASSWORD)
    credentials_match = compare_digest(
        submitted_email, settings.DEMO_LOGIN_EMAIL
    ) and compare_digest(submitted_password, settings.DEMO_LOGIN_PASSWORD)

    if credentials_configured and credentials_match:
        request.session.cycle_key()
        request.session[DEMO_SESSION_KEY] = True
        return redirect("dashboard-preview")

    return render(request, "dashboard/preview.html", {"authenticated": False, "login_failed": True})


@require_POST
def sign_out(request: HttpRequest) -> HttpResponse:
    """Remove the demo session and return the visitor to sign-in."""
    request.session.flush()
    return redirect("dashboard-preview")
