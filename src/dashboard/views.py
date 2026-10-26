"""Dashboard views for selected and account-owned skills."""

from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from skills.forms import SkillForm, TimezoneForm
from skills.models import Skill as OwnedSkill
from skills.progression import TimezoneNotConfigured, local_date_for_user, progression_for_user
from tracking.models import (
    DailyCompletion,
    MissedSkillEpisode,
    UserPreference,
    UserSkill,
)
from tracking.models import (
    Skill as TrackingSkill,
)
from tracking.progress import current_goal_progress

DATE_RANGE_DAYS = 7


def dashboard_context(request: HttpRequest, extra: dict | None = None) -> dict:
    """Build context for private account-owned skills and progression."""
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

    skills = OwnedSkill.objects.filter(owner=user).prefetch_related("schedules", "completions")
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


def _skill_card(skill: OwnedSkill, dates: list[date]) -> dict:
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
    """Render selected library skills and private account-owned progression."""
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    active_skills = list(
        UserSkill.objects.filter(user=request.user, is_active=True)
        .select_related("skill")
        .prefetch_related(Prefetch("userskillschedule_set", to_attr="prefetched_schedules"))
        .order_by("skill__name")
    )
    has_reminders_enabled = UserPreference.objects.filter(
        user=request.user, reminders_enabled=True
    ).exists()
    active_missed_skill_ids = set()
    if has_reminders_enabled:
        active_missed_skill_ids = set(
            MissedSkillEpisode.objects.filter(
                user_skill__in=active_skills, closed_at__isnull=True
            ).values_list("user_skill_id", flat=True)
        )
    month_start = today.replace(day=1)
    completion_start = min(week_start, month_start)
    completions = DailyCompletion.objects.filter(
        user_skill__in=active_skills, completed_on__range=(completion_start, today)
    )
    completed = {(item.user_skill_id, item.completed_on) for item in completions}
    cards = []
    for item in active_skills:
        days = [
            {
                "date": week_start + timedelta(days=index),
                "complete": (item.id, week_start + timedelta(days=index)) in completed,
            }
            for index in range(7)
        ]
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
                "goal_met": goal_progress is not None
                and goal_progress["completed"] >= goal_progress["target"],
                "is_missed": item.id in active_missed_skill_ids,
            }
        )
    library_query = request.GET.get("q", "").strip()
    library = TrackingSkill.objects.filter(
        visibility=TrackingSkill.Visibility.SYSTEM, is_active=True
    )
    if library_query:
        library = library.filter(name__icontains=library_query)
    library = library.order_by("name")
    return render(
        request,
        "dashboard/preview.html",
        dashboard_context(
            request,
            {
                "cards": cards,
                "library": library,
                "library_query": library_query,
                "today": today,
                "active_skill_ids": {item.skill_id for item in active_skills},
            },
        ),
    )
