"""Authenticated profile settings views."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from tracking.models import MissedSkillEpisode, ProfileReminderDigestDismissal, UserPreference

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


def _visible_missed_episodes(user, reminders_enabled: bool) -> list[MissedSkillEpisode]:
    """Return current missed episodes unless the user acknowledged this set."""
    if not reminders_enabled:
        return []
    episodes = list(
        MissedSkillEpisode.objects.filter(
            user_skill__user=user,
            user_skill__is_active=True,
            closed_at__isnull=True,
        )
        .select_related("user_skill__skill")
        .order_by("user_skill__skill__name")
    )
    dismissal = ProfileReminderDigestDismissal.objects.filter(user=user).first()
    if dismissal and not any(episode.created_at > dismissal.dismissed_at for episode in episodes):
        return []
    return episodes


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
        {
            "form": form,
            "return_url": return_url,
            "missed_episodes": _visible_missed_episodes(
                request.user,
                preference.reminders_enabled,
            ),
        },
    )


@login_required
@require_POST
def dismiss_reminder_digest(request: HttpRequest) -> HttpResponse:
    """Acknowledge the current user's digest without resolving missed skills."""
    preference = UserPreference.objects.filter(user=request.user).first()
    if preference and _visible_missed_episodes(request.user, preference.reminders_enabled):
        ProfileReminderDigestDismissal.objects.update_or_create(
            user=request.user,
            defaults={"dismissed_at": timezone.now()},
        )
    return redirect("profile-settings")
