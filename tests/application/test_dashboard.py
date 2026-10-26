"""Dashboard behavior for selected and account-owned skills."""

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from skills.models import Completion, SkillSchedule
from skills.models import Skill as OwnedSkill
from tracking.models import DailyCompletion, MissedSkillEpisode, Skill, UserPreference, UserSkill


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        email="student@csuchico.edu", password="Secure skillstreak password 2026!"
    )


@pytest.fixture
def system_skill(db):
    return Skill.objects.create(
        slug="touch-grass",
        name="Touch Grass",
        description="Spend time outdoors.",
        visibility=Skill.Visibility.SYSTEM,
    )


@pytest.mark.django_db
def test_anonymous_dashboard_request_redirects_to_registered_member_sign_in(client) -> None:
    response = client.get(reverse("dashboard-preview"))
    assert response.status_code == 302
    assert response.url == "/sign-in?next=/"


@pytest.mark.django_db
def test_registered_member_can_select_and_complete_a_system_skill(
    client, user, system_skill
) -> None:
    client.force_login(user)
    selected = client.post(reverse("toggle-selection", args=[system_skill.id]))
    user_skill = UserSkill.objects.get(user=user, skill=system_skill)
    completed = client.post(reverse("toggle-completion", args=[user_skill.id]))

    assert selected.status_code == 302
    assert completed.status_code == 302
    assert DailyCompletion.objects.filter(
        user_skill=user_skill, completed_on=timezone.localdate()
    ).exists()
    dashboard = client.get(reverse("dashboard-preview")).content.decode()
    assert user.email in dashboard
    assert "Touch Grass" in dashboard
    assert "Spend time outdoors." in dashboard
    assert '<span class="detail-label">Progress</span>' in dashboard
    assert "1 day completed this week" in dashboard
    assert "This week" not in dashboard
    assert "Completed today — undo" in dashboard


@pytest.mark.django_db
def test_skill_actions_are_isolated_to_the_signed_in_account(client, user, system_skill) -> None:
    other_user = get_user_model().objects.create_user(
        email="other@csuchico.edu", password="Secure skillstreak password 2026!"
    )
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


@pytest.mark.django_db
def test_skill_library_can_filter_active_system_skills_by_name(client, user) -> None:
    matching_skill = Skill.objects.create(
        slug="read-fiction", name="Read Fiction", visibility=Skill.Visibility.SYSTEM
    )
    Skill.objects.create(slug="exercise", name="Exercise", visibility=Skill.Visibility.SYSTEM)
    client.force_login(user)
    response = client.get(reverse("dashboard-preview"), {"q": "fiction"})
    assert response.status_code == 200
    assert matching_skill.name in response.content.decode()
    assert "Exercise" not in response.content.decode()
    assert 'value="fiction"' in response.content.decode()


def test_skill_actions_reject_requests_without_a_csrf_token() -> None:
    response = Client(enforce_csrf_checks=True).post(reverse("toggle-selection", args=[1]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_dashboard_cards_do_not_expose_a_weekly_completed_value(client, user, system_skill) -> None:
    UserSkill.objects.create(user=user, skill=system_skill, started_on=timezone.localdate())
    client.force_login(user)
    response = client.get(reverse("dashboard-preview"))
    assert "weekly_completed" not in response.context["cards"][0]
    assert response.context["cards"][0]["days"]


@pytest.mark.django_db
def test_dashboard_omits_the_secondary_line_when_a_skill_has_no_description(client, user) -> None:
    skill = Skill.objects.create(
        slug="private-no-description",
        name="Private Skill",
        visibility=Skill.Visibility.PRIVATE,
        created_by=user,
    )
    UserSkill.objects.create(user=user, skill=skill, started_on=timezone.localdate())
    client.force_login(user)
    content = client.get(reverse("dashboard-preview")).content.decode()
    assert "<h3>Private Skill</h3></div>" in content
    assert "<h3>Private Skill</h3><p" not in content


@pytest.mark.django_db
def test_dashboard_marks_an_active_missed_skill_when_reminders_are_enabled(
    client, user, system_skill
) -> None:
    user_skill = UserSkill.objects.create(
        user=user, skill=system_skill, started_on=timezone.localdate()
    )
    UserPreference.objects.create(user=user, reminders_enabled=True)
    MissedSkillEpisode.objects.create(
        user_skill=user_skill,
        first_missed_on=timezone.localdate() - timedelta(days=1),
        last_missed_on=timezone.localdate() - timedelta(days=1),
    )
    client.force_login(user)
    response = client.get(reverse("dashboard-preview"))
    assert response.context["cards"][0]["is_missed"] is True
    content = response.content.decode()
    assert 'class="skill-icon missed"' in content
    assert 'aria-label="Missed scheduled skill"' in content


@pytest.mark.django_db
def test_dashboard_hides_missed_indicator_when_reminders_are_disabled(
    client, user, system_skill
) -> None:
    user_skill = UserSkill.objects.create(
        user=user, skill=system_skill, started_on=timezone.localdate()
    )
    UserPreference.objects.create(user=user, reminders_enabled=False)
    MissedSkillEpisode.objects.create(
        user_skill=user_skill,
        first_missed_on=timezone.localdate() - timedelta(days=1),
        last_missed_on=timezone.localdate() - timedelta(days=1),
    )
    client.force_login(user)
    response = client.get(reverse("dashboard-preview"))
    assert response.context["cards"][0]["is_missed"] is False
    content = response.content.decode()
    assert 'class="skill-icon missed"' not in content
    assert 'aria-label="Missed scheduled skill"' not in content


@pytest.mark.django_db
def test_completing_a_missed_skill_closes_its_active_episode(client, user, system_skill) -> None:
    user_skill = UserSkill.objects.create(
        user=user, skill=system_skill, started_on=timezone.localdate()
    )
    UserPreference.objects.create(user=user, reminders_enabled=True)
    episode = MissedSkillEpisode.objects.create(
        user_skill=user_skill,
        first_missed_on=timezone.localdate() - timedelta(days=1),
        last_missed_on=timezone.localdate() - timedelta(days=1),
    )
    client.force_login(user)
    response = client.post(reverse("toggle-completion", args=[user_skill.id]))
    episode.refresh_from_db()
    dashboard = client.get(reverse("dashboard-preview"))
    assert response.status_code == 302
    assert episode.closed_at is not None
    assert dashboard.context["cards"][0]["is_missed"] is False


@pytest.mark.django_db
def test_authenticated_member_sees_an_empty_dashboard(client) -> None:
    user = get_user_model().objects.create_user(
        email="learner@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    client.force_login(user)
    content = client.get("/").content.decode()
    assert "Your skills" in content
    assert "learner@csuchico.edu" in content
    assert "Choose a skill below" in content
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
    owned_skill = OwnedSkill.objects.create(owner=user, name="Practice Python")
    SkillSchedule.objects.create(skill=owned_skill, weekday=date.today().weekday())
    Completion.objects.create(skill=owned_skill, completed_on=date.today())
    OwnedSkill.objects.create(owner=other_user, name="Private Other Skill")
    client.force_login(user)
    content = client.get("/").content.decode()
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
    assert "Set your timezone" in client.get("/").content.decode()


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
    response = Client(enforce_csrf_checks=True).post("/logout")
    assert response.status_code == 403
