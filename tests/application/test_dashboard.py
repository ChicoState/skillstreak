"""Tests for the authenticated sample dashboard."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.mark.django_db
def test_authenticated_member_sees_the_static_dashboard(client) -> None:
    user = get_user_model().objects.create_user(
        email="learner@csuchico.edu", password="Secure skillstreak password 2026!"
    )
    client.force_login(user)

    response = client.get("/")

    content = response.content.decode()
    assert response.status_code == 200
    assert "Your skills" in content
    assert "learner@csuchico.edu" in content
    assert "Demo session" not in content


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
