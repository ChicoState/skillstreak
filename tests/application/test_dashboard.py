"""Tests for the authenticated, account-owned dashboard."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from skills.models import Completion, Skill, SkillSchedule


@pytest.mark.django_db
def test_authenticated_member_sees_an_empty_dashboard(client) -> None:
    user = get_user_model().objects.create_user(
        email="learner@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    client.force_login(user)

    response = client.get("/")

    content = response.content.decode()
    assert response.status_code == 200
    assert "Your skills" in content
    assert "learner@csuchico.edu" in content
    assert "No skills yet" in content
    assert "Jogging" not in content
    assert "Reading" not in content
    assert "March activity" not in content


@pytest.mark.django_db
def test_dashboard_renders_only_owned_skills_and_derived_progression(client) -> None:
    user = get_user_model().objects.create_user(
        email="learner@csuchico.edu",
        password="Secure skillstreak password 2026!",
        timezone="America/Los_Angeles",
    )
    other_user = get_user_model().objects.create_user(
        email="other@csuchico.edu",
        password="Secure skillstreak password 2026!",
        timezone="America/Los_Angeles",
    )
    owned_skill = Skill.objects.create(owner=user, name="Practice Python")
    SkillSchedule.objects.create(skill=owned_skill, weekday=date.today().weekday())
    Completion.objects.create(skill=owned_skill, completed_on=date.today())
    Skill.objects.create(owner=other_user, name="Private Other Skill")
    client.force_login(user)

    response = client.get("/")

    content = response.content.decode()
    assert response.status_code == 200
    assert "Practice Python" in content
    assert "Private Other Skill" not in content
    assert "10 XP" in content
    assert "Level 1" in content
    assert 'name="completed_on"' in content
    assert date.today().isoformat() in content


@pytest.mark.django_db
def test_dashboard_shows_timezone_setup_when_timezone_is_missing(client) -> None:
    user = get_user_model().objects.create_user(
        email="learner@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    client.force_login(user)

    response = client.get("/")

    assert response.status_code == 200
    assert "Set your timezone" in response.content.decode()


@pytest.mark.django_db
def test_logout_clears_the_authenticated_session(client) -> None:
    user = get_user_model().objects.create_user(
        email="learner@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    client.force_login(user)

    response = client.post("/logout")

    assert response.status_code == 302
    assert response.url == "/sign-in"
    assert client.get("/").url == "/sign-in?next=/"


def test_logout_rejects_a_request_without_a_csrf_token() -> None:
    csrf_client = Client(enforce_csrf_checks=True)

    response = csrf_client.post("/logout")

    assert response.status_code == 403
