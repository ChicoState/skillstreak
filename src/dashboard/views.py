"""Authenticated selected-skill dashboard."""

from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from tracking.models import DailyCompletion, Skill, UserSkill


def preview(request: HttpRequest) -> HttpResponse:
    """Render sign-in or the current user's active skills and weekly history."""
    if not request.user.is_authenticated:
        return render(request, "dashboard/preview.html")
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    active_skills = list(
        UserSkill.objects.filter(user=request.user, is_active=True)
        .select_related("skill")
        .order_by("skill__name")
    )
    completions = DailyCompletion.objects.filter(
        user_skill__in=active_skills,
        completed_on__range=(week_start, week_start + timedelta(days=6)),
    )
    completed = {(item.user_skill_id, item.completed_on) for item in completions}
    cards = []
    for item in active_skills:
        days = []
        for index in range(7):
            day = week_start + timedelta(days=index)
            days.append({"date": day, "complete": (item.id, day) in completed})
        cards.append(
            {
                "user_skill": item,
                "days": days,
                "today_completed": (item.id, today) in completed,
                "weekly_completed": sum(day["complete"] for day in days),
            }
        )
    library = Skill.objects.filter(visibility=Skill.Visibility.SYSTEM, is_active=True).order_by(
        "name"
    )
    return render(
        request,
        "dashboard/preview.html",
        {
            "cards": cards,
            "library": library,
            "today": today,
            "active_skill_ids": {item.skill_id for item in active_skills},
        },
    )


@require_POST
def sign_in(request: HttpRequest) -> HttpResponse:
    """Authenticate one of the provisioned local demo users."""
    user = authenticate(
        request, username=request.POST.get("email", ""), password=request.POST.get("password", "")
    )
    if user is not None:
        login(request, user)
        return redirect("dashboard-preview")
    return render(request, "dashboard/preview.html", {"login_failed": True})


@require_POST
def sign_out(request: HttpRequest) -> HttpResponse:
    """End the authenticated session."""
    logout(request)
    return redirect("dashboard-preview")
