"""Reconcile durable in-app missed states from a member's active schedules."""

from calendar import monthrange
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from .models import (
    DailyCompletion,
    MissedSkillEpisode,
    UserPreference,
    UserSkill,
    UserSkillSchedule,
)


def local_date_for_preference(preference: UserPreference, now: datetime | None = None) -> date:
    """Return a preference's local date from an injectable current instant."""
    return (now or timezone.now()).astimezone(ZoneInfo(preference.timezone)).date()


def _schedule_for_date(user_skill: UserSkill, on_date: date) -> UserSkillSchedule | None:
    return next(
        (
            schedule
            for schedule in user_skill.userskillschedule_set.all()
            if schedule.effective_from <= on_date
            and (schedule.effective_through is None or schedule.effective_through >= on_date)
        ),
        None,
    )


def _completed_period(schedule: UserSkillSchedule, on_date: date) -> tuple[date, date, int] | None:
    """Return the just-finished period and its required completion count."""
    if schedule.rule_type == UserSkillSchedule.RuleType.DAILY:
        return on_date, on_date, 1
    if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_WEEK and on_date.weekday() == 6:
        return on_date - timedelta(days=6), on_date, schedule.target_days_per_week
    if (
        schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_MONTH
        and on_date.day == monthrange(on_date.year, on_date.month)[1]
    ):
        return on_date.replace(day=1), on_date, schedule.target_days_per_month
    return None


def _record_miss(user_skill: UserSkill, missed_on: date) -> None:
    """Open or extend one unresolved episode for a newly missed period."""
    episode, created = MissedSkillEpisode.objects.select_for_update().get_or_create(
        user_skill=user_skill,
        closed_at__isnull=True,
        defaults={
            "first_missed_on": missed_on,
            "last_missed_on": missed_on,
        },
    )
    if not created and missed_on > episode.last_missed_on:
        episode.last_missed_on = missed_on
        episode.consecutive_misses += 1
        episode.save(update_fields=["last_missed_on", "consecutive_misses", "updated_at"])


@transaction.atomic
def reconcile_missed_skills(preference: UserPreference, *, now: datetime | None = None) -> None:
    """Record newly missed finished periods for one opted-in member.

    The first reconciliation after opt-in establishes an observation date rather
    than creating a historical backlog. A persisted cursor lets the next visit
    process every elapsed day exactly once after an absence.
    """
    if not preference.reminders_enabled:
        return

    today = local_date_for_preference(preference, now)
    if preference.reminders_started_on is None:
        preference.reminders_started_on = today
        preference.reminders_checked_through = today - timedelta(days=1)
        preference.save(update_fields=["reminders_started_on", "reminders_checked_through"])
        return

    yesterday = today - timedelta(days=1)
    if preference.reminders_checked_through is None:
        # Existing opted-in members begin observing from their next local day;
        # do not infer a historical backlog when this field is introduced.
        preference.reminders_checked_through = yesterday
        preference.save(update_fields=["reminders_checked_through"])
        return
    first_unchecked = max(
        preference.reminders_started_on,
        preference.reminders_checked_through + timedelta(days=1),
    )
    if first_unchecked > yesterday:
        return

    completion_links = Prefetch(
        "dailycompletion_set",
        queryset=DailyCompletion.objects.filter(completed_on__range=(first_unchecked, yesterday)),
        to_attr="prefetched_reminder_completions",
    )
    active_skills = (
        UserSkill.objects.filter(user=preference.user, is_active=True)
        .prefetch_related("userskillschedule_set", completion_links)
        .order_by("pk")
    )
    for user_skill in active_skills:
        completed_dates = {
            completion.completed_on for completion in user_skill.prefetched_reminder_completions
        }
        on_date = first_unchecked
        while on_date <= yesterday:
            if on_date >= user_skill.started_on:
                schedule = _schedule_for_date(user_skill, on_date)
                if schedule is not None:
                    period = _completed_period(schedule, on_date)
                    if period is not None:
                        period_start, period_end, target = period
                        if period_start >= preference.reminders_started_on:
                            completed = sum(
                                period_start <= completed_on <= period_end
                                for completed_on in completed_dates
                            )
                            if completed < target:
                                _record_miss(user_skill, period_end)
            on_date += timedelta(days=1)
    preference.reminders_checked_through = yesterday
    preference.save(update_fields=["reminders_checked_through"])


@transaction.atomic
def apply_reminder_preference_change(
    preference: UserPreference,
    *,
    previously_enabled: bool,
    now: datetime | None = None,
) -> None:
    """Start fresh on opt-in and close unresolved state on opt-out."""
    if preference.reminders_enabled and not previously_enabled:
        preference.reminders_started_on = local_date_for_preference(preference, now)
        preference.reminders_checked_through = preference.reminders_started_on - timedelta(days=1)
    elif not preference.reminders_enabled and previously_enabled:
        MissedSkillEpisode.objects.filter(
            user_skill__user=preference.user,
            closed_at__isnull=True,
        ).update(closed_at=timezone.now())
        preference.reminders_started_on = None
        preference.reminders_checked_through = None
