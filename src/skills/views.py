"""Authenticated skill creation, timezone, and completion views."""

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from dashboard.views import dashboard_context

from .forms import CompletionForm, SkillForm, TimezoneForm
from .models import Skill, SkillSchedule
from .progression import CompletionEligibilityError, TimezoneNotConfigured, toggle_completion


def invalid_dashboard_response(
    request: HttpRequest, context: dict, *, status: int = 400
) -> HttpResponse:
    """Render validation errors alongside the current dashboard state."""
    return render(
        request, "dashboard/preview.html", dashboard_context(request, context), status=status
    )


@login_required
@require_http_methods(["GET", "POST"])
def create_skill(request: HttpRequest) -> HttpResponse:
    """Create an owned skill and its selected weekly schedule."""
    form = SkillForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            skill = Skill.objects.create(owner=request.user, name=form.cleaned_data["name"])
            SkillSchedule.objects.bulk_create(
                [
                    SkillSchedule(skill=skill, weekday=weekday)
                    for weekday in form.cleaned_data["weekdays"]
                ]
            )
        return redirect("dashboard-preview")

    return invalid_dashboard_response(request, {"skill_form": form}, status=200)


@login_required
@require_POST
def sync_timezone(request: HttpRequest) -> HttpResponse:
    """Persist a valid browser-detected timezone for the signed-in account."""
    form = TimezoneForm(request.POST)
    if not form.is_valid():
        return invalid_dashboard_response(request, {"timezone_form": form})

    request.user.timezone = form.cleaned_data["timezone"]
    request.user.save(update_fields=["timezone"])
    return redirect("dashboard-preview")


@login_required
@require_POST
def toggle_skill_completion(request: HttpRequest, skill_id: int) -> HttpResponse:
    """Toggle one owner-scoped, scheduled completion date."""
    skill = get_object_or_404(Skill, pk=skill_id, owner=request.user)
    form = CompletionForm(request.POST)
    if not form.is_valid():
        return invalid_dashboard_response(request, {"completion_form": form})

    try:
        toggle_completion(skill, form.cleaned_data["completed_on"])
    except (CompletionEligibilityError, TimezoneNotConfigured) as error:
        form.add_error(None, str(error))
        return invalid_dashboard_response(request, {"completion_form": form})

    return redirect("dashboard-preview")
