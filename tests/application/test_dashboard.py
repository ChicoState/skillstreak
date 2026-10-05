"""Authentication, per-account selection, and binary completion coverage."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from tracking.models import DailyCompletion, Skill, UserSkill


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="student-one@example.com",
        email="student-one@example.com",
        password="correct-password",
    )


@pytest.fixture
def system_skill(db):
    return Skill.objects.create(
        slug="touch-grass",
        name="Touch Grass",
        description="Spend time outdoors.",
        visibility=Skill.Visibility.SYSTEM,
    )


def test_home_page_shows_a_sign_in_prompt_when_not_authenticated(client) -> None:
    response = client.get(reverse("dashboard-preview"))

    assert response.status_code == 200
    assert "Welcome to SkillStreak" in response.content.decode()
    assert "Your skills" not in response.content.decode()


@pytest.mark.django_db
def test_valid_provisioned_credentials_create_a_session_and_show_dashboard(
    client, user, system_skill
) -> None:
    response = client.post(
        reverse("dashboard-sign-in"),
        {"email": user.email, "password": "correct-password"},
    )

    assert response.status_code == 302
    assert response.url == reverse("dashboard-preview")
    assert "Your skills" in client.get(reverse("dashboard-preview")).content.decode()


@pytest.mark.django_db
def test_invalid_credentials_remain_blocked_with_a_generic_error(client, user) -> None:
    response = client.post(
        reverse("dashboard-sign-in"),
        {"email": user.email, "password": "wrong-password"},
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "The email or password is incorrect." in content
    assert "Your skills" not in content
    assert user.email not in content


def test_sign_in_rejects_a_request_without_a_csrf_token() -> None:
    csrf_client = Client(enforce_csrf_checks=True)
    response = csrf_client.post(reverse("dashboard-sign-in"), {"email": "any", "password": "value"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_logged_in_user_can_select_and_complete_a_system_skill(client, user, system_skill) -> None:
    client.force_login(user)

    selected = client.post(reverse("toggle-selection", args=[system_skill.id]))
    user_skill = UserSkill.objects.get(user=user, skill=system_skill)
    completed = client.post(reverse("toggle-completion", args=[user_skill.id]))

    assert selected.status_code == 302
    assert completed.status_code == 302
    assert user_skill.is_active is True
    assert DailyCompletion.objects.filter(
        user_skill=user_skill, completed_on=timezone.localdate()
    ).exists()
    dashboard = client.get(reverse("dashboard-preview")).content.decode()
    assert "Touch Grass" in dashboard
    assert "Completed today — undo" in dashboard


@pytest.mark.django_db
def test_completion_and_selection_are_isolated_to_the_signed_in_account(
    client, user, system_skill
) -> None:
    other_user = get_user_model().objects.create_user(username="student-two@example.com")
    other_selection = UserSkill.objects.create(
        user=other_user, skill=system_skill, started_on=timezone.localdate()
    )
    client.force_login(user)

    response = client.post(reverse("toggle-completion", args=[other_selection.id]))

    assert response.status_code == 404
    assert not DailyCompletion.objects.exists()


@pytest.mark.django_db
def test_only_active_system_skills_can_be_selected(client, user) -> None:
    private_skill = Skill.objects.create(
        slug="private-skill", name="Private Skill", visibility=Skill.Visibility.PRIVATE
    )
    client.force_login(user)

    response = client.post(reverse("toggle-selection", args=[private_skill.id]))

    assert response.status_code == 404
    assert not UserSkill.objects.exists()
