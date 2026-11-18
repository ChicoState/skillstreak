"""Tests for schedule-aware coin streak calculations."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model

from coins.streaks import next_overall_reward, next_skill_reward, skill_streak
from tracking.models import DailyCompletion, Skill, UserSkill, UserSkillSchedule


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email="streak-coins@csuchico.edu", password="Secure skillstreak password 2026!"
    )


@pytest.mark.django_db
def test_streak_counts_completed_non_daily_occurrences(user):
    skill = Skill.objects.create(slug="walk", name="Walk", visibility=Skill.Visibility.SYSTEM)
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=date(2026, 1, 5))
    schedule = UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAYS_OF_WEEK,
        effective_from=date(2026, 1, 5),
    )
    schedule.scheduleweekday_set.create(weekday=1)
    schedule.scheduleweekday_set.create(weekday=3)
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 1, 5))
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 1, 7))
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 1, 12))

    summary = skill_streak(user_skill, as_of=date(2026, 1, 12))

    assert summary.current_occurrences == 3
    assert summary.cycle_start == date(2026, 1, 5)


@pytest.mark.django_db
def test_next_skill_reward_projects_from_future_non_daily_occurrences(user):
    skill = Skill.objects.create(slug="read", name="Read", visibility=Skill.Visibility.SYSTEM)
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=date(2026, 1, 5))
    schedule = UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAYS_OF_WEEK,
        effective_from=date(2026, 1, 5),
    )
    schedule.scheduleweekday_set.create(weekday=1)
    schedule.scheduleweekday_set.create(weekday=3)
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 1, 5))

    reward = next_skill_reward(user_skill, as_of=date(2026, 1, 5))

    assert reward.milestone_weeks == 1
    assert reward.projected_date == date(2026, 1, 7)


@pytest.mark.django_db
def test_weekly_target_schedule_counts_each_completion_as_an_occurrence(user):
    skill = Skill.objects.create(slug="gym", name="Gym", visibility=Skill.Visibility.SYSTEM)
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=date(2026, 1, 5))
    UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAYS_PER_WEEK,
        target_days_per_week=2,
        week_starts_on=1,
        effective_from=date(2026, 1, 5),
    )
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 1, 5))
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 1, 7))

    summary = skill_streak(user_skill, as_of=date(2026, 1, 7))

    assert summary.current_occurrences == 2


@pytest.mark.django_db
def test_overall_reward_projection_handles_a_skill_with_no_completions(user):
    skill = Skill.objects.create(
        slug="new-skill", name="New Skill", visibility=Skill.Visibility.SYSTEM
    )
    UserSkill.objects.create(user=user, skill=skill, started_on=date(2026, 1, 5))

    reward = next_overall_reward(user, as_of=date(2026, 1, 5))

    assert reward is not None
    assert reward.milestone_weeks == 1
