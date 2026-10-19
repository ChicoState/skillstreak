"""Selected-skill dashboard for authenticated team members."""

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from tracking.models import DailyCompletion, Skill, UserSkill
from tracking.progress import current_goal_progress


@login_required
def preview(request: HttpRequest) -> HttpResponse:
    """Render the current member's active skills and current-week history."""
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    active_skills = list(
        UserSkill.objects.filter(user=request.user, is_active=True)
        .select_related("skill")
        .prefetch_related(Prefetch("userskillschedule_set", to_attr="prefetched_schedules"))
        .order_by("skill__name")
    )
    month_start = today.replace(day=1)
    completion_start = min(week_start, month_start)
    completions = DailyCompletion.objects.filter(
        user_skill__in=active_skills,
        completed_on__range=(completion_start, today),
    )
    completed = {(item.user_skill_id, item.completed_on) for item in completions}
    cards = []
    for item in active_skills:
        days = []
        for index in range(7):
            day = week_start + timedelta(days=index)
            days.append({"date": day, "complete": (item.id, day) in completed})
        item_completions = {
            completed_on for user_skill_id, completed_on in completed if user_skill_id == item.id
        }
        goal_progress = current_goal_progress(item, item_completions, today)
        weekly_count = sum(day["complete"] for day in days)
        weekly_progress_text = (
            f"{weekly_count} day{'s' if weekly_count != 1 else ''} completed this week"
        )
        cards.append(
            {
                "user_skill": item,
                "days": days,
                "today_completed": (item.id, today) in completed,
                "progress_text": goal_progress["text"] if goal_progress else weekly_progress_text,
                "goal_met": (
                    goal_progress is not None
                    and goal_progress["completed"] >= goal_progress["target"]
                ),
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
