"""Goal-aware progress summaries for a selected skill."""

from calendar import monthrange
from datetime import date, timedelta

from .models import UserSkill, UserSkillSchedule


def current_goal_progress(
    user_skill: UserSkill, completions: set[date], today: date
) -> dict[str, int | str] | None:
    """Return the current goal's count and copy, or None for system skills."""
    schedules = (
        user_skill.prefetched_schedules
        if hasattr(user_skill, "prefetched_schedules")
        else user_skill.userskillschedule_set.all()
    )
    schedule = next(
        (
            item
            for item in schedules
            if item.effective_from <= today
            and (item.effective_through is None or item.effective_through >= today)
        ),
        None,
    )
    if schedule is None:
        return None

    if schedule.rule_type == UserSkillSchedule.RuleType.DAILY:
        period_start = period_end = today
        target = 1
        period_name = "today"
    elif schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_WEEK:
        period_start = today - timedelta(days=today.weekday())
        period_end = period_start + timedelta(days=6)
        target = schedule.target_days_per_week
        period_name = "this week"
    elif schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_MONTH:
        period_start = today.replace(day=1)
        period_end = today.replace(day=monthrange(today.year, today.month)[1])
        target = schedule.target_days_per_month
        period_name = "this month"
    else:
        return None

    completed = sum(period_start <= completion <= period_end for completion in completions)
    return {
        "completed": completed,
        "target": target,
        "text": f"{completed} of {target} day{'s' if target != 1 else ''} {period_name}",
    }
