"""Theme persistence and reminder indicators in the redesigned dashboard."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from tracking.models import MissedSkillEpisode, Skill, UserPreference, UserSkill


@pytest.mark.django_db
def test_member_can_save_a_named_color_palette(client) -> None:
    user = get_user_model().objects.create_user(
        email="theme-user@csuchico.edu",
        password="A safe theme test password 2026",
    )
    client.force_login(user)

    response = client.post(
        reverse("profile-settings"),
        {
            "timezone": "UTC",
            "reminders_enabled": "",
            "theme": "blue",
        },
    )

    preference = UserPreference.objects.get(user=user)
    assert response.status_code == 302
    assert preference.theme == "blue"
    assert client.get(reverse("dashboard-preview")).context["theme"] == "blue"


@pytest.mark.django_db
def test_member_cannot_save_an_unknown_color_palette(client) -> None:
    user = get_user_model().objects.create_user(
        email="invalid-theme@csuchico.edu",
        password="A safe theme test password 2026",
    )
    client.force_login(user)

    response = client.post(
        reverse("profile-settings"),
        {"timezone": "UTC", "theme": "arbitrary-user-css"},
    )

    assert response.status_code == 200
    assert UserPreference.objects.get(user=user).theme == UserPreference.Theme.GREEN


@pytest.mark.django_db
def test_missed_skill_has_an_icon_on_dashboard_landing_and_detail(client) -> None:
    user = get_user_model().objects.create_user(
        email="reminder-design@csuchico.edu",
        password="A safe reminder test password 2026",
    )
    preference = UserPreference.objects.create(user=user, reminders_enabled=True)
    skill = Skill.objects.create(slug="reminder-design-skill", name="Reminder design skill")
    user_skill = UserSkill.objects.create(
        user=user,
        skill=skill,
        started_on=timezone.localdate(),
    )
    MissedSkillEpisode.objects.create(
        user_skill=user_skill,
        first_missed_on=timezone.localdate() - timedelta(days=1),
        last_missed_on=timezone.localdate() - timedelta(days=1),
    )
    client.force_login(user)

    landing = client.get(reverse("dashboard-preview"))
    detail = client.get(reverse("dashboard-preview"), {"skill": user_skill.id})

    assert preference.reminders_enabled
    assert "Missed scheduled skill" in landing.content.decode()
    assert "Missed check-in" in detail.content.decode()


@pytest.mark.django_db
def test_completing_a_missed_skill_clears_its_redesigned_dashboard_indicator(client) -> None:
    user = get_user_model().objects.create_user(
        email="completion-reminder@csuchico.edu",
        password="A safe completion test password 2026",
    )
    UserPreference.objects.create(user=user, reminders_enabled=True)
    skill = Skill.objects.create(slug="completion-reminder-skill", name="Completion reminder")
    user_skill = UserSkill.objects.create(
        user=user,
        skill=skill,
        started_on=timezone.localdate(),
    )
    episode = MissedSkillEpisode.objects.create(
        user_skill=user_skill,
        first_missed_on=timezone.localdate() - timedelta(days=1),
        last_missed_on=timezone.localdate() - timedelta(days=1),
    )
    client.force_login(user)

    response = client.post(
        reverse("toggle-completion", args=[user_skill.id]), {"return_view": "dashboard"}
    )

    episode.refresh_from_db()
    assert response.status_code == 302
    assert episode.closed_at is not None
    assert "Missed scheduled skill" not in client.get(reverse("dashboard-preview")).content.decode()
