"""Authenticated profile settings views."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from tracking.models import UserPreference

from .forms import ProfileSettingsForm


def _return_url(request: HttpRequest) -> str:
    """Return a safe same-site destination after saving settings."""
    next_url = request.POST.get("next") if request.method == "POST" else request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("dashboard-preview")


@login_required
@require_http_methods(["GET", "POST"])
def settings(request: HttpRequest) -> HttpResponse:
    """Display and update the signed-in user's settings."""
    preference, _ = UserPreference.objects.get_or_create(
        user=request.user,
        defaults={"timezone": "UTC", "reminders_enabled": False},
    )
    return_url = _return_url(request)
    form = ProfileSettingsForm(request.POST or None, instance=preference)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(return_url)
    return render(
        request,
        "profiles/settings.html",
        {"form": form, "return_url": return_url},
    )
