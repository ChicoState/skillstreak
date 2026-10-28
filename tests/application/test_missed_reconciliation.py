"""Automatic missed-state reconciliation for selected skills."""

from datetime import UTC, date, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from tracking.models import (
    DailyCompletion,
    MissedSkillEpisode,
    Skill,
    UserPreference,
    UserSkill,
    UserSkillSchedule,
)
from tracking.reminders import reconcile_missed_skills


@pytest.mark.django_db
def test_dashboard_marks_a_missed_personal_daily_skill_after_its_first_due_day(client) -> None:
    """A member-created skill gains an indicator without demo-only seed data."""
    user = get_user_model().objects.create_user(
        email="personal-reminder@csuchico.edu",
        password="A safe reminder test password 2026",
    )
    yesterday = timezone.localdate() - timedelta(days=1)
    UserPreference.objects.create(
        user=user,
        reminders_enabled=True,
        reminders_started_on=yesterday,
        reminders_checked_through=yesterday - timedelta(days=1),
    )
    skill = Skill.objects.create(
        slug="private-personal-reminder",
        name="Practice piano",
        created_by=user,
        visibility=Skill.Visibility.PRIVATE,
    )
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=yesterday)
    UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAILY,
        effective_from=yesterday,
    )
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"))

    assert response.status_code == 200
    assert "Missed scheduled skill" in response.content.decode()


@pytest.mark.django_db
def test_reconciliation_marks_a_personal_weekly_goal_when_the_week_ends_short() -> None:
    user = get_user_model().objects.create_user(
        email="weekly-personal-reminder@csuchico.edu",
        password="A safe reminder test password 2026",
    )
    preference = UserPreference.objects.create(
        user=user,
        reminders_enabled=True,
        reminders_started_on=date(2026, 9, 1),
        reminders_checked_through=date(2026, 9, 27),
    )
    skill = Skill.objects.create(
        slug="private-weekly-personal-reminder",
        name="Practice painting",
        created_by=user,
        visibility=Skill.Visibility.PRIVATE,
    )
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=date(2026, 9, 1))
    UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAYS_PER_WEEK,
        effective_from=date(2026, 9, 1),
        target_days_per_week=3,
        week_starts_on=1,
    )
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 9, 28))
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 9, 30))

    reconcile_missed_skills(
        preference,
        now=datetime(2026, 10, 5, 8, tzinfo=UTC),
    )
    reconcile_missed_skills(
        preference,
        now=datetime(2026, 10, 5, 12, tzinfo=UTC),
    )

    episode = MissedSkillEpisode.objects.get(user_skill=user_skill, closed_at__isnull=True)
    assert episode.first_missed_on == date(2026, 10, 4)
    assert episode.consecutive_misses == 1
    assert (
        MissedSkillEpisode.objects.filter(user_skill=user_skill, closed_at__isnull=True).count()
        == 1
    )


@pytest.mark.django_db
def test_reconciliation_marks_a_personal_monthly_goal_when_the_month_ends_short() -> None:
    user = get_user_model().objects.create_user(
        email="monthly-personal-reminder@csuchico.edu",
        password="A safe reminder test password 2026",
    )
    preference = UserPreference.objects.create(
        user=user,
        reminders_enabled=True,
        reminders_started_on=date(2026, 9, 1),
        reminders_checked_through=date(2026, 9, 30),
    )
    skill = Skill.objects.create(
        slug="private-monthly-personal-reminder",
        name="Sketch",
        created_by=user,
        visibility=Skill.Visibility.PRIVATE,
    )
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=date(2026, 9, 1))
    UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAYS_PER_MONTH,
        effective_from=date(2026, 9, 1),
        target_days_per_month=2,
    )
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 10, 4))

    reconcile_missed_skills(
        preference,
        now=datetime(2026, 11, 1, 8, tzinfo=UTC),
    )

    episode = MissedSkillEpisode.objects.get(user_skill=user_skill, closed_at__isnull=True)
    assert episode.first_missed_on == date(2026, 10, 31)


@pytest.mark.django_db
def test_reconciliation_catches_every_unchecked_daily_period_after_an_absence() -> None:
    user = get_user_model().objects.create_user(
        email="catch-up-reminder@csuchico.edu",
        password="A safe reminder test password 2026",
    )
    preference = UserPreference.objects.create(
        user=user,
        reminders_enabled=True,
        reminders_started_on=date(2026, 9, 1),
        reminders_checked_through=date(2026, 9, 30),
    )
    skill = Skill.objects.create(slug="catch-up-skill", name="Catch-up skill")
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=date(2026, 9, 1))
    UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAILY,
        effective_from=date(2026, 9, 1),
    )

    reconcile_missed_skills(
        preference,
        now=datetime(2026, 10, 5, 8, tzinfo=UTC),
    )

    episode = MissedSkillEpisode.objects.get(user_skill=user_skill, closed_at__isnull=True)
    assert episode.first_missed_on == date(2026, 10, 1)
    assert episode.last_missed_on == date(2026, 10, 4)
    assert episode.consecutive_misses == 4


@pytest.mark.django_db
def test_opt_in_starts_a_fresh_observation_window_without_a_historical_backlog(client) -> None:
    user = get_user_model().objects.create_user(
        email="fresh-reminder-window@csuchico.edu",
        password="A safe reminder test password 2026",
    )
    skill = Skill.objects.create(slug="fresh-reminder-skill", name="Fresh reminder skill")
    user_skill = UserSkill.objects.create(
        user=user,
        skill=skill,
        started_on=timezone.localdate() - timedelta(days=7),
    )
    UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAILY,
        effective_from=user_skill.started_on,
    )
    client.force_login(user)

    response = client.post(
        reverse("profile-settings"),
        {"timezone": "UTC", "reminders_enabled": "on", "theme": "green"},
    )

    preference = UserPreference.objects.get(user=user)
    assert response.status_code == 302
    assert preference.reminders_started_on == timezone.localdate()
    assert preference.reminders_checked_through == timezone.localdate() - timedelta(days=1)
    assert not MissedSkillEpisode.objects.filter(user_skill=user_skill).exists()
    assert "Missed scheduled skill" not in client.get(reverse("dashboard-preview")).content.decode()
