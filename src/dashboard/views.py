"""Views and context preparation for the authenticated dashboard."""

from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from skills.forms import SkillForm, TimezoneForm
from skills.models import Skill
from skills.progression import TimezoneNotConfigured, local_date_for_user, progression_for_user

DATE_RANGE_DAYS = 7


def dashboard_context(request: HttpRequest, extra: dict | None = None) -> dict:
    """Build owner-scoped dashboard context for normal and error renders."""
    user = request.user
    context = {
        "progression": progression_for_user(user),
        "skill_form": SkillForm(),
        "timezone_form": TimezoneForm(),
        "completion_form": None,
        "timezone_configured": False,
        "date_labels": [],
        "skill_cards": [],
    }
    try:
        local_today = local_date_for_user(user)
    except TimezoneNotConfigured:
        local_today = None

    skills = Skill.objects.filter(owner=user).prefetch_related("schedules", "completions")
    if local_today:
        dates = [local_today - timedelta(days=offset) for offset in range(DATE_RANGE_DAYS, -1, -1)]
        context["timezone_configured"] = True
        context["date_labels"] = [
            {
                "date": current_date,
                "label": current_date.strftime("%a"),
                "today": current_date == local_today,
            }
            for current_date in dates
        ]
        context["skill_cards"] = [_skill_card(skill, dates) for skill in skills]
    else:
        context["skill_cards"] = [
            {"skill": skill, "scheduled_weekdays": set(), "completed_dates": set(), "days": []}
            for skill in skills
        ]

    if extra:
        context.update(extra)
    return context


def _skill_card(skill: Skill, dates: list[date]) -> dict:
    scheduled_weekdays = {schedule.weekday for schedule in skill.schedules.all()}
    completed_dates = {completion.completed_on for completion in skill.completions.all()}
    return {
        "skill": skill,
        "scheduled_weekdays": scheduled_weekdays,
        "completed_dates": completed_dates,
        "days": [
            {
                "date": current_date,
                "label": current_date.strftime("%a"),
                "day_number": current_date.day,
                "scheduled": current_date.weekday() in scheduled_weekdays,
                "completed": current_date in completed_dates,
                "today": current_date == dates[-1],
            }
            for current_date in dates
        ],
    }


@login_required
def preview(request: HttpRequest) -> HttpResponse:
    """Render the signed-in member's private skills and progression."""
    return render(request, "dashboard/preview.html", dashboard_context(request))
