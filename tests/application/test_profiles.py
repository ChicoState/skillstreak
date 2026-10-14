"""Profile settings behavior for authenticated users."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from tracking.models import UserPreference


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
    profile_link = f'{reverse("profile-settings")}?next={reverse("dashboard-preview")}'
    assert profile_link in response.content.decode()
