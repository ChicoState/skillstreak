"""Schedule-aware streak and reward projections."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from tracking.models import DailyCompletion, UserSkill, UserSkillSchedule

from .rewards import INDIVIDUAL_MILESTONES, OVERALL_MILESTONES

MAX_PROJECTION_DAYS = 366


@dataclass(frozen=True)
class StreakSummary:
    current_occurrences: int
    cycle_start: date | None


@dataclass(frozen=True)
class SkillRewardProjection:
    milestone_occurrences: int
    amount: int
    projected_date: date | None


@dataclass(frozen=True)
class OverallRewardProjection:
    milestone_occurrences: int
    amount: int
    projected_date: date | None
    current_occurrences: int


def _active_schedule(user_skill: UserSkill, on_date: date) -> UserSkillSchedule | None:
    return next(
        (
            schedule
            for schedule in user_skill.userskillschedule_set.all()
            if schedule.effective_from <= on_date
            and (schedule.effective_through is None or schedule.effective_through >= on_date)
        ),
        None,
    )


def _is_scheduled(schedule: UserSkillSchedule, on_date: date) -> bool:
    if schedule.rule_type == UserSkillSchedule.RuleType.DAILY:
        return True
    if schedule.rule_type == UserSkillSchedule.RuleType.EVERY_N_DAYS:
        return (on_date - schedule.effective_from).days % schedule.interval_days == 0
    if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_OF_WEEK:
        return schedule.scheduleweekday_set.filter(weekday=on_date.isoweekday()).exists()
    if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_OF_MONTH:
        return schedule.schedulemonthday_set.filter(day_of_month=on_date.day).exists()
    # Weekly/monthly target schedules allow the member to choose which days;
    # every day in the active period is a valid scheduled occurrence.
    return schedule.rule_type in {
        UserSkillSchedule.RuleType.DAYS_PER_WEEK,
        UserSkillSchedule.RuleType.DAYS_PER_MONTH,
    }


def _scheduled_dates(user_skill: UserSkill, start: date, end: date) -> list[date]:
    dates: list[date] = []
    current = start
    while current <= end:
        schedule = _active_schedule(user_skill, current)
        if schedule is None or _is_scheduled(schedule, current):
            dates.append(current)
        current += timedelta(days=1)
    return dates


def skill_streak(user_skill: UserSkill, *, as_of: date) -> StreakSummary:
    completed = set(
        DailyCompletion.objects.filter(user_skill=user_skill, completed_on__lte=as_of).values_list(
            "completed_on", flat=True
        )
    )
    if not completed:
        return StreakSummary(0, None)

    schedule = _active_schedule(user_skill, as_of)
    if schedule and schedule.rule_type in {
        UserSkillSchedule.RuleType.DAYS_PER_WEEK,
        UserSkillSchedule.RuleType.DAYS_PER_MONTH,
    }:
        return _flexible_period_streak(user_skill, completed, schedule, as_of)

    scheduled = _scheduled_dates(user_skill, user_skill.started_on, as_of)
    streak = 0
    cycle_start = None
    for scheduled_date in reversed(scheduled):
        if scheduled_date not in completed:
            break
        streak += 1
        cycle_start = scheduled_date
    return StreakSummary(streak, cycle_start)


def _flexible_period_streak(
    user_skill: UserSkill,
    completed: set[date],
    schedule: UserSkillSchedule,
    as_of: date,
) -> StreakSummary:
    def period_start(on_date: date) -> date:
        if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_WEEK:
            return on_date - timedelta(days=on_date.weekday())
        return on_date.replace(day=1)

    current_period = period_start(as_of)
    streak = 0
    cycle_start = None
    while current_period >= schedule.effective_from:
        period_end = (
            current_period + timedelta(days=6)
            if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_WEEK
            else current_period.replace(
                day=monthrange(current_period.year, current_period.month)[1]
            )
        )
        period_completions = sorted(
            item for item in completed if current_period <= item <= min(period_end, as_of)
        )
        if not period_completions:
            break
        streak += len(period_completions)
        cycle_start = period_completions[0]
        current_period -= (
            timedelta(days=7)
            if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_WEEK
            else timedelta(days=1)
        )
        if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_MONTH:
            previous_month = current_period.replace(day=1) - timedelta(days=1)
            current_period = previous_month.replace(day=1)
    return StreakSummary(streak, cycle_start)


def next_skill_reward(user_skill: UserSkill, *, as_of: date) -> SkillRewardProjection | None:
    summary = skill_streak(user_skill, as_of=as_of)
    milestone = next(
        (value for value in INDIVIDUAL_MILESTONES if value > summary.current_occurrences), None
    )
    if milestone is None:
        milestone = max(INDIVIDUAL_MILESTONES) + 2
    amount = INDIVIDUAL_MILESTONES.get(milestone, INDIVIDUAL_MILESTONES[max(INDIVIDUAL_MILESTONES)])
    dates = _scheduled_dates(
        user_skill,
        as_of + timedelta(days=1),
        as_of + timedelta(days=MAX_PROJECTION_DAYS),
    )
    remaining = milestone - summary.current_occurrences
    projected_date = dates[remaining - 1] if len(dates) >= remaining else None
    return SkillRewardProjection(milestone, amount, projected_date)


def next_overall_reward(user, *, as_of: date) -> OverallRewardProjection | None:
    from tracking.models import UserSkill

    active_skills = list(UserSkill.objects.filter(user=user, is_active=True))
    current_skill = max(
        active_skills,
        key=lambda item: skill_streak(item, as_of=as_of).current_occurrences,
        default=None,
    )
    current = skill_streak(current_skill, as_of=as_of).current_occurrences if current_skill else 0
    milestone = next((value for value in OVERALL_MILESTONES if value > current), None)
    if milestone is None:
        return None
    amount = OVERALL_MILESTONES[milestone]
    projection = next_skill_reward(current_skill, as_of=as_of) if current_skill else None
    return OverallRewardProjection(
        milestone_occurrences=milestone,
        amount=amount,
        projected_date=projection.projected_date if projection else None,
        current_occurrences=current,
    )
