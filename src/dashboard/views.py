"""Dashboard landing, skill detail, and library views for authenticated members."""

from calendar import monthrange
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q, prefetch_related_objects
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone

from tracking.library import available_library_skills, normalize_library_query
from tracking.models import DailyCompletion, SkillTag, Tag, UserSkill, UserSkillSchedule
from tracking.progress import current_goal_progress


def current_schedule(user_skill: UserSkill, today):
    """Return the selected skill's schedule that applies on ``today``."""
    schedules = (
        user_skill.prefetched_schedules
        if hasattr(user_skill, "prefetched_schedules")
        else user_skill.userskillschedule_set.all()
    )
    return next(
        (
            schedule
            for schedule in schedules
            if schedule.effective_from <= today
            and (schedule.effective_through is None or schedule.effective_through >= today)
        ),
        None,
    )


def schedule_details(schedule, today, today_completed: bool, goal_met: bool) -> dict[str, object]:
    """Describe a supported MVP schedule without inventing fixed task times."""
    if schedule is None or schedule.rule_type == UserSkillSchedule.RuleType.DAILY:
        return {
            "frequency": "Daily",
            "deadline_label": "Next check-in" if today_completed else "Due",
            "deadline_date": today + timedelta(days=1) if today_completed else today,
        }
    if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_WEEK:
        week_end = today + timedelta(days=6 - today.weekday())
        return {
            "frequency": f"{schedule.target_days_per_week} days per week",
            "deadline_label": "Next weekly goal begins" if goal_met else "Weekly goal ends",
            "deadline_date": week_end + timedelta(days=1) if goal_met else week_end,
        }
    if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_MONTH:
        month_end = today.replace(day=monthrange(today.year, today.month)[1])
        return {
            "frequency": f"{schedule.target_days_per_month} days per month",
            "deadline_label": "Next monthly goal begins" if goal_met else "Monthly goal ends",
            "deadline_date": month_end + timedelta(days=1) if goal_met else month_end,
        }
    return {"frequency": "Daily", "deadline_label": "Due", "deadline_date": today}


def month_calendar(today, started_on, completed_dates: set) -> list[list[dict[str, object]]]:
    """Build Monday-first calendar weeks for the selected skill's current month."""
    first_weekday, days_in_month = monthrange(today.year, today.month)
    cells: list[dict[str, object]] = [{"date": None} for _ in range(first_weekday)]
    for day_number in range(1, days_in_month + 1):
        day = today.replace(day=day_number)
        cells.append(
            {
                "date": day,
                "complete": day in completed_dates,
                "future": day > today,
                "today": day == today,
                "unavailable": day < started_on,
            }
        )
    while len(cells) % 7:
        cells.append({"date": None})
    return [cells[index : index + 7] for index in range(0, len(cells), 7)]


@login_required
def preview(request: HttpRequest) -> HttpResponse:
    """Render the Dashboard landing, selected detail, or Skill library."""
    active_view = request.GET.get("view")
    if active_view != "library":
        active_view = "dashboard"
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    active_skills = list(
        UserSkill.objects.filter(user=request.user, is_active=True)
        .select_related("skill")
        .order_by("skill__name", "pk")
    )
    selected_user_skill = None
    selected_id = request.GET.get("skill", "")
    if selected_id.isdecimal():
        requested_id = int(selected_id)
        selected_user_skill = next(
            (item for item in active_skills if item.id == requested_id), None
        )

    selected_card = None
    landing_cards = []
    if active_view == "dashboard" and selected_user_skill is not None:
        prefetch_related_objects(
            [selected_user_skill],
            Prefetch("userskillschedule_set", to_attr="prefetched_schedules"),
        )
        month_start = today.replace(day=1)
        completion_start = min(week_start, month_start)
        completions = DailyCompletion.objects.filter(
            user_skill=selected_user_skill,
            completed_on__range=(completion_start, today),
        )
        completed = {item.completed_on for item in completions}
        days = []
        for index in range(7):
            day = week_start + timedelta(days=index)
            days.append({"date": day, "complete": day in completed})
        goal_progress = current_goal_progress(selected_user_skill, completed, today)
        weekly_count = sum(day["complete"] for day in days)
        weekly_progress_text = (
            f"{weekly_count} day{'s' if weekly_count != 1 else ''} completed this week"
        )
        selected_card = {
            "user_skill": selected_user_skill,
            "days": days,
            "today_completed": today in completed,
            "progress_text": goal_progress["text"] if goal_progress else weekly_progress_text,
            "goal_met": (
                goal_progress is not None and goal_progress["completed"] >= goal_progress["target"]
            ),
            "calendar_weeks": month_calendar(today, selected_user_skill.started_on, completed),
        }
        selected_card.update(
            schedule_details(
                current_schedule(selected_user_skill, today),
                today,
                selected_card["today_completed"],
                selected_card["goal_met"],
            )
        )
    elif active_view == "dashboard":
        completed_today = set(
            DailyCompletion.objects.filter(
                user_skill__in=active_skills,
                completed_on=today,
            ).values_list("user_skill_id", flat=True)
        )
        landing_cards = [
            {"user_skill": item, "today_completed": item.id in completed_today}
            for item in active_skills
        ]
    library_query = ""
    library_tag = ""
    library_tags = Tag.objects.none()
    library = available_library_skills(request.user).none()
    library_results = library
    if active_view == "library":
        library_query = normalize_library_query(request.GET.get("q", ""))
        library_tag = request.GET.get("tag", "").strip()[:48]
        if not Tag.objects.filter(slug=library_tag).exists():
            library_tag = ""
        tag_links = Prefetch(
            "skilltag_set",
            queryset=SkillTag.objects.select_related("tag").prefetch_related(
                Prefetch("tag__tagalias_set", to_attr="prefetched_aliases")
            ),
            to_attr="prefetched_tag_links",
        )
        library = (
            available_library_skills(request.user)
            .prefetch_related(tag_links)
            .order_by("name", "pk")
        )
        if library_query:
            library_results = library.filter(
                Q(name__icontains=library_query)
                | Q(description__icontains=library_query)
                | Q(tags__name__icontains=library_query)
                | Q(tags__tagalias__term__icontains=library_query)
            )
        else:
            library_results = library
        if library_tag:
            library_results = library_results.filter(tags__slug=library_tag)
        if library_query or library_tag:
            library_results = library_results.distinct().order_by("name")
        else:
            library_results = library.none()
        library_tags = Tag.objects.all()
    return render(
        request,
        "dashboard/preview.html",
        {
            "active_skills": active_skills,
            "active_view": active_view,
            "selected_user_skill": selected_user_skill,
            "selected_card": selected_card,
            "landing_cards": landing_cards,
            "library_query": library_query,
            "library_tag": library_tag,
            "library_tags": library_tags,
            "library": library,
            "library_results": library_results,
            "today": today,
            "active_skill_ids": {item.skill_id for item in active_skills},
        },
    )
