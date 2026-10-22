"""Repeatable local data for manually testing in-app reminders."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command

from tracking.models import (
    DailyCompletion,
    MissedSkillEpisode,
    Skill,
    UserPreference,
    UserSkillSchedule,
)


@pytest.mark.django_db
def test_reminder_demo_seed_creates_repeatable_missed_skill_data() -> None:
    user = get_user_model().objects.create_user(
        email="reminder-demo@csuchico.edu",
        password="A safe local test password 2026",
    )

    call_command("seed_reminder_demo", "--email", user.email)
    call_command("seed_reminder_demo", "--email", user.email)

    preference = UserPreference.objects.get(user=user)
    active_episodes = MissedSkillEpisode.objects.filter(
        user_skill__user=user,
        closed_at__isnull=True,
    ).select_related("user_skill__skill")
    schedules = UserSkillSchedule.objects.filter(user_skill__user=user)

    assert preference.reminders_enabled
    assert {episode.user_skill.skill.name for episode in active_episodes} == {
        "Reminder Demo: Exercise",
        "Reminder Demo: Read",
    }
    assert active_episodes.count() == 2
    assert all(schedule.rule_type == UserSkillSchedule.RuleType.DAILY for schedule in schedules)
    assert all(
        episode.user_skill.skill.visibility == Skill.Visibility.PRIVATE
        and episode.user_skill.skill.created_by == user
        for episode in active_episodes
    )
    assert DailyCompletion.objects.filter(
        user_skill__user=user,
        user_skill__skill__name="Reminder Demo: Meditate",
    ).exists()


@pytest.mark.django_db
def test_reminder_demo_seed_requires_an_existing_account() -> None:
    with pytest.raises(CommandError, match="No account exists"):
        call_command("seed_reminder_demo", "--email", "missing-demo@csuchico.edu")
