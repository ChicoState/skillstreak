"""Custom-skill creation, ownership, and goal-progress behavior."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from tracking.models import (
    DailyCompletion,
    ScheduleWeekday,
    Skill,
    UserSkill,
    UserSkillSchedule,
)


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email="creator@csuchico.edu", password="Secure skillstreak password 2026!"
    )


def custom_skill_payload(**overrides):
    payload = {
        "name": "Practice guitar",
        "description": "Work on scales and a song.",
        "started_on": timezone.localdate().isoformat(),
        "frequency": "weekly",
        "target_days": "3",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_authenticated_member_can_create_a_private_weekly_custom_skill(client, user) -> None:
    client.force_login(user)

    response = client.post(reverse("create-custom-skill"), custom_skill_payload())

    skill = Skill.objects.get(name="Practice guitar")
    user_skill = UserSkill.objects.get(user=user, skill=skill)
    schedule = UserSkillSchedule.objects.get(user_skill=user_skill)
    assert response.status_code == 302
    assert response.url == reverse("dashboard-preview")
    assert skill.created_by == user
    assert skill.visibility == Skill.Visibility.PRIVATE
    assert skill.slug.startswith("private-")
    assert user_skill.is_active is True
    assert schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_WEEK
    assert schedule.target_days_per_week == 3


@pytest.mark.django_db
def test_authenticated_member_can_create_a_monthly_any_day_goal(client, user) -> None:
    client.force_login(user)

    response = client.post(
        reverse("create-custom-skill"),
        custom_skill_payload(name="Sketch", frequency="monthly", target_days="12"),
    )

    schedule = UserSkillSchedule.objects.get(user_skill__skill__name="Sketch")
    assert response.status_code == 302
    assert schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_MONTH
    assert schedule.target_days_per_month == 12


@pytest.mark.django_db
def test_custom_skill_form_rejects_blank_names_and_invalid_frequency_targets(client, user) -> None:
    client.force_login(user)

    response = client.post(
        reverse("create-custom-skill"), custom_skill_payload(name="   ", target_days="8")
    )

    assert response.status_code == 200
    assert "Enter a skill name." in response.content.decode()
    assert not Skill.objects.exists()


@pytest.mark.django_db
def test_custom_skills_are_not_visible_to_another_member(client, user) -> None:
    client.force_login(user)
    client.post(reverse("create-custom-skill"), custom_skill_payload())
    other_user = get_user_model().objects.create_user(
        email="other@csuchico.edu", password="Secure skillstreak password 2026!"
    )

    client.force_login(other_user)
    response = client.get(reverse("dashboard-preview"))

    assert "Practice guitar" not in response.content.decode()
    assert not UserSkill.objects.filter(user=other_user).exists()


@pytest.mark.django_db
def test_monthly_custom_skill_dashboard_card_shows_goal_aware_progress(client, user) -> None:
    skill = Skill.objects.create(
        slug="private-sketch-test",
        name="Sketch",
        created_by=user,
        visibility=Skill.Visibility.PRIVATE,
    )
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=date(2026, 10, 1))
    UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAYS_PER_MONTH,
        effective_from=date(2026, 10, 1),
        target_days_per_month=4,
    )
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 10, 2))
    DailyCompletion.objects.create(user_skill=user_skill, completed_on=date(2026, 10, 3))
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"))

    assert "2 of 4 days this month" in response.content.decode()


@pytest.mark.django_db
def test_dashboard_skills_heading_contains_the_custom_skill_entry_point(client, user) -> None:
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"))
    content = response.content.decode()

    assert response.status_code == 200
    assert 'class="overview-add-skill"' not in content
    assert 'class="skills-add-skill library-button"' in content
    assert content.index("Your skills") < content.index(f'href="{reverse("create-custom-skill")}"')


def test_custom_skill_creation_requires_authentication(client) -> None:
    response = client.get(reverse("create-custom-skill"))

    assert response.status_code == 302
    assert response.url == f"/sign-in?next={reverse('create-custom-skill')}"


@pytest.mark.django_db
def test_custom_skill_form_disables_browser_autocomplete_for_saved_entry_fields(
    client, user
) -> None:
    client.force_login(user)

    response = client.get(reverse("create-custom-skill"))

    assert response.status_code == 200
    assert response.content.decode().count('autocomplete="off"') == 5


def test_custom_skill_creation_requires_a_csrf_token() -> None:
    from django.test import Client

    response = Client(enforce_csrf_checks=True).post(
        reverse("create-custom-skill"), custom_skill_payload()
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_weekday_schedule_rows_remain_reserved_for_fixed_day_rules() -> None:
    """Weekly numeric goals must not invent weekday rows."""
    user = get_user_model().objects.create_user(
        email="weekdays@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    skill = Skill.objects.create(
        slug="private-weekly-test",
        name="Weekly test",
        created_by=user,
        visibility=Skill.Visibility.PRIVATE,
    )
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=timezone.localdate())
    schedule = UserSkillSchedule.objects.create(
        user_skill=user_skill,
        rule_type=UserSkillSchedule.RuleType.DAYS_PER_WEEK,
        effective_from=timezone.localdate(),
        target_days_per_week=2,
        week_starts_on=1,
    )

    assert not ScheduleWeekday.objects.filter(schedule=schedule).exists()
