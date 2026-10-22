"""Profile settings behavior for authenticated users."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from tracking.models import (
    MissedSkillEpisode,
    ProfileReminderDigestDismissal,
    Skill,
    UserPreference,
    UserSkill,
)


def create_active_missed_skill(user, slug: str, name: str) -> MissedSkillEpisode:
    skill = Skill.objects.create(slug=slug, name=name)
    user_skill = UserSkill.objects.create(user=user, skill=skill, started_on=timezone.localdate())
    return MissedSkillEpisode.objects.create(
        user_skill=user_skill,
        first_missed_on=timezone.localdate() - timedelta(days=1),
        last_missed_on=timezone.localdate() - timedelta(days=1),
    )


@pytest.mark.django_db
def test_user_can_view_and_update_their_timezone(client) -> None:
    user = get_user_model().objects.create_user(
        email="timezone-user@csuchico.edu",
        password="Secure skillstreak password 2026!",
    )
    client.force_login(user)

    profile = client.get(reverse("profile-settings"), {"next": reverse("dashboard-preview")})

    assert profile.status_code == 200
    assert user.email in profile.content.decode()
    assert UserPreference.objects.get(user=user).timezone == "UTC"
    assert not UserPreference.objects.get(user=user).reminders_enabled

    updated = client.post(
        reverse("profile-settings"),
        {
            "timezone": "America/Los_Angeles",
            "reminders_enabled": "on",
            "next": reverse("dashboard-preview"),
        },
    )

    assert updated.status_code == 302
    assert updated.url == reverse("dashboard-preview")
    assert UserPreference.objects.get(user=user).timezone == "America/Los_Angeles"
    assert UserPreference.objects.get(user=user).reminders_enabled


@pytest.mark.django_db
def test_profile_settings_rejects_an_unknown_timezone(client) -> None:
    user = get_user_model().objects.create_user(
        email="timezone-validation@csuchico.edu",
        password="Secure skillstreak password 2026!",
    )
    client.force_login(user)

    response = client.post(reverse("profile-settings"), {"timezone": "Mars/Olympus_Mons"})

    assert response.status_code == 200
    assert "Select a valid choice" in response.content.decode()
    assert UserPreference.objects.get(user=user).timezone == "UTC"


@pytest.mark.django_db
def test_anonymous_user_is_redirected_from_profile_settings(client) -> None:
    response = client.get(reverse("profile-settings"))

    assert response.status_code == 302
    assert response.url == "/sign-in?next=/profile/"


@pytest.mark.django_db
def test_profile_settings_rejects_an_external_return_url(client) -> None:
    user = get_user_model().objects.create_user(
        email="timezone-return-url@csuchico.edu",
        password="Secure skillstreak password 2026!",
    )
    client.force_login(user)

    response = client.post(
        reverse("profile-settings"),
        {"timezone": "America/Los_Angeles", "next": "https://example.com"},
    )

    assert response.status_code == 302
    assert response.url == reverse("dashboard-preview")


@pytest.mark.django_db
def test_profile_settings_rejects_a_request_without_a_csrf_token() -> None:
    user = get_user_model().objects.create_user(
        email="timezone-csrf@csuchico.edu",
        password="Secure skillstreak password 2026!",
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post(reverse("profile-settings"), {"timezone": "America/Los_Angeles"})

    assert response.status_code == 403


@pytest.mark.django_db
def test_dashboard_profile_menu_links_to_profile_settings(client) -> None:
    user = get_user_model().objects.create_user(
        email="timezone-menu@csuchico.edu",
        password="Secure skillstreak password 2026!",
    )
    client.force_login(user)

    response = client.get(reverse("dashboard-preview"))

    assert response.status_code == 200
    profile_link = f"{reverse('profile-settings')}?next={reverse('dashboard-preview')}"
    assert profile_link in response.content.decode()


@pytest.mark.django_db
def test_profile_shows_all_active_missed_skills_when_reminders_are_enabled(client) -> None:
    user = get_user_model().objects.create_user(
        email="digest-user@csuchico.edu",
        password="Secure skillstreak password 2026!",
    )
    UserPreference.objects.create(user=user, reminders_enabled=True)
    create_active_missed_skill(user, "digest-exercise", "Digest exercise")
    create_active_missed_skill(user, "digest-reading", "Digest reading")
    client.force_login(user)

    response = client.get(reverse("profile-settings"))

    content = response.content.decode()
    assert "Missed skills" in content
    assert "Digest exercise" in content
    assert "Digest reading" in content
    assert "Dismiss reminder" in content


@pytest.mark.django_db
def test_profile_hides_missed_skills_when_reminders_are_disabled(client) -> None:
    user = get_user_model().objects.create_user(
        email="digest-disabled@csuchico.edu",
        password="Secure skillstreak password 2026!",
    )
    UserPreference.objects.create(user=user, reminders_enabled=False)
    create_active_missed_skill(user, "digest-disabled-skill", "Disabled digest skill")
    client.force_login(user)

    response = client.get(reverse("profile-settings"))

    assert "Missed skills" not in response.content.decode()


@pytest.mark.django_db
def test_dismissing_profile_digest_keeps_the_skill_missed(client) -> None:
    user = get_user_model().objects.create_user(
        email="digest-dismiss@csuchico.edu",
        password="Secure skillstreak password 2026!",
    )
    UserPreference.objects.create(user=user, reminders_enabled=True)
    episode = create_active_missed_skill(user, "digest-dismiss-skill", "Dismiss digest skill")
    client.force_login(user)

    response = client.post(reverse("dismiss-profile-reminder-digest"))

    episode.refresh_from_db()
    profile = client.get(reverse("profile-settings"))
    dashboard = client.get(reverse("dashboard-preview"))
    assert response.status_code == 302
    assert ProfileReminderDigestDismissal.objects.filter(user=user).exists()
    assert episode.closed_at is None
    assert "Missed skills" not in profile.content.decode()
    assert 'aria-label="Missed scheduled skill"' in dashboard.content.decode()


@pytest.mark.django_db
def test_new_missed_episode_makes_a_dismissed_profile_digest_visible_again(client) -> None:
    user = get_user_model().objects.create_user(
        email="digest-reappear@csuchico.edu",
        password="Secure skillstreak password 2026!",
    )
    UserPreference.objects.create(user=user, reminders_enabled=True)
    create_active_missed_skill(user, "digest-before-dismissal", "Earlier missed skill")
    client.force_login(user)
    client.post(reverse("dismiss-profile-reminder-digest"))
    dismissal = ProfileReminderDigestDismissal.objects.get(user=user)
    later_episode = create_active_missed_skill(user, "digest-after-dismissal", "Later missed skill")
    MissedSkillEpisode.objects.filter(pk=later_episode.pk).update(
        created_at=dismissal.dismissed_at + timedelta(microseconds=1)
    )

    response = client.get(reverse("profile-settings"))

    content = response.content.decode()
    assert "Missed skills" in content
    assert "Earlier missed skill" in content
    assert "Later missed skill" in content


@pytest.mark.django_db
def test_profile_digest_dismissal_requires_a_csrf_token() -> None:
    user = get_user_model().objects.create_user(
        email="digest-csrf@csuchico.edu",
        password="Secure skillstreak password 2026!",
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post(reverse("dismiss-profile-reminder-digest"))

    assert response.status_code == 403
