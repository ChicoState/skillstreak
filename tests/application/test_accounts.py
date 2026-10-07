"""Tests for internal team account registration and authentication."""

from html import unescape

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.mark.django_db
def test_csuchico_team_member_can_register_and_reach_the_dashboard(client) -> None:
    response = client.post(
        "/register",
        {
            "email": "Learner@CSUCHICO.EDU",
            "password1": "Secure skillstreak password 2026!",
            "password2": "Secure skillstreak password 2026!",
        },
    )

    assert response.status_code == 302
    assert response.url == "/"
    assert get_user_model().objects.filter(email="learner@csuchico.edu").exists()
    assert "Your skills" in client.get("/").content.decode()


@pytest.mark.django_db
def test_registration_rejects_an_email_outside_the_team_domain(client) -> None:
    response = client.post(
        "/register",
        {
            "email": "learner@example.com",
            "password1": "Secure skillstreak password 2026!",
            "password2": "Secure skillstreak password 2026!",
        },
    )

    assert response.status_code == 200
    assert "@csuchico.edu" in response.content.decode()
    assert get_user_model().objects.count() == 0


@pytest.mark.django_db
def test_user_manager_rejects_an_account_outside_the_team_domain() -> None:
    with pytest.raises(ValueError, match="@csuchico.edu"):
        get_user_model().objects.create_user(
            email="learner@example.com", password="Secure skillstreak password 2026!"
        )


@pytest.mark.django_db
def test_registration_rejects_a_case_variant_of_an_existing_email(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(
        email="learner@csuchico.edu", password="Secure skillstreak password 2026!"
    )

    response = client.post(
        "/register",
        {
            "email": "LEARNER@csuchico.edu",
            "password1": "Another secure password 2026!",
            "password2": "Another secure password 2026!",
        },
    )

    assert response.status_code == 200
    assert "We couldn't create an account with those details." in unescape(
        response.content.decode()
    )
    assert user_model.objects.count() == 1


@pytest.mark.django_db
def test_registration_rejects_mismatched_passwords(client) -> None:
    response = client.post(
        "/register",
        {
            "email": "learner@csuchico.edu",
            "password1": "Secure skillstreak password 2026!",
            "password2": "Different secure password 2026!",
        },
    )

    assert response.status_code == 200
    assert "The two password fields didn't match." in unescape(response.content.decode())


@pytest.mark.django_db
def test_registration_rejects_a_request_without_a_csrf_token() -> None:
    csrf_client = Client(enforce_csrf_checks=True)

    response = csrf_client.post(
        "/register",
        {
            "email": "learner@csuchico.edu",
            "password1": "Secure skillstreak password 2026!",
            "password2": "Secure skillstreak password 2026!",
        },
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_existing_team_member_can_sign_in_with_email_and_password(client) -> None:
    get_user_model().objects.create_user(
        email="learner@csuchico.edu", password="Secure skillstreak password 2026!"
    )

    response = client.post(
        "/sign-in",
        {"email": "LEARNER@CSUCHICO.EDU", "password": "Secure skillstreak password 2026!"},
    )

    assert response.status_code == 302
    assert response.url == "/"
    assert "Your skills" in client.get("/").content.decode()


@pytest.mark.django_db
def test_sign_in_rejects_invalid_credentials_without_disclosing_which_value_failed(client) -> None:
    response = client.post(
        "/sign-in", {"email": "learner@csuchico.edu", "password": "incorrect-password"}
    )

    assert response.status_code == 200
    assert "The email or password is incorrect." in response.content.decode()


@pytest.mark.django_db
def test_dashboard_redirects_anonymous_visitors_to_sign_in(client) -> None:
    response = client.get("/")

    assert response.status_code == 302
    assert response.url == "/sign-in?next=/"


def test_authentication_uses_server_side_database_sessions() -> None:
    assert settings.SESSION_ENGINE == "django.contrib.sessions.backends.db"


@pytest.mark.django_db
def test_sign_in_ignores_an_external_return_target(client) -> None:
    get_user_model().objects.create_user(
        email="learner@csuchico.edu", password="Secure skillstreak password 2026!"
    )

    response = client.post(
        "/sign-in?next=https://example.com",
        {"email": "learner@csuchico.edu", "password": "Secure skillstreak password 2026!"},
    )

    assert response.status_code == 302
    assert response.url == "/"
