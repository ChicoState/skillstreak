"""Selected-skill dashboard for authenticated team members."""

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from tracking.models import DailyCompletion, Skill, UserSkill


@login_required
def preview(request: HttpRequest) -> HttpResponse:
    """Render the current member's active skills and current-week history."""
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
